from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from .contracts.pattern_record_contract import PatternRecordContract


class TimeAxisError(Exception):
    """Raised when time axis normalization fails."""


# =====================================================================
# Config & View models
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
# Public API
# =====================================================================

def normalize_time_axis(
    records: List[PatternRecordContract],
    *,
    config: Optional[TimeAxisConfig] = None,
) -> TimeSeriesPatternView:
    """
    Normalize PatternRecordContracts onto a discrete time axis.

    Timestamp policy:
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
            raise TimeAxisError("Record missing timestamp.")

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
                raise TimeAxisError("Timestamps are not monotonic.")

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
# Internal helpers
# =====================================================================

def _extract_timestamp(rec: PatternRecordContract) -> Optional[float]:
    """
    Extract timestamp from observation.

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
    from shared.timezone import KST
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KST or timezone.utc)
    return dt.timestamp()


# =====================================================================
# Raw Observation Time Axis (append-only)
# =====================================================================

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # loader.py에 정의된 RawLogRecord 참조
    from .loader import RawLogRecord


class ReplayTimeAxisError(Exception):
    """Raised when time axis normalization fails."""


@dataclass(frozen=True)
class ReplayTimeAxis:
    """
    Deterministic time axis for raw observation logs.

    Characteristics:
    - operates on raw records (dict payload)
    - no bucketing
    - strictly replay-oriented ordering
    """
    records: List["RawLogRecord"]

    @property
    def total_records(self) -> int:
        return len(self.records)

    def time_range(self) -> Optional[Tuple[float, float]]:
        if not self.records:
            return None

        start = self.records[0].ts_kst.timestamp()
        end = self.records[-1].ts_kst.timestamp()
        return start, end


def normalize_observation_time_axis(
    records: List["RawLogRecord"],
    *,
    enforce_monotonic: bool = False,
) -> ReplayTimeAxis:
    """
    Time axis normalization.

    Ordering policy:
    - primary: ts_kst
    - secondary: line_no (stable replay guarantee)

    Notes:
    - enforce_monotonic=False by default because raw observer logs
      may legally contain out-of-order timestamps.
    """
    ordered = sorted(records, key=lambda r: (r.ts_kst, r.line_no))

    if enforce_monotonic:
        for i in range(1, len(ordered)):
            if ordered[i].ts_kst < ordered[i - 1].ts_kst:
                raise ReplayTimeAxisError(
                    "Timestamps are not monotonic after sorting."
                )

    return ReplayTimeAxis(records=ordered)
