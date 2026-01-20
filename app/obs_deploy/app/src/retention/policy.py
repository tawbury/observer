from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RetentionPolicy:
    """
    Retention rule definition.

    All durations are expressed in days.
    None means 'keep forever'.
    """

    raw_snapshot_days: Optional[int] = 7
    pattern_record_days: Optional[int] = 30
    decision_snapshot_days: Optional[int] = None  # keep forever

    def is_infinite(self, days: Optional[int]) -> bool:
        return days is None
