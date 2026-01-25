# Track A/B 로컬 구동 테스트 계획

**목표:** Track A와 Track B가 예상되는 경로에 로그와 아카이브를 올바르게 생성하는지 검증

**테스트 환경:**
- Docker Compose: 5개 서비스 모두 healthy 상태
- Observer 버전: Standalone 모드 (OBSERVER_STANDALONE=1)
- 시간대: Asia/Seoul (KST)

---

## 📋 경로 설정 정보

### 1️⃣ 컨테이너 환경 변수 (docker-compose.yml)

```yaml
환경 변수:
  - OBSERVER_DATA_DIR=/app/data/observer        # 데이터 저장소
  - OBSERVER_LOG_DIR=/app/logs                   # 로그 루트
  - OBSERVER_SYSTEM_LOG_DIR=/app/logs/system    # 시스템 로그
  - OBSERVER_CONFIG_DIR=/app/config             # 설정/아카이브 루트
  
  - TRACK_A_ENABLED=${TRACK_A_ENABLED:-true}    # Track A 활성화 (기본값: true)
  - TRACK_B_ENABLED=${TRACK_B_ENABLED:-false}   # Track B 활성화 (기본값: false)
```

### 2️⃣ 호스트 볼륨 마운팅

```
컨테이너 내부 → 호스트 경로:
/app/data/observer → ../../observer/data
/app/logs           → ../../observer/logs
/app/config         → ../../observer/config
/app/secrets        → ../../observer/secrets
```

실제 호스트 경로:
- `observer/data/` - 실시간 데이터 디렉토리
- `observer/logs/` - 로그 디렉토리
- `infra/oci_deploy/config/` - 설정/아카이브 루트

### 3️⃣ Track A 경로 (Swing Trading - 10분 주기)

```
Base Directory: /app/config/observer  (호스트: infra/oci_deploy/config/observer/)

Log Path Pattern:
  /app/config/observer/swing/YYYYMMDD.jsonl
  
예시:
  /app/config/observer/swing/20260125.jsonl
  
내용:
  - 종목별 현재가 정보 (FHKST01010100 API)
  - 타임스탬프, 가격(open/high/low/close), 거래량
  - 10분마다 업데이트
```

### 4️⃣ Track B 경로 (Scalp Trading - 1분 주기)

```
Base Directory: /app/config/observer  (호스트: infra/oci_deploy/config/observer/)

Log Path Pattern:
  /app/config/observer/scalp/YYYYMMDD.jsonl
  
예시:
  /app/config/observer/scalp/20260125.jsonl
  
내용:
  - WebSocket 실시간 데이터 (H0STCNT0)
  - 타임스탬프, 가격, 거래량, 세션ID
  - 1분마다 로테이션
```

### 5️⃣ 시스템 로그 경로

```
Gap Detection Log:
  /app/logs/system/gap_YYYYMMDD.jsonl
  
Overflow Log:
  /app/logs/system/overflow_YYYYMMDD.jsonl
  
System Log:
  /app/logs/system/observer.log
```

---

## 🧪 테스트 단계

### Phase 1: 초기 상태 검증 (5분)
**목표:** 디렉토리 구조 및 컨테이너 상태 확인

```bash
# 1. 컨테이너 상태 확인
docker ps -a

# 2. 마운트된 볼륨 확인
docker volume ls

# 3. 컨테이너 내부 경로 구조 확인
docker exec observer bash -c "ls -la /app/config/observer/ 2>/dev/null || echo '디렉토리 생성 대기'"
docker exec observer bash -c "ls -la /app/logs/"

# 4. 호스트 볼륨 확인
ls -R infra/oci_deploy/config/observer/ 2>/dev/null || echo "아직 생성되지 않음"
ls -R observer/logs/
```

**예상 결과:**
- ✅ 모든 컨테이너 healthy
- ✅ observer/logs/system 디렉토리 존재
- ❓ infra/oci_deploy/config/observer/ 아직 생성되지 않을 수 있음 (Track A/B 시작 후 생성)

### Phase 2: Track A 수동 테스트 (10분)
**목표:** Track A가 swing 로그를 생성하는지 확인

```bash
# 1. Observer 애플리케이션 상태 확인
docker logs observer --tail 50

# 2. Track A 실행 여부 확인 (로그에서 "Track A" 검색)
docker logs observer | grep -i "track a"

# 3. 생성된 swing 로그 확인
docker exec observer bash -c "find /app/config -name '*.jsonl' 2>/dev/null"

# 4. Swing 로그 내용 샘플 확인 (첫 3줄)
docker exec observer bash -c "head -3 /app/config/observer/swing/*.jsonl 2>/dev/null || echo '파일 미생성'"
```

**예상 결과:**
```
✅ Track A 로그:
  - /app/config/observer/swing/20260125.jsonl 생성
  - JSON 형식 레코드 (symbol, timestamp, price, volume)
  - 파일 크기 증가 (10분 주기로 업데이트)
```

**검증 포인트:**
- [ ] swing 디렉토리 생성 확인
- [ ] YYYYMMDD.jsonl 파일명 형식 확인
- [ ] JSON 레코드 구조 확인
- [ ] 타임스탬프 형식 (ISO8601) 확인

### Phase 3: Track B 활성화 및 테스트 (15분)
**목표:** Track B를 활성화하고 scalp 로그 생성 확인

```bash
# 1. Track B 활성화 (환경 변수 업데이트)
# docker-compose.yml에서 TRACK_B_ENABLED=true로 변경 필요
# 또는 .env 파일에서 설정

# 2. Observer 컨테이너 재시작
docker restart observer

# 3. 로그에서 Track B 초기화 확인
docker logs observer --tail 30 | grep -i "track b"

# 4. scalp 로그 생성 확인
docker exec observer bash -c "watch -n 2 'ls -lh /app/config/observer/scalp/ 2>/dev/null || echo \"대기 중...\"'"

# 5. Scalp 로그 내용 확인 (첫 3줄)
docker exec observer bash -c "head -3 /app/config/observer/scalp/20260125.jsonl 2>/dev/null"
```

**예상 결과:**
```
✅ Track B 로그:
  - /app/config/observer/scalp/20260125.jsonl 생성
  - 1분 주기로 새로운 파일 생성 (또는 회전)
  - JSON 형식 레코드
```

### Phase 4: 호스트 볼륨 동기화 확인 (10분)
**목표:** 호스트 파일시스템에 파일이 올바르게 마운트되었는지 확인

```bash
# 1. infra/oci_deploy/config/observer/ 확인
ls -R infra/oci_deploy/config/observer/

# 2. 파일 크기 및 수정 시간 확인
ls -lh infra/oci_deploy/config/observer/swing/
ls -lh infra/oci_deploy/config/observer/scalp/

# 3. 파일 내용 샘플 확인
head -5 infra/oci_deploy/config/observer/swing/20260125.jsonl
```

**예상 결과:**
```
✅ 호스트에서 보이는 경로:
  - infra/oci_deploy/config/observer/swing/20260125.jsonl
  - infra/oci_deploy/config/observer/scalp/20260125.jsonl
  - 컨테이너의 파일과 동일한 내용
```

### Phase 5: 로그 회전 검증 (Optional - 30분+)
**목표:** 시간 기반 로그 회전이 올바르게 작동하는지 확인

```bash
# Track A: 10분 회전 확인
# - 10분이 경과하면 새로운 파일명으로 회전

# Track B: 1분 회전 확인
# - 1분이 경과하면 새로운 파일명으로 회전

# 확인 방법:
watch -n 10 'echo "=== Swing ===" && ls -1 infra/oci_deploy/config/observer/swing/ && echo "=== Scalp ===" && ls -1 infra/oci_deploy/config/observer/scalp/'
```

---

## 📊 검증 체크리스트

### Track A (Swing)
- [ ] /app/config/observer/swing/ 디렉토리 생성
- [ ] YYYYMMDD.jsonl 파일 생성
- [ ] JSON 형식의 레코드 포함
- [ ] "symbol" 필드 존재
- [ ] "timestamp" ISO8601 형식
- [ ] "price" 객체 (open/high/low/close)
- [ ] "volume" 숫자형
- [ ] 10분 주기로 레코드 추가 (또는 새 파일)
- [ ] 호스트 infra/oci_deploy/config/observer/swing/에 동일한 파일 보임

### Track B (Scalp)
- [ ] /app/config/observer/scalp/ 디렉토리 생성
- [ ] YYYYMMDD.jsonl 파일 생성
- [ ] JSON 형식의 레코드 포함
- [ ] "symbol" 필드 존재
- [ ] "timestamp" ISO8601 형식
- [ ] "price" 객체 포함
- [ ] "source": "websocket" 표시
- [ ] "session_id" 포함
- [ ] 1분 주기로 회전 (또는 새 파일)
- [ ] 호스트 infra/oci_deploy/config/observer/scalp/에 동일한 파일 보임

### 시스템 로그
- [ ] /app/logs/system/observer.log 생성
- [ ] /app/logs/system/gap_YYYYMMDD.jsonl (생성 여부)
- [ ] /app/logs/system/overflow_YYYYMMDD.jsonl (생성 여부)
- [ ] 정상적인 로그 레벨 (INFO, WARNING, ERROR)
- [ ] 호스트 observer/logs/system/에 동일한 파일 보임

---

## ⚙️ 문제 해결 가이드

| 증상 | 원인 | 해결책 |
|------|------|--------|
| swing/scalp 파일 미생성 | Track A/B 미활성화 | docker-compose.yml에서 TRACK_A/B_ENABLED 확인 |
| 파일이 컨테이너에는 있지만 호스트에 없음 | 볼륨 마운트 실패 | `docker inspect observer` 에서 Mounts 확인 |
| JSON 파일이 비어있음 | 데이터 수집 미진행 | KIS_APP_KEY/SECRET 환경 변수 확인 |
| 타임스탐프가 UTC | 타임존 설정 오류 | Docker 컨테이너의 TZ 환경 변수 확인 |
| 로그 파일이 계속 증가 | 로그 로테이션 미작동 | LogRotationManager 설정 확인 |

---

## 📝 기록

**테스트 시작 시간:** YYYY-MM-DD HH:MM:SS KST

**Phase 별 소요 시간:**
- Phase 1: ___분
- Phase 2: ___분
- Phase 3: ___분
- Phase 4: ___분
- Phase 5: ___분

**최종 검증 결과:** ✅ / ⚠️ / ❌

**발견된 문제:**
1. 
2. 
3. 

**결론:**
