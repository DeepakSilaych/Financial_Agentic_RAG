import anthropic
import instructor
from database import *
from config import *
from pydantic import BaseModel, Field
from typing import Literal, List, Set
import os

client = instructor.from_anthropic(anthropic.Anthropic())

# os.environ["TESSDATA_PREFIX"] = "/usr/share/tesseract-ocr/4.00/tessdata"

FINANCE_TERMS_LITERALS = Literal[
    "financial_accounting",
    "managerial_accounting",
    "corporate_finance",
    "investment_management",
    "capital_markets",
    "financial_modeling",
    "valuation_techniques",
    "portfolio_management",
    "behavioral_finance",
    "risk_management",
    "banking_and_financial_institutions",
    "investment_banking",
    "central_banking_and_monetary_policy",
    "credit_analysis",
    "trade_finance",
    "payments_and_settlement_systems",
    "economic_analysis",
    "taxation_and_public_finance",
    "financial_regulation",
    "treasury_management",
    "alternative_investments",
    "derivatives_and_options",
    "quantitative_finance",
    "sustainable_finance",
    "personal_financial_planning",
    "wealth_management",
    "project_and_infrastructure_finance",
    "real_estate_finance",
    "commodities_markets",
    "cryptocurrencies_and_blockchain",
    "market_analysis_and_benchmarking",
    "financial_statement_analysis",
    "strategic_finance_and_swot_analysis",
    "big_data_and_analytics_in_finance",
    "customer_and_employee_analysis",
    "emerging_markets_and_global_finance",
]

ITEMS_10K_LITERALS = Literal[
    "item_1_business",
    "item_1a_risk_factors",
    "item_1b_unresolved_staff_comments",
    "item_2_properties",
    "item_3_legal_proceedings",
    "item_4_mine_safety_disclosures",
    "item_5_market_for_registrant_s_common_equity_related_stockholder_matters_and_issuer_purchases_of_equity_securities",
    "item_6_selected_financial_data",
    "item_7_management_s_discussion_and_analysis_of_financial_condition_and_results_of_operations",
    "item_7a_quantitative_and_qualitative_disclosures_about_market_risk",
    "item_8_financial_statements_and_supplementary_data",
    "item_9_changes_in_and_disagreements_with_accountants_on_accounting_and_financial_disclosure",
    "item_9a_controls_and_procedures",
    "item_9b_other_information",
    "item_10_directors_executive_officers_and_corporate_governance",
    "item_11_executive_compensation",
    "item_12_security_ownership_of_certain_beneficial_owners_and_management_and_related_stockholder_matters",
    "item_13_certain_relationships_and_related_transactions_and_director_independence",
    "item_14_principal_accountant_fees_and_services",
    "item_15_exhibits_financial_statement_schedules",
    "item_16_form_10k_summary",
]


class TableValuesSchema(BaseModel):
    succint_context: str = Field(
        description="A short succinct context to situate this chunk within the overall document."
    )
    listofstr: List[str] | str = Field(
        description="List of strings where each string is having description of a financial number/value from the TABLE in brief including all the context(Table name, row name, column name) it has for the value with the exact value."
    )
    topic: FINANCE_TERMS_LITERALS | Literal["Other"] | str = Field(
        description="""One topic from the following list that best describes the content of this chunk. 
        Do not create new topics or modify these options. Select the closest match from the given list.
        Only in a very rare case, if you cannot find any topic that fits this chunk, then return 'Other' but you should try to not do that in every case."""
    )
    item_10K: ITEMS_10K_LITERALS | str | None = Field(
        description="The item no. with name if it is a 10-K document otherwise None."
    )


class ListOfStrSchema(BaseModel):
    listofstr: List[str] = Field(
        description="Given a string representation of a list, return a list of strings by correctly parsing the string representation of the list."
    )


class FinanceDynamicMetadataSchema(BaseModel):
    succint_context: str = Field(
        description="A short succinct context to situate this chunk within the overall document."
    )
    topic: FINANCE_TERMS_LITERALS | Literal["Other"] | str = Field(
        description="""One topic from the following list that best describes the content of this chunk. 
        Do not create new topics or modify these options. Select the closest match from the given list.
        Only in a very rare case, if you cannot find any topic that fits this chunk, then return 'Other' but you should try to not do that in every case."""
    )
    item_10K: ITEMS_10K_LITERALS | str | None = Field(
        description="The item no. with name if it is a 10-K document otherwise None."
    )


class OtherDynamicMetadataSchema(BaseModel):
    succint_context: str = Field(
        description="A short succinct context to situate this chunk within the overall document."
    )
    topic: str = Field(
        description="One broad Topic from the list of broad topics you have assigned already to some chunks of this document, that best describes the content of this chunk. If you cannot find any topic that fits this chunk, then return a new BROAD topic that best describes the content of this chunk."
    )


def validate_and_process_finance_response(response, typetext, type):
    """Helper function to validate and process finance response."""
    if type == "10-K":
        if typetext == "table":
            keyvals = response.listofstr
            topic = response.topic
            item_10K = response.item_10K
            if not isinstance(keyvals, list):
                prompt = f"You are provided with a string which is a actually a list but represented in string format. Return the list of strings. keep all the text as it is, I just want you to convert it into a list of strings. \n Convert this: {keyvals}"
                keyvals = (
                    llm.with_structured_output(ListOfStrSchema).invoke(prompt).listofstr
                )
            if response.topic not in GLOBAL_SET_OF_FINANCE_TERMS:
                topic = "Other"
            if response.item_10K not in GLOBAL_SET_OF_10K_ITEMS:
                item_10K = "Other"
            return TableValuesSchema(
                succint_context=response.succint_context,
                listofstr=keyvals,
                topic=topic,
                item_10K=item_10K,
            )
        else:
            item_10K = response.item_10K
            topic = response.topic
            if response.topic not in GLOBAL_SET_OF_FINANCE_TERMS:
                topic = "Other"
            if response.item_10K not in GLOBAL_SET_OF_10K_ITEMS:
                item_10K = "Other"
            return FinanceDynamicMetadataSchema(
                succint_context=response.succint_context, topic=topic, item_10K=None
            )
    else:
        if typetext == "table":
            keyvals = response.listofstr
            topic = response.topic
            if not isinstance(keyvals, list):
                prompt = f"You are provided with a string which is a actually a list but represented in string format. Return the list of strings. keep all the text as it is, I just want you to convert it into a list of strings. \n Convert this: {keyvals}"
                keyvals = (
                    llm.with_structured_output(ListOfStrSchema).invoke(prompt).listofstr
                )
            if response.topic not in GLOBAL_SET_OF_FINANCE_TERMS:
                topic = "Other"
            return TableValuesSchema(
                succint_context=response.succint_context,
                listofstr=keyvals,
                topic=topic,
                item_10K=None,
            )
        else:
            # for finance type, if the topic is not in the finance terms, then set it to "Other"
            if response.topic not in GLOBAL_SET_OF_FINANCE_TERMS:
                return FinanceDynamicMetadataSchema(
                    succint_context=response.succint_context,
                    topic="Other",
                    item_10K=None,
                )
        return response


class FinanceDynamicMetadataSchema(BaseModel):
    succint_context: str = Field(
        description="A short succinct context to situate this chunk within the overall document."
    )
    topic: FINANCE_TERMS_LITERALS | Literal["Other"] | str = Field(
        description="""One topic from the following list that best describes the content of this chunk. 
        Do not create new topics or modify these options. Select the closest match from the given list.
        Only in a very rare case, if you cannot find any topic that fits this chunk, then return 'Other' but you should try to not do that in every case."""
    )
    item_10K: ITEMS_10K_LITERALS | str | None = Field(
        description="The item no. with name if it is a 10-K document otherwise None."
    )


class OtherDynamicMetadataSchema(BaseModel):
    succint_context: str = Field(
        description="A short succinct context to situate this chunk within the overall document."
    )
    topic: str = Field(
        description="One broad Topic from the list of broad topics you have assigned already to some chunks of this document, that best describes the content of this chunk. If you cannot find any topic that fits this chunk, then return a new BROAD topic that best describes the content of this chunk."
    )


DOCUMENT_CONTEXT_PROMPT = """
<document>
{doc_content}
</document>
"""

GLOBAL_SET_OF_FINANCE_TERMS_PROMPT = """
Here are some broad topics in finance with their brief descriptions
{finance_terms}
"""

SET_OF_TERMS_USED_TILL_NOW = """
Here are the broad topics that you have assigned to the chunks till now:
{topics}
If the above is empty, then you have not assigned any topics till now for any chunk of this document.
"""

FINANCE_CHUNK_CONTEXT_PROMPT = """
Here is the chunk we want to situate within the whole document
<chunk>
{chunk_content}
</chunk>

You need to give 3 things for this chunk ensure no field is left empty:
1. Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk.
2. Please give one Topic from the list of broad topics in finance with their brief explaination that best describes the content of this chunk.
If you cannot find any topic that fits this chunk, then return the closest match from the given list of topics.
4. If this chunk is from a 10-K document, then also provide the item number with name (section) in which this chunk is there in the given 10-K document.
You can look inside the provided document to find the item number with name (section) in which this chunk is there in the given 10-K document.
Also there will be one item number with name (section) in which this chunk is in so you must return that only from the provided list of item numbers in the given 10-K document.
Return any one of the item number with name from the list of item numbers in 10-K document in the given document. 

Return in FinanceDynamicMetadataSchema format."""

FINANCE_TABLE_CHUNK_CONTEXT_PROMPT = """
Here is the chunk of a table that we want to situate within the whole document
<chunk>
{chunk_content}
</chunk>

Here is the chunk just before the table chunk
<chunk>
{chunk_before_table}
</chunk>

You need to give 4 things for this chunk ensure no field is left empty:
1. Please give a short succinct context to situate this Table chunk within the overall document for the purposes of improving search retrieval of the chunk. Also include all the context for this chunk which you can get from the chunk just before the table chunk.
2. Please Identify all the Financial Numbers/Values in the table and describe them in brief including all the context(Table name, row name, column name, any other important information describing that value) it has for the value with the exact value.
Do not reference anything like 'as stated earlier' or 'as mentioned above'. Include all the context for the value in the same string.
Return a list of strings where each string is having description of a value as mentioned above.
3. Please give one Topic from the list of broad topics in finance with their brief explaination that best describes the content of this chunk.
If you cannot find any topic that fits this chunk, then return the closest match from the given list of topics.
4. If this chunk is from a 10-K document, then also provide the item number with name (section) in which this chunk is there in the given 10-K document.
You can look inside the provided document to find the item number with name (section) in which this chunk is there in the given 10-K document.
Also there will be one item number with name (section) in which this chunk is in so you must return that only from the provided list of item numbers in the given 10-K document.
Return any one of the item number with name from the list of item numbers in 10-K document in the given document. 

If the document is not a 10-K document, then return None for this field.

Return in TableValuesSchema format."""

OTHER_CHUNK_CONTEXT_PROMPT = """
Here is the chunk we want to situate within the whole document
<chunk>
{chunk_content}
</chunk>

You need to give 2 things for this chunk ensure no field is left empty:
1. Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk.
2. Please assign one broad Topic from the list of broad topics you have assigned already to some chunks of this document, that best describes the content of this chunk.
If you cannot find any topic that fits this chunk, then return a new BROAD topic that best describes the content of this chunk.

Remember you have assigned {num_topics} topics till now for the chunks of this document.
If the above number is ~ 10, then keep care of the new topics you are assigning to the chunks of this document and make them very broad so that they can be used for the future chunks of this doc as well.
If the above number is ~ 1-2, then do not worry about the new topics you are assigning to the chunks of this document and make them very specific to the content of the chunk.

Return in OtherDynamicMetadataSchema format."""


def situate_context_finance(doc: str, chunk: str, typetext: str, type: str):
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
                        "text": DOCUMENT_CONTEXT_PROMPT.format(doc_content=doc),
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": GLOBAL_SET_OF_FINANCE_TERMS_PROMPT.format(
                            finance_terms="\n".join(GLOBAL_SET_OF_FINANCE_TERMS)
                        ),
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": FINANCE_CHUNK_CONTEXT_PROMPT.format(
                            chunk_content=chunk
                        ),
                    },
                ],
            }
        ],
        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
        response_model=FinanceDynamicMetadataSchema,
    )
    # Validate and process the response
    validated_response = validate_and_process_finance_response(
        response[0], typetext, type
    )
    return [validated_response]


def situate_context_finance_table(
    doc: str, chunk: str, prev_chunk: str, typetext: str, type: str
):
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
                        "text": DOCUMENT_CONTEXT_PROMPT.format(doc_content=doc),
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": GLOBAL_SET_OF_FINANCE_TERMS_PROMPT.format(
                            finance_terms="\n".join(GLOBAL_SET_OF_FINANCE_TERMS)
                        ),
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": FINANCE_TABLE_CHUNK_CONTEXT_PROMPT.format(
                            chunk_content=chunk, chunk_before_table=prev_chunk
                        ),
                    },
                ],
            }
        ],
        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
        response_model=TableValuesSchema,
    )
    # Validate and process the response
    validated_response = validate_and_process_finance_response(
        response[0], typetext, type
    )
    return [validated_response]


def situate_context_others(doc: str, chunk: str, set_of_topics: Set[str]):
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
                        "text": DOCUMENT_CONTEXT_PROMPT.format(doc_content=doc),
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": SET_OF_TERMS_USED_TILL_NOW.format(
                            topics="\n".join(set_of_topics)
                        ),
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": OTHER_CHUNK_CONTEXT_PROMPT.format(
                            chunk_content=chunk, num_topics=len(set_of_topics)
                        ),
                    },
                ],
            }
        ],
        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
        response_model=OtherDynamicMetadataSchema,
    )
    return response


def make_succinct_context_for_value(company_name: str, year: str, type: str):
    if type == "10-K" or type == "10-Q":
        if company_name and year:
            return f"This value is from a {type} report of {company_name} for the year {year}."
        elif company_name:
            return f"This value is from a {type} report of {company_name}."
        elif year:
            return f"This value is from a {type} report for the year {year}."
        else:
            return f"This value is from a {type} report."
    else:
        if company_name and year:
            return f"This value is from a finance-related document of {company_name} for the year {year}."
        elif company_name:
            return f"This value is from a finance-related document of {company_name}."
        elif year:
            return f"This value is from a finance-related document for the year {year}."
        else:
            return "This value is from a finance-related document."
