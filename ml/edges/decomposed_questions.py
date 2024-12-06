from langgraph.types import Send
from langgraph.graph import END
from utils import log_message
import state, nodes
from typing import List
from state import QuestionNode


def send_decomposed_questions(state: state.OverallState):
    """
    Sends the decomposed questions to the next RAG graphs by fanning out the
    questions so that they run in parallel.
    """
    log_message("---SEND DECOMPOSED QUESTIONS---")
    image_url = state.get("image_url", "")
    questions = state["decomposed_questions"]
    image_desc=state.get("image_desc","")
    return [Send("rag", {"question": question, "image_url": image_url, "image_desc":image_desc}) for question in questions]


def send_decomposed_question_groups(state: state.OverallState):
    """
    Sends the decomposed question groups to the next RAG graphs by fanning out the
    questions so that they run in parallel.
    """
    log_message("---SEND DECOMPOSED QUESTION GROUPS---")
    image_url = state.get("image_url", "")
    question_groups = state["decomposed_question_groups"]
    image_desc=state.get("image_desc","")
    return [Send("rag", {"question_group": group, "image_url": image_url,"image_desc":image_desc}) for group in question_groups] 


def send_decomposed_question_groups_with_serial_hack(state: state.OverallState):
    """
    Sends the decomposed question groups to the next RAG graphs by fanning out the
    questions so that they run in parallel.
    """
    log_message("---RUNNING RAG AGENT ON ALL QUERIES IN PARALLEL---")

    question_groups = state["decomposed_question_groups"]
    image_desc=state.get("image_desc","")
    image_url=state.get("image_url","")
    return [Send("rag1", {"question_group": [group],"image_url":state.get("image_url",""),"image_desc":state.get("image_desc","")}) for group in question_groups]


def critic_check(state: state.OverallState):
    """
    After the decomposed check,
    """
    log_message("---RUNNING RAG AGENT ON ALL QUERIES IN PARALLEL---")

    critic_suggestions = state["critic_suggestion"]
    critic_count = state["critic_counter"]
    question_groups = state["decomposed_question_groups"]

    if critic_suggestions.strip() == "No changes." or critic_count == 3:
        return "rag"
        # return 
    else:
        return "decompose"


def get_nodes_by_layer(root: QuestionNode, target_layer: int) -> List[QuestionNode]:
    result = []

    if root.layer == target_layer:
        result.append(root)

    for child in root.children:
        result.extend(get_nodes_by_layer(child, target_layer))

    return result


def get_max_depth(root: QuestionNode) -> int:
    """
    Calculates the maximum depth of a question tree.

    :param root: The root node of the question tree.
    :return: The maximum depth of the tree.
    """
    if not root.children:
        return root.layer  # Leaf node: return its layer value

    # Recursively calculate the depth for all children and return the max
    return max(get_max_depth(child) for child in root.children)


def send_2_layer_decomposed_questions(state: state.InternalRAGState):
    log_message(f"----RUNNING RAG AGENT ON SECOND LAYER SUBQUERIES----")
    question_tree = QuestionNode.from_dict(state["question_tree"])
    x_layer_questions = get_nodes_by_layer(question_tree, 2)
    return [
        Send(
            f"rag_2_layer",
            {"question": question.question, "question_tree": question_tree.to_dict(),"image_url":state.get("image_url",""),"image_desc":state.get("image_desc","")},
        )
        for question in x_layer_questions
    ]


def send_1_layer_decomposed_questions(state: state.InternalRAGState):
    log_message(f"----RUNNING RAG AGENT ON FIRST LAYER SUBQUERIES----")
    question_tree =  QuestionNode.from_dict(state["question_tree"])
    x_layer_questions = get_nodes_by_layer(question_tree, 1)
    return [
        Send(
            f"rag_1_layer",
            {"question": question.question, "question_tree": question_tree.to_dict(),"image_url":state.get("image_url",""),"image_desc":state.get("image_desc","")},
        )
        for question in x_layer_questions
    ]

def send_first_set_of_decomposed_questions(state: state.OverallState):
    question_tree =  QuestionNode.from_dict(state["question_tree"])
    depth = get_max_depth(question_tree)
    x_layer_questions = get_nodes_by_layer(question_tree, depth)
    return [
        Send(
            f"rag_{depth}_layer",
            {"question": question.question, "question_tree": question_tree.to_dict(),"image_url":state.get("image_url",""),"image_desc":state.get("image_desc","")},
        )
        for question in x_layer_questions
    ]


## REPEATER WORKFLOW

def aggregate_child_answers(root):
    # If the node has no children, there's nothing to aggregate
    if not root.children:
        return
    
    # Recursively aggregate answers for all children
    for child in root.children:
        aggregate_child_answers(child)
        # Append the child's answer to the parent's child_answers list
        if child.answer:  # Ensure there's an answer to add
            root.child_answers.append(child.answer)

def repeat_1(state:state.OverallState):
    question_tree=QuestionNode.from_dict(state["question_tree_1"])
    x_layer_questions=get_nodes_by_layer(question_tree,1)
    return [Send(f"rag_1_time",{"question":question.question, "question_tree_1":question_tree.to_dict(),"image_url":state.get("image_url",""),"image_desc":state.get("image_desc","")}) for question in x_layer_questions]

def repeat_2(state:state.OverallState):
    question_tree=QuestionNode.from_dict(state["question_tree_2"])
    x_layer_questions=get_nodes_by_layer(question_tree,1)
    return [Send(f"rag_2_time",{"question":question.question, "question_tree_2":question_tree.to_dict(),"image_url":state.get("image_url",""),"image_desc":state.get("image_desc","")}) for question in x_layer_questions]

def repeat_3(state:state.OverallState):
    question_tree=QuestionNode.from_dict(state["question_tree_3"])
    x_layer_questions=get_nodes_by_layer(question_tree,1)
    return [Send(f"rag_3_time",{"question":question.question, "question_tree_3":question_tree.to_dict(),"image_url":state.get("image_url",""),"image_desc":state.get("image_desc","")}) for question in x_layer_questions]


def check_answer_fit_1(state: state.OverallState):
    log_message(f"----CHECKING REPEATER ONCE----")
    

    answered=state['sufficient']

    if(answered=='Yes'):
        #return "combine_answer_v3"
        return "combine_answer_v3"
    else:
        return "decomposer_node_2"
    
def check_answer_fit_2(state: state.OverallState):
    log_message(f"----CHECKING REPEATER ONCE----")
    
    answered=state['sufficient']

    if(answered=='Fully Answered'):
        #return "combine_answer_v3"
        return "combine_answer_v3"
    else:
        return "decomposer_node_3"

