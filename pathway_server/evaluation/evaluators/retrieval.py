from typing import Dict
import numpy as np
from langsmith.schemas import Example, Run
from langsmith.evaluation import EvaluationResult

from .base import BaseEvaluator
from ..metrics import BaseMetric, ContainsString


class NonLLMContextPrecision(BaseEvaluator):
    def __init__(self, metric: BaseMetric = ContainsString(), threshold: float = 0.9):
        self.metric = metric
        self.threshold = threshold

    def evaluate(self, run: Run, example: Example) -> EvaluationResult:
        retrieved_contexts = run.outputs["documents"]  # type: ignore
        retrieved_contexts = [doc.page_content for doc in retrieved_contexts]
        reference_context = example.outputs["reference_context"]  # type: ignore

        if len(retrieved_contexts) == 0:
            return EvaluationResult(key=self.__class__.__name__, score=0)

        # Calculate the score for each retrieved context
        scores = []
        for doc in retrieved_contexts:
            doc = doc.replace("\n", " ")
            doc = doc.replace("<br>", " ")
            doc = doc.replace("*", "")

            _scores = []
            for i in range(len(doc)):
                if i + len(reference_context) > len(doc):
                    content = doc[i:]
                else:
                    content = doc[i : i + len(reference_context)]
                _scores.append(self.metric.score(content, reference_context))
            scores.append(max(_scores))

        # Convert scores to binary
        scores = [1 if score >= self.threshold else 0 for score in scores]

        # Calculate MRR
        scores = [1 / (i + 1) if score != 0 else 0 for i, score in enumerate(scores)]

        return EvaluationResult(key=self.__class__.__name__, score=max(scores))
