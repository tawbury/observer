# observer/analysis/features/feature_schema.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional


FeatureDType = Literal["int", "float", "str", "bool"]


@dataclass(frozen=True)
class FeatureSpec:
    """
    Schema-light feature specification.

    Rules:
      - Observation summary only (no score/signal/prediction).
      - All features MUST be registered here before emission.
    """
    key: str
    dtype: FeatureDType
    description: str
    required: bool = True
    default: Optional[Any] = None


@dataclass(frozen=True)
class FeatureSchema:
    """
    Feature schema container.
    """
    version: str
    features: Dict[str, FeatureSpec]


# ----------------------------------------------------------------------
# Decision Feature Schema v1
# ----------------------------------------------------------------------

def load_decision_feature_schema_v1() -> FeatureSchema:
    """
    Decision Feature Schema v1.0.0

    Scope:
      - Raw observation aggregation
      - Scalping & swing common denominator
      - Time/volume/frequency based summaries only
    """

    features: Dict[str, FeatureSpec] = {
        # --------------------------------------------------
        # Volume / count
        # --------------------------------------------------
        "record_count": FeatureSpec(
            key="record_count",
            dtype="int",
            description="Number of raw observation records aggregated.",
            required=True,
            default=0,
        ),

        # --------------------------------------------------
        # Time span
        # --------------------------------------------------
        "first_timestamp": FeatureSpec(
            key="first_timestamp",
            dtype="int",
            description="Epoch timestamp of the first observation in the window.",
            required=False,
        ),
        "last_timestamp": FeatureSpec(
            key="last_timestamp",
            dtype="int",
            description="Epoch timestamp of the last observation in the window.",
            required=False,
        ),
        "timespan_seconds": FeatureSpec(
            key="timespan_seconds",
            dtype="int",
            description="Time span between first and last observation (seconds).",
            required=False,
            default=0,
        ),

        # --------------------------------------------------
        # Frequency
        # --------------------------------------------------
        "avg_interval_seconds": FeatureSpec(
            key="avg_interval_seconds",
            dtype="float",
            description="Average interval between observations (seconds).",
            required=False,
            default=0.0,
        ),
    }

    return FeatureSchema(
        version="v1.0.0",
        features=features,
    )
