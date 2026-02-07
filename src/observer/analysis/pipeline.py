# observer/analysis/pipeline.py

from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any

from .loader import (
    load_pattern_records,
    load_observation_jsonl_records,
    load_observation_jsonl_records,
    RawLoadResult,
)
from .time_axis import (
    TimeAxisConfig,
    normalize_time_axis,
    normalize_observation_time_axis,
    ReplayTimeAxis,
)
from .clustering import cluster_patterns
from .stats import aggregate_cluster_stats
from .dataset_builder import build_scalp_candidate_dataset


# =====================================================================
# Offline Pattern Analysis Pipeline
# =====================================================================

def run_offline_pattern_analysis(
    input_path: Path,
    *,
    bucket_seconds: float = 1.0,
    max_records: Optional[int] = None,
):
    """
    Execute Offline Analysis Pipeline.

    Order is fixed and must not be altered.
    """

    # 1) Load
    load_result = load_pattern_records(
        input_path,
        strict=True,
        max_records=max_records,
    )

    # 2) Time normalization
    ts_view = normalize_time_axis(
        load_result.records,
        config=TimeAxisConfig(bucket_seconds=bucket_seconds),
    )

    # 3) Clustering
    clusters = cluster_patterns(ts_view)

    # 4) Statistics
    stats = aggregate_cluster_stats(clusters)

    # 5) Dataset build
    dataset = build_scalp_candidate_dataset(clusters, stats)

    return {
        "load": load_result,
        "time_series": ts_view,
        "clusters": clusters,
        "stats": stats,
        "dataset": dataset,
    }


# =====================================================================
# Observation Replay & Analysis Bootstrap Pipeline
# =====================================================================

class ReplayPipelineError(RuntimeError):
    """Raised when replay pipeline execution fails."""


def run_replay_analysis(
    input_path: Path,
    *,
    max_records: Optional[int] = None,
    enforce_monotonic: bool = False,
) -> Dict[str, Any]:
    """
    Execute Analysis & Discovery Pipeline.

    Definition:
    - Read observer logs back into code
    - Normalize into deterministic time axis
    - DO NOT perform clustering, stats, or dataset materialization
    - Output is a replayable, analysis-ready in-memory structure

    This pipeline intentionally stops before any 'interpretation' step.
    """

    try:
        # 1) Load raw observation logs
        load_result: RawLoadResult = load_observation_jsonl_records(
            input_path,
            max_records=max_records,
        )

        # 2) Deterministic time ordering (replay axis)
        time_axis: ReplayTimeAxis = normalize_observation_time_axis(
            load_result.records,
            enforce_monotonic=enforce_monotonic,
        )

    except Exception as e:
        raise ReplayPipelineError(
            f"Replay pipeline failed for input={input_path}: {e}"
        ) from e

    return {
        "input_path": input_path,
        "load": load_result,
        "time_axis": time_axis,
    }
