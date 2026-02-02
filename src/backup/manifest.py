from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class BackupManifest:
    """
    Metadata describing a single backup artifact.
    """

    backup_at: datetime
    source: str
    archive_name: str
    record_count: int
    checksum: Optional[str] = None
