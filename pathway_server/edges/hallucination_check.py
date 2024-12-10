import state
from config import MAX_HALLUCINATION_RETRIES
from utils import log_message


def assess_hallucination(state: state.InternalRAGState):
    """
    Checks for hallucinations and decide whether to regenerate the answer or end the workflow.

    Args:
        state (state.InternalRAGState): The current graph state.

    Returns:
        str: The next node to execute in the workflow.
    """
    question_group_id = state.get("question_group_id", 1)
    log_message(
        "---CHECK IF GENERATED ANSWER CONTAINS HALLUCINATIONS---",
        f"question_group{question_group_id}",
    )

    # Checking for hallucination flag and  retry count
    if state.get("answer_contains_hallucinations", False):
        _retries = state.get("hallucinations_retries", 0)

        if _retries > MAX_HALLUCINATION_RETRIES:
            log_message(
                "---MAXIMUM HALLUCINATION RETRIES REACHED---",
                f"question_group{question_group_id}",
            )
            return "too_many_retries"

        log_message(
            f"---HALLUCINATIONS DETECTED: RETRY {_retries}---",
            f"question_group{question_group_id}",
        )
        return "retry"

    log_message(
        "---NO HALLUCINATIONS DETECTED---",
        f"question_group{question_group_id}",
    )
    return "no_hallucination"
