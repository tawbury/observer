# Phase 03: Archive Runner

**목적:** KIS 연동 기반으로 Archive(로그) 생성까지 안정화  
**상태:** 현재 구현 완료, 로그 생성 미작동 디버깅 필요  
**SSoT:** 아카이브 생성 관련 단일 진실 소스

---

## 1. Runner 개요

### 1.1 입력/처리/출력
| 단계 | 내용 | 실제 구현 상태 |
|------|------|----------------|
| **입력** | ObservationSnapshot (외부 생성) | `on_snapshot()` 메서드 존재 |
| **처리** | Validation → Guard → Enrichment | 전체 파이프라인 구현됨 |
| **출력** | JSONL 파일 (config/observer/) | JsonlFileSink 구현됨 |

### 1.2 핵심 문제
- **증거:** `on_snapshot()` 메서드는 존재하나 호출 트리거/루프 불명확
- **원인:** 외부 시스템 연동 없이 내부 루프만 대기 상태

---

## 2. 이벤트 생성 흐름

### 2.1 정상 흐름
```
외부 시스템 (KIS API 등)
    ↓ 스냅샷 생성
Observer.on_snapshot(snapshot) 호출
    ↓ Validation
DefaultSnapshotValidator.validate()
    ↓ Guard
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

### 2.2 현재 상태 문제점
- **메인 루프:** `while True: time.sleep(0.5)`만 실행
- **스냅샷 호출:** `run_observer()`에서 `observer.start()` 호출 없음
- **외부 트리거:** KIS API 연동 코드가 분석 범위에 없음

---

## 3. 저장 경로/파일 규칙 (SSoT)

### 3.1 경로 결정 로직
```python
# paths.py (line 153-165)
def observer_asset_dir() -> Path:
    path = config_dir() / "observer"
    path.mkdir(parents=True, exist_ok=True)
    return path
```

### 3.2 Standalone 모드 경로
- **환경 변수:** `QTS_OBSERVER_STANDALONE=1`
- **프로젝트 루트:** `paths.py` 위치가 기준
- **실제 경로:** `config/observer/` (data 하위 아님)

### 3.3 파일 명명 규칙
- **기본 파일명:** `observer.jsonl`
- **롤링:** `RotationConfig` 설정 시 시간 기반 분리
- **인코딩:** UTF-8
- **쓰기:** Append-only

### 3.4 볼륨 마운트와 경로 정합성
| 컨테이너 경로 | 호스트 마운트 | 실제 저장 위치 |
|----------------|---------------|----------------|
| `/app/config` | `./config` | `./config/observer/` |
| `/app/data/observer` | `./data` | (현재 미사용) |

---

## 4. 필수 환경변수/설정 우선순위

### 4.1 최소 계약
| 환경변수 | 용도 | 필수 여부 | 우선순위 |
|----------|------|-----------|----------|
| `QTS_OBSERVER_STANDALONE` | Standalone 모드 활성화 | **Yes** | 1 |
| `PYTHONPATH` | 모듈 경로 | Yes | 2 |
| `OBSERVER_DATA_DIR` | 데이터 디렉터리 | No (참조용) | 3 |
| `OBSERVER_LOG_DIR` | 로그 디렉터리 | No (참조용) | 4 |

### 4.2 환경변수 불일치 가능성
- **문서:** `OBSERVER_STANDALONE`으로 기술된 곳 있음
- **배포:** `QTS_OBSERVER_STANDALONE`으로 실제 사용
- **계약:** `QTS_OBSERVER_STANDALONE`을 표준으로 고정

### 4.3 설정 우선순위
1. **환경 변수** (최우선)
2. **설정 파일** (deployment_config.json)
3. **기본값** (코드 내부)

---

## 5. 운영 체크리스트 (로그 미생성 디버깅)

### 5.1 기본 점검
- [ ] `QTS_OBSERVER_STANDALONE=1` 설정 확인
- [ ] `config/observer/` 디렉터리 생성 확인
- [ ] Observer 프로세스 실행 상태 확인
- [ ] 포트 8000 사용 여부 점검 (현재 미구현)

### 5.2 스냅샷 트리거 점검
- [ ] `observer.start()` 호출 여부 확인
- [ ] 외부 KIS API 연동 상태 점검
- [ ] `on_snapshot()` 호출 코드 존재 여부 확인
- [ ] 외부 트리거 루프/이벤트 확인

### 5.3 파일 시스템 점검
- [ ] `config/observer/observer.jsonl` 파일 생성 여부
- [ ] 파일 쓰기 권한 확인
- [ ] 디스크 공간 확인
- [ ] 볼륨 마운트 정상 여부

### 5.4 로그 분석
- [ ] Observer 시작 로그 확인
- [ ] Validation 실패 로그 확인
- [ ] Guard 차단 로그 확인
- [ ] EventBus/Sink 오류 로그 확인

---

## 6. 관측/로그/헬스체크 관점

### 6.1 관측 지표
- **파일 생성:** `config/observer/observer.jsonl` 존재 여부
- **파일 크기:** 시간별 파일 크기 변화
- **라인 수:** JSONL 라인 수 증가 여부

### 6.2 로그 패턴
```bash
# 정상 시작
"Observer started | session_id=..."

# 스냅샷 수신
"Snapshot received | symbol=..."

# Validation 실패
"Validation failed | errors=..."

# Guard 차단
"Guard blocked | reason=..."

# 기록 성공
"Record published | file=..."
```

### 6.3 헬스체크 방법
```bash
# 파일 존재 확인
ls -la config/observer/observer.jsonl

# 실시간 모니터링
tail -f config/observer/observer.jsonl

# Observer 프로세스 확인
ps aux | grep observer.py
```

---

## 7. 디버깅 절차 (로그 미생성 시)

### 7.1 1단계: 기본 환경 점검
```bash
# 환경변수 확인
env | grep OBSERVER

# 디렉터리 권한 확인
ls -la config/
mkdir -p config/observer
```

### 7.2 2단계: Observer 실행 점검
```bash
# Observer 시작 로그 확인
docker logs qts-observer

# start() 호출 확인
grep -n "observer.start" app/observer.py
```

### 7.3 3단계: 외부 연동 점검
```bash
# KIS API 연동 코드 확인
find . -name "*.py" -exec grep -l "on_snapshot" {} \;

# 스냅샷 생성 코드 확인
grep -r "ObservationSnapshot" src/
```

### 7.3 4단계: 파일 시스템 점검
```bash
# 실제 저장 위치 확인
python -c "from paths import observer_asset_dir; print(observer_asset_dir())"

# 쓰기 테스트
echo "test" > config/observer/test.txt
```

---

## 8. 해결을 위한 다음 단계

### 8.1 즉시 조치
1. `run_observer()`에서 `observer.start()` 호출 추가
2. 환경변수 이름 표준화 (`QTS_OBSERVER_STANDALONE`)
3. `config/observer/` 디렉터리 자동 생성 강화

### 8.2 근본 해결
1. KIS API 연동 모듈 구현
2. 스냅샷 생성 주기 설정
3. 헬스체크 엔드포인트 구현 (포트 8000)

### 8.3 모니터링 강화
1. 파일 생성 감시
2. 로그 레벨 조정
3. Prometheus 메트릭 추가

---

**SSoT 선언:** 이 문서는 Observer 아카이브 생성의 단일 진실 소스입니다. 모든 경로, 환경변수, 운영 절차는 이 문서를 기준으로 합니다.