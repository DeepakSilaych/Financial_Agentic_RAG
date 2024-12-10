from langgraph.types import Send
from langgraph.graph import END

import state, nodes


def YorN__parallel(state: state.VisualizerState):
    if state["is_visualizable"].is_visualizable:
        return [
            Send(nodes.get_metrics.__name__, {"input_data": state["input_data"]}),
            Send(nodes.get_charts_name.__name__, {"input_data": state["input_data"]}),
        ]
    else:
        return END


def get_metrics__parallel(state: state.VisualizerState):
    return [
        Send(
            nodes.get_metric_value.__name__,
            {"metric": metric, "input_data": state["input_data"]},
        )
        for metric in state["metrics"]
    ]


def get_charts__parallel(state: state.VisualizerState):
    return [
        Send(
            nodes.get_charts_data.__name__,
            {"input_data": state["input_data"], "state": names},
        )
        for names in state["chart_names"]
    ]
