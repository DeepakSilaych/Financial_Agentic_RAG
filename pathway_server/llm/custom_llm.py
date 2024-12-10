from typing import (
    Any,
    Dict,
    Optional,
    Type,
    Union,
)
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.outputs import ChatResult
from typing_extensions import override

from pydantic import BaseModel, Field
from langchain_core.language_models.base import LanguageModelInput
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig, ensure_config
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_mistralai import ChatMistralAI
import config
from config import SIMULATE_ERRORS
from utils import log_message
from .model_wrappers import ChatGemini, Llama
from dotenv import load_dotenv
load_dotenv()

class LLM(BaseChatModel):
    openai: Optional[ChatOpenAI] = None
    anthropic: Optional[ChatAnthropic] = None
    mistral: Optional[ChatMistralAI] = None
    gemini: Optional[ChatGemini] = None
    llama: Optional[Any] = None

    _models: list[BaseChatModel | None] = []
    _model_names: list[str] = []
    initial_model: str = Field(default="openai", description="Model to use")
    num_retries: int = Field(default=2, description="Number of retries for each model")

    _schema_given: Optional[Union[Dict, Type[BaseModel]]] = None

    def instanciate_models(self) -> None:
        """
        Initializes all LLMs and assigns `None` to failed ones.
        """
        # Define initialization logic for each model
        model_initializers = {
            "openai": lambda: ChatOpenAI(model="gpt-4o-mini"),
            "anthropic": lambda: ChatAnthropic(model="claude-3-5-haiku-20241022"),  # type: ignore
            "mistral": lambda: ChatMistralAI(model="mistral-large-latest"),  # type: ignore
            "gemini": lambda: ChatGemini(model="gemini-1.5-flash"),
            "llama": lambda: Llama("meta/meta-llama-3-70b-instruct"),
        }

        # Attempt to initialize each model
        for attr, initializer in model_initializers.items():
            try:
                setattr(self, attr, initializer())
            except Exception as e:
                setattr(self, attr, None)
                log_message(f"Failed to instantiate model {attr}: {e}")
        self._models = [
            self.openai,
            self.anthropic,
            self.mistral,
            self.gemini,
            self.llama,
        ]
        self._model_names = [
            "openai",
            "anthropic",
            "mistral",
            "gemini",
            "llama",
        ]
        # Find the index corresponding to `model_given`
        start_index = self._model_names.index(self.initial_model)
        # Reorder model_order to start from `model_given`
        self._models = self._models[start_index:] + self._models[:start_index]
        self._model_names = (
            self._model_names[start_index:] + self._model_names[:start_index]
        )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.instanciate_models()
        

    @override
    def invoke(
        self,
        input_given: LanguageModelInput,
        config: Optional[RunnableConfig] = None,
        *,
        stop: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> BaseMessage:
        config = ensure_config(config)

        for model, model_name in zip(self._models, self._model_names):
            if SIMULATE_ERRORS[model_name]:
                raise RuntimeError(f"Simulating error in `{model_name}`")

            if model is None:
                continue

            for attempt in range(self.num_retries):  # Retry twice for each model
                try:
                    log_message(f"Attempt {attempt + 1} using {model_name}")
                    if self._schema_given:
                        # print(f"using {model}")
                        return model.with_structured_output(self._schema_given).invoke(
                            input_given, config, **kwargs
                        )  # type: ignore
                    else:
                        return model.invoke(input_given, config, **kwargs)
                except Exception as e:
                    log_message(f"{model} failed on attempt {attempt + 1}: {e}")

        user_input_given = input("All models failed. Do you want to retry? (y/n): ").strip().lower()
        if user_input_given in {"yes", "y"}:
            log_message("Retrying as per user request...")
            from dotenv import load_dotenv
            load_dotenv(override=True)
            self.instanciate_models()
            return self.invoke(input_given, config, stop=stop, **kwargs)  # Recursive retry
        else:
            raise RuntimeError("All models failed, and user chose not to retry.")

    @override
    def with_structured_output(
        self,
        schema: Optional[Union[Dict, Type[BaseModel]]] = None,
        *,
        include_raw: bool = False,
        **kwargs: Any,
    ) -> "LLM":
        new_instance = self.model_copy(deep=False)
        new_instance._schema_given = schema
        return new_instance

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        raise NotImplementedError

    @property
    def _llm_type(self) -> str:
        return "custom"


llm = LLM(initial_model=config.INITIAL_MODEL_PROVIDER)
