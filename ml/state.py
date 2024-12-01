import operator
from typing import List, TypedDict, Annotated, Optional, Dict, Literal

from pydantic import BaseModel
from langchain_core.documents import Document


class QuestionNode:
    def __init__(self, parent_question: Optional[str], question: str, layer: int):
        self.parent_question = parent_question  # The question that led to this one
        self.question = question  # The current question
        self.layer = layer  # The depth of this question in the tree
        self.answer = None
        self.child_answers = []
        self.children = []
        self.citations = []

    def add_child(self, child):
        self.children.append(child)


# Custom Reducer function for question tree
def merge_question_nodes(
    existing_node: QuestionNode, new_node: QuestionNode
) -> QuestionNode:
    """
    Merges two QuestionNode trees by combining their children.

    :param existing_node: The current QuestionNode in the state.
    :param new_node: The new QuestionNode to merge.
    :return: A merged QuestionNode tree.
    """
    if existing_node is None:
        return new_node

    if new_node is None:
        return existing_node

    # Ensure the nodes correspond to the same question
    if existing_node.question != new_node.question:
        raise ValueError("Cannot merge nodes with different questions.")

    # Merge answers (assuming new_node's answer takes precedence if non-None)
    existing_node.answer = new_node.answer or existing_node.answer

    # Merge child answers
    existing_node.child_answers = list(
        set(existing_node.child_answers + new_node.child_answers)
    )

    # Merge children nodes by question
    existing_children_by_question = {
        child.question: child for child in existing_node.children
    }
    for new_child in new_node.children:
        if new_child.question in existing_children_by_question:
            # Recursively merge matching child nodes
            merged_child = merge_question_nodes(
                existing_children_by_question[new_child.question], new_child
            )
            existing_children_by_question[new_child.question] = merged_child
        else:
            # Add new child node
            existing_children_by_question[new_child.question] = new_child

    # Update children list
    existing_node.children = list(existing_children_by_question.values())

    return existing_node


class OverallState(TypedDict):
    messages: Annotated[List[str], operator.add]
    question: str
    follow_up_questions: List[str]
    combined_citations: Annotated[List[dict], operator.add]
    final_answer: str
    final_answer_with_citations: str
    combined_documents: Annotated[List[Document], operator.add]
    missing_company_year_pairs : List[dict]
    reports_to_download : List[dict]
    combined_metadata : List[dict]

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

    question_tree: Annotated[Optional[QuestionNode], merge_question_nodes]
    question_tree_1: Annotated[Optional[QuestionNode], merge_question_nodes]
    question_tree_2: Annotated[Optional[QuestionNode], merge_question_nodes]
    question_tree_3: Annotated[Optional[QuestionNode], merge_question_nodes]
    qa_pairs: Annotated[List[str], operator.add]
    question_store: Annotated[List[str], operator.add]
    subquestion_store: Annotated[List[str],operator.add]
    # MIGHT REMOVE SOON
    question_tree_store: Annotated[List[QuestionNode], operator.add]
    # analysis_required: bool # yes or no
    analysis_suggestions: List[str]     # Suggestions of Analysis types that can be done on query (to ask user)
    analysis_type: List[str]            # analyis types to be done after being selected by user
    
    clarifying_questions: Annotated[List[Dict], operator.add]
    clarifications: List[Dict]
    
    # Supervisor for the task decomposing supervisor
    ## either fix circular imports
    # supervisor_messages: Annotated[List[SupervisorOutput], operator.add] ## might not be needed yet
    supervisor_scratchpad: str ## scratchpad for the supervisor. We could also make it annotated list?
    last_supervisor_decision: Optional[str]
    next_agent: Optional[str]
    
    fast_vs_slow: str ## "fast" or "slow", type will be fixed to enum later
    normal_vs_research: str ## "answer" or "research", type will be fixed to enum later
    # log_tree: Annotated[Dict[str, List[Dict[str, dict]]], operator.add]
    image_path: str
    image_desc: str
    image_url: str
    
    urls: List[str]



class InternalRAGState(TypedDict):
    original_question: str
    question: str
    decomposed_answers: Annotated[List[str], operator.add]
    question_group: Annotated[List[str], operator.add]
    question_group_id: str 
    question_tree: Annotated[Optional[QuestionNode], merge_question_nodes]
    question_tree_1: Annotated[Optional[QuestionNode], merge_question_nodes]
    question_tree_2: Annotated[Optional[QuestionNode], merge_question_nodes]
    question_tree_3: Annotated[Optional[QuestionNode], merge_question_nodes]
    analysis_question_groups: List[str]
    answer: str
    documents: List[Document]
    documents_after_metadata_filter: List[Document]
    combined_documents: Annotated[
        List[Document], operator.add
    ]  # for combining all the documents in overall state
    no_of_retrievals: int
    metadata: dict
    formatted_metadata : str
    doc_grading_retries: int
    is_answer_sufficient: bool
    answer_contains_hallucinations: bool
    hallucination_reason : str
    hallucinations_retries: int
    answer_generation_retries: int
    prev_node: str
    insufficiency_reason: str
    irrelevancy_reason: str
    expanded_question: str
    metadata_filters: List[str]  #  [ company_name , year , intra_metadata ]
    metadata_retries: int
    citations: List[dict]
    analysis_subquestions: Annotated[List[str], operator.add]
    analysis_subresponses: Annotated[
        List[str], operator.add
    ]  # responses from prefetched retreiver responses
    topics_union_set : List[str]
    rewritten_question : str
    query_type : Literal['Quantitative', 'Qualitative']
    urls: List[str]
    web_searched: bool
    

    image_url: str



class QuestionDecomposer(TypedDict):
    subquestions: Annotated[List[str], operator.add]
    collection: Annotated[List[str], operator.add]
    question: str
    counter: int
    previous_question: str
    decompose_further: bool


class Metric(BaseModel):
    name: str
    description: str
    data: str


class Value(BaseModel):
    name_of_the_metric: str
    value: float


class Chart(BaseModel):
    type: str
    data: str
    instructions: str


class CodeFormat(BaseModel):
    pngfilename: str
    code: str


class Metrics(BaseModel):
    metrics: List[Metric]


class Metrics_with_values(BaseModel):
    values: List[Value]


class Insights(BaseModel):
    insights: List[str]


class GenCharts_instructions(BaseModel):
    charts: List[Chart]


class FileName(BaseModel):
    pngfilename: str


class Visualizable(BaseModel):
    is_visualizable: bool


class VisualizerState(TypedDict):
    input_data: str
    is_visualizable: Visualizable
    metrics: list[Metric]
    values: Annotated[list[Value], operator.add]
    final_insights: list[str]
    charts: list[Chart]
    final_chart_names: Annotated[list[FileName], operator.add]
    final_output: str


class PersonaState(TypedDict):
    persona: dict[str, str]
    persona_question: str
    persona_generated_questions: Annotated[List[str], operator.add]
    persona_generated_answers: Annotated[List[str], operator.add]
    persona_specific_answers: Annotated[list[str], operator.add]
   
