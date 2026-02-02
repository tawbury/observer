from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Protocol


JsonDict = Dict[str, Any]


@dataclass(frozen=True)
class ConditionContext:
    """
    Minimal stateless context for condition evaluation.

    - config: threshold knobs supplied externally
    """
    config: Mapping[str, Any]


class ConditionEvaluator(Protocol):
    """
    Pure evaluator: evaluate(bundle_dict, context) -> dict[str,bool]
    """
    def evaluate(self, bundle: Mapping[str, Any], context: ConditionContext) -> Dict[str, bool]: ...
