import state, config, nodes
from utils import log_message


def assess_graded_documents(state: state.InternalRAGState):
    """
    Determines whether to generate an answer, or re-generate a question.
    """
    question_group_id = state.get("question_group_id", 1)
    # log_message("---ASSESS GRADED DOCUMENTS---",f"question_group{question_group_id}")

    filtered_documents = state["documents"]

    log_message(
        f"------NO. OF RELEVANT DOCS = {len(filtered_documents)}, SO GENEARTING ANSWER------",
        f"question_group{question_group_id}",
    )

    if len(filtered_documents) >= config.DOCS_RELEVANCE_THRESHOLD:
        # We have enough relevant documents
        return "enough_relevant_docs"

    # Enough documents are not relevant
    # We will re-generate a new query if we have not done so already (at least 3 times)
    # otherwise, we will call web search
    doc_grading_retries = state.get("doc_grading_retries", 0)
    log_message(
        "-----doc_grading_retries: " + str(doc_grading_retries),
        f"question_group{question_group_id}",
    )

    if doc_grading_retries > config.MAX_DOC_GRADING_RETRIES:
        log_message(
            "------CALLING WEB SEARCH------", f"question_group{question_group_id}"
        )
        return "too_many_retries"
    else:
        log_message(
            "------TRANSFORMING QUERY USING REWRITE AND HYDE------",
            f"question_group{question_group_id}",
        )
        return "retry"
