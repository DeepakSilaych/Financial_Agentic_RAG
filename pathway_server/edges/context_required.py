import state, nodes


def combine_history_or_not(state: state.OverallState):
    if state["context_required"]:
        return "yes"
    else:
        return "no"