import state, nodes
from utils import log_message
from langgraph.types import Send

def send_analysis_questions(state: state.InternalRAGState):
    """
    Sends the analysis questions to RAGs for agents context
    """
    question_groups = state["analysis_question_groups"]
    return [Send("agent_rag", {"question_group": group}) for group in question_groups]