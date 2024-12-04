from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

import state, nodes
from llm import llm
import uuid
from dotenv import load_dotenv
load_dotenv()
from utils import send_logs
from config import LOGGING_SETTINGS

class DocumentGrade(BaseModel):
    """Binary score and reason for relevance check on retrieved documents."""

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'."
    )
    reason: str = Field(
        description="A brief reason explaining why the document is relevant or irrelevant."
    )


class DocumentGraderInput(BaseModel):
    question: str
    document: str


_system_prompt = """You are a grader assessing relevance of a retrieved document to a user question. \n 
    If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
    It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
    While (irrelevant documents marked as relevant) are acceptable, (relevant documents marked as irrelevant) must be avoided at all costs.\n
    Provide a simple binary score: "yes" for relevant and "no" for irrelevant.\n
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""
grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt),
        ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
    ]
)
document_grader = grade_prompt | llm.with_structured_output(DocumentGrade)


def grade_document(question, document):
    """
    Helper function to grade a single document.
    """
    score = document_grader.invoke(
        {"question": question, "document": document.page_content}
    )
    return {"grade": score.binary_score, "reason": score.reason, "document": document}


def grade_documents(state: state.InternalRAGState):
    """
    Determines whether the retrieved documents are relevant to the question and collects reasons for irrelevance.

    Args:
        state (dict): The current graph state.

    Returns:
        state (dict): Updates documents key with only filtered relevant documents and includes reasons for irrelevance.
    """

    question = state["original_question"]
    documents = state["documents"]
    doc_grading_retries = state.get("doc_grading_retries", 0)

    # Sending all chunks for relevance grading parallely to improve efficiency
    with ThreadPoolExecutor() as executor:
        results = list(
            executor.map(lambda doc: grade_document(question, doc), documents)
        )

    filtered_docs = [res["document"] for res in results if res["grade"] == "yes"]
    reasons = [res["reason"] for res in results if res["grade"] == "no"]

    concatenated_reasons = " | ".join(reasons)
    # documents_kv = state.get("documents_with_kv", [])
    # filtered_docs.extend(documents_kv)


    ###### log_tree part
    # import uuid , nodes 
    id = str(uuid.uuid4())
    child_node = nodes.grade_documents.__name__ + "//" + id
    parent_node = state.get("prev_node" , "START")
    log_tree = {}
    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    if not LOGGING_SETTINGS['grade_documents']:
        child_node = parent_node  

    output_state = {
        "documents": filtered_docs,
        "irrelevancy_reason": concatenated_reasons,
        "doc_grading_retries": doc_grading_retries + 1,
        "prev_node" : child_node,
        "log_tree" : log_tree ,
    }


    send_logs(
        parent_node = parent_node , 
        curr_node= child_node , 
        child_node=None , 
        input_state=state , 
        output_state=output_state , 
        text=child_node.split("//")[0] ,
    )
    
    ######

    return output_state 