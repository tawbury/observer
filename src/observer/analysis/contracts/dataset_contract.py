# observer/analysis/contracts/dataset_contract.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .cluster_contract import PatternClusterContract


@dataclass(frozen=True)
class ScalpCandidateDatasetContract:
    """
    Output artifact of Analysis.
    Pure data structure – no logic.
    """

    generated_at: str
    criteria: Dict[str, float]
    clusters: List[PatternClusterContract]

    @property
    def total_clusters(self) -> int:
        return len(self.clusters)

    @property
    def total_patterns(self) -> int:
        return sum(c.size for c in self.clusters)
