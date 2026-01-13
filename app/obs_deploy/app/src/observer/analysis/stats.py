# QTS/src/ops/observer/analysis/stats.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Any, Optional

from .contracts.cluster_contract import PatternClusterContract


# =====================================================================
# Phase 5: Cluster Statistics (UNCHANGED)
# =====================================================================

@dataclass(frozen=True)
class ClusterStats:
    cluster_id: str
    pattern_type: str
    count: int
    guard_pass_ratio: float
    first_ts: float | None
    last_ts: float | None


def aggregate_cluster_stats(
    clusters: List[PatternClusterContract],
) -> Dict[str, ClusterStats]:
    """
    Produce read-only statistics per cluster.
    """

    stats: Dict[str, ClusterStats] = {}

    for c in clusters:
        ts = sorted(c.timestamps)
        stats[c.cluster_id] = ClusterStats(
            cluster_id=c.cluster_id,
            pattern_type=c.pattern_type,
            count=c.size,
            guard_pass_ratio=c.guard_pass_ratio,
            first_ts=ts[0] if ts else None,
            last_ts=ts[-1] if ts else None,
        )

    return stats


# =====================================================================
# Phase 11: Observation Replay Statistics (APPEND-ONLY)
# =====================================================================

class Phase11StatsError(RuntimeError):
    """Raised when Phase 11 statistics aggregation fails."""


@dataclass(frozen=True)
class Phase11ReplayStats:
    """
    Minimal, interpretation-free statistics for Phase 11 replay data.

    Design principles:
    - no feature extraction
    - no clustering
    - no semantic interpretation
    - purely descriptive metrics
    """
    total_records: int
    first_ts_utc: Optional[str]
    last_ts_utc: Optional[str]
    duration_seconds: Optional[float]
    has_gaps: bool


def aggregate_observation_replay_stats(
    *,
    time_axis,
) -> Phase11ReplayStats:
    """
    Aggregate minimal statistics from Phase11TimeAxis.

    Input:
    - time_axis: Phase11TimeAxis

    Output:
    - Phase11ReplayStats

    Notes:
    - 'gap' here only indicates non-uniform time deltas,
      not missing data semantics.
    """

    try:
        records = time_axis.records

        if not records:
            return Phase11ReplayStats(
                total_records=0,
                first_ts_utc=None,
                last_ts_utc=None,
                duration_seconds=None,
                has_gaps=False,
            )

        first_dt = records[0].ts_utc
        last_dt = records[-1].ts_utc

        # detect simple gaps (non-zero, non-uniform deltas)
        has_gaps = False
        if len(records) > 2:
            deltas = []
            for i in range(1, len(records)):
                delta = (records[i].ts_utc - records[i - 1].ts_utc).total_seconds()
                deltas.append(delta)

            # if deltas are not all equal, we call it a "gap"
            has_gaps = not all(d == deltas[0] for d in deltas if d >= 0)

        return Phase11ReplayStats(
            total_records=len(records),
            first_ts_utc=first_dt.isoformat(),
            last_ts_utc=last_dt.isoformat(),
            duration_seconds=(last_dt - first_dt).total_seconds(),
            has_gaps=has_gaps,
        )

    except Exception as e:
        raise Phase11StatsError(
            f"Failed to aggregate Phase 11 replay stats: {e}"
        ) from e
