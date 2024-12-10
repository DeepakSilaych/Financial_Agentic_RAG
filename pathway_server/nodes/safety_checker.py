"""
Module for checking query safety and content modification.

This module processes user queries to ensure they do not contain harmful or irrelevant content. It uses a language model and image descriptions to modify queries as needed, logs safety checks, and sends logs to a server.

Functions:
- check_safety: Evaluates and modifies a query for safety and relevance, logging results.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from utils import log_message, image_to_description
from prompt import prompts
import state, nodes, config
from llm import llm
from utils import send_logs
from config import LOGGING_SETTINGS

import uuid


class SafetyChecker(BaseModel):
    modified_query: str = Field(
        default=None,
        description="modify the query if it contains any harmful or useless content",
    )


_system_prompt_for_safety = prompts._system_prompt_for_safety

safety_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt_for_safety),
        ("human", "Context: {image_desc}"),
        ("human", "Query: {query}"),
    ],
)

query_safety_checker = safety_prompt | llm.with_structured_output(SafetyChecker)


def check_safety(state: state.OverallState):
    log_message("---CHECKING FOR HARMFUL CONTENT---")
    question = state["question"]
    image_path = state.get("image_path", "")

    if not config.WORKFLOW_SETTINGS["vision"]:
        image_path = ""

    image_url, image_desc = image_to_description(image_path)
    safety_output = query_safety_checker.invoke({"query": question, "image_desc": image_desc})

    log_message(f"{safety_output.modified_query}")

    ###### log_tree part
    id = str(uuid.uuid4())
    child_node = nodes.check_safety.__name__ + "//" + id
    parent_node = state.get("prev_node", "START")
    # if parent_node == "":

    log_tree = {}

    if not LOGGING_SETTINGS["check_safety"]:
        child_node = parent_node

    log_tree[parent_node] = [child_node]

    ##### Server Logging part

    output_state = {
        "query_safe": safety_output.modified_query is not None,
        "modified_query": safety_output.modified_query,
        "question": safety_output.modified_query,
        "final_answer": "I am unable to answer this question.",
        "image_desc": image_desc,
        "image_url": image_url,
        "image_path": image_path,
        "prev_node": child_node,
        "log_tree": log_tree,
    }

    send_logs(
        parent_node=parent_node,
        curr_node=child_node,
        child_node=None,
        input_state=state,
        output_state=output_state,
        text=child_node.split("//")[0],
    )

    ######

    return output_state
