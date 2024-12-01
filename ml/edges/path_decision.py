import state, nodes
from langgraph.graph import END
from utils import log_message


def path_decided(state: state.OverallState):
    path_decided = state["path_decided"]
    if state["final_answer"] == "Generate from context":
        log_message("Can be answered from old context")
        return nodes.general_llm.__name__
    if path_decided == "web":
        log_message("---SENDING QUERY TO WEB SEARCH MODULE---")
        return "web_path"
    elif path_decided == "general":
        log_message("---SENDING QUERY TO QUESTION-ANSWERING MODULE---")
        return nodes.general_llm.__name__
    elif path_decided == "simple_financial":
        log_message("---SIMPLE FINANCIAL---")
        return nodes.ask_clarifying_questions.__name__ if state.get("fast_vs_slow","slow")=="slow" else "rag"
    else:
        log_message("---SENDING QUERY TO FINANCIAL MODULE---")
        return nodes.ask_clarifying_questions.__name__
    
def path_decided_post_clarification(state:state.OverallState):
    path_decided = state["path_decided"]
    if state["final_answer"] == "Generate from context":
        log_message("Can be answered from old context")
        return nodes.general_llm.__name__
    if path_decided == "simple_financial":
        return "rag"
    if path_decided =="complex_financial":
        return nodes.decompose_question_v2.__name__
    if path_decided =="analysis":
        return "analysis"
    if path_decided == "persona":
        return "persona"