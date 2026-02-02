from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from ops.maintenance._types import BackupResult


@dataclass(frozen=True)
class BackupPlan:
    source_files: List[Path]
    backup_root: Path  # where backup folder will be created


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def build_backup_plan(data_root: Path, backup_root: Path, include_globs: Optional[List[str]] = None) -> BackupPlan:
    """
    data_root: 백업 대상 데이터 루트
    backup_root: 백업 결과가 저장될 루트 (테스트에서는 temp dir 권장)
    include_globs: None이면 data_root 아래 모든 파일(재귀)
    """
    if include_globs:
        files: List[Path] = []
        for g in include_globs:
            files.extend([p for p in data_root.rglob(g) if p.is_file()])
    else:
        files = [p for p in data_root.rglob("*") if p.is_file()]

    return BackupPlan(source_files=sorted(set(files)), backup_root=backup_root)


def run_backup(plan: BackupPlan) -> BackupResult:
    """
    Backup-First 원칙: 실패하면 success=False 반환, 이후 단계에서 삭제 금지 근거로 사용.
    Idempotency: 같은 파일이 이미 백업돼 있으면 덮어쓰되(copy2), 결과는 동일하게 유지.
    """
    try:
        stamp = _utc_stamp()
        target_root = plan.backup_root / f"backup_{stamp}"
        target_root.mkdir(parents=True, exist_ok=True)

        copied: List[str] = []
        for src in plan.source_files:
            # data_root 상대 경로를 유지하도록 백업
            # (상대 경로 계산이 실패할 수 있으므로 안전 처리)
            try:
                rel = src.relative_to(src.anchor)  # absolute-safe fallback
            except Exception:
                rel = Path(src.name)

            dst = target_root / rel.as_posix().lstrip("/\\")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(str(dst))

        manifest = {
            "schema_version": "1.0",
            "captured_at_utc": datetime.now(timezone.utc).isoformat(),
            "file_count": len(plan.source_files),
            "copied_files": copied,
        }
        manifest_path = target_root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        return BackupResult(success=True, backup_root=target_root, manifest_path=manifest_path)

    except Exception as e:
        return BackupResult(success=False, error=f"{type(e).__name__}: {e}")
