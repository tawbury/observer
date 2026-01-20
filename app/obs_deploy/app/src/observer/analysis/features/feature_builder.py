# observer/analysis/features/feature_builder.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from .feature_registry import FeatureRegistry
from .feature_validator import FeatureValidator


@dataclass(frozen=True)
class FeatureBuildContext:
    """
    Context for feature building.

    Notes:
      - Context carries partition-level identifiers only.
      - Strategy semantics are explicitly forbidden.
    """
    symbol: Optional[str]
    date_yyyymmdd: str


class FeatureBuilder:
    """
    Build 'observation summary' features from raw observation records.

    Rules:
      - Emit only registered features (schema-first).
      - No strategy/signal/scoring logic.
      - Missing/invalid timestamps are ignored safely.
    """

    TIMESTAMP_KEY = "timestamp"  # expected epoch seconds (int)

    def __init__(self, registry: FeatureRegistry) -> None:
        self.registry = registry
        self.validator = FeatureValidator(registry)

    def build_from_records(
        self,
        ctx: FeatureBuildContext,
        records: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build a single feature row for the given partition (symbol/date).

        Returns:
          Dict[str, Any] validated against FeatureSchema.
        """
        timestamps: List[int] = []
        record_count = 0

        for rec in records:
            record_count += 1
            ts = rec.get(self.TIMESTAMP_KEY)
            if isinstance(ts, int):
                timestamps.append(ts)

        emitted: Dict[str, Any] = {}

        # --------------------------------------------------
        # record_count
        # --------------------------------------------------
        if self.registry.has("record_count"):
            emitted["record_count"] = record_count

        # --------------------------------------------------
        # time-based features
        # --------------------------------------------------
        if timestamps:
            timestamps.sort()
            first_ts = timestamps[0]
            last_ts = timestamps[-1]
            span = max(0, last_ts - first_ts)

            if self.registry.has("first_timestamp"):
                emitted["first_timestamp"] = first_ts

            if self.registry.has("last_timestamp"):
                emitted["last_timestamp"] = last_ts

            if self.registry.has("timespan_seconds"):
                emitted["timespan_seconds"] = span

            if self.registry.has("avg_interval_seconds"):
                if len(timestamps) > 1:
                    avg_interval = span / float(len(timestamps) - 1)
                else:
                    avg_interval = 0.0
                emitted["avg_interval_seconds"] = avg_interval
        else:
            # No valid timestamps → defaults handled by validator
            pass

        # Validate against schema (required/defaults/dtypes)
        return self.validator.validate_row(emitted)
