import json
from typing import List, Optional
from pydantic import BaseModel, Field
from database import FinancialDatabase
from langchain_core.prompts import ChatPromptTemplate

import state
from llm import llm
from utils import log_message

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
_system_prompt_for_clarify = """

You are an advanced query evaluator specializing in financial analysis of 10-K reports. Your primary goal is to determine whether a user query requires clarification to ensure accurate and relevant retrieval of information.

---

### Strict Instructions:

1. Ask questions ONLY when essential to resolve ambiguity or fill critical gaps that would lead to incomplete or incorrect information retrieval.
2. If the query is sufficiently clear and actionable as it stands, respond with:
  
   {{
       "question_type": "none",
       "question": null,
       "options": null
   }}
   
3. If clarification is needed, select the most suitable question type:
   - Direct Answer: For open-ended clarifications (e.g., *"What time frame should the analysis cover?"*).
   - Single Choice: When a specific option must be selected (e.g., *"Which year's filing should be analyzed?"*).
   - Multiple Choice: When there are multiple valid options (e.g., *"What aspects of the 10-K report should the analysis focus on?"*).

---

### Guidelines for Question Generation:

- Necessity Check: Do not ask a question unless it is absolutely required to complete the retrieval task accurately.
- Relevance: Ensure the question is directly tied to the context of financial analysis of 10-K reports.
- Data-Aware: Use the available list of companies and years of data to guide question generation. Avoid asking for information that is clearly irrelevant or unavailable.
- Clarity & Precision: Frame questions in a manner that is specific, concise, and unambiguous, resembling how a financial expert would inquire.
- Avoid Redundancy: Do not ask generic or trivial questions. Every question must address a specific gap in the query.

---

### Examples:

#### Example 1:
User Query: *"What were the major risks highlighted in Tesla's 10-K filing?"*  
Response:  
{{
    "question_type": "none",
    "question": null,
    "options": null
}}
---

#### Example 2:
User Query: *"Can you provide insights on Apple's revenue?"*  
Response:  
{{
    "question_type": "single-choice",
    "question": "Which year's revenue for Apple should be analyzed?",
    "options": ["2023", "2022", "2021"]
}}
---

#### Example 3:
User Query: *"Explain the risk factors in latest financial report of Meta."*  
Response:  
{{
    "question_type": "multiple-choice",
    "question": "Which type of risks are you most interested in?",
    "options": ["Financial risks (e.g., revenue volatility)", "Technological risks (e.g., innovation or data security)", "Legal and regulatory risks (e.g., antitrust or privacy laws)", "Market competition risks (e.g., new entrants, competitors)"]
}}
---

#### Example 4:
User Query: *"Tell me about Google's financial highlights."*  
Response:  
{{
    "question_type": "multiple-choice",
    "question": "What aspects of Google's financial highlights should be analyzed?",
    "options": ["Revenue", "Profit margins", "Expenses", "All key financial metrics"]
}}
---

#### Example 5:
User Query: *"Compare Meta and Google's revenue for the year 2021."*  
Response:  
{{
    "question_type": "none",
    "question": null,
    "options": null
}}
---

#### Example 6:
User Query: *"What governance practices are covered in Meta Platforms' reports?"*  
Response:  
{{
    "question_type": "multiple-choice",
    "question": "Which specific governance practices should the analysis focus on?",
    "options": ["Board structure", "Executive compensation", "Shareholder rights"]
}}
---

#### Example 7:
User Query: *"Can you analyze 10-K filings?"*  
Response:  
{{
    "question_type": "direct-answer",
    "question": "Could you specify the company or year for the 10-K filings you need analyzed?",
    "options": null
}}
---


    Now, given the following user query, generate clarifying question as needed:"""

clarify_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt_for_clarify),
        ("human", "**User Query:** *{query}\n**Data Available**: {company_year_data}"),
    ]
)
clarifying_question_generator = clarify_prompt | llm.with_structured_output(
    ClarifyingQuestion
)


def ask_clarifying_questions(state: state.OverallState):
    """
    A Human-in-the-Loop function that:
    1. Generates clarifying questions based on the user's initial query.
    2. Interacts with the user to collect responses to these questions.
    3. Uses an LLM to combine the original query, clarifying questions, and user responses into a refined final query.
    """
    log_message("---GENERATING CLARIFYING QUESTIONS BASED ON USER QUERY---")
    query = state["question"]
    clarifying_output = clarifying_question_generator.invoke(
        {"query": query, "company_year_data": company_year_data}
    )
    analysis_suggestions = None
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

    if analysis_required:
        analysis_suggestions = analysis_suggestion_generator.invoke(
            {"query": query}
        ).analysis_suggestions
    return {
        "clarifying_questions": [clar_out],
        "analysis_suggestions": analysis_suggestions,
    }


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
def type_of_analysis(state:state.OverallState):
    question=state["question"]
    topics=analysis_suggestion_generator.invoke({
        "query":question
    }).analysis_suggestions
    return {
        "analysis_suggestions":topics
    }


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
