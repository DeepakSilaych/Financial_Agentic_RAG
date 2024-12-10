# ------------------------------
# Hallucination Detection Using HHEM
# ------------------------------
# This module evaluates whether a generated answer contains hallucinations based on supporting documents.
# It leverages the HHEM (Hallucination Evaluation Model) to assess the factual accuracy and consistency 
# of the response. The system checks if the generated answer aligns with the context and documents, 
# and flags it if any hallucinations (false claims or unsupported information) are detected.
#
# Key Components:
# 1. **check_hallucination_hhem**: The main function that processes the generated answer and supporting documents, 
#    and uses the HHEM model to evaluate if hallucinations are present.
# 2. **Pipeline**: The HuggingFace `pipeline` is used to load a pre-trained model (HHEM) for classification. 
#    This model evaluates whether the answer is consistent with the supporting documents.
# 3. **Logging**: Extensive logging is implemented to track the evaluation process, including any errors, 
#    hallucination flags, and retries.
#
# Features:
# - If hallucinations are detected (e.g., unsupported or contradictory information in the answer), 
#   the answer is flagged with a binary score ('yes' or 'no'), and a reason is logged.
# - The system also logs detailed information about retries for hallucination detection.
#
# Future Improvements:
# - Handle edge cases better by refining the hallucination criteria or improving model accuracy.
# ------------------------------

from transformers import pipeline, AutoTokenizer

import state, nodes
from utils import log_message, send_logs
import config
from config import LOGGING_SETTINGS
import uuid


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
        model="hallucination_evaluation_model-transformers-hhem-2.1-open-v1",
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

        ###### log_tree part
        # import uuid , nodes
        id = str(uuid.uuid4())
        child_node = nodes.check_hallucination_hhem.__name__ + "//" + id
        parent_node = state.get("prev_node", "START")
        if parent_node == "":
            parent_node = "START"
        log_tree = {}

        if (
            not LOGGING_SETTINGS["check_hallucination_hhem"]
            or state.get("send_log_tree_logs", "") == "False"
        ):
            child_node = parent_node

        log_tree[parent_node] = [child_node]
        ######

        ##### Server Logging part

        output_state = {
            "answer_contains_hallucinations": None,
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

    # Determine hallucination flag
    hallucination_flag = "yes" if score < 0.5 else "no"

    answer_contains_hallucinations = False

    if hallucination_flag == "yes":
        log_message(
            "---GRADE: ANSWER CONTAINS HALLUCINATIONS---",
            f"question_group{question_group_id}",
        )
        answer_contains_hallucinations = True
    else:
        log_message(
            "---GRADE: ANSWER DOES NOT CONTAIN HALLUCINATIONS---",
            f"question_group{question_group_id}",
        )

    hallucination_retries = state.get("hallucinations_retries", 0)
    hallucination_retries += 1

    ###### log_tree part
    # import uuid , nodes
    id = str(uuid.uuid4())
    child_node = nodes.check_hallucination_hhem.__name__ + "//" + id
    parent_node = state.get("prev_node", "START")
    if parent_node == "":
        parent_node = "START"
    log_tree = {}

    if (
        not LOGGING_SETTINGS["check_hallucination_hhem"]
        or state.get("send_log_tree_logs", "") == "False"
    ):
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
        "answer_contains_hallucinations": answer_contains_hallucinations,
        "hallucinations_retries": hallucination_retries,
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
