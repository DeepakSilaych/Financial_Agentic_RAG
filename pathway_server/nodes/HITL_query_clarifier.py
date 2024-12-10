# -----------------------------
# Clarifying Question and Financial Analysis Suggestion Generation
# -----------------------------
# This module is responsible for generating clarifying questions based on a user query and suggesting
# the required financial analysis to answer the query. It integrates with a financial database and
# utilizes a language model to generate insightful clarifications and analysis recommendations.

# Key Components:
# 1. **ClarifyingQuestion**: A Pydantic model that defines the structure of a clarifying question 
#    which can either be multiple-choice, single-choice, direct-answer, or none, based on the user query.
# 2. **ClarifyingQuestion Generation**: Two types of prompts (strict and relaxed) are used to generate 
#    clarifying questions, ensuring that they are essential for answering the query.
# 3. **AnalysisSuggestion**: A Pydantic model that suggests specific financial analyses required to 
#    answer the user's query, with a pre-defined set of available financial analyses.
# 4. **Analysis Question Generation**: A function that determines the type of financial analysis to 
#    perform based on the query, asking the user to confirm which analyses to proceed with.
# 5. **Logging**: Throughout the process, logs are maintained for tracking the flow and decisions 
#    made by the system, ensuring traceability and providing transparency in the decision-making process.

# Functionality:
# - **Clarifying Questions**: The system generates clarifying questions to ensure that the user’s query 
#   is fully understood and the correct analysis is performed.
# - **Financial Analysis Suggestions**: Based on the query, the system suggests the relevant financial 
#   analyses that should be conducted, sorted by their relevance.
# - **User Interaction**: Users are prompted to confirm which analyses they want to proceed with.
# - **Logging**: Detailed logs are generated at each stage of the process, which are sent to the server 
#   for analysis tracking.

# Features:
# - Generates clarifying questions to refine user queries.
# - Suggests the most relevant financial analyses for answering a user query.
# - Allows users to select the type of analysis they want to proceed with.
# - Tracks and logs the process for accountability and transparency.

# Improvements:
# - The prompt models can be further tuned to handle more complex user queries and edge cases.
# - The database integration could be expanded to support more dynamic querying based on various company data.
# -----------------------------

import json
from typing import List, Optional
from pydantic import BaseModel, Field
from database import FinancialDatabase
from langchain_core.prompts import ChatPromptTemplate
import datetime
from prompt import prompts
import state
from llm import llm
from utils import log_message, send_logs
from config import LOGGING_SETTINGS

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

today = datetime.date.today()
today = today.strftime("%B %d, %Y")


class ClarifyingQuestion(BaseModel):
    """Generates a single clarifying question based on the initial user query, strictly ensuring the question is essential."""

    question_type: str = Field(
        ...,
        description="The type of question to ask: 'multiple-choice', 'single-choice', or 'direct-answer'. If no question is needed, use 'none'.",
    )
    question: Optional[str] = Field(
        default=None,
        description="The single clarifying question to ask the user. Leave null if no question is needed.",
    )
    options: Optional[List[str]] = Field(
        default=None,
        description="List of options if the question is of type 'multiple-choice' or 'single-choice'. Leave null if not applicable.",
    )


# System prompt for generating clarifying questions based on the initial query
_system_prompt_for_clarify_strict = prompts._system_prompt_for_clarify_strict


_system_prompt_for_clarify_relaxed = prompts._system_prompt_for_clarify_relaxed
clarify_prompt_strict = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt_for_clarify_strict),
        (
            "human",
            "**User Query:** *{query}*\n**Available Data**: {company_year_data}\n**Clarified Questions and User Responses:** {clarified}\nToday's date is {today}",
        ),
    ]
)
clarify_prompt_relaxed = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt_for_clarify_relaxed),
        (
            "human",
            "**User Query:** *{query}*\n**Available Data**: {company_year_data}\n**Clarified Questions and User Responses:** {clarified}\nToday's date is {today}",
        ),
    ]
)
clarifying_question_generator_strict = (
    clarify_prompt_strict | llm.with_structured_output(ClarifyingQuestion)
)
clarifying_question_generator_relaxed = (
    clarify_prompt_relaxed | llm.with_structured_output(ClarifyingQuestion)
)


def ask_clarifying_questions(state: state.OverallState):
    log_message("---GENERATING CLARIFYING QUESTIONS BASED ON USER QUERY---")
    query = state["question"]
    clarifying_questions = state.get("clarifying_questions", [])
    clarifications = state.get("clarifications", [])
    combined_clarifications = " | ".join(
        f"Q: {q['question']}   A: {a}"
        for q, a in zip(clarifying_questions, clarifications)
    )
    if state["fast_vs_slow"] == "fast":
        clarifying_output = clarifying_question_generator_strict.invoke(
            {
                "query": query,
                "company_year_data": company_year_data,
                "clarified": combined_clarifications,
                "today": today,
            }
        )
    else:
        clarifying_output = clarifying_question_generator_relaxed.invoke(
            {
                "query": query,
                "company_year_data": company_year_data,
                "clarified": combined_clarifications,
                "today": today,
            }
        )

    clar_out = {
        "question": getattr(clarifying_output, "question", None),
        "question_type": getattr(clarifying_output, "question_type", None),
        "options": getattr(clarifying_output, "options", None),
    }

    ## modify this
    analysis_required: bool = (
        state.get("fast_vs_slow", None) == "slow"
        or state.get("path_decided", None) == "analysis"
    )
    analysis_suggestions=[]
    if analysis_required:
        analysis_suggestions = analysis_suggestion_generator.invoke(
            {"query": query}
        ).analysis_suggestions 
        

    ###### log_tree part
    import uuid, nodes

    id = str(uuid.uuid4())
    child_node = nodes.ask_clarifying_questions.__name__ + "//" + id
    parent_node = state.get("prev_node", "START")
    log_tree = {}

    if not LOGGING_SETTINGS["ask_clarifying_questions"]:
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    # if not LOGGING_SETTINGS['ask_clarifying_questions']:
    #         child_node = parent_node  
    
    ######
    if(len(clarifying_questions)!=0 and clarifying_questions[-1]["question_type"]=="none"):
        output_state = {
            "analysis_suggestions": analysis_suggestions,
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
        return output_state

    output_state = {
        "clarifying_questions": [clar_out],
        "analysis_suggestions": analysis_suggestions,
        "prev_node": child_node,
        "log_tree": log_tree,
    }
    send_logs(
            parent_node = parent_node , 
            curr_node= child_node , 
            child_node=None , 
            input_state=state , 
            output_state=output_state , 
            text=child_node.split("//")[0] ,
        )
    return output_state


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


def type_of_analysis(state: state.OverallState):
    question = state["question"]
    topics = analysis_suggestion_generator.invoke(
        {"query": question}
    ).analysis_suggestions
    return {"analysis_suggestions": topics}


class AnalysisQuestion(BaseModel):
    analysis_question: Optional[str] = Field(
        default=None,
        description="Suggest specific analysis to be done for answering the query and ask/confirm with the user",
    )


_system_prompt_for_analysis = f"""You are a query evaluator tasked with deciding whether the query requires some financial analysis to be performed or not.
If the query does not need any such analysis/review and can be directly answered from retrieval without reasoning, respond with exactly "No Analysis Required".
Otherwise, if answering the query REQUIRES any type of Financial Analysis to be done, then ask an analysis question suggesting some types of Financial analysis that should be done to answer query and ask user which among them he wants to be performed.
Types of Financial Analysis that can be performed are:
{available_financial_analyses}

You can also suggest other financial analysis as well based on the query asked by the user.

Here is an example:
1. Input: "What was the R&D expenditure of XYZ as compared to PQR in 2021?"
   Output: None

2. Input: "Compare R&D expenditure of XYZ with PQR and how does it affect the growth of both the companies?"
   Output: "The query requires financial analysis. would you like to proceed with ABC analysis, BCD review, CDE analysis?"

Now, given the following user query, generate an analysis question as needed:"""

analysis_prompt = ChatPromptTemplate.from_messages(
    [("system", _system_prompt_for_analysis), ("human", "**User Query:** *{query}")]
)
analysis_question_generator = analysis_prompt | llm.with_structured_output(
    AnalysisQuestion
)


def ask_analysis_question(state: state.OverallState):
    log_message("---GENERATING ANALYSIS QUESTION FOR THE USER QUERY---")
    query = state["question"]
    analysis_output = analysis_question_generator.invoke({"query": query})
    return {"analysis_question": analysis_output.analysis_question}
