from typing import Dict

from langsmith.schemas import Example, Run
from langsmith.evaluation import EvaluationResult


class BaseEvaluator:
    """Base class for evaluators, including support for Langsmith default evaluators."""

    def info(self) -> Dict[str, str]:
        """Returns information about the evaluator."""
        return {"name": self.__class__.__name__}

    def evaluate(self, run: Run, example: Example) -> EvaluationResult:
        """Default evaluation method, should be overridden by subclasses."""
        raise NotImplementedError
