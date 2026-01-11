from __future__ import annotations

from typing import Any, Dict, Mapping

from .base import ConditionContext, ConditionEvaluator


class ThresholdConditions(ConditionEvaluator):
    """
    Threshold conditions (bool only):
      - value_change_exceeds_x
      - event_frequency_exceeds_n
    """

    def evaluate(self, bundle: Mapping[str, Any], context: ConditionContext) -> Dict[str, bool]:
        features = bundle.get("features", {}) or {}
        cfg = context.config

        x = float(cfg.get("value_change_exceeds_x", 0.01))   # default: 1%
        n = int(cfg.get("event_frequency_exceeds_n", 20))

        value_diff_pct = float(features.get("value_diff_pct", 0.0))
        event_count_last_n = int(features.get("event_count_last_n", 0))

        return {
            "value_change_exceeds_x": (value_diff_pct > x),
            "event_frequency_exceeds_n": (event_count_last_n > n),
        }
