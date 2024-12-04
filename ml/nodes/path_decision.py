from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from utils import log_message

from langchain_core.output_parsers import StrOutputParser

import state
from llm import llm


class PathDecider(BaseModel):
    path_decided: Optional[str] = Field(
        default=None,
        description="Decides whether the query is a web query, financial query, or a general question.",
    )


_system_prompt_for_path_decider = """
You are a query planner in a question-answering engine tasked with identifying the type of query and deciding the appropriate path for it. Analyse the queries carefully. You have documents related to finances of major companies such as 10-K reports, financial statements, and other financial data of companies like Apple, Google, etc. You also have access to web search engines for complex web queries.
Your responsibilities are as follows:

1. **Query Type Identification**:
    - **Web Query**: Queries related to general information, news, or facts.
    - **Simple Financial Query**: Queries related to financial data, stock prices, or investment which can be answered directly from a single  document and would can be answered by a simple RAG module.
    - **Complex Financial Query**: Queries related to financial data, stock prices, or investment which you feel are multi-hop and require information from multiple sources and would need further clarification or context. This module cannot reason enough by itself and only performs retrieval with query decomposition.
    - **General Question**: Queries that don't fall into the above categories and can be answered by inherent knowledge or general reasoning or statements like salutations, greetings, etc.
    - **Information Retrieval + Reasoning**: Queries that require information retrieval from the documents and as well reasoning power for sufficiently answering the query .
    
2. **Path Selection**:
    - **Web Query**: Send the query to the web search module for information retrieval.
    - **Simple Financial Query**: Send the query to the naive RAG module for answering.
    - **Complex Financial Query**: Send the query to the complete RAG module for answering.
    - **General Question**: Proceed with the question-answering module for detailed responses.
    - **Information Retrieval + Reasoning**: Send the query to the persona RAG module for detailed analysis and reasoning along with RAG module for answering.
    
3. **Output Specification**:
    - If the query is a web query, output "web".
    - If it is a simple financial query, output "simple_financial".
    - If it is a complex financial query, output "complex_financial".
    - If it is a general question, output "general".
    - If it is an analysis required query, output "persona".
    
    
Few examples of queries are:

1. "What is the GDP of India?"
    - **Query Type**: Web Query
    - **Path**: Web Search Module
    - **Output**: "web"
    
2. "What is the stock price of Apple?"
    - **Query Type**: Simple Financial Query
    - **Path**: Naive RAG Module
    - **Output**: "simple_financial"
    
3. "What is the impact of COVID-19 on the economy?"
    - **Query Type**: Web Query
    - **Path**: Web Search Module
    - **Output**: "web"
    
4. "Which is better to invest in, Apple or Google?"
    - **Query Type**: Complex Financial Query
    - **Path**: Complete RAG Module
    - **Output**: "complex_financial"
    
5. "Hello! How are you?"
    - **Query Type**: General Question
    - **Path**: Question-Answering Module
    - **Output**: "general"

6. "What is the stock price of Apple and Microsoft?"
    - **Query Type**: Complex Financial Query
    - **Path**: Complete RAG Module
    - **Output**: "complex_financial"
    
7. "Compare the stocks of Apple and Google over the last 5 years."
    - **Query Type**: Complex Financial Query
    - **Path**: Complete RAG Module
    - **Output**: "complex_financial"
    
8. "Analyse the stocks of Apple and Google over the last 5 years."
    - **Query Type**: Reasoning + RAG required
    - **Path**: Persona RAG Module
    - **Output**: "persona"
"""

# 9. "Compare the stocks of Apple and Google over the last 5 years, which is a better investment?"
#     - **Query Type**: Reasoning + RAG required
#     - **Path**: Persona RAG Module
#     - **Output**: "persona"
# """

path_decider_prompt = ChatPromptTemplate.from_messages(
    [("system", _system_prompt_for_path_decider), ("human", "User query: {query}")]
)

query_path_decider = path_decider_prompt | llm.with_structured_output(PathDecider)


def path_decider(state: state.OverallState):
    log_message("---DECIDING THE PATH FOR THE QUERY---")
    query = state["question"]
    path_decider_output = query_path_decider.invoke({"query": query})
    return {
        "path_decided": path_decider_output.path_decided,
    }


### TODO: these prompts need to be given fast mode, slow mode !!! answer mode/ analysis mode

#### Split Path Decider: one portion before the clarifying questions, one after ###

_system_prompt_for_split_decider_1 = """
You are a query planner in a question-answering engine tasked with identifying the type of query and deciding the appropriate path for it. Analyse the queries carefully. You have documents related to finances of major companies such as 10-K reports, financial statements, and other financial data of companies like Apple, Google, etc. You also have access to web search engines for complex web queries.
Your responsibilities are as follows:

1. **Query Type Identification**:
    - **Web Query**: Queries related to general information, news, or facts.
    - **Financial Query**: Queries related to financial data, stock prices. This will use information that has to be fetched from the documents.
    
2. **Path Selection**:
    - **Web Query**: Send the query to the web search module for information retrieval.
    - **Financial Query**: Send the query to the RAG module for answering.
    
3. **Output Specification**:
    - If the query is a web query, output "web".
    - If it is a simple financial query, output "financial".
    
    
Few examples of queries are, with some explanation provided for some queries:

1. "What is the GDP of India?"
    - **Query Type**: Web Query
    - **Path**: Web Search Module
    - **Output**: "web"
    
2. "What is the stock price of Apple as of the last quarter of 2021?"
    - **Query Type**: Simple Financial Query
    - **Path**: RAG Module
    - **Output**: "financial"

3. "What is the impact of COVID-19 on the economy?"
    - **Query Type**: Web Query
    - **Path**: Web Search Module
    - **Output**: "web"
    
4. "Which is better to invest in, Apple or Google?"
    - **Query Type**: Complex
    - **Path**: Complete Module
    - **Output**: "financial"
    
"""

_system_prompt_for_split_decider_2_normal_mode = """
You are a query planner in a question-answering engine tasked with identifying the type of query and deciding the appropriate path for it. Analyse the queries carefully. You have documents related to finances of major companies such as 10-K reports, financial statements, and other financial data of companies like Apple, Google, etc. You also have access to web search engines for complex web queries.
Your responsibilities are as follows:

1. **Query Type Identification**:
    - **Simple Financial Query**: Queries related to financial data, stock prices, or investment which can be answered directly from a single  document and would can be answered by a simple RAG module.
    - **Complex Financial Query**: Queries related to financial data, stock prices, or investment which you feel are multi-hop and require information from multiple sources and would need further clarification or context. .
    
2. **Path Selection**:
    - **Simple Financial Query**: Send the query to the naive RAG module for answering.
    - **Complex Financial Query**: Send the query to the complete RAG module for answering.
    
3. **Output Specification**:
    - If it is a simple financial query, output "simple_financial".
    - If it is a complex financial query, output "complex_financial".
    
    
Few examples of queries are, with some explanation provided for some queries:
    
1. "What is the stock price of Apple in 2021 for the end of the financial year?"
    - **Query Type**: Simple Financial Query
    - **Path**: Naive RAG Module
    - **Output**: "simple_financial"
    - **Explanation**: This query can be answered directly from a single document, and does not require any further decomposition of the question.

2. "What is the stock price of Apple and Microsoft in the period 2021-2023?"
    - **Query Type**: Complex Financial Query
    - **Path**: Complete RAG Module
    - **Output**: "complex_financial"
    - **Explanation**: This query requires retreiving stock prices for both companies of the given period. No reasoning or analysis is required.
"""

_system_prompt_for_split_decider_2_research_mode = """
You are a query planner in a question-answering engine tasked with identifying the type of query and deciding the appropriate path for it. Analyse the queries carefully. You have documents related to finances of major companies such as 10-K reports, financial statements, and other financial data of companies like Apple, Google, etc. You also have access to web search engines for complex web queries.
Your responsibilities are as follows:

1. **Query Type Identification**:
    - **Simple Financial Query**: Queries related to financial data, stock prices, or investment which can be answered directly from a single  document and would can be answered by a simple RAG module.
    - **Complex Financial Query**: Queries related to financial data, stock prices, or investment which you feel are multi-hop and require information from multiple sources and would need further clarification or context. This module cannot reason enough by itself and only performs retrieval with query decomposition.
    - **Information Retrieval + Reasoning**: Queries that require information retrieval from the documents and as well as high level reasoning power for sufficiently answering the query. Here, the query will be forwarded to a team of expert agents who will discuss the question in fine detail.
    
2. **Path Selection**:
    - **Simple Financial Query**: Send the query to the naive RAG module for answering.
    - **Complex Financial Query**: Send the query to the complete RAG module for answering.
    - **Information Retrieval + Reasoning**: Send the query to the persona RAG module for detailed analysis and reasoning along with RAG module for answering.
    
3. **Output Specification**:
    - If it is a simple financial query, output "simple_financial".
    - If it is a complex financial query, output "complex_financial".
    - If it is a query involving retreival and reasoning, output "discuss".
    
    
Few examples of queries are, with some explanation provided for some queries:
    
1. "What is the stock price of Apple in 2021 for the end of the financial year?"
    - **Query Type**: Simple Financial Query
    - **Path**: Naive RAG Module
    - **Output**: "simple_financial"
    - **Explanation**: This query can be answered directly from a single document, and does not require any further decomposition of the question.
      
2. "Which is better to invest in, Apple or Google?"
    - **Query Type**: Complex Financial Query
    - **Path**: Complete RAG Module
    - **Output**: "discuss"
    - **Explanation**: This query requires a comparison of two companies where we would require reasoning over some fundamental indicators of both companies.

3. "What is the stock price of Apple and Microsoft in the period 2021-2023?"
    - **Query Type**: Complex Financial Query
    - **Path**: Complete RAG Module
    - **Output**: "complex_financial"
    - **Explanation**: This query requires retreiving stock prices for both companies of the given period. No reasoning or analysis is required.
"""

split_decider_first_prompt = ChatPromptTemplate.from_messages(
    [("system", _system_prompt_for_split_decider_1), ("human", "User query: {query}")]
)

split_path_first_decider = split_decider_first_prompt | llm.with_structured_output(
    PathDecider
)


# splitting path decider to run just before the clarifying questions
def split_path_decider_1(state: state.OverallState):
    log_message("---DECIDING THE PATH FOR THE QUERY---")
    query = state["question"]
    path_decider_output = split_path_first_decider.invoke({"query": query})
    print(path_decider_output)
    log_message(
        f"---DECIDED THE PATH FOR THE QUERY: {path_decider_output.path_decided}---"
    )
    return {
        "path_decided": path_decider_output.path_decided,
    }


split_decider_second_prompt_normal = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt_for_split_decider_2_normal_mode),
        ("human", "User query: {query}"),
    ]
)
split_path_second_decider_normal = (
    split_decider_second_prompt_normal | llm.with_structured_output(PathDecider)
)

split_decider_second_prompt_research = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt_for_split_decider_2_research_mode),
        ("human", "User query: {query}"),
    ]
)
split_path_second_decider_research = (
    split_decider_second_prompt_research | llm.with_structured_output(PathDecider)
)


# runs after clarifying query
def split_path_decider_2(state: state.OverallState):
    log_message("---DECIDING THE PATH FOR THE QUERY---")
    query = state["question"]
    if state.get("normal_vs_research", "research") == "normal":
        path_decider_output = split_path_second_decider_normal.invoke({"query": query})
    else:
        path_decider_output = split_path_second_decider_research.invoke(
            {"query": query}
        )
    return {
        "path_decided": path_decider_output.path_decided,
    }


## TODO:rewrite the following prompt
_system_prompt_for_answer_analysis="""
You are a financial analyst who has been given the task of drafting an answer to a question. Your task is answering the following question {query} 

To achieve this you have used your team to research an answer to the question. You have additionally ran detailed analysis into the quantitivate aspects related to your question. This will let you add supporting detail to your answer.

You are now tasked with combining these answers appropriately to get the final answer to the main question.
Make sure you include all the necessary facts and details from the answers to create a comprehensive final answer. Be sure not to miss out on any important information."""

answer_analysis_prompt = ChatPromptTemplate.from_messages(
    [("system", _system_prompt_for_answer_analysis), ("human", "Answer from team: {answer}\n Results from Quantitative Analysis: {KPI_answer}\n")]
)
answer_analysis = answer_analysis_prompt | llm |StrOutputParser()

def combine_answer_analysis(state:state.OverallState):
    log_message("--COMBINING THE ANSWER--")
    answer = answer_analysis.invoke({"query":state["question"],"answer":state["final_answer"],"KPI_answer":('\n'.join([s for s in state["partial_answer"]]))})
    return {"final_answer" : answer}
    