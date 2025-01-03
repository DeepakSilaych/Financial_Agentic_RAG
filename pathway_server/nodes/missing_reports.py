import state

from langchain_core.prompts import ChatPromptTemplate
from llm import llm
import json

# TODO : refined_query -> extract company year pairs -> check availability -> HIL dalo
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from prompt import prompts
# from typing import List, Dict
# from langchain_core.prompts import ChatPromptTemplate
from utils import log_message
from database import FinancialDatabase
import state
from llm import llm
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import requests
import pdfkit

from utils import send_logs
from config import LOGGING_SETTINGS
import uuid, nodes

load_dotenv()
with open("experiments/kpis/kpis.json") as f:
    data = json.load(f)
available_financial_analyses = "\n".join(
    [f"\t{n+1}. {val['topic']}" for n, val in enumerate(data)]
)

db = FinancialDatabase()
company_year_data = ", ".join(
    [
        f"({d['company_name']}, {d['filing_year']})"
        for d in db.get_all_company_year_pairs()
    ]
)


class AnalysisSuggestion(BaseModel):
    analysis_suggestions: Optional[List[str]] = Field(
        default=None,
        description="Suggest specific types of analysis to be done for answering the query and ask/confirm with the user",
    )


_system_prompt_for_analysis_suggestion = f"""You are a query evaluator tasked with deciding whether the query requires some financial analysis to be performed or not.
The types of Financial Analysis that can be performed are:
{available_financial_analyses}

If the query does not need any such analysis and can be directly answered from retrieval without reasoning, respond with an **EMPTY** list.
Otherwise, if answering the query REQUIRES any type of Financial Analysis from the above list, then output a **Ordered List** of **Financial Analysis in Order of Relevance** from the **most relevant analysis to least relevant** that can be performed on the query.
Note that the number of elements of this list should be *16* and sorted such that *Most important Analysis* types are in the beginning.

    Here are a few examples:

---

**Example 1:**
**User Query:** *"What was the R&D expenditure of Google in 2021?"*  
**Response:**  
    No Financial Analysis Needed

---

**Example 2:**
**User Query:** *"How has Tesla's debt strategy evolved over the past five years, and what impact does it have on the company's solvency and future growth?"*  
**Response:**  
    1. "Debt Management Analysis"
    2. "Solvency Analysis"
    3. "Trend Analysis"
    4. "Scenario Analysis"
    5. "Liquidity Analysis"
    6. "Capital Structure Analysis"
    7. "Risk Analysis"
    8. "Valuation Analysis"
    9. "Profitability Analysis"
    10. "Balance Sheet Reviews"
    11. "Income Statement Reviews"
    12. "Cashflow Analysis"
    13. "SWOT Analysis"
    14. "Break Even Analysis"
    15. "Efficiency Analysis"
    16. "Customer Lifetime Value Analysis"

---

**Example 4:**
**User Query:** *"What are Amazon's key drivers of profitability, and how do operating expenses contribute to or detract from its growth?"*  
**Response:**  
    1. "Profitability Analysis"
    2. "Income Statement Reviews"
    3. "Efficiency Analysis"
    4. "Trend Analysis"
    5. "SWOT Analysis"
    6. "Risk Analysis"
    7. "Valuation Analysis"
    8. "Working Capital Analysis"
    9. "Cashflow Analysis"
    10. "Scenario Analysis"
    11. "Liquidity Analysis"
    12. "Balance Sheet Reviews"
    13. "Capital Structure Analysis"
    14. "Customer Lifetime Value Analysis"
    15. "Debt Management Analysis"
    16. "Break Even Analysis"

---

**Example 5:**
**User Query:** *"How has Microsoft's working capital management supported its operational growth and market expansion?"*  
**Response:**  
    1. "Working Capital Analysis"
    2. "Balance Sheet Reviews"
    3. "Liquidity Analysis"
    4. "Efficiency Analysis"
    5. "Trend Analysis"
    6. "Cashflow Analysis"
    7. "Profitability Analysis"
    8. "Scenario Analysis"
    9. "SWOT Analysis"
    10. "Risk Analysis"
    11. "Valuation Analysis"
    12. "Income Statement Reviews"
    13. "Capital Structure Analysis"
    14. "Break Even Analysis"
    15. "Debt Management Analysis"
    16. "Customer Lifetime Value Analysis"

---

**Example 6:**
**User Query:** *"What is average net income of Google over past 3 years?"*  
**Response:**  
    No Financial Analysis Needed

---

**Example 7:**
**User Query:** *"How does Apple's capital structure balance equity and debt, and how does it influence shareholder returns?"*  
**Response:**  
    1. "Capital Structure Analysis"
    2. "Valuation Analysis"
    3. "Debt Management Analysis"
    4. "Profitability Analysis"
    5. "Solvency Analysis"
    6. "Scenario Analysis"
    7. "Trend Analysis"
    8. "Risk Analysis"
    9. "Balance Sheet Reviews"
    10. "Liquidity Analysis"
    11. "SWOT Analysis"
    12. "Cashflow Analysis"
    13. "Efficiency Analysis"
    14. "Income Statement Reviews"
    15. "Working Capital Analysis"
    16. "Break Even Analysis"
---

Now, given the following user query, generate list of types of financial analysis required:"""

analysis_suggestion_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt_for_analysis_suggestion),
        ("human", "**User Query:** *{query}"),
    ]
)
analysis_suggestion_generator = analysis_suggestion_prompt | llm.with_structured_output(
    AnalysisSuggestion
)


def type_of_analysis(question):
    topics = analysis_suggestion_generator.invoke(
        {"query": question}
    ).analysis_suggestions
    return topics


class CompanyYearPair(BaseModel):
    """Represents a single company-year pair."""

    company_name: str = Field(
        ...,
        description="Name of the parent company for the company mentioned in the query.",
    )
    filing_year: Optional[str] = Field(
        None, description="Filing year for the company. Can be None if not specified."
    )


class CompanyYearPairsOutput(BaseModel):
    """Represents the structured output for company-year pairs."""

    company_year_pairs: List[CompanyYearPair] = Field(
        ..., description="A list of company-year pairs extracted from the user query."
    )


_company_year_extraction_prompt = prompts._company_year_extraction_prompt 


extraction_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _company_year_extraction_prompt),
        (
            "human",
            "Query: {query} \n\n Note : Present year is 2024 . ( Use this to extract year for relative terms like : this year , last year ,  next year etc.)",
        ),
    ]
)
company_year_extractor = extraction_prompt | llm.with_structured_output(
    CompanyYearPairsOutput
)


def extract_company_year_pairs(query):
    """
    Extracts a list of company-year pairs from the user's refined query.
    The query may explicitly mention the companies and their corresponding years.

    Args:
        state (state.InternalRAGState): The internal state containing the refined query.

    Returns:
        CompanyYearPairsOutput: The structured output containing the company-year pairs.
    """

    extracted_pairs = company_year_extractor.invoke({"query": query}).company_year_pairs

    if not isinstance(extracted_pairs, list):
        log_message(
            f"Warning: Unexpected output type for company-year extraction: {type(extracted_pairs)}"
        )
        extracted_pairs = []

    return extracted_pairs


def google_search(query, num_results=5):
    # Google Search URL with the query
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num={num_results}"

    # Set a User-Agent to mimic a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }

    # Send the HTTP request to Google
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        log_message("Failed to fetch search results.")
        return None

    # Parse the HTML content
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract the first valid SEC link ending with `.htm`
    for link in soup.find_all("a", href=True):
        href = link.get("href")
        if "sec.gov/Archives/edgar/data" in href and href.endswith(".htm"):
            if href.startswith("/url?q="):
                href = href.split("/url?q=")[1].split("&")[0]
            log_message(f"Found SEC link: {href}")
            return href

    log_message("No valid SEC link found.")
    return None


def convert_url_to_pdf(url, company, year):
    # Folder to save reports
    save_folder = os.path.join(os.getcwd(), "financial_reports")
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    try:
        # File name for the PDF
        filename = f"{company}_{year}_10K.pdf".replace(" ", "_")
        filepath = os.path.join(save_folder, filename)

        # Convert URL directly to PDF
        pdfkit.from_url(url, filepath)

        log_message(f"Document saved at: {filepath}")
        return filepath
    except Exception as e:
        log_message(f"Error converting URL to PDF: {e}")
        return None


# Main agent function to handle the process
def financial_report_agent(company, year):
    # Extract company and year from the prompt
    # company, year = extract_company_and_year(prompt)
    log_message(f"-------- SEARCHING FOR 10K Report of {company} , {year} --------")

    if not company or not year or company.lower() == "none" or year.lower() == "none":
        log_message(f"-------- Company Name or Year Missing --------")
        return

    if int(year) > 2023:
        log_message(
            f"-------- 10 K REPORT NOT FILLED YET FOR : {company} , {year}  --------"
        )
        return

    # Search for SEC 10-K reports
    query = f"{company} 10k {year} site:sec.gov/Archives/edgar/data"
    url = google_search(query)

    if not url:
        log_message(
            f"----- No valid links found in search results for {company} , {year} ------"
        )
        return

    # Attempt to convert the first valid document to PDF
    file_path = convert_url_to_pdf(url, company, year)
    if file_path:
        log_message(f"----- Successfully downloaded {file_path} ------", 1)
    else:
        log_message(
            f"----- Failed to download 10 k report for {company} , {year} ------", 1
        )


def identify_missing_reports(state: state.OverallState):
    """
    Identifies company-year pairs mentioned in the user's query that are missing in the knowledge base.
    Returns a list of company-year pairs that are not found in the knowledge base.

    Args:
        query (str): The user query containing company-year pairs.

    Returns:
        list: A list of dictionaries representing missing company-year pairs.
    """
    log_message("---- EXTRACTING MISSING DOCUMENT DETAILS ----", 1)
    db = FinancialDatabase()

    query = state["question"]
    topics = type_of_analysis(query)
    company_set_1 = db.get_all_company_year_pairs()
    company_set_2 = extract_company_year_pairs(query)
    combined_metadata = []
    for pair in company_set_2:
        combined_metadata.append(
            {"company_name": pair.company_name, "filing_year": pair.filing_year}
        )
    # state["combined_metadata"] = combined_metadata

    company_set_1_str = ", ".join(
        [
            f"{{{pair['company_name']} : {pair['filing_year']} }}"
            for pair in company_set_1
        ]
    )
    company_set_2_str = ", ".join(
        [f"{{{pair.company_name} : {pair.filing_year}}}" for pair in company_set_2]
    )

    log_message(f"company_set_1_str :\n\n {company_set_1_str} ", 1)
    log_message(f"company_set_2_str :\n\n {company_set_2_str} ", 1)

    missing_company_year_pairs = []

    company_set_1_tuples = set(
        (pair["company_name"], pair["filing_year"]) for pair in company_set_1
    )

    for pair in company_set_2:
        company_name = pair.company_name
        if company_name != None:
            company_name = company_name.lower()
        filing_year = pair.filing_year

        if (company_name, filing_year) not in company_set_1_tuples:
            if (
                not company_name
                or not filing_year
                or company_name.lower() == "none"
                or filing_year.lower() == "none"
            ):
                continue
            missing_company_year_pairs.append(
                {
                    "company_name": company_name,
                    "filing_year": filing_year,
                }
            )

    log_message(f"\n\n Missing Company-Year Pairs: {missing_company_year_pairs}\n\n", 1)
    # [{company_name='apple', filing_year='2023'} {company_name='google', filing_year='2022'}]
    # To get a company : extracted_pairs[0].company_name

    ###### log_tree part

    id = str(uuid.uuid4())
    child_node = nodes.identify_missing_reports.__name__ + "//" + id
    parent_node = state.get("prev_node", "START")
    log_tree = {}
    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    if not LOGGING_SETTINGS["identify_missing_reports"]:
        child_node = parent_node

    output_state = {
        "combined_metadata": combined_metadata,
        "missing_company_year_pairs": missing_company_year_pairs,
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


def download_missing_reports(state: state.OverallState):
    missing_company_year_pairs = state.get("reports_to_download", [])
    for pair in missing_company_year_pairs:
        financial_report_agent(pair["company_name"], pair["filing_year"])
    ###### log_tree part
    id = str(uuid.uuid4())
    child_node = nodes.download_missing_reports.__name__ + "//" + id
    parent_node = state.get("prev_node", "START")
    log_tree = {}

    if not LOGGING_SETTINGS["download_missing_reports"]:
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    output_state = {
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


##### ----- Finding Missing Company-year pair using llm

# class CompanyYearPair2(BaseModel):
#     """Represents a single company-year pair."""
#     company_name: str = Field(..., description="Name of the missing company .")
#     filing_year: Optional[str] = Field(None, description="Filing year for the missing company. Can be None if not specified.")
#     reason : str = Field( description = "Detailed reason why this pair has been listed as missing ?")

# class CompanyYearPairsOutput2(BaseModel):
#     """Represents the structured output for company-year pairs."""
#     company_year_pairs: List[CompanyYearPair2] = Field(
#         ...,
#         description="A list of company-year present in the company_set_2 data but missing in the knowledge base (company_set_2) data."
#     )


# _missing_docs_extraction_prompt2 = """
# Think step by step :
# You are a Finance Expert. Your task is to output company year pairs which are missing in the knowledge base (Company_set_1) .

# ### Instructions:
# - You are given two sets of company-year pairs:
#   - **Company Set 1**: The list of company-year present in the knowledge base.
#   - **Company Set 2**: The list of company-year pairs extracted from the user's query.

# - **Comparison Process**:
#   - For each company-year pair in **Company Set 2**,
#     if:
#         the company-year pair is found in **Company Set 1** then it is not missing.
#     else:
#         If the company-year pair in **Company Set 2** is not present in **Company Set 1** then it is missing.

#   - If the company-year pair in **Company Set 2** is part of a parent company in **Company Set 1** (or if the company is referred to by a full form or abbreviation), treat it as present in the knowledge base and do **not** flag it as missing.
#   - If no year is mentioned for a company in **Company Set 2**, you may use the most recent year available from the knowledge base or return "None" if the year cannot be determined.

# - **Key Notes**:
#   - Always check for **parent company** relations and **full-form/abbreviation matching** when comparing.
#   - Only return the company-year pairs that are found in **Company Set 2** but are **missing from Company Set 1**.
#   - Do not treat a company-year pair missing with reason : 'company was present but this year was present with this company in the knowledge base' : This is not a valid reason for treating a pair missing.

# ### Output Format:
# - Return a list of dictionaries of companies missing in knowledge base , each containing:
#     - "company_name" (the name of the company missing in company set 1),
#     - "filing_year" (the corresponding year for the missing company, or "None" if no year is found).
#     - "reason" ( proper very detailed reason why this company has been listed as missing )


# """


# _missing_docs_extraction_prompt = """

# Think step by step:
# You are a Finance Expert. Your task is to output company-year pairs which are missing in the knowledge base (Company_set_1).

# ### Instructions:
# - You are given two sets of company-year pairs:
#   - **Company Set 1**: The list of company-year pairs present in the knowledge base.
#   - **Company Set 2**: The list of company-year pairs extracted from the user's query.

# ### Comparison Process:
# For each company-year pair in **Company Set 2**:
# - If the company-year pair is found **exactly** in **Company Set 1**, it is **not missing**.
# - If the company-year pair is **not found** in **Company Set 1**, it is flagged as **missing**.

# ### Special Cases:
# - **Parent Company & Abbreviations**: If a company in **Company Set 2** is a child or abbreviation of a company in **Company Set 1**, it is **not flagged as missing**.
# - **Unspecified Year**: If no year is mentioned for a company in **Company Set 2**, use the most recent year available for that company in **Company Set 1**, or return "None" if the year cannot be determined.

# ### Key Notes:
# - Always check for **parent company relations** and **abbreviation matching** when comparing.
# - Only return the company-year pairs from **Company Set 2** that are **missing** from **Company Set 1**.
# - Do **not** treat a company-year pair as missing if the company is present in **Company Set 1**, even if it has a different year (this will not be considered as missing).

# ### Output Format:
# Return a list of dictionaries for companies that are missing in **Company Set 1**, each containing:
# - `"company_name"`: The name of the company missing in **Company Set 1**.
# - `"filing_year"`: The corresponding year for the company, or `"None"` if no year is found.
# - `"reason"`: A detailed reason explaining why the company-year pair is missing. Examples:
#   - `"company was not found in knowledge base"`
#   - `"company was found in knowledge base but the specified year was missing"`
#   - `"company-year pair is missing because the company does not have that year listed"`

# """


# missing_docs_extraction_prompt = ChatPromptTemplate.from_messages(
#     [("system", _missing_docs_extraction_prompt), ("human", "Identify the docs present in the company_set_2 but missing in company_set_1 \n\n**Company Set 1 (Knowledge Base)**:\n {company_set_1}\n\n**Company Set 2 (User Query)**: \n{company_set_2}")]
# )
# missing_docs_extractor = missing_docs_extraction_prompt | llm.with_structured_output(
#     CompanyYearPairsOutput2
# )


# def identify_missing_doc2(query):
#     """
#     Identifies company-year pairs mentioned in the user's query that are missing in the knowledge base.
#     Returns a list of company-year pairs that are not found in the knowledge base.

#     Args:
#         state (state.InternalRAGState): The state containing the user query and internal data.

#     Returns:
#         CompanyYearPairsOutput: A structured output containing missing company-year pairs.
#     """
#     # query = state["question"]
#     # question_group_id = state.get("question_group_id", 1)

#     # Log the query for tracking
#     # log_message(f"---QUERY: {query}", f"question_group{question_group_id}")

#     db = FinancialDatabase()
#     company_set_1 = db.get_all_company_year_pairs()

#     print(f"\n\n company_set_1 :\n\n {company_set_1} \n\n")

#     company_set_2 = extract_company_year_pairs(query)

#     # company_set_1_str = ", ".join([f"{{company_name :{pair['company_name']} , filing_year : {pair['filing_year']} }}" for pair in company_set_1])
#     # company_set_2_str = ", ".join([f"{{company_name :{pair.company_name} , filing_year : {pair.filing_year} }}" for pair in company_set_2])
#     company_set_1_str = ", ".join([f"{{{pair['company_name']} : {pair['filing_year']} }}" for pair in company_set_1])
#     company_set_2_str = ", ".join([f"{{{pair.company_name} : {pair.filing_year}}}" for pair in company_set_2])

#     print(f"\n\n company_set_1_str :\n\n {company_set_1_str} \n\n")
#     print(f"\n\n company_set_2_str :\n\n {company_set_2_str} \n\n")

#     # Extract missing company-year pairs from the query
#     missing_company_year_pairs = missing_docs_extractor.invoke({
#         "company_set_1": company_set_1_str,
#         "company_set_2": company_set_2_str
#     }).company_year_pairs

#     print(f"\n\n 1 : {missing_company_year_pairs} \n\n")

#     # If the result is not a list or not in the expected format, log a warning and return an empty list
#     if not isinstance(missing_company_year_pairs, list):
#         log_message(f"Warning: Unexpected output type for missing company-year extraction: {type(missing_company_year_pairs)}")
#         missing_company_year_pairs = []

#     # Filter out the pairs that are missing in the knowledge base

#     print(f"\n\n 1 : {missing_company_year_pairs} \n\n")
#     # missing_pairs = [
#     #     CompanyYearPair(company_name=pair['company_name'], filing_year=pair.get('filing_year', None))
#     #     for pair in missing_company_year_pairs
#     # ]

#     # Return the structured output as a list of missing company-year pairs
#     # return CompanyYearPairsOutput(company_year_pairs=missing_pairs)
#     return
