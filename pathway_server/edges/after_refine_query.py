import state, nodes
from utils import log_message
from langgraph.graph import END


## TODO: this should be dealt with in refactor
def naive_or_complex(state: state.OverallState):
    path_decided = state["path_decided"]
    analysis_required: bool = (
        state.get("fast_vs_slow", None) == "slow" or state.get("", None) == "analysis"
    )
    if path_decided == "simple_financial":
        return "rag"
    elif analysis_required:
        return "analysis"
    elif path_decided == "complex_financial":
        return nodes.decompose_question_v2.__name__
    else:
        return "persona_rag"
