from langgraph.graph import END, StateGraph, START

import state, nodes

graph = StateGraph(state.InternalRAGState)
graph.add_node(nodes.expand_question.__name__, nodes.expand_question)
graph.add_node(nodes.retrieve_documents.__name__, nodes.retrieve_documents)
graph.add_node(nodes.generate_answer.__name__, nodes.generate_answer)
graph.add_edge(START, nodes.expand_question.__name__)
graph.add_edge(nodes.expand_question.__name__, nodes.retrieve_documents.__name__)
graph.add_edge(nodes.retrieve_documents.__name__, nodes.generate_answer.__name__)
graph.add_edge(nodes.generate_answer.__name__, END)

with_question_expansion = graph.compile()
