from typing import Optional
from langgraph.graph import END, StateGraph, START
import uuid

import state, nodes, edges
from nodes.question_decomposer import (
    question_decomposer_v5,
    combine_questions_v3,
    check_sufficient,
)
from .rag_e2e import rag_e2e


# Define the QuestionNode class
class QuestionNode:
    def __init__(self, parent_question: Optional[str], question: str, layer: int):
        self.parent_question = parent_question  # The question that led to this one
        self.question = question  # The current question
        self.layer = layer  # The depth of this question in the tree
        self.answer = None
        self.child_answers = []
        self.children = []
        self.sufficient_answers = []

    def add_child(self, child):
        self.children.append(child)


# Function to build the question tree
def build_question_tree(
    question,
    depth=0,
    max_depth=1,
    parent_question=None,
    sufficient=False,
    sufficient_ans=None,
    suggestion=None,
):
    if depth > max_depth:
        return None  # Stop building beyond max depth

    # Create a node for the current question

    current_node = QuestionNode(
        parent_question=parent_question, question=question, layer=depth
    )

    # Decompose the question to find subquestions
    subquestions = question_decomposer_v5.invoke(
        {"question": question}
    ).decomposed_questions

    # If no subquestions or if the decomposition fails to produce new questions
    if not subquestions or subquestions[0] == question:
        return current_node  # Leaf node: no further decomposition

    # Recursively build child nodes for each subquestion
    for subquestion in subquestions:
        child_node = build_question_tree(
            subquestion, depth + 1, max_depth, parent_question=question
        )
        if child_node:
            current_node.add_child(child_node)

    return current_node


def search_question_in_tree(
    root: QuestionNode, target_question: str
) -> Optional[QuestionNode]:
    """
    Searches for a specific question in the question tree.

    :param root: The root of the question tree.
    :param target_question: The question to search for.
    :return: The QuestionNode corresponding to the target question, or None if not found.
    """
    # Check if the current node matches the target question
    if root.question == target_question:
        return root

    # Recursively search in children
    for child in root.children:
        result = search_question_in_tree(child, target_question)
        if result:
            return result

    return None  # If the question is not found in this subtree


def aggregate_child_answers(root: QuestionNode):
    # If the node has no children, there's nothing to aggregate
    if not root.children:
        return

    # Recursively aggregate answers for all children
    for child in root.children:
        aggregate_child_answers(child)
        # Append the child's answer to the parent's child_answers list
        if child.answer:  # Ensure there's an answer to add
            root.child_answers.append(child.answer)


# GOING TO BE MAKING A QUESTION TREE ITSELF, BUT JUST LIMITING IT TO ONE LAYER
def decomposer_node_1(state: state.OverallState):
    question = state["question"]
    tree = build_question_tree(question)
    return {"question_tree_1": tree, "question_store": [question]}


def decomposer_node_2(state: state.OverallState):
    question = state["question_store"][-1]
    tree = build_question_tree(question)
    return {
        "question_tree_2": tree,
    }


def decomposer_node_3(state: state.OverallState):
    question = state["question_store"][-1]
    tree = build_question_tree(question)
    return {
        "question_tree_3": tree,
    }


def rag_1_time(state: state.InternalRAGState):
    question_group_id = str(uuid.uuid4())
    question = state["question"]
    res = rag_e2e.invoke(
        {
            "question": question,
            "question_group_id": question_group_id,
        }
    )
    question_tree = state["question_tree_1"]
    question_node = search_question_in_tree(question_tree, question)
    question_node.answer = res["answer"]
    return {
        # "decomposed_questions": [prev_question],
        "question_tree_1": question_tree,
        "combined_documents": res["documents"],
        # "question_group": [state["question_group"]],
        # "number_of_question" : [len(state["question_group"])]
    }


def rag_2_time(state: state.InternalRAGState):
    question_group_id = str(uuid.uuid4())
    question = state["question"]
    res = rag_e2e.invoke(
        {
            "question": question,
            "question_group_id": question_group_id,
        }
    )
    question_tree = state["question_tree_2"]
    question_node = search_question_in_tree(question_tree, question)
    question_node.answer = res["answer"]
    return {
        # "decomposed_questions": [prev_question],
        "question_tree_2": question_tree,
        "combined_documents": res["documents"],
        # "question_group": [state["question_group"]],
        # "number_of_question" : [len(state["question_group"])]
    }


def rag_3_time(state: state.InternalRAGState):
    question_group_id = str(uuid.uuid4())
    question = state["question"]
    res = rag_e2e.invoke(
        {
            "question": question,
            "question_group_id": question_group_id,
        }
    )
    question_tree = state["question_tree_3"]
    question_node = search_question_in_tree(question_tree, question)
    question_node.answer = res["answer"]
    return {
        # "decomposed_questions": [prev_question],
        "question_tree_3": question_tree,
        "combined_documents": res["documents"],
        # "question_group": [state["question_group"]],
        # "number_of_question" : [len(state["question_group"])]
    }


def aggregate1(state: state.OverallState):
    question = state["question"]
    question_tree = state["question_tree_1"]
    # question_node=workflows.search_question_in_tree()

    aggregate_child_answers(question_tree)
    questions = [i.question for i in question_tree.children]

    qa_pairs = [
        f"{i+1}. {question}: {answer}"
        for i, (question, answer) in enumerate(
            zip(questions, question_tree.child_answers)
        )
    ]

    answered = check_sufficient.invoke(
        {"question": question, "qa_pairs": qa_pairs}
    ).sufficient_answer

    new_question = combine_questions_v3(
        questions, question_tree.child_answers, question_tree.question
    )

    return {
        "question_store": [new_question],
        "qa_pairs": qa_pairs,
        "sufficient": answered,
        #    'question_tree_store':[question_tree]
    }


def aggregate2(state: state.OverallState):
    question = state["question_store"][-1]
    question_tree = state["question_tree_2"]
    # question_node=workflows.search_question_in_tree()

    aggregate_child_answers(question_tree)
    questions = [i.question for i in question_tree.children]

    qa_pairs = [
        f"{i+1}. {question}: {answer}"
        for i, (question, answer) in enumerate(
            zip(questions, question_tree.child_answers)
        )
    ]

    answered = check_sufficient.invoke(
        {"question": question, "qa_pairs": qa_pairs}
    ).sufficient_answer

    new_question = combine_questions_v3(
        questions, question_tree.child_answers, question_tree.question
    )

    return {
        "question_store": [new_question],
        "qa_pairs": qa_pairs,
        "sufficient": answered,
        #    'question_tree_store':[question_tree]
    }


def aggregate3(state: state.OverallState):
    question = state["question_store"][-1]
    question_tree = state["question_tree_3"]
    # question_node=workflows.search_question_in_tree()

    aggregate_child_answers(question_tree)
    questions = [i.question for i in question_tree.children]

    new_question = combine_questions_v3(
        questions, question_tree.child_answers, question_tree.question
    )
    qa_pairs = [
        f"{i+1}. {question}: {answer}"
        for i, (question, answer) in enumerate(
            zip(questions, question_tree.child_answers)
        )
    ]

    return {
        "question_store": [new_question],
        "qa_pairs": qa_pairs,
        #   'question_tree_store':[question_tree]
    }


graph = StateGraph(state.OverallState)
graph.add_node(nodes.process_query.__name__, nodes.process_query)
graph.add_node(nodes.check_safety.__name__, nodes.check_safety)
graph.add_node(nodes.decompose_question_v2.__name__, nodes.decompose_question_v2)
graph.add_node(nodes.ask_clarifying_questions.__name__, nodes.ask_clarifying_questions)
graph.add_node(nodes.refine_query.__name__, nodes.refine_query)

graph.add_node(decomposer_node_1.__name__, decomposer_node_1)
graph.add_node(decomposer_node_2.__name__, decomposer_node_2)
graph.add_node(decomposer_node_3.__name__, decomposer_node_3)

graph.add_node(aggregate1.__name__, aggregate1)
graph.add_node(aggregate2.__name__, aggregate2)
graph.add_node(aggregate3.__name__, aggregate3)

graph.add_node(rag_1_time.__name__, rag_1_time)
graph.add_node(rag_2_time.__name__, rag_2_time)
graph.add_node(rag_3_time.__name__, rag_3_time)

graph.add_node(nodes.combine_answer_v3.__name__, nodes.combine_answer_v3)

graph.add_edge(START, nodes.check_safety.__name__)
graph.add_edge(nodes.check_safety.__name__, nodes.process_query.__name__)
graph.add_conditional_edges(
    nodes.process_query.__name__,
    edges.route_initial_query,
    {
        nodes.ask_clarifying_questions.__name__: nodes.ask_clarifying_questions.__name__,
        "end_workflow": END,
    },
)
graph.add_conditional_edges(
    nodes.check_safety.__name__,
    edges.query_modified_or_not,
    {nodes.process_query.__name__: nodes.process_query.__name__, END: END},
)
graph.add_conditional_edges(
    nodes.ask_clarifying_questions.__name__,
    edges.refine_query_or_not,
    {
        "decompose": decomposer_node_1.__name__,
        nodes.refine_query.__name__: nodes.refine_query.__name__,
    },
)
graph.add_edge(nodes.refine_query.__name__, decomposer_node_1.__name__)
graph.add_conditional_edges(
    decomposer_node_1.__name__, edges.repeat_1, [rag_1_time.__name__]
)
graph.add_edge(rag_1_time.__name__, aggregate1.__name__)
graph.add_conditional_edges(
    aggregate1.__name__,
    edges.check_answer_fit_1,
    {
        "decomposer_node_2": decomposer_node_2.__name__,
        "combine_answer_v3": nodes.combine_answer_v3.__name__,
    },
)

graph.add_conditional_edges(
    decomposer_node_2.__name__, edges.repeat_2, [rag_2_time.__name__]
)
graph.add_edge(rag_2_time.__name__, aggregate2.__name__)
graph.add_conditional_edges(
    aggregate2.__name__,
    edges.check_answer_fit_2,
    {
        "decomposer_node_3": decomposer_node_3.__name__,
        "combine_answer_v3": nodes.combine_answer_v3.__name__,
    },
)

graph.add_conditional_edges(decomposer_node_3.__name__, edges.repeat_3)


graph.add_edge(rag_3_time.__name__, aggregate3.__name__)
graph.add_edge(aggregate3.__name__, nodes.combine_answer_v3.__name__)
graph.add_edge(nodes.combine_answer_v3.__name__, END)
# fmt: on
# Set up memory
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
final_workflow = graph.compile(
    checkpointer=memory, interrupt_before=[nodes.refine_query.__name__]
)
