# TASK-1.3: Trading Hours 유틸리티 생성

## 태스크 정보
- **Phase**: 1 - 공유 유틸리티 추출
- **우선순위**: Medium
- **의존성**: 없음
- **상태**: 대기

---

## 목표
`_in_trading_hours()` 메서드를 공유 유틸리티 함수로 추출하여 코드 중복을 제거합니다.

---

## 현재 문제

### 중복 코드 패턴
TrackACollector와 TrackBCollector에서 동일한 메서드가 반복됩니다:

```python
def _in_trading_hours(self, dt: datetime) -> bool:
    t = dt.time()
    return self.cfg.trading_start <= t <= self.cfg.trading_end
```

### 영향 파일 목록 (2개)

| # | 파일 경로 | 라인 |
|---|----------|------|
| 1 | `app/obs_deploy/app/src/collector/track_a_collector.py` | 68-70 |
| 2 | `app/obs_deploy/app/src/collector/track_b_collector.py` | 100-102 |

---

## 구현 계획

### 1. 신규 파일 생성

**파일**: `app/obs_deploy/app/src/shared/trading_hours.py`

```python
"""
Trading hours utilities for Korean stock market.

This module provides functions to check trading hours and market sessions
for the Korean stock market (KRX).
"""
from __future__ import annotations

from datetime import datetime, time
from typing import NamedTuple


__all__ = [
    "in_trading_hours",
    "TradingSession",
    "KRX_REGULAR_SESSION",
    "KRX_PRE_MARKET",
    "KRX_AFTER_HOURS",
]


class TradingSession(NamedTuple):
    """Trading session definition with start and end times."""
    name: str
    start: time
    end: time

    def contains(self, dt: datetime) -> bool:
        """Check if datetime is within this trading session."""
        t = dt.time()
        return self.start <= t <= self.end


# Korean Stock Exchange (KRX) trading sessions
KRX_PRE_MARKET = TradingSession(
    name="pre_market",
    start=time(8, 30),
    end=time(8, 59),
)

KRX_REGULAR_SESSION = TradingSession(
    name="regular",
    start=time(9, 0),
    end=time(15, 30),
)

KRX_AFTER_HOURS = TradingSession(
    name="after_hours",
    start=time(15, 40),
    end=time(18, 0),
)


def in_trading_hours(
    dt: datetime,
    start: time,
    end: time,
) -> bool:
    """
    Check if datetime is within the specified trading hours.

    Args:
        dt: Datetime to check
        start: Trading start time
        end: Trading end time

    Returns:
        True if dt is within [start, end], False otherwise

    Example:
        >>> from datetime import datetime, time
        >>> dt = datetime(2026, 1, 24, 10, 30)
        >>> in_trading_hours(dt, time(9, 0), time(15, 30))
        True
    """
    t = dt.time()
    return start <= t <= end


def is_regular_trading_hours(dt: datetime) -> bool:
    """
    Check if datetime is within KRX regular trading hours (09:00-15:30).

    Args:
        dt: Datetime to check

    Returns:
        True if within regular trading hours
    """
    return KRX_REGULAR_SESSION.contains(dt)


def is_market_open(dt: datetime) -> bool:
    """
    Check if datetime is within any KRX trading session.

    Includes pre-market, regular, and after-hours sessions.

    Args:
        dt: Datetime to check

    Returns:
        True if market is open in any session
    """
    return (
        KRX_PRE_MARKET.contains(dt) or
        KRX_REGULAR_SESSION.contains(dt) or
        KRX_AFTER_HOURS.contains(dt)
    )


def get_current_session(dt: datetime) -> TradingSession | None:
    """
    Get the current trading session for the given datetime.

    Args:
        dt: Datetime to check

    Returns:
        TradingSession if within a session, None otherwise
    """
    for session in [KRX_PRE_MARKET, KRX_REGULAR_SESSION, KRX_AFTER_HOURS]:
        if session.contains(dt):
            return session
    return None
```

### 2. 기존 파일 수정

#### `src/collector/track_a_collector.py`

**Before:**
```python
def _in_trading_hours(self, dt: datetime) -> bool:
    t = dt.time()
    return self.cfg.trading_start <= t <= self.cfg.trading_end
```

**After:**
```python
from shared.trading_hours import in_trading_hours

# 클래스 내부에서
def _in_trading_hours(self, dt: datetime) -> bool:
    return in_trading_hours(dt, self.cfg.trading_start, self.cfg.trading_end)
```

또는 메서드를 완전히 제거하고 직접 호출:
```python
# 사용 위치에서
if in_trading_hours(current_time, self.cfg.trading_start, self.cfg.trading_end):
    # ...
```

#### `src/collector/track_b_collector.py`

동일한 패턴으로 수정

---

## 검증 방법

### 1. 단위 테스트
```python
# tests/unit/shared/test_trading_hours.py
import pytest
from datetime import datetime, time
from shared.trading_hours import (
    in_trading_hours,
    is_regular_trading_hours,
    is_market_open,
    get_current_session,
    KRX_REGULAR_SESSION,
    TradingSession,
)


class TestInTradingHours:
    def test_within_hours(self):
        dt = datetime(2026, 1, 24, 10, 30)
        assert in_trading_hours(dt, time(9, 0), time(15, 30)) is True

    def test_before_hours(self):
        dt = datetime(2026, 1, 24, 8, 30)
        assert in_trading_hours(dt, time(9, 0), time(15, 30)) is False

    def test_after_hours(self):
        dt = datetime(2026, 1, 24, 16, 0)
        assert in_trading_hours(dt, time(9, 0), time(15, 30)) is False

    def test_at_start_boundary(self):
        dt = datetime(2026, 1, 24, 9, 0)
        assert in_trading_hours(dt, time(9, 0), time(15, 30)) is True

    def test_at_end_boundary(self):
        dt = datetime(2026, 1, 24, 15, 30)
        assert in_trading_hours(dt, time(9, 0), time(15, 30)) is True


class TestTradingSession:
    def test_session_contains(self):
        dt = datetime(2026, 1, 24, 10, 0)
        assert KRX_REGULAR_SESSION.contains(dt) is True

    def test_session_not_contains(self):
        dt = datetime(2026, 1, 24, 8, 0)
        assert KRX_REGULAR_SESSION.contains(dt) is False


class TestGetCurrentSession:
    def test_regular_session(self):
        dt = datetime(2026, 1, 24, 10, 0)
        session = get_current_session(dt)
        assert session is not None
        assert session.name == "regular"

    def test_no_session(self):
        dt = datetime(2026, 1, 24, 7, 0)
        session = get_current_session(dt)
        assert session is None
```

### 2. 통합 테스트
```bash
# 기존 테스트 통과 확인
pytest app/obs_deploy/app/src/collector/ -v

# 중복 패턴 검색
grep -rn "_in_trading_hours" --include="*.py" app/obs_deploy/app/src/
```

---

## 완료 조건

- [ ] `src/shared/trading_hours.py` 파일 생성됨
- [ ] `in_trading_hours()` 함수 구현됨
- [ ] `TradingSession` 클래스 구현됨
- [ ] KRX 세션 상수 정의됨
- [ ] track_a_collector.py 수정됨
- [ ] track_b_collector.py 수정됨
- [ ] 단위 테스트 통과
- [ ] 기존 테스트 모두 통과

---

## 추가 고려사항

### 휴장일 처리
현재 구현은 시간만 확인합니다. 휴장일 처리가 필요한 경우 향후 확장:

```python
# 향후 확장 예시
HOLIDAYS_2026 = [
    date(2026, 1, 1),   # 신정
    date(2026, 1, 27),  # 설날 연휴
    # ...
]

def is_trading_day(dt: datetime) -> bool:
    """Check if date is a trading day (not weekend or holiday)."""
    if dt.weekday() >= 5:  # Saturday or Sunday
        return False
    if dt.date() in HOLIDAYS_2026:
        return False
    return True
```

---

## 관련 태스크
- [TASK-3.1](../phase-3/TASK-3.1-base-collector.md): BaseCollector (이 유틸리티 사용)
