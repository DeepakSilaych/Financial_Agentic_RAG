from langgraph.graph import END, StateGraph, START
from langgraph.checkpoint.memory import MemorySaver
import state, nodes, edges
from config import WORKFLOW_SETTINGS

# fmt: off
graph = StateGraph(state.InternalRAGState)

graph.add_node(nodes.do_task.__name__, nodes.do_task)

graph.add_edge(START, nodes.do_task.__name__)
graph.add_edge(nodes.do_task.__name__, END)

# fmt: on
task_handler = graph.compile()
