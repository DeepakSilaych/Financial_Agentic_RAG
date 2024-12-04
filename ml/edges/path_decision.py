import state
from utils import log_message

def decide_path(state: state.OverallState):
    path_decided = state["path_decided"]
    if state["final_answer"] == "Generate from context":
        log_message("Can be answered from old context")
        return "direct"
    if path_decided == "web":
        log_message("---SENDING QUERY TO WEB SEARCH MODULE---")
        return "web"
    else:
        log_message("---SENDING QUERY TO FINANCIAL MODULE---")
        return "ask_questions"


def decide_path_post_clarification(state: state.OverallState):
    path_decided = state["path_decided"]
    log_message("Path Decided: ", path_decided)
    if state["final_answer"] == "Generate from context":
        log_message("Can be answered from old context")
        return "direct"
    if path_decided == "simple_financial":
        return "rag"
    if path_decided == "complex_financial":
        return "decomposed_rag"
    if path_decided == "discuss":
        return "persona"
