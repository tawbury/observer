# TASK-1.1: Timezone 유틸리티 생성

## 태스크 정보
- **Phase**: 1 - 공유 유틸리티 추출
- **우선순위**: Critical
- **의존성**: 없음
- **상태**: 대기

---

## 목표
ZoneInfo import 패턴을 중앙화된 유틸리티 모듈로 추출하여 코드 중복을 제거합니다.

---

## 현재 문제

### 중복 코드 패턴
다음 파일들에서 동일한 패턴이 반복됩니다:

```python
try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore
```

### 영향 파일 목록 (9개)

| # | 파일 경로 | 라인 |
|---|----------|------|
| 1 | `app/obs_deploy/app/src/auth/token_lifecycle_manager.py` | 20-23 |
| 2 | `app/obs_deploy/app/src/collector/track_a_collector.py` | 17-20 |
| 3 | `app/obs_deploy/app/src/collector/track_b_collector.py` | 27-30 |
| 4 | `app/obs_deploy/app/src/gap/gap_detector.py` | 21-24 |
| 5 | `app/obs_deploy/app/src/monitoring/prometheus_metrics.py` | 29-32 |
| 6 | `app/obs_deploy/app/src/monitoring/grafana_dashboard.py` | 28-31 |
| 7 | `app/obs_deploy/app/src/optimize/performance_profiler.py` | 30-33 |
| 8 | `app/obs_deploy/app/src/observer/log_rotation_manager.py` | 17-20 |
| 9 | `app/obs_deploy/app/src/universe/universe_scheduler.py` | 10-13 |

---

## 구현 계획

### 1. 신규 파일 생성

**파일**: `app/obs_deploy/app/src/shared/timezone.py`

```python
"""
Timezone utilities with ZoneInfo compatibility.

This module provides a unified interface for timezone handling,
with fallback support for environments where zoneinfo is unavailable.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

# ZoneInfo compatibility wrapper
try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore

if TYPE_CHECKING:
    from zoneinfo import ZoneInfo as ZoneInfoType


__all__ = ["ZoneInfo", "get_zoneinfo", "now_with_tz", "is_zoneinfo_available"]


def is_zoneinfo_available() -> bool:
    """Check if ZoneInfo is available in the current environment."""
    return ZoneInfo is not None


def get_zoneinfo(tz_name: str) -> Optional["ZoneInfoType"]:
    """
    Get a ZoneInfo object for the given timezone name.

    Args:
        tz_name: Timezone name (e.g., "Asia/Seoul", "UTC")

    Returns:
        ZoneInfo object if available, None otherwise

    Example:
        >>> tz = get_zoneinfo("Asia/Seoul")
        >>> if tz:
        ...     now = datetime.now(tz)
    """
    if ZoneInfo is None:
        return None
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return None


def now_with_tz(tz_name: Optional[str] = None) -> datetime:
    """
    Get current datetime with optional timezone.

    Args:
        tz_name: Optional timezone name. If None or ZoneInfo unavailable,
                 returns UTC datetime.

    Returns:
        Current datetime with timezone info

    Example:
        >>> now = now_with_tz("Asia/Seoul")
        >>> now.tzinfo is not None
        True
    """
    if tz_name and ZoneInfo is not None:
        try:
            return datetime.now(ZoneInfo(tz_name))
        except Exception:
            pass
    return datetime.now(timezone.utc)
```

### 2. 기존 파일 수정

각 파일에서 다음과 같이 변경합니다:

**Before:**
```python
try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore
```

**After:**
```python
from shared.timezone import ZoneInfo, get_zoneinfo
```

### 3. 파일별 수정 사항

#### `src/auth/token_lifecycle_manager.py`
- 라인 20-23: try/except 블록 제거
- 라인 1 근처: `from shared.timezone import ZoneInfo, get_zoneinfo` 추가

#### `src/collector/track_a_collector.py`
- 라인 17-20: try/except 블록 제거
- 상단에 shared import 추가

#### `src/collector/track_b_collector.py`
- 라인 27-30: try/except 블록 제거
- 상단에 shared import 추가

#### `src/gap/gap_detector.py`
- 라인 21-24: try/except 블록 제거
- 상단에 shared import 추가

#### `src/monitoring/prometheus_metrics.py`
- 라인 29-32: try/except 블록 제거
- 상단에 shared import 추가

#### `src/monitoring/grafana_dashboard.py`
- 라인 28-31: try/except 블록 제거
- 상단에 shared import 추가

#### `src/optimize/performance_profiler.py`
- 라인 30-33: try/except 블록 제거
- 상단에 shared import 추가

#### `src/observer/log_rotation_manager.py`
- 라인 17-20: try/except 블록 제거
- 상단에 shared import 추가

#### `src/universe/universe_scheduler.py`
- 라인 10-13: try/except 블록 제거
- 상단에 shared import 추가

---

## 검증 방법

### 1. 단위 테스트
```python
# tests/unit/shared/test_timezone.py
import pytest
from shared.timezone import (
    ZoneInfo,
    get_zoneinfo,
    now_with_tz,
    is_zoneinfo_available
)

def test_get_zoneinfo_valid():
    tz = get_zoneinfo("Asia/Seoul")
    if is_zoneinfo_available():
        assert tz is not None
    else:
        assert tz is None

def test_get_zoneinfo_invalid():
    tz = get_zoneinfo("Invalid/Timezone")
    assert tz is None

def test_now_with_tz():
    now = now_with_tz("Asia/Seoul")
    assert now.tzinfo is not None

def test_now_with_tz_none():
    now = now_with_tz(None)
    assert now.tzinfo is not None  # Falls back to UTC
```

### 2. 통합 테스트
```bash
# 모든 기존 테스트가 통과하는지 확인
pytest app/obs_deploy/app/src/ -v

# ZoneInfo 관련 import 패턴 검색 (0개여야 함)
grep -rn "try:" --include="*.py" app/obs_deploy/app/src/ | grep -i "zoneinfo"
```

### 3. 중복 패턴 확인
```bash
# 다음 명령어 결과가 0개여야 함
grep -rn "from zoneinfo import ZoneInfo" --include="*.py" app/obs_deploy/app/src/ | grep -v shared/timezone.py
```

---

## 완료 조건

- [ ] `src/shared/timezone.py` 파일 생성됨
- [ ] 모든 9개 파일에서 중복 코드 제거됨
- [ ] 새로운 import 문으로 대체됨
- [ ] 단위 테스트 통과
- [ ] 기존 테스트 모두 통과
- [ ] `try: from zoneinfo` 패턴이 shared/timezone.py 외에 없음

---

## 롤백 계획

문제 발생 시:
1. Git에서 변경 전 상태로 복원
2. 개별 파일 단위로 원래 try/except 패턴 복구

```bash
git checkout HEAD~1 -- app/obs_deploy/app/src/auth/token_lifecycle_manager.py
# ... 각 파일에 대해 반복
```

---

## 관련 태스크
- [TASK-1.2](TASK-1.2-time-helper-mixin.md): Time Helper Mixin (이 태스크에 의존)
