# TASK-2.1: Retention 모듈 통합

## 태스크 정보
- **Phase**: 2 - 모듈 통합
- **우선순위**: High
- **의존성**: Phase 1 완료
- **상태**: 대기

---

## 목표
중복된 두 Retention 모듈을 하나로 통합하여 코드 일관성과 유지보수성을 향상시킵니다.

---

## 현재 문제

### 중복 모듈 구조

현재 두 개의 Retention 관련 모듈이 존재합니다:

```
src/retention/                  # 기존 모듈 (4개 파일)
├── __init__.py
├── cleaner.py                  # RetentionCleaner 클래스
├── index.py
├── policy.py                   # RetentionPolicy (카테고리 기반)
└── scanner.py                  # DatasetScanner 클래스

src/maintenance/retention/      # 신규 모듈 (3개 파일)
├── __init__.py
├── policy.py                   # RetentionPolicy (TTL 기반)
└── scanner.py                  # scan_expired() 함수
```

### API 차이점

#### `src/retention/policy.py` (기존)
```python
@dataclass(frozen=True)
class RetentionPolicy:
    raw_snapshot_days: int = 7
    pattern_record_days: int = 30
    decision_snapshot_days: Optional[int] = None

    @property
    def raw_ttl(self) -> timedelta:
        return timedelta(days=self.raw_snapshot_days)

    @property
    def pattern_ttl(self) -> timedelta:
        return timedelta(days=self.pattern_record_days)
```

#### `src/maintenance/retention/policy.py` (신규)
```python
@dataclass(frozen=True)
class RetentionPolicy:
    ttl_days: int = 7
    include_globs: Optional[List[str]] = None
    exclude_globs: Optional[List[str]] = None

    @property
    def ttl(self) -> timedelta:
        return timedelta(days=self.ttl_days)
```

---

## 구현 계획

### 1. 통합 RetentionPolicy 설계

**파일**: `app/obs_deploy/app/src/retention/policy.py`

```python
"""
Unified retention policy for data lifecycle management.

Supports both category-based retention (raw snapshots, patterns, decisions)
and TTL-based retention with glob patterns.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import List, Optional


__all__ = ["RetentionPolicy", "CategoryRetention"]


@dataclass(frozen=True)
class CategoryRetention:
    """Retention settings for a specific data category."""
    days: int
    include_globs: Optional[List[str]] = None
    exclude_globs: Optional[List[str]] = None

    @property
    def ttl(self) -> timedelta:
        return timedelta(days=self.days)


@dataclass(frozen=True)
class RetentionPolicy:
    """
    Unified retention policy supporting multiple retention strategies.

    Attributes:
        ttl_days: Default TTL for general data (days)
        raw_snapshot_days: Retention for raw market snapshots
        pattern_record_days: Retention for pattern analysis records
        decision_snapshot_days: Retention for decision snapshots (None = keep forever)
        include_globs: Glob patterns to include in cleanup
        exclude_globs: Glob patterns to exclude from cleanup

    Example:
        >>> policy = RetentionPolicy(
        ...     ttl_days=7,
        ...     raw_snapshot_days=7,
        ...     pattern_record_days=30,
        ...     exclude_globs=["*.important"]
        ... )
        >>> policy.raw_ttl
        datetime.timedelta(days=7)
    """
    # General TTL (for maintenance module compatibility)
    ttl_days: int = 7

    # Category-specific retention (for retention module compatibility)
    raw_snapshot_days: int = 7
    pattern_record_days: int = 30
    decision_snapshot_days: Optional[int] = None

    # Glob patterns (for maintenance module compatibility)
    include_globs: Optional[List[str]] = None
    exclude_globs: Optional[List[str]] = None

    @property
    def ttl(self) -> timedelta:
        """Default TTL as timedelta."""
        return timedelta(days=self.ttl_days)

    @property
    def raw_ttl(self) -> timedelta:
        """Raw snapshot TTL as timedelta."""
        return timedelta(days=self.raw_snapshot_days)

    @property
    def pattern_ttl(self) -> timedelta:
        """Pattern record TTL as timedelta."""
        return timedelta(days=self.pattern_record_days)

    @property
    def decision_ttl(self) -> Optional[timedelta]:
        """Decision snapshot TTL as timedelta, or None for infinite retention."""
        if self.decision_snapshot_days is None:
            return None
        return timedelta(days=self.decision_snapshot_days)

    def get_category(self, category: str) -> CategoryRetention:
        """
        Get retention settings for a specific category.

        Args:
            category: One of 'raw', 'pattern', 'decision', or 'default'

        Returns:
            CategoryRetention with appropriate settings
        """
        if category == "raw":
            return CategoryRetention(
                days=self.raw_snapshot_days,
                include_globs=self.include_globs,
                exclude_globs=self.exclude_globs,
            )
        elif category == "pattern":
            return CategoryRetention(
                days=self.pattern_record_days,
                include_globs=self.include_globs,
                exclude_globs=self.exclude_globs,
            )
        elif category == "decision":
            days = self.decision_snapshot_days or 365 * 100  # 100 years if None
            return CategoryRetention(
                days=days,
                include_globs=self.include_globs,
                exclude_globs=self.exclude_globs,
            )
        else:
            return CategoryRetention(
                days=self.ttl_days,
                include_globs=self.include_globs,
                exclude_globs=self.exclude_globs,
            )

    @classmethod
    def from_ttl(cls, ttl_days: int, **kwargs) -> "RetentionPolicy":
        """
        Create policy with uniform TTL across all categories.

        Args:
            ttl_days: TTL to apply to all categories
            **kwargs: Additional policy options

        Returns:
            RetentionPolicy with uniform settings
        """
        return cls(
            ttl_days=ttl_days,
            raw_snapshot_days=ttl_days,
            pattern_record_days=ttl_days,
            decision_snapshot_days=ttl_days,
            **kwargs,
        )
```

### 2. Scanner 통합

**파일**: `app/obs_deploy/app/src/retention/scanner.py`

```python
"""
Unified data scanner for retention policy enforcement.

Combines functionality from both legacy DatasetScanner and
maintenance scan_expired functions.
"""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Generator, List, Optional

from .policy import RetentionPolicy


__all__ = ["DatasetScanner", "ExpiredFile", "scan_expired"]


@dataclass
class ExpiredFile:
    """Represents a file that has exceeded its retention period."""
    path: Path
    age_days: float
    category: str
    size_bytes: int


class DatasetScanner:
    """
    Scanner for finding files that exceed retention policies.

    Supports both category-based and TTL-based scanning.
    """

    def __init__(self, policy: RetentionPolicy, base_path: Optional[Path] = None):
        """
        Initialize scanner with retention policy.

        Args:
            policy: Retention policy to apply
            base_path: Base directory to scan (optional)
        """
        self.policy = policy
        self.base_path = base_path or Path(".")

    def scan(
        self,
        path: Optional[Path] = None,
        category: str = "default",
    ) -> Generator[ExpiredFile, None, None]:
        """
        Scan directory for expired files.

        Args:
            path: Directory to scan (uses base_path if not specified)
            category: Data category for TTL lookup

        Yields:
            ExpiredFile for each expired file found
        """
        scan_path = path or self.base_path
        if not scan_path.exists():
            return

        retention = self.policy.get_category(category)
        cutoff = datetime.now() - retention.ttl

        for file_path in scan_path.rglob("*"):
            if not file_path.is_file():
                continue

            # Check glob patterns
            if not self._matches_patterns(file_path, retention):
                continue

            # Check age
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if mtime < cutoff:
                age_days = (datetime.now() - mtime).total_seconds() / 86400
                yield ExpiredFile(
                    path=file_path,
                    age_days=age_days,
                    category=category,
                    size_bytes=file_path.stat().st_size,
                )

    def _matches_patterns(self, path: Path, retention) -> bool:
        """Check if path matches include/exclude glob patterns."""
        name = path.name

        # Check excludes first
        if retention.exclude_globs:
            for pattern in retention.exclude_globs:
                if fnmatch.fnmatch(name, pattern):
                    return False

        # Check includes
        if retention.include_globs:
            for pattern in retention.include_globs:
                if fnmatch.fnmatch(name, pattern):
                    return True
            return False  # Has includes but didn't match any

        return True  # No includes = include all


def scan_expired(
    policy: RetentionPolicy,
    path: Path,
    category: str = "default",
) -> List[ExpiredFile]:
    """
    Convenience function to scan for expired files.

    Maintains compatibility with maintenance module API.

    Args:
        policy: Retention policy to apply
        path: Directory to scan
        category: Data category

    Returns:
        List of expired files
    """
    scanner = DatasetScanner(policy, path)
    return list(scanner.scan(category=category))
```

### 3. maintenance/retention 제거 및 리다이렉트

**파일**: `app/obs_deploy/app/src/maintenance/retention/__init__.py`

```python
"""
Deprecated: Use src/retention instead.

This module is maintained for backward compatibility only.
"""
import warnings

warnings.warn(
    "maintenance.retention is deprecated. Use retention module directly.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from unified module
from retention.policy import RetentionPolicy
from retention.scanner import scan_expired

__all__ = ["RetentionPolicy", "scan_expired"]
```

### 4. 파일 삭제

Phase 완료 후 삭제할 파일:
- `src/maintenance/retention/policy.py`
- `src/maintenance/retention/scanner.py`

---

## 마이그레이션 가이드

### 기존 코드 업데이트

#### 기존 retention 모듈 사용자
```python
# Before
from retention.policy import RetentionPolicy
policy = RetentionPolicy(raw_snapshot_days=7)

# After (변경 없음)
from retention.policy import RetentionPolicy
policy = RetentionPolicy(raw_snapshot_days=7)
```

#### 기존 maintenance.retention 모듈 사용자
```python
# Before
from maintenance.retention.policy import RetentionPolicy
policy = RetentionPolicy(ttl_days=7)

# After
from retention.policy import RetentionPolicy
policy = RetentionPolicy(ttl_days=7)
# 또는
policy = RetentionPolicy.from_ttl(7)
```

---

## 검증 방법

### 1. 단위 테스트
```python
# tests/unit/retention/test_policy.py
import pytest
from datetime import timedelta
from retention.policy import RetentionPolicy, CategoryRetention


class TestRetentionPolicy:
    def test_default_values(self):
        policy = RetentionPolicy()
        assert policy.ttl_days == 7
        assert policy.raw_snapshot_days == 7
        assert policy.pattern_record_days == 30

    def test_ttl_property(self):
        policy = RetentionPolicy(ttl_days=14)
        assert policy.ttl == timedelta(days=14)

    def test_raw_ttl_property(self):
        policy = RetentionPolicy(raw_snapshot_days=5)
        assert policy.raw_ttl == timedelta(days=5)

    def test_get_category_raw(self):
        policy = RetentionPolicy(raw_snapshot_days=10)
        category = policy.get_category("raw")
        assert category.days == 10

    def test_from_ttl(self):
        policy = RetentionPolicy.from_ttl(14)
        assert policy.ttl_days == 14
        assert policy.raw_snapshot_days == 14
        assert policy.pattern_record_days == 14

    def test_glob_patterns(self):
        policy = RetentionPolicy(
            include_globs=["*.json"],
            exclude_globs=["*.important.json"],
        )
        assert "*.json" in policy.include_globs
        assert "*.important.json" in policy.exclude_globs
```

### 2. 통합 테스트
```bash
# 기존 테스트 통과 확인
pytest app/obs_deploy/app/src/retention/ -v
pytest app/obs_deploy/app/src/maintenance/ -v

# import 테스트
python -c "from retention.policy import RetentionPolicy; print('OK')"
python -c "from maintenance.retention import RetentionPolicy; print('Deprecated warning expected')"
```

### 3. 하위 호환성 확인
```bash
# 기존 API가 동작하는지 확인
grep -rn "from retention.policy import" --include="*.py" app/obs_deploy/
grep -rn "from maintenance.retention" --include="*.py" app/obs_deploy/
```

---

## 완료 조건

- [ ] 통합 `RetentionPolicy` 클래스 구현됨
- [ ] 통합 `DatasetScanner` 클래스 구현됨
- [ ] `scan_expired()` 함수 호환성 유지됨
- [ ] `maintenance/retention/` 디렉토리에 deprecation 경고 추가됨
- [ ] 기존 retention 모듈 API 유지됨
- [ ] 기존 maintenance.retention API 유지됨 (with deprecation)
- [ ] 단위 테스트 통과
- [ ] 기존 테스트 모두 통과

---

## 관련 태스크
- [TASK-2.2](TASK-2.2-consolidate-backup.md): Backup 모듈 통합 (유사 패턴)
