"""
Module for Deciding Paths for Queries and Answer Analysis

This module processes user queries, determines the appropriate path for handling them, 
and analyzes answers based on predefined prompts. It uses the `langchain` framework to 
integrate with LLMs for decision-making tasks, including different deciders for query 
stages (PathDecider, SplitPathDecider, AnswerAnalysis).

Key Components:
- PathDecider: Identifies whether the query is web-related, financial, or general.
- SplitPathDecider: Decides the handling path based on query type (before and after clarifying questions).
- AnswerAnalysis: Combines and analyzes the final answer with quantitative results.
- Logging and State Management: Tracks query flow and decision-making using logs and state.

Imports:
- langchain_core.prompts, pydantic.BaseModel, utils, llm, and other required modules for processing and logging.

Functions:
- path_decider: Decides the query path.
- split_path_decider_1 & split_path_decider_2: Decides paths before and after clarifying questions.
- combine_answer_analysis: Combines and logs the final answer with analysis.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from utils import log_message

from langchain_core.output_parsers import StrOutputParser
from prompt import prompts
import state
from llm import llm
import uuid
from utils import send_logs
from config import LOGGING_SETTINGS


class PathDecider(BaseModel):
    path_decided: Optional[str] = Field(
        default=None,
        description="Decides whether the query is a web query, financial query, or a general question.",
    )


_system_prompt_for_path_decider = prompts._system_prompt_for_path_decider

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

_system_prompt_for_split_decider_1 = prompts._system_prompt_for_split_decider_1

_system_prompt_for_split_decider_2_normal_mode = prompts._system_prompt_for_split_decider_2_normal_mode

_system_prompt_for_split_decider_2_research_mode = prompts._system_prompt_for_split_decider_2_research_mode

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
    log_message(
        f"---DECIDED THE PATH FOR THE QUERY: {path_decider_output.path_decided}---"
    )

            ###### log_tree part
    # import uuid , nodes 
    id = str(uuid.uuid4())
    child_node = "split_path_decider_1" + "//" + id
    # parent_node = state.get("prev_node" , "START")
    parent_node = state.get("prev_node" , "")
    log_tree = {}
    # tree_log(f"send_Log_tree_logs : {state['send_log_tree_logs']}",1)
    if not LOGGING_SETTINGS['split_path_decider_1'] or state.get("send_log_tree_logs" , "") == "False":
        child_node = parent_node 

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part
    output_state =  {
        "path_decided": path_decider_output.path_decided,
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

            ###### log_tree part
    # import uuid , nodes 
    id = str(uuid.uuid4())
    child_node = "split_path_decider_2" + "//" + id
    # parent_node = state.get("prev_node" , "START")
    parent_node = state.get("prev_node" , "")
    log_tree = {}
    # tree_log(f"send_Log_tree_logs : {state['send_log_tree_logs']}",1)
    if not LOGGING_SETTINGS['split_path_decider_2'] or state.get("send_log_tree_logs" , "") == "False":
        child_node = parent_node 

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part
    output_state =  {
        "path_decided": path_decider_output.path_decided,
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


## TODO:rewrite the following prompt
_system_prompt_for_answer_analysis = prompts._system_prompt_for_answer_analysis

answer_analysis_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _system_prompt_for_answer_analysis),
        (
            "human",
            "Answer from team: {answer}\n Results from Quantitative Analysis: {KPI_answer}\n",
        ),
    ]
)
answer_analysis = answer_analysis_prompt | llm | StrOutputParser()


def combine_answer_analysis(state: state.OverallState):
    log_message("--COMBINING THE ANSWER--")
    """ answer = answer_analysis.invoke(
        {
            "query": state["question"],
            "answer": state["final_answer"],
            "KPI_answer": state.get("kpi_answer", "None"),
        }
    ) """
    answer=state['final_answer']

    ###### log_tree part
    # import uuid , nodes
    id = str(uuid.uuid4())
    child_node = "combine_answer_analysis" + "//" + id
    # parent_node = state.get("prev_node" , "START")
    parent_node = state.get("combine_answer_parents", "")
    log_tree = {}
    # tree_log(f"send_Log_tree_logs : {state['send_log_tree_logs']}",1)
    if (
        not LOGGING_SETTINGS["combine_answer_analysis"]
        or state.get("send_log_tree_logs", "") == "False"
    ):
        child_node = parent_node

    log_tree[parent_node] = [child_node]
    ######

    ##### Server Logging part
    output_state = {
        "final_answer": answer,
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
    # return {"final_answer": answer}
