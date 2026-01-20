from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .time_axis import TimeSeriesPatternView
from .contracts.pattern_record_contract import PatternRecordContract


class Phase5ClusteringError(Exception):
    """Raised when clustering cannot be performed."""


# =====================================================================
# Config & Result models
# =====================================================================

@dataclass(frozen=True)
class ClusterConfig:
    """
    Clustering configuration for Phase 5.

    min_cluster_size:
        Minimum number of records per cluster.
    """
    min_cluster_size: int = 1


@dataclass
class PatternCluster:
    cluster_id: int
    records: List[PatternRecordContract]


@dataclass
class ClusterResult:
    clusters: List[PatternCluster]
    unclustered: List[PatternRecordContract]

    @property
    def total_clusters(self) -> int:
        return len(self.clusters)

    @property
    def total_records(self) -> int:
        clustered = sum(len(c.records) for c in self.clusters)
        return clustered + len(self.unclustered)


# =====================================================================
# Public API
# =====================================================================

def cluster_patterns(
    ts_view: Optional[TimeSeriesPatternView],
    *,
    config: Optional[ClusterConfig] = None,
) -> ClusterResult:
    """
    Cluster patterns from a TimeSeriesPatternView.

    Canonical Phase 5 policy:
    - Buckets drive clustering.
    - Unbucketed records are preserved as unclustered.
    - Deterministic, no ML.
    """
    if ts_view is None:
        raise Phase5ClusteringError("TimeSeriesPatternView is required.")

    cfg = config or ClusterConfig()

    clusters: List[PatternCluster] = []
    unclustered: List[PatternRecordContract] = list(ts_view.unbucketed)

    current_records: List[PatternRecordContract] = []

    def _flush_cluster():
        nonlocal current_records, clusters, unclustered
        if not current_records:
            return

        if len(current_records) < cfg.min_cluster_size:
            # Too small -> unclustered
            unclustered.extend(current_records)
        else:
            cluster_id = len(clusters)
            clusters.append(
                PatternCluster(
                    cluster_id=cluster_id,
                    records=current_records.copy(),
                )
            )
        current_records.clear()

    # -----------------------------------------------------------------
    # Main clustering loop (bucket order guaranteed)
    # -----------------------------------------------------------------

    last_bucket_index = None

    for bucket in ts_view.buckets:
        if last_bucket_index is None:
            current_records.extend(bucket.records)
        else:
            if bucket.bucket_index != last_bucket_index + 1:
                _flush_cluster()
                current_records.extend(bucket.records)
            else:
                current_records.extend(bucket.records)

        last_bucket_index = bucket.bucket_index

    # Flush tail
    _flush_cluster()

    return ClusterResult(
        clusters=clusters,
        unclustered=unclustered,
    )
