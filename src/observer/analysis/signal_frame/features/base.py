from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Protocol


JsonDict = Dict[str, Any]


@dataclass(frozen=True)
class FeatureContext:
    """
    Minimal stateless context for feature extraction.

    - records: replay records (list of mappings)
    - index: current record index in records
    - window_n: sliding window size used by some features
    - time_axis_index: optional external bucket/time-axis index (if available)
    """
    records: List[Mapping[str, Any]]
    index: int
    window_n: int = 20
    time_axis_index: int | None = None


class FeatureExtractor(Protocol):
    """
    Pure extractor: extract(record, context) -> JSON-serializable dict
    """
    def extract(self, record: Mapping[str, Any], context: FeatureContext) -> JsonDict: ...
