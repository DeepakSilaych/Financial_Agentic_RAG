import state, nodes, config
from utils import log_message


def assess_answer(state: state.InternalRAGState):
    """
    Checks if answer satisfies the query and decide whether to regenerate the answer or end the workflow.

    Args:
        state (state.InternalRAGState): The current graph state.

    Returns:
        str: The next node to execute in the workflow.
    """
    question_group_id = state.get("question_group_id", 1)
    log_message(
        "------CHECKING IF GENERATED ANSWER SATISFY QUERY------",
        f"question_group{question_group_id}",
    )

    if state.get("is_answer_sufficient", False):
        log_message(
            "------ANSWER SUFFICIENT: ENDING WORKFLOW------",
            f"question_group{question_group_id}",
        )
        return "ok"

    _retries = state.get("answer_generation_retries", 0)
    # log_message(f"---ANSWER INSUFFICIENT: RETRY {_retries}---",f"question_group{question_group_id}")

    if _retries > config.MAX_ANSWER_GENERATION_RETRIES:
        log_message(
            "------ANSWER INSUFFICIENT: MAXIMUM ANSWER_GENERATION_RETRIES REACHED: ENDING WORKFLOW------",
            f"question_group{question_group_id}",
        )
        return "too_many_retries"

    log_message(
        "------ANSWER INSUFFICIENT: REROUTING TO RETRIEVER------",
        f"question_group{question_group_id}",
    )
    return "retry"
