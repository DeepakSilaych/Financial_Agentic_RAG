"""
Module for extracting and combining task and question for query processing.

This module refines a query by extracting the task and question from the prompt, and combines them into a Python code that satisfies the user's request. It uses language models for decision-making and code generation.

Functions:
- make_task_question: Extracts the task and question from the query.
- combine_task_question: Combines the task and question into Python code and executes it.
"""

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

import state
import config
from llm import llm
from utils import log_message
from prompt import prompts

class Task_Question(BaseModel):
    """Draft a refined query and determine routing."""

    task: str = Field(description="Task given within the prompt.")
    question: str = Field(description="Question within the prompt.")


_system_prompt = prompts.task_router_system_prompt


decision_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt),
        (
            "human",
            "Here is the original prompt: {question}",
        ),
    ]
)

task_question = decision_prompt | llm.with_structured_output(Task_Question)


def make_task_question(state: state.OverallState):
    log_message("---EXTRACTING TASK AND QUESTION---")
    query = state["question"]

    task_question_output = task_question.invoke({"question": query})

    return {
        "task": task_question_output.task,
        "question_in_query": task_question_output.question,
    }


class Task_Question_Combiner(BaseModel):
    """Writes code which completely satisfies the user's prompt."""

    code: str = Field("Python code that combines the task and question.")


combine_task_question_system_prompt = prompts.combine_task_question_system_prompt

combine_task_question_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", combine_task_question_system_prompt),
        (
            "human",
            "Task: {task}\nQuestion: {question}\nOriginal_prompt: {original_prompt}",
        ),
    ]
)


def combine_task_question(state: state.OverallState):
    log_message("---COMBINING TASK AND QUESTION---")
    task = state["task"]
    question = state["question_in_query"]
    final_answer = state["final_answer"]

    print("Inside combine_task_question")
    if task == "None" and question == "None":
        return {}
    elif question == "None":
        code = state["code"]
    else:
        code = combine_task_question_prompt.invoke(
            {
                "task": task + "\n" + code,
                "question": question + "\n" + final_answer,
                "original_prompt": state["question"],
            }
        )["code"]

    # Write code to a python file
    with open("combined_task_question.py", "w") as file:
        file.write(code)

    try:
        # Execute the python file
        exec(open("combined_task_question.py").read())
    except Exception as e:
        print(e)
        log_message("Error in executing the code.")

    return {"task": task, "question": question, "code": code}
