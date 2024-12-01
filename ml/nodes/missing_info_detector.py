from typing import List

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

import state
from llm import llm
from utils import log_message


class MissingInfo(BaseModel):
    """Detects if there is missing information in retrieved documents to sufficiently answer the query."""

    sufficiency: str = Field(
        description="Indicate if the documents are sufficient to answer the question, 'sufficient' or 'insufficient'"
    )
    missing_info: List[str] = Field(
        default=[],
        description="List key pieces of missing information necessary to fully answer the question, if any",
    )


_system_prompt = """You are an evaluator determining if the retrieved documents provide sufficient information to answer the user question.\n
    If the documents contain enough information to answer the question, classify them as 'sufficient.'\n
    If critical information is missing to answer the question, classify as 'insufficient' and list the missing elements briefly.\n
    Aim to capture any gaps in data that prevent a complete answer to the user question."""
grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt),
        ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
    ]
)
missing_info_detector = grade_prompt | llm.with_structured_output(MissingInfo)


def detect_missing_info(state: state.InternalRAGState) -> state.HIL_State:
    """
    Determines whether the retrieved documents contain enough information to answer the question
    """
    log_message("---CHECK IF ANY DATA IS MISSING---")
    question = state["question"]
    documents = state["documents"]
    detector_output = missing_info_detector.invoke(
        {"question": question, "documents": documents}
    )
    if detector_output.sufficiency == "insufficient":
        missing_info = detector_output.missing_info
        log_message("---RETRIEVED DOCUMENTS ARE NOT SUFFICIENT TO ANSWER THE QUERY---")
        for m in missing_info:
            log_message("MISSING INFO :", m)
        return {
            "HIL": True,
            "missing_info": missing_info,
        }
    else:
        return {"HIL": False}
