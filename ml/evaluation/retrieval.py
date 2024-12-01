from dotenv import load_dotenv

load_dotenv()

from .evaluators import retrieval as retrieval_evaluators
from .evaluate import evaluate
from . import metrics

########
from langgraph.graph import END, StateGraph, START
import state, nodes, edges

# fmt: off
retriever_only_graph = StateGraph(state.InternalRAGState)
retriever_only_graph.add_node(nodes.retrieve_documents.__name__, nodes.retrieve_documents)

retriever_only_graph.add_edge(START, nodes.retrieve_documents.__name__)
retriever_only_graph.add_edge(nodes.retrieve_documents.__name__, END)
# fmt: on

retriever_only_workflow = retriever_only_graph.compile()

########

# fmt: off
with_metadata_filtering_graph = StateGraph(state.InternalRAGState)
with_metadata_filtering_graph.add_node(nodes.retrieve_documents_with_metadata.__name__, nodes.retrieve_documents_with_metadata)
with_metadata_filtering_graph.add_node(nodes.extract_metadata.__name__, nodes.extract_metadata)

with_metadata_filtering_graph.add_edge(START, nodes.extract_metadata.__name__)
with_metadata_filtering_graph.add_edge(nodes.extract_metadata.__name__, nodes.retrieve_documents_with_metadata.__name__)
with_metadata_filtering_graph.add_edge(nodes.retrieve_documents_with_metadata.__name__ , END)
# fmt: on

with_metadata_filtering_workflow = with_metadata_filtering_graph.compile()

########


def no_docs(state):
    return {
        "documents": [],
    }


# fmt: off
with_document_grading_graph = StateGraph(state.InternalRAGState)
with_document_grading_graph.add_node(nodes.retrieve_documents.__name__, nodes.retrieve_documents)
with_document_grading_graph.add_node(nodes.grade_documents.__name__, nodes.grade_documents)
with_document_grading_graph.add_node(nodes.rewrite_with_hyde.__name__, nodes.rewrite_with_hyde)
with_document_grading_graph.add_node(no_docs.__name__, no_docs)

with_document_grading_graph.add_edge(START, nodes.retrieve_documents.__name__)
with_document_grading_graph.add_edge(nodes.retrieve_documents.__name__ , nodes.grade_documents.__name__)
with_document_grading_graph.add_conditional_edges(
            nodes.grade_documents.__name__,
            edges.assess_graded_documents,
            {
                "enough_relevant_docs": END,
                "too_many_retries": no_docs.__name__,
                "retry": nodes.rewrite_with_hyde.__name__,
            },
        )
with_document_grading_graph.add_edge(no_docs.__name__, END)
with_document_grading_graph.add_edge(nodes.rewrite_with_hyde.__name__, nodes.retrieve_documents.__name__)
# fmt: on

with_document_grading_workflow = with_document_grading_graph.compile()

########


if __name__ == "__main__":
    experiment = "retrieval"
    indexer = "openparse"

    for dataset in ["Single-Hop-Qualitative"]:
        for name, workflow in (
            ("retriever_only", retriever_only_workflow),
            # ("with_metadata_filtering", with_metadata_filtering_workflow),
            # ("with_document_grading_and_rewriting", with_document_grading_workflow),
        ):
            evaluate(
                experiment_name=f"{experiment}-{name}",
                workflow=workflow,
                workflow_name=name,
                dataset_name=dataset,
                evaluators=[
                    retrieval_evaluators.NonLLMContextPrecision(
                        metric=metrics.LevenshteinStringDistance()
                    ),
                ],
                metadata={
                    "indexer": indexer,
                    "distance_metric": "LevenshteinStringDistance",
                    "search_algorithm": "Hybrid (BM25 + KNN)",
                },
                # max_concurrency=4,  # uncomment for latency experiment
            )
