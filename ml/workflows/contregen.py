from typing import List, Optional
from langgraph.graph import END, StateGraph, START
import uuid
from langgraph.types import Send

import state, nodes, edges
from utils import log_message
from nodes.question_decomposer import (
    question_decomposer_v3,
    question_combiner,
    combine_questions,
)
from .rag_e2e import rag_e2e
from nodes.question_decomposer import question_combiner_v2
from state import QuestionNode
from langgraph.checkpoint.memory import MemorySaver


# Function to build the question tree
def build_question_tree(question, depth=0, max_depth=3, parent_question=None):
    if depth > max_depth:
        print(f"Max depth reached for question: {question}")
        return None  # Stop building beyond max depth

    # Create a node for the current question
    print(f"Creating node at depth {depth}: {question}")
    current_node = QuestionNode(
        parent_question=parent_question, question=question, layer=depth
    )

    # Decompose the question to find subquestions
    try:
        subquestions = question_decomposer_v3.invoke(
            {"question": question}
        ).decomposed_questions
        print(f"Decomposing '{question}' -> {subquestions}")
    except Exception as e:
        print(f"Error during decomposition: {e}")
        return current_node  # Return the current node if decomposition fails

    # If no subquestions or decomposition returns the same question
    if not subquestions or all(sub == question for sub in subquestions):
        print(
            f"Terminating at depth {depth}: No further decomposition for '{question}'"
        )
        return current_node  # Leaf node: no further decomposition

    # Recursively build child nodes for each subquestion
    for subquestion in subquestions:
        if subquestion == question:  # Skip duplicate decomposition
            print(f"Skipping duplicate subquestion: '{subquestion}'")
            continue
        child_node = build_question_tree(
            subquestion, depth + 1, max_depth, parent_question=question
        )
        if child_node:
            current_node.add_child(child_node)

    return current_node


def search_question_in_tree(
    root: QuestionNode, target_question: str
) -> Optional[QuestionNode]:
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


def decomposer_node(state: state.OverallState):
    question = state["question"]
    return {"question_tree": build_question_tree(question).to_dict()}


def rag_3_layer(state: state.InternalRAGState):
    question_group_id = str(uuid.uuid4())
    question = state["question"]
    answer = rag_e2e.invoke(
        {
            "question": question,
            "question_group_id": question_group_id,
        }
    )["answer"]
    question_tree = QuestionNode.from_dict(state["question_tree"])
    question_node = search_question_in_tree(question_tree, question)
    question_node.answer = answer
    return {"question_tree": question_tree.to_dict()}


def rag_2_layer(state: state.InternalRAGState):
    question_group_id = str(uuid.uuid4())
    question = state["question"]
    question_tree = QuestionNode.from_dict(state["question_tree"])
    question_node = search_question_in_tree(question_tree, question)

    aggregate_child_answers(question_tree)
    if question_node.children:
        new_question = combine_questions(
            question_node.children, question_node.child_answers, question
        )
    else:
        new_question = question
    log_message(
        f"Combined question:  {new_question}", f"question_group{question_group_id}"
    )
    question_node.answer = rag_e2e.invoke(
        {"question": question, "question_group_id": question_group_id}
    )["answer"]
    return {"question_tree": question_tree.to_dict()}


def rag_1_layer(state: state.InternalRAGState):
    question_group_id = str(uuid.uuid4())
    question = state["question"]
    question_tree = QuestionNode.from_dict(state["question_tree"])
    question_node = search_question_in_tree(question_tree, question)

    aggregate_child_answers(question_tree)
    if question_node.children:
        new_question = combine_questions(
            question_node.children, question_node.child_answers, question
        )
    else:
        new_question = question
    log_message(
        f"Combined question:  {new_question}", f"question_group{question_group_id}"
    )
    question_node.answer = rag_e2e.invoke(
        {"question": question, "question_group_id": question_group_id}
    )["answer"]
    return {"question_tree": question_tree.to_dict()}


graph = StateGraph(state.OverallState)
graph.add_node(
    nodes.combine_conversation_history.__name__, nodes.combine_conversation_history
)
graph.add_node(nodes.check_safety.__name__, nodes.check_safety)
graph.add_node(nodes.decompose_question_v2.__name__, nodes.decompose_question_v2)
graph.add_node(nodes.ask_clarifying_questions.__name__, nodes.ask_clarifying_questions)
graph.add_node(nodes.refine_query.__name__, nodes.refine_query)
graph.add_node(decomposer_node.__name__, decomposer_node)
graph.add_node(rag_3_layer.__name__, rag_3_layer)
graph.add_node(rag_2_layer.__name__, rag_2_layer)
graph.add_node(rag_1_layer.__name__, rag_1_layer)
graph.add_node(nodes.combine_answer_v2.__name__, nodes.combine_answer_v2)
graph.add_edge(START, nodes.check_safety.__name__)
graph.add_edge(nodes.check_safety.__name__, nodes.combine_conversation_history.__name__)
graph.add_conditional_edges(
    nodes.combine_conversation_history.__name__,
    edges.route_initial_query,
    {
        nodes.ask_clarifying_questions.__name__: nodes.ask_clarifying_questions.__name__,
        "end_workflow": END,
    },
)
graph.add_conditional_edges(
    nodes.check_safety.__name__,
    edges.query_safe_or_not,
    {
        nodes.combine_conversation_history.__name__: nodes.combine_conversation_history.__name__,
        END: END,
    },
)
graph.add_conditional_edges(
    nodes.ask_clarifying_questions.__name__,
    edges.refine_query_or_not,
    {
        "decompose": decomposer_node.__name__,
        nodes.refine_query.__name__: nodes.refine_query.__name__,
    },
)
graph.add_edge(nodes.refine_query.__name__, decomposer_node.__name__)
graph.add_conditional_edges(
    decomposer_node.__name__, edges.send_first_set_of_decomposed_questions
)
graph.add_conditional_edges(
    rag_3_layer.__name__, edges.send_2_layer_decomposed_questions
)
graph.add_conditional_edges(
    rag_2_layer.__name__, edges.send_1_layer_decomposed_questions
)
graph.add_edge(rag_1_layer.__name__, nodes.combine_answer_v2.__name__)
graph.add_edge(nodes.combine_answer_v2.__name__, END)

memory = MemorySaver()
final_workflow_with_contregen = graph.compile(
    checkpointer=memory, interrupt_before=[nodes.refine_query.__name__]
)
