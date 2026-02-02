from __future__ import annotations

from typing import Any, Dict, Mapping

from .base import ConditionContext, ConditionEvaluator
from ..features.time import get_ts_seconds
from ..features.frequency import get_pattern_id


class WindowConditions(ConditionEvaluator):
    """
    Window conditions (bool only):
      - consecutive_events_ge_n
      - pattern_reappeared_within_t

    Notes:
    - pattern_reappeared_within_t uses meta["records_window"] when present.
    """

    def evaluate(self, bundle: Mapping[str, Any], context: ConditionContext) -> Dict[str, bool]:
        features = bundle.get("features", {}) or {}
        meta = bundle.get("meta", {}) or {}
        cfg = context.config

        n = int(cfg.get("consecutive_events_ge_n", 3))
        t = float(cfg.get("pattern_reappeared_within_t", 60.0))  # seconds

        streak = int(features.get("same_pattern_streak", 1))
        consecutive_events_ge_n = (streak >= n)

        # meta.records_window is injected by the pipeline (JSON-safe)
        records_window = meta.get("records_window")
        pattern_reappeared_within_t = False

        if isinstance(records_window, list) and records_window:
            cur = records_window[-1]
            cur_pat = get_pattern_id(cur)
            cur_ts = get_ts_seconds(cur)

            if cur_ts is not None:
                # scan backwards (excluding current) while within t seconds
                for past in reversed(records_window[:-1]):
                    past_ts = get_ts_seconds(past)
                    if past_ts is None:
                        continue
                    if (cur_ts - past_ts) > t:
                        break
                    if get_pattern_id(past) == cur_pat:
                        pattern_reappeared_within_t = True
                        break

        return {
            "consecutive_events_ge_n": consecutive_events_ge_n,
            "pattern_reappeared_within_t": pattern_reappeared_within_t,
        }
