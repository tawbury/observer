# 복구 파일 활용 전략

**작성**: 2026-01-20
**대상**: api_server.py, main.py 등 backup에서 복구된 파일들
**목표**: 현재 프로젝트에 최적으로 통합

---

## 📊 현재 상태 분석

### 현재 프로젝트의 구조
```
app/obs_deploy/app/
├── observer.py              (진입점, 단순 대기 루프만 있음)
├── paths.py                 (경로 관리)
└── src/observer/
    ├── observer.py          (Core Orchestrator - Phase 4 완성)
    ├── event_bus.py         (EventBus 구현됨)
    ├── snapshot.py
    ├── pattern_record.py
    ├── validation.py
    ├── guard.py
    ├── phase4_enricher.py   (Phase 4 완성)
    ├── performance_metrics.py
    └── [기타 파일들]
```

### Backup 파일의 상태
```
backup/e531842/
├── api_server.py.utf8.py        (FastAPI 서버 - 450줄)
├── main.py.utf8.py              (Docker 엔트리 - 109줄)
├── event_bus.py.utf8.py         (이벤트 버스 - 194줄)
├── logging_config.py.utf8.py    (로깅 설정 - 250줄)
├── log_rotation.py.utf8.py      (로그 로테이션 - 250줄)
└── [기타 지원 파일들]
```

### 핵심 발견사항

✅ **좋은 뉴스**
1. 현재 프로젝트는 **핵심 Observer 로직 완성** (Phase 4 까지 완료)
2. Backup의 api_server.py는 **모니터링 계층** (별도의 관심사)
3. event_bus.py는 **양쪽 모두 구현**되어 있음

❌ **문제점**
1. 현재 `app/obs_deploy/app/observer.py`는 **단순 대기 루프만 함**
2. **모니터링/헬스체크 엔드포인트 없음**
3. **Docker와의 통합 불완전** (FastAPI 없음)
4. **테스트 데이터 손실** (Track A/B)

---

## 🎯 최적 활용 전략

### 전략 1: 계층분리 구조 (추천 ⭐⭐⭐⭐⭐)

```
Observer System Architecture
═══════════════════════════════════════════════

┌─────────────────────────────────┐
│    API Layer (외부 인터페이스)   │ ← api_server.py 활용
│  /health, /ready, /status       │
│  /metrics, /metrics/observer    │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│  Orchestration Layer (현재 상태)  │ ← 현재 observer.py
│  - Snapshot 수신                │
│  - Validation                   │
│  - Guard                        │
│  - PatternRecord 생성           │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│   EventBus Layer (현재 구현)     │ ← event_bus.py
│  - JSONL 저장                   │
│  - 로테이션 관리                 │
└────────────┬────────────────────┘
             │
┌────────────▼────────────────────┐
│  Storage Layer (파일 시스템)     │ ← paths.py
│  - /app/data/observer/          │
│  - /app/logs/                   │
└─────────────────────────────────┘
```

**구현 방식**:
1. api_server.py를 **별도의 모듈**로 추가 (`observer/api_server.py`)
2. main.py의 로직을 **비동기 통합** (FastAPI + Observer)
3. 현재 observer.py는 **그대로 유지** (핵심 로직)
4. 두 서버를 **asyncio.gather()로 동시 실행**

---

### 전략 2: 각 파일별 활용 방안

#### 1️⃣ api_server.py (450줄) - ⭐⭐⭐⭐⭐ 최고 우선순위

**현재 상태**: 없음
**복구 상태**: 완전함 ✅

**활용 방안**:
```
✅ 직접 사용
  - 파일명: observer/api_server.py (숨자리 파일 제거)
  - 위치: app/obs_deploy/app/src/observer/api_server.py

⚙️ 필요한 수정:
  - import 경로 확인 (작은 변경만 필요)
  - 현재 프로젝트의 performance_metrics 연동

🎯 이득:
  - Kubernetes 헬스체크 지원
  - Prometheus 메트릭
  - 전체 시스템 상태 모니터링
```

**구체적 구현**:
```python
# app/obs_deploy/app/src/observer/api_server.py (복구 파일)
# 변경 사항:
# 1. import paths 수정
#    from .deployment_paths import ...
#    →
#    from paths import observer_asset_dir, observer_log_dir
#
# 2. get_metrics() 연동
#    from .performance_metrics import get_metrics
#    (이미 현재 프로젝트에 있음)

# app/obs_deploy/app/observer.py (Docker 엔트리)
async def main():
    # Observer 시작
    observer = Observer(...)

    # FastAPI 서버 시작
    api_task = asyncio.create_task(run_api_server(host="0.0.0.0", port=8000))

    # 둘 다 실행
    await asyncio.gather(observer.run(), api_task)
```

**이득**:
```
현재: 상태 파악 불가능
복구 후:
  - ✅ /health → Kubernetes Liveness Probe
  - ✅ /ready → Kubernetes Readiness Probe
  - ✅ /status → 전체 시스템 상태
  - ✅ /metrics → Prometheus 모니터링
```

---

#### 2️⃣ main.py (109줄) - ⭐⭐⭐⭐⭐ 최고 우선순위

**현재 상태**: 불완전 (단순 대기 루프)
**복구 상태**: Docker + FastAPI 완전 통합 ✅

**활용 방안**:
```
✅ 마이그레이션 대상
  - 현재 observer.py 대체
  - 환경 변수 설정 추가
  - 비동기 통합 완성

🔄 순차:
  1. 현재 observer.py 백업
  2. main.py 복사 → observer.py
  3. import 경로 조정
  4. 테스트
```

**구체적 변경사항**:
```python
# backup/e531842/main.py의 핵심 로직
async def run_observer_with_api():
    configure_environment()
    setup_observer_logging(...)

    event_bus = EventBus([
        JsonlFileSink("observer.jsonl", enable_rotation=True)
    ])

    observer = Observer(
        session_id=f"observer-{uuid4()}",
        mode="DOCKER",
        event_bus=event_bus
    )

    status_tracker = get_status_tracker()

    # Observer + API 동시 실행
    await observer.start()
    api_task = asyncio.create_task(run_api_server(host="0.0.0.0", port=8000))

    await api_task
```

**이득**:
```
현재: 단순 대기만 함
복구 후:
  - ✅ 로깅 자동 설정
  - ✅ EventBus 자동 초기화
  - ✅ API 서버 자동 시작
  - ✅ Docker 환경 완전 지원
```

---

#### 3️⃣ event_bus.py (194줄) - ⭐⭐⭐⭐ 검증 필요

**현재 상태**: 구현됨
**복구 상태**: 마찬가지로 구현됨 ✅

**활용 방안**:
```
🔍 비교 분석
  - 현재: app/obs_deploy/app/src/observer/event_bus.py
  - Backup: backup/e531842/event_bus.py.utf8.py

💡 권장:
  - diff로 비교 후 최신 기능 병합
  - 로테이션 관리 확인
  - JsonlFileSink 기능 검증
```

**검증 명령**:
```bash
diff -u app/obs_deploy/app/src/observer/event_bus.py \
         backup/e531842/event_bus.py.utf8.py | head -100
```

---

#### 4️⃣ logging_config.py + log_rotation.py (500줄) - ⭐⭐⭐⭐ 필요 검증

**현재 상태**: 구현되어 있는지 확인 필요
**복구 상태**: 완전함 ✅

**활용 방안**:
```
✅ 현재에 있는지 확인
  - 있으면: diff로 버전 비교
  - 없으면: 직접 추가 또는 현재 구현 확인

🎯 목표:
  - 시간 기반 로그 로테이션
  - 파일명 형식: observer_YYYYMMDD_HHMM.jsonl
  - 자동 정리
```

---

#### 5️⃣ 테스트 데이터 (Track A/B) - ⭐⭐⭐ 실제 테스트에 활용

**현재 상태**: 없음
**복구 상태**: 완전함 ✅

**활용 방안**:
```
🧪 테스트 시나리오
  1. Track A (31줄): 작은 테스트
     - API 엔드포인트 검증
     - 기본 기능 테스트

  2. Track B (579줄): 대규모 테스트
     - 부하 테스트
     - 성능 측정
     - 로그 로테이션 검증

📊 활용:
  - test/fixtures/track_a_test.jsonl
  - test/fixtures/track_b_test.jsonl
  - 자동 테스트에서 재생
```

---

## 🛠️ 구현 로드맵

### Phase 1: API 서버 추가 (2-3시간)

```
Step 1: 파일 복사 및 정리
├─ cp backup/e531842/api_server.py.utf8.py \
│      app/obs_deploy/app/src/observer/api_server.py
├─ 파일명에서 .utf8 제거
└─ import 경로 검증

Step 2: Import 경로 수정
├─ from .deployment_paths import ...
│  → from paths import observer_asset_dir, observer_log_dir
├─ from .performance_metrics import ...
│  (이미 현재에 있는지 확인)
└─ 기타 상대 import 확인

Step 3: 현재 코드와 병합
├─ get_status_tracker() 함수 위치 확인
├─ performance_metrics 연동
└─ import 경로 최종 조정

Step 4: 테스트
├─ python -m py_compile app/obs_deploy/app/src/observer/api_server.py
├─ 기본 import 테스트
└─ 함수 시그니처 검증
```

**예상 결과**:
```
app/obs_deploy/app/src/observer/api_server.py (450줄)
  - ObserverStatusTracker 클래스
  - 6개 FastAPI 엔드포인트
  - Prometheus 메트릭
```

---

### Phase 2: Docker 엔트리 통합 (1-2시간)

```
Step 1: 현재 observer.py 백업
├─ cp app/obs_deploy/app/observer.py \
│      app/obs_deploy/app/observer_original.py
└─ 기존 로직 보존

Step 2: main.py 로직 통합
├─ backup/e531842/main.py의 핵심 로직 분석
├─ 현재 프로젝트의 Observer 호출 방식 이해
└─ 통합 방안 설계

Step 3: 비동기 통합 구현
├─ Observer 시작
├─ API 서버 시작 (asyncio.create_task)
├─ 둘 다 동시 실행 (asyncio.gather)
└─ 에러 처리

Step 4: 환경 변수 설정
├─ OBSERVER_STANDALONE=1
├─ PYTHONPATH=/app/src:/app
├─ OBSERVER_DATA_DIR=/app/data/observer
└─ OBSERVER_LOG_DIR=/app/logs

Step 5: 테스트
├─ python app/obs_deploy/app/observer.py
├─ API 엔드포인트 확인
└─ 로그 생성 확인
```

**예상 결과**:
```
app/obs_deploy/app/observer.py (개선됨)
  - 로깅 자동 설정
  - EventBus 자동 초기화
  - API 서버 자동 시작
  - Docker 환경 완전 지원
```

---

### Phase 3: 테스트 데이터 통합 (30분)

```
Step 1: 테스트 디렉토리 생성
├─ mkdir -p test/fixtures
└─ mkdir -p test/test_data

Step 2: 테스트 데이터 복사
├─ cp backup/e531842/track_a_test.utf8.jsonl \
│      test/fixtures/track_a_test.jsonl
├─ cp backup/e531842/track_b_test.utf8.jsonl \
│      test/fixtures/track_b_test.jsonl
└─ 파일 정리

Step 3: 테스트 스크립트 작성
├─ test/test_api_integration.py
├─ test/test_track_data.py
└─ test/test_performance.py

Step 4: 테스트 실행
├─ pytest test/test_api_integration.py
├─ pytest test/test_track_data.py
└─ 성능 측정
```

**예상 결과**:
```
test/fixtures/
  ├── track_a_test.jsonl (31줄 - 빠른 테스트)
  ├── track_b_test.jsonl (579줄 - 부하 테스트)
  └── README.md (테스트 가이드)
```

---

### Phase 4: 커밋 및 검증 (30분)

```
Step 1: 변경 사항 정리
├─ git status (변경된 파일 확인)
├─ git diff (변경 내용 확인)
└─ 문제가 없는지 검증

Step 2: 커밋 준비
├─ git add app/obs_deploy/app/src/observer/api_server.py
├─ git add app/obs_deploy/app/observer.py
├─ git add test/fixtures/track_*.jsonl
└─ 기타 필요한 파일들

Step 3: 커밋 메시지 작성
├─ 주제: FastAPI 모니터링 계층 추가 및 Docker 통합 완성
├─ 설명:
│   - api_server.py: 6개 엔드포인트 추가
│   - main.py: 비동기 통합
│   - 테스트 데이터: Track A/B 통합
│   - 모든 파일 UTF-8 변환 완료
└─ Co-Authored-By: Backup e531842

Step 4: 푸시
├─ git push origin observer
└─ 모니터링
```

---

## 📈 예상 효과

### 구현 전 vs 후

```
                구현 전              구현 후
─────────────────────────────────────────────────
관찰 능력      매우 제한적         완전한 모니터링
헬스체크       없음                HTTP 엔드포인트
Kubernetes    지원 불가능         완전 지원
메트릭         없음                Prometheus 형식
Docker        불완전              완전 통합
테스트        수동 테스트만        자동 테스트
─────────────────────────────────────────────────
```

### 추가되는 기능

✅ **API 엔드포인트**
```
GET /health            → Kubernetes Liveness Probe
GET /ready             → Kubernetes Readiness Probe
GET /status            → 전체 시스템 상태
GET /metrics           → Prometheus 메트릭
GET /metrics/observer  → JSON 형식 메트릭
```

✅ **모니터링 가능**
```
- Observer 상태 (실행/중지)
- EventBus 연결 상태
- CPU/메모리/디스크 사용량
- 총 스냅샷 수 / 에러 수
- Uptime 측정
```

✅ **Docker 완전 지원**
```
- HEALTHCHECK 자동 응답
- 환경 변수 자동 설정
- 정상 종료 (graceful shutdown)
- 로그 자동 관리
```

---

## ⚠️ 주의사항

### 호환성 확인 필수

```bash
# 1. Import 경로 검증
grep -n "^from observer\|^from \.observer" backup/e531842/api_server.py.utf8.py

# 2. 의존성 확인
grep -n "^import\|^from" backup/e531842/api_server.py.utf8.py | head -20

# 3. 현재 프로젝트와 비교
diff -u app/obs_deploy/app/src/observer/event_bus.py \
         backup/e531842/event_bus.py.utf8.py | head -50
```

### 가능한 문제점

1. **Import 경로 차이**
   - Backup: `from observer.*` 또는 `from .observer.*`
   - 현재: `from paths import ...`
   - **해결**: 경로 정정 필요

2. **의존성 충돌**
   - fastapi, uvicorn, psutil 확인
   - **해결**: requirements.txt 확인

3. **파일 위치 차이**
   - Backup은 `/app/` 기준
   - 현재는 `app/obs_deploy/app/` 기준
   - **해결**: 환경 변수로 해결됨

---

## 🎯 최종 제안

### 우선순위별 구현

**1순위 (필수)**:
- [ ] api_server.py 복사 및 import 경로 수정
- [ ] main.py 로직 통합 (Docker 엔트리)
- [ ] 테스트 데이터 추가

**2순위 (중요)**:
- [ ] event_bus.py diff 검증
- [ ] logging_config.py 확인

**3순위 (선택)**:
- [ ] 추가 테스트 스크립트 작성
- [ ] CI/CD 파이프라인 업데이트

---

## ✅ 체크리스트

실행 순서:
- [ ] RECOVERY_CODE_SUMMARY.md 읽기
- [ ] api_server.py import 경로 검증
- [ ] 현재 event_bus.py와 diff 확인
- [ ] 파일 복사 및 정리
- [ ] 테스트 실행
- [ ] 커밋 및 푸시

---

**이 전략을 따르면**:
✅ 현재 코드의 핵심 로직 보존
✅ Backup 파일의 장점 활용
✅ 최소 충돌로 최대 기능 추가
✅ Docker & Kubernetes 완전 지원

**준비 되셨나요? 다음 단계를 말씀해주세요!**
