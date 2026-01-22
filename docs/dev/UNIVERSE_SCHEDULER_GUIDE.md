# Universe 자동 스크리닝 가이드

## 개요

Observer 시스템은 **UniverseScheduler**를 통해 매일 자동으로 전체 종목을 스크리닝합니다.

**새로운 자동화 방식:**
- ✅ KIS API에서 실시간으로 전체 종목 리스트 자동 조회
- ✅ 신규 상장/상장폐지 자동 반영
- ✅ 수동 파일 관리 불필요
- ✅ API 실패 시 캐시 파일로 자동 Fallback

## 자동 실행 스케줄

- **실행 시간**: 매일 05:00 AM (KST - 한국 시간)
- **실행 내용**: 
  1. **KIS API에서 전체 종목 리스트 자동 조회** (최신 상태)
  2. 각 종목의 전일 종가 조회 (KIS API)
  3. 전일 종가 4,000원 이상 종목만 필터링
  4. 결과를 `config/universe/YYYYMMDD_kr_stocks.json`에 저장
  5. 조회된 종목 리스트를 `config/symbols/kr_all_symbols.txt`에 자동 캐싱

## 설정 방법

### 1. KIS API 인증 정보 설정

Universe Scheduler가 작동하려면 KIS API 키가 필요합니다.

#### 로컬 환경
`.env` 파일 생성 (obs_deploy 디렉토리):
```bash
# .env
KIS_APP_KEY=your_actual_app_key
KIS_APP_SECRET=your_actual_app_secret
KIS_IS_VIRTUAL=false
```

#### VM 배포
SSH로 접속 후:
```bash
cd ~/observer-deploy

# .env 파일 생성
cat > .env << 'EOF'
KIS_APP_KEY=your_actual_app_key
KIS_APP_SECRET=your_actual_app_secret
KIS_IS_VIRTUAL=false

DB_HOST=postgres
DB_USER=postgres
DB_PASSWORD=observer_db_pwd
DB_NAME=observer
DB_PORT=5432
EOF

# 권한 설정 (보안을 위해)
chmod 600 .env
```

### 2. 전체 종목 리스트 관리

**이제 자동으로 관리됩니다!**

#### 자동 조회 우선순위

시스템은 다음 순서로 종목 리스트를 가져옵니다:

1. **KIS API 실시간 조회** (최우선) ✅ 
   - 매일 최신 상장 종목 자동 반영
   - 신규 상장/상장폐지 즉시 업데이트
   
2. **캐시 파일** (`config/symbols/kr_all_symbols.txt`)
   - API 조회 성공 시 자동 생성/업데이트
   - API 장애 시 Fallback으로 사용
   
3. **Built-in Fallback** (최소 20개 대표 종목)
   - 모든 소스 실패 시 안전장치

#### 캐시 파일 갱신

- **자동 갱신**: API 조회 성공 시마다 자동으로 최신 파일로 업데이트
- **수동 확인**: `config/symbols/kr_all_symbols.txt` 파일 확인
- **갱신 시점**: 매일 05:00 스케줄러 실행 시

```bash
# 캐시 파일 확인
cat ~/observer-deploy/config/symbols/kr_all_symbols.txt | wc -l

# 예상: 2,500줄 (KOSPI + KOSDAQ 전체)
```

#### 문제 해결: API 조회 실패 시

API 조회가 실패하더라도 시스템은 계속 작동합니다:
- 이전에 캐시된 파일 사용
- 로그에 경고 메시지 출력
- 유니버스 생성은 정상 진행

**API 조회 실패 원인:**
- KIS API 임시 장애
- Rate Limit 초과
- 네트워크 문제

**복구 방법:**
- 다음날 자동으로 재시도
- 또는 수동으로 `scheduler.run_once()` 실행

### 3. 컨테이너 재시작

설정 변경 후 컨테이너를 재시작해야 적용됩니다:

```bash
cd ~/observer-deploy
docker compose down
docker compose up -d

# 로그 확인
docker compose logs -f observer
```

## 작동 확인

### 1. 로그에서 스케줄러 시작 확인
```bash
docker compose logs observer | grep "Universe Scheduler"
```

예상 출력:
```
observer | KIS credentials found - Universe Scheduler will be enabled
observer | Universe Scheduler configured: daily run at 05:00 KST
observer | Universe Scheduler thread started
observer | Next universe generation at 2026-01-23T05:00:00+09:00 (in 46800s)
```

### 2. 수동 실행 (테스트용)

스케줄러는 매일 05:00에만 실행되지만, 테스트를 위해 수동으로 실행할 수 있습니다:

```bash
# 컨테이너 내부 접속
docker compose exec observer bash

# Python 대화형 모드
python3 << 'PYEOF'
import asyncio
import os
from provider import KISAuth, ProviderEngine
from universe.universe_scheduler import UniverseScheduler

# KIS 인증
app_key = os.environ["KIS_APP_KEY"]
app_secret = os.environ["KIS_APP_SECRET"]
auth = KISAuth(app_key, app_secret, is_virtual=False)
engine = ProviderEngine(auth, is_virtual=False)

# 스케줄러 생성 및 즉시 실행
scheduler = UniverseScheduler(engine)
result = asyncio.run(scheduler.run_once())

print("Universe generation result:")
print(f"  Status: {'Success' if result.get('ok') else 'Failed'}")
print(f"  Snapshot: {result.get('snapshot_path')}")
print(f"  Symbol count: {result.get('count')}")
PYEOF
```

### 3. 생성된 유니버스 파일 확인

```bash
# 최신 유니버스 파일 확인
ls -lh ~/observer-deploy/config/universe/

# 내용 확인
cat ~/observer-deploy/config/universe/$(ls -t ~/observer-deploy/config/universe/ | head -1) | head -30
```

## 스케줄러 설정 변경

`observer.py`에서 스케줄러 설정을 변경할 수 있습니다:

```python
scheduler_config = SchedulerConfig(
    hour=5,              # 실행 시간 (KST)
    minute=0,
    min_price=4000,      # 최소 가격 (원)
    min_count=100,       # 최소 종목 수
    market="kr_stocks",
    anomaly_ratio=0.30   # 이상 탐지 임계값 (30%)
)
```

## 문제 해결

### KIS 인증 오류
```
Universe Scheduler disabled - KIS_APP_KEY/SECRET not found
```
→ `.env` 파일에 KIS_APP_KEY, KIS_APP_SECRET 확인

### 종목 수 부족 오류
```
Universe size too small: 50 < 100
```
→ `kr_all_symbols.txt`에 더 많은 종목 추가 필요

### 스케줄러가 시작되지 않음
```bash
# observer 컨테이너 로그 확인
docker compose logs observer | grep -i "error\|failed\|universe"
```

## 알림 (Alerting)

스케줄러는 다음 상황에서 경고 로그를 생성합니다:

1. **universe_count_below_min**: 생성된 유니버스 종목 수가 최소값(100) 미만
2. **universe_count_anomaly**: 전날 대비 종목 수가 30% 이상 변동
3. **universe_fallback**: API 오류로 전날 유니버스 재사용
4. **universe_fatal**: Fallback도 실패

이 알림들은 로그에서 확인 가능하며, 추후 Prometheus/Alertmanager와 연동할 수 있습니다.

## 다음 단계

1. ✅ KIS API 키 설정 (.env 파일)
2. ✅ **자동 종목 조회 구현 완료** - 더 이상 수동 파일 관리 불필요
3. ⏳ 컨테이너 재배포
4. ⏳ 다음날 05:00에 자동 실행 확인
5. ⏳ 생성된 유니버스 파일 검증
6. ⏳ 캐시 파일 자동 생성 확인 (kr_all_symbols.txt)

## 주요 개선사항

### Before (기존 방식)
- ❌ 수동으로 kr_all_symbols.txt 파일 관리 필요
- ❌ 신규 상장/상장폐지 수동 업데이트 필요
- ❌ 약 2,500개 종목 코드 수동 입력
- ❌ 파일 유지보수 부담

### After (새로운 방식)
- ✅ KIS API에서 자동으로 전체 종목 조회
- ✅ 신규 상장/상장폐지 자동 반영
- ✅ 수동 파일 관리 완전 불필요
- ✅ API 실패 시 캐시 파일 자동 Fallback
- ✅ 캐시 파일 자동 갱신으로 데이터 최신성 유지

---

**Last Updated**: 2026-01-22  
**Version**: 1.0
