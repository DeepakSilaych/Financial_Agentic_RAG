import json
from typing import List, Optional
from pydantic import BaseModel, Field
from database import FinancialDatabase
from langchain_core.prompts import ChatPromptTemplate
import datetime

import state
from llm import llm
from utils import log_message , send_logs
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
_system_prompt_for_clarify_strict = """

You are an advanced query evaluator specializing in financial analysis of 10-K reports. Your primary goal is to determine whether a user query requires clarification to ensure accurate and relevant retrieval of information.

---

### Strict Instructions:

1. If there is any potential ambiguity or missing detail, PROACTIVELY ASK clarifying questions. Ensure questions resolve ambiguity or fill gaps critical for accurate and complete information retrieval.
2. If the query is sufficiently clear and actionable, respond with:
  
   {{
       "question_type": "none",
       "question": null,
       "options": null
   }}
   
3. If clarification is needed, select the most suitable question type:
   - Direct Answer: For open-ended and user-specific clarifications (e.g., *"What time frame should the analysis cover?"*).
   - Single Choice: When only one relevant option must be selected (e.g., *"Which year's filing should be analyzed?"*).
   - Multiple Choice: For queries with multiple valid options (e.g., *"What aspects of the 10-K report should the analysis focus on?"*).

---

### Guidelines for Question Generation:
- Necessity Check: Do not ask a question unless it is absolutely required to complete the retrieval task accurately. Every question must address a specific gap in the query.
- Address Ambiguities Proactively: If any part of the query could be interpreted differently or leaves room for detail, ASK a question to refine the understanding.
- Relevance: Ensure the question is directly tied to the context of financial analysis of 10-K reports.
- Contextual Awareness: Consider available data (e.g., companies, years) to generate realistic options. 
- Clarity & Precision: Frame questions in a manner that is specific, concise, and unambiguous, resembling how a financial expert would inquire.
- Avoid Repetition: Do not repeat any question which has been clarified already. 

### Guidelines for Option Creation (if the question is Single Choice or Multiple Choice):
- Options: Ensure at least two options for Single Choice and at least three for Multiple Choice.
- Relevance: Tailor options to the query's context to make them actionable.
- Logical Organization: Arrange options in a logical sequence, such as by importance, chronological order, or category.
- Avoid Generic Filler: Avoid generic options unless the context justifies it and it adds clarity.

---

### Examples:

#### Example 1:
User Query: *"What was Net income of Tesla in 2021 based on their 10-K filing?"*  
Response:  
{{
    "question_type": "none",
    "question": null,
    "options": null
}}
---

#### Example 2:
User Query: *"Provide insights on the latest 10-K filing."*  
Response:  
{{
    "question_type": "direct-answer",
    "question": "Could you specify the company for which you need the latest 10-K filing analyzed?",
    "options": null
}}
---

#### Example 3:
User Query: *"Explain the risk factors in latest financial report of Meta."*  
Response:  
{{
    "question_type": "multiple-choice",
    "question": "Which categories of risks in Meta's latest financial report are you most interested in?",
    "options": ["Financial risks (e.g., revenue volatility)", "Technological risks (e.g., innovation or data security)", "Legal and regulatory risks (e.g., antitrust or privacy laws)", "Market competition risks (e.g., new entrants, competitors)"]
}}
---

#### Example 4:
User Query: *"What are the key governance practices in Apple's filings?""*  
Response:  
{{
    "question_type": "multiple-choice",
    "question": "Which specific governance practices in Apple's filings would you like to explore?",
    "options": ["Board structure and composition", "Executive compensation and incentives", "Shareholder rights and voting mechanisms", "Diversity, equity, and inclusion initiatives"]
}}
---

#### Example 5:
User Query: *"Compare revenues of Meta and Google for the year 2020."*  
Response:  
{{
    "question_type": "none",
    "question": null,
    "options": null
}}
---

#### Example 6:
User Query: *"Can you provide details about Meta's profitability for 2021?"*  
Response:  
{{
    "question_type": "single-choice",
    "question": "Which metric of profitability are you most interested in?",
    "options": ["Net income", "Operating margin", "Gross margin", "Return on equity (ROE)"]
}}
---

#### Example 7:
User Query: *"What are Microsoft's key achievements in their 10-K?"*  
Response:  
{{
    "question_type": "single-choice",
    "question": "Which year's achievements would you like to focus on?",
    "options": ["2020", "2021", "2022", "2023"]
}}

---

#### Example 8:
User Query: *"What are the takeaways from Google's latest filings?"*  
Response:  
{{
    "question_type": "multiple-choice",
    "question": "Which key takeaways from Google's filings would you like to focus on?",
    "options": ["Financial performance (e.g., revenue, profit)", "Risk factors", "Market position and competition", "Governance practices"]
}}

---

    Now, given the following user query, generate clarifying question as needed:"""


_system_prompt_for_clarify_relaxed = """
You are an advanced query evaluator specializing in financial analysis of 10-K reports. Your goal is to refine user queries by asking clarifying questions that enhance the accuracy, relevance, and depth of the final response. Your questioning approach reflects the thoughtful inquiry process of a professional financial analyst.

---
### Guidelines for Clarifying Questions:

1. **Enhance Context**:  
   If there are any ambiguities or missing details in the query, proactively ask a clarifying question that adds significant value to the query's context or ensures accurate retrieval. Avoid redundant or trivial questions. Examples of valuable clarifications include:
   - Determining the scope of analysis (e.g., timeframe, company, specific metrics).
   - Identifying focus areas (e.g., risk factors, revenue trends, governance practices).
   - Understanding the type of analysis required (e.g., which liquidity or profitability metrics).

2. **Research-Oriented Inquiry**:  
   Frame questions that uncover key details a financial analyst would typically explore. For instance:
   - Which specific time period should the analysis cover?
   - Are there particular metrics or comparisons of interest?
   - Should the focus be on a section of the 10-K (e.g., risk factors, financial highlights)?

3. **Clarity & Relevance**:  
   Questions must be concise, directly tied to the query, and focused on financial analysis. Do not ask general or unrelated questions.

4. **Contextual Awareness**:  
   - If the query involves vague terms like "latest," resolve ambiguity using today's date.
   - Tailor your questions to align with the context of the query (e.g., known companies or available datasets).
   - You would be provided a list of clarifying questions already clarified by the user, DO NOT REPEAT THEM.

5. **Logical Options**:  
   For Single Choice or Multiple Choice questions, ensure options are:
   - Realistic and relevant (e.g., years, metrics, focus areas).
   - Organized logically (e.g., by chronological order or importance).

---

### Types of Questions:
- **Direct Answer**: For open-ended clarifications (e.g., "What time period should the analysis focus on?").  
- **Single Choice**: When a single option needs to be specified (e.g., "Which company's 10-K filing should be analyzed?").  
- **Multiple Choice**: For queries involving multiple valid options (e.g., "What aspects of the 10-K filing are of interest?").

---

### Examples:
**Example 1:**
**User Query:** *"What are the key insights from Tesla's latest 10-K?"*
**Response:**
{{
    "question_type": "multiple-choice",
    "question": "Which aspects of Tesla's latest 10-K are you most interested in?",
    "options": ["Financial performance (e.g., revenue, profit)", "Risk factors", "Governance practices", "Market trends"]
}}
**Example 2:**
**User Query:** *"Explain Apple's governance practices in their 10-K filings."*
**Response:**
{{
    "question_type": "single-choice",
    "question": "Which governance practices of Apple are you interested in?",
    "options": ["Board structure", "Executive compensation", "Shareholder rights", "Diversity and inclusion initiatives"]
}}
**Example 3:**
**User Query:** *"What was the net income of Meta in 2021?"*
**Response:**
{{
    "question_type": "none",
    "question": null,
    "options": null
}}
**Example 4:**
**User Query:** *"Compare revenue trends for Meta and Google."*
**Response:**
{{
    "question_type": "direct-answer",
    "question": "Could you specify the time period for the revenue comparison?",
    "options": null
}}
**Example 5:**
**User Query:** *"Provide insights on risk factors in the latest filings of Microsoft."*
**Response:**
{{
    "question_type": "multiple-choice",
    "question": "Which categories of risks in Microsoft's latest filings would you like to focus on?",
    "options": ["Financial risks (e.g., revenue volatility)", "Technological risks (e.g., innovation or cybersecurity)", "Legal and regulatory risks (e.g., privacy laws)", "Market competition risks"]
}}
Now, given the user query, generate a clarifying question (if needed) by adhering to the above guidelines. 
You must respect the time of the user, and hence not ask questions that are too trivial, i.e that can be inferred from the original query and previous responses."""
clarify_prompt_strict = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt_for_clarify_strict),
        ("human", "**User Query:** *{query}*\n**Available Data**: {company_year_data}\n**Clarified Questions and User Responses:** {clarified}\nToday's date is {today}"),
    ]
)
clarify_prompt_relaxed = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt_for_clarify_relaxed),
        ("human", "**User Query:** *{query}*\n**Available Data**: {company_year_data}\n**Clarified Questions and User Responses:** {clarified}\nToday's date is {today}")
    ]
)
clarifying_question_generator_strict = clarify_prompt_strict | llm.with_structured_output(
    ClarifyingQuestion
)
clarifying_question_generator_relaxed = clarify_prompt_relaxed | llm.with_structured_output(
    ClarifyingQuestion
)

def ask_clarifying_questions(state: state.OverallState):
    log_message("---GENERATING CLARIFYING QUESTIONS BASED ON USER QUERY---")
    query = state["question"]
    clarifying_questions = state.get("clarifying_questions",[])
    clarifications = state.get("clarifications", [])
    combined_clarifications = " | ".join(
        f"Q: {q['question']}   A: {a}"
        for q, a in zip(clarifying_questions, clarifications)
    )
    if state["fast_vs_slow"]=="fast":
        clarifying_output = clarifying_question_generator_strict.invoke(
            {"query": query, "company_year_data": company_year_data, "clarified": combined_clarifications, "today": today}
        )
    else:
        clarifying_output = clarifying_question_generator_relaxed.invoke(
            {"query": query, "company_year_data": company_year_data, "clarified": combined_clarifications, "today":  today}
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

    if analysis_required:
        analysis_suggestions = analysis_suggestion_generator.invoke(
            {"query": query}
        ).analysis_suggestions
    else:
        analysis_suggestions = []

    ###### log_tree part
    import uuid , nodes 
    id = str(uuid.uuid4())
    child_node = nodes.ask_clarifying_questions.__name__ + "//" + id
    parent_node = state.get("prev_node" , "START")
    log_tree = {}

    if not LOGGING_SETTINGS['ask_clarifying_questions']:
            child_node = parent_node  

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part

    # if not LOGGING_SETTINGS['ask_clarifying_questions']:
    #         child_node = parent_node  


    output_state = {
        "clarifying_questions": [clar_out],
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
    
    ######

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
