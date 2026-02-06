# observer/analysis/dataset_builder.py

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Any, Optional

from shared.timezone import now_kst

from .contracts.cluster_contract import PatternClusterContract
from .contracts.dataset_contract import ScalpCandidateDatasetContract
from .stats import ClusterStats


class Phase5DatasetBuildError(Exception):
    pass


# =====================================================================
# Phase 5 Dataset Builder (UNCHANGED)
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
# Phase 11: Raw Observation Dataset Builder (APPEND-ONLY)
# =====================================================================

class Phase11DatasetBuildError(RuntimeError):
    """Raised when Phase 11 dataset building fails."""


class Phase11ObservationDataset(dict):
    """
    Phase 11 in-memory dataset representation.

    Design notes:
    - intentionally lightweight (dict-based)
    - no persistence, no schema hard-binding
    - serves as analysis bootstrap asset for Phase 12+

    Canonical keys:
      - meta
      - records
    """


def build_observation_replay_dataset(
    *,
    time_axis,
    source: Optional[str] = None,
) -> Phase11ObservationDataset:
    """
    Build Phase 11 observation replay dataset.

    Input:
    - time_axis: Phase11TimeAxis (from time_axis.py)
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

        dataset = Phase11ObservationDataset(
            meta={
                "phase": 11,
                "generated_at": now_kst().isoformat(),
                "source": source,
                "total_records": len(records_out),
            },
            records=records_out,
        )

        return dataset

    except Exception as e:
        raise Phase11DatasetBuildError(
            f"Failed to build Phase 11 observation dataset: {e}"
        ) from e
