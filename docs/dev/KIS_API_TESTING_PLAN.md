# KIS API 코드 점검 상세 계획

**목적:** Observer 프로젝트의 KIS API 통합 코드가 공식 문서를 준수하는지 확인  
**검토일:** 2026-01-25  
**상태:** 로컬 구동 테스트 전 점검

---

## 1. 검토 순서 및 체크리스트

### Phase 1: 환경 설정 검증 ✅ 

#### 1.1 환경 변수 확인
```bash
# .env 또는 docker-compose.yml에서 확인
KIS_APP_KEY              # ✅ 구현됨
KIS_APP_SECRET           # ✅ 구현됨
KIS_PAPER_APP_KEY        # ⚠️ 명시 필요 (kis_auth.py 라인 69)
KIS_PAPER_APP_SECRET     # ⚠️ 명시 필요
KIS_BASE_URL             # ✅ 구현됨 (기본값 있음)
KIS_IS_VIRTUAL           # ✅ docker-compose에 있음 (기본값 false)
KIS_HTS_ID               # ❌ 미구현 (WebSocket용)
```

**체크 포인트:**
- [ ] `.env.example` 파일 있는지 확인
- [ ] docker-compose.yml에서 모든 환경변수 정의 확인
- [ ] KIS_HTS_ID 추가 필요 여부 판단

#### 1.2 인증 구성 검증

**kis_auth.py 라인 68-73:**
```python
self.app_key = app_key or os.getenv("KIS_APP_KEY" if not is_virtual else "KIS_PAPER_APP_KEY")
self.app_secret = app_secret or os.getenv("KIS_APP_SECRET" if not is_virtual else "KIS_PAPER_APP_SECRET")
```

**점검:**
- [ ] 모의투자 모드에서 KIS_PAPER_APP_KEY 환경변수 로드 확인
- [ ] 실전투자 모드에서 KIS_APP_KEY 환경변수 로드 확인

---

### Phase 2: REST API 레이트 제한 검증

#### 2.1 RateLimiter 클래스 (kis_rest_provider.py 라인 44-80)

**현재 설정:**
```python
requests_per_second: int = 15      # 공식 제한: 20
requests_per_minute: int = 900     # 공식 제한: 1000
```

**점검 사항:**
- [ ] 15 req/sec = 20 req/sec의 75% (안전)
- [ ] 900 req/min = 1000 req/min의 90% (안전)
- [ ] **일일 제한이 구현되지 않음** ⚠️

**Action Required:**
```python
# 추가 필요
daily_limit = 500000
requests_per_day = 0
last_day_reset = datetime.now(timezone.utc)
```

#### 2.2 API 호출 패턴 검증

**확인할 파일:**
- [ ] kis_rest_provider.py의 `fetch_current_price()` (라인 134-180)
- [ ] kis_rest_provider.py의 `fetch_daily_prices()` (라인 182-240)

**체크리스트:**
- [ ] `await self.rate_limiter.acquire()` 호출 확인
- [ ] 토큰 유효성 확인: `await self.auth.ensure_token()`
- [ ] TR_ID 정확성:
  - [ ] FHKST01010100 (현재가 조회) ✅
  - [ ] FHKST01010400 (일일 히스토리) ✅

---

### Phase 3: WebSocket 연결 검증

#### 3.1 엔드포인트 확인 (kis_websocket_provider.py 라인 79-82)

**⚠️ CRITICAL: 엔드포인트 검증 필요**

```python
# 현재 코드에서:
WEBSOCKET_URL = "wss://openapi.koreainvestment.com:9443/websocket"

# 공식 GitHub 샘플에서 언급한 엔드포인트:
# Real: ws://ops.koreainvestment.com:21000
# Virtual: ws://ops.koreainvestment.com:31000
```

**Action:**
- [ ] 공식 GitHub 샘플 코드 재확인
- [ ] ops.koreainvestment.com 엔드포인트 검증
- [ ] openapi.koreainvestment.com 엔드포인트와 차이 확인

#### 3.2 메시지 코드 검증

**확인:**
```python
MSG_SUBSCRIBE = "H0STCNT0"      # 실시간 실행 데이터 ✅
MSG_UNSUBSCRIBE = "H0STCNT9"    # 구독 취소 ✅
MSG_LOGIN = "CSPAT00600001"     # 로그인 ✅
```

- [ ] 공식 문서와 일치 확인
- [ ] 최대 구독 수: 41개 ✅

#### 3.3 HTS ID 처리

**현재 상태:** 미구현  
**필요성:** WebSocket 구독 시 필요 (공식 github 참고)

**Action:**
```python
# kis_websocket_provider.py에 추가 필요
def __init__(self, auth: KISAuth, hts_id: str = None, is_virtual: bool = False):
    self.hts_id = hts_id or os.getenv("KIS_HTS_ID")
    if not self.hts_id:
        logger.warning("HTS_ID not provided, some features may not work")
```

---

### Phase 4: 에러 처리 검증

#### 4.1 HTTP 에러 코드 매핑

**현재 구현 (kis_rest_provider.py):**
```python
# 점검할 부분
if data.get("rt_cd") != "0":
    error_msg = data.get("msg1", "Unknown error")
```

**공식 에러 코드 참고:**
- https://apiportal.koreainvestment.com/faq-error-code
- [ ] 주요 에러 코드 매핑 추가

**필요한 처리:**
```python
# 429: Rate Limit Exceeded
if response.status == 429:
    # 지수 백오프 재시도

# 401: Unauthorized (토큰 만료)
if response.status == 401:
    # 토큰 자동 갱신 후 재시도

# 503: Service Unavailable
if response.status == 503:
    # 재시도 또는 알림
```

---

### Phase 5: 로컬 구동 테스트 계획

#### 5.1 테스트 환경 설정

```bash
# 1단계: 컨테이너 실행 확인
docker ps -a
# ✅ 모든 5개 컨테이너 healthy 확인

# 2단계: 환경 변수 확인
docker exec observer env | grep KIS

# 3단계: 로그 확인
docker logs observer | grep -i "kis\|auth\|token"
```

#### 5.2 인증 테스트

```python
# test/test_kis_auth.py (신규)
import asyncio
from app.observer.src.provider.kis import KISAuth

async def test_token_issuance():
    auth = KISAuth(
        app_key="test_key",
        app_secret="test_secret",
        is_virtual=True  # 모의투자 모드
    )
    token = await auth.ensure_token()
    assert token is not None
    print(f"Token: {token[:20]}...")
```

#### 5.3 REST API 테스트

```python
# test/test_kis_rest.py (신규)
async def test_fetch_current_price():
    auth = KISAuth(..., is_virtual=True)
    provider = KISRestProvider(auth)
    
    # 삼성전자 (005930) 현재가 조회
    result = await provider.fetch_current_price("005930")
    assert result["meta"]["source"] == "kis"
    assert "instruments" in result
    print(f"Current Price: {result}")
```

#### 5.4 WebSocket 테스트

```python
# test/test_kis_websocket.py (신규)
async def test_websocket_subscribe():
    auth = KISAuth(..., is_virtual=True)
    ws = KISWebSocketProvider(auth, hts_id="USER_HTS_ID")
    
    # 삼성전자 실시간 구독
    await ws.subscribe(["005930"])
    
    # 5초 대기 후 데이터 확인
    await asyncio.sleep(5)
    await ws.unsubscribe(["005930"])
```

---

## 2. 공식 GitHub 샘플 코드와 비교

### 2.1 kis_auth.py 비교

**공식 샘플:**
```python
# https://github.com/koreainvestment/open-trading-api/blob/main/examples_user/kis_auth.py

# 토큰 발급
ka.auth(svr="prod")  # 또는 "vps" (모의투자)

# 토큰 파일 위치
config_root = os.path.join(os.path.expanduser("~"), "KIS", "config")
```

**Observer 구현과의 차이:**
- [ ] 토큰 저장 위치 비교
- [ ] 자동 갱신 로직 비교
- [ ] 파일 잠금 메커니즘 확인

### 2.2 API 호출 패턴 비교

**공식 샘플:**
```python
from domestic_stock_functions import inquire_price

result = inquire_price(env_dv="real", fid_cond_mrkt_div_code="J", fid_input_iscd="005930")
```

**Observer 패턴:**
```python
from kis_rest_provider import KISRestProvider

provider = KISRestProvider(auth)
result = await provider.fetch_current_price("005930")
```

**차이점:**
- [ ] 매개변수 이름 표준화
- [ ] 반환 형식 정규화
- [ ] 에러 처리 메커니즘

---

## 3. 보안 체크리스트

### 3.1 토큰 관리
- [ ] 토큰이 평문으로 저장되는지 확인
- [ ] 캐시 파일의 접근 권한 확인 (600)
- [ ] 토큰 만료 시간 검증

### 3.2 환경 변수 보안
- [ ] `.env` 파일이 `.gitignore`에 있는지 확인
- [ ] App Key/Secret이 로그에 기록되지 않는지 확인
- [ ] Docker secrets 사용 권장

### 3.3 API 호출 보안
- [ ] HTTPS/WSS 사용 확인
- [ ] TLS 버전 확인 (1.2 이상)
- [ ] 인증서 검증 활성화

---

## 4. 성능 체크리스트

### 4.1 레이트 제한
- [ ] 토큰 버킷 알고리즘 정확성
- [ ] 동시 요청 처리 능력
- [ ] 버스트 트래픽 대응

### 4.2 재연결
- [ ] 지수 백오프 설정 검증
- [ ] 최대 재시도 횟수 확인
- [ ] 무한 루프 방지 메커니즘

### 4.3 메모리/리소스
- [ ] 웹소켓 메모리 누수 확인
- [ ] 토큰 캐시 크기 제어
- [ ] 연결 풀 관리

---

## 5. 로컬 테스트 명령어

```bash
# 현재 위치: d:\development\prj_obs

# 1. 컨테이너 상태 확인
docker ps --format "table {{.Names}}\t{{.Status}}"

# 2. Observer 로그 확인
docker logs observer -f --tail 100

# 3. 환경 변수 확인
docker exec observer env | grep -i kis

# 4. Python 테스트 실행
docker exec observer python -m pytest test/test_kis_auth.py -v

# 5. API 호출 테스트 (수동)
docker exec observer python -c "
from src.provider.kis import KISAuth
import asyncio

async def test():
    auth = KISAuth(is_virtual=True)
    token = await auth.ensure_token()
    print(f'Token received: {len(token)} chars')

asyncio.run(test())
"
```

---

## 6. 체크리스트 완료 추적

| 항목 | 상태 | 담당 | 예상 완료 |
|-----|------|-----|---------|
| 환경 변수 문서화 | ⏳ | Dev | 2026-01-26 |
| .env.example 작성 | ⏳ | Dev | 2026-01-26 |
| 일일 레이트 제한 추가 | ⏳ | Dev | 2026-01-27 |
| WebSocket 엔드포인트 검증 | ⏳ | QA | 2026-01-27 |
| HTS ID 통합 | ⏳ | Dev | 2026-01-28 |
| 토큰 캐시 암호화 | ⏳ | Security | 2026-01-29 |
| 에러 코드 매핑 | ⏳ | Dev | 2026-01-30 |
| 종합 테스트 | ⏳ | QA | 2026-01-31 |

---

## 7. 참고 자료 링크

### 공식 문서
- [KIS API 포털](https://apiportal.koreainvestment.com/)
- [GitHub 샘플 코드](https://github.com/koreainvestment/open-trading-api)
- [에러 코드 목록](https://apiportal.koreainvestment.com/faq-error-code)
- [AI 도우미 (24/7)](https://chatgpt.com/g/g-68b920ee7afc8191858d3dc05d429571)

### Observer 문서
- [observer_architecture_v2.md](../archi/observer_architecture_v2.md)
- [kis_api_specification_v1.0.md](kis_api_specification_v1.0.md)
- [KIS_API_COMPLIANCE_AUDIT.md](KIS_API_COMPLIANCE_AUDIT.md)

---

**작성일:** 2026-01-25  
**최종 검토:** 대기 중  
**다음 단계:** 로컬 구동 테스트 및 디버깅

