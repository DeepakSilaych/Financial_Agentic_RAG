from langgraph.graph import StateGraph, START, END

import state
from nodes import kpi as kpis_nodes

graph = StateGraph(state.OverallState)

# fmt: off
graph.add_node(kpis_nodes.get_required_kpis.__name__, kpis_nodes.get_required_kpis)
graph.add_node(kpis_nodes.get_required_values.__name__, kpis_nodes.get_required_values)
graph.add_node(kpis_nodes.calculate_kpis.__name__, kpis_nodes.calculate_kpis)
graph.add_node(kpis_nodes.generate_answer_from_kpis.__name__, kpis_nodes.generate_answer_from_kpis)

graph.add_edge(START, kpis_nodes.get_required_kpis.__name__)
graph.add_edge(kpis_nodes.get_required_kpis.__name__, kpis_nodes.get_required_values.__name__)
graph.add_edge(kpis_nodes.get_required_values.__name__, kpis_nodes.calculate_kpis.__name__)
graph.add_edge(kpis_nodes.calculate_kpis.__name__, kpis_nodes.generate_answer_from_kpis.__name__)
graph.add_edge(kpis_nodes.generate_answer_from_kpis.__name__, END)
# fmt: on

kpi_workflow = graph.compile()
