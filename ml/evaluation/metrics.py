from typing import Dict
from rapidfuzz.distance import Levenshtein


class BaseMetric:
    """Base class for metrics, including support for Langsmith."""

    def info(self) -> Dict[str, str]:
        """Returns information about the metric."""
        return {"name": self.__class__.__name__}

    def score(self, response: str, reference: str) -> float:
        """Default scoring method, can be overridden by subclasses."""
        raise NotImplementedError


class ContainsString(BaseMetric):
    """A metric that scores based on whether the reference contains the reponse string."""

    def score(self, response: str, reference: str) -> float:
        return float(response in reference)


class LevenshteinStringDistance(BaseMetric):
    """A metric that scores based on whether the reference contains the reponse string."""

    def score(self, response: str, reference: str) -> float:
        return 1 - Levenshtein.normalized_distance(reference, response)
