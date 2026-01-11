from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, Iterator, Mapping, Optional, Protocol, runtime_checkable


# ---------------------------------------------------------------------
# Phase 14 Contract Notes (LOCKED INTENT)
#
# This module must NOT:
# - interpret conditions
# - score / rank / prioritize
# - select strategies
# - keep state (cache, accumulation)
# - touch execution/broker
#
# It MUST:
# - translate SignalBundle (or dataset-loaded row) to decision_pipeline input contract
# - do so deterministically, minimally, and one-way
# ---------------------------------------------------------------------


@runtime_checkable
class _DictLike(Protocol):
    """Minimal protocol for objects convertible to dict without meaning changes."""
    def to_dict(self) -> Mapping[str, Any]: ...


def _to_mapping(obj: Any) -> Mapping[str, Any]:
    """
    Convert a SignalBundle-ish object to a read-only mapping representation.

    Accepted:
    - dict / Mapping
    - dataclass (asdict)
    - objects with .to_dict()
    - objects with __dict__ (fallback)
    """
    if obj is None:
        raise TypeError("signal must not be None")

    if isinstance(obj, Mapping):
        return obj

    if is_dataclass(obj):
        return asdict(obj)

    if isinstance(obj, _DictLike):
        return obj.to_dict()

    if hasattr(obj, "__dict__"):
        # NOTE: This is a fallback; do not mutate the returned mapping.
        return dict(getattr(obj, "__dict__"))

    raise TypeError(f"Unsupported signal object type: {type(obj)!r}")


class SignalDecisionAdapter:
    """
    Phase 14 core adapter: SignalBundle -> DecisionInputContract

    Important:
    - This class is intentionally "thin".
    - The concrete DecisionInput type will be fixed AFTER we re-check
      decision_pipeline contracts in Phase 14 Step 1.
    """

    def __init__(self) -> None:
        # Stateless by design: no fields stored.
        pass

    def adapt(self, signal: Any) -> Dict[str, Any]:
        """
        Convert a single SignalBundle-ish object to a decision_pipeline-consumable input.

        Returns a plain dict for now (skeleton stage).
        In Step 1 completion, this will be upgraded to the actual DecisionInputContract type,
        or a dict that runner accepts without modification.

        Rules:
        - deterministic
        - minimal fields
        - no derived calculations
        """
        src = _to_mapping(signal)

        # -----------------------------------------------------------------
        # TODO (Phase 14 Step 1):
        # Decide the EXACT target contract:
        # - Which decision_pipeline runner input does it require?
        # - Which fields are mandatory?
        #
        # Then replace this mapping with explicit field-to-field translation.
        # -----------------------------------------------------------------

        # Skeleton minimal pass-through:
        # - Keep only "known-safe" identifiers if present.
        # - Preserve the rest in "meta" without interpretation.
        decision_input: Dict[str, Any] = {}

        # Phase 14 top-level identifiers (LOCKED)
        for k in (
                "build_id",
                "session_id",
                "source",
                "symbol",
                "market",
                "captured_at",
        ):
            if k in src:
                decision_input[k] = src[k]

        # Common signal identity candidates
        for k in ("symbol", "ticker", "market", "captured_at", "timestamp", "time"):
            if k in src and k not in decision_input:
                decision_input[k] = src[k]

        # Keep original source payload as meta (read-only usage downstream)
        # NOTE: meta must not be used here for decision logic.
        decision_input["meta"] = dict(src)

        return decision_input

    def adapt_many(self, signals: Iterable[Any]) -> Iterator[Dict[str, Any]]:
        """
        Batch adapter (streaming).
        Must remain lazy: no buffering / accumulation.
        """
        for s in signals:
            yield self.adapt(s)


def adapt_many(signals: Iterable[Any]) -> Iterator[Dict[str, Any]]:
    """
    Functional wrapper for convenience / testing.
    """
    return SignalDecisionAdapter().adapt_many(signals)
