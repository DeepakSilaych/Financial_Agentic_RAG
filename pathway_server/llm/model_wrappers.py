from __future__ import annotations
from typing import Union, Dict, Any, Optional, Type
from typing_extensions import override

from pydantic import BaseModel
import instructor
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.llms.replicate import Replicate
from langchain_core.language_models.base import LanguageModelInput
from langchain_core.runnables import RunnableConfig
from langchain_core.prompt_values import PromptValue

from utils import log_message
from .parser import PydanticOutputParser
import os
from dotenv import load_dotenv
load_dotenv()


class ChatGemini(ChatGoogleGenerativeAI):
    model_name: str = "gemini-1.5-flash"
    schema_given: Optional[Union[Dict, Type[BaseModel]]] = None
    lng_instance: Any = None
    instructor_instance: Any = None

    def __init__(self, model: str = "gemini-1.5-flash"):
        super().__init__(model=model)
        self.model_name = model
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.instructor_instance = instructor.from_gemini(
            client=genai.GenerativeModel(model_name=f"models/{model}"),
            mode=instructor.Mode.GEMINI_JSON,
        )
        self.lng_instance = ChatGoogleGenerativeAI(model=model)

    @override
    def invoke(
        self,
        input: LanguageModelInput,
        config: Optional[RunnableConfig] = None,
        *,
        stop: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> Any:
        try:
            if self.schema_given:
                if isinstance(input, str):
                    messages = [
                        {
                            "role": "system",
                            "content": input,
                        }
                    ]
                elif isinstance(input, PromptValue):
                    messages = [
                        {
                            "role": "system",
                            "content": input.to_string(),
                        }
                    ]
                else:
                    messages = input
                # Generate the response
                # llm = instructor.from_gemini(
                #     client=genai.GenerativeModel(model_name="models/gemini-1.5-flash"),
                #     mode=instructor.Mode.GEMINI_JSON,
                # )
                # log_message("not llm error")
                response =self.instructor_instance.chat.completions.create(
                    messages=messages,
                    response_model=self.schema_given,
                    max_retries=3,
                )
                # log_message(f"not response error {response}")
                return response
            else:
                log_message("no schema")
                return self.lng_instance.invoke(input=input)
        except Exception as e:
            log_message(
                f"the input was {input} \n and schema was {self.schema_given}\n"
            )
            log_message(f"Error during invocation: {e}")
            raise RuntimeError(f"Error during invocation: {e}")

    @override
    def with_structured_output(
        self,
        schema: Union[Dict, Type[BaseModel]],
        *,
        include_raw: bool = False,
        **kwargs: Any,
    ) -> "ChatGemini":
        new_instance = self.model_copy(deep=False)
        new_instance.schema_given = schema
        return new_instance


class Llama:
    model_name: str
    model: Any

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = Replicate(
            model=model_name,
            # model_kwargs={"temperature": 0, "max_length": 1000, "top_p": 1},
        )

    def with_structured_output(self, schema: BaseModel):
        parser = PydanticOutputParser(pydantic_object=schema, llm=self.model)
        return self.model | parser

    def invoke(self, input: Any, config: Any):
        return self.model.invoke(input, config)
