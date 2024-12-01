from langgraph.types import Send
from langgraph.graph import END

import state, nodes


def YorN__parallel(state: state.VisualizerState):
    if state["is_visualizable"].is_visualizable:
        return [
            Send(nodes.get_metrics.__name__, {"input_data": state["input_data"]}),
            Send(nodes.get_charts_desc.__name__, {"input_data": state["input_data"]}),
        ]
    else:
        return END


def get_metrics__parallel(state: state.VisualizerState):
    return [
        Send(nodes.get_metric_value.__name__, metric) for metric in state["metrics"]
    ]


def get_charts__parallel(state: state.VisualizerState):
    return [
        Send(nodes.generate_chart_code_and_save.__name__, chart)
        for chart in state["charts"]
    ]
