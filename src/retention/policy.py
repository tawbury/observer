from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import List, Optional


@dataclass(frozen=True)
class RetentionPolicy:
    """
    Unified retention policy supporting both TTL-based and category-based retention.

    Supports two modes:
    1. TTL mode: Simple time-to-live with glob patterns
    2. Category mode: Different retention for data categories

    All durations are in days. None means 'keep forever'.
    """

    # TTL mode (simple)
    ttl_days: int = 7
    include_globs: Optional[List[str]] = None
    exclude_globs: Optional[List[str]] = None

    # Category mode (advanced)
    raw_snapshot_days: Optional[int] = None
    pattern_record_days: Optional[int] = None
    decision_snapshot_days: Optional[int] = None

    @property
    def ttl(self) -> timedelta:
        """Get TTL as timedelta."""
        return timedelta(days=self.ttl_days)

    def is_infinite(self, days: Optional[int]) -> bool:
        """Check if retention period is infinite (keep forever)."""
        return days is None

    @classmethod
    def from_ttl(cls, days: int, include: Optional[List[str]] = None, exclude: Optional[List[str]] = None) -> RetentionPolicy:
        """
        Create TTL-based policy.

        Args:
            days: Days to retain files
            include: Glob patterns to include (None = all)
            exclude: Glob patterns to exclude

        Returns:
            RetentionPolicy instance
        """
        return cls(
            ttl_days=days,
            include_globs=include,
            exclude_globs=exclude,
        )

    @classmethod
    def from_categories(
        cls,
        raw_snapshot_days: Optional[int] = 7,
        pattern_record_days: Optional[int] = 30,
        decision_snapshot_days: Optional[int] = None,
    ) -> RetentionPolicy:
        """
        Create category-based policy.

        Args:
            raw_snapshot_days: Retention for raw snapshots
            pattern_record_days: Retention for pattern records
            decision_snapshot_days: Retention for decision snapshots (None = forever)

        Returns:
            RetentionPolicy instance
        """
        return cls(
            raw_snapshot_days=raw_snapshot_days,
            pattern_record_days=pattern_record_days,
            decision_snapshot_days=decision_snapshot_days,
        )
