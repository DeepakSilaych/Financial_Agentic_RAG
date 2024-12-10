from langchain_core.prompts import ChatPromptTemplate
from typing import Literal
from pydantic import BaseModel, Field
from llm import llm
import state
from prompt import prompts
_system_prompt = prompts._system_qq_prompt


class RouteSchema(BaseModel):
    """
    The schema for routing financial questions into quantitative or qualitative categories.
    """

    category: Literal["Quantitative", "Qualitative"] = Field(
        description="The category of the question: either 'Quantitative' or 'Qualitative'."
    )
    reason: str = Field(
        description="A brief explanation of why the question belongs to the given category."
    )


# Updated prompt template with few-shot examples
routing_prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt),
        (
            "human",
            "Classify the following financial question into quantitative or qualitative: \n{question}",
        ),
    ]
)

# Define the routing pipeline
qq_classifier = routing_prompt_template | llm.with_structured_output(RouteSchema)
