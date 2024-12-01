from langgraph.graph import END, StateGraph, START

import state, nodes

## Reranking without metadata extraction

## q -> retrival -> reranking -> generation

# fmt: off
graph = StateGraph(state.InternalRAGState)
graph.add_node(nodes.retrieve_documents.__name__, nodes.retrieve_documents)
graph.add_node(nodes.generate_answer.__name__, nodes.generate_answer)
graph.add_node(nodes.rerank_documents.__name__ , nodes.rerank_documents)

graph.add_edge(START, nodes.retrieve_documents.__name__)
graph.add_edge(nodes.retrieve_documents.__name__, nodes.rerank_documents.__name__ )
graph.add_edge(nodes.rerank_documents.__name__ , nodes.generate_answer.__name__)
graph.add_edge(nodes.generate_answer.__name__, END)
# fmt: on

with_rerank_rag = graph.compile()
