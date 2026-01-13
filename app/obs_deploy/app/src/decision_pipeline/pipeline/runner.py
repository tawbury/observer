from __future__ import annotations

from typing import Any, Dict

from .extract import Extractor
from .transform import Transformer
from .evaluate import Evaluator
from .decide import Decider


class DecisionPipelineRunner:
    """
    Decision Pipeline Runner (ETEDA, Act 제외)

    흐름:
        Extract → Transform → Evaluate → Decide
    """

    def __init__(self) -> None:
        self._extractor = Extractor()
        self._transformer = Transformer()
        self._evaluator = Evaluator()
        self._decider = Decider()

    def run(
        self,
        context: Dict[str, Any],
        *,
        strategy_name: str | None = None,
    ) -> Dict[str, Any]:

        raw = self._extractor.extract(context)
        transformed = self._transformer.transform(raw)
        evaluated = self._evaluator.evaluate(transformed)
        decided = self._decider.decide(
            evaluated,
            strategy_name=strategy_name,
        )

        return decided
