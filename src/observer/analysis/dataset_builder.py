# observer/analysis/dataset_builder.py

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Any, Optional

from shared.timezone import now_kst

from .contracts.cluster_contract import PatternClusterContract
from .contracts.dataset_contract import ScalpCandidateDatasetContract
from .stats import ClusterStats


class ScalpDatasetBuildError(Exception):
    pass


# =====================================================================
# Scalp Candidate Dataset Builder
# =====================================================================

def build_scalp_candidate_dataset(
    clusters: List[PatternClusterContract],
    stats: Dict[str, ClusterStats],
    *,
    min_count: int = 3,
    min_guard_pass_ratio: float = 0.6,
) -> ScalpCandidateDatasetContract:
    """
    Select clusters that satisfy fixed, explainable criteria.
    """

    selected: List[PatternClusterContract] = []

    for c in clusters:
        s = stats.get(c.cluster_id)
        if not s:
            continue

        if s.count < min_count:
            continue

        if s.guard_pass_ratio < min_guard_pass_ratio:
            continue

        selected.append(c)

    return ScalpCandidateDatasetContract(
        generated_at=now_kst().isoformat(),
        criteria={
            "min_count": float(min_count),
            "min_guard_pass_ratio": float(min_guard_pass_ratio),
        },
        clusters=selected,
    )


# =====================================================================
# Raw Observation Dataset Builder
# =====================================================================

class ReplayDatasetBuildError(RuntimeError):
    """Raised when replay dataset building fails."""


class ReplayObservationDataset(dict):
    """
    In-memory replay dataset representation.

    Design notes:
    - intentionally lightweight (dict-based)
    - no persistence, no schema hard-binding
    - serves as analysis bootstrap asset

    Canonical keys:
      - meta
      - records
    """


def build_observation_replay_dataset(
    *,
    time_axis,
    source: Optional[str] = None,
) -> ReplayObservationDataset:
    """
    Build observation replay dataset.

    Input:
    - time_axis: ReplayTimeAxis (from time_axis.py)
    - source: optional human-readable source identifier

    Output:
    - dict-like dataset with stable, explainable structure

    This function intentionally performs:
    - NO feature extraction
    - NO aggregation
    - NO interpretation
    """

    try:
        records_out: List[Dict[str, Any]] = []

        for r in time_axis.records:
            records_out.append(
                {
                    "ts_utc": r.ts_utc.isoformat(),
                    "line_no": r.line_no,
                    "payload": r.payload,
                }
            )

        dataset = ReplayObservationDataset(
            meta={
                "generated_at": now_kst().isoformat(),
                "source": source,
                "total_records": len(records_out),
            },
            records=records_out,
        )

        return dataset

    except Exception as e:
        raise ReplayDatasetBuildError(
            f"Failed to build observation replay dataset: {e}"
        ) from e
