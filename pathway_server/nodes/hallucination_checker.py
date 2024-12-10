# -----------------------------
# Hallucination Grading for Generated Answers
# -----------------------------
# This module evaluates whether the generated answer contains hallucinations based on supporting documents.
# It leverages a specialized hallucination grading model to assess if the generated answer aligns with the 
# information provided in the supporting documents.
#
# Key Components:
# 1. **HallucinationGrade**: A Pydantic model that defines the structure of the hallucination grading output, 
#    which includes a binary score ('yes' or 'no') and an optional reason for the hallucination if present.
# 2. **HallucinationGraderInput**: A Pydantic model to capture the input required for hallucination grading, 
#    including the generated answer and the supporting documents.
# 3. **hallucination_grade_prompt**: A prompt template that formats the data for the hallucination grading model.
# 4. **check_hallucination**: The main function that invokes the hallucination grading model and determines 
#    whether the generated answer contains hallucinations.
#
# Functionality:
# - **Hallucination Evaluation**: The system checks if the generated answer matches the facts in the 
#   supporting documents, scoring the answer as either containing hallucinations ('yes') or being consistent 
#   with the documents ('no').
# - **Logging**: Logs are generated to track the state and grading process, including the hallucination reason 
#   and retry counts.
#
# Features:
# - Uses a pre-trained model to perform hallucination checks.
# - Supports logging for detailed insights and tracking of the hallucination grading process.
# - Includes retry logic for repeated hallucination checks.
#
# Improvements:
# - Could refine the hallucination grading process with better models or advanced techniques for hallucination detection.
# -----------------------------

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from typing import Optional
from prompt import prompts
import state, nodes
from llm import llm
from utils import log_message, send_logs
from config import LOGGING_SETTINGS
import uuid


class HallucinationGrade(BaseModel):
    """Binary score for hallucination check on generated answers."""

    binary_score: str = Field(
        description="Answer contains hallucination, 'yes' or 'no'"
    )
    reason: Optional[str] = Field(
        default=None, description="Reason for hallucination if binary score is 'Yes'"
    )


class HallucinationGraderInput(BaseModel):
    answer: str
    supporting_documents: str


_system_prompt = prompts.hallcuination_system_prompt

hallucination_grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt),
        (
            "human",
            "Generated answer: \n\n {answer} \n\n Supporting documents: {supporting_documents}",
        ),
    ]
)

hallucination_grader = hallucination_grade_prompt | llm.with_structured_output(
    HallucinationGrade
)


def check_hallucination(state: state.InternalRAGState):
    """
    Determines whether the generated answer contains hallucinations based on supporting documents.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates answer with a hallucination flag if hallucinations are detected
    """
    question_group_id = state.get("question_group_id", 1)
    log_message(
        "---CHECK GENERATED ANSWER FOR HALLUCINATIONS---",
        f"question_group{question_group_id}",
    )
    answer = state["answer"]
    try:
        supporting_documents = " ".join(
            [doc.page_content for doc in state["documents"]]
        )
    except:
        supporting_documents = " ".join([" ".join(doc) for doc in state["documents"]])
    # supporting_documents = " ".join([doc.page_content for doc in state["documents"]])

    # Score the answer
    score = hallucination_grader.invoke(
        {"answer": answer, "supporting_documents": supporting_documents}
    )
    hallucination_flag = score.binary_score  # type: ignore
    hallucination_reason = score.reason

    answer_contains_hallucinations = False
    hallucination_reason_var = None

    if hallucination_flag == "yes":
        log_message(
            "---GRADE: ANSWER CONTAINS HALLUCINATIONS---",
            f"question_group{question_group_id}",
        )
        answer_contains_hallucinations = True
        hallucination_reason_var = hallucination_reason
    else:
        log_message(
            "---GRADE: ANSWER DOES NOT CONTAIN HALLUCINATIONS---",
            f"question_group{question_group_id}",
        )
        answer_contains_hallucinations = False
        hallucination_reason_var = "None"

    hallucinations_retries = state.get("hallucinations_retries", 0)
    hallucinations_retries += 1

    # ##### log_tree part
    # curr_node = nodes.check_hallucination.__name__
    # prev_node = state.get("prev_node" , "")
    # state["log_tree"][prev_node] = [{"node" : curr_node , "state" : state}]

    # #####

    ###### log_tree part
    # import uuid , nodes
    id = str(uuid.uuid4())
    child_node = nodes.check_hallucination.__name__ + "//" + id
    parent_node = state.get("prev_node", "START")
    if parent_node == "":
        parent_node = "START"
    log_tree = {}

    if (
        not LOGGING_SETTINGS["check_hallucination"]
        or state.get("send_log_tree_logs", "") == "False"
    ):
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "answer_contains_hallucinations": answer_contains_hallucinations,
        "hallucination_reason": hallucination_reason_var,
        "hallucinations_retries": hallucinations_retries,
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
