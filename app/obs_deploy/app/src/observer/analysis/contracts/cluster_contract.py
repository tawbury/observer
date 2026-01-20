# observer/analysis/contracts/cluster_contract.py

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .pattern_record_contract import PatternRecordContract


@dataclass(frozen=True)
class PatternClusterContract:
    """
    Deterministic cluster of pattern records.
    """

    cluster_id: str
    pattern_type: str
    records: List[PatternRecordContract]

    @property
    def size(self) -> int:
        return len(self.records)

    @property
    def guard_pass_ratio(self) -> float:
        if not self.records:
            return 0.0
        passed = sum(1 for r in self.records if r.guard_passed())
        return passed / len(self.records)

    @property
    def timestamps(self) -> List[float]:
        return [
            r.timestamp()
            for r in self.records
            if r.timestamp() is not None
        ]
