from typing import List, Optional, Dict, Literal

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from utils import log_message
from database import FinancialDatabase
import config
import state , nodes
from llm import llm
import uuid
from config import GLOBAL_SET_OF_FINANCE_TERMS

from utils import send_logs , tree_log
from config import LOGGING_SETTINGS


class QueryMetadata(BaseModel):
    """Metadata structure for parsing relevant 10-K report details from user queries."""

    company_name: Optional[str] = Field(
        description="Matched exact Parent Company Name from the Parent Company List if specified in the query"
    )
    filing_year: Optional[str] = Field(
        description="Filling year for the document (e.g. 2022) if specified in the query"
    )
    # topics: List[str] = Field(
    #     default=[],
    #     description="Key topics of interest (e.g., revenue, net income, risk factors, ESG)",
    # )

class QueryMetadata_QQ(BaseModel):
    """Metadata structure for parsing relevant 10-K report details from user queries."""

    company_name: Optional[str] = Field(
        description="Matched exact Parent Company Name from the Parent Company List if specified in the query"
    )
    filing_year: Optional[str] = Field(
        description="Filling year for the document (e.g. 2022) if specified in the query"
    )
    category: Literal['Quantitative', 'Qualitative'] = Field(
        description="The category of the question: either 'Quantitative' or 'Qualitative'."
    )
    # topics: List[str] = Field(
    #     default=[],
    #     description="Key topics of interest (e.g., revenue, net income, risk factors, ESG)",
    # )

_system_prompt_old = """You are a metadata extractor for financial queries focusing on 10-K reports. 
Extract relevant metadata to make retrieval more accurate.
Identify key information such as:
1. Company name 
2. Filing Year of the document (Make sure to output only 1 year and not a range)

Respond with the metadata in a structured format.
"""
_system_prompt = """
You are a metadata extractor for financial queries focusing on 10-K reports. 
Your goal is to extract relevant metadata to make retrieval more accurate.

Key tasks:
1. Identify the **Parent Company Name**:
   - The company name in the query may not always refer to the parent company.
   - Match the company name mentioned in the query to the **parent company** in the provided list of parent companies (`company_set`).
   - Use the context of the query to determine which parent company the mentioned company belongs to.
   - Ensure that the output is an **exact match** with one of the parent company names in the provided list.
   - If no match is found or the company cannot be linked to a parent company in the list, set "company_name" to None.

2. Extract the **Filing Year**:
   - Identify the filing year of the document.
   - Ensure the output contains only **one specific year** (e.g., `2023`) and not a range or ambiguous dates.
   - In case of relative terms like last year , present year , next year . Use this information : ( Present year is 2024 )
   - If there are more than 1 years in the question , then take the most recent year ( Present year is 2024 )
   - If no filing year is identified, set "filing_year" to "None".

Respond with the metadata in a structured format.

List of parent companies provided:
{company_set}
"""

prompt_qq = """
You are a metadata extractor for financial queries focusing on 10-K reports. 
Your goal is to extract relevant metadata to make retrieval more accurate.

Key tasks:
1. Identify the **Parent Company Name**:
   - The company name in the query may not always refer to the parent company.
   - Match the company name mentioned in the query to the **parent company** in the provided list of parent companies (`company_set`).
   - Use the context of the query to determine which parent company the mentioned company belongs to.
   - Ensure that the output is an **exact match** with one of the parent company names in the provided list.
   - If no match is found or the company cannot be linked to a parent company in the list, set "company_name" to None.

2. Extract the **Filing Year**:
   - Identify the filing year of the document.
   - Ensure the output contains only **one specific year** (e.g., `2023`) and not a range or ambiguous dates.
   - If no filing year is identified, set "filing_year" to "None".

3. Classify user questions into one of the following categories:
1. **Quantitative**: Questions that require numerical data, tables, charts, or figures in the reports for an answer.
2. **Qualitative**: Questions that involve interpreting textual content, such as management discussions, business strategies, or narrative descriptions.
### NOTE ###
If you are unsure about category direct it to Quantitative Category.

Respond with the metadata in a structured format.
{{
    company_name : <parent company name>,
    filing_year : <year>,
    category : <Quantitative/Qualitative>
}}

List of parent companies provided:
{company_set}
"""
metadata_extraction_prompt = ChatPromptTemplate.from_messages(
    [("system", _system_prompt), ("human", "Query: {query}")]
)
metadata_extractor = metadata_extraction_prompt | llm.with_structured_output(
    QueryMetadata
)

metadata_extraction_with_qq_prompt = ChatPromptTemplate.from_messages(
    [("system", _system_prompt), ("human", "Query: {query}")]
)
metadata_extractor_qq = metadata_extraction_with_qq_prompt | llm.with_structured_output(
    QueryMetadata_QQ
)


def extract_metadata_1(state: state.InternalRAGState):
    """
    Extract metadata from the user query to optimize document retrieval.
    """
    question_group_id = state.get("question_group_id", 1)
    question = state["question"]
    log_message(f"---QUERY: {question}", f"question_group{question_group_id}")

    ## Extracting this for db state
    db = FinancialDatabase()

    companies_set = db.get_companies()

    extracted_metadata = metadata_extractor.invoke(
        {"query": question, "company_set": companies_set}
    )

    # Unpack metadata for easy access
    company_name = extracted_metadata.company_name
    filing_year = extracted_metadata.filing_year

    log_message(
        "------"
        f"Extracted Metadata - company_name: {company_name}, year: {filing_year}",
        f"question_group{question_group_id}",
    )
    

    return {
        "metadata": {
            "company_name": company_name,
            "year": filing_year,
            # "topics": topics,
        },
    }


class ExtractedTopicsOutput(BaseModel):
    topics: List[str] = Field(
        description="List of topics extracted from the query. Topics must be exact strings from the predefined topics set."
    )


_topic_extraction_prompt1 = ChatPromptTemplate.from_template(
    """
You are a Finance Expert. 
You are given a list of topics : "Topics_set" and a question : "query". You need to which top 3 topics in the topics_set correspond most closely to what the query is asking.
Make sure that all topics ( List of strings ) are selected from the topics_set below. No topic in the output should be outside topics_set.     

Topics_set = {topics_set}

- Given the query, return a structured output with a **list of strings** containing exactly the topics that are most relevant to the query. 
- No topic in the output should be outside topics set.                                                  
- If no topic matches, return an empty list. The output should contain only the topics that appear in the provided set, no other topics should be included.
                                                            

Query: {query}
"""
)

_topic_extraction_prompt2 = ChatPromptTemplate.from_template(
    """
You are a Finance Expert.
You are given a list of topics: "Topics_set" and a question: "query". Your task is to identify the top 3 topics in the "Topics_set" that most closely correspond to what the query is asking.

### Instructions:
- Make sure all topics are selected **from the Topics_set** provided below.
- No topic should appear in the output that is not in the Topics_set.
- You are to **rank** the top 3 topics that are most relevant to the query based on the closeness to the content of the query.
- If fewer than 3 topics are relevant, return only those topics that match.
- If no topics match, return an empty list.

### Output Format:                                                           
- The output should be a **list of strings** containing exactly the topics from the `Topics_set` that are most relevant to the query. 
- The order of topics should represent their relevance to the query (most relevant topics first).
- No other topics should be included in the output.
- If no topics match, return an empty list.
                                                             
Example Output : 
{{
    [<topic1>,<topic2>,<topic3>]
}}
                                                                                                                         

**Topics_set**: {topics_set}

**Query**: {query}

"""
)

# topic_extraction_prompt = ChatPromptTemplate.from_messages(
#         [("system", _topic_extraction_prompt), ("human", "Query: {query}\nTopics Set: {topics_set}")]
#     )

topic_extractor = _topic_extraction_prompt2 | llm.with_structured_output(
    ExtractedTopicsOutput
)


def extract_topics(query: str, topics_set: set) -> List[str]:
    """
    Extract the top topics from the query using the provided set of topics.
    Ensures that the topics returned are only from the provided topics set.

    Args:
    - query (str): The user query.
    - topics_set (set): Set of topics to choose from.

    Returns:
    - List[str]: Topics that best match the query, ensuring they are from the topics set.
    """

    topics_str = ", ".join(topics_set)

    extracted_topics = topic_extractor.invoke(
        {"query": query, "topics_set": topics_str}
    )

    topics_list = extracted_topics.topics  # structured output is a list of strings

    log_message(f"\n\n topics_list : {topics_list} \n\n")
    # Fallback handling: If topics_list is not a list, default to an empty list
    if not isinstance(topics_list, list):
        log_message(
            f"Warning: Expected a list of topics, but received: {type(topics_list)}"
        )
        topics_list = []
        # return None

    valid_topics = [topic for topic in topics_list if topic in topics_set]

    return valid_topics


def extract_metadata(state: state.InternalRAGState):
    """
    Extract metadata from the user query ( company_name , year , ) to optimize document retrieval.
    """
    question_group_id = state.get("question_group_id", 1)
    query = state["question"]
    log_message(f"---QUERY: {query}, question_group{question_group_id}", question_group_id)

    ## Extracting this for db state
    db = FinancialDatabase()

    companies_set = db.get_companies()

    extracted_metadata = metadata_extractor_qq.invoke(
        {"query": query, "company_set": companies_set}
    )

    # Unpack metadata for easy access
    company_name = extracted_metadata.company_name
    filing_year = extracted_metadata.filing_year
    category = extracted_metadata.category

    #metadata = {"company_name": company_name, "year": filing_year}
    # topics_union_set = db.get_union_of_topics(metadata , GLOBAL_SET_OF_FINANCE_TERMS)
    state["topics_union_set"] = GLOBAL_SET_OF_FINANCE_TERMS

    valid_topics = extract_topics(
        query, GLOBAL_SET_OF_FINANCE_TERMS
    )  # would be a list / empty list

    log_message(
        "------"
        f"Extracted Metadata - company_name: {company_name}, year: {filing_year}, Category: {category}"
        f"question_group{question_group_id}",
    )

    ###### log_tree part
    # import uuid , nodes 
    id = str(uuid.uuid4())
    child_node = nodes.extract_metadata.__name__ + "//" + id
    parent_node = state.get("prev_node" , "START")
    log_tree = {}
    # tree_log(f"send_Log_tree_logs : {state['send_log_tree_logs']}",1)
    if not LOGGING_SETTINGS['extract_metadata'] or state.get("send_log_tree_logs" , "") == "False":
        child_node = parent_node 

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part
    output_state =  {
        "question": query,
        "metadata": {
            "company_name": company_name,  # name_string / "None" / None
            "year": filing_year,  # year_string / "None" / None
            "topics": valid_topics,  # list / empty list
        },
        "category" : category,
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


# class CompanyYearMetadata(BaseModel):
#     """Metadata structure for extracting company and year pairs from user queries."""
#     company_name: Optional[str] = Field(
#         description="Name of the company (if specified in the query)"
#     )
#     filing_date_range: Optional[str] = Field(
#         description="Time period or date range relevant to the filing (e.g., 2021-2023)"
#     )


# _system_prompt_for_pairs = """You are a metadata extractor for financial queries focusing on 10-K reports.
# Your task is to extract and return pairs of companies and their respective filing years or date ranges.
# For example:
# - Query: "Summarize Apple's revenue for 2022 and Microsoft's financials for 2021-2023"
#   Response: [{"company_name": "Apple", "filing_date_range": "2022"}, {"company_name": "Microsoft", "filing_date_range": "2021-2023"}]

# Return a structured JSON list of key-value pairs with the company name and year/date range.
# """

# metadata_extraction_prompt_for_pairs = ChatPromptTemplate.from_messages(
#     [("system", _system_prompt_for_pairs), ("human", "Query: {query}")]
# )
# metadata_extractor_for_pairs = metadata_extraction_prompt_for_pairs | llm.with_structured_output(
#     CompanyYearMetadata
# )


# def extract_company_year_pairs(state: state.InternalRAGState):
#     """
#     Extracts a list of key-value pairs containing the company and filing year(s)
#     from the user query.

#     Args:
#         query (str): The user query containing companies and years.

#     Returns:
#         List[Dict[str, str]]: A list of dictionaries, each with 'company_name' and 'filing_date_range'.
#     """
#     query = state["question"]

#     extracted_pairs = metadata_extractor_for_pairs.invoke({"query": query})


#     result = [
#         {"company_name": pair.company_name, "filing_date_range": pair.filing_date_range}
#         for pair in extracted_pairs
#     ]

#     log_message(f"Extracted Company-Year Pairs: {result}")

#     state["extracted_company_year"] = result
#     return state
