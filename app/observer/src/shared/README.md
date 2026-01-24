# Shared Utilities

이 모듈은 Observer 프로젝트 전반에서 사용되는 공통 유틸리티를 제공합니다.

## 모듈 구성

### timezone.py
타임존 관리를 위한 유틸리티 함수들을 제공합니다.

```python
from shared.timezone import get_zoneinfo, now_with_tz

# KST 타임존 가져오기
kst = get_zoneinfo("Asia/Seoul")

# 특정 타임존으로 현재 시간 가져오기
now_kst = now_with_tz("Asia/Seoul")
```

**주요 함수**:
- `get_zoneinfo(tz_name: str)`: ZoneInfo 객체 반환
- `now_with_tz(tz_name: Optional[str])`: 타임존이 적용된 현재 시간 반환

### time_helpers.py
시간 관련 기능을 제공하는 Mixin 클래스입니다.

```python
from shared.time_helpers import TimeAwareMixin

class MyCollector(TimeAwareMixin):
    def __init__(self, tz_name="Asia/Seoul"):
        self._tz_name = tz_name
        self._init_timezone()
    
    def process(self):
        current_time = self._now()  # 타임존 적용된 현재 시간
```

**주요 기능**:
- `TimeAwareMixin`: 타임존 인식 시간 처리를 위한 Mixin
- `_now()`: 설정된 타임존으로 현재 시간 반환

### trading_hours.py
장중/장외 시간 판별을 위한 유틸리티입니다.

```python
from shared.trading_hours import in_trading_hours, KRX_REGULAR_SESSION

# 현재 시간이 장중인지 확인
is_trading = in_trading_hours(
    datetime.now(),
    KRX_REGULAR_SESSION.start,
    KRX_REGULAR_SESSION.end
)
```

**주요 상수**:
- `KRX_REGULAR_SESSION`: 한국 정규장 시간 (09:00 ~ 15:30)
- `KRX_AFTER_HOURS_SESSION`: 시간외 거래 시간 (15:40 ~ 16:00)

### serialization.py
데이터 직렬화 및 핑거프린트 생성 유틸리티입니다.

```python
from shared.serialization import safe_to_dict, order_hint_fingerprint

# 객체를 딕셔너리로 안전하게 변환
data_dict = safe_to_dict(my_dataclass)

# Order와 Hint에 대한 고유 핑거프린트 생성
fp = order_hint_fingerprint(order_decision, execution_hint)
```

**주요 함수**:
- `safe_to_dict(obj)`: 다양한 타입의 객체를 딕셔너리로 변환
- `order_hint_fingerprint(order, hint)`: 주문과 힌트의 고유 해시 생성

## 사용 원칙

1. **중복 제거**: 동일한 코드가 3개 이상의 파일에서 발견되면 shared로 이동
2. **타입 안정성**: 모든 함수는 타입 힌트를 포함
3. **Null 안전성**: Optional 파라미터는 기본값 제공
4. **문서화**: Docstring으로 사용법과 예외 상황 명시

## 의존성

- Python 3.11+
- zoneinfo (Python 표준 라이브러리)
- dataclasses, json, hashlib (표준 라이브러리)
