from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .clustering import ClusterResult, PatternCluster
from .time_axis import TimeSeriesPatternView
from .contracts import PatternRecordContract



# =====================================================================
# Exceptions
# =====================================================================

class ScaffoldError(RuntimeError):
    """Raised when scaffold dataset generation fails."""


# =====================================================================
# Config
# =====================================================================

@dataclass(frozen=True)
class ScaffoldConfig:
    """
    Configuration for scaffold dataset generation.

    cluster_id policy:
    - >= 0 : clustered
    - -1   : unclustered
    """
    unclustered_id: int = -1


# =====================================================================
# Result
# =====================================================================

@dataclass
class ScaffoldDataset:
    """
    Canonical scaffold dataset.

    rows: list of normalized dict rows
    """
    rows: List[Dict[str, Any]]

    @property
    def total_rows(self) -> int:
        return len(self.rows)

    @property
    def total_records(self) -> int:
        return len(self.rows)


# =====================================================================
# Core
# =====================================================================

def build_scaffold_dataset(
    cluster_result: Optional[ClusterResult],
    *,
    config: ScaffoldConfig = ScaffoldConfig(),
) -> ScaffoldDataset:
    """
    Build a normalized scaffold dataset from clustering result.

    Rules:
    - MUST be deterministic
    - MUST preserve all records
    - MUST include unclustered records
    - MUST NOT depend on Observer-Core internals
    """

    if cluster_result is None:
        raise ScaffoldError("ClusterResult is None.")

    rows: List[Dict[str, Any]] = []
    record_index = 0

    # ------------------------------------------------------------
    # Clustered records
    # ------------------------------------------------------------
    for cluster in cluster_result.clusters:
        _append_cluster_rows(
            rows=rows,
            cluster=cluster,
            cluster_id=cluster.cluster_id,
            start_index=record_index,
        )
        record_index += len(cluster.records)

    # ------------------------------------------------------------
    # Unclustered records
    # ------------------------------------------------------------
    for rec in cluster_result.unclustered:
        rows.append(
            _row_from_record(
                rec,
                cluster_id=config.unclustered_id,
                record_index=record_index,
            )
        )
        record_index += 1

    return ScaffoldDataset(rows=rows)


# =====================================================================
# Internals
# =====================================================================

def _append_cluster_rows(
    *,
    rows: List[Dict[str, Any]],
    cluster: PatternCluster,
    cluster_id: int,
    start_index: int,
) -> None:
    """
    Append rows for a single cluster.
    """
    idx = start_index
    for rec in cluster.records:
        rows.append(
            _row_from_record(
                rec,
                cluster_id=cluster_id,
                record_index=idx,
            )
        )
        idx += 1


def _row_from_record(
    rec: PatternRecordContract,
    *,
    cluster_id: int,
    record_index: int,
) -> Dict[str, Any]:
    """
    Convert PatternRecordContract to scaffold row.
    """

    observation = rec.observation or {}

    # timestamp resolution (best-effort)
    ts = (
        observation.get("snapshot", {})
        .get("meta", {})
        .get("timestamp")
    )

    return {
        "cluster_id": cluster_id,
        "record_index": record_index,
        "session_id": rec.session_id,
        "timestamp": ts,
        "payload": observation,
    }
