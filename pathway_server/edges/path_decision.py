import state
from utils import log_message

import os


def is_folder_empty(folder_path):
    if not os.path.exists(folder_path):
        print(f"The folder '{folder_path}' does not exist.")
        return False
    if not os.path.isdir(folder_path):
        print(f"The path '{folder_path}' is not a folder.")
        return False
    return len(os.listdir(folder_path)) == 0


def decide_path(state: state.OverallState):
    log_message("----DECIDING PATH 1----")
    path_decided = state["path_decided"]
    if is_folder_empty("data") or path_decided == "general":
        log_message("---SENDING QUERY TO GENERAL MODULE---")
        return "general"
    if path_decided == "web":
        log_message("---SENDING QUERY TO WEB SEARCH MODULE---")
        return "web"
    else:
        log_message("---SENDING QUERY TO FINANCIAL MODULE---")
        return "ask_questions"


def decide_path_post_clarification(state: state.OverallState):
    path_decided = state["path_decided"]
    log_message("----DECIDING PATH POST CLARIFICATION----")
    log_message(
        f"Path Decided:  {path_decided} | state['final_answer'] : {state['final_answer']}",
        1,
    )
    if state["final_answer"] == "Generate from context":
        log_message("Can be answered from old context")
        return "direct"
    if path_decided == "simple_financial":
        return "rag"
    if path_decided == "complex_financial":
        return "decomposed_rag"
    if path_decided == "reason":
        return "persona"
