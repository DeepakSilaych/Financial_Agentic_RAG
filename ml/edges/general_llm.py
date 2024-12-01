import nodes.general_llm
import state, nodes
from langgraph.graph import END
from utils import log_message


def general_llm_answered(state: state.OverallState):
    answer = state["final_answer"]
    if answer:
        log_message(f"---ANSWERED BY INHERENT KNOWLEDGE OF LLM---")
        return END
    else:
        # assert(answer != None)
        log_message(f"---RETRYING---SHOULD NOT HAPPEN---")
        return nodes.general_llm.__name__
