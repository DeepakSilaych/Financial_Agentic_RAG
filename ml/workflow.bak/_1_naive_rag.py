from langgraph.graph import END, StateGraph, START

import state, nodes

# fmt: off
graph = StateGraph(state.InternalRAGState)
graph.add_node(nodes.retrieve_documents.__name__, nodes.retrieve_documents)
graph.add_node(nodes.generate_answer.__name__, nodes.generate_answer)

graph.add_edge(START, nodes.retrieve_documents.__name__)
graph.add_edge(nodes.retrieve_documents.__name__, nodes.generate_answer.__name__)
graph.add_edge(nodes.generate_answer.__name__, END)
# fmt: on

naive_rag = graph.compile()
