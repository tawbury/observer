from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import List, Optional


@dataclass(frozen=True)
class RetentionPolicy:
    """
    ttl_days: mtime 기준 만료(운영 안전 최소 버전)
    include_globs: 스캔 포함 패턴 (None이면 전체)
    exclude_globs: 제외 패턴
    """
    ttl_days: int = 7
    include_globs: Optional[List[str]] = None
    exclude_globs: Optional[List[str]] = None

    @property
    def ttl(self) -> timedelta:
        return timedelta(days=int(self.ttl_days))
