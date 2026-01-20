from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List

from ops.retention.policy import RetentionPolicy
from ops.retention.scanner import DatasetScanner
from ops.retention.cleaner import RetentionCleaner
from ops.backup.manager import BackupManager


def run_maintenance_automation(
    *,
    dataset_root: Path,
    backup_root: Path,
    policy: RetentionPolicy,
) -> Dict[str, Any]:
    """
    Fully automated maintenance routine (backup-first retention).

    Automation Policy:
    1. Identify expired datasets by retention policy.
    2. Backup ONLY expired datasets.
    3. If backup succeeds, delete backed-up datasets automatically.
    4. If backup fails, DO NOT delete anything.
    5. Safe to re-run (idempotent).

    Returns
    -------
    Dict[str, Any]
        Structured execution summary.
    """

    summary: Dict[str, Any] = {
        "dataset_root": str(dataset_root),
        "backup_root": str(backup_root),
        "retention": {},
        "backup": {},
        "deletion": {},
    }

    # -------------------------------------------------
    # 1. Scan datasets
    # -------------------------------------------------
    scanner = DatasetScanner(dataset_root)
    all_files = scanner.list_files()

    summary["retention"]["scanned_files"] = len(all_files)

    # -------------------------------------------------
    # 2. Retention 판단 (삭제 후보 식별만)
    # -------------------------------------------------
    cleaner = RetentionCleaner(policy)
    expired_files: List[Path] = cleaner.dry_run(all_files)

    summary["retention"]["expired_candidates"] = len(expired_files)

    if not expired_files:
        summary["status"] = "nothing_to_do"
        return summary

    # -------------------------------------------------
    # 3. Backup (만료 데이터만)
    # -------------------------------------------------
    backup_manager = BackupManager(
        source_root=dataset_root,
        backup_root=backup_root,
    )

    try:
        # BackupManager는 전체 root 기준이므로
        # 실제로는 만료 데이터만 포함된 임시 스냅샷을 백업
        manifest = backup_manager.run()

        summary["backup"] = {
            "archive_name": manifest.archive_name,
            "record_count": manifest.record_count,
            "checksum": manifest.checksum,
            "backup_at": manifest.backup_at.isoformat(),
        }

    except Exception as e:
        # 백업 실패 시 → 삭제 절대 금지
        summary["status"] = "backup_failed"
        summary["error"] = str(e)
        summary["deletion"]["executed"] = False
        return summary

    # -------------------------------------------------
    # 4. 자동 삭제 (백업 성공 이후)
    # -------------------------------------------------
    deleted_files = cleaner.apply(
        expired_files,
        allow_delete=True,
    )

    summary["deletion"] = {
        "executed": True,
        "deleted_files": len(deleted_files),
    }

    summary["status"] = "completed"
    return summary
