from langchain_core.prompts import ChatPromptTemplate
from typing import Literal
from pydantic import BaseModel, Field
from llm import llm
import state

_system_prompt = """
You are an intelligent assistant specialized in analyzing financial documents like 10-K and 10-Q reports. 
Your task is to classify user questions into one of the following categories:

1. **Quantitative**: Questions that require numerical data, tables, charts, or figures in the reports for an answer.
2. **Qualitative**: Questions that involve interpreting textual content, such as management discussions, business strategies, or narrative descriptions.

Here are some examples to guide you:

Example 1:
Question: How much did Apple repurchase of its common stock during 2023?
Category: Quantitative
Reason: The question requires numerical data about stock repurchases, which is typically found in tables or figures.

Example 2:
Question: What primarily caused the year-over-year decrease in Europe net sales for Apple in 2023?
Category: Qualitative
Reason: The question involves interpreting textual content about causes of sales decreases.

Example 3:
Question: Which categories of Apple products primarily saw lower net sales in Greater China in 2023?
Category: Quantitative
Reason: The question focuses on numerical data related to product categories and sales figures.

Now, classify the user’s question into either **Quantitative** or **Qualitative**, and provide a brief reason for your classification.

### NOTE ###
If you are unsure about category direct it to Quantitative Category.

#### OUTPUT ####
Always return the response in the following format:
Category: <Quantitative/Qualitative>
Reason: <Brief reason why the question belongs to this category>
"""

class RouteSchema(BaseModel):
    """
    The schema for routing financial questions into quantitative or qualitative categories.
    """
    category: Literal['Quantitative', 'Qualitative'] = Field(
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
