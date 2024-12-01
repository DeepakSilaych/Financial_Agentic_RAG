from langgraph.graph import END, StateGraph, START

import state, nodes, edges


# fmt: off
visualization_agent = StateGraph(state.VisualizerState)
visualization_agent.add_edge(START, nodes.is_visualizable_route.__name__)
visualization_agent.add_node(nodes.is_visualizable_route.__name__,nodes.is_visualizable_route)
visualization_agent.add_node(nodes.get_metrics.__name__, nodes.get_metrics)
visualization_agent.add_node(nodes.get_metric_value.__name__, nodes.get_metric_value)
visualization_agent.add_node(nodes.get_insights.__name__, nodes.get_insights)
visualization_agent.add_node(nodes.get_charts_desc.__name__, nodes.get_charts_desc)
visualization_agent.add_node(nodes.generate_chart_code_and_save.__name__, nodes.generate_chart_code_and_save)
visualization_agent.add_node(nodes.charts_final_output.__name__, nodes.charts_final_output)
visualization_agent.add_conditional_edges(nodes.is_visualizable_route.__name__, edges.YorN__parallel, {nodes.get_metrics.__name__ : nodes.get_metrics.__name__, nodes.get_charts_desc.__name__ : nodes.get_charts_desc.__name__, END : END})
visualization_agent.add_conditional_edges(nodes.get_metrics.__name__, edges.get_metrics__parallel, [nodes.get_metric_value.__name__])
visualization_agent.add_conditional_edges(nodes.get_charts_desc.__name__, edges.get_charts__parallel, [nodes.generate_chart_code_and_save.__name__])

visualization_agent.add_edge(nodes.get_metric_value.__name__, nodes.get_insights.__name__)
visualization_agent.add_edge(nodes.generate_chart_code_and_save.__name__, nodes.charts_final_output.__name__)
visualization_agent.add_edge(nodes.get_insights.__name__, END)
visualization_agent.add_edge(nodes.charts_final_output.__name__, END)
# fmt: on

visual_workflow = visualization_agent.compile()
