from __future__ import annotations

from typing import Mapping, Optional

from .base import FeatureContext, FeatureExtractor, JsonDict


def get_numeric_value(record: Mapping[str, object]) -> Optional[float]:
    """
    Accepts:
      - record["value"] or record["price"]
    Returns:
      - float, or None if missing/unparseable
    """
    v = record.get("value", record.get("price"))
    if v is None:
        return None
    try:
        return float(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


class VolatilityLiteFeatures(FeatureExtractor):
    """
    Volatility-lite features:
      - value_diff_abs: abs diff vs previous value
      - value_diff_pct: abs diff / abs(prev) (guarded)
      - rolling_range_n: max(value)-min(value) within last_n window
    """

    def extract(self, record: Mapping[str, object], context: FeatureContext) -> JsonDict:
        i = context.index
        window_n = max(1, int(context.window_n))
        start = max(0, i - window_n + 1)
        window = context.records[start : i + 1]

        cur_v = get_numeric_value(record)
        prev_v = get_numeric_value(context.records[i - 1]) if i > 0 else None

        if cur_v is None or prev_v is None:
            diff_abs = 0.0
            diff_pct = 0.0
        else:
            diff_abs = abs(cur_v - prev_v)
            denom = abs(prev_v) if abs(prev_v) > 1e-12 else 1e-12
            diff_pct = diff_abs / denom

        values = [v for v in (get_numeric_value(r) for r in window) if v is not None]
        if not values:
            rolling_range_n = 0.0
        else:
            rolling_range_n = float(max(values) - min(values))

        return {
            "value_diff_abs": float(diff_abs),
            "value_diff_pct": float(diff_pct),
            "rolling_range_n": float(rolling_range_n),
        }
