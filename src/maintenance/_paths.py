from __future__ import annotations

from pathlib import Path
from observer.paths import project_root, maintenance_log_dir


def obs_root() -> Path:
    """Observer project root (resolved via observer.paths)"""
    return project_root()


def maintenance_log_path() -> Path:
    """
    Observer maintenance log path.
    Uses centralized maintenance_log_dir() which honors OBSERVER_LOG_DIR.
    """
    return maintenance_log_dir() / "cleanup.log"

