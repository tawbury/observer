from __future__ import annotations

from pathlib import Path


def ops_root() -> Path:
    # .../src/ops/maintenance/_paths.py -> .../src/ops
    return Path(__file__).resolve().parents[2]


def maintenance_log_path() -> Path:
    # 고정 경로: src/ops/logs/maintenance/cleanup.log
    path = ops_root() / "logs" / "maintenance" / "cleanup.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
