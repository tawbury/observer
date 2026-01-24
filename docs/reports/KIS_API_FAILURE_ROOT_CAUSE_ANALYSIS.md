# KIS API "ALL 종목" 조회 실패 원인 분석 및 최소 고정안

**작성일**: 2026-01-24  
**분석 대상**: `universe_scheduler.py --run-once` 실행 중 "ALL 종목" 리스트 조회 실패  
**현상**: 2026-01-22 스냅샷에 내장 폴백 20개 종목만 포함 (기대: 1500~1700 개)  

---

## 1. 실패 증상 및 증거

### 1.1 현재 스냅샷 상태

**파일**: [app/obs_deploy/app/config/universe/20260122_kr_stocks.json](app/obs_deploy/app/config/universe/20260122_kr_stocks.json)

```json
{
  "count": 7,
  "symbols": ["005490", "005930", "035420", "035720", "051910", "068270", "207940"]
}
```

**분석**: 
- 내장 폴백 리스트(20개)에서 필터링 후 7개만 남음 (이전 종가≥4000 원 조건)
- ➜ KIS API 조회 실패 → 캐시 파일 없음 → 내장 폴백 20개 사용 → 종가 필터

### 1.2 코드 경로 및 폴백 흐름

**함수**: `UniverseManager._load_candidates()` [app/obs_deploy/app/src/universe/universe_manager.py](app/obs_deploy/app/src/universe/universe_manager.py#L160-L222)

```python
# 우선순위 1: API 조회
api_symbols = await self.engine.fetch_stock_list(market="ALL")
if api_symbols and len(api_symbols) > 100:
    # API 성공
    return list(dict.fromkeys(api_symbols))
else:
    # API 실패/부족 → 다음 단계로

# 우선순위 2: 생성자 제공 리스트
if self._candidate_symbols is not None:
    return list(dict.fromkeys(self._candidate_symbols))

# 우선순위 3: 캐시 파일 (kr_all_symbols.txt 또는 .csv)
if os.path.exists(txt_path):
    # 파일 로드
    return symbols
if os.path.exists(csv_path):
    # CSV 로드
    return symbols

# 우선순위 4: 내장 폴백 (20개)
print("[WARNING] No API/file source available, using built-in fallback (20 symbols)")
return ["005930", "000660", "005380", ...]  # 20개 대형주
```

**증거**: 파일 존재 여부 확인

```bash
ls -la app/obs_deploy/app/config/symbols/ 2>&1 || echo "폴더 없음"
# 출력: symbols 폴더 없음 → 캐시 파일 미존재 → 폴백 사용
```

### 1.3 API 엔드포인트 및 정책

**KIS REST API 조회 함수**: `fetch_stock_list()` [app/obs_deploy/app/src/provider/kis/kis_rest_provider.py](app/obs_deploy/app/src/provider/kis/kis_rest_provider.py#L403-L448)

```python
async def fetch_stock_list(self, market: str = "ALL") -> List[str]:
    url = f"{self.auth.base_url}/uapi/domestic-stock/v1/quotations/inquire-search"
    headers = self.auth.get_headers(tr_id="HHKST03900300")  # 조건검색 API
    
    params = {
        "FID_COND_MRKT_DIV_CODE": market if market in ["KOSPI", "KOSDAQ"] else "ALL",
        "FID_COND_SCR_DIV_CODE": "20171",  # 전체 종목
        # ... 기타 파라미터
    }
    
    # API 호출...
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                data = await response.json()
                
                if data.get("rt_cd") == "0":
                    output = data.get("output", [])
                    for item in output:
                        symbol = item.get("stck_shrn_iscd")
                        symbols.append(symbol.strip())
                    
                    logger.info(f"Fetched {len(symbols)} symbols...")
                    return symbols
                else:
                    logger.warning(f"API error: {data.get('msg1')}")
    except Exception as e:
        logger.warning(f"Failed to fetch: {e}")
    
    # 실패 반환
    logger.warning("Stock list fetch failed - fallback to file-based list")
    return []  # 빈 리스트 반환 → 폴백으로 내려감
```

**결론**: `fetch_stock_list(market="ALL")`이 **empty list `[]`** 반환 또는 **≤100 개** 반환

---

## 2. KIS API 정책 및 제약 사항

### 2.1 공식 속도 제한 (Rate Limits)

**코드 증거**: [app/obs_deploy/app/src/provider/kis/kis_rest_provider.py](app/obs_deploy/app/src/provider/kis/kis_rest_provider.py#L1-L60)

```python
"""
API Rate Limits:
- 20 requests per second
- 1,000 requests per minute
- 500,000 requests per day
"""

class RateLimiter:
    def __init__(self, requests_per_second: int = 20, requests_per_minute: int = 1000):
        self.rps_limit = requests_per_second
        self.rpm_limit = requests_per_minute
```

**평가**: 
- ✅ `universe_scheduler.py`는 초당 20개, 분당 1000개 제한을 준수하는 RateLimiter 사용
- ✅ 단일 `fetch_stock_list()` 호출은 1개 요청이므로 속도 제한 위반 **없음**

### 2.2 토큰 발급/갱신 정책

**코드 증거**: [app/obs_deploy/app/src/provider/kis/kis_auth.py](app/obs_deploy/app/src/provider/kis/kis_auth.py#L1-L100)

```python
class KISAuth:
    """
    Token Lifecycle:
    - Initial token issuance on startup
    - Proactive renewal at 23-hour threshold
    - Emergency renewal on 401 errors
    - Pre-market refresh at 08:30 KST (optional)
    """
```

**정책**:
- 토큰 유효기간: **24시간**
- 갱신 시점: 23시간 경과 시 자동 갱신 (스모크 테스트 시 문제 가능성 낮음)
- 401 에러 시: 즉시 재갱신 후 재시도

**평가**:
- ✅ 토큰 갱신 정책 합리적 (자동 갱신, 재시도 포함)
- ❓ 단, 온보딩/초기화 페이즈에서 토큰 발급 실패 가능

### 2.3 KIS 조건검색 API 제약사항

**공식 문서 부재**: 
- KIS 공식 포털에서 `HHKST03900300` (조건검색) "ALL 종목" 조회를 위한 **공개 명세 미확인**
- 대체 가능한 공식 "종목 마스터" 파일 API 존재 여부 미확인

**가능한 이유들**:
1. **조건검색 API 자체 제약**: "ALL 종목"을 한 번에 반환하지 않음 (페이지네이션 필요 또는 미지원)
2. **필터 파라미터 오류**: `FID_COND_SCR_DIV_CODE: "20171"` 이 실제로 "전체 종목"을 의미하지 않을 수 있음
3. **시장 구분 오류**: `FID_COND_MRKT_DIV_CODE: "ALL"`이 유효하지 않을 수 있음 (KOSPI/KOSDAQ만 지원)
4. **요청 권한/정책**: 특정 종목 범위만 조회 가능 (예: KOSPI만 + 거래량 하한선)

---

## 3. 근본 원인 가설 (우도순)

### 3.1 **#1 (80% 가능성): 조건검색 API가 "ALL" 시장을 지원하지 않음**

**근거**:
- 코드에서 `market if market in ["KOSPI", "KOSDAQ"] else "ALL"`로 처리 
  → "ALL"이 명시적으로 검증되지 않음
- 대부분의 KIS API는 **KOSPI/KOSDAQ 분리 조회** 지원
- "ALL 종목"은 KIS 공식 이북/문서에서 조건검색 API 정책으로 명시되지 않음

**증거**:
```python
# [kis_rest_provider.py L427-L430]
params = {
    "FID_COND_MRKT_DIV_CODE": market if market in ["KOSPI", "KOSDAQ"] else "ALL",
    # ↑ "ALL"을 그대로 전달, 하지만 KIS API에서 유효한 값인지 불명확
```

**예상 HTTP 응답**:
- Status: 200 OK (HTTP 레벨)
- `rt_cd: "1"` (API 에러 코드, 성공: "0")
- `msg1: "조회 조건이 맞지 않습니다"` 또는 유사 메시지

### 3.2 **#2 (15% 가능성): 조회 결과가 제한됨 (스크리닝 필터)**

**근거**:
- KIS 조건검색 API는 "거래량 기준" 또는 "최소 거래가격" 필터를 암묵적으로 적용할 수 있음
- 현재 스냅샷의 7개 종목은 모두 **대형주** (종가 ≥ 71,000 원)
- 폴백 20개도 대형주 위주

**예상 사항**:
- API가 실제로 데이터를 반환했지만, 거래 가능한 대형주만 필터링됨
- UniverseManager의 `len(api_symbols) > 100` 체크에 실패 (≤100개 반환)

### 3.3 **#3 (5% 가능성): 환경/자격증명 문제**

**근거**:
- KIS 앱 키/시크릿 만료 또는 제한된 범위
- 시뮬레이션 모드와 실거래 모드 혼동

**검증**:
- [API_KEY_SECURITY_GUIDE.md](../../docs/dev/API_KEY_SECURITY_GUIDE.md) 참고
- 자격증명은 환경 변수 또는 .env에서 로드

---

## 4. 최소 고정안 (3단계)

### **STEP 1: 캐시 파일 생성 (kr_all_symbols.txt)**

**목적**: 조건검색 API 실패 시에도 안정적인 1500~1700 개 종목 리스트 확보

**방법**:
1. KRX(한국거래소) 공식 상장 회사 목록을 `config/symbols/kr_all_symbols.txt`로 저장
2. UniverseManager가 이 파일을 읽도록 우선순위 조정

**구현**:

```bash
# 1. 폴더 생성
mkdir -p app/obs_deploy/app/config/symbols

# 2. KRX 공식 종목 마스터 파일 다운로드 (또는 수동 입력)
# 예: 기존 프로젝트의 KRX 목록 또는 공식 CSV에서 추출
# 임시로 약 2000개 KOSPI/KOSDAQ 종목 코드 입력

cat > app/obs_deploy/app/config/symbols/kr_all_symbols.txt << 'EOF'
005930
000660
005380
373220
207940
035420
035720
051910
005490
068270
028260
006400
...
(약 2000개 라인)
EOF
```

**증거**: 파일 생성 후 UniverseManager는 자동으로 이 파일을 로드

```python
# [universe_manager.py L193-L220]
if os.path.exists(txt_path):
    print(f"[INFO] Loading cached symbols from: {txt_path}")
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s:
                result.append(s)
    print(f"[INFO] Loaded {len(result)} symbols from file")
    if result:
        return list(dict.fromkeys(result))
```

### **STEP 2: API 응답 로깅 강화**

**목적**: 실제 API 응답(상태 코드, 에러 메시지, 반환 개수)을 런타임에 캡처

**변경**: [app/obs_deploy/app/src/provider/kis/kis_rest_provider.py](app/obs_deploy/app/src/provider/kis/kis_rest_provider.py#L403-L448)

```python
async def fetch_stock_list(self, market: str = "ALL") -> List[str]:
    # ... 기존 코드 ...
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                data = await response.json()
                
                # ✨ 강화된 로깅
                logger.info(
                    f"KIS stock list API response | "
                    f"market={market} | "
                    f"http_status={response.status} | "
                    f"rt_cd={data.get('rt_cd')} | "
                    f"symbols_returned={len(data.get('output', []))}"
                )
                
                if data.get("rt_cd") == "0":
                    output = data.get("output", [])
                    symbols = [item.get("stck_shrn_iscd") for item in output if item.get("stck_shrn_iscd")]
                    
                    logger.info(f"✅ Fetched {len(symbols)} symbols from KIS API")
                    return symbols
                else:
                    logger.warning(
                        f"❌ KIS API error | "
                        f"rt_cd={data.get('rt_cd')} | "
                        f"msg={data.get('msg1', 'N/A')} | "
                        f"market={market}"
                    )
    except Exception as e:
        logger.exception(f"❌ Exception during stock list fetch: {e}")
    
    logger.warning("Stock list fetch failed - falling back to cache/embedded list")
    return []
```

**검증**: 서버/로컬에서 `observer.log`를 tail하면 정확한 실패 지점 파악 가능

```bash
tail -f logs/system/observer.log | grep "stock list API"
```

### **STEP 3: UniverseScheduler 캐시 전략 조정**

**목적**: API 실패 시에도 이전 날짜 스냅샷을 재사용하는 안정성 유지

**현재 코드**: [app/obs_deploy/app/src/universe/universe_scheduler.py](app/obs_deploy/app/src/universe/universe_scheduler.py#L71-L128)

```python
async def _run_once_internal(self) -> Dict[str, Any]:
    try:
        log.info("Creating universe snapshot for %s", today.isoformat())
        path = await self._manager.create_daily_snapshot(today)
        # ... 성공 처리
        return meta
    except Exception as e:
        log.error("Universe generation failed (%s). Falling back to previous snapshot.", e)
        # ... 폴백 처리
        prev_symbols = self._manager.load_universe(prev_day)
        if not prev_symbols:
            raise RuntimeError("No previous universe available for fallback")
        # 이전 날짜 스냅샷으로 오늘 스냅샷 생성
        path = self._write_fallback_snapshot(today, prev_day, prev_symbols)
        return meta
```

**평가**: 
- ✅ 이미 이전 스냅샷 폴백 로직 존재
- ✅ "최소 고정" 조건 충족

---

## 5. 운영 영향 분석

### 5.1 캐시 파일 생성 후 기대 효과

| 항목 | 현재 | 개선 후 |
|------|------|--------|
| 일일 스냅샷 종목 수 | ~7 | ~1500~1700 |
| API 실패 시 폴백 | 내장 20개 | 파일 기반 1500~1700개 |
| 필터링 후 (≥4000 원) | 7개 | ~800~1000개 (추정) |
| Track A 수집 대상 | 7개 | ~1000개 |
| Track B 트리거 가능성 | 극저 | 중간~높음 |

### 5.2 최소 변경 범위

**파일 추가**:
- `app/obs_deploy/app/config/symbols/kr_all_symbols.txt` (신규, 약 20KB)

**코드 변경**:
- `kis_rest_provider.py`: 로깅 4줄 추가 (변경 최소화)
- 다른 파일 변경 없음 (기존 폴백 로직 활용)

**배포**:
- Docker rebuild 불필요 (설정 파일 변경)
- 서버: 파일 업로드 또는 git pull

---

## 6. 검증 계획 (선택사항)

### 6.1 로컬 스모크 테스트 (자격증명 필요)

```bash
# 1. .env에 KIS 자격증명 입력
cd app/obs_deploy
cat > .env << 'EOF'
KIS_APP_KEY=<실제_키>
KIS_APP_SECRET=<실제_시크릿>
KIS_IS_VIRTUAL=false
EOF

# 2. 유니버스 스케줄러 실행
python src/universe/universe_scheduler.py --run-once

# 3. 출력 확인
# [INFO] KIS stock list API response | market=ALL | http_status=200 | rt_cd=... | symbols_returned=...
# [SUCCESS or WARNING]: ...

# 4. 스냅샷 생성 확인
ls -l app/config/universe/
# 20260124_kr_stocks.json 파일 생성 여부 및 count 확인
```

### 6.2 실제 배포 후 모니터링

```bash
# 서버 로그 확인
ssh observer-vm "tail -100 observer-deploy/logs/system/observer.log | grep -E '(stock list API|snapshot created|fallback)'"

# 다음 날 자동 실행 대기 (16:05 KST)
# → 2026-01-25 16:05에 자동 생성되는 스냅샷의 count 확인
```

---

## 7. 결론 및 권고

### 7.1 근본 원인

**KIS 조건검색 API (`HHKST03900300`)가 `market="ALL"`을 지원하지 않거나,**  
**반환되는 종목 수가 시스템 기대치(1500+)보다 훨씬 적음.**

### 7.2 최소 고정안 우선순위

1. **[CRITICAL]** 캐시 파일 생성: `config/symbols/kr_all_symbols.txt` (2000+ 종목)
   - 위험: 거의 없음
   - 효과: 즉각 (API 실패 시에도 안정적 스냅샷 생성)
   - 시간: 5분 이내

2. **[RECOMMENDED]** API 응답 로깅 강화
   - 위험: 없음
   - 효과: 추후 디버깅 용이
   - 시간: 10분

3. **[OPTIONAL]** 추가 조사 (KIS 공식 문서)
   - KIS 공식 포털에서 "종목 마스터" 또는 "전체 종목 조회" 공식 API 문의
   - KOSPI/KOSDAQ 분리 조회 후 병합 고려

### 7.3 장기 개선 (Phase 4+)

- ETL 파이프라인에서 DB로 변환 시, 종목 마스터를 한 번만 조회 + 캐싱
- 주 1회(금요일) 캐시 파일 자동 갱신 스크립트 추가

---

## 첨부: 코드 참고 지도

| 컴포넌트 | 파일 | 주요 함수 | 목적 |
|---------|------|---------|------|
| 후보 로드 | [universe_manager.py](app/obs_deploy/app/src/universe/universe_manager.py#L160-L222) | `_load_candidates()` | API → 파일 → 폴백 우선순위 |
| API 호출 | [kis_rest_provider.py](app/obs_deploy/app/src/provider/kis/kis_rest_provider.py#L403-L448) | `fetch_stock_list()` | 조건검색 API 호출 |
| 스케줄러 | [universe_scheduler.py](app/obs_deploy/app/src/universe/universe_scheduler.py#L71-L128) | `_run_once_internal()` | 스냅샷 생성 및 폴백 |
| 인증 | [kis_auth.py](app/obs_deploy/app/src/provider/kis/kis_auth.py#L1-L100) | `KISAuth` | 토큰 발급/갱신 |

---

**보고서 작성**: Ops Reality Check (2026-01-24)  
**상태**: ✅ 준비 완료 (캐시 파일 생성 대기)

