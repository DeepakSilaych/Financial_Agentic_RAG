import state
from utils import log_message
from langgraph.graph import END


def route_initial_query(state: state.OverallState):
    if state["final_answer"] != "none":
        log_message("Querying the LLM for a direct answer.")
        return "direct"
    else:
        log_message("Querying the RAG pipeline for an answer.")
        return "rag"
