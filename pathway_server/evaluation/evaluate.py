from typing import List, Dict, Optional

from langchain_core.runnables import Runnable
from langsmith import Client
from langsmith.evaluation import evaluate as langsmith_evaluate

import config
from .evaluators.base import BaseEvaluator


def evaluate(
    experiment_name: str,
    workflow: Runnable,
    dataset_name: str,
    evaluators: List[BaseEvaluator] | BaseEvaluator,
    workflow_name: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
    limit: Optional[int] = None,
    dataset_reps: int = 1,
    **kwargs,
):
    if not workflow_name:
        workflow_name = workflow.__class__.__name__
    if not isinstance(evaluators, list):
        evaluators = [evaluators]
    if not metadata:
        metadata = {}

    client = Client()

    return langsmith_evaluate(
        workflow.invoke,
        data=client.list_examples(dataset_name=dataset_name, limit=limit),
        evaluators=[ev.evaluate for ev in evaluators],
        max_concurrency=config.EVAL_QUERY_BATCH_SIZE,
        experiment_prefix=experiment_name,
        metadata={"evaluators": [ev.info for ev in evaluators]} | metadata,
        num_repetitions=dataset_reps,
        **kwargs,
    )
