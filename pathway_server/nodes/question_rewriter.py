"""
Module for query rewriting using LLM and HyDE approach.

This module provides functionality to rewrite queries by:
1. Rewriting with a general LLM-based model.
2. Enhancing with a hypothetical document-based approach (HyDE).

It includes methods for query transformation, parallel processing, and logging.

Functions:
- rewrite_question: Rewrites a question using LLM.
- rewrite_with_hyde: Rewrites a question using both LLM and HyDE.

Dependencies:
- langchain_core, pydantic, ThreadPoolExecutor, utils, llm
"""

from concurrent.futures import ThreadPoolExecutor

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils import log_message
from pydantic import BaseModel, Field

import state, nodes
from llm import llm
import uuid

from utils import send_logs
from config import LOGGING_SETTINGS
from prompt import prompts

class Hyde_doc(BaseModel):
    """Generate Hypothetical Answer to the query"""

    Hyde_ans: str = Field(description="Generate a Hypothetical answer.")


# System prompt for the question rewriter
_system_prompt = prompts.re_write_system_prompt
re_write_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt),
        (
            "human",
            "Here is the initial question: \n\n {question} \n Formulate an improved question.",
        ),
    ]
)
question_rewriter = re_write_prompt | llm | StrOutputParser()

_system_prompt_answergrader = prompts._system_prompt_answergrader
re_write_prompt_answergrader = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt_answergrader),
        (
            "human",
            "Here is the initial question: \n\n {question}. \n\n Here is the generated answer: \n\n{answer}. Here is the reason for insufficiency: \n\n {reason}. \n Formulate an improved question.",
        ),
    ]
)
question_rewriter2 = re_write_prompt_answergrader | llm | StrOutputParser()

_system_prompt_gradedocs = prompts._system_prompt_gradedocs
re_write_prompt_gradedocs = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt_gradedocs),
        (
            "human",
            "Here is the initial question: \n\n {question}. \n\n Here is the reason for the documents to be graded irrelevant: {reason}. \n\n Formulate an improved question.",
        ),
    ]
)

question_rewriter3 = re_write_prompt_gradedocs | llm | StrOutputParser()


### Not using rewrite_question


def rewrite_question(state: state.InternalRAGState):
    """
    Transform the query to produce a better question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates question key with a re-phrased question
    """
    question_group_id = state.get("question_group_id", 1)

    log_message("---TRANSFORM QUERY---", f"question_group{question_group_id}")
    question = state["original_question"]
    documents = state["documents"]
    # loop_step = state.get("loop_step", 0)
    prev_node = state.get("prev_node", "")
    prev_node_rewrite = state.get("prev_node_rewrite", "")
    answer = state.get("answer", "")
    insufficiency_reason = state.get("insufficiency_reason", "")

    metadata_retries = state["metadata_retries"]
    if len(state["documents"]) + len(state.get("documents_with_kv", [])) == 0 and (
        prev_node_rewrite.split("//")[0]
        == nodes.retrieve_documents_with_metadata.__name__
        or prev_node_rewrite.split("//")[0]
        == nodes.retrieve_documents_with_quant_qual.__name__
    ):
        metadata_retries += 1

    # Re-write question
    if prev_node == "grade_answer":
        better_question = question_rewriter2.invoke(
            {"question": question, "answer": answer, "reason": insufficiency_reason}
        )
    else:
        better_question = question_rewriter.invoke({"question": question})

    ###### log_tree part
    id = str(uuid.uuid4())
    child_node = nodes.rewrite_question.__name__ + "//" + id
    parent_node = state.get("prev_node", "START")
    log_tree = {}

    if (
        not LOGGING_SETTINGS["rewrite_question"]
        or state.get("send_log_tree_logs", "") == "False"
    ):
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "documents": documents,
        "metadata_retries": metadata_retries,
        "question": better_question,
        # "loop_step": loop_step + 1,
        "prev_node": child_node,
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


# System prompt for the HyDE-based rewriter
_hyde_system_prompt = prompts._hyde_system_prompt
hyde_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _hyde_system_prompt),
        (
            "human",
            "Here is the initial question: \n\n {question} \n Generate a hypothetical answer and then improve the question based on it ( Make sure to not change the semantics of what the question is asking ).",
        ),
    ]
)
hyde_rewriter = hyde_prompt | llm.with_structured_output(Hyde_doc)


def rewrite_with_hyde(state: state.InternalRAGState):
    """
    Rewrites the query using a hypothetical document (HyDE).

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates question key with a re-phrased question based on HyDE
    """
    question_group_id = state.get("question_group_id", 1)

    log_message(
        "------TRANSFORMING QUERY USING HyDE AND REWRITING------",
        f"question_group{question_group_id}",
    )
    question = state["original_question"]
    # documents = state["documents"]
    answer = state.get("answer", "")
    insufficiency_reason = state.get("insufficiency_reason", "")
    # prev_node = state["prev_node"]
    prev_node_rewrite = state.get("prev_node_rewrite", "")
    irrelevancy_reason = state.get("irrelevancy_reason", "")

    metadata_retries = state["metadata_retries"]
    if len(state["documents"]) + len(state.get("documents_with_kv", [])) == 0 and (
        prev_node_rewrite.split("//")[0]
        == nodes.retrieve_documents_with_metadata.__name__
        or prev_node_rewrite.split("//")[0]
        == nodes.retrieve_documents_with_quant_qual.__name__
    ):
        metadata_retries += 1

    # Generate hypothetical document and re-write question based on it
    # better_question = hyde_rewriter.invoke({"question": question})
    def get_hyde_question() -> str:
        return hyde_rewriter.invoke({"question": question}).Hyde_ans

    def get_rewritten_question() -> str:
        if prev_node_rewrite.split("//")[0] == nodes.grade_answer.__name__:
            return question_rewriter2.invoke(
                {"question": question, "answer": answer, "reason": insufficiency_reason}
            )
        elif prev_node_rewrite.split("//")[0] == nodes.grade_documents.__name__:
            return question_rewriter3.invoke(
                {"question": question, "reason": irrelevancy_reason}
            )
        else:
            return question_rewriter.invoke({"question": question})

    with ThreadPoolExecutor() as executor:
        hyde_question_future = executor.submit(get_hyde_question)
        rewritten_question_future = executor.submit(get_rewritten_question)

        hyde_better_question = hyde_question_future.result()
        rewriting_question = rewritten_question_future.result()

    better_question = hyde_better_question + "xxxxxxxxxx" + rewriting_question

    ###### log_tree part
    id = str(uuid.uuid4())
    child_node = nodes.rewrite_with_hyde.__name__ + "//" + id
    parent_node = state.get("prev_node", "START")
    log_tree = {}

    if (
        not LOGGING_SETTINGS["rewrite_with_hyde"]
        or state.get("send_log_tree_logs", "") == "False"
    ):
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "question": better_question,
        "metadata_retries": metadata_retries,
        "rewritten_question": rewriting_question,
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
