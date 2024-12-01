import state, nodes
from langgraph.graph import END
from utils import log_message


def query_modified_or_not(state: state.OverallState):
    modified_query = state["modified_query"]
    if not modified_query:
        log_message("----FILTERING NOT POSSIBLE----ENDING WORKFLOW----")
        return END
    else:
        return nodes.process_query.__name__
