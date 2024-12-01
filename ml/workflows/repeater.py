
from typing import Optional
from langgraph.graph import END, StateGraph, START
import uuid

import state, nodes, edges
from nodes.question_decomposer import (
    question_decomposer_v5,
    question_decomposer_v6,
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
        self.citations = []
        self.child_citations = []

    def add_child(self, child):
        self.children.append(child)


# Function to build the question tree
def build_question_tree(
    question,
    depth=0,
    max_depth=1,
    parent_question=None,
    sufficient=False,
    list_subquestions=None,
    qa_pairs=None,
    # combined_citations = None,
):
    if depth > max_depth:
        return None  # Stop building beyond max depth
    
    current_node = QuestionNode(parent_question=parent_question, question=question, layer=depth)
    if (depth==max_depth):
        return current_node

    if sufficient:
        questions_str = "\n".join(list_subquestions)
        subquestions = question_decomposer_v6.invoke(
            {"question": question, "sub_ques": questions_str}
        ).decomposed_questions
    else:
        subquestions = question_decomposer_v5.invoke(
            {"question": question}
        ).decomposed_questions
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
        if child.citations:
            root.child_citations.extend(child.citations)


# GOING TO BE MAKING A QUESTION TREE ITSELF, BUT JUST LIMITING IT TO ONE LAYER
def decomposer_node_1(state: state.OverallState):
    question = state["question"]
    tree = build_question_tree(question)
    subquestion_store = [i.question for i in tree.children]
    return {
        "question_tree_1": tree,
        "question_store": [question],
        "subquestion_store": subquestion_store,
    }


def decomposer_node_2(state: state.OverallState):
    # question=state["question_store"][-1]
    question = state["question_store"][-1]
    subquestion_store=state['subquestion_store']
    combined_citations = state.get("combined_citations",[])
    tree = build_question_tree(question, 0, 1, None, True,subquestion_store)
    new_subquestion_store = [i.question for i in tree.children]
    return {"question_tree_2": tree, "subquestion_store": new_subquestion_store}


def decomposer_node_3(state: state.OverallState):
    # question=state["question_store"][-1]
    question = state["question_store"][-1]
    subquestion_store=state['subquestion_store']
    combined_citations = state.get("combined_citations",[])
    tree = build_question_tree(question, 0, 1, None, True, subquestion_store)
    new_subquestion_store = [i.question for i in tree.children]
    return {"question_tree_3": tree, "subquestion_store": new_subquestion_store}


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
    question_node.citations = res["citations"]
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
    question_node.citations = res["citations"]
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
    question_node.citations = res["citations"]
    return {
        # "decomposed_questions": [prev_question],
        "question_tree_3": question_tree,
        "combined_document": res["documents"],
        # "question_group": [state["question_group"]],
        # "number_of_question" : [len(state["question_group"])]
    }


def aggregate1(state: state.OverallState):
    main_question = state["question"]
    question_tree = state["question_tree_1"]
    combined_citations = state["combined_citations"]
    qa_pairs=state['qa_pairs']
    # combined_citations = state
    # question_node=workflows.search_question_in_tree()

    aggregate_child_answers(question_tree)

    new_qa_pairs = [f"{i.question}: {i.answer}" for i in question_tree.children]

    
    qa_pairs.extend(new_qa_pairs)
    combined_citations.extend(question_tree.child_citations)

    new_question = combine_questions_v3(qa_pairs, main_question)
    answered = check_sufficient.invoke(
        {"question": new_question, "qa_pairs": qa_pairs}
    ).sufficient_answer

    return {
        "question_store": [new_question],
        "qa_pairs": new_qa_pairs,
        "sufficient": answered,
        "combined_citations" : combined_citations
        #    'question_tree_store':[question_tree]
    }


def aggregate2(state: state.OverallState):
    main_question = state["question"]
    question_tree = state["question_tree_2"]
    combined_citations = state["combined_citations"]
    qa_pairs=state['qa_pairs']
    # question_node=workflows.search_question_in_tree()

    aggregate_child_answers(question_tree)

    new_qa_pairs = [f"{i.question}: {i.answer}" for i in question_tree.children]

    qa_pairs.extend(new_qa_pairs)

    combined_citations.extend(question_tree.child_citations)

    new_question = combine_questions_v3(qa_pairs, main_question)

    answered = check_sufficient.invoke(
        {"question": new_question, "qa_pairs": qa_pairs}
    ).sufficient_answer

    return {
        "question_store": [new_question],
        "qa_pairs": new_qa_pairs,
        "sufficient": answered,
        "combined_citations" : combined_citations,
        #    'question_tree_store':[question_tree]
    }


def aggregate3(state: state.OverallState):
    main_question = state["question_store"][0]
    question_tree = state["question_tree_3"]
    # question_node=workflows.search_question_in_tree()
    combined_citations = state["combined_citations"]
    qa_pairs=state['qa_pairs']
    # question_node=workflows.search_question_in_tree()

    aggregate_child_answers(question_tree)

    new_qa_pairs = [f"{i.question}: {i.answer}" for i in question_tree.children]

    qa_pairs.extend(new_qa_pairs)


    combined_citations.extend(question_tree.child_citations)

    return {
        "qa_pairs":new_qa_pairs,
        "combined_citations" : combined_citations
        #   'question_tree_store':[question_tree]
    }


graph = StateGraph(state.OverallState)
#graph.add_node(nodes.process_query.__name__, nodes.process_query)
#graph.add_node(nodes.ask_clarifying_questions.__name__, nodes.ask_clarifying_questions)
#graph.add_node(nodes.refine_query.__name__, nodes.refine_query)

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

graph.add_node(nodes.append_citations.__name__ , nodes.append_citations)

# graph.add_node(nodes.append_citations.__name__ , nodes.append_citations)
graph.add_edge(START, decomposer_node_1.__name__)
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

graph.add_conditional_edges(
    decomposer_node_3.__name__, edges.repeat_3, [rag_3_time.__name__]
)
graph.add_edge(rag_3_time.__name__, aggregate3.__name__)
graph.add_edge(aggregate3.__name__, nodes.combine_answer_v3.__name__)
graph.add_edge(nodes.combine_answer_v3.__name__,nodes.append_citations.__name__)
graph.add_edge(nodes.append_citations.__name__ , END)

# fmt: on

repeater = graph.compile()

from typing import Optional
from langgraph.graph import END, StateGraph, START
import uuid

import state, nodes, edges
from nodes.question_decomposer import (
    question_decomposer_v5,
    question_decomposer_v6,
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
        self.citations = []
        self.child_citations = []

    def add_child(self, child):
        self.children.append(child)


# Function to build the question tree
def build_question_tree(
    question,
    depth=0,
    max_depth=1,
    parent_question=None,
    sufficient=False,
    list_subquestions=None,
    qa_pairs=None,
    # combined_citations = None,
):
    if depth > max_depth:
        return None  # Stop building beyond max depth
    
    current_node = QuestionNode(parent_question=parent_question, question=question, layer=depth)
    if (depth==max_depth):
        return current_node

    if sufficient:
        questions_str = "\n".join(list_subquestions)
        subquestions = question_decomposer_v6.invoke(
            {"question": question, "sub_ques": questions_str}
        ).decomposed_questions
    else:
        subquestions = question_decomposer_v5.invoke(
            {"question": question}
        ).decomposed_questions
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
        if child.citations:
            root.child_citations.extend(child.citations)


# GOING TO BE MAKING A QUESTION TREE ITSELF, BUT JUST LIMITING IT TO ONE LAYER
def decomposer_node_1(state: state.OverallState):
    question = state["question"]
    tree = build_question_tree(question)
    subquestion_store = [i.question for i in tree.children]
    return {
        "question_tree_1": tree,
        "question_store": [question],
        "subquestion_store": subquestion_store,
    }


def decomposer_node_2(state: state.OverallState):
    # question=state["question_store"][-1]
    question = state["question_store"][-1]
    subquestion_store=state['subquestion_store']
    combined_citations = state.get("combined_citations",[])
    tree = build_question_tree(question, 0, 1, None, True,subquestion_store)
    new_subquestion_store = [i.question for i in tree.children]
    return {"question_tree_2": tree, "subquestion_store": new_subquestion_store}


def decomposer_node_3(state: state.OverallState):
    # question=state["question_store"][-1]
    question = state["question_store"][-1]
    subquestion_store=state['subquestion_store']
    combined_citations = state.get("combined_citations",[])
    tree = build_question_tree(question, 0, 1, None, True, subquestion_store)
    new_subquestion_store = [i.question for i in tree.children]
    return {"question_tree_3": tree, "subquestion_store": new_subquestion_store}


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
    question_node.citations = res["citations"]
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
    question_node.citations = res["citations"]
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
    question_node.citations = res["citations"]
    return {
        # "decomposed_questions": [prev_question],
        "question_tree_3": question_tree,
        "combined_document": res["documents"],
        # "question_group": [state["question_group"]],
        # "number_of_question" : [len(state["question_group"])]
    }


def aggregate1(state: state.OverallState):
    main_question = state["question"]
    question_tree = state["question_tree_1"]
    combined_citations = state["combined_citations"]
    qa_pairs=state['qa_pairs']
    # combined_citations = state
    # question_node=workflows.search_question_in_tree()

    aggregate_child_answers(question_tree)

    new_qa_pairs = [f"{i.question}: {i.answer}" for i in question_tree.children]

    
    qa_pairs.extend(new_qa_pairs)
    combined_citations.extend(question_tree.child_citations)

    new_question = combine_questions_v3(qa_pairs, main_question)
    answered = check_sufficient.invoke(
        {"question": new_question, "qa_pairs": qa_pairs}
    ).sufficient_answer

    return {
        "question_store": [new_question],
        "qa_pairs": new_qa_pairs,
        "sufficient": answered,
        "combined_citations" : combined_citations
        #    'question_tree_store':[question_tree]
    }


def aggregate2(state: state.OverallState):
    main_question = state["question"]
    question_tree = state["question_tree_2"]
    combined_citations = state["combined_citations"]
    qa_pairs=state['qa_pairs']
    # question_node=workflows.search_question_in_tree()

    aggregate_child_answers(question_tree)

    new_qa_pairs = [f"{i.question}: {i.answer}" for i in question_tree.children]

    qa_pairs.extend(new_qa_pairs)

    combined_citations.extend(question_tree.child_citations)

    new_question = combine_questions_v3(qa_pairs, main_question)

    answered = check_sufficient.invoke(
        {"question": new_question, "qa_pairs": qa_pairs}
    ).sufficient_answer

    return {
        "question_store": [new_question],
        "qa_pairs": new_qa_pairs,
        "sufficient": answered,
        "combined_citations" : combined_citations,
        #    'question_tree_store':[question_tree]
    }


def aggregate3(state: state.OverallState):
    main_question = state["question_store"][0]
    question_tree = state["question_tree_3"]
    # question_node=workflows.search_question_in_tree()
    combined_citations = state["combined_citations"]
    qa_pairs=state['qa_pairs']
    # question_node=workflows.search_question_in_tree()

    aggregate_child_answers(question_tree)

    new_qa_pairs = [f"{i.question}: {i.answer}" for i in question_tree.children]

    qa_pairs.extend(new_qa_pairs)


    combined_citations.extend(question_tree.child_citations)

    return {
        "qa_pairs":new_qa_pairs,
        "combined_citations" : combined_citations
        #   'question_tree_store':[question_tree]
    }


graph = StateGraph(state.OverallState)


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

graph.add_node(nodes.append_citations.__name__ , nodes.append_citations)

# graph.add_node(nodes.append_citations.__name__ , nodes.append_citations)
graph.add_edge(START, decomposer_node_1.__name__)
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

graph.add_conditional_edges(
    decomposer_node_3.__name__, edges.repeat_3, [rag_3_time.__name__]
)
graph.add_edge(rag_3_time.__name__, aggregate3.__name__)
graph.add_edge(aggregate3.__name__, nodes.combine_answer_v3.__name__)
graph.add_edge(nodes.combine_answer_v3.__name__,nodes.append_citations.__name__)
graph.add_edge(nodes.append_citations.__name__ , END)

# fmt: on

repeater = graph.compile()

