from langgraph.graph import END, StateGraph, START

import state, nodes, edges

# fmt: off
graph = StateGraph(state.InternalRAGState)

graph.add_node(nodes.retrieve_documents.__name__, nodes.retrieve_documents)
graph.add_node(nodes.extract_metadata.__name__, nodes.extract_metadata)
graph.add_node(nodes.grade_documents.__name__,nodes.grade_documents)
graph.add_node(nodes.generate_answer.__name__, nodes.generate_answer)
graph.add_node(nodes.rewrite_with_hyde.__name__ , nodes.rewrite_with_hyde)
graph.add_node(nodes.search_web.__name__ ,nodes.search_web)
graph.add_node(nodes.retrieve_documents_with_metadata.__name__,nodes.retrieve_documents_with_metadata)

graph.add_edge(START, nodes.extract_metadata.__name__)
graph.add_edge(nodes.extract_metadata.__name__, nodes.retrieve_documents.__name__)
graph.add_edge(nodes.retrieve_documents.__name__ , nodes.grade_documents.__name__)
graph.add_conditional_edges(
    nodes.grade_documents.__name__,
    edges.assess_graded_documents,
    {
        nodes.rewrite_with_hyde.__name__: nodes.rewrite_with_hyde.__name__,
        nodes.search_web.__name__: nodes.search_web.__name__,
        nodes.generate_answer.__name__: nodes.generate_answer.__name__,
    },
)
graph.add_edge(nodes.rewrite_with_hyde.__name__ , nodes.retrieve_documents_with_metadata.__name__)
graph.add_edge(nodes.retrieve_documents_with_metadata.__name__ , nodes.grade_documents.__name__)
graph.add_edge(nodes.search_web.__name__ , nodes.generate_answer.__name__)
graph.add_edge(nodes.generate_answer.__name__, END)
# fmt: on

with_doc_relevance = graph.compile()
