import state, nodes, config
from utils import log_message


def assess_metadata_filter(state: state.InternalRAGState):
    """
    Determines whether to generate an answer, or re-generate a question.
    """
    documents = state["documents"]
    documents_kv = state.get("documents_with_kv", [])
    log_message("---- ASSESSING METADATA FILTERS ----")
    if (len(documents) + len(documents_kv)) == 0:
        if state["metadata_retries"] <= config.MAX_METADATA_FILTERING_RETRIES:
            log_message("---- 0 DOCUMENTS RETRIEVED , RETRYING ----", 1)
            return "retry"
        else:
            log_message("---- RETRIEVAL RETRY LIMIT EXCEEDED , SEARCHING WEB ----", 1)
            return "too_many_retries"
    log_message(
        "---- SUFFICIENT DOCUMENTS RETRIEVED , SENDING TO GRADE DOCUMENTS ----", 1
    )
    return "ok"
