from __future__ import annotations

from pathlib import Path


def obs_root() -> Path:
    # .../src/maintenance/_paths.py -> .../src
    return Path(__file__).resolve().parents[2]


def maintenance_log_path() -> Path:
    # 고정 경로: logs/maintenance/cleanup.log
    path = obs_root() / "logs" / "maintenance" / "cleanup.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
