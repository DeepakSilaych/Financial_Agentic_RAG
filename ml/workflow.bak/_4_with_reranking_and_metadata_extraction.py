from langgraph.graph import END, StateGraph, START

import state, nodes

## Reranking with metadata extraction

## q -> metadata_extraction -> retrival -> reranking -> generation

# fmt: off
graph = StateGraph(state.InternalRAGState)
graph.add_node(nodes.retrieve_documents_with_metadata.__name__, nodes.retrieve_documents_with_metadata)
graph.add_node(nodes.generate_answer.__name__, nodes.generate_answer)
graph.add_node(nodes.rerank_documents.__name__ , nodes.rerank_documents)
graph.add_node(nodes.extract_metadata.__name__, nodes.extract_metadata)

graph.add_edge(START, nodes.extract_metadata.__name__)
graph.add_edge(nodes.extract_metadata.__name__, nodes.retrieve_documents_with_metadata.__name__)
graph.add_edge(nodes.retrieve_documents_with_metadata.__name__, nodes.rerank_documents.__name__ )
graph.add_edge(nodes.rerank_documents.__name__ , nodes.generate_answer.__name__)
graph.add_edge(nodes.generate_answer.__name__, END)
# fmt: on

with_rerank_and_metadata_extraction_rag = graph.compile()
