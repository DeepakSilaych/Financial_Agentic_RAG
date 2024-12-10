"""
This module defines functions and models for grading answers, either generated through a retrieval-augmented generation (RAG) approach or web-based methods, to determine their sufficiency and relevance to a given question.

Modules and Components:
1. **Answer Grading:**
   - `AnswerGrader`: A Pydantic model that captures a binary score and reason for whether a given answer satisfies a question.
   - `grade_answer`: A function that evaluates the sufficiency of a generated answer (RAG-based) for a given query using the `AnswerGrader`.

2. **Web Answer Grading:**
   - `WebAnswerGrader`: A Pydantic model that captures binary scores for both RAG and web-generated answers along with a reason.
   - `grade_web_answer`: A function that compares both RAG and web-generated answers, grading each and selecting the most relevant answer based on the scores.

3. **Logging:**
   - Detailed logging functionality is incorporated at each step to track the decision-making process regarding answer sufficiency and the selection of the best answer. Logs are captured for both successful and failed evaluations.
   - Logs include details about the grading process, sufficiency flags, reasons for grading outcomes, and answer comparisons.
   - Logs are sent to an external server for real-time tracking via the `send_logs` function.

4. **Prompts:**
   - Utilizes LangChain's `ChatPromptTemplate` for generating prompts and invoking the LLM with structured outputs using the `llm` library.
   - The `answer_grader` and `web_answer_grader` templates are configured for efficient grading of answers and scoring.

5. **UUID & State Handling:**
   - Unique identifiers (`uuid4`) are used to track each grading step in the process to ensure the traceability of actions within a session.
   - The module integrates with the `state` (an internal state management system) to pass necessary context for each step of the grading process.

Dependencies:
- `Pydantic` for data validation with structured models.
- `LangChain` for prompt-based interaction with LLMs.
- Internal utility functions such as `log_message` and `send_logs` for logging and external communication.
- `state`, `nodes`, and `llm` modules for managing internal logic and LLM interactions.

Usage:
- The grading functions evaluate answers and return updated states, including insights into the sufficiency of answers and the selected final response.
"""


from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from prompt import prompts
import state, nodes
from llm import llm
from utils import log_message
import uuid

from utils import send_logs
from config import LOGGING_SETTINGS


class AnswerGrader(BaseModel):
    """Grader assesses whether an answer addresses a question with a binary score and reasoning."""

    binary_score: str = Field(
        description="Answer addresses the question, 'yes' or 'no'"
    )
    reason: str = Field(
        description="Reason why the answer does not address the question (only applicable if binary_score is 'no')"
    )


_system_prompt = prompts.answer_grader_system_prompt

answer_grader_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt),
        ("human", "User question: \n\n {question} \n\n LLM generation: {generation}"),
    ]
)

answer_grader = answer_grader_prompt | llm.with_structured_output(AnswerGrader)


def grade_answer(state: state.InternalRAGState):
    """
    Determines whether the generated answer satisfies the query or not.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates answer with a hallucination flag if query is unanswered
                      and includes the reason for insufficiency if applicable.
    """
    question_group_id = state.get("question_group_id", 1)
    log_message(
        "------CHECKING IF ANSWER SATISFIES QUERY------",
        f"question_group{question_group_id}",
    )
    question = state["original_question"]
    answer = state["answer"]

    # Score the answer
    score = answer_grader.invoke({"question": question, "generation": answer})
    answer_sufficiency_flag = score.binary_score  # type: ignore
    reason = score.reason if answer_sufficiency_flag == "no" else None

    if answer_sufficiency_flag == "no":
        log_message(
            "------ANSWER IS INSUFFICIENT------", f"question_group{question_group_id}"
        )
        is_answer_sufficient = False
        insufficiency_reason = reason
    else:
        log_message(
            "------ANSWER IS SUFFICIENT------", f"question_group{question_group_id}"
        )
        is_answer_sufficient = True
        insufficiency_reason = None

    answer_generation_retries = state.get("answer_generation_retries", 0)
    # state["answer_generation_retries"] += 1
    # state["prev_node"] = "grade_answer"

    ###### log_tree part
    id = str(uuid.uuid4())
    child_node = nodes.grade_answer.__name__ + "//" + id
    prev_node_rewrite = child_node
    parent_node = state.get("prev_node", "START")
    log_tree = {}

    if (
        not LOGGING_SETTINGS["grade_answer"]
        or state.get("send_log_tree_logs", "") == "False"
    ):
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "answer_generation_retries": answer_generation_retries + 1,
        "insufficiency_reason": insufficiency_reason,
        "is_answer_sufficient": is_answer_sufficient,
        "prev_node_rewrite": prev_node_rewrite,
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


class WebAnswerGrader(BaseModel):
    """Grader assesses whether an answer addresses a question with a binary score and reasoning."""

    rag_score: str = Field(description="Score given to rag answer '1' or '0' ")
    web_score: str = Field(description="Score given to web answer '1' or '0' ")

    reason: str = Field(
        description="Reason for the score given to rag answer and web answer"
    )


web_answer_grader_prompt = ChatPromptTemplate.from_template(
    prompts.web_answer_grader_prompt
)


web_answer_grader = web_answer_grader_prompt | llm.with_structured_output(
    WebAnswerGrader
)


def grade_web_answer(state: state.InternalRAGState):
    """
    Determines which generated answer satisfies the query or not.
    Compares both the RAG and web-generated answers and assigns a binary score to each answer.

    Args:
        state (dict): The current graph state.

    Returns:
        dict: Updates the state with the selected answer (the one with score '1').
    """
    question_group_id = state.get("question_group_id", 1)
    log_message(
        "------COMPARING RAG ANSWER WITH WEB ANSWER------",
        f"question_group{question_group_id}",
    )

    question = state["original_question"]
    rag_answer = state.get("doc_generated_answer", "")
    web_answer = state.get("web_generated_answer", "")

    # id = str(uuid.uuid4())
    # child_node = nodes.grade_web_answer.__name__ + "//" + id
    # parent_node = state.get("prev_node" , "START")
    # log_tree = {}
    # log_tree[parent_node] = [child_node]

    if rag_answer == "":

        id = str(uuid.uuid4())
        child_node = nodes.grade_web_answer.__name__ + "//" + id
        parent_node = state.get("prev_node", "START")
        log_tree = {}

        if not LOGGING_SETTINGS["grade_web_answer"]:
            child_node = parent_node

        log_tree[parent_node] = [child_node]

        log_message(
            "------NO RAG ANSWER FOUND : RETURNING WEB GENERATED ANSWER------",
            f"question_group{question_group_id}",
        )

        output_state = {
            "answer": web_answer,
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
        return output_state

    res = web_answer_grader.invoke(
        {"question": question, "rag_answer": rag_answer, "web_answer": web_answer}
    )

    try:
        rag_score = res.rag_score
        web_score = res.web_score

        log_message(
            f"RAG Answer Score: {rag_score}, Web Answer Score: {web_score}",
            f"question_group{question_group_id}",
        )

        # Select the answer with the higher score
        if rag_score == "1":
            answer = rag_answer
        else:
            answer = web_answer

    except Exception as e:
        log_message(
            f"Error grading answers: {str(e)}", f"question_group{question_group_id}"
        )
        answer = state.get("answer", "")

    ###### log_tree part
    id = str(uuid.uuid4())
    child_node = nodes.grade_web_answer.__name__ + "//" + id
    parent_node = state.get("prev_node", "START")
    log_tree = {}

    if (
        not LOGGING_SETTINGS["grade_web_answer"]
        or state.get("send_log_tree_logs", "") == "False"
    ):
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "answer": answer,
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
