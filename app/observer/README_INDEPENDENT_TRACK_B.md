# 독립 Track B 스캐너 구현

## 개요

KIS 공식 API 기반으로 Track A와 독립적인 실시간 스캐닝 시스템을 구현합니다.

### 주요 특징

- **독립성**: Track A와 완전히 독립적인 실시간 스캐닝
- **실시간성**: 이벤트 발생 즉시 스켈프 데이터 수집
- **동적 슬롯 관리**: 우선순위 기반 동적 슬롯 할당
- **KIS 공식 API**: 공식 문서 기반 구현

## 아키텍처

```
IndependentTrackBScanner
├── RealTimeEventScanner
│   ├── VolumeSurgeDetector (거래량 급등 감지)
│   └── VolatilityDetector (변동성 스파이크 감지)
├── DynamicSlotManager (동적 슬롯 관리)
├── ScalpDataCollector (스켈프 데이터 수집)
└── KISWebSocketEnhanced (향상된 WebSocket)
```

## 파일 구조

```
src/
├── collector/
│   ├── independent_track_b_scanner.py      # 독립 스캐너 메인 모듈
│   └── track_b_independent.py             # 독립 Track B 컬렉터
├── provider/kis/
│   ├── kis_websocket_enhanced.py          # 향상된 WebSocket 프로바이더
│   └── kis_auth_enhanced.py                # 향상된 인증 모듈
└── test_independent_track_b.py            # 테스트 스크립트
```

## KIS API 참조

### 공식 문서
- **API 포털**: https://apiportal.koreainvestment.com/intro
- **GitHub**: https://github.com/koreainvestment/open-trading-api
- **WikiDocs**: https://wikidocs.net/book/7847

### 주요 API 기능

#### 1. WebSocket 연결
```python
# 승인키 발급
approval_key = await auth.get_websocket_approval_key()

# WebSocket 연결
websocket = await websockets.connect(
    "ws://ops.koreainvestment.com:21000",
    extra_headers={
        "Authorization": f"Bearer {approval_key}",
        "Content-Type": "application/json"
    }
)
```

#### 2. 종목 구독
```python
# 구독 요청
subscribe_request = {
    "header": {
        "approval_key": approval_key,
        "tr_id": "H0STCNT0"
    },
    "body": {
        "tr_key": "005930"  # 종목코드
    }
}

await websocket.send(json.dumps(subscribe_request))
```

#### 3. 실시간 데이터 수신
```python
# 실시간 가격 데이터
price_data = {
    "symbol": "005930",
    "price": 50000,
    "volume": 100000,
    "timestamp": "2026-01-26T14:30:00+09:00"
}
```

## 이벤트 감지

### 1. 거래량 급등 (Volume Surge)
- **조건**: 1분 평균 거래량 대비 5배 이상
- **우선순위**: 0.9
- **감지 로직**: 60초 윈도우 내 거래량 추이적 분석

### 2. 변동성 스파이크 (Volatility Spike)
- **조건**: 1분 내 가격 변동 5% 이상
- **우선순위**: 0.95
- **감지 로직**: 60초 윈도우 내 가격 추이적 분석

## 동적 슬롯 관리

### 슬롯 할당 규칙
1. **새 슬롯**: 빈 슬롯이 있으면 바로 할당
2. **우선순위 교체**: 가장 낮은 우선순위 슬롯과 교체
3. **동적 해제**: 활성화되지 않은 종목 자동 해제

### 슬롯 제한
- **최대 슬롯**: 41개
- **최소 체류 시간**: 120초
- **재할당 간격**: 30초

## 사용 방법

### 1. 기본 설정
```python
from collector.track_b_independent import TrackBIndependent

# 독립 Track B 생성
track_b = TrackBIndependent(market="kr_stocks", max_slots=41)

# 시작
await track_b.start()
```

### 2. 환경 변수 설정
```bash
export KIS_APP_KEY="your_app_key"
export KIS_APP_SECRET="your_app_secret"
export REAL_APP_KEY="your_real_app_key"
export REAL_APP_SECRET="your_real_app_secret"
```

### 3. 테스트 실행
```bash
cd app/observer
python test_independent_track_b.py
```

## 성능 최적화

### 1. 메모리 관리
- **거래량 히스토리**: 60초 윈도우 (deque)
- **가격 히스토리**: 60초 윈도우 (deque)
- **슬롯 정보**: 메모리에 캐시

### 2. 비동기 처리
- **WebSocket 메시지**: 비동기 루프에서 처리
- **이벤트 감지**: 병렬 처리 지원
- **슬롯 관리**: 비동기 할당/해제

### 3. 에러 핸들링
- **WebSocket 연결**: 자동 재연결
- **API 오류**: 로깅 및 재시도
- **예외 처리**: 전역 예외 핸들러

## 모니터링

### 1. 통계 정보
```python
stats = track_b.get_stats()
print(f"활성 슬롯: {stats['active_slots']}")
print(f"구독 종목: {stats['subscribed_symbols']}")
print(f"Universe 크기: {stats['universe_size']}")
```

### 2. 로그 레벨
- **INFO**: 주요 이벤트 및 상태 변경
- **DEBUG**: 상세한 디버깅 정보
- **ERROR**: 오류 및 예외 상황

## 확장성

### 1. 새로운 이벤트 타입
```python
class PriceMomentumEvent(RealTimeEvent):
    def __init__(self, symbol: str, timestamp: datetime, momentum: float):
        super().__init__(
            symbol=symbol,
            event_type="price_momentum",
            timestamp=timestamp,
            priority_score=0.85,
            details={"momentum": momentum}
        )
```

### 2. 커스텀 감지기
```python
class CustomDetector:
    def detect(self, symbol: str, price: float, volume: int, timestamp: datetime):
        # 커스텀 로직 구현
        pass
```

### 3. 다른 시장 지원
- **해외 주식**: 미국, 일본 등
- **선물/옵션**: 국내/해외 파생상품
- **채권**: 국내 채권

## 문제 해결

### 1. WebSocket 연결 실패
- **원인**: 승인키 만료 또는 네트워크 문제
- **해결**: 자동 토큰 갱신 및 재연결 로직

### 2. 이벤트 미감지
- **원인**: 데이터 부족 또는 임계값 설정
- **해결**: 윈도우 크기 조정 및 임계값 튜닝

### 3. 슬롯 부족
- **원인**: 동시다발 이벤트
- **해결**: 우선순위 기반 교체 로직

## 배포

### 1. Docker 환경
```dockerfile
# Dockerfile에 추가
COPY src/collector/independent_track_b_scanner.py /app/src/collector/
COPY src/provider/kis/kis_websocket_enhanced.py /app/src/provider/kis/
```

### 2. 운영 환경
- **Python**: 3.8+
- **의존성**: websockets, requests
- **환경 변수**: KIS API 키

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 지원

- [KIS Open API 공식 문서](https://apiportal.koreainvestment.com/intro)
- [KIS Open API GitHub](https://github.com/koreainvestment/open-trading-api)
- [KIS WebSocket WikiDocs](https://wikidocs.net/book/7847)
