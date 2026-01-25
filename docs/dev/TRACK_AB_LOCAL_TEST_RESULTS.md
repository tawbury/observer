# Track A/B 로컬 구동 테스트 결과

**테스트 날짜:** 2026-01-25  
**테스트 시간:** 15:35 KST  
**시스템:** Docker Compose (5 services, all healthy)

---

## 📊 테스트 요약

### 테스트 목표
Track A와 Track B가 원하는 경로에 로그와 아카이브를 올바르게 생성하는지 검증

### 테스트 결과: ⚠️ **부분 성공 (Conditional Pass)**

---

## 🔍 Phase 1: 초기 상태 검증

### ✅ 컨테이너 상태
```
✅ observer                Up 6 minutes (healthy)
✅ observer-postgres       Up 6 minutes (healthy)
✅ observer-prometheus     Up 6 minutes (healthy)
✅ observer-grafana        Up 6 minutes (healthy)
✅ observer-alertmanager   Up 6 minutes (healthy)
```

**결론:** 모든 컨테이너 정상 작동

### ✅ 볼륨 마운트 구조

**컨테이너 내부 경로:**
```
✅ /app/config/observer/       - 존재 (Track A/B 로그 저장소)
✅ /app/data/observer/         - 존재 (런타임 데이터)
✅ /app/logs/                  - 존재
✅ /app/logs/system/           - 존재 (시스템 로그)
```

**호스트 마운트 매핑:**
```
컨테이너 /app/logs           ← 호스트 D:\development\prj_obs\observer\logs (마운트됨)
컨테이너 /app/config/observer ← 호스트 infra/oci_deploy/config/observer (준비됨)
```

**결론:** 경로 구조 정상

---

## 🔍 Phase 2: Track A/B 환경 검증

### 환경 변수 상태

**Track A:**
```
TRACK_A_ENABLED=true              ✅ (활성화됨)
KIS_APP_KEY=                       ❌ (비어있음)
KIS_APP_SECRET=                    ❌ (비어있음)
KIS_IS_VIRTUAL=false              ℹ️  (실제 API 모드)
```

**Track B:**
```
TRACK_B_ENABLED=false             ⚠️  (비활성화)
```

### 중요한 발견사항

#### 1️⃣ **Track A 비활성화 이유**

```
로그: "Track A Collector disabled (TRACK_A_ENABLED=false or KIS credentials missing)"
```

실제 원인:
- ✅ `TRACK_A_ENABLED=true` (설정은 정상)
- ❌ **KIS_APP_KEY와 KIS_APP_SECRET이 비어있음**
- 따라서 **Track A 수집기가 자동으로 비활성화됨**

#### 2️⃣ **Track B 완전 비활성화**

```
TRACK_B_ENABLED=false (환경 변수로 명시적 비활성화)
```

---

## ✅ 로그 파일 생성 확인

### 시스템 로그

```
✅ /app/logs/system/observer.log           - 생성됨 (크기: ~2.5KB)
```

**로그 샘플:**
```
2026-01-25 06:30:24,796 | INFO | ObserverDocker | Observer system fully operational
2026-01-25 06:30:24,796 | INFO | ObserverDocker | Event archive: /app/data/observer
2026-01-25 06:30:24,796 | INFO | ObserverDocker | Logs: /app/logs
2026-01-25 06:30:24,796 | INFO | ObserverDocker | Log file: /app/logs/system/observer.log
2026-01-25 06:30:24,797 | INFO | ObserverDocker | Starting FastAPI server on 0.0.0.0:8000
```

**결론:** 시스템 로깅 정상 작동 ✅

### Track A 로그 (Swing 거래)

```
상태: ❌ 미생성
위치: /app/config/observer/swing/
파일명 예상: YYYYMMDD.jsonl (예: 20260125.jsonl)

원인: KIS 인증 정보 부재로 인한 자동 비활성화
```

### Track B 로그 (Scalp 거래)

```
상태: ❌ 미생성
위치: /app/config/observer/scalp/
파일명 예상: YYYYMMDD.jsonl (예: 20260125.jsonl)

원인: TRACK_B_ENABLED=false (명시적 비활성화)
```

---

## 📋 경로 구조 검증

### 호스트 볼륨 마운트 포인트

```
✅ /app/logs (D:\development\prj_obs\observer\logs)
   - system/ 하위 디렉토리 존재
   - observer.log 파일 생성됨

❓ /app/config/observer (infra/oci_deploy/config/observer/)
   - 디렉토리 생성됨 (비어있음)
   - Track A/B 활성화 시 swing/, scalp/ 하위 디렉토리 자동 생성 예상
```

---

## 🎯 다음 단계 (필수)

### Track A 테스트 활성화

Track A를 테스트하려면 KIS API 인증정보 필요:

**옵션 1: 실제 KIS API 사용**
```bash
# docker-compose.yml 또는 .env에서 설정
export KIS_APP_KEY=<실제 KIS 앱 키>
export KIS_APP_SECRET=<실제 KIS 앱 시크릿>
export KIS_IS_VIRTUAL=false  # 실제 API 사용

docker restart observer
```

**옵션 2: 가상 모드 사용**
```bash
export KIS_IS_VIRTUAL=true   # 모의 데이터 사용
docker restart observer
```

### Track B 테스트 활성화

```bash
export TRACK_B_ENABLED=true
docker restart observer
```

---

## 📊 검증 결과 정리

| 항목 | 상태 | 결론 |
|------|------|------|
| 컨테이너 구동 | ✅ 5/5 healthy | 인프라 정상 |
| 경로 구조 | ✅ 모두 존재 | 마운트 정상 |
| 시스템 로깅 | ✅ 작동 중 | 로그 파일 생성 확인 |
| Track A (Swing) | ❌ KIS 인증정보 부재 | 테스트 불가 (인증정보 필요) |
| Track B (Scalp) | ❌ 비활성화 | 테스트 불가 (TRACK_B_ENABLED=true 필요) |

---

## 💡 결론

### 인프라 상태: ✅ **완전 정상**

1. ✅ 모든 Docker 컨테이너 정상 작동
2. ✅ 볼륨 마운팅 구조 정확
3. ✅ 경로 해석 정확
4. ✅ 시스템 로깅 동작 중

### 로그 생성: ⚠️ **조건부 가능**

- **시스템 로그:** ✅ 정상 생성 중
- **Track A 로그:** ❌ KIS 인증정보 필요
- **Track B 로그:** ❌ 활성화 필요

### 테스트 상태: ✅ **준비 완료**

- 경로 구조: ✅ 검증 완료
- 마운트 구조: ✅ 검증 완료
- **다음 단계:** Track A/B 활성화 후 재테스트 필요

---

## 🔧 추천 다음 작업

1. **KIS API 인증정보 설정**
   - .env 파일 또는 docker-compose.yml에 KIS_APP_KEY, KIS_APP_SECRET 추가
   - 또는 KIS_IS_VIRTUAL=true로 설정하여 모의 모드 테스트

2. **Track A 동작 검증**
   ```bash
   # Observer 재시작 후
   docker logs observer | grep "Track A"
   ls -la /app/config/observer/swing/
   ```

3. **Track B 활성화 및 검증**
   ```bash
   # TRACK_B_ENABLED=true 설정 후
   docker restart observer
   ls -la /app/config/observer/scalp/
   ```

4. **로그 로테이션 검증**
   - Track A: 10분 주기 파일 회전
   - Track B: 1분 주기 파일 회전
   - 예상 파일명: `20260125_093000_swing.jsonl` (시간_분_초 포함)

---

**문서 작성:** 2026-01-25 06:35:00 KST  
**테스트 담당자:** GitHub Copilot  
**상태:** ✅ 인프라 검증 완료 | ⏳ 기능 테스트 대기 중
