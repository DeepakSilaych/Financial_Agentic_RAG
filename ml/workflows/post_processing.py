from langgraph.graph import END, StateGraph, START

import state, nodes, edges


# fmt: off
visualization_agent = StateGraph(state.VisualizerState)
visualization_agent.add_edge(START, nodes.is_visualizable_route.__name__)
visualization_agent.add_node(nodes.is_visualizable_route.__name__,nodes.is_visualizable_route)
visualization_agent.add_node(nodes.get_metrics.__name__, nodes.get_metrics)
visualization_agent.add_node(nodes.get_metric_value.__name__, nodes.get_metric_value)
visualization_agent.add_node(nodes.get_charts_name.__name__, nodes.get_charts_name)
visualization_agent.add_node(nodes.get_charts_data.__name__, nodes.get_charts_data)
visualization_agent.add_node(nodes.get_final_insights.__name__, nodes.get_final_insights)


## Edges

visualization_agent.add_conditional_edges(
    nodes.is_visualizable_route.__name__, 
    edges.YorN__parallel, 
    {nodes.get_metrics.__name__ : nodes.get_metrics.__name__, 
     nodes.get_charts_name.__name__ : nodes.get_charts_name.__name__, 
     END : END}
)

visualization_agent.add_conditional_edges(
    nodes.get_metrics.__name__, 
    edges.get_metrics__parallel, 
    [nodes.get_metric_value.__name__]
)
visualization_agent.add_conditional_edges(
    nodes.get_charts_name.__name__, 
    edges.get_charts__parallel, 
    [nodes.get_charts_data.__name__]
)

visualization_agent.add_edge(
    nodes.get_metric_value.__name__,
    nodes.get_final_insights.__name__
)


visualization_agent.add_edge(
    nodes.get_final_insights.__name__, 
    END
)

visualization_agent.add_edge(
    nodes.get_charts_data.__name__, 
    END
)

# fmt: on

visual_workflow = visualization_agent.compile()
