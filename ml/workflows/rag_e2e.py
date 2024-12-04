from langgraph.graph import END, StateGraph, START

import state, nodes, edges
from config import WORKFLOW_SETTINGS
import sys
sys.setrecursionlimit(1000)

# fmt: off
graph = StateGraph(state.InternalRAGState)

graph.add_node(nodes.generate_answer_with_citation_state.__name__, nodes.generate_answer_with_citation_state)

if WORKFLOW_SETTINGS["assess_graded_documents"] or WORKFLOW_SETTINGS["assess_metadata_filters"] or WORKFLOW_SETTINGS["check_hallucination"] or WORKFLOW_SETTINGS["grade_answer"]:
    graph.add_node(nodes.generate_web_answer.__name__, nodes.generate_web_answer)
    graph.add_node(nodes.search_web.__name__, nodes.search_web)

    graph.add_edge(nodes.search_web.__name__, nodes.generate_web_answer.__name__)
    if WORKFLOW_SETTINGS["grade_web_answer"]:
        graph.add_node(nodes.grade_web_answer.__name__ , nodes.grade_web_answer)

        graph.add_edge(nodes.generate_web_answer.__name__ , nodes.grade_web_answer.__name__)
        graph.add_edge(nodes.grade_web_answer.__name__ , END)
    else:
        graph.add_edge(nodes.generate_web_answer.__name__, END)

if WORKFLOW_SETTINGS["rewrite_with_hyde"]:
    graph.add_node("query_rewriter", nodes.rewrite_with_hyde)
else:
    graph.add_node("query_rewriter", nodes.rewrite_question)

if WORKFLOW_SETTINGS["metadata_filtering"]:
    graph.add_node(nodes.extract_metadata.__name__, nodes.extract_metadata)
    if WORKFLOW_SETTINGS["metadata_filtering_with_quant_qual"]:
        graph.add_node("retriever", nodes.retrieve_documents_with_quant_qual)
    else:
        graph.add_node("retriever", nodes.retrieve_documents_with_metadata)

    graph.add_edge(START, nodes.extract_metadata.__name__)
    graph.add_edge(nodes.extract_metadata.__name__, "retriever")

    if WORKFLOW_SETTINGS["assess_metadata_filters"]:
        _ok_node = ""
        if WORKFLOW_SETTINGS["grade_documents"]:
            _ok_node = nodes.grade_documents.__name__
        elif WORKFLOW_SETTINGS["reranking"]:
            _ok_node = nodes.rerank_documents.__name__
        else:
            _ok_node = nodes.generate_answer_with_citation_state.__name__
        graph.add_conditional_edges(
            "retriever",
            edges.assess_metadata_filter,
            {
                "ok": _ok_node,
                "too_many_retries": nodes.search_web.__name__,
                "retry": "query_rewriter",
            },
        )
else:
    graph.add_node("retriever", nodes.retrieve_documents)

    graph.add_edge(START, "retriever")



if WORKFLOW_SETTINGS["grade_documents"]:
    graph.add_node(nodes.grade_documents.__name__, nodes.grade_documents)

    if not WORKFLOW_SETTINGS["assess_metadata_filters"]:
        graph.add_edge("retriever", nodes.grade_documents.__name__)

    if WORKFLOW_SETTINGS["assess_graded_documents"]:
        graph.add_conditional_edges(
            nodes.grade_documents.__name__,
            edges.assess_graded_documents,
            {
                "enough_relevant_docs": nodes.rerank_documents.__name__ if WORKFLOW_SETTINGS["reranking"] else nodes.generate_answer_with_citation_state.__name__,
                "too_many_retries": nodes.search_web.__name__,
                "retry": "query_rewriter",
            },
        )
    elif WORKFLOW_SETTINGS["reranking"]:
        graph.add_edge(nodes.grade_documents.__name__, nodes.rerank_documents.__name__)
    else:
        graph.add_edge(nodes.grade_documents.__name__, nodes.generate_answer_with_citation_state.__name__)

if WORKFLOW_SETTINGS["reranking"]:
    graph.add_node(nodes.rerank_documents.__name__, nodes.rerank_documents)

    if not WORKFLOW_SETTINGS["grade_documents"]:
        graph.add_edge("retriever", nodes.rerank_documents.__name__)

    graph.add_edge(nodes.rerank_documents.__name__, nodes.generate_answer_with_citation_state.__name__)

if not WORKFLOW_SETTINGS["reranking"] and not WORKFLOW_SETTINGS["grade_documents"]:
    graph.add_edge("retriever", nodes.generate_answer_with_citation_state.__name__)

if WORKFLOW_SETTINGS["grade_answer"]:
    graph.add_node(nodes.grade_answer.__name__, nodes.grade_answer)

if WORKFLOW_SETTINGS["calculator"]:
    graph.add_node(nodes.calc_agent.__name__, nodes.calc_agent)

if WORKFLOW_SETTINGS["check_hallucination"]:
    if WORKFLOW_SETTINGS["hallucination_checker"] == "hhem":
        graph.add_node("hallucination_checker", nodes.check_hallucination_hhem)
    else:
        graph.add_node("hallucination_checker", nodes.check_hallucination)

    if WORKFLOW_SETTINGS['calculator']:
        graph.add_edge(nodes.generate_answer_with_citation_state.__name__, nodes.calc_agent.__name__)
        graph.add_edge(nodes.calc_agent.__name__, "hallucination_checker")

        graph.add_conditional_edges(
            "hallucination_checker",
            edges.assess_hallucination,
            {
                "retry": nodes.generate_answer_with_citation_state.__name__,
                "too_many_retries": nodes.search_web.__name__,
                "no_hallucination": nodes.grade_answer.__name__ if WORKFLOW_SETTINGS["grade_answer"] else END,
            },
        )

    
    else:
        graph.add_edge(nodes.generate_answer_with_citation_state.__name__, "hallucination_checker")
        graph.add_conditional_edges(
            "hallucination_checker",
            edges.assess_hallucination,
            {
                "retry": nodes.generate_answer_with_citation_state.__name__,
                "too_many_retries": nodes.search_web.__name__,
                "no_hallucination": nodes.grade_answer.__name__ if WORKFLOW_SETTINGS["grade_answer"] else END,
            },
        )

if WORKFLOW_SETTINGS["grade_answer"]:
    if not WORKFLOW_SETTINGS["check_hallucination"]:
        if WORKFLOW_SETTINGS["calculator"]:
            graph.add_edge(nodes.generate_answer_with_citation_state.__name__, nodes.calc_agent.__name__)
            graph.add_edge(nodes.calc_agent.__name__, nodes.grade_answer.__name__)
        else:
            graph.add_edge(nodes.generate_answer_with_citation_state.__name__, nodes.grade_answer.__name__)

    graph.add_conditional_edges(
        nodes.grade_answer.__name__, 
        edges.assess_answer,
        {
            "ok" : END, 
            "retry": "query_rewriter",
            "too_many_retries": nodes.search_web.__name__,
        },
    )

graph.add_edge("query_rewriter", "retriever")

if not WORKFLOW_SETTINGS["grade_answer"] and not WORKFLOW_SETTINGS["check_hallucination"]:
    if WORKFLOW_SETTINGS['calculator']:
        graph.add_edge(nodes.generate_answer_with_citation_state.__name__, nodes.calc_agent.__name__)
        graph.add_edge(nodes.calc_agent.__name__, END)
    else:
        graph.add_edge(nodes.generate_answer_with_citation_state.__name__, END)
# fmt: on

if WORKFLOW_SETTINGS["with_site_blocker"]:
    rag_e2e = graph.compile(
        interrupt_after=[
            nodes.search_web.__name__,
        ]
    )
else:
    rag_e2e = graph.compile()
