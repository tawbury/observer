from __future__ import annotations

from typing import Mapping, Optional

from .base import FeatureContext, FeatureExtractor, JsonDict


def get_ts_seconds(record: Mapping[str, object]) -> Optional[float]:
    """
    Accepts:
      - record["ts"] or record["timestamp"] as epoch seconds (int/float or numeric-string)
    Returns:
      - float seconds, or None if missing/unparseable
    """
    v = record.get("ts", record.get("timestamp"))
    if v is None:
        return None
    try:
        return float(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


class TimeFeatures(FeatureExtractor):
    """
    Time-based features:
      - delta_t_prev: time diff from previous observation (seconds, non-negative)
      - bucket_index: external time axis index if provided; else record index
      - relative_position_in_window: [0..1] position inside last_n window
    """

    def extract(self, record: Mapping[str, object], context: FeatureContext) -> JsonDict:
        i = context.index

        ts = get_ts_seconds(record)
        prev_ts = get_ts_seconds(context.records[i - 1]) if i > 0 else None

        if ts is None or prev_ts is None:
            delta_t_prev = 0.0
        else:
            delta_t_prev = max(0.0, ts - prev_ts)

        bucket_index = context.time_axis_index if context.time_axis_index is not None else i

        window_n = max(1, int(context.window_n))
        window_start = max(0, i - window_n + 1)
        window_len = i - window_start + 1

        if window_len <= 1:
            rel_pos = 0.0
        else:
            rel_pos = (i - window_start) / float(window_len - 1)

        return {
            "delta_t_prev": float(delta_t_prev),
            "bucket_index": int(bucket_index),
            "relative_position_in_window": float(rel_pos),
        }
