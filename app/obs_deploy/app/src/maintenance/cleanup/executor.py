from __future__ import annotations

from pathlib import Path
from typing import List

from ops.maintenance._types import CleanupResult, RetentionCandidate
from ops.maintenance._paths import maintenance_log_path


def _append_log(lines: List[str]) -> None:
    log_path = maintenance_log_path()
    with log_path.open("a", encoding="utf-8") as f:
        for line in lines:
            f.write(line.rstrip("\n") + "\n")


def execute_cleanup(
    *,
    candidates: List[RetentionCandidate],
    backup_success: bool,
) -> CleanupResult:
    """
    Backup-First 강제:
      backup_success=False면 삭제는 절대 발생하지 않는다.
    """
    if not backup_success:
        _append_log(["[SKIP] backup_failed -> no deletion (backup-first)"])
        return CleanupResult(success=True, deleted=[], skipped=[c.path for c in candidates])

    deleted: List[Path] = []
    skipped: List[Path] = []

    try:
        for c in candidates:
            p = c.path
            if not p.exists():
                skipped.append(p)
                continue

            # 파일만 삭제 (디렉토리는 건드리지 않음: 안전 최소)
            if p.is_file():
                p.unlink()
                deleted.append(p)
            else:
                skipped.append(p)

        _append_log([
            f"[OK] cleanup deleted={len(deleted)} skipped={len(skipped)}",
            *[f"  - deleted: {p.as_posix()}" for p in deleted],
        ])
        return CleanupResult(success=True, deleted=deleted, skipped=skipped)

    except Exception as e:
        _append_log([f"[ERROR] cleanup failed: {type(e).__name__}: {e}"])
        return CleanupResult(success=False, deleted=deleted, skipped=skipped, error=f"{type(e).__name__}: {e}")
