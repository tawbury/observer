# TASK-1.2: Time Helper Mixin 생성

## 태스크 정보
- **Phase**: 1 - 공유 유틸리티 추출
- **우선순위**: Critical
- **의존성**: TASK-1.1 (Timezone 유틸리티)
- **상태**: 대기

---

## 목표
`_now()` 헬퍼 메서드를 TimeAwareMixin 클래스로 추출하여 8개 파일의 코드 중복을 제거합니다.

---

## 현재 문제

### 중복 코드 패턴
다음 파일들에서 거의 동일한 `_now()` 메서드가 반복됩니다:

```python
def _now(self) -> datetime:
    if self._tz:
        return datetime.now(self._tz)
    return datetime.now()
```

### 영향 파일 목록 (8개)

| # | 파일 경로 | 메서드 위치 |
|---|----------|------------|
| 1 | `app/obs_deploy/app/src/auth/token_lifecycle_manager.py` | 라인 ~81 |
| 2 | `app/obs_deploy/app/src/collector/track_a_collector.py` | 라인 ~63 |
| 3 | `app/obs_deploy/app/src/collector/track_b_collector.py` | 라인 ~95 |
| 4 | `app/obs_deploy/app/src/gap/gap_detector.py` | 라인 ~288 |
| 5 | `app/obs_deploy/app/src/retention/cleaner.py` | 라인 ~25 |
| 6 | `app/obs_deploy/app/src/observer/log_rotation_manager.py` | 라인 ~165 |
| 7 | `app/obs_deploy/app/src/backup/manager.py` | 라인 ~31 |
| 8 | `app/obs_deploy/app/src/backup/backup_manager.py` | 라인 ~106 |

---

## 구현 계획

### 1. 신규 파일 생성

**파일**: `app/obs_deploy/app/src/shared/time_helpers.py`

```python
"""
Time helper utilities and mixins for timezone-aware datetime operations.

This module provides reusable components for handling time operations
consistently across the codebase.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .timezone import get_zoneinfo


__all__ = ["TimeAwareMixin", "now_with_timezone"]


class TimeAwareMixin:
    """
    Mixin class providing timezone-aware time helpers.

    Classes using this mixin should set `_tz_name` attribute
    to enable timezone-aware datetime operations.

    Attributes:
        _tz_name: Optional timezone name (e.g., "Asia/Seoul")
        _tz: Cached ZoneInfo object (set automatically)

    Example:
        >>> class MyCollector(TimeAwareMixin):
        ...     def __init__(self):
        ...         self._tz_name = "Asia/Seoul"
        ...         self._init_timezone()
        ...
        ...     def collect(self):
        ...         current_time = self._now()
    """

    _tz_name: Optional[str] = None
    _tz: Optional[object] = None  # ZoneInfo or None

    def _init_timezone(self) -> None:
        """
        Initialize timezone from _tz_name.
        Call this in __init__ after setting _tz_name.
        """
        if self._tz_name:
            self._tz = get_zoneinfo(self._tz_name)
        else:
            self._tz = None

    def _now(self) -> datetime:
        """
        Get current datetime with configured timezone.

        Returns:
            Current datetime. If timezone is configured and available,
            returns timezone-aware datetime. Otherwise returns UTC.
        """
        if self._tz:
            return datetime.now(self._tz)
        return datetime.now(timezone.utc)

    def _today(self) -> datetime:
        """
        Get today's date at midnight with configured timezone.

        Returns:
            Today's date at 00:00:00 with timezone info.
        """
        now = self._now()
        return now.replace(hour=0, minute=0, second=0, microsecond=0)


def now_with_timezone(tz_name: Optional[str] = None) -> datetime:
    """
    Standalone function to get current datetime with timezone.

    Use this when you don't need the mixin pattern.

    Args:
        tz_name: Optional timezone name

    Returns:
        Current datetime with timezone
    """
    if tz_name:
        tz = get_zoneinfo(tz_name)
        if tz:
            return datetime.now(tz)
    return datetime.now(timezone.utc)
```

### 2. 기존 파일 수정 패턴

**Before:**
```python
class SomeClass:
    def __init__(self, config):
        self.cfg = config
        if config.tz_name:
            self._tz = ZoneInfo(config.tz_name)
        else:
            self._tz = None

    def _now(self) -> datetime:
        if self._tz:
            return datetime.now(self._tz)
        return datetime.now()
```

**After:**
```python
from shared.time_helpers import TimeAwareMixin

class SomeClass(TimeAwareMixin):
    def __init__(self, config):
        self.cfg = config
        self._tz_name = config.tz_name
        self._init_timezone()

    # _now() 메서드 제거 - 믹스인에서 상속
```

### 3. 파일별 수정 사항

#### `src/auth/token_lifecycle_manager.py`
```python
# Before
class TokenLifecycleManager:
    def __init__(self, cfg: TokenLifecycleConfig, ...):
        if cfg.tz_name:
            self._tz = ZoneInfo(cfg.tz_name)
        # ...

    def _now(self) -> datetime:
        if self._tz:
            return datetime.now(self._tz)
        return datetime.now()

# After
from shared.time_helpers import TimeAwareMixin

class TokenLifecycleManager(TimeAwareMixin):
    def __init__(self, cfg: TokenLifecycleConfig, ...):
        self._tz_name = cfg.tz_name
        self._init_timezone()
        # ...
    # _now() 메서드 제거
```

#### `src/collector/track_a_collector.py`
```python
# After
from shared.time_helpers import TimeAwareMixin

class TrackACollector(TimeAwareMixin):
    def __init__(self, cfg: TrackAConfig, ...):
        self._tz_name = cfg.tz_name
        self._init_timezone()
        # ...
```

#### `src/collector/track_b_collector.py`
```python
# After
from shared.time_helpers import TimeAwareMixin

class TrackBCollector(TimeAwareMixin):
    def __init__(self, cfg: TrackBConfig, ...):
        self._tz_name = cfg.tz_name
        self._init_timezone()
        # ...
```

#### `src/gap/gap_detector.py`
```python
# After
from shared.time_helpers import TimeAwareMixin

class GapDetector(TimeAwareMixin):
    def __init__(self, config: GapDetectorConfig, ...):
        self._tz_name = config.tz_name
        self._init_timezone()
        # ...
```

#### `src/retention/cleaner.py`
```python
# After
from shared.time_helpers import TimeAwareMixin

class RetentionCleaner(TimeAwareMixin):
    def __init__(self, config, ...):
        self._tz_name = config.tz_name if hasattr(config, 'tz_name') else None
        self._init_timezone()
        # ...
```

#### `src/observer/log_rotation_manager.py`
```python
# After
from shared.time_helpers import TimeAwareMixin

class LogRotationManager(TimeAwareMixin):
    def __init__(self, config, ...):
        self._tz_name = config.tz_name
        self._init_timezone()
        # ...
```

#### `src/backup/manager.py`
```python
# After
from shared.time_helpers import TimeAwareMixin

class BackupManager(TimeAwareMixin):
    def __init__(self, config, ...):
        self._tz_name = getattr(config, 'tz_name', None)
        self._init_timezone()
        # ...
```

#### `src/backup/backup_manager.py`
```python
# After
from shared.time_helpers import TimeAwareMixin

class BackupManager(TimeAwareMixin):
    def __init__(self, config: BackupConfig, ...):
        self._tz_name = config.tz_name
        self._init_timezone()
        # ...
```

---

## 검증 방법

### 1. 단위 테스트
```python
# tests/unit/shared/test_time_helpers.py
import pytest
from datetime import datetime, timezone
from shared.time_helpers import TimeAwareMixin, now_with_timezone


class TestTimeAwareMixin:
    def test_now_with_timezone(self):
        class TestClass(TimeAwareMixin):
            def __init__(self):
                self._tz_name = "Asia/Seoul"
                self._init_timezone()

        obj = TestClass()
        now = obj._now()
        assert now.tzinfo is not None

    def test_now_without_timezone(self):
        class TestClass(TimeAwareMixin):
            def __init__(self):
                self._tz_name = None
                self._init_timezone()

        obj = TestClass()
        now = obj._now()
        assert now.tzinfo == timezone.utc

    def test_today(self):
        class TestClass(TimeAwareMixin):
            def __init__(self):
                self._tz_name = "Asia/Seoul"
                self._init_timezone()

        obj = TestClass()
        today = obj._today()
        assert today.hour == 0
        assert today.minute == 0


def test_now_with_timezone_function():
    now = now_with_timezone("Asia/Seoul")
    assert now.tzinfo is not None


def test_now_with_timezone_none():
    now = now_with_timezone(None)
    assert now.tzinfo == timezone.utc
```

### 2. 통합 테스트
```bash
# 모든 기존 테스트가 통과하는지 확인
pytest app/obs_deploy/app/src/ -v

# _now 메서드 중복 검색 (shared 외에 0개여야 함)
grep -rn "def _now(self)" --include="*.py" app/obs_deploy/app/src/ | grep -v shared/
```

### 3. 상속 확인
```bash
# TimeAwareMixin 상속 확인
grep -rn "TimeAwareMixin" --include="*.py" app/obs_deploy/app/src/
```

---

## 완료 조건

- [ ] `src/shared/time_helpers.py` 파일 생성됨
- [ ] 모든 8개 파일에서 `_now()` 메서드 제거됨
- [ ] 모든 8개 클래스가 `TimeAwareMixin` 상속
- [ ] `_init_timezone()` 호출 추가됨
- [ ] 단위 테스트 통과
- [ ] 기존 테스트 모두 통과
- [ ] 중복 `_now()` 메서드가 없음

---

## 주의사항

1. **다중 상속 순서**: 기존에 다른 클래스를 상속받는 경우, TimeAwareMixin을 먼저 배치
   ```python
   class MyClass(TimeAwareMixin, SomeOtherBase):
   ```

2. **_init_timezone() 호출 필수**: `__init__`에서 `_tz_name` 설정 후 반드시 호출

3. **기존 _tz 속성**: 일부 클래스는 이미 `_tz` 속성을 사용 중일 수 있음. 믹스인의 `_tz`와 충돌 여부 확인 필요

---

## 관련 태스크
- [TASK-1.1](TASK-1.1-timezone-utility.md): Timezone 유틸리티 (선행 태스크)
- [TASK-3.1](../phase-3/TASK-3.1-base-collector.md): BaseCollector (이 태스크 사용)
