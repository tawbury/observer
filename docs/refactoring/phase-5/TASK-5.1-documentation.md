# TASK-5.1: 모듈 문서화

## 태스크 정보
- **Phase**: 5 - 문서화 및 정리
- **우선순위**: Low
- **의존성**: Phase 1-4 완료
- **상태**: 대기

---

## 목표
주요 모듈에 대한 README 문서를 작성하여 코드베이스의 이해도와 유지보수성을 향상시킵니다.

---

## 문서화 대상

### 핵심 모듈 (우선순위 높음)
1. `src/shared/` - 공유 유틸리티
2. `src/collector/` - 데이터 수집기
3. `src/provider/` - 데이터 제공자
4. `src/observer/` - 핵심 관찰 엔진
5. `src/decision_pipeline/` - 의사결정 파이프라인

### 지원 모듈 (우선순위 중간)
6. `src/backup/` - 백업 관리
7. `src/retention/` - 데이터 보존
8. `src/universe/` - 유니버스 관리
9. `src/trigger/` - 트리거 엔진

---

## 문서 템플릿

### 모듈 README 템플릿

```markdown
# 모듈명

## 개요
[모듈의 목적과 역할을 1-2문장으로 설명]

## 구조
```
모듈명/
├── __init__.py
├── core.py
└── ...
```

## 주요 컴포넌트

### ClassName
[클래스 설명]

```python
from 모듈명 import ClassName

instance = ClassName(config)
result = instance.method()
```

## 설정

### 환경 변수
| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| VAR_NAME | 설명 | default |

### 설정 클래스
```python
@dataclass
class ModuleConfig:
    option: str = "default"
```

## 사용 예시

### 기본 사용법
```python
# 예시 코드
```

### 고급 사용법
```python
# 예시 코드
```

## 의존성
- `다른_모듈`: 용도
- `외부_라이브러리`: 용도

## 관련 문서
- [관련 문서 링크]
```

---

## 구현 계획

### 1. shared 모듈 문서

**파일**: `app/observer/src/shared/README.md`

```markdown
# Shared Utilities

## 개요
Observer 시스템 전반에서 사용되는 공유 유틸리티 모듈입니다.
코드 중복을 방지하고 일관된 동작을 보장합니다.

## 구조
```
shared/
├── __init__.py
├── timezone.py        # 타임존 유틸리티
├── time_helpers.py    # 시간 관련 믹스인
├── trading_hours.py   # 거래시간 유틸리티
└── serialization.py   # 직렬화 유틸리티
```

## 주요 컴포넌트

### timezone.py
타임존 처리를 위한 유틸리티입니다.

```python
from shared.timezone import get_zoneinfo, now_with_tz

# 타임존 객체 생성
tz = get_zoneinfo("Asia/Seoul")

# 현재 시간 (타임존 적용)
current_time = now_with_tz("Asia/Seoul")
```

### time_helpers.py
타임존 인식 클래스를 위한 믹스인입니다.

```python
from shared.time_helpers import TimeAwareMixin

class MyCollector(TimeAwareMixin):
    def __init__(self):
        self._tz_name = "Asia/Seoul"
        self._init_timezone()

    def collect(self):
        now = self._now()  # 믹스인에서 제공
```

### trading_hours.py
거래시간 확인 유틸리티입니다.

```python
from shared.trading_hours import in_trading_hours, KRX_REGULAR_SESSION
from datetime import datetime, time

# 거래시간 확인
if in_trading_hours(datetime.now(), time(9, 0), time(15, 30)):
    print("거래시간입니다")

# 정의된 세션 사용
if KRX_REGULAR_SESSION.contains(datetime.now()):
    print("정규장입니다")
```

### serialization.py
객체 직렬화 유틸리티입니다.

```python
from shared.serialization import safe_to_dict, order_hint_fingerprint

# 객체를 딕셔너리로 변환
data = safe_to_dict(my_object)

# 핑거프린트 생성
fp = order_hint_fingerprint(order, hint)
```

## 사용 가이드

### 새 클래스에 타임존 기능 추가
```python
from shared.time_helpers import TimeAwareMixin

class MyService(TimeAwareMixin):
    def __init__(self, tz_name: str = "Asia/Seoul"):
        self._tz_name = tz_name
        self._init_timezone()

    def do_something(self):
        current = self._now()  # 타임존 인식 현재 시간
        # ...
```

## 의존성
- `zoneinfo` (Python 3.9+) 또는 `backports.zoneinfo`
- `dataclasses`
- `hashlib`
```

### 2. collector 모듈 문서

**파일**: `app/observer/src/collector/README.md`

```markdown
# Data Collectors

## 개요
시장 데이터를 수집하는 컬렉터 모듈입니다.
Track A (주기적 배치)와 Track B (실시간 WebSocket) 두 가지 수집 방식을 제공합니다.

## 구조
```
collector/
├── __init__.py
├── base.py              # BaseCollector 추상 클래스
├── track_a_collector.py # 주기적 배치 수집
└── track_b_collector.py # 실시간 WebSocket 수집
```

## 주요 컴포넌트

### BaseCollector
모든 컬렉터의 기본 클래스입니다.

```python
from collector import BaseCollector, BaseCollectorConfig

class MyCollector(BaseCollector):
    async def collect_once(self):
        # 수집 로직 구현
        return {"data": ...}

    def get_interval(self):
        return 60  # 60초 간격
```

### TrackACollector
주기적으로 시장 데이터를 배치 수집합니다.

```python
from collector import TrackACollector, TrackAConfig

config = TrackAConfig(
    interval_minutes=10,
    tz_name="Asia/Seoul",
)

collector = TrackACollector(
    cfg=config,
    engine=provider_engine,
    universe_manager=universe_manager,
)

await collector.start()
```

### TrackBCollector
실시간 WebSocket을 통해 데이터를 수집합니다.

```python
from collector import TrackBCollector, TrackBConfig

config = TrackBConfig(
    max_slots=41,
    min_dwell_seconds=120,
)

collector = TrackBCollector(
    cfg=config,
    engine=provider_engine,
    trigger_engine=trigger_engine,
    slot_manager=slot_manager,
)

await collector.start()
```

## 설정

### TrackAConfig
| 옵션 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| interval_minutes | int | 10 | 수집 간격 (분) |
| trading_start | time | 09:00 | 거래 시작 시간 |
| trading_end | time | 15:30 | 거래 종료 시간 |
| tz_name | str | Asia/Seoul | 타임존 |

### TrackBConfig
| 옵션 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| max_slots | int | 41 | 최대 WebSocket 슬롯 |
| min_dwell_seconds | int | 120 | 최소 체류 시간 |
| check_interval_seconds | int | 5 | 확인 간격 |

## 의존성
- `shared.time_helpers`: TimeAwareMixin
- `shared.trading_hours`: 거래시간 유틸리티
- `provider`: 데이터 제공자
- `trigger`: 트리거 엔진 (Track B)
- `slot`: 슬롯 관리자 (Track B)
```

### 3. 기타 모듈 문서

각 모듈에 대해 유사한 README.md 파일을 생성합니다:
- `src/provider/README.md`
- `src/observer/README.md`
- `src/decision_pipeline/README.md`
- `src/backup/README.md`
- `src/retention/README.md`

---

## 검증 방법

### 1. 문서 완성도 확인
```bash
# README 파일 존재 확인
find app/observer/src -name "README.md" -type f

# 예상: 최소 5개 이상
```

### 2. 마크다운 문법 검사
```bash
# markdownlint 설치 후
markdownlint app/observer/src/*/README.md
```

### 3. 링크 유효성 검사
```bash
# markdown-link-check 사용
markdown-link-check app/observer/src/*/README.md
```

---

## 완료 조건

- [ ] `src/shared/README.md` 작성됨
- [ ] `src/collector/README.md` 작성됨
- [ ] `src/provider/README.md` 작성됨
- [ ] `src/observer/README.md` 작성됨
- [ ] `src/decision_pipeline/README.md` 작성됨
- [ ] 마크다운 문법 오류 없음
- [ ] 코드 예시가 실제로 동작함

---

## 관련 태스크
- [TASK-5.3](TASK-5.3-migration-guide.md): 마이그레이션 가이드 (문서화 일부)
