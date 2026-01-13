from __future__ import annotations

from typing import Mapping

from .base import FeatureContext, FeatureExtractor, JsonDict
from .time import get_ts_seconds


def get_pattern_id(record: Mapping[str, object]) -> str:
    """
    Accepts:
      - record["pattern"] or record["pattern_id"]
    Returns:
      - string (deterministic), empty string if missing
    """
    v = record.get("pattern", record.get("pattern_id", ""))
    return "" if v is None else str(v)


class FrequencyFeatures(FeatureExtractor):
    """
    Frequency features:
      - event_count_last_n: count of records in last_n window
      - event_density_last_n: count / duration(seconds) within last_n window
      - same_pattern_streak: backward streak length for same pattern id
    """

    def extract(self, record: Mapping[str, object], context: FeatureContext) -> JsonDict:
        i = context.index
        window_n = max(1, int(context.window_n))
        start = max(0, i - window_n + 1)
        window = context.records[start : i + 1]

        event_count_last_n = len(window)

        t_first = get_ts_seconds(window[0]) if window else None
        t_last = get_ts_seconds(window[-1]) if window else None

        if t_first is None or t_last is None:
            # deterministic fallback when timestamps absent
            event_density_last_n = float(event_count_last_n)
        else:
            duration = max(1e-9, float(t_last - t_first))
            event_density_last_n = float(event_count_last_n) / duration

        cur_pat = get_pattern_id(record)
        streak = 1
        j = i - 1
        while j >= 0:
            if get_pattern_id(context.records[j]) == cur_pat:
                streak += 1
                j -= 1
                continue
            break

        return {
            "event_count_last_n": int(event_count_last_n),
            "event_density_last_n": float(event_density_last_n),
            "same_pattern_streak": int(streak),
        }
