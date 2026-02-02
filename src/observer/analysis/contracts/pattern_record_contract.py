# observer/analysis/contracts/pattern_record_contract.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class PatternRecordContract:
    """
    Phase 4 output contract (read-only).

    This contract MUST NOT import or depend on Observer-Core classes.
    It represents the persisted JSON structure only.
    """

    # --- core identifiers ---
    session_id: str
    generated_at: str

    # --- observation payload ---
    observation: Dict[str, Any]

    # --- metadata (always present after Phase 4) ---
    schema: Dict[str, Any]
    quality: Dict[str, Any]
    interpretation: Dict[str, Any]

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "PatternRecordContract":
        """
        Create contract from JSON-decoded dict.
        Fail fast if mandatory fields are missing.
        """
        metadata = raw.get("metadata", {})

        return cls(
            session_id=metadata.get("session_id", ""),
            generated_at=metadata.get("generated_at", ""),
            observation=raw.get("observation", {}),
            schema=metadata.get("_schema", {}),
            quality=metadata.get("_quality", {}),
            interpretation=metadata.get("_interpretation", {}),
        )

    # -------------------------
    # Convenience accessors
    # -------------------------

    def pattern_type(self) -> Optional[str]:
        return self.interpretation.get("pattern_type")

    def timestamp(self) -> Optional[float]:
        return self.observation.get("timestamp")

    def guard_passed(self) -> bool:
        return bool(self.quality.get("guard_passed", False))
