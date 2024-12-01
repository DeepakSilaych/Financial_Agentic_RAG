import state, nodes

def refine_query_or_not(state: state.OverallState):
    clarifying_questions = state["clarifying_questions"]
    if not clarifying_questions or clarifying_questions[-1]["question_type"]=="none" or  len(clarifying_questions)>=3:
        return "decompose"
    else:
        return nodes.refine_query.__name__

# TODO: What if the user response is like "No Analysis" for the analysis suggested?
# Then, it should go back to original workflow, but currently it does not!
def check_query_type(state: state.OverallState):
    analysis_question = state["analysis_question"]
    if "No Analysis Required" in analysis_question:
        return nodes.decompose_question_v2.__name__
    else:
        return nodes.create_persona.__name__

