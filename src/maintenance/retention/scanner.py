from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List

from shared.timezone import now_kst

from ops.maintenance._types import RetentionCandidate
from ops.maintenance.retention.policy import RetentionPolicy


def _matches_any(path: Path, patterns: List[str]) -> bool:
    # Path.match는 경로 세그먼트 기준이므로, rglob 패턴과 혼용 시 단순화
    s = path.as_posix()
    return any(Path(s).match(p) or path.match(p) for p in patterns)


def scan_expired(data_root: Path, policy: RetentionPolicy) -> List[RetentionCandidate]:
    """
    만료 대상 '산출'만 수행. 삭제는 cleanup에서만 수행.
    기준: 파일 mtime < now - ttl
    """
    now = now_kst().timestamp()
    threshold = now - policy.ttl.total_seconds()

    if policy.include_globs:
        files: List[Path] = []
        for g in policy.include_globs:
            files.extend([p for p in data_root.rglob(g) if p.is_file()])
    else:
        files = [p for p in data_root.rglob("*") if p.is_file()]

    if policy.exclude_globs:
        files = [p for p in files if not _matches_any(p, policy.exclude_globs)]

    candidates: List[RetentionCandidate] = []
    for p in sorted(set(files)):
        try:
            if p.stat().st_mtime < threshold:
                candidates.append(RetentionCandidate(path=p, reason="expired_by_mtime"))
        except FileNotFoundError:
            # 스캔 중 동시 삭제 등 레이스는 무시 (안전: 후보에서 제외)
            continue

    return candidates
