# This module is responsible for detecting if any critical information is missing from the retrieved documents 
# that would prevent sufficiently answering the user's query.

# Key Functions:
# - detect_missing_info: This function checks if the documents retrieved during the information retrieval 
#   process contain enough details to sufficiently answer the user's query. It utilizes the LLM and a 
#   pre-defined system prompt to assess the sufficiency of the information and identify any missing details.

# Data Models:
# - MissingInfo: Model to structure the output of the missing information detection, including 
#   a sufficiency indicator ("sufficient" or "insufficient") and a list of missing information, if any.

# The module integrates LangChain for structured prompts and responses from the LLM and logs the results 
# for further analysis or actions.

from typing import List
from prompt import prompts
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


_system_prompt = prompts.missing_info_system_prompt
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
