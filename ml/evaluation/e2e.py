from dotenv import load_dotenv

load_dotenv()

from workflows.repeater import repeater
from .evaluators import e2e as e2e_evaluators
from .evaluate import evaluate

########
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

if __name__ == "__main__":
    experiment = "e2e"
    indexer = "openparse"

    for dataset in ["Multi-Hop-Qualitative"]:
        for name, workflow in (
            ("repeater", repeater),
            # ("with_metadata_filtering", with_metadata_filtering),
        ):
            evaluate(
                experiment_name=f"{experiment}-{name}",
                workflow=workflow,
                workflow_name=name,
                dataset_name=dataset,
                evaluators=[
                    e2e_evaluators.LLMFaithfulness(),
                    e2e_evaluators.LLMResponseRelevancy(),
                    e2e_evaluators.LLMCorrectness(),
                ],
                metadata={
                    "indexer": indexer,
                    "search_algorithm": "Hybrid (BM25 + KNN)",
                },
                # max_concurrency=4,  # uncomment for latency experiment
            )
