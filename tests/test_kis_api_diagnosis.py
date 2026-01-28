"""
KIS API Stock List Collection - Debug and Improvement Plan

목표: 2894개 전종목을 수집하는 배치 로직 설계
1. 현재 로직: 단일 요청 (ALL) - 실패할 수 있음
2. 개선안: 시장 분할 + 페이징 + 재시도 로직
"""
import asyncio
from typing import List


async def diagnose_current_logic():
    """현재 fetch_stock_list 로직 진단"""
    print("=" * 80)
    print("DIAGNOSIS: Current KIS API Stock List Collection")
    print("=" * 80)
    
    print("""
    📍 현재 구현 위치: app/observer/src/provider/kis/kis_rest_provider.py
    📍 함수: fetch_stock_list(market: str = "ALL") → List[str]
    
    🔍 현재 로직 분석:
    ─────────────────
    
    1️⃣  요청 파라미터:
        - 엔드포인트: /uapi/domestic-stock/v1/quotations/inquire-search
        - TR_ID: HHKST03900300 (조건검색 API)
        - market: "KOSPI", "KOSDAQ", or "ALL"
        - FID_COND_SCR_DIV_CODE: "20171" (전체 종목)
    
    2️⃣  응답 처리:
        - output 배열 순회
        - stck_shrn_iscd (주식 단축 종목코드) 추출
        - mksc_shrn_iscd (종목코드) 폴백
    
    3️⃣  반환:
        - ✅ rt_cd == "0" → 수집된 종목 리스트 반환
        - ❌ rt_cd != "0" → 빈 리스트 반환
    
    ❌ 문제점:
    ─────────
    
    1. **API 응답 제한**
       - KIS API는 한 번의 요청에서 모든 종목을 반환하지 않을 수 있음
       - 페이징 또는 오프셋이 필요할 수 있음
       - 현재 코드는 페이징 미지원
    
    2. **시장 분할 미지원**
       - "ALL" 요청이 실패할 수 있음
       - KOSPI, KOSDAQ 별로 분리 요청 시도 없음
    
    3. **재시도 로직 없음**
       - 일시적 오류 시 즉시 실패
       - 배치 수집 전략 부재
    
    4. **응답 크기 제한**
       - KIS API는 최대 응답 크기 제한이 있을 수 있음
       - 보통 1000-2000개 단위로 제한
       - 현재 2894개를 한 번에 받을 수 없을 가능성 높음
    """)
    
    print()


async def analyze_solution_approach():
    """해결 방안 분석"""
    print("=" * 80)
    print("SOLUTION: Multi-Step Stock Collection Strategy")
    print("=" * 80)
    
    print("""
    🎯 목표: 2894개 전종목 수집 (API 제한 극복)
    
    📋 세 가지 접근법:
    
    [옵션 1] 시장 분할 수집 (권장)
    ────────────────────────────
    1단계: KOSPI 수집
    2단계: KOSDAQ 수집
    3단계: KONEX 수집 (있으면)
    → 시장별로 2000-3000개 종목 수집 가능
    
    장점:
    ✅ API 호출량 충분 (보통 시장당 1회)
    ✅ 응답 크기 관리 가능
    ✅ 개별 시장 실패 감지 가능
    
    단점:
    ❌ 3회 API 호출 필요
    ❌ 구현 복잡도 증가
    
    [옵션 2] 페이징 + 오프셋 (KIS API 지원 여부 확인 필요)
    ──────────────────────────────────────────────
    1. 첫 요청: offset=0, limit=1000
    2. 반복: offset 증가하며 계속 요청
    3. 반환값 < 1000 시 종료
    
    장점:
    ✅ 유연한 응답 크기 처리
    ✅ 여러 번 호출 가능
    
    단점:
    ❌ KIS API가 지원하지 않을 수 있음
    ❌ 호출량 증가
    
    [옵션 3] 하이브리드 (권장)
    ──────────────────────────
    1. 시장별로 분할 수집 (KOSPI, KOSDAQ)
    2. 각 시장에서 페이징 시도 (supported이면)
    3. 3회 이상 요청 시 재시도 (타임아웃 등)
    
    구현 전략:
    ┌─────────────────────────────────────┐
    │ Step 1: Validate API Capability     │
    │ - Check if API supports pagination  │
    │ - Check response size limits        │
    │ - Log actual API responses          │
    └─────────────────────────────────────┘
              ↓
    ┌─────────────────────────────────────┐
    │ Step 2: Implement Market Split      │
    │ - fetch_stock_list("KOSPI")         │
    │ - fetch_stock_list("KOSDAQ")        │
    │ - Combine results                   │
    └─────────────────────────────────────┘
              ↓
    ┌─────────────────────────────────────┐
    │ Step 3: Add Pagination (if needed)  │
    │ - Implement offset-based pagination │
    │ - Batch retry with backoff          │
    └─────────────────────────────────────┘
              ↓
    ┌─────────────────────────────────────┐
    │ Step 4: Cache Results               │
    │ - Save to kr_all_symbols.txt        │
    │ - Add metadata (fetch_date, count)  │
    └─────────────────────────────────────┘
    """)
    
    print()


async def design_improved_fetch_stock_list():
    """개선된 fetch_stock_list 설계"""
    print("=" * 80)
    print("DESIGN: Improved fetch_stock_list()")
    print("=" * 80)
    
    print("""
    📝 개선된 코드 구조:
    
    async def fetch_stock_list(self, market: str = "ALL") -> List[str]:
        '''
        Improved stock list fetching with multiple fallback strategies:
        1. Try market-specific requests (KOSPI, KOSDAQ, KONEX)
        2. Implement pagination if API supports it
        3. Add retry logic with exponential backoff
        4. Cache results for future use
        '''
        
        # Strategy 1: Market-Split Collection
        all_symbols = []
        
        for target_market in ["KOSPI", "KOSDAQ"]:
            symbols = await self._fetch_stock_list_single(
                market=target_market,
                max_retries=3,
                retry_delay=1.0
            )
            all_symbols.extend(symbols)
        
        # Strategy 2: Pagination (if API supports)
        if len(all_symbols) < 2500:  # 예상보다 적음
            symbols = await self._fetch_stock_list_paginated(
                market="ALL",
                page_size=1000,
                max_pages=5
            )
            all_symbols.extend(symbols)
        
        # Deduplicate and return
        return list(dict.fromkeys(all_symbols))
    
    
    async def _fetch_stock_list_single(
        self, 
        market: str,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> List[str]:
        '''Single market fetch with retry logic'''
        for attempt in range(max_retries):
            try:
                symbols = await self._try_fetch_market(market)
                if symbols:
                    logger.info(f"✅ Fetched {len(symbols)} symbols from {market}")
                    return symbols
            except Exception as e:
                logger.warning(
                    f"Attempt {attempt+1}/{max_retries} failed for {market}: {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
        
        logger.warning(f"❌ Failed to fetch {market} after {max_retries} attempts")
        return []
    
    
    async def _fetch_stock_list_paginated(
        self,
        market: str,
        page_size: int = 1000,
        max_pages: int = 5
    ) -> List[str]:
        '''Pagination-based collection (if API supports)'''
        all_symbols = []
        
        for page in range(max_pages):
            offset = page * page_size
            params = {
                ...existing params...,
                "offset": offset,
                "limit": page_size,
            }
            
            symbols = await self._try_fetch_with_params(market, params)
            if not symbols:
                break  # No more data
            
            all_symbols.extend(symbols)
            logger.info(f"Page {page+1}: fetched {len(symbols)} symbols (offset={offset})")
            
            if len(symbols) < page_size:
                break  # Last page
        
        return all_symbols
    
    
    async def _try_fetch_market(self, market: str) -> List[str]:
        '''
        Try fetching stocks for a specific market
        Returns: List of stock codes or empty list if failed
        '''
        symbols = []
        
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
                        
                        logger.info(f"✅ {market}: {len(symbols)} symbols")
                        return symbols
                    else:
                        logger.warning(f"❌ {market}: rt_cd={data.get('rt_cd')}")
        except Exception as e:
            logger.warning(f"❌ {market}: {type(e).__name__}: {e}")
        
        return []
    """)
    
    print()


async def plan_implementation():
    """구현 계획"""
    print("=" * 80)
    print("IMPLEMENTATION PLAN")
    print("=" * 80)
    
    print("""
    🎯 단계별 구현 계획:
    
    [Phase 1] 현재 API 동작 검증 (로컬 테스트)
    ──────────────────────────────────────────
    목표: KIS API 실제 응답 확인
    방법: 다음을 테스트
      1. market="ALL" 요청 → 응답 크기 확인
      2. market="KOSPI" 요청 → 응답 크기 확인
      3. market="KOSDAQ" 요청 → 응답 크기 확인
      4. 페이징 파라미터 지원 여부 확인
    
    테스트 파일: test_kis_api_capabilities.py
    
    [Phase 2] kis_rest_provider.py 개선
    ──────────────────────────────────
    변경 대상:
      - fetch_stock_list() 함수
      - 신규: _fetch_stock_list_single()
      - 신규: _fetch_stock_list_paginated()
    
    변경 내용:
      1. 시장 분할 수집
      2. 재시도 로직 (exponential backoff)
      3. 페이징 지원 (선택)
      4. 향상된 로깅
    
    파일: app/observer/src/provider/kis/kis_rest_provider.py
    예상 추가 라인: 150-200줄
    
    [Phase 3] UniverseManager 개선
    ──────────────────────────────
    변경:
      - _load_candidates()에 배치 수집 트리거
      - 초기화 시 full fetch 시도
      - 타임아웃 관리
    
    [Phase 4] 통합 테스트
    ──────────────────────
    테스트:
      1. 전종목 수집 검증 (2500+)
      2. 캐시 파일 생성 검증
      3. 다음 부팅 시 재사용 검증
      4. OCI 서버 배포 검증
    
    [Phase 5] OCI 배포
    ──────────────────
    1. 코드 커밋
    2. 멀티플랫폼 빌드
    3. GHCR 푸시
    4. OCI 배포
    5. 심볼 수집 실시간 모니터링
    """)
    
    print()


async def main():
    print("\n")
    print("█" * 80)
    print("KIS API STOCK LIST COLLECTION - ANALYSIS & IMPROVEMENT PLAN")
    print("█" * 80)
    print()
    
    await diagnose_current_logic()
    await analyze_solution_approach()
    await design_improved_fetch_stock_list()
    await plan_implementation()
    
    print("=" * 80)
    print("ANALYSIS COMPLETED - READY FOR IMPLEMENTATION")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
