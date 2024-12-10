from dotenv import load_dotenv

load_dotenv()

from workflows.simple_parallel import simple_parallel
from .evaluators import e2e as e2e_evaluators
from .evaluators import retrieval as retrieval_evaluators
from .evaluate import evaluate

if __name__ == "__main__":
    experiment = "e2e"
    indexer = "openparse"

    for dataset in ["Multi-Hop-Full-Filtered"]:
        for name, workflow in (
            ("simple_parallel", simple_parallel),
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
                    retrieval_evaluators.NonLLMContextPrecision(),
                ],
                metadata={
                    "indexer": indexer,
                    "search_algorithm": "Hybrid (BM25 + KNN)",
                },
                limit=30,
                # max_concurrency=4,  # uncomment for latency experiment
            )
