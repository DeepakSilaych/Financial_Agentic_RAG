import state, nodes, config


def assess_metadata_filter(state: state.InternalRAGState):
    """
    Determines whether to generate an answer, or re-generate a question.
    """
    question_group_id = state.get("question_group_id", 1)

    documents = state["documents"]
    documents_kv = state.get("documents_with_kv", [])
    if (len(documents) + len(documents_kv)) == 0:
        if state["metadata_retries"] <= config.MAX_METADATA_FILTERING_RETRIES:
            return "retry"
        else:
            return "too_many_retries"

    return "ok"
