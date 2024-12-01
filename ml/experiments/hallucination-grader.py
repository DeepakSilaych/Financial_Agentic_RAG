from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
import state
from llm import llm
from utils import log_message


class HallucinationGrade(BaseModel):
    """Binary score for hallucination check on generated answers."""

    binary_score: str = Field(
        description="Answer contains hallucination, 'yes' or 'no'"
    )


class HallucinationGraderInput(BaseModel):
    answer: str
    supporting_documents: str


_system_prompt = """You are a grader assessing if the generated answer contains hallucinations based on the supporting documents.
Your task is to check if the generated answer is consistent with the information present in the supporting documents.

1. Hallucination not present
- Minor paraphrasing, inferred conclusions, or rephrased content should not be flagged as hallucinations as long as the key facts and information align with the documents.
- The answer might contain information that is inferred from multiple lines in the context.
- Be slightly lenient in grading hallucination for answers with numbers when words like 'around' , 'approx' are used in the answer. 

2. Hallucination Present
- Only label the answer as hallucinated if it contains claims that are **completely different**, unsupported, or contradicted by the supporting documents.
- If the answer makes any factual claims or includes details not present in the documents, or if it contradicts the evidence provided, then it should be flagged as hallucinated.


Provide a binary score 'yes' or 'no' to indicate whether the answer contains hallucinations:
- if 'yes' add a reason for the hallucination in the string. 
- 'no' if it aligns well with the supporting documents even if paraphrased.

"""

hallucination_grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt),
        (
            "human",
            "Generated answer: \n\n {answer} \n\n Supporting documents: {supporting_documents}",
        ),
    ]
)

hallucination_grader = hallucination_grade_prompt | llm


def grade_hallucinations(answer, supporting_documents):
    """
    Determines whether the generated answer contains hallucinations based on supporting documents.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates answer with a hallucination flag if hallucinations are detected
    """
    # question_group_id = state.get("question_group_id", 1)
    # log_message("---CHECK GENERATED ANSWER FOR HALLUCINATIONS---", f"question_group{question_group_id}")
    # answer = state["answer"]
    # try:
    #     print(state["documents"])
    #     supporting_documents = " ".join([doc.page_content for doc in state["documents"]])
    # except:
    #     supporting_documents = " ".join([" ".join(doc) for doc in state["documents"]])
    # supporting_documents = " ".join([doc.page_content for doc in state["documents"]])

    # Score the answer
    score = hallucination_grader.invoke(
        {"answer": answer, "supporting_documents": supporting_documents}
    )
    # hallucination_flag = score.binary_score  # type: ignore

    print(score)

    # if hallucination_flag == "no":
    #     # log_message("---GRADE: ANSWER CONTAINS HALLUCINATIONS---", f"question_group{question_group_id}")
    #     answer_contains_hallucinations  = False
    # else:
    #     # log_message("---GRADE: ANSWER DOES NOT CONTAIN HALLUCINATIONS---", f"question_group{question_group_id}")
    #     answer_contains_hallucinations  = True
    #     print( )

    # state["hallucinations_retries"] = state.get("hallucinations_retries", 0)
    # state["hallucinations_retries"] += 1
    # state["prev_node"] = hallucination_grader.__name__
    # print(answer_contains_hallucinations)

    return


answer = "The revenue of apple is approximately 144 billion dollars"
# answer = "The revenue of google more than 148 billion dollars."

supporting_documents = "The revenue of google is $148.21 billion. The revenue of apple is 4 billion dollars less than google. "

grade_hallucinations(answer, supporting_documents)
