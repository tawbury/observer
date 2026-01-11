from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from .policy import RetentionPolicy


class RetentionCleaner:
    """
    Applies retention rules to observer dataset files.

    Default behavior is dry-run.
    Hard delete requires explicit allow_delete=True.
    """

    def __init__(self, policy: RetentionPolicy):
        self.policy = policy

    # -------------------------
    # internal helpers
    # -------------------------

    def _now(self) -> datetime:
        return datetime.now(tz=timezone.utc)

    def _is_expired(
        self,
        file_path: Path,
        retention_days: Optional[int],
        now: datetime,
    ) -> bool:
        if retention_days is None:
            return False

        mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
        expire_at = mtime + timedelta(days=retention_days)
        return now >= expire_at

    def _classify(self, path: Path) -> Optional[int]:
        """
        Returns retention days for given dataset file.
        None means keep forever.
        """
        name = str(path).lower()

        if "decision" in name:
            return self.policy.decision_snapshot_days
        if "pattern" in name:
            return self.policy.pattern_record_days
        if "raw" in name:
            return self.policy.raw_snapshot_days

        # unknown dataset type → do not touch
        return None

    # -------------------------
    # public API
    # -------------------------

    def dry_run(self, files: List[Path]) -> List[Path]:
        """
        Returns files that WOULD be deleted.
        """
        now = self._now()
        expired: List[Path] = []

        for path in files:
            retention_days = self._classify(path)
            if retention_days is None:
                continue

            if self._is_expired(path, retention_days, now):
                expired.append(path)

        return expired

    def apply(
        self,
        files: List[Path],
        *,
        allow_delete: bool = False,
    ) -> List[Path]:
        """
        Apply retention cleanup.

        If allow_delete is False, behaves exactly like dry_run.
        """
        expired = self.dry_run(files)

        if not allow_delete:
            return expired

        deleted: List[Path] = []

        for path in expired:
            try:
                path.unlink()
                deleted.append(path)
            except Exception:
                # fail-safe: never crash retention
                continue

        return deleted
