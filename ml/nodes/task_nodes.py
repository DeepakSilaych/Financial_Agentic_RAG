from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

import state
import config
from llm import llm
from utils import log_message


class Prompt_For_GPT4(BaseModel):
    """Draft a refined query and determine routing."""

    prompt: str = Field(
        description="The prompt given to the user."
    )

_system_prompt = """
You are a helpful chat assistant. You have been asked to assist a user with any prompt they provide.
Your task is to create a system prompt for GPT-4 model corresponding to the task provided to you. Like you should write such a prompt with such details that the model can understand the task and generate code to perform the task in python. The model should only give the code to perform the task and nothing else.
"""

generate_prompt_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt),
        (
            "human",
            "Here is the original prompt: {prompt}",
        ),
    ]
)

generate_prompt_prompter = generate_prompt_prompt | llm.with_structured_output(Prompt_For_GPT4)

def do_task(state: state.OverallState):
    log_message("---CREATING PROMPT FOR GPT-4---")
    print(state)
    task = state["task"]
    
    code = generate_prompt_prompter.invoke({"prompt": task})
    print("Inside do_task")
    print(code)
    
    return {
        "code": code
    }