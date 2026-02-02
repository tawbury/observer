from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Iterable, List, Optional, Set, Dict, Any

from ._paths import obs_root, maintenance_log_path


@dataclass(frozen=True)
class CleanupRule:
    이름: str
    대상_폴더: Path
    보관_일수: int
    패턴: str
    재귀: bool
    허용_확장자: Optional[Set[str]] = None


def _append_log(lines: Iterable[str]) -> None:
    log_path = maintenance_log_path()
    with log_path.open("a", encoding="utf-8") as f:
        for line in lines:
            f.write(line.rstrip("\n") + "\n")


def _today_local() -> date:
    return datetime.now().date()


def _last_run_path() -> Path:
    path = maintenance_log_path().parent / "cleanup_last_run.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _load_last_run(path: Path) -> Optional[date]:
    try:
        if not path.exists():
            return None
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            return None
        return date.fromisoformat(content)
    except Exception:
        return None


def _save_last_run(path: Path, run_date: date) -> None:
    try:
        path.write_text(run_date.isoformat(), encoding="utf-8")
    except Exception:
        _append_log(["[정리] 마지막 실행 기록 저장 실패"])


def _iter_candidates(rule: CleanupRule) -> Iterable[Path]:
    if rule.재귀:
        yield from rule.대상_폴더.rglob(rule.패턴)
    else:
        yield from rule.대상_폴더.glob(rule.패턴)


def _is_expired(path: Path, now: datetime, days: int) -> bool:
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
    except FileNotFoundError:
        return False
    expire_at = mtime + timedelta(days=days)
    return now >= expire_at


def _is_allowed(path: Path, rule: CleanupRule) -> bool:
    if not path.is_file():
        return False
    if rule.허용_확장자 is None:
        return True
    return path.suffix.lower() in rule.허용_확장자


def _rel_to_root(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def run_storage_cleanup(base_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    저장소 정리 정책 실행.

    - logs/ : 3일 초과 파일
    - config/*.jsonl : 7일 초과 파일
    - data/*.db : 30일 초과 파일
    """
    root = base_root or obs_root()
    now = datetime.now()

    rules = [
        CleanupRule(
            이름="로그",
            대상_폴더=root / "logs",
            보관_일수=3,
            패턴="*",
            재귀=True,
            허용_확장자=None,
        ),
        CleanupRule(
            이름="설정JSONL",
            대상_폴더=root / "config",
            보관_일수=7,
            패턴="*.jsonl",
            재귀=False,
            허용_확장자={".jsonl"},
        ),
        CleanupRule(
            이름="데이터DB",
            대상_폴더=root / "data",
            보관_일수=30,
            패턴="*.db",
            재귀=False,
            허용_확장자={".db"},
        ),
    ]

    summary: Dict[str, Any] = {
        "삭제": 0,
        "스킵": 0,
        "오류": 0,
        "삭제_목록": [],
    }

    _append_log([f"[정리] 저장소 정리 시작: {now.isoformat()}"])

    for rule in rules:
        if not rule.대상_폴더.exists():
            _append_log([f"[정리] 대상 폴더 없음: {rule.대상_폴더.as_posix()}"])
            continue

        for path in _iter_candidates(rule):
            if not _is_allowed(path, rule):
                summary["스킵"] += 1
                continue

            if not _is_expired(path, now, rule.보관_일수):
                summary["스킵"] += 1
                continue

            try:
                path.unlink()
                rel = _rel_to_root(path, root)
                _append_log([f"[정리] 삭제됨: {rel}"])
                summary["삭제"] += 1
                summary["삭제_목록"].append(rel)
            except Exception as e:
                rel = _rel_to_root(path, root)
                _append_log([f"[정리] 삭제 실패: {rel} (오류: {type(e).__name__}: {e})"])
                summary["오류"] += 1

    _append_log([
        f"[정리] 저장소 정리 완료: 삭제={summary['삭제']} 스킵={summary['스킵']} 오류={summary['오류']}"
    ])
    return summary


def run_daily_cleanup(*, force: bool = False, base_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    하루 1회만 실행되는 정리 작업.
    """
    stamp_path = _last_run_path()
    today = _today_local()
    last_run = _load_last_run(stamp_path)

    if not force and last_run == today:
        _append_log(["[정리] 오늘 이미 실행됨 -> 스킵"])
        return {"status": "skipped", "reason": "already_ran_today"}

    result = run_storage_cleanup(base_root=base_root)
    _save_last_run(stamp_path, today)
    return {"status": "completed", **result}


if __name__ == "__main__":
    run_daily_cleanup()
