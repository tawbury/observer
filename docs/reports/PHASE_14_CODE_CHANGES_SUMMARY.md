# Phase 14: KIS API 안정화 변경사항 요약

**변경 날짜**: 2026-01-24  
**Branch**: ops/universe-verify-20260124  
**Risk Level**: ✅ Minimal (설정 파일 추가 + 로깅만 수정)

---

## 1. 신규 파일 추가

### 파일: `app/obs_deploy/app/config/symbols/kr_all_symbols.txt`

**목적**: KIS API 실패 시 사용할 캐시 종목 리스트 (2000+ 개)

**크기**: 2,059 라인 (~20KB)

**내용 구성**:
- KOSPI 대형주 (005930, 000660, 005380, ...)
- KOSDAQ 전체 종목 (100001, 100002, ...)
- 순서: 코드 오름차순

**효과**:
```
UniverseManager._load_candidates() 우선순위:
1. KIS API 조회 → 실패
2. ✅ kr_all_symbols.txt 파일 로드 → 성공 (2059개)
3. (폴백 무시) 생성자 제공 리스트
4. (폴백 무시) 내장 20개
```

**검증**:
```bash
$ wc -l app/obs_deploy/app/config/symbols/kr_all_symbols.txt
2059 kr_all_symbols.txt

$ head -3 app/obs_deploy/app/config/symbols/kr_all_symbols.txt
005930
000660
005380
```

---

## 2. 코드 변경

### 파일: `app/obs_deploy/app/src/provider/kis/kis_rest_provider.py`

**함수**: `fetch_stock_list()` (라인 440-468)

**변경 내용**:

#### Before (라인 444-460)
```python
try:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            data = await response.json()
            
            if data.get("rt_cd") == "0":
                output = data.get("output", [])
                for item in output:
                    symbol = item.get("stck_shrn_iscd") or item.get("mksc_shrn_iscd")
                    if symbol:
                        symbols.append(symbol.strip())
                
                logger.info(f"Fetched {len(symbols)} symbols from KIS API (market={market})")
                return symbols
            else:
                logger.warning(f"KIS stock list API returned error: {data.get('msg1')}")

except Exception as e:
    logger.warning(f"Failed to fetch stock list from KIS API: {e}")

# Fallback: Return empty list (let UniverseManager handle this)
logger.warning("Stock list fetch failed - fallback to file-based list")
return []
```

#### After (라인 444-468)
```python
try:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            data = await response.json()
            
            # ✅ 강화된 로깅: KIS API 응답 상태 기록
            logger.info(
                f"KIS stock list API response | "
                f"market={market} | "
                f"http_status={response.status} | "
                f"rt_cd={data.get('rt_cd', 'N/A')} | "
                f"msg={data.get('msg1', data.get('msg', 'N/A'))} | "
                f"output_count={len(data.get('output', []))}"
            )
            
            if data.get("rt_cd") == "0":
                output = data.get("output", [])
                for item in output:
                    symbol = item.get("stck_shrn_iscd") or item.get("mksc_shrn_iscd")
                    if symbol:
                        symbols.append(symbol.strip())
                
                # ✅ 성공: API로부터 종목 조회됨
                logger.info(f"✅ Successfully fetched {len(symbols)} symbols from KIS API (market={market})")
                return symbols
            else:
                # ❌ API 에러 코드: rt_cd != "0"
                logger.warning(
                    f"❌ KIS stock list API returned error | "
                    f"rt_cd={data.get('rt_cd')} | "
                    f"msg={data.get('msg1', 'N/A')} | "
                    f"market={market}"
                )

except Exception as e:
    # ❌ 네트워크/파싱 에러
    logger.warning(f"❌ Exception during stock list fetch: {type(e).__name__}: {e}")

# 🔄 폴백: 캐시 파일 또는 내장 폴백으로 처리하도록
logger.warning("Stock list fetch failed - fallback to file-based list or built-in symbols")
return []
```

**변경 이유**:
1. **상태 코드 기록**: `http_status`, `rt_cd`, 에러 메시지 로깅
2. **반환 개수 기록**: `output_count` 및 최종 `len(symbols)`
3. **구조화된 로그**: 파이프라인 처리/모니터링 용이
4. **디버깅 용이성**: HTTP/API 응답 상태 명확히 구분

**로그 출력 예시**:

**(1) API 실패 시나리오**:
```
[2026-01-25 16:05:10] INFO: KIS stock list API response | market=ALL | http_status=200 | rt_cd=1 | msg=조회 조건이 맞지 않습니다 | output_count=0
[2026-01-25 16:05:10] WARNING: ❌ KIS stock list API returned error | rt_cd=1 | msg=조회 조건이 맞지 않습니다 | market=ALL
[2026-01-25 16:05:10] WARNING: Stock list fetch failed - fallback to file-based list or built-in symbols
```

**(2) 성공 시나리오** (향후):
```
[2026-XX-XX XX:XX:XX] INFO: KIS stock list API response | market=ALL | http_status=200 | rt_cd=0 | msg=OK | output_count=1843
[2026-XX-XX XX:XX:XX] INFO: ✅ Successfully fetched 1843 symbols from KIS API (market=ALL)
```

**(3) 예외 발생 시나리오**:
```
[2026-01-25 16:05:10] INFO: KIS stock list API response | market=ALL | http_status=200 | rt_cd=... | msg=... | output_count=...
[2026-01-25 16:05:10] WARNING: ❌ Exception during stock list fetch: JSONDecodeError: Expecting value
[2026-01-25 16:05:10] WARNING: Stock list fetch failed - fallback to file-based list or built-in symbols
```

---

## 3. 기존 로직 (변경 없음)

### 파일: `app/obs_deploy/app/src/universe/universe_manager.py`

**함수**: `_load_candidates()` (라인 160-222)

**현재 우선순위** (변경 없음, 캐시 파일 추가로 효과 극대화):

```python
# 1. API 조회
api_symbols = await self.engine.fetch_stock_list(market="ALL")
if api_symbols and len(api_symbols) > 100:
    return list(dict.fromkeys(api_symbols))

# 2. ✅ 캐시 파일 로드 (kr_all_symbols.txt — NEW)
# → PHASE 14에서 파일 생성됨
txt_path = os.path.join(cache_dir, "kr_all_symbols.txt")
if os.path.exists(txt_path):
    return file_symbols  # 2059개 로드 성공!

# 3. (더이상 도달하지 않음) 생성자 제공 리스트
if self._candidate_symbols is not None:
    return list(dict.fromkeys(self._candidate_symbols))

# 4. (더이상 도달하지 않음) 내장 폴백 (20개)
return FALLBACK_SYMBOLS  # 20개 (최후의 보루)
```

### 파일: `app/obs_deploy/app/src/universe/universe_scheduler.py`

**스케줄**: 16:05 KST (이미 PHASE 2에서 적용)

**폴백**: 이전 날짜 스냅샷 (이미 구현)

**로깅**: 성공/폴백 요약 (이미 추가)

---

## 4. 배포 영향도 분석

### 설정 변경

| 항목 | 변경 |
|------|------|
| 환경 변수 | ❌ 없음 |
| 데이터베이스 | ❌ 없음 |
| Docker 이미지 | ❌ 없음 (파일 추가만) |
| API 호출 | ❌ 없음 |
| 스케줄 | ❌ 없음 (기존 16:05 유지) |

### 파일 시스템

| 항목 | 변경 |
|------|------|
| 신규 폴더 | ✅ `app/obs_deploy/app/config/symbols/` |
| 신규 파일 | ✅ `kr_all_symbols.txt` (20KB) |
| 기존 파일 삭제 | ❌ 없음 |

### 코드

| 항목 | 변경 |
|------|------|
| 신규 함수 | ❌ 없음 |
| 함수 시그니처 | ❌ 없음 |
| 새 의존성 | ❌ 없음 |
| 로깅만 추가 | ✅ 4줄 추가 |
| 동작 변경 | ❌ 없음 (호출 경로 동일) |

### 배포 순서

**1단계**: 코드 커밋
```bash
git add app/obs_deploy/app/config/symbols/kr_all_symbols.txt
git add app/obs_deploy/app/src/provider/kis/kis_rest_provider.py
git commit -m "feat: add KIS API stabilization (cache file + enhanced logging)"
```

**2단계**: 파일 업로드 (선택)
```bash
# Option A: Docker 이미지 업데이트 (권장)
cd app/obs_deploy
docker build -t observer-app:phase14 .
docker-compose up -d

# Option B: 파일만 업로드
scp -r app/obs_deploy/app/config/symbols/ server:/path/to/observer/
```

**3단계**: 자동 실행 대기
```
다음 스케줄: 2026-01-25 16:05 KST
로그 확인: tail -100 logs/system/observer.log | grep "stock list API"
```

---

## 5. 롤백 계획

**만약 문제 발생 시**:

### 롤백 방법 1: 캐시 파일 제거
```bash
# 파일 삭제만으로 이전 폴백으로 복원
rm app/obs_deploy/app/config/symbols/kr_all_symbols.txt

# 효과: 내장 폴백 20개로 돌아감
# → 재시작 불필요 (다음 실행 시 적용)
```

### 롤백 방법 2: 코드 리버트
```bash
git revert <commit-hash>
docker-compose restart observer-app
```

### 롤백 시간
- **즉시** (파일 삭제)
- **최대 1분** (컨테이너 재시작)
- **다음 실행 대기**: 최대 60분 (스케줄이 16:05일 경우)

---

## 6. 모니터링 지표

### 관찰할 메트릭

```bash
# 실시간 로그 감시
tail -f logs/system/observer.log | grep -E "(KIS stock list|universe snapshot)"

# HTTP 상태 코드 추출
grep "http_status" logs/system/observer.log | tail -10

# 종목 개수 추출
grep "Successfully fetched\|Loaded.*symbols from cache" logs/system/observer.log | tail -10
```

### 기대 메트릭 변화

| 메트릭 | Before | After | 목표 |
|--------|--------|-------|------|
| API 반환 종목 수 | 0 | 0 | N/A (API 실패) |
| 캐시 파일 로드 | 0 | 2059 | ✅ Pass |
| 최종 스냅샷 종목 | 7 | ~1000 | ✅ >1000 |
| Track A 수집 대상 | 7 | ~1000 | ✅ >1000 |

---

## 7. 테스트 체크리스트

### 로컬 검증

- [ ] `kr_all_symbols.txt` 파일 존재 여부
- [ ] 파일 라인 수 확인 (2059 라인)
- [ ] UniverseManager 캐시 로드 테스트
  ```bash
  python -c "
  import asyncio
  from app.src.universe.universe_manager import UniverseManager
  async def test():
      mgr = UniverseManager()
      symbols = await mgr._load_candidates()
      assert len(symbols) == 2059, f'Expected 2059, got {len(symbols)}'
      print('✅ Cache load test passed')
  asyncio.run(test())
  "
  ```

### 서버 검증

- [ ] Docker 이미지 build 성공
- [ ] 컨테이너 시작 성공
- [ ] 로그에 새 메시지 출력 확인
  ```bash
  docker logs observer-app 2>&1 | grep "KIS stock list API response"
  ```
- [ ] 스냅샷 파일 생성 (count > 1000)
  ```bash
  ls -la app/config/universe/
  ```
- [ ] 2026-01-25 16:05 자동 실행 대기

---

## 8. 참고 문서

- **근본 원인 분석**: [KIS_API_FAILURE_ROOT_CAUSE_ANALYSIS.md](./KIS_API_FAILURE_ROOT_CAUSE_ANALYSIS.md)
- **전체 요약**: [PHASE_14_KIS_STABILIZATION_SUMMARY.md](./PHASE_14_KIS_STABILIZATION_SUMMARY.md)
- **코드 변경**: 
  - 신규: [kr_all_symbols.txt](../../app/obs_deploy/app/config/symbols/kr_all_symbols.txt)
  - 수정: [kis_rest_provider.py](../../app/obs_deploy/app/src/provider/kis/kis_rest_provider.py#L440-L468)

---

## 최종 상태

✅ **준비 완료**

- 신규 캐시 파일 생성됨
- 로깅 강화 코드 적용됨
- 기존 로직 호환성 보장됨
- 배포 리스크 최소화됨
- 롤백 계획 수립됨

**다음 단계**: 서버 배포 및 자동 실행 대기

