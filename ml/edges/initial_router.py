import state, nodes
from utils import log_message
from langgraph.graph import END


def route_initial_query(state: state.OverallState):
    if state["final_answer"] != "none":
        log_message("Querying the LLM for a direct answer.")
        return nodes.general_llm.__name__
    else:
        log_message("Querying the RAG pipeline for an answer.")
        return nodes.ask_clarifying_questions.__name__
