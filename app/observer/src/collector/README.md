# Collector Module

실시간 시장 데이터 수집을 담당하는 모듈입니다.

## 아키텍처

```
BaseCollector (추상 클래스)
    ├── TrackACollector (분봉 데이터)
    └── TrackBCollector (체결 데이터)
```

## BaseCollector

모든 Collector의 공통 기능을 제공하는 추상 베이스 클래스입니다.

### 주요 기능

1. **타임존 관리**: TimeAwareMixin 상속으로 타임존 인식 시간 처리
2. **장중 판별**: `is_in_trading_hours()` 메서드로 장중/장외 판단
3. **에러 핸들링**: `on_error` 콜백으로 에러 전파
4. **비동기 수집**: `collect_once()` 추상 메서드 구현 필요

### 사용 예시

```python
from collector.base import BaseCollector, CollectorConfig
from datetime import time

class MyCollector(BaseCollector):
    async def collect_once(self) -> Dict[str, Any]:
        """실제 데이터 수집 로직 구현"""
        if not self.is_in_trading_hours():
            return {"status": "outside_trading_hours"}
        
        # 데이터 수집 로직
        data = await fetch_market_data()
        return {"status": "success", "data": data}

# Collector 초기화
config = CollectorConfig(
    tz_name="Asia/Seoul",
    trading_start=time(9, 0),
    trading_end=time(15, 30)
)

collector = MyCollector(config, on_error=lambda msg: print(f"Error: {msg}"))

# 수집 실행
result = await collector.collect_once()
```

## TrackACollector

분봉 단위 시장 데이터를 수집합니다.

### 특징
- KIS API를 통한 분봉 데이터 수집
- 장중 시간대만 수집 (09:00 ~ 15:30)
- PostgreSQL에 저장
- Prometheus 메트릭 노출

## TrackBCollector

실시간 체결 데이터를 수집합니다.

### 특징
- WebSocket 기반 실시간 수집
- 고빈도 데이터 처리
- 버퍼링 및 배치 저장
- 체결 시간 타임스탬프 정확도 중요

## 설정

환경변수로 Collector 활성화/비활성화:
```bash
TRACK_A_ENABLED=true
TRACK_B_ENABLED=false
```

## 디버깅

로그 레벨 설정:
```python
import logging
logging.getLogger("collector").setLevel(logging.DEBUG)
```
