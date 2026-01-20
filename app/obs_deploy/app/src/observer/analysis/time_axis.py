from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from .contracts.pattern_record_contract import PatternRecordContract


class Phase5TimeAxisError(Exception):
    """Raised when time axis normalization fails."""


# =====================================================================
# Config & View models (Phase 5)
# =====================================================================

@dataclass(frozen=True)
class TimeAxisConfig:
    bucket_seconds: float = 1.0
    allow_missing_timestamps: bool = True
    enforce_monotonic: bool = True


@dataclass
class TimeBucket:
    bucket_index: int
    start_ts: float
    records: List[PatternRecordContract]


@dataclass
class TimeSeriesPatternView:
    config: TimeAxisConfig
    buckets: List[TimeBucket]
    gaps: List[Tuple[int, int]]
    unbucketed: List[PatternRecordContract]

    @property
    def total_buckets(self) -> int:
        return len(self.buckets)

    @property
    def total_records(self) -> int:
        return sum(len(b.records) for b in self.buckets) + len(self.unbucketed)


# =====================================================================
# Public API (Phase 5)
# =====================================================================

def normalize_time_axis(
    records: List[PatternRecordContract],
    *,
    config: Optional[TimeAxisConfig] = None,
) -> TimeSeriesPatternView:
    """
    Normalize PatternRecordContracts onto a discrete time axis.

    Timestamp policy (Phase 5 canonical):
    - Only observation.snapshot.meta timestamps are valid
    - generated_at is NOT used as a fallback
    """
    cfg = config or TimeAxisConfig()

    extracted: List[Tuple[float, PatternRecordContract]] = []
    unbucketed: List[PatternRecordContract] = []

    for rec in records:
        ts = _extract_timestamp(rec)

        if ts is None:
            if cfg.allow_missing_timestamps:
                unbucketed.append(rec)
                continue
            raise Phase5TimeAxisError("Record missing timestamp.")

        extracted.append((ts, rec))

    if not extracted:
        return TimeSeriesPatternView(
            config=cfg,
            buckets=[],
            gaps=[],
            unbucketed=unbucketed,
        )

    # Sort by timestamp
    extracted.sort(key=lambda x: x[0])

    # Optional monotonic enforcement
    if cfg.enforce_monotonic:
        for i in range(1, len(extracted)):
            if extracted[i][0] < extracted[i - 1][0]:
                raise Phase5TimeAxisError("Timestamps are not monotonic.")

    # Build buckets
    bucket_seconds = cfg.bucket_seconds
    first_ts = extracted[0][0]

    buckets_map = {}

    for ts, rec in extracted:
        idx = int((ts - first_ts) // bucket_seconds)
        buckets_map.setdefault(idx, []).append(rec)

    buckets: List[TimeBucket] = []
    for idx in sorted(buckets_map):
        start_ts = first_ts + idx * bucket_seconds
        buckets.append(
            TimeBucket(
                bucket_index=idx,
                start_ts=start_ts,
                records=buckets_map[idx],
            )
        )

    # Detect gaps
    gaps: List[Tuple[int, int]] = []
    indices = [b.bucket_index for b in buckets]

    for i in range(1, len(indices)):
        if indices[i] > indices[i - 1] + 1:
            gaps.append((indices[i - 1] + 1, indices[i] - 1))

    return TimeSeriesPatternView(
        config=cfg,
        buckets=buckets,
        gaps=gaps,
        unbucketed=unbucketed,
    )


# =====================================================================
# Internal helpers (Phase 5)
# =====================================================================

def _extract_timestamp(rec: PatternRecordContract) -> Optional[float]:
    """
    Extract timestamp from Phase 4 compatible observation.

    Priority:
    1. observation.snapshot.meta.timestamp_ms
    2. observation.snapshot.meta.timestamp (ISO)
    """
    obs = rec.observation or {}

    try:
        meta = obs.get("snapshot", {}).get("meta", {})

        if "timestamp_ms" in meta:
            return float(meta["timestamp_ms"]) / 1000.0

        if "timestamp" in meta:
            return _parse_iso(meta["timestamp"])

    except Exception:
        return None

    return None


def _parse_iso(value: str) -> float:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt.replace(tzinfo=timezone.utc).timestamp()


# =====================================================================
# Phase 11: Raw Observation Time Axis (append-only)
# =====================================================================

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # loader.py에 정의된 Phase11RawRecord를 타입 힌트로만 참조
    from .loader import Phase11RawRecord


class Phase11TimeAxisError(Exception):
    """Raised when Phase 11 time axis normalization fails."""


@dataclass(frozen=True)
class Phase11TimeAxis:
    """
    Phase 11 deterministic time axis for raw observation logs.

    Characteristics:
    - operates on raw records (dict payload)
    - no bucketing
    - strictly replay-oriented ordering
    """
    records: List["Phase11RawRecord"]

    @property
    def total_records(self) -> int:
        return len(self.records)

    def time_range(self) -> Optional[Tuple[float, float]]:
        if not self.records:
            return None

        start = self.records[0].ts_utc.timestamp()
        end = self.records[-1].ts_utc.timestamp()
        return start, end


def normalize_observation_time_axis(
    records: List["Phase11RawRecord"],
    *,
    enforce_monotonic: bool = False,
) -> Phase11TimeAxis:
    """
    Phase 11 time axis normalization.

    Ordering policy:
    - primary: ts_utc
    - secondary: line_no (stable replay guarantee)

    Notes:
    - enforce_monotonic=False by default because raw observer logs
      may legally contain out-of-order timestamps.
    """
    ordered = sorted(records, key=lambda r: (r.ts_utc, r.line_no))

    if enforce_monotonic:
        for i in range(1, len(ordered)):
            if ordered[i].ts_utc < ordered[i - 1].ts_utc:
                raise Phase11TimeAxisError(
                    "Timestamps are not monotonic after sorting."
                )

    return Phase11TimeAxis(records=ordered)
