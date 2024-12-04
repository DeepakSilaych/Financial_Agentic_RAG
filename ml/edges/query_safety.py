import state, nodes
from langgraph.graph import END
from utils import log_message


def query_safe_or_not(state: state.OverallState):
    query_safe = state["query_safe"]
    if query_safe:
        return "yes"
    else:
        return "no"
