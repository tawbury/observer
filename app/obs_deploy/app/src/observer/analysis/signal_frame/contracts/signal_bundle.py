from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping


JsonDict = Dict[str, Any]


@dataclass(frozen=True)
class SignalBundle:
    """
    Phase 12 contract (name not used in code): feature vector + condition signals.

    Principles:
    - Pure data, JSON-serializable
    - No scoring, no ranking, no strategy semantics
    - Deterministic for same input
    """

    schema_version: str
    record_key: str

    # Minimal trace metadata (keep small, JSON-safe)
    meta: JsonDict

    # Feature vector
    features: JsonDict

    # Condition signals (condition_name -> bool)
    conditions: Dict[str, bool]

    def to_dict(self) -> JsonDict:
        return {
            "schema_version": self.schema_version,
            "record_key": self.record_key,
            "meta": dict(self.meta),
            "features": dict(self.features),
            "conditions": dict(self.conditions),
        }


def ensure_plain_dict(m: Mapping[str, Any]) -> JsonDict:
    """
    Normalize any Mapping to a plain dict (JSON-friendly).
    """
    return dict(m)
