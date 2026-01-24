from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class BackupResult:
    success: bool
    backup_root: Optional[Path] = None
    manifest_path: Optional[Path] = None
    error: Optional[str] = None


@dataclass(frozen=True)
class RetentionCandidate:
    path: Path
    reason: str  # e.g., "expired_by_mtime"


@dataclass(frozen=True)
class CleanupResult:
    success: bool
    deleted: List[Path] = field(default_factory=list)
    skipped: List[Path] = field(default_factory=list)
    error: Optional[str] = None


@dataclass(frozen=True)
class MaintenanceReport:
    backup: BackupResult
    candidates: List[RetentionCandidate]
    cleanup: CleanupResult
