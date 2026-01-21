# Observer Architecture v2.0

# Meta
- Project Name: 
- File Name: 
- Document ID: 
- Status: Draft
- Created Date: {{CURRENT_DATE}}
- Last Updated: {{CURRENT_DATE}}
- Author: 
- Reviewer: 
- Parent Document: [[observer_architecture_v2.md]]
- Related Reference: [[data_pipeline_architecture_observer_v1.0.md]], [[obs_architecture.md]], [[kis_api_specification_v1.0.md]], [[DB_MIGRATION_INTEGRATION_GUIDE.md]]
- Version: v2.0

---

**목적:** 시장 데이터 관찰 및 아카이빙 시스템  
**상태:** 독립 프로젝트로 승격 완료  
**SSoT:** Observer 시스템의 단일 진실 소스

---

## 1. 시스템 개요

### 1.1 핵심 목표
- **관찰 대상:** KOSPI/KOSDAQ 종목 중 **4000원 이상** 종목만 스냅샷
- **데이터 원천:** KIS API 실시간 시세 데이터
- **출력 형태:** JSONL 아카이브 (config/observer/)
- **처리 방식:** 실시간 스냅샷 → Validation → Guard → Enrichment → Archive

### 1.2 시스템 경계
| 포함 | 제외 |
|------|------|
| 시장 데이터 관찰 및 수집 | 자동매매/전략 실행 |
| 4000원 이상 종목 필터링 | 포트폴리오 관리 |
| JSONL 아카이빙 | 실시간 트레이딩 |
| 데이터 품질 검증 | 리스크 관리 |

---

## 2. 데이터 흐름 아키텍처

### 2.1 전체 파이프라인
```
KIS API (실시간 시세)
    ↓ 종목 필터 (4000원 이상)
Phase15InputBridge
    ↓ ObservationSnapshot 생성
Observer.on_snapshot()
    ↓ Validation
DefaultSnapshotValidator.validate()
    ↓ Guard (가격 필터)
DefaultGuard.decide()
    ↓ PatternRecord 생성
PatternRecord(snapshot=snapshot, ...)
    ↓ Enrichment
DefaultRecordEnricher.enrich()
    ↓ EventBus
EventBus.dispatch(record)
    ↓ JsonlFileSink
JsonlFileSink.publish(record)
    ↓ 파일 저장
config/observer/*.jsonl
```

### 2.2 스냅샷 생성 규칙

#### 필터링 조건
- **최소 가격:** 4000원 이상
- **대상 시장:** KOSPI + KOSDAQ 전체
- **데이터 종류:** 실시간 현재가
- **수집 주기:** 1초 간격 (설정 가능)

#### 스냅샷 구조
```python
ObservationSnapshot(
    context={
        "phase": "observation",
        "ingest": "kis_current_price",
        "source": "kis_api",
        "received_at": "2026-01-20T08:19:00Z",
        "filter_criteria": {
            "min_price": 4000,
            "market": "KOSPI,KOSDAQ"
        }
    },
    observation={
        "symbol": "005930",
        "price": 75000,
        "change": 100,
        "volume": 1000000,
        "raw": {...}  # KIS API 원본 데이터
    },
    meta={
        "schema_version": "v2.0.0",
        "run_id": "obs-20260120-001",
        "captured_at": "2026-01-20T08:19:00Z"
    }
)
```

---

## 3. 핵심 컴포넌트

### 3.1 데이터 소스 (Phase 15)

#### KisCurrentPriceSource
```python
class KisCurrentPriceSource:
    """KIS 실시간 시세 데이터 소스"""
    
    def __init__(self, min_price: int = 4000):
        self._min_price = min_price
        # KIS API 연동 설정
    
    def fetch_market_data(self) -> List[Dict]:
        """전체 종목 시세 수집"""
        # KIS API 호출로 전체 종목 데이터 수집
        pass
    
    def filter_by_price(self, data: List[Dict]) -> List[Dict]:
        """4000원 이상 종목 필터링"""
        return [item for item in data if item.get('price', 0) >= self._min_price]
```

#### Phase15InputBridge
```python
class Phase15InputBridge:
    """KIS 데이터 → ObservationSnapshot 변환"""
    
    def build_snapshot(self, market_data: Dict) -> ObservationSnapshot:
        """개별 종목 데이터를 스냅샷으로 변환"""
        return ObservationSnapshot(
            context=self._build_context(market_data),
            observation=self._build_observation(market_data),
            meta=self._build_meta(market_data)
        )
```

### 3.2 Observer Core

#### Observer
```python
class Observer:
    """메인 오케스트레이터"""
    
    def on_snapshot(self, snapshot: ObservationSnapshot) -> None:
        """스냅샷 처리 메인 진입점"""
        # Validation → Guard → Enrichment → EventBus
        pass
```

#### DefaultGuard (가격 필터)
```python
class DefaultGuard:
    """스냅샷 필터링 규칙"""
    
    def decide(self, snapshot: ObservationSnapshot, validation: ValidationResult) -> GuardDecision:
        """4000원 이상 종목만 통과"""
        price = snapshot.observation.get('price', 0)
        
        if price < 4000:
            return GuardDecision(
                allow=False,
                action="filter",
                reason=f"Price {price} below minimum 4000"
            )
        
        return GuardDecision(allow=True, action="pass", reason="Price filter passed")
```

### 3.3 아카이브 시스템

#### JsonlFileSink
```python
class JsonlFileSink:
    """JSONL 파일 출력"""
    
    def __init__(self, base_dir: Path = Path("config/observer")):
        self._base_dir = base_dir
    
    def publish(self, record: PatternRecord) -> None:
        """PatternRecord를 JSONL로 저장"""
        file_path = self._get_file_path()
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(record.to_json() + '\n')
```

---

## 4. 필터링 전략

### 4.1 1차 필터 (데이터 소스 레벨)
```python
# KIS API 수집 시점 필터링
def fetch_filtered_market_data(self) -> List[Dict]:
    all_data = self.fetch_market_data()
    return [item for item in all_data if item['price'] >= 4000]
```

### 4.2 2차 필터 (Guard 레벨)
```python
# Observer 내부에서 추가 검증
def decide(self, snapshot: ObservationSnapshot) -> GuardDecision:
    price = snapshot.observation.get('price', 0)
    if price < 4000:
        return GuardDecision(allow=False, reason="Price below threshold")
    return GuardDecision(allow=True)
```

### 4.3 필터링 로깅
```python
# 필터링 결과 통계 기록
def log_filtering_stats(self, total: int, filtered: int, passed: int):
    self._log.info(
        "Filtering stats | total=%d | filtered=%d | passed=%d | rate=%.2f%%",
        total, filtered, passed, (passed/total*100) if total > 0 else 0
    )
```

---

## 5. 아카이브 구조

### 5.1 파일 명명 규칙
```
config/observer/
├── current_price/
│   ├── 20260120/
│   │   ├── 08_00.jsonl    # 시간 단위 롤링
│   │   ├── 09_00.jsonl
│   │   └── ...
│   └── 20260121/
└── system/
    ├── observer_stats.jsonl
    └── filtering_stats.jsonl
```

### 5.2 JSONL 레코드 형식
```json
{
  "timestamp": "2026-01-20T08:19:00Z",
  "symbol": "005930",
  "price": 75000,
  "change": 100,
  "volume": 1000000,
  "snapshot_id": "obs-20260120-0819-005930-001",
  "filter_applied": {
    "min_price": 4000,
    "passed": true
  },
  "meta": {
    "schema_version": "v2.0.0",
    "source": "kis_api",
    "ingest_mode": "current_price"
  }
}
```

---

## 6. 운영 설정

### 6.1 환경변수
```bash
# 기본 설정
OBSERVER_MODE=standalone
PYTHONPATH=/app/src:/app

# 필터링 설정
MIN_PRICE_THRESHOLD=4000
TARGET_MARKETS=KOSPI,KOSDAQ
POLL_INTERVAL_SEC=1

# 경로 설정
OBSERVER_DATA_DIR=/app/data/observer
OBSERVER_LOG_DIR=/app/logs

# KIS 연동 (선택적)
KIS_APP_KEY=your_key
KIS_APP_SECRET=your_secret
PHASE15_SOURCE_MODE=kis
```

### 6.2 설정 파일
```json
{
  "observer": {
    "version": "2.0.0",
    "mode": "standalone",
    "filters": {
      "min_price": 4000,
      "markets": ["KOSPI", "KOSDAQ"],
      "enabled": true
    },
    "archive": {
      "base_dir": "/app/data/observer",
      "rolling_policy": "hourly",
      "retention_days": 7
    }
  }
}
```

---

## 7. 모니터링

### 7.1 필터링 지표
- **전체 종목 수:** KOSPI/KOSDAQ 전체
- **필터링된 종목 수:** 4000원 미만 종목
- **통과된 종목 수:** 4000원 이상 종목
- **필터링률:** (필터링된 수 / 전체 수) × 100%

### 7.2 아카이브 지표
- **파일 생성率:** 시간당 파일 생성 수
- **레코드 수:** 파일당 레코드 수
- **파일 크기:** 시간별 파일 크기
- **디스크 사용량:** 전체 아카이브 크기

---

## 8. 배포 구성

### 8.1 Docker 설정
```dockerfile
# 독립 프로젝트로 실행
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ /app/
ENV OBSERVER_MODE=standalone
ENV MIN_PRICE_THRESHOLD=4000

CMD ["python", "-c", "from src.runtime.observation_runner import run_observer; run_observer()"]
```

### 8.2 Docker Compose
```yaml
version: '3.8'
services:
  observer:
    build: .
    environment:
      - OBSERVER_MODE=standalone
      - MIN_PRICE_THRESHOLD=4000
      - TARGET_MARKETS=KOSPI,KOSDAQ
    volumes:
      - ./data/observer:/app/data/observer
      - ./logs:/app/logs
    ports:
      - "8000:8000"
```

---

## 9. 다음 단계

### 9.1 즉시 구현
1. **4000원 필터링 로직** 구현
2. **KIS API 연동** 완료
3. **Phase15 Runner** 엔트리포인트로 변경
4. **환경변수 표준화** 적용

### 9.2 향후 확장
1. **동적 필터링** (가격 기준 변경 가능)
2. **종목 그룹핑** (섹터/시장별 필터링)
3. **실시간 대시보드** (필터링 통계 시각화)
4. **고급 아카이빙** (압축/인덱싱)

---

**SSoT 선언:** 이 문서는 Observer 시스템 v2.0의 단일 진실 소스입니다. 모든 아키텍처, 필터링 규칙, 운영 절차는 이 문서를 기준으로 합니다.

## 참고 웹페이지
**공식 api 홈페이지** : https://apiportal.koreainvestment.com/intro
**공식 api 깃페이지** : https://github.com/koreainvestment/open-trading-api
**공식 api 위키독스** : https://wikidocs.net/book/7847