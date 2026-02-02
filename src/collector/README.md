# Collector Module

실시간 시장 데이터 수집을 담당하는 모듈입니다.

## 현재 구성

```
BaseCollector (추상 클래스)
├── track_a_collector.py   # 분봉 수집
└── track_b_collector.py   # 체결 수집 (Track A 의존성 제거, 부트스트랩형)
```

보조 스크립트
- collect_live_scalp.py: WebSocket 실시간 체결 로그를 바로 파일로 적재하는 경량 CLI

## BaseCollector

모든 Collector의 공통 기능을 제공하는 추상 베이스 클래스입니다.

### 주요 기능
1. 타임존 관리: TimeAwareMixin 상속으로 타임존 인식 시간 처리
2. 장중 판별: `is_in_trading_hours()` 메서드로 장중/장외 판단
3. 에러 핸들링: `on_error` 콜백으로 에러 전파
4. 비동기 수집: `collect_once()` 추상 메서드 구현 필요

## TrackACollector

분봉 단위 시장 데이터를 수집합니다.

### 특징
- KIS API를 통한 분봉 데이터 수집
- 장중 시간대만 수집 (09:00 ~ 15:30)
- PostgreSQL에 저장
- Prometheus 메트릭 노출

## TrackBCollector (현행)

Track A 없이 독립적으로 41개 WebSocket 슬롯을 관리하는 체결 데이터 수집기입니다.

### 특징
- 부트스트랩 심볼 기반 즉시 구독 (Track A 로그 의존성 제거)
- SlotManager로 41개 슬롯 동적 관리 및 오버플로우 기록
- 실시간 2Hz 체결 데이터 수집 및 config/observer/scalp/YYYYMMDD.jsonl 로깅

## 중복 정리

다음 프로토타입/중복 파일을 제거했습니다. Track B는 `track_b_collector.py` 하나로 운용합니다.
- independent_track_b_collector.py
- independent_track_b_scanner.py
- track_b_independent.py
- live_scalp_collector.py

관련 실험용 테스트(`tests/test_independent_track_b.py`, `app/observer/test_independent_track_b.py`)도 제거되었습니다. 독립 실행 검증은 `tests/test_track_b_standalone.py`를 사용하세요.
