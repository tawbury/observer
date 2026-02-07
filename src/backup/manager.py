from __future__ import annotations

import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from shared.timezone import now_kst

from .checksum import calculate_sha256
from .manifest import BackupManifest


class BackupManager:
    """
    Local backup manager for observer datasets.

    This manager:
    - creates a tar.gz archive
    - generates a manifest
    - calculates checksum
    """

    def __init__(self, source_root: Path, backup_root: Path):
        self.source_root = source_root
        self.backup_root = backup_root

    # -------------------------
    # helpers
    # -------------------------

    def _now(self) -> datetime:
        return now_kst()

    def _collect_files(self) -> List[Path]:
        if not self.source_root.exists():
            return []

        return [
            p
            for p in self.source_root.rglob("*")
            if p.is_file() and not p.name.startswith(".")
        ]

    def _ensure_backup_root(self) -> None:
        self.backup_root.mkdir(parents=True, exist_ok=True)

    def _archive_name(self, timestamp: datetime) -> str:
        return f"observer_backup_{timestamp.strftime('%Y%m%d_%H%M%S')}.tar.gz"

    # -------------------------
    # public API
    # -------------------------

    def dry_run(self) -> List[Path]:
        """
        Returns files that WOULD be included in backup.
        """
        return self._collect_files()

    def run(self) -> BackupManifest:
        """
        Execute backup.

        Creates:
        - tar.gz archive
        - manifest.json
        """
        self._ensure_backup_root()

        files = self._collect_files()
        timestamp = self._now()
        archive_name = self._archive_name(timestamp)
        archive_path = self.backup_root / archive_name

        # 1. create archive
        with tarfile.open(archive_path, "w:gz") as tar:
            for path in files:
                arcname = path.relative_to(self.source_root)
                tar.add(path, arcname=arcname)

        # 2. checksum
        checksum = calculate_sha256(archive_path)

        # 3. manifest
        manifest = BackupManifest(
            backup_at=timestamp,
            source=str(self.source_root),
            archive_name=archive_name,
            record_count=len(files),
            checksum=checksum,
        )

        manifest_path = archive_path.with_suffix(".manifest.json")
        self._write_manifest(manifest, manifest_path)

        return manifest

    def _write_manifest(self, manifest: BackupManifest, path: Path) -> None:
        data = {
            "backup_at": manifest.backup_at.isoformat(),
            "source": manifest.source,
            "archive_name": manifest.archive_name,
            "record_count": manifest.record_count,
            "checksum": manifest.checksum,
        }

        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
