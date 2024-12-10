import anthropic
import instructor
from pydantic import BaseModel, Field
from typing import Literal
from database import *
from config import *
import os
from langchain.chat_models import ChatOpenAI

client = instructor.from_anthropic(anthropic.Anthropic())
db = FinancialDatabase()
llm = ChatOpenAI(model="gpt-4o")

class ListofKeyValues(BaseModel):
    listofstr: list[str] = Field(
        description="List of strings where each string is a detailed description of some value."
    )


class StaticStatementSchema(BaseModel):
    """
    The schema for the financial statement metadata.
    """

    type: Literal["10-K", "10-Q", "Finance", "Legal", "Other"] | str | None = Field(
        description="The type of the Financial Statement."
    )
    company_name: str | None = Field(
        description="The name of the company. If not present, return None."
    )
    year: str | None = Field(
        description="The year of the financial statement if present, ex: '2021' in string format. If not present or for any other type of document, return None."
    )
    quarter: Literal["Q1", "Q2", "Q3"] | str | None = Field(
        description="The quarter of the report if it is 10-Q financial statement otherwise None."
    )


static_metadata_prompt = """First, identify the following things of document from the given document's first 10 pages in the following way:
First identify the type of the document as follows:
If the document is a 10-K, (i.e something like 'FORM 10-K' must be there on a title of some page) then return '10-K'.
If the document is a 10-Q, (i.e something like 'FORM 10-Q' must be there on a title of some page) then return '10-Q'.
If the document is finance-related in any way and not a 10-K or 10-Q, then return 'Finance'.
If the document is none of the above then only, check if it is related to legal matters in any small aspect also then return 'Legal'.
If the document does not belong to any of the above categories then return 'Other'.

Then extract the company name from the document(It must be present if it is a 10-K, 10-Q or Finance type else return None).
Only extract the company name do not include any Suffixes. Like:
"Company Name: Google LLC" should be extracted as "google" only.
"Company Name: Amazon.com, inc" should be extracted as "amazon" only.
"Company Name: Nike, Inc." should be extracted as "nike" only.
And so on.
If the company name is one of the following then return the company name as mentioned below otherwise return the company name as you extracted from the document.
{companies}

Extract the year from the document(It must be present if it is a 10-K, 10-Q or Finance type else return None). 
The year should be extracted in the format of 'YYYY' as a string. If the year is mentioned in the document as '2021' then extract it as '2021'.
If the year is not present then return None.

If the document is a 10-Q, extract the quarter as well. Else return None for the quarter.
Example:"... ended April 1, ..." or "... ended March 31, ..." should be extracted as "Q1".
        "... ended July 1, ..." or "... ended June 30, ..." should be extracted as "Q2".
        "... ended October 1, ..." or "... ended September 30, ..." should be extracted as "Q3".
Note: There is no Q4 in 10-Q reports.

Return the extracted information in the StaticStatementSchema format.
"""

DOCUMENT_CONTEXT_PROMPT = """
<document>
{doc_content}
</document>
"""


def extract_static_metatdata(nodes: list):
    """
    Extracts static metadata from the document.
    """
    nodes_first_10_pages = []
    for node in nodes:
        if len(node.bbox) > 0 and node.bbox[0].page < 10:
            nodes_first_10_pages.append(node)
    document_first_10_page_text = "\n".join(node.text for node in nodes_first_10_pages)

    response = client.chat.completions.create_with_completion(
        model="claude-3-haiku-20240307",
        max_tokens=4096,
        temperature=0.0,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": DOCUMENT_CONTEXT_PROMPT.format(
                            doc_content=document_first_10_page_text
                        ),
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": static_metadata_prompt.format(
                            companies=db.get_companies()
                        ),
                    },
                ],
            }
        ],
        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
        response_model=StaticStatementSchema,
    )
    response = response[0]

    if response.type:
        type = response.type
        if type not in ["10-K", "10-Q", "Finance", "Legal", "Other"]:
            type = "Other"
    else:
        type = "Other"

    if response.company_name:
        company_name = response.company_name
    else:
        company_name = None

    if response.year:
        year = response.year
    else:
        year = None

    if response.quarter:
        quarter = response.quarter
        if quarter not in ["Q1", "Q2", "Q3"]:
            quarter = None
    else:
        quarter = None

    return type, company_name, year, quarter

def extract_static_metadata_using_openai(nodes: list):
    """
    Extracts static metadata from the document.
    """
    nodes_first_10_pages = []
    for node in nodes:
        if len(node.bbox) > 0 and node.bbox[0].page < 10:
            nodes_first_10_pages.append(node)
    document_first_10_page_text = "\n".join(node.text for node in nodes_first_10_pages)

    response = llm.with_structured_output(StaticStatementSchema).invoke(
        DOCUMENT_CONTEXT_PROMPT.format(doc_content=document_first_10_page_text) + "\n" + static_metadata_prompt.format(companies=db.get_companies())
    )

    if response.type:
        type = response.type
        if type not in ["10-K", "10-Q", "Finance", "Legal", "Other"]:
            type = "Other"
    else:
        type = "Other"

    if response.company_name:
        company_name = response.company_name
    else:
        company_name = None

    if response.year:
        year = response.year
    else:
        year = None

    if response.quarter:
        quarter = response.quarter
        if quarter not in ["Q1", "Q2", "Q3"]:
            quarter = None
    else:
        quarter = None

    return type, company_name, year, quarter