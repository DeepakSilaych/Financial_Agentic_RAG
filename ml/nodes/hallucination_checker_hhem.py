from transformers import pipeline, AutoTokenizer

import state
from utils import log_message
import config


def check_hallucination_hhem(state: state.InternalRAGState):
    """
    Determines whether the generated answer contains hallucinations based on supporting documents
    using HHEM model.

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
    except AttributeError:
        supporting_documents = " ".join([" ".join(doc) for doc in state["documents"]])

    prompt = f"""
    You are a grader assessing if the generated answer contains hallucinations based on the supporting documents.
    Your task is to check if the generated answer is consistent with the information present in the supporting documents.

    1. Hallucination not present
    - Minor paraphrasing, inferred conclusions, or rephrased content should not be flagged as hallucinations as long as the key facts and information align with the documents.
    - The answer might contain information that is inferred from multiple lines in the context.
    - Be slightly lenient in grading hallucination for answers with numbers when words like 'around', 'approx' are used in the answer. 

    2. Hallucination Present
    - Only label the answer as hallucinated if it contains claims that are **completely different**, unsupported, or contradicted by the supporting documents.
    - If the answer makes any factual claims or includes details not present in the documents, or if it contradicts the evidence provided, then it should be flagged as hallucinated.

    Provide a binary score 'yes' or 'no' to indicate whether the answer contains hallucinations:
    - if 'yes' add a reason for the hallucination in the string. 
    - 'no' if it aligns well with the supporting documents even if paraphrased.

    Supporting Documents: {supporting_documents}

    Generated Answer: {answer}
    """

    # Initialize HHEM classifier
    classifier = pipeline(
        "text-classification",
        model="vectara/hallucination_evaluation_model",
        tokenizer=AutoTokenizer.from_pretrained(
            "google/flan-t5-base", cache_dir=config.TOKENIZER_CACHE_DIR
        ),
        trust_remote_code=True,
    )

    # Get prediction from HHEM model
    try:
        result = classifier(prompt, top_k=None)
        score_dict = next(item for item in result if item["label"] == "consistent")
        score = score_dict["score"]
    except Exception as e:
        log_message(
            f"Error evaluating hallucination: {e}", f"question_group{question_group_id}"
        )
        state["answer_contains_hallucinations"] = None
        return state

    # Determine hallucination flag
    hallucination_flag = "yes" if score < 0.5 else "no"

    if hallucination_flag == "yes":
        log_message(
            "---GRADE: ANSWER CONTAINS HALLUCINATIONS---",
            f"question_group{question_group_id}",
        )
        state["answer_contains_hallucinations"] = True
    else:
        log_message(
            "---GRADE: ANSWER DOES NOT CONTAIN HALLUCINATIONS---",
            f"question_group{question_group_id}",
        )
        state["answer_contains_hallucinations"] = False

    state["hallucinations_retries"] = state.get("hallucinations_retries", 0)
    state["hallucinations_retries"] += 1

    return state
