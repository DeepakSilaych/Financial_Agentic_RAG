from typing import Optional
from langgraph.graph import END, StateGraph, START
import uuid
import json

import state, nodes, edges
from nodes.question_decomposer import (
    cache_retriever_call,
    question_decomposer_v5,
    question_decomposer_v6,
    combine_questions_v3,
    check_sufficient,
)
from .rag_e2e import rag_e2e
from state import QuestionNode , add_child_to_node

import requests
import config

from utils import send_logs , log_message , tree_log

from pydantic import BaseModel
from config import LOGGING_SETTINGS , WORKFLOW_SETTINGS
from typing import Any, Dict, Optional
from typing import List, TypedDict, Annotated, Optional, Dict, Literal, Any, Union



class Document(BaseModel):
    metadata: dict
    page_content: str




def write_cache(query, answer):
    id = str(uuid.uuid4())

    entry = {"record_id": id, "query": query, "answer": answer, "is_cache": "cache"}
    with open("./data_cache/answers.jsonlines", "a") as f:
        f.write(json.dumps(entry) + "\n")

def call_answer_endpoint(question):
    url = f"http://{config.VECTOR_STORE_HOST}:{config.VECTOR_STORE_PORT}/answer"
    print('INPUT PRE', input)

    params = {"question": question}
    
    try:

        response = requests.post(url, params=params)
        
 
        if response.status_code == 200:
            response=response.json()
            documents=[Document.model_validate(doc) for doc in response['documents']]
            documents_after_metada=[Document.model_validate(doc) for doc in response['documents_after_metadata_filter']]

            response['documents']=documents
            response['documents_after_metadata_filter']=documents_after_metada

            return response 
        else:
            return {"error": f"API call failed with status code {response}"}
    except requests.exceptions.RequestException as e:

        return {"error": str(e)}

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

    current_node = QuestionNode(
        parent_question=parent_question, question=question, layer=depth
    )
    if depth == max_depth:
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
        subquestions.append(question)
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
        if child.log_tree:
            # log_message(f"child log tree : {child.log_tree}")
            root.child_logs.append(child.log_tree)
        if child.last_node:
            root.child_last_nodes.append(child.last_node)


# GOING TO BE MAKING A QUESTION TREE ITSELF, BUT JUST LIMITING IT TO ONE LAYER
def decomposer_node_1(state: state.OverallState):
    question = state["question"]
    tree = build_question_tree(question)
    subquestion_store = [i.question for i in tree.children]

    child_node = "decomposer_node_1" 
    parent_node = state.get("prev_node" , "START")
    log_tree = {}
    log_tree[parent_node] = [child_node]
    log_tree[child_node] = ["rag_1_time"]

    output_state = {
        "question_tree_1": tree.to_dict(),
        "question_store": [question],
        "subquestion_store": subquestion_store,
        "prev_node" : child_node,
        "log_tree" : log_tree ,
    }

    print(f"INput state : {state} \n\n output_state : {output_state}") 
    send_logs(
        parent_node = parent_node , 
        curr_node= child_node , 
        child_node=None , 
        input_state=state , 
        output_state=output_state , 
        text=child_node.split("//")[0] ,
    )

    return output_state


def decomposer_node_2(state: state.OverallState):

    question = state["question_store"][-1]
    subquestion_store = state["subquestion_store"]
    combined_citations = state.get("combined_citations", [])
    tree = build_question_tree(question, 0, 1, None, True, subquestion_store)
    new_subquestion_store = [i.question for i in tree.children]
    ###### log_tree part
    # import uuid , nodes 
    id = str(uuid.uuid4())

    child_node = "decomposer_node_2" 
    parent_node = state.get("prev_node" , "START")
    log_tree = {}
    log_tree[parent_node] = [child_node]
    log_tree[child_node] = ["rag_2_time"]
    ######
    ##### Server Logging part
    if not LOGGING_SETTINGS['decomposer_node_2']:
        child_node = parent_node
    output_state = {
        "question_tree_2": tree.to_dict(),
        "subquestion_store": new_subquestion_store,
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


def decomposer_node_3(state: state.OverallState):

    question = state["question_store"][-1]
    subquestion_store = state["subquestion_store"]
    combined_citations = state.get("combined_citations", [])
    tree = build_question_tree(question, 0, 1, None, True, subquestion_store)
    new_subquestion_store = [i.question for i in tree.children]
    ###### log_tree part

    id = str(uuid.uuid4())

    child_node = "decomposer_node_3" 
    parent_node = state.get("prev_node" , "START")
    log_tree = {}
    log_tree[parent_node] = [child_node]
    log_tree[child_node] = ["rag_3_time"]
    ######
    ##### Server Logging part
    if not LOGGING_SETTINGS['decomposer_node_3']:
        child_node = parent_node  
    output_state = {
        "question_tree_3": tree.to_dict(), 
        "subquestion_store": new_subquestion_store,
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


def rag_1_time(state: state.InternalRAGState):
    question_group_id = str(uuid.uuid4())
    question = state["question"]
    if config.RAG_ENDPOINT:
        res=call_answer_endpoint(question)
    else:
        res=rag_e2e.invoke({
            'question':question,
            "prev_node":"decomposer_node_1",
            "question_group_id":question_group_id
        })
    
    print(res)
    question_tree = QuestionNode.from_dict(state["question_tree_1"])
    question_node = search_question_in_tree(question_tree, question)
    question_node.answer = res["answer"]
    question_node.citations = res["citations"]
    question_node.log_tree = res["log_tree"]
    question_node.last_node = res["prev_node"]
    agg1_parents = res["prev_node"]
    write_cache(question, res["answer"])

    log_message(f"question_node.log_tree : {question_node.log_tree}" , 1)

    id = str(uuid.uuid4())
    child_node = "rag_1_time" + "//" + id
    parent_node = state.get("prev_node" , "START")
    log_tree = {}
    log_tree[parent_node] = [child_node]
    log_tree[child_node] = ["rag_1_time"]

    log_message(f"question_tree.to_dict() : {question_tree.to_dict()}" , 1)

    documents = res["documents"]

    return {

        "question_tree_1": question_tree.to_dict(),
        "combined_documents": documents,
        "prev_node" : "rag_1_time_cache",
        "aggregate1_parents" : agg1_parents

    }


def rag_2_time(state: state.InternalRAGState):
    question_group_id = str(uuid.uuid4())
    question = state["question"]
    if config.RAG_ENDPOINT:
        res=call_answer_endpoint(question)
    else:
        res=rag_e2e.invoke({
            'question':question,
            "prev_node":"decomposer_node_2",
            "question_group_id":question_group_id
        })
    question_tree = QuestionNode.from_dict(state["question_tree_2"])
    question_node = search_question_in_tree(question_tree, question)

    question_node.answer = res["answer"]
    question_node.citations = res["citations"]
    question_node.log_tree = res["log_tree"]
    question_node.last_node = res["prev_node"]
    agg2_parents = res["prev_node"]

    id = str(uuid.uuid4())
    child_node = "rag_2_time" + "//" + id
    parent_node = state.get("prev_node" , "START")
    log_tree = {}
    log_tree[parent_node] = [child_node]
    log_tree[child_node] = ["rag_2_time"]
    ##### Server Logging part
    log_message(f"question_tree.to_dict() : {question_tree.to_dict()}" , 1)

    documents = res["documents"]
    write_cache(question, res["answer"])

    return {

        "question_tree_2": question_tree.to_dict(),
        "combined_documents": documents,
        "aggregate2_parents" : agg2_parents

    }


def rag_3_time(state: state.InternalRAGState):
    question_group_id = str(uuid.uuid4())
    question = state["question"]
    if config.RAG_ENDPOINT:
        res=call_answer_endpoint(question)
    else:
        res=rag_e2e.invoke({
            'question':question,
            "prev_node":"decomposer_node_3",
            "question_group_id":question_group_id
        })
    question_tree = QuestionNode.from_dict(state["question_tree_3"])
    question_node = search_question_in_tree(question_tree, question)
    question_node.answer = res["answer"]
    question_node.citations = res["citations"]
    question_node.log_tree = res["log_tree"]
    question_node.last_node = res["prev_node"]
    documents = res["documents"]
    agg3_parents = res["prev_node"]
    write_cache(question, res["answer"])

    id = str(uuid.uuid4())
    child_node = "rag_3_time" + "//" + id
    parent_node = state.get("prev_node" , "START")
    log_tree = {}
    log_tree[parent_node] = [child_node]
    log_tree[child_node] = ["rag_3_time"]
    ##### Server Logging part
    log_message(f"question_tree.to_dict() : {question_tree.to_dict()}" , 1)

    return {

        "question_tree_3": question_tree.to_dict(),
        "combined_documents": documents,
         "aggregate3_parents" : agg3_parents

    }

def aggregate1(state: state.OverallState):
    main_question = state["question"]
    question_tree = QuestionNode.from_dict(state["question_tree_1"])
    combined_citations = state["combined_citations"]
    qa_pairs = state["qa_pairs"]

    aggregate_child_answers(question_tree)

    new_qa_pairs = [f"{i.question}: {i.answer}" for i in question_tree.children]

    qa_pairs.extend(new_qa_pairs)
    combined_citations.extend(question_tree.child_citations)

    overall_log_tree = state["log_tree"] 
    log_message(f"question_tree.logs {question_tree.log_tree}" , 1)
    log_message(f"{question_tree.child_logs}" , 1)

    parent_node = ""
    tree_log(f"{question_tree.child_logs}" , 1)
    for tree in question_tree.child_logs:
        log_message(f"datatype : {tree} " , 1)
        last_key , last_value = list(tree.items())[-1]
        overall_log_tree = add_child_to_node(overall_log_tree , tree)
        overall_log_tree[last_value[0]] = ["aggregate1"]


    if not parent_node or parent_node == "":
        parent_node = state.get("aggregate1_parents" , "rag_1_time_cache")

    new_question = combine_questions_v3(qa_pairs, main_question)
    answered = check_sufficient.invoke(
        {"question": new_question, "qa_pairs": "\n".join(qa_pairs)}
    ).sufficient_answer

    curr_node = "aggregate1" 
    if not LOGGING_SETTINGS['aggregate1']:
        curr_node = parent_node

    output_state = {
        "question_store": [new_question],
        "qa_pairs": new_qa_pairs,
        "sufficient": answered,
        "combined_citations" : combined_citations,

        "prev_node" : "aggregate1",
        "log_tree" : overall_log_tree ,

    }

    send_logs(
        parent_node= parent_node , 
        curr_node= curr_node , 
        child_node= None ,
        input_state=state , 
        output_state=output_state , 
        text=curr_node.split("//")[0] ,
    )

    return output_state



def aggregate2(state: state.OverallState):
    main_question = state["question"]
    question_tree = QuestionNode.from_dict(state["question_tree_2"])
    combined_citations = state["combined_citations"]
    qa_pairs = state["qa_pairs"]


    aggregate_child_answers(question_tree)

    new_qa_pairs = [f"{i.question}: {i.answer}" for i in question_tree.children]

    qa_pairs.extend(new_qa_pairs)

    combined_citations.extend(question_tree.child_citations)

    parent_node = ""
    overall_log_tree = state["log_tree"] 
    for tree in question_tree.child_logs:
        last_key , last_value = list(tree.items())[-1]
        overall_log_tree = add_child_to_node(overall_log_tree , tree)
        overall_log_tree[last_value[0]] = ["aggregate2"]


    new_question = combine_questions_v3(qa_pairs, main_question)

    answered = check_sufficient.invoke(
        {"question": new_question, "qa_pairs": "\n".join(qa_pairs)}
    ).sufficient_answer

    if not parent_node or parent_node == "":
        parent_node = state.get("aggregate2_parents" , "rag_2_time_cache")

    curr_node = "aggregate2" 
    if not LOGGING_SETTINGS['aggregate2']:
        curr_node = parent_node

    output_state = {
        "question_store": [new_question],
        "qa_pairs": new_qa_pairs,
        "sufficient": answered,
        "combined_citations" : combined_citations,
        "prev_node" : "aggregate2",
        "log_tree" :  overall_log_tree ,
    }

    send_logs(
        parent_node= parent_node , 
        curr_node= curr_node , 
        child_node= None ,
        input_state=state , 
        output_state=output_state , 
        text=curr_node.split("//")[0] ,
    )
    
    ######

    return output_state



def aggregate3(state: state.OverallState):
    main_question = state["question_store"][0]
    question_tree = QuestionNode.from_dict(state["question_tree_3"])

    combined_citations = state["combined_citations"]
    qa_pairs = state["qa_pairs"]


    aggregate_child_answers(question_tree)

    new_qa_pairs = [f"{i.question}: {i.answer}" for i in question_tree.children]

    qa_pairs.extend(new_qa_pairs)

    combined_citations.extend(question_tree.child_citations)

    overall_log_tree = state["log_tree"] 
    parent_node = ""
    tree_log(f"{question_tree.child_logs}" , 1)
    for tree in question_tree.child_logs:
        # tree_log(tree , 1)
        last_key , last_value = list(tree.items())[-1]
        overall_log_tree = add_child_to_node(overall_log_tree , tree)
        overall_log_tree[last_value[0]] = ["aggregate3"]
        # parent_node = parent_node +  "$$" + last_value[0]

    if not parent_node or parent_node == "":
        parent_node = state.get("aggregate3_parents" , "rag_1_time_cache")

    curr_node = "aggregate3" 
    if not LOGGING_SETTINGS['aggregate3']:
        curr_node = parent_node
    

    output_state = {
        "qa_pairs":new_qa_pairs,
        "combined_citations" : combined_citations,
        "prev_node" : "aggregate3",
        "log_tree" : overall_log_tree ,

    }

    send_logs(
        parent_node= parent_node , 
        curr_node= curr_node , 
        child_node= None ,
        input_state=state , 
        output_state=output_state , 
        text=curr_node.split("//")[0] ,
    )
    
    ######

    return output_state

    

graph = StateGraph(state.OverallState)
# graph.add_node(nodes.process_query.__name__, nodes.process_query)
# graph.add_node(nodes.ask_clarifying_questions.__name__, nodes.ask_clarifying_questions)
# graph.add_node(nodes.refine_query.__name__, nodes.refine_query)

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

graph.add_node(nodes.append_citations.__name__, nodes.append_citations)

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
graph.add_edge(nodes.combine_answer_v3.__name__, nodes.append_citations.__name__)
graph.add_edge(nodes.append_citations.__name__, END)

# fmt: on

repeater = graph.compile()
