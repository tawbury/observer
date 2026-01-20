# KIS (한국투자증권) API 상세 명세서

**Document ID**: SPEC-KIS-API-001
**Version**: 1.0.0
**Date**: 2026-01-20
**Parent Document**: data_pipeline_architecture_observer_v1.0.md
**Status**: Draft

---

## 1. 개요

본 문서는 Stock Trading Observer 시스템에서 사용하는 한국투자증권(KIS) OpenAPI의 상세 명세를 정의합니다.

### 1.1 API 기본 정보

| 항목 | 정보 |
|-----|------|
| **서비스명** | 한국투자증권 OpenAPI |
| **Base URL (운영)** | `https://openapi.koreainvestment.com:9443` |
| **Base URL (모의)** | `https://openapivts.koreainvestment.com:9443` |
| **WebSocket URL (운영)** | `wss://openapi.koreainvestment.com:9443/ws` |
| **WebSocket URL (모의)** | `wss://openapivts.koreainvestment.com:9943/ws` |
| **API 문서** | https://apiportal.koreainvestment.com/ |
| **인증 방식** | OAuth 2.0 (App Key + App Secret) |
| **프로토콜** | HTTPS, WSS |

---

## 2. 인증 (Authentication)

### 2.1 OAuth 2.0 토큰 발급

#### Endpoint
```
POST /oauth2/tokenP
```

#### Request Headers
```http
Content-Type: application/json
```

#### Request Body
```json
{
  "grant_type": "client_credentials",
  "appkey": "{APP_KEY}",
  "appsecret": "{APP_SECRET}"
}
```

#### Response (Success)
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access_token_token_expired": "2026-01-20 18:30:00",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

#### Response (Error)
```json
{
  "error_description": "Invalid client credentials",
  "error_code": "40100"
}
```

### 2.2 토큰 갱신 정책

- **토큰 유효기간**: 24시간 (86400초)
- **갱신 시점**: 토큰 만료 1시간 전 (23시간 경과 시)
- **재시도 정책**:
  - 실패 시 1분 후 재시도
  - 최대 3회 재시도
  - 3회 실패 시 CRITICAL 알림

### 2.3 인증 헤더 (Authenticated Requests)

모든 API 요청에 다음 헤더 필수:

```http
Authorization: Bearer {access_token}
appkey: {APP_KEY}
appsecret: {APP_SECRET}
Content-Type: application/json; charset=utf-8
```

---

## 3. REST API 명세

### 3.1 Rate Limiting

| 구분 | 제한 |
|-----|------|
| **초당 요청 수** | 20 req/sec |
| **분당 요청 수** | 1,000 req/min |
| **일일 요청 수** | 500,000 req/day |
| **동시 연결 수** | 10 connections |

**Rate Limit 초과 시 응답**:
```json
{
  "rt_cd": "1",
  "msg_cd": "EGW00123",
  "msg1": "초당 거래건수를 초과하였습니다."
}
```

**처리 방법**:
- 429 응답 수신 시 exponential backoff (1s → 2s → 5s → 10s)
- Rate limit 여유분 모니터링 (Response Header: `X-Ratelimit-Remaining`)
- 요청 분산 (Track A: 4000 종목 / 10분 = 약 7 req/sec)

### 3.2 주식 현재가 조회 (Track A용)

#### Endpoint
```
GET /uapi/domestic-stock/v1/quotations/inquire-price
```

#### Request Headers
```http
Authorization: Bearer {access_token}
appkey: {APP_KEY}
appsecret: {APP_SECRET}
tr_id: FHKST01010100  # 모의: VHKST01010100
Content-Type: application/json; charset=utf-8
```

#### Query Parameters
```
FID_COND_MRKT_DIV_CODE: J  # 주식
FID_INPUT_ISCD: 005930      # 종목코드 (6자리)
```

#### Response (Success)
```json
{
  "rt_cd": "0",
  "msg_cd": "MCA00000",
  "msg1": "정상처리 되었습니다.",
  "output": {
    "stck_prpr": "71100",        // 현재가
    "prdy_vrss": "100",          // 전일대비
    "prdy_vrss_sign": "2",       // 전일대비부호 (1:상한, 2:상승, 3:보합, 4:하한, 5:하락)
    "prdy_ctrt": "0.14",         // 전일대비율
    "stck_oprc": "71000",        // 시가
    "stck_hgpr": "71200",        // 고가
    "stck_lwpr": "70800",        // 저가
    "acml_vol": "1523400",       // 누적거래량
    "acml_tr_pbmn": "108324567", // 누적거래대금
    "hts_kor_isnm": "삼성전자",    // 종목명
    "stck_prdy_clpr": "71000",   // 전일종가
    "askp1": "71100",            // 매도호가1
    "bidp1": "71000",            // 매수호가1
    "askp_rsqn1": "3100",        // 매도잔량1
    "bidp_rsqn1": "5200"         // 매수잔량1
  }
}
```

#### Response (Error)
```json
{
  "rt_cd": "1",
  "msg_cd": "40720000",
  "msg1": "모의투자 종목코드를 입력하지 않았습니다."
}
```

#### 필드 매핑 (MarketDataContract)

| KIS 필드 | MarketDataContract 필드 | 타입 | 비고 |
|---------|------------------------|------|------|
| `stck_oprc` | `price.open` | float | 시가 |
| `stck_hgpr` | `price.high` | float | 고가 |
| `stck_lwpr` | `price.low` | float | 저가 |
| `stck_prpr` | `price.close` | float | 현재가 (종가) |
| `acml_vol` | `volume` | int | 누적거래량 |
| `bidp1` | `bid_price` | float | 매수호가 |
| `askp1` | `ask_price` | float | 매도호가 |
| `bidp_rsqn1` | `bid_size` | int | 매수잔량 |
| `askp_rsqn1` | `ask_size` | int | 매도잔량 |

### 3.3 주식 일봉 조회 (Universe 생성용)

#### Endpoint
```
GET /uapi/domestic-stock/v1/quotations/inquire-daily-price
```

#### Request Headers
```http
Authorization: Bearer {access_token}
appkey: {APP_KEY}
appsecret: {APP_SECRET}
tr_id: FHKST01010400  # 모의: VHKST01010400
```

#### Query Parameters
```
FID_COND_MRKT_DIV_CODE: J
FID_INPUT_ISCD: 005930
FID_PERIOD_DIV_CODE: D  # D:일봉, W:주봉, M:월봉
FID_ORG_ADJ_PRC: 0      # 0:수정주가, 1:원주가
```

#### Response (Success)
```json
{
  "rt_cd": "0",
  "msg_cd": "MCA00000",
  "output": [
    {
      "stck_bsop_date": "20260120",  // 영업일자
      "stck_oprc": "71000",          // 시가
      "stck_hgpr": "71500",          // 고가
      "stck_lwpr": "70500",          // 저가
      "stck_clpr": "71100",          // 종가
      "acml_vol": "12345678",        // 거래량
      "prdy_vrss_sign": "2",         // 전일대비부호
      "prdy_vrss": "100"             // 전일대비
    }
  ]
}
```

**Universe 필터링 로직**:
1. 전일 영업일 데이터 조회 (`stck_bsop_date`)
2. 전일 종가(`stck_clpr`) ≥ 4000원 종목만 선정
3. 선정된 종목 리스트를 `config/universe/YYYYMMDD_kr_stocks.json`에 저장

---

## 4. WebSocket API 명세 (Track B용)

### 4.1 WebSocket 연결

#### Connection URL
```
wss://openapi.koreainvestment.com:9943/ws
```

#### Connection Headers
```http
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: {random_base64}
Sec-WebSocket-Version: 13
```

#### Approval Key 발급 (사전 필요)

WebSocket 사용 전 Approval Key 발급 필요:

```
POST /oauth2/Approval
```

Request Body:
```json
{
  "grant_type": "client_credentials",
  "appkey": "{APP_KEY}",
  "secretkey": "{APP_SECRET}"
}
```

Response:
```json
{
  "approval_key": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

### 4.2 실시간 체결가 구독 (H0STCNT0)

#### Subscribe Message
```json
{
  "header": {
    "approval_key": "{APPROVAL_KEY}",
    "custtype": "P",           // P:개인, B:법인
    "tr_type": "1",            // 1:등록, 2:해제
    "content-type": "utf-8"
  },
  "body": {
    "input": {
      "tr_id": "H0STCNT0",     // 실시간 체결가
      "tr_key": "005930"        // 종목코드
    }
  }
}
```

#### Unsubscribe Message
```json
{
  "header": {
    "approval_key": "{APPROVAL_KEY}",
    "custtype": "P",
    "tr_type": "2",            // 2:해제
    "content-type": "utf-8"
  },
  "body": {
    "input": {
      "tr_id": "H0STCNT0",
      "tr_key": "005930"
    }
  }
}
```

#### Real-time Data Message (수신)

**메시지 포맷**: 파이프(`|`) 구분 텍스트

```
0|H0STCNT0^005930|093105^71100^71200^70800^100^2^0.14^1523400^108324567^71000^71100^3100^71000^5200
```

**필드 분해**:
```
위치 | 필드명 | 설명
-----|--------|------
0    | 유형   | 0:실시간데이터
1    | TR_ID^종목코드 | H0STCNT0^005930
2    | 데이터 | ^ 구분 필드들
```

**데이터 필드 (^ 구분)**:
```
순서 | 필드명 | 예시값 | 설명
-----|--------|--------|------
0    | 체결시간 | 093105 | HHmmss
1    | 현재가 | 71100 |
2    | 고가 | 71200 |
3    | 저가 | 70800 |
4    | 전일대비 | 100 |
5    | 전일대비부호 | 2 | 1~5
6    | 전일대비율 | 0.14 |
7    | 누적거래량 | 1523400 |
8    | 누적거래대금 | 108324567 |
9    | 시가 | 71000 |
10   | 매도호가1 | 71100 |
11   | 매도잔량1 | 3100 |
12   | 매수호가1 | 71000 |
13   | 매수잔량1 | 5200 |
```

#### 파싱 로직 (Python 예시)

```python
def parse_kis_websocket_message(raw_message: str) -> dict:
    """
    KIS WebSocket 메시지 파싱

    Args:
        raw_message: "0|H0STCNT0^005930|093105^71100^..."

    Returns:
        MarketDataContract 형식의 dict
    """
    parts = raw_message.split('|')

    if parts[0] != '0':
        raise ValueError(f"Unknown message type: {parts[0]}")

    tr_info = parts[1].split('^')
    tr_id = tr_info[0]
    symbol = tr_info[1]

    fields = parts[2].split('^')

    return {
        "meta": {
            "source": "kis",
            "market": "kr_stocks",
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "schema_version": "1.0"
        },
        "instruments": [
            {
                "symbol": symbol,
                "timestamp": f"{datetime.now().strftime('%Y-%m-%d')}T{fields[0][:2]}:{fields[0][2:4]}:{fields[0][4:6]}+09:00",
                "price": {
                    "open": float(fields[9]),
                    "high": float(fields[2]),
                    "low": float(fields[3]),
                    "close": float(fields[1])
                },
                "volume": int(fields[7]),
                "bid_price": float(fields[12]) if len(fields) > 12 else None,
                "ask_price": float(fields[10]) if len(fields) > 10 else None,
                "bid_size": int(fields[13]) if len(fields) > 13 else None,
                "ask_size": int(fields[11]) if len(fields) > 11 else None
            }
        ]
    }
```

### 4.3 WebSocket Rate Limiting

| 구분 | 제한 |
|-----|------|
| **동시 구독 종목 수** | 41개 (실시간 체결가 기준) |
| **초당 메시지 수신** | 약 2Hz × 41 = 82 msg/sec (최대) |
| **재연결 제한** | 1시간에 최대 60회 |

**동시 구독 제한 처리**:
- 41개 슬롯 엄격 관리 (SlotManager)
- 새로운 종목 구독 전 기존 종목 해제(unsubscribe) 필수
- Overflow 종목은 Ledger에 기록

### 4.4 WebSocket 연결 상태 관리

#### 정상 연결 확인 (PINGPONG)

**PING 메시지 (매 30초 전송)**:
```json
{
  "header": {
    "approval_key": "{APPROVAL_KEY}",
    "custtype": "P",
    "tr_type": "3",
    "content-type": "utf-8"
  },
  "body": {
    "input": {
      "tr_id": "PINGPONG",
      "tr_key": ""
    }
  }
}
```

**PONG 응답 (수신)**:
```
0|PINGPONG|
```

**PING 무응답 처리**:
- 10초 이내 PONG 미수신 시 연결 끊김으로 판단
- 즉시 재연결 시도

#### 연결 종료 메시지

정상 종료 시 서버에서 전송:
```json
{
  "header": {
    "tr_id": "DISCONNECT"
  },
  "body": {
    "msg1": "WebSocket connection closed by server"
  }
}
```

#### 재연결 정책 (Backoff)

```python
def calculate_reconnect_backoff(attempt: int) -> float:
    """
    재연결 Backoff 시간 계산

    Args:
        attempt: 재연결 시도 횟수 (1부터 시작)

    Returns:
        대기 시간 (초)
    """
    backoff_schedule = [1, 2, 5, 10, 20, 30, 60]

    if attempt <= len(backoff_schedule):
        return backoff_schedule[attempt - 1]
    else:
        return 60  # 최대 60초
```

**재연결 시 처리**:
1. 기존 WebSocket 연결 완전 종료
2. Backoff 시간만큼 대기
3. 새로운 WebSocket 연결 생성
4. Approval Key 재사용 (24시간 유효)
5. 기존 슬롯 종목들 재구독 (우선순위 순)

---

## 5. 에러 코드 및 처리

### 5.1 REST API 에러 코드

| 코드 | 메시지 | 처리 방법 |
|-----|--------|---------|
| `40100` | Invalid client credentials | APP_KEY/SECRET 확인, 재발급 |
| `40720000` | 종목코드 오류 | 종목코드 검증, 로그 기록 후 스킵 |
| `EGW00123` | 초당 거래건수 초과 | Rate limit backoff 적용 |
| `EGW00201` | 시스템 점검 | 점검 시간 확인, 대기 |
| `50000000` | 서버 내부 오류 | 재시도 3회, 실패 시 알림 |

### 5.2 WebSocket 에러 처리

| 상황 | 감지 방법 | 처리 |
|-----|---------|------|
| 연결 실패 | Connection refused | Backoff 재연결 |
| 인증 실패 | Invalid approval_key | Approval Key 재발급 |
| 구독 실패 | Subscribe error response | 해당 종목 슬롯 해제, 로그 기록 |
| PING 무응답 | 10초 timeout | 강제 재연결 |
| 예상치 못한 연결 끊김 | WebSocket close event | Gap marker 기록, 즉시 재연결 |

### 5.3 에러 로깅 포맷

```json
{
  "timestamp": "2026-01-20T09:31:05.123Z",
  "level": "ERROR",
  "logger": "kis_provider",
  "error_type": "API_ERROR",
  "error_code": "EGW00123",
  "error_message": "초당 거래건수를 초과하였습니다.",
  "context": {
    "endpoint": "/uapi/domestic-stock/v1/quotations/inquire-price",
    "symbol": "005930",
    "attempt": 1,
    "action": "retry_with_backoff"
  }
}
```

---

## 6. 성능 최적화

### 6.1 연결 풀 관리

```python
class KISRestClient:
    """
    KIS REST API 클라이언트 (연결 풀 사용)
    """
    def __init__(self, pool_size: int = 10):
        self.session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=pool_size,
            pool_maxsize=pool_size,
            max_retries=Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504]
            )
        )
        self.session.mount('https://', adapter)
```

### 6.2 요청 분산 전략

**Track A (10분 주기, 4000 종목)**:
- 목표: 10분 = 600초 동안 4000 요청
- 초당 요청: 4000 / 600 = 6.67 req/sec
- Rate Limit (20 req/sec) 여유 있음
- 배치 크기: 100 종목씩 처리, 배치 간 15초 대기

**구현 의사코드**:
```python
async def collect_track_a_batch(symbols: List[str], batch_size: int = 100):
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i+batch_size]

        # 병렬 요청 (asyncio)
        tasks = [fetch_price(symbol) for symbol in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 다음 배치 전 대기 (rate limit 준수)
        await asyncio.sleep(15)
```

### 6.3 WebSocket 메시지 처리 성능

**목표 처리량**: 41 종목 × 2Hz = 82 msg/sec

**최적화 전략**:
- 비동기 I/O (asyncio WebSocket)
- 메시지 파싱 캐싱 (정규표현식 컴파일)
- 버퍼링 기반 JSONL Writer (1000 레코드 또는 60초 단위 flush)

---

## 7. 보안 고려사항

### 7.1 자격 증명 관리

**환경 변수**:
```bash
KIS_APP_KEY=xxxxxxxxxxxxxxxxxxxxxxxxx
KIS_APP_SECRET=yyyyyyyyyyyyyyyyyyyyyyyyy
KIS_APPROVAL_KEY=zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz
KIS_ACCOUNT_NO=12345678-01  # 계좌번호 (필요 시)
```

**보안 규칙**:
- `.env` 파일 Git 제외 (`.gitignore`)
- 프로덕션: Azure Key Vault 사용
- 로그에 자격 증명 노출 금지 (마스킹 처리)

### 7.2 TLS/SSL 검증

```python
import ssl
import certifi

# SSL 인증서 검증 활성화
ssl_context = ssl.create_default_context(cafile=certifi.where())
ssl_context.check_hostname = True
ssl_context.verify_mode = ssl.CERT_REQUIRED
```

---

## 8. 테스트 전략

### 8.1 모의투자 환경

**모의투자 설정**:
- Base URL: `https://openapivts.koreainvestment.com:9443`
- WebSocket: `wss://openapivts.koreainvestment.com:9943/ws`
- TR_ID 차이: `V` prefix (예: VHKST01010100)

### 8.2 단위 테스트 시나리오

1. **토큰 발급 테스트**
   - 정상 발급
   - 잘못된 자격 증명
   - 토큰 만료 처리

2. **REST API 테스트**
   - 현재가 조회 성공
   - 존재하지 않는 종목
   - Rate limit 초과

3. **WebSocket 테스트**
   - 연결 및 구독 성공
   - 41개 슬롯 제한 확인
   - 재연결 동작 검증

### 8.3 통합 테스트

```python
@pytest.mark.integration
async def test_track_b_full_cycle():
    """Track B 전체 사이클 테스트"""
    # 1. WebSocket 연결
    ws_client = KISWebSocketClient()
    await ws_client.connect()

    # 2. 41개 종목 구독
    symbols = ["005930", "000660", ...][:41]
    for symbol in symbols:
        await ws_client.subscribe(symbol)

    # 3. 30초 동안 메시지 수신 (약 60개 예상)
    messages = []
    async with asyncio.timeout(30):
        async for msg in ws_client.stream():
            messages.append(msg)

    # 4. 검증
    assert len(messages) >= 50, "최소 50개 메시지 수신 필요"
    assert all(msg['meta']['source'] == 'kis' for msg in messages)
```

---

## 9. 참고 자료

- **KIS OpenAPI 포털**: https://apiportal.koreainvestment.com/
- **API 가이드 문서**: https://apiportal.koreainvestment.com/intro
- **WebSocket 가이드**: https://apiportal.koreainvestment.com/websocket
- **에러 코드 목록**: https://apiportal.koreainvestment.com/error-codes

---

## 10. 변경 이력

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-20 | Initial KIS API specification |

---

**문서 상태**: Draft - C-001 이슈 해결용
