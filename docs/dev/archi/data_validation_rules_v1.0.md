# 데이터 검증 및 Guard 규칙 명세서

**Document ID**: SPEC-DATA-VALIDATION-001
**Version**: 1.0.0
**Date**: 2026-01-20
**Parent Document**: data_pipeline_architecture_observer_v1.0.md
**Status**: Draft

---

## 1. 개요

본 문서는 Stock Trading Observer의 Observer Core에서 수행하는 데이터 검증(Validation)과 Guard 체크 규칙을 정의합니다.

### 1.1 검증 파이프라인

```
Raw Data (Provider)
    ↓
[Phase 1] Schema Validation (스키마 검증)
    ↓
[Phase 2] Range Validation (범위 검증)
    ↓
[Phase 3] Guard Checks (이상 데이터 필터링)
    ↓
[Phase 4] Quality Flag Assignment (품질 플래그 할당)
    ↓
Validated Data → Observer Core
```

---

## 2. Schema Validation (스키마 검증)

### 2.1 MarketDataContract 필수 필드 검증

#### 필수 필드 목록

| 경로 | 필드명 | 타입 | 필수 여부 | 설명 |
|-----|--------|------|----------|------|
| `meta.source` | 프로바이더 | string | **필수** | kis, kiwoom, upbit, ib |
| `meta.market` | 마켓 | string | **필수** | kr_stocks, crypto, us_stocks |
| `meta.captured_at` | 수집 시각 | ISO8601 | **필수** | 시스템 수신 시각 |
| `meta.schema_version` | 스키마 버전 | string | **필수** | 1.0 |
| `instruments[].symbol` | 종목 코드 | string | **필수** | 6자리 (국내) |
| `instruments[].timestamp` | 이벤트 시각 | ISO8601 | **필수** | 원본 이벤트 시각 |
| `instruments[].price.open` | 시가 | float | **필수** | > 0 |
| `instruments[].price.high` | 고가 | float | **필수** | > 0 |
| `instruments[].price.low` | 저가 | float | **필수** | > 0 |
| `instruments[].price.close` | 종가/현재가 | float | **필수** | > 0 |
| `instruments[].volume` | 거래량 | int | **필수** | >= 0 |
| `instruments[].bid_price` | 매수호가 | float | 선택 | > 0 |
| `instruments[].ask_price` | 매도호가 | float | 선택 | > 0 |
| `instruments[].bid_size` | 매수잔량 | int | 선택 | >= 0 |
| `instruments[].ask_size` | 매도잔량 | int | 선택 | >= 0 |

#### 검증 규칙

**V-001: 필수 필드 존재 검증**
```python
def validate_required_fields(data: dict) -> ValidationResult:
    """
    필수 필드 존재 여부 검증

    Returns:
        ValidationResult(passed=True/False, errors=[...])
    """
    required_paths = [
        "meta.source",
        "meta.market",
        "meta.captured_at",
        "meta.schema_version",
        "instruments[0].symbol",
        "instruments[0].timestamp",
        "instruments[0].price.open",
        "instruments[0].price.high",
        "instruments[0].price.low",
        "instruments[0].price.close",
        "instruments[0].volume"
    ]

    errors = []
    for path in required_paths:
        if not get_nested_value(data, path):
            errors.append(f"Missing required field: {path}")

    return ValidationResult(
        passed=(len(errors) == 0),
        errors=errors
    )
```

**V-002: 타입 검증**
```python
FIELD_TYPES = {
    "meta.source": str,
    "meta.market": str,
    "meta.captured_at": str,  # ISO8601
    "meta.schema_version": str,
    "instruments[0].symbol": str,
    "instruments[0].timestamp": str,
    "instruments[0].price.open": (int, float),
    "instruments[0].price.high": (int, float),
    "instruments[0].price.low": (int, float),
    "instruments[0].price.close": (int, float),
    "instruments[0].volume": int,
    "instruments[0].bid_price": (int, float, type(None)),
    "instruments[0].ask_price": (int, float, type(None)),
    "instruments[0].bid_size": (int, type(None)),
    "instruments[0].ask_size": (int, type(None))
}

def validate_field_types(data: dict) -> ValidationResult:
    """필드 타입 검증"""
    errors = []

    for path, expected_type in FIELD_TYPES.items():
        value = get_nested_value(data, path)
        if value is not None and not isinstance(value, expected_type):
            errors.append(f"Invalid type for {path}: expected {expected_type}, got {type(value)}")

    return ValidationResult(passed=(len(errors) == 0), errors=errors)
```

**V-003: Enum 값 검증**
```python
VALID_ENUMS = {
    "meta.source": ["kis", "kiwoom", "upbit", "ib"],
    "meta.market": ["kr_stocks", "crypto", "us_stocks"],
    "meta.schema_version": ["1.0"]
}

def validate_enum_values(data: dict) -> ValidationResult:
    """Enum 값 검증"""
    errors = []

    for path, valid_values in VALID_ENUMS.items():
        value = get_nested_value(data, path)
        if value and value not in valid_values:
            errors.append(f"Invalid value for {path}: {value} not in {valid_values}")

    return ValidationResult(passed=(len(errors) == 0), errors=errors)
```

### 2.2 ISO8601 타임스탬프 검증

**V-004: ISO8601 포맷 검증**
```python
import re
from datetime import datetime

ISO8601_REGEX = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3,6})?(Z|[+-]\d{2}:\d{2})$'

def validate_iso8601_timestamp(timestamp: str) -> bool:
    """
    ISO8601 타임스탬프 검증

    Valid examples:
        - 2026-01-20T09:31:05.123Z
        - 2026-01-20T09:31:05+09:00
        - 2026-01-20T09:31:05.123456+09:00
    """
    if not re.match(ISO8601_REGEX, timestamp):
        return False

    try:
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False
```

**V-005: 타임스탬프 시간 범위 검증**
```python
from datetime import datetime, timedelta, timezone

def validate_timestamp_range(timestamp: str) -> ValidationResult:
    """
    타임스탬프가 합리적인 범위 내에 있는지 검증

    Rules:
        - 미래 시각은 최대 5초까지 허용 (시계 오차)
        - 과거 시각은 최대 24시간까지 허용 (재처리 고려)
    """
    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)

    future_threshold = now + timedelta(seconds=5)
    past_threshold = now - timedelta(hours=24)

    if dt > future_threshold:
        return ValidationResult(
            passed=False,
            errors=[f"Timestamp too far in future: {timestamp}"]
        )

    if dt < past_threshold:
        return ValidationResult(
            passed=False,
            errors=[f"Timestamp too far in past: {timestamp}"]
        )

    return ValidationResult(passed=True, errors=[])
```

---

## 3. Range Validation (범위 검증)

### 3.1 가격 필드 범위 검증

**V-006: 가격 양수 검증**
```python
def validate_price_positive(price_data: dict) -> ValidationResult:
    """
    모든 가격 필드가 양수인지 검증

    Fields: open, high, low, close, bid_price, ask_price
    """
    errors = []
    price_fields = ['open', 'high', 'low', 'close']

    for field in price_fields:
        value = price_data.get(field)
        if value is not None and value <= 0:
            errors.append(f"Price {field} must be positive: {value}")

    # 선택 필드
    if price_data.get('bid_price') is not None and price_data['bid_price'] <= 0:
        errors.append(f"bid_price must be positive: {price_data['bid_price']}")

    if price_data.get('ask_price') is not None and price_data['ask_price'] <= 0:
        errors.append(f"ask_price must be positive: {price_data['ask_price']}")

    return ValidationResult(passed=(len(errors) == 0), errors=errors)
```

**V-007: OHLC 관계 검증**
```python
def validate_ohlc_relationship(price_data: dict) -> ValidationResult:
    """
    OHLC 가격 관계 검증

    Rules:
        - High >= Open, Close, Low
        - Low <= Open, Close, High
    """
    o = price_data['open']
    h = price_data['high']
    l = price_data['low']
    c = price_data['close']

    errors = []

    if h < o or h < c or h < l:
        errors.append(f"High {h} must be >= Open {o}, Close {c}, Low {l}")

    if l > o or l > c or l > h:
        errors.append(f"Low {l} must be <= Open {o}, Close {c}, High {h}")

    return ValidationResult(passed=(len(errors) == 0), errors=errors)
```

**V-008: 호가 스프레드 검증**
```python
def validate_bid_ask_spread(instrument: dict) -> ValidationResult:
    """
    매수/매도 호가 스프레드 검증

    Rules:
        - Ask >= Bid (스프레드는 항상 양수 또는 0)
        - 스프레드가 현재가의 10% 초과 시 경고
    """
    bid = instrument.get('bid_price')
    ask = instrument.get('ask_price')

    if bid is None or ask is None:
        return ValidationResult(passed=True, errors=[])

    errors = []
    warnings = []

    if ask < bid:
        errors.append(f"Ask {ask} < Bid {bid} (invalid spread)")

    spread_pct = ((ask - bid) / bid) * 100 if bid > 0 else 0
    if spread_pct > 10:
        warnings.append(f"Wide spread: {spread_pct:.2f}% (Bid: {bid}, Ask: {ask})")

    return ValidationResult(
        passed=(len(errors) == 0),
        errors=errors,
        warnings=warnings
    )
```

### 3.2 거래량 범위 검증

**V-009: 거래량 음수 검증**
```python
def validate_volume_non_negative(volume: int) -> ValidationResult:
    """
    거래량이 0 이상인지 검증
    """
    if volume < 0:
        return ValidationResult(
            passed=False,
            errors=[f"Volume must be non-negative: {volume}"]
        )

    return ValidationResult(passed=True, errors=[])
```

**V-010: 거래량 상한 검증 (이상치 탐지)**
```python
def validate_volume_upper_bound(symbol: str, volume: int, market: str) -> ValidationResult:
    """
    거래량 이상치 검증

    Rules (kr_stocks):
        - 거래량 > 10억 주: 경고
        - 거래량 > 100억 주: 오류 (비정상)
    """
    warnings = []
    errors = []

    if market == "kr_stocks":
        if volume > 10_000_000_000:  # 100억 주
            errors.append(f"Abnormal volume for {symbol}: {volume:,}")
        elif volume > 1_000_000_000:  # 10억 주
            warnings.append(f"High volume for {symbol}: {volume:,}")

    return ValidationResult(
        passed=(len(errors) == 0),
        errors=errors,
        warnings=warnings
    )
```

### 3.3 종목 코드 검증

**V-011: 종목 코드 포맷 검증**
```python
import re

SYMBOL_PATTERNS = {
    "kr_stocks": r'^\d{6}$',        # 6자리 숫자 (예: 005930)
    "crypto": r'^[A-Z]+-[A-Z]+$',   # BTC-KRW, ETH-USDT
    "us_stocks": r'^[A-Z]{1,5}$'    # AAPL, MSFT, GOOGL
}

def validate_symbol_format(symbol: str, market: str) -> ValidationResult:
    """
    종목 코드 포맷 검증
    """
    pattern = SYMBOL_PATTERNS.get(market)

    if not pattern:
        return ValidationResult(
            passed=False,
            errors=[f"Unknown market: {market}"]
        )

    if not re.match(pattern, symbol):
        return ValidationResult(
            passed=False,
            errors=[f"Invalid symbol format for {market}: {symbol}"]
        )

    return ValidationResult(passed=True, errors=[])
```

---

## 4. Guard Checks (이상 데이터 필터링)

### 4.1 가격 급등락 Guard

**G-001: 전일 대비 급등락 감지**
```python
def guard_price_spike(symbol: str, current_price: float, prev_close: float) -> GuardResult:
    """
    전일 종가 대비 급등락 감지

    Rules:
        - 상승/하락률 > 30%: 상한가/하한가 의심, degraded flag
        - 상승/하락률 > 50%: 데이터 오류 의심, rejected
    """
    change_pct = abs((current_price - prev_close) / prev_close) * 100

    if change_pct > 50:
        return GuardResult(
            passed=False,
            action="REJECT",
            reason=f"Extreme price change: {change_pct:.2f}%",
            quality_flag="rejected"
        )

    if change_pct > 30:
        return GuardResult(
            passed=True,
            action="ACCEPT_DEGRADED",
            reason=f"Large price change: {change_pct:.2f}% (possible limit up/down)",
            quality_flag="degraded"
        )

    return GuardResult(
        passed=True,
        action="ACCEPT",
        quality_flag="normal"
    )
```

**G-002: 틱 간 가격 급변 감지 (Scalp 전용)**
```python
def guard_tick_price_jump(symbol: str, current_price: float, prev_tick_price: float) -> GuardResult:
    """
    이전 틱 대비 가격 급변 감지 (2Hz WebSocket 데이터)

    Rules:
        - 틱 간 변화율 > 5%: 체결 오류 또는 급등락, degraded
        - 틱 간 변화율 > 10%: 데이터 오류 의심, rejected
    """
    if prev_tick_price is None or prev_tick_price == 0:
        return GuardResult(passed=True, action="ACCEPT", quality_flag="normal")

    change_pct = abs((current_price - prev_tick_price) / prev_tick_price) * 100

    if change_pct > 10:
        return GuardResult(
            passed=False,
            action="REJECT",
            reason=f"Extreme tick jump: {change_pct:.2f}%",
            quality_flag="rejected"
        )

    if change_pct > 5:
        return GuardResult(
            passed=True,
            action="ACCEPT_DEGRADED",
            reason=f"Large tick jump: {change_pct:.2f}%",
            quality_flag="degraded"
        )

    return GuardResult(passed=True, action="ACCEPT", quality_flag="normal")
```

### 4.2 거래량 이상 Guard

**G-003: 거래량 급증 감지**
```python
def guard_volume_surge(symbol: str, current_volume: int, avg_volume_5m: int) -> GuardResult:
    """
    5분 평균 대비 거래량 급증 감지

    Rules:
        - 거래량 > 평균 × 10: 급증 이벤트, degraded (정상 이벤트일 수 있음)
        - 거래량 > 평균 × 50: 데이터 오류 의심, rejected
    """
    if avg_volume_5m == 0:
        return GuardResult(passed=True, action="ACCEPT", quality_flag="normal")

    surge_ratio = current_volume / avg_volume_5m

    if surge_ratio > 50:
        return GuardResult(
            passed=False,
            action="REJECT",
            reason=f"Extreme volume surge: {surge_ratio:.1f}x average",
            quality_flag="rejected"
        )

    if surge_ratio > 10:
        return GuardResult(
            passed=True,
            action="ACCEPT_DEGRADED",
            reason=f"Volume surge: {surge_ratio:.1f}x average (possible news event)",
            quality_flag="degraded"
        )

    return GuardResult(passed=True, action="ACCEPT", quality_flag="normal")
```

### 4.3 타임스탬프 순서 Guard

**G-004: 시간 역행 감지**
```python
def guard_timestamp_order(symbol: str, current_ts: datetime, prev_ts: datetime) -> GuardResult:
    """
    타임스탬프 순서 검증 (시간 역행 감지)

    Rules:
        - current_ts < prev_ts: 시간 역행, rejected
        - current_ts == prev_ts: 중복 가능성, degraded
    """
    if prev_ts is None:
        return GuardResult(passed=True, action="ACCEPT", quality_flag="normal")

    if current_ts < prev_ts:
        return GuardResult(
            passed=False,
            action="REJECT",
            reason=f"Timestamp out of order: {current_ts} < {prev_ts}",
            quality_flag="rejected"
        )

    if current_ts == prev_ts:
        return GuardResult(
            passed=True,
            action="ACCEPT_DEGRADED",
            reason=f"Duplicate timestamp: {current_ts}",
            quality_flag="degraded"
        )

    return GuardResult(passed=True, action="ACCEPT", quality_flag="normal")
```

### 4.4 Market Hours Guard

**G-005: 장 운영 시간 검증**
```python
from datetime import time

MARKET_HOURS = {
    "kr_stocks": {
        "open": time(9, 0),
        "close": time(15, 30)
    },
    "crypto": {
        "open": time(0, 0),
        "close": time(23, 59)  # 24시간
    },
    "us_stocks": {
        "open": time(23, 30),   # KST 기준 (US 09:30 ET)
        "close": time(6, 0)     # KST 기준 (US 16:00 ET)
    }
}

def guard_market_hours(market: str, timestamp: datetime) -> GuardResult:
    """
    장 운영 시간 내 데이터인지 검증

    Rules:
        - 장 외 시간 데이터: degraded (시간외 거래 가능성)
        - 공휴일/주말: degraded
    """
    hours = MARKET_HOURS.get(market)
    if not hours:
        return GuardResult(passed=True, action="ACCEPT", quality_flag="normal")

    # 암호화폐는 24시간
    if market == "crypto":
        return GuardResult(passed=True, action="ACCEPT", quality_flag="normal")

    event_time = timestamp.time()
    is_weekend = timestamp.weekday() >= 5  # 5=토, 6=일

    if is_weekend:
        return GuardResult(
            passed=True,
            action="ACCEPT_DEGRADED",
            reason="Weekend trading data",
            quality_flag="degraded"
        )

    if not (hours["open"] <= event_time <= hours["close"]):
        return GuardResult(
            passed=True,
            action="ACCEPT_DEGRADED",
            reason=f"After-hours trading: {event_time}",
            quality_flag="degraded"
        )

    return GuardResult(passed=True, action="ACCEPT", quality_flag="normal")
```

---

## 5. Quality Flag Assignment

### 5.1 Quality Flag 종류

| Flag | 의미 | 조건 | 사용 처리 |
|------|------|------|---------|
| **normal** | 정상 데이터 | 모든 검증 통과 | 전략에 바로 사용 가능 |
| **degraded** | 품질 저하 | Guard에서 경고 발생 | 주의하여 사용 (필터링 고려) |
| **gap** | 갭 구간 | 데이터 수신 중단 후 재수신 | 갭 분석 시 제외 |
| **rejected** | 거부됨 | Validation 실패 또는 Guard 거부 | 사용 불가, 로그만 기록 |

### 5.2 Quality Flag 할당 로직

```python
def assign_quality_flag(
    validation_result: ValidationResult,
    guard_results: List[GuardResult],
    is_after_gap: bool = False
) -> str:
    """
    최종 Quality Flag 할당

    Priority (높은 순):
        1. rejected (validation 실패 또는 guard 거부)
        2. gap (갭 후 첫 데이터)
        3. degraded (guard 경고)
        4. normal (모두 통과)
    """
    # Validation 실패
    if not validation_result.passed:
        return "rejected"

    # Guard 거부
    rejected_guards = [g for g in guard_results if g.action == "REJECT"]
    if rejected_guards:
        return "rejected"

    # 갭 후 첫 데이터
    if is_after_gap:
        return "gap"

    # Guard 경고
    degraded_guards = [g for g in guard_results if g.action == "ACCEPT_DEGRADED"]
    if degraded_guards:
        return "degraded"

    # 모두 정상
    return "normal"
```

---

## 6. 검증 실패 처리

### 6.1 로깅 전략

**검증 실패 로그 포맷**:
```json
{
  "timestamp": "2026-01-20T09:31:05.123Z",
  "level": "WARNING",
  "logger": "observer.validation",
  "event_type": "validation_failure",
  "symbol": "005930",
  "validation_errors": [
    "Missing required field: meta.captured_at",
    "Invalid type for instruments[0].volume: expected int, got str"
  ],
  "raw_data_sample": "{\"meta\": {...}}",
  "action": "rejected"
}
```

**Guard 경고 로그 포맷**:
```json
{
  "timestamp": "2026-01-20T09:31:05.123Z",
  "level": "INFO",
  "logger": "observer.guard",
  "event_type": "guard_warning",
  "symbol": "005930",
  "guard_name": "price_spike",
  "reason": "Large price change: 32.5% (possible limit up/down)",
  "quality_flag": "degraded",
  "action": "accept_degraded"
}
```

### 6.2 메트릭 수집

**검증 메트릭**:
- `validation_pass_rate`: 검증 통과율 (%)
- `validation_fail_count`: 검증 실패 건수
- `guard_reject_count`: Guard 거부 건수
- `guard_degrade_count`: Guard 경고 건수
- `quality_flag_distribution`: Flag별 분포 (normal/degraded/gap/rejected)

**목표**:
- Validation Pass Rate: **99.5%+**
- Guard Reject Rate: **< 0.1%**
- Quality Flag "normal": **> 95%**

---

## 7. 테스트 케이스

### 7.1 Schema Validation 테스트

```python
@pytest.mark.parametrize("missing_field,expected_error", [
    ("meta.source", "Missing required field: meta.source"),
    ("instruments[0].price.close", "Missing required field: instruments[0].price.close"),
    ("instruments[0].volume", "Missing required field: instruments[0].volume")
])
def test_schema_validation_missing_fields(missing_field, expected_error):
    """필수 필드 누락 테스트"""
    data = create_valid_market_data()
    remove_nested_field(data, missing_field)

    result = validate_required_fields(data)
    assert not result.passed
    assert expected_error in result.errors
```

### 7.2 Range Validation 테스트

```python
def test_ohlc_relationship_invalid():
    """OHLC 관계 위반 테스트"""
    price_data = {
        "open": 100,
        "high": 90,   # High < Open (invalid)
        "low": 80,
        "close": 95
    }

    result = validate_ohlc_relationship(price_data)
    assert not result.passed
    assert "High" in result.errors[0]
```

### 7.3 Guard Check 테스트

```python
def test_guard_price_spike_extreme():
    """극단적 가격 급등 테스트"""
    result = guard_price_spike(
        symbol="005930",
        current_price=100000,
        prev_close=50000  # 100% 상승
    )

    assert not result.passed
    assert result.action == "REJECT"
    assert result.quality_flag == "rejected"
```

---

## 8. 참고 자료

- **Parent Document**: data_pipeline_architecture_observer_v1.0.md
- **Related**: obs_architecture.md (Section 2.6 Observer Core)

---

## 9. 변경 이력

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-20 | Initial data validation rules specification (C-002 해결용) |

---

**문서 상태**: Draft - C-002 이슈 해결용
