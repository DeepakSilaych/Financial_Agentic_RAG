import state, nodes
from langgraph.graph import END
from langgraph.types import Send

from utils import log_message


def task_question_router(state: state.OverallState):
    log_message("---EXTRACTING TASK AND QUESTION---")
    query = state["question_in_query"]
    task = state["task"]

    if task != "None" and query != "None":
        log_message("Task: ", task)
        log_message("Question: ", query)
        print("Task: ", task, "Question: ", query)
        return [Send("task_subgraph", {}), Send[nodes.path_decider.__name__, {}]]

    if task == "None":
        log_message("Task: None")
        return nodes.path_decider.__name__
    if query == "None":
        log_message("Question: None")
        return "task_subgraph"


def task_question_combiner(state: state.OverallState):
    log_message("---COMBINING TASK AND QUESTION---")
    task = state["task"]
    question = state["question_in_query"]
    if (task == "None") or (question == "None"):
        return END
