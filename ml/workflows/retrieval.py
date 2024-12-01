from langgraph.graph import END, StateGraph, START

import state, nodes
from config import WORKFLOW_SETTINGS

# fmt: off
graph = StateGraph(state.InternalRAGState)

if WORKFLOW_SETTINGS["query_expansion"]:
    graph.add_node(nodes.expand_question.__name__, nodes.expand_question)

    graph.add_edge(START, nodes.expand_question.__name__)

if WORKFLOW_SETTINGS["metadata_filtering"]:
    graph.add_node(nodes.extract_metadata.__name__, nodes.extract_metadata)
    graph.add_node("retriever", nodes.retrieve_documents_with_metadata)

    if WORKFLOW_SETTINGS["query_expansion"]:
        graph.add_edge(nodes.expand_question.__name__, nodes.extract_metadata.__name__)
    else:
        graph.add_edge(START, nodes.extract_metadata.__name__)
    graph.add_edge(nodes.extract_metadata.__name__, "retriever")
else:
    graph.add_node("retriever", nodes.retrieve_documents)

    if WORKFLOW_SETTINGS["query_expansion"]:
        graph.add_edge(nodes.expand_question.__name__, "retriever")
    else:
        graph.add_edge(START, "retriever")

if WORKFLOW_SETTINGS["grade_documents"]:
    graph.add_node(nodes.grade_documents.__name__, nodes.grade_documents)

    graph.add_edge("retriever", nodes.grade_documents.__name__)

if WORKFLOW_SETTINGS["reranking"]:
    graph.add_node(nodes.rerank_documents.__name__, nodes.rerank_documents)

    if WORKFLOW_SETTINGS["grade_documents"]:
        graph.add_edge(nodes.grade_documents.__name__, nodes.rerank_documents.__name__)
    else:
        graph.add_edge("retriever", nodes.rerank_documents.__name__)

    graph.add_edge(nodes.rerank_documents.__name__, END)

if not WORKFLOW_SETTINGS["reranking"] and not WORKFLOW_SETTINGS["grade_documents"]:
    graph.add_edge("retriever", END)
# fmt: on

retrieval = graph.compile()
