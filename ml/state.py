import operator
from typing import List, TypedDict, Annotated, Optional, Dict, Literal, Any, Union

from pydantic import BaseModel
from langchain_core.documents import Document
from utils import log_message, tree_log
import json
from langgraph.checkpoint.serde.base import SerializerProtocol
import json
from typing import Any, Dict, Optional


class QuestionNode:
    def __init__(self, parent_question: Optional[str], question: str, layer: int):
        self.parent_question = parent_question
        self.question = question
        self.layer = layer
        self.answer = None
        self.child_answers = []
        self.children = []
        self.citations = []
        self.child_citations = []  # New field for child citations
        self.log_tree = {}
        self.child_logs = []
        self.last_node = None
        self.child_last_nodes = []

    def add_child(self, child: "QuestionNode"):
        self.children.append(child)

    def to_dict(self) -> Dict[str, Any]:
        """Convert QuestionNode to a dictionary for serialization."""
        # log_message(f"self.log_tree : {self.log_tree}" ,1)
        # log_message(f"self.child_logs : {self.child_logs}" ,1)
        return {
            "parent_question": self.parent_question,
            "question": self.question,
            "layer": self.layer,
            "answer": self.answer,
            "child_answers": self.child_answers,
            "children": [child.to_dict() for child in self.children],
            "citations": self.citations,
            "child_citations": self.child_citations,  # Include child_citations in serialization
            "log_tree": self.log_tree,
            "child_logs": self.child_logs,
            "last_node": self.last_node,
            "child_last_nodes": self.child_last_nodes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuestionNode":
        """Reconstruct a QuestionNode from a dictionary."""
        node = cls(
            parent_question=data.get("parent_question"),
            question=data["question"],
            layer=data["layer"],
        )
        node.answer = data.get("answer")
        node.child_answers = data.get("child_answers", [])
        node.children = [cls.from_dict(child) for child in data.get("children", [])]
        node.citations = data.get("citations", [])
        node.child_citations = data.get(
            "child_citations", []
        )  # Deserialize child_citations
        node.log_tree = data.get("log_tree", {})
        # log_message(f"node.log_tree : {node.log_tree}",1)
        node.child_logs = data.get("child_logs", [])
        # log_message(f"node.child_logs : {node.child_logs}" ,1)
        node.last_node = data.get("last_node", "")
        node.child_last_nodes = data.get("child_last_nodes", [])
        return node


def merge_question_dicts(
    existing_node: Dict[str, Any], new_node: Dict[str, Any]
) -> Dict[str, Any]:
    # tree_log(f"AT START : existing_node :  {existing_node} , NEW NODE : {new_node}" , 1)

    if existing_node is None:
        return new_node

    if new_node is None:
        return existing_node

    # Ensure the nodes correspond to the same question
    if existing_node["question"] != new_node["question"]:
        raise ValueError("Cannot merge nodes with different questions.")

    # Merge answers (assuming new_node's answer takes precedence if non-None)
    existing_node["answer"] = new_node.get("answer") or existing_node.get("answer")

    # Merge child answers
    existing_node["child_answers"] = list(
        set(existing_node.get("child_answers", []) + new_node.get("child_answers", []))
    )

    # Merge children nodes by question
    existing_children_by_question = {
        child["question"]: child for child in existing_node.get("children", [])
    }
    for new_child in new_node.get("children", []):
        if new_child["question"] in existing_children_by_question:
            # Recursively merge matching child nodes
            merged_child = merge_question_dicts(
                existing_children_by_question[new_child["question"]], new_child
            )
            existing_children_by_question[new_child["question"]] = merged_child
        else:
            # Add new child node
            existing_children_by_question[new_child["question"]] = new_child

    # Update children list
    existing_node["children"] = list(existing_children_by_question.values())

    # Merge citations
    def merge_list_of_dicts(existing_list, new_list):
        # Transform into hashable forms (tuple of sorted key-value pairs)
        existing_hashed = {frozenset(citation.items()) for citation in existing_list}
        new_hashed = {frozenset(citation.items()) for citation in new_list}
        # Combine and convert back to list of dictionaries
        merged_hashed = existing_hashed | new_hashed
        return [dict(citation) for citation in merged_hashed]

    existing_node["citations"] = merge_list_of_dicts(
        existing_node.get("citations", []), new_node.get("citations", [])
    )
    existing_node["child_citations"] = merge_list_of_dicts(
        existing_node.get("child_citations", []), new_node.get("child_citations", [])
    )

    existing_node["log_tree"] = add_child_to_node(
        existing_node.get("log_tree", []), new_node.get("log_tree", [])
    )

    # existing_node["log_tree"] = new_node.get("log_tree" , {})
    # child_logs = [{}]
    # for node in new_node.get("child_logs" , []):
    #     child_logs.append()

    # existing_node["child_logs"] = new_node.get("child_logs" , [])
    existing_node["last_node"] = new_node.get("last_node") or existing_node.get(
        "last_node"
    )
    # existing_node["child_last_nodes"] = new_node.get("child_last_nodes" , [])
    existing_node["child_last_nodes"] = list(
        set(
            existing_node.get("child_last_nodes", [])
            + new_node.get("child_last_nodes", [])
        )
    )
    # tree_log(f" AT START ,  last node : {existing_node["last_node"]} , new node : {new_node["last_node"]} ,   ")
    # tree_log(f"AT FINISH existing_node :  {existing_node}" , 1)
    return existing_node


def add_child_to_node(
    existing_log_tree: Dict[str, List[str]], new_log_tree: Dict[str, List[str]]
) -> Dict[str, List[str]]:
    """
    Adds a child node to the given parent node in the log_tree.
    If the parent node doesn't exist, it creates the entry with the child.

    Args:
        existing_log_tree: Dict[str, List[str]]
        new_log_tree: Dict[str, List[str]]
    """
    # Create a copy of the first dictionary to avoid modifying it in place
    # log_message(f"existing log tree 2 : {existing_log_tree}" , 1 )

    updated_log_tree = existing_log_tree.copy()
    # Iterate through the second dictionary and merge
    for key, value in new_log_tree.items():
        if key in updated_log_tree:
            # If the key already exists, append the new list to the existing list
            for item in value:
                if item not in updated_log_tree[key]:
                    updated_log_tree[key].append(item)
            # updated_log_tree[key].extend(value)
        else:
            # If the key doesn't exist, create a new entry with the value
            updated_log_tree[key] = value

    # log_message(f"existing log tree : {existing_log_tree} , new_log_tree : {new_log_tree} , \n\n updated_log_tree : {updated_log_tree} " , 1)
    return updated_log_tree
    # return updated_log_tree


def prev_node_merge(existing_str: str, new_str: str) -> str:
    # log_message(f"Updating prev node | existing_str : {existing_str} , new_str : {new_str}", 1)
    if new_str is None:
        return existing_str
    return new_str

def prev_node_merge2(existing_str: str, new_str: str) -> str:
    # log_message(f"Updating prev node | existing_str : {existing_str} , new_str : {new_str}", 1)
    if new_str is None:
        return existing_str
    if existing_str is None: 
        return new_str
    return existing_str + "$$" + new_str




class KPIState(TypedDict):
    analysis_companies_by_year: List[Dict]

    analyses_to_be_done: list[str]
    analyses_kpis_by_company_year: list[dict[str, Any]]
    analyses_kpis_by_company_year_calculated: list[dict[str, Any]]
    analyses_values: list[dict[str, Any]]
    final_answer: str
    prev_node : str 
    log_tree: Annotated[
        Dict[str, List[str]], add_child_to_node
    ]  # [ key ( prev_node_name+//+uuid ) : value ( List[str (prev_node_name+//+uuid )])]


class OverallState(TypedDict):
    user_id: str
    messages: Annotated[List[str], operator.add]
    question: str
    follow_up_questions: List[str]
    combined_citations: Annotated[List[dict], operator.add]
    final_answer: str
    final_answer_with_citations: str
    combined_documents: Annotated[List[Document], operator.add]
    missing_company_year_pairs: List[dict]
    reports_to_download: List[dict]

    db_state: List[dict]

    personas: List[dict[str, str]]
    persona_specific_questions: List[str]
    persona_specific_answers: Annotated[list[str], operator.add]
    persona_generated_questions_using_supervisor: Annotated[List[str], operator.add]
    persona_generated_answers_using_supervisor: Annotated[List[str], operator.add]
    current_persona: Optional[dict[str, str]]

    path_decided: str

    decomposed_questions: Annotated[List[str], operator.add]
    decomposed_question_groups: List[List[str]]
    critic_suggestion: str
    critic_counter: int
    decomposed_answers: Annotated[List[str], operator.add]

    question_tree: Annotated[Optional[Dict[str, Any]], merge_question_dicts]
    question_tree_1: Annotated[Optional[Dict[str, Any]], merge_question_dicts]
    question_tree_2: Annotated[Optional[Dict[str, Any]], merge_question_dicts]
    question_tree_3: Annotated[Optional[Dict[str, Any]], merge_question_dicts]
    qa_pairs: Annotated[List[str], operator.add]
    question_store: Annotated[List[str], operator.add]
    subquestion_store: Annotated[List[str], operator.add]

    # analysis_required: bool # yes or no
    analysis_suggestions: List[
        str
    ]  # Suggestions of Analysis types that can be done on query (to ask user)
    analysis_companies_by_year: List[Dict]

    analyses_to_be_done: list[str]
    # analyses_kpis_by_company_year: list[dict[str, Any]]
    # analyses_kpis_by_company_year_calculated: list[dict[str, Any]]
    # analyses_values: list[dict[str, Any]]
    kpi_answer: Annotated[str, prev_node_merge]

    clarifying_questions: Annotated[List[Dict], operator.add]
    clarifications: List[Dict]

    fast_vs_slow: str  ## "fast" or "slow", type will be fixed to enum later
    normal_vs_research: str  ## "answer" or "research", type will be fixed to enum later
    # log_tree: Annotated[Dict[str, List[Dict[str, dict]]], operator.add]
    image_path: str
    image_url : str
    image_desc: str
    query_safe: str

    urls: List[str]
    prev_node: Annotated[str, prev_node_merge]
    # combined_logs :
    log_tree: Annotated[
        Dict[str, List[str]], add_child_to_node
    ]  # [ key ( prev_node_name+//+uuid ) : value ( List[str (prev_node_name+//+uuid )])]
    combined_metadata: List[Dict]

    overall_retries: int

    # File paths for retreival filtering
    query_path: List[str]

    # frontend variables
    message_id: str
    chat_id: str
    space_id: str

    persona_last_nodes : Annotated[str , prev_node_merge2] # parent nodes for combine_persona_specific_answers
    combine_answer_parents : Annotated[str , prev_node_merge2] # parent nodes for final_combine_answer_analysis

class InternalRAGState(TypedDict):
    ## Ques
    user_id: str
    original_question: str
    question: str
    category: Literal["Quantitative", "Qualitative"]
    decomposed_answers: Annotated[List[str], operator.add]
    question_group: Annotated[List[str], operator.add]
    question_group_id: str
    question_tree: Annotated[Optional[Dict[str, Any]], merge_question_dicts]
    question_tree_1: Annotated[Optional[Dict[str, Any]], merge_question_dicts]
    question_tree_2: Annotated[Optional[Dict[str, Any]], merge_question_dicts]
    question_tree_3: Annotated[Optional[Dict[str, Any]], merge_question_dicts]
    analysis_question_groups: List[str]
    expanded_question: str
    analysis_subquestions: Annotated[List[str], operator.add]
    analysis_subresponses: Annotated[
        List[str], operator.add
    ]  # responses from prefetched retreiver responses

    ## Metadata
    metadata: dict
    formatted_metadata: str
    metadata_filters: List[str]  #  [ company_name , year , topics , ]
    # Query path for filtering
    query_path: List[str]

    ## Answer
    answer: str
    doc_generated_answer: str
    web_generated_answer: str

    ## Documents
    documents: List[Document]  # Changes after doc grading are made here
    documents_after_metadata_filter: List[
        Document
    ]  # Retains docs after metadata filtering
    documents_with_kv: List[Document]  # Retains docs with key value pairs
    fallback_qq_retriever: bool
    combined_documents: Annotated[
        List[Document], operator.add
    ]  # for combining all the documents in overall state

    ## Retries/Sufficiency/Reason
    no_of_retrievals: int
    doc_grading_retries: int
    is_answer_sufficient: bool
    answer_contains_hallucinations: bool
    hallucination_reason: str
    hallucinations_retries: int
    answer_generation_retries: int
    prev_node: Annotated[str, prev_node_merge]
    insufficiency_reason: str
    irrelevancy_reason: str
    metadata_retries: int

    ## Misc
    citations: List[dict]
    topics_union_set: List[str]
    rewritten_question: str
    query_type: Literal["Quantitative", "Qualitative"]
    urls: List[str]
    web_searched: bool
    image_url : str
    image_desc: str
    log_tree: Annotated[
        Dict[str, List[str]], add_child_to_node
    ]  # [ key ( prev_node_name+//+uuid ) : value ( List[str (prev_node_name+//+uuid )])]

    send_log_tree_logs : str
    prev_node_rewrite : str

class QuestionDecomposer(TypedDict):
    subquestions: Annotated[List[str], operator.add]
    collection: Annotated[List[str], operator.add]
    question: str
    counter: int
    previous_question: str
    decompose_further: bool


class BarChart(BaseModel):
    type: Literal["Bar Chart"]  # Default type for BarChart
    data: Dict[str, List[List[float]]]
    x_label: str
    y_label: str
    title: str


# Line Chart Definition
class LineChart(BaseModel):
    type: Literal["Line Chart"]  # Default type for LineChart
    data: Dict[str, List[List[float]]]
    x_label: str
    y_label: str
    title: str


# Pie Chart Definition
class PieChart(BaseModel):
    type: Literal["Pie Chart"]  # Default type for PieChart
    labels: List[str]  # Labels for each section (e.g., regions, product categories)
    values: List[float]  # Values for each section (percentages or actual amounts)
    title: str


# General Chart Class that accepts any type of chart
class Chart(BaseModel):
    chart: List[
        Union[BarChart, LineChart, PieChart, Literal[""]]
    ]  # Chart type can be any of the above


# General Chart Class that accepts any type of chart
class Chart_Name(BaseModel):
    title: str  # The title of the chart
    type: Literal[
        "Bar Chart", "Line Chart", "Pie Chart"
    ]  # Chart type can be any of the above
    reason: str  # Reason for choosing the chart type


class Chart_Name_data(BaseModel):
    data: List[Chart_Name]  # A list of Chart_Name objects


class Chart_Name_for_data(BaseModel):
    input_data: str
    state: Chart_Name


class CodeFormat(BaseModel):
    pngfilename: str
    code: str


class Metric(BaseModel):
    metric_name: str
    metric_description: str
    data_required: str


class Value(BaseModel):
    name_of_the_metric: str = ""
    value: float | int = 0


class Metric_Value(BaseModel):
    metric: Metric
    input_data: str


class Metrics(BaseModel):
    output: List[Metric]


class Metrics_with_values(BaseModel):
    values: List[Value]


class Insights(BaseModel):
    insights: str
    grade: float


class GenCharts_instructions(BaseModel):
    charts: List[Chart]


class Give_Output(BaseModel):
    output: str


class Visualizable(BaseModel):
    is_visualizable: bool
    reason: str


class VisualizerState(TypedDict):
    input_data: str
    is_visualizable: Visualizable
    metrics: list[Metric]
    values: Annotated[list[Value], operator.add]
    final_insights: Annotated[list[str], operator.add]
    chart_names: List[Chart_Name]
    charts: Annotated[list[Chart], operator.add]
    final_output: str


class PersonaState(TypedDict):
    persona: dict[str, str]
    persona_question: str
    image_url:str
    image_desc:str
    persona_generated_questions: Annotated[List[str], operator.add]
    persona_generated_answers: Annotated[List[str], operator.add]
    persona_specific_answers: Annotated[List[str], operator.add]
    prev_node : Annotated[str , prev_node_merge]
    persona_last_nodes : Annotated[str , prev_node_merge2] # parent nodes for combine_persona_specific_answers
