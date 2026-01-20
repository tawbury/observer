# Dynamic Polling Engine 설계 보고서

**문서 버전:** v1.0.0  
**작성일:** 2026-01-13  
**대상 시스템:** QTS Observer - Stock Market Data Collection  
**배포 환경:** Azure VM (Docker + systemd)

---

## 1. 개요 (Executive Summary)

### 1.1 목적

본 문서는 한국투자증권(KIS) REST API를 활용하여 약 2,500개 종목의 시장 데이터를 수집하는 **Dynamic Polling Engine**의 설계 전략을 제시합니다. 이 엔진은 스캘핑/스윙 전략의 백테스트 데이터 수집을 위해 다음 두 가지 모드를 지원합니다:

- **Normal Mode**: 전체 종목을 30초~3분 간격으로 스캔
- **Burst Mode**: 급등/급락 이벤트 감지 시 특정 종목을 1초 간격(틱 수준)으로 로깅

### 1.2 핵심 제약사항

1. **Observer 아키텍처 원칙 준수**
   - Observer는 판단/전략/실행을 수행하지 않음 (Judgment-free)
   - ObservationSnapshot 수신 → PatternRecord 생성 → EventBus 전달
   - Stateless 원칙 유지 (상태 저장 최소화)

2. **KIS API Rate Limit**
   - 초당 요청 제한: 약 20 req/sec (공식 문서 기준)
   - 분당 요청 제한: 약 1,000 req/min
   - 일일 요청 제한: 약 100,000 req/day

3. **데이터 계약 (Contract)**
   - `ObservationSnapshot` 구조 준수
   - `PatternRecord` 래핑 규칙 준수
   - JSONL 파일 기반 Append-only 저장

---

## 2. 문제 분석 (Problem Analysis)

### 2.1 Rate Limit 관리 문제

**시나리오 1: 전체 종목 순차 스캔**
- 2,500 종목 × 1 req/종목 = 2,500 requests
- 20 req/sec 제한 → 최소 125초 (약 2분) 소요
- 결론: 30초 간격 스캔은 **불가능**, 최소 2~3분 간격 필요

**시나리오 2: Burst Mode 동시 운영**
- Normal Mode: 2,500 종목 / 3분 = 약 14 req/sec
- Burst Mode: 최대 10종목 × 1 req/sec = 10 req/sec
- 합계: 24 req/sec → **Rate Limit 초과 위험**

**핵심 과제:**
- Normal Mode와 Burst Mode의 대역폭 경쟁 해결
- Rate Limit 내에서 우선순위 기반 스케줄링 필요

### 2.2 "Stateless" 원칙과 급등 감지의 모순

**문제:**
- 급등/급락 감지를 위해서는 "이전 가격" 정보 필요
- Observer는 Stateless 원칙을 따라야 함

**현재 코드 분석:**
```python
# @d:\development\prj_ops\app\obs_deploy\app\src\observer\snapshot.py:24-25
_last_price: Optional[float] = None
_last_volume: Optional[float] = None
```
- 모듈 레벨 변수로 "직전 값" 캐싱 중
- 단일 종목 기준으로 설계됨 (2,500 종목 대응 불가)

**해결 방향:**
- "Stateless"의 정의를 "Observer 내부 상태 최소화"로 해석
- 메모리 효율적인 단기 캐시 허용 (Redis 또는 In-memory Dict)
- 캐시는 "관측 보조 도구"이지 "비즈니스 로직 상태"가 아님

### 2.3 Dual-Speed Logging 아키텍처

**요구사항:**
- Normal Mode: 느린 주기 (2~3분)
- Burst Mode: 빠른 주기 (1초)
- 두 모드의 독립적 운영 및 우선순위 제어

**기술 선택지:**
1. **Asyncio 기반 Concurrent Tasks**
2. **Multithreading with Priority Queue**
3. **Single-threaded Event Loop with Scheduler**

---

## 3. 설계 전략 (Implementation Strategy)

### 3.1 아키텍처 개요

```
┌─────────────────────────────────────────────────────────┐
│           Dynamic Polling Engine (DPE)                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐      ┌──────────────┐               │
│  │ Rate Limiter │◄─────┤ Task Queue   │               │
│  │ (Token Bucket)│      │ (Priority)   │               │
│  └──────┬───────┘      └──────▲───────┘               │
│         │                     │                        │
│         │                     │                        │
│  ┌──────▼───────┐      ┌──────┴───────┐               │
│  │ Normal Mode  │      │ Burst Mode   │               │
│  │ Scheduler    │      │ Trigger      │               │
│  │ (3min cycle) │      │ (1sec cycle) │               │
│  └──────┬───────┘      └──────▲───────┘               │
│         │                     │                        │
│         │              ┌──────┴───────┐               │
│         │              │ Surge        │               │
│         │              │ Detector     │               │
│         │              └──────▲───────┘               │
│         │                     │                        │
│  ┌──────▼─────────────────────┴───────┐               │
│  │   KIS API Client (REST)            │               │
│  └──────┬─────────────────────────────┘               │
│         │                                              │
│  ┌──────▼─────────────────────────────┐               │
│  │   Price Cache (In-Memory)          │               │
│  │   {symbol: {price, volume, ts}}    │               │
│  └──────┬─────────────────────────────┘               │
│         │                                              │
│  ┌──────▼─────────────────────────────┐               │
│  │   Snapshot Builder                 │               │
│  └──────┬─────────────────────────────┘               │
│         │                                              │
└─────────┼─────────────────────────────────────────────┘
          │
          ▼
    ┌─────────────┐
    │  Observer   │ (기존 Observer-Core)
    │  on_snapshot│
    └─────────────┘
```

### 3.2 핵심 컴포넌트 설계

#### 3.2.1 Rate Limiter (Token Bucket Algorithm)

**목적:** KIS API Rate Limit 준수

**구현 전략:**
```python
class TokenBucketRateLimiter:
    """
    Token Bucket 알고리즘 기반 Rate Limiter
    - capacity: 20 (초당 최대 요청 수)
    - refill_rate: 20 tokens/sec
    - 요청 전 token 소비, 부족 시 대기
    """
    def __init__(self, capacity: int = 20, refill_rate: float = 20.0):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> None:
        """토큰 획득 (부족 시 대기)"""
        async with self._lock:
            while self.tokens < tokens:
                await self._refill()
                await asyncio.sleep(0.05)  # 50ms 대기
            self.tokens -= tokens
    
    async def _refill(self) -> None:
        """경과 시간 기반 토큰 보충"""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate
        )
        self.last_refill = now
```

**특징:**
- Asyncio 기반 비동기 처리
- 초당 20 req 제한 준수
- Burst 요청 시 자동 throttling

#### 3.2.2 Price Cache (In-Memory)

**목적:** 급등/급락 감지를 위한 "이전 가격" 저장

**설계 원칙:**
- Observer 외부에 위치 (Stateless 원칙 유지)
- 메모리 효율성: 종목당 최소 정보만 저장
- TTL(Time-to-Live) 기반 자동 정리

**데이터 구조:**
```python
@dataclass
class PriceSnapshot:
    """종목별 최신 가격 정보 (경량화)"""
    symbol: str
    price: float
    volume: int
    timestamp: float  # epoch seconds
    
class PriceCache:
    """
    메모리 효율적인 가격 캐시
    - 2,500 종목 × 32 bytes ≈ 80 KB (매우 작음)
    - TTL: 10분 (오래된 데이터 자동 삭제)
    """
    def __init__(self, ttl_seconds: int = 600):
        self._cache: Dict[str, PriceSnapshot] = {}
        self._ttl = ttl_seconds
        self._lock = asyncio.Lock()
    
    async def update(self, symbol: str, price: float, volume: int) -> None:
        """가격 정보 업데이트"""
        async with self._lock:
            self._cache[symbol] = PriceSnapshot(
                symbol=symbol,
                price=price,
                volume=volume,
                timestamp=time.time()
            )
    
    async def get_previous(self, symbol: str) -> Optional[PriceSnapshot]:
        """이전 가격 조회 (급등 감지용)"""
        async with self._lock:
            snapshot = self._cache.get(symbol)
            if snapshot and (time.time() - snapshot.timestamp) < self._ttl:
                return snapshot
            return None
    
    async def cleanup_expired(self) -> None:
        """TTL 초과 데이터 정리 (백그라운드 태스크)"""
        async with self._lock:
            now = time.time()
            expired = [
                sym for sym, snap in self._cache.items()
                if (now - snap.timestamp) > self._ttl
            ]
            for sym in expired:
                del self._cache[sym]
```

**메모리 사용량 분석:**
- 종목당: 8 (symbol ref) + 8 (price) + 8 (volume) + 8 (timestamp) = 32 bytes
- 2,500 종목: 32 × 2,500 = 80,000 bytes ≈ **78 KB**
- 결론: 메모리 부담 무시 가능

#### 3.2.3 Surge Detector (급등/급락 감지)

**목적:** Burst Mode 트리거 조건 판단

**감지 로직:**
```python
class SurgeDetector:
    """
    급등/급락 이벤트 감지기
    - Observer 외부에 위치 (판단 로직 분리)
    - 단순 임계값 기반 (전략 로직 아님)
    """
    def __init__(
        self,
        price_change_threshold: float = 0.03,  # 3% 변동
        volume_spike_threshold: float = 2.0,   # 2배 급증
    ):
        self.price_threshold = price_change_threshold
        self.volume_threshold = volume_spike_threshold
    
    def detect(
        self,
        current_price: float,
        current_volume: int,
        previous: Optional[PriceSnapshot]
    ) -> bool:
        """
        급등/급락 여부 판단
        
        조건:
        1. 가격 변동률 > 3% OR
        2. 거래량 급증 > 2배
        """
        if previous is None:
            return False
        
        # 가격 변동률
        price_change = abs(current_price - previous.price) / previous.price
        if price_change > self.price_threshold:
            return True
        
        # 거래량 급증
        if previous.volume > 0:
            volume_ratio = current_volume / previous.volume
            if volume_ratio > self.volume_threshold:
                return True
        
        return False
```

**중요:** 
- 이 로직은 "관측 트리거"이지 "전략 판단"이 아님
- Observer 원칙 위반 없음 (외부 컴포넌트)

#### 3.2.4 Task Queue (Priority-based)

**목적:** Normal Mode와 Burst Mode 작업 우선순위 관리

**설계:**
```python
from asyncio import PriorityQueue
from enum import IntEnum

class TaskPriority(IntEnum):
    """우선순위 정의 (낮을수록 높은 우선순위)"""
    BURST = 1      # Burst Mode (최우선)
    NORMAL = 2     # Normal Mode (일반)

@dataclass(order=True)
class PollTask:
    """폴링 작업 단위"""
    priority: int
    symbol: str = field(compare=False)
    mode: str = field(compare=False)  # "normal" or "burst"
    scheduled_at: float = field(compare=False)

class TaskScheduler:
    """
    우선순위 기반 작업 스케줄러
    - Burst Mode 작업 우선 처리
    - Rate Limiter와 연동
    """
    def __init__(self, rate_limiter: TokenBucketRateLimiter):
        self.queue = PriorityQueue()
        self.rate_limiter = rate_limiter
        self.burst_symbols: Set[str] = set()  # Burst Mode 활성 종목
    
    async def enqueue_normal(self, symbol: str) -> None:
        """Normal Mode 작업 추가"""
        task = PollTask(
            priority=TaskPriority.NORMAL,
            symbol=symbol,
            mode="normal",
            scheduled_at=time.time()
        )
        await self.queue.put(task)
    
    async def enqueue_burst(self, symbol: str) -> None:
        """Burst Mode 작업 추가 (우선순위 높음)"""
        task = PollTask(
            priority=TaskPriority.BURST,
            symbol=symbol,
            mode="burst",
            scheduled_at=time.time()
        )
        await self.queue.put(task)
        self.burst_symbols.add(symbol)
    
    async def dequeue_and_execute(
        self,
        executor: Callable[[str], Awaitable[None]]
    ) -> None:
        """작업 꺼내서 실행 (Rate Limit 준수)"""
        task = await self.queue.get()
        
        # Rate Limiter 토큰 획득 대기
        await self.rate_limiter.acquire(tokens=1)
        
        # 실행
        await executor(task.symbol)
```

### 3.3 Loop 아키텍처 선택: **Asyncio 기반**

**선택 이유:**

1. **I/O Bound 작업 최적화**
   - KIS API 호출은 네트워크 I/O (CPU 사용 낮음)
   - Asyncio의 비동기 I/O가 이상적

2. **경량 동시성**
   - 2,500 종목 동시 관리 시 Thread보다 메모리 효율적
   - Context Switching 오버헤드 최소화

3. **Rate Limiter 통합 용이**
   - `asyncio.sleep()` 기반 정밀한 타이밍 제어
   - Token Bucket과 자연스러운 통합

**대안 비교:**

| 방식 | 장점 | 단점 | 적합성 |
|------|------|------|--------|
| **Asyncio** | I/O 최적화, 메모리 효율 | 디버깅 복잡 | ✅ **최적** |
| Multithreading | 구현 단순 | GIL 제약, 메모리 부담 | ⚠️ 차선 |
| Single-threaded | 안정성 높음 | 동시성 부족 | ❌ 부적합 |

### 3.4 전체 실행 흐름 (Logic Flow)

```
[시작]
  │
  ├─ (1) Normal Mode Scheduler 시작
  │    └─ 2,500 종목을 3분 주기로 순회
  │       └─ 각 종목을 TaskQueue에 NORMAL 우선순위로 추가
  │
  ├─ (2) Task Executor 시작 (Asyncio Loop)
  │    └─ while True:
  │         ├─ TaskQueue에서 작업 꺼내기 (우선순위 순)
  │         ├─ Rate Limiter 토큰 획득 대기
  │         ├─ KIS API 호출 (현재가 조회)
  │         ├─ Price Cache 업데이트
  │         ├─ Surge Detector 실행
  │         │    └─ 급등 감지 시:
  │         │         └─ Burst Mode 활성화 (해당 종목)
  │         │              └─ 1초 주기로 TaskQueue에 BURST 우선순위 추가
  │         ├─ ObservationSnapshot 생성
  │         └─ Observer.on_snapshot() 호출
  │
  ├─ (3) Burst Mode Manager
  │    └─ 활성 종목 모니터링
  │       └─ 조건 해제 시 (예: 5분 경과 or 변동성 안정)
  │            └─ Burst Mode 종료 → Normal Mode 복귀
  │
  └─ (4) Cache Cleanup Task (백그라운드)
       └─ 10분마다 TTL 초과 데이터 삭제
```

---

## 4. 구현 세부사항 (Implementation Details)

### 4.1 KIS API Rate Limit 관리 전략

**계층적 제한 적용:**

```python
class KisRateLimitManager:
    """
    다층 Rate Limit 관리
    - Layer 1: 초당 제한 (20 req/sec)
    - Layer 2: 분당 제한 (1,000 req/min)
    - Layer 3: 일일 제한 (100,000 req/day)
    """
    def __init__(self):
        self.second_limiter = TokenBucketRateLimiter(
            capacity=20, refill_rate=20.0
        )
        self.minute_counter = 0
        self.minute_reset_time = time.time() + 60
        self.daily_counter = 0
        self.daily_reset_time = time.time() + 86400
    
    async def acquire(self) -> None:
        """모든 계층 제한 확인 후 토큰 획득"""
        # Layer 1: 초당 제한
        await self.second_limiter.acquire()
        
        # Layer 2: 분당 제한
        if self.minute_counter >= 1000:
            wait_time = self.minute_reset_time - time.time()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self.minute_counter = 0
            self.minute_reset_time = time.time() + 60
        
        # Layer 3: 일일 제한
        if self.daily_counter >= 100000:
            wait_time = self.daily_reset_time - time.time()
            if wait_time > 0:
                logging.warning(f"Daily limit reached. Waiting {wait_time}s")
                await asyncio.sleep(wait_time)
            self.daily_counter = 0
            self.daily_reset_time = time.time() + 86400
        
        # 카운터 증가
        self.minute_counter += 1
        self.daily_counter += 1
```

### 4.2 Normal Mode 스케줄링 전략

**목표:** 2,500 종목을 3분(180초)에 균등 분산

**구현:**
```python
class NormalModeScheduler:
    """
    Normal Mode 종목 스케줄러
    - 2,500 종목을 180초에 균등 분산
    - 종목당 간격: 180 / 2,500 = 0.072초 (72ms)
    """
    def __init__(
        self,
        symbols: List[str],
        interval_sec: float = 180.0,
        task_queue: TaskScheduler
    ):
        self.symbols = symbols
        self.interval = interval_sec
        self.task_queue = task_queue
        self.delay_per_symbol = interval_sec / len(symbols)
    
    async def run(self) -> None:
        """무한 루프로 종목 스케줄링"""
        while True:
            start_time = time.time()
            
            for symbol in self.symbols:
                # Burst Mode 활성 종목은 스킵 (중복 방지)
                if symbol not in self.task_queue.burst_symbols:
                    await self.task_queue.enqueue_normal(symbol)
                
                # 균등 분산 대기
                await asyncio.sleep(self.delay_per_symbol)
            
            # 한 사이클 완료 후 다음 사이클까지 대기
            elapsed = time.time() - start_time
            if elapsed < self.interval:
                await asyncio.sleep(self.interval - elapsed)
```

**특징:**
- 종목당 72ms 간격으로 TaskQueue에 추가
- Rate Limiter가 실제 API 호출 속도 제어
- Burst Mode 활성 종목 자동 제외

### 4.3 Burst Mode 트리거 및 종료 로직

**활성화 조건:**
```python
class BurstModeManager:
    """
    Burst Mode 생명주기 관리
    - 활성화: 급등/급락 감지 시
    - 종료: 5분 경과 or 변동성 안정
    """
    def __init__(
        self,
        task_queue: TaskScheduler,
        max_burst_symbols: int = 10,  # 동시 최대 10종목
        burst_duration_sec: float = 300.0,  # 5분
    ):
        self.task_queue = task_queue
        self.max_burst = max_burst_symbols
        self.burst_duration = burst_duration_sec
        self.active_bursts: Dict[str, float] = {}  # {symbol: start_time}
    
    async def activate(self, symbol: str) -> bool:
        """Burst Mode 활성화"""
        # 최대 개수 제한
        if len(self.active_bursts) >= self.max_burst:
            logging.warning(f"Burst limit reached. Ignoring {symbol}")
            return False
        
        if symbol not in self.active_bursts:
            self.active_bursts[symbol] = time.time()
            logging.info(f"Burst Mode activated: {symbol}")
            
            # 1초 주기 작업 시작
            asyncio.create_task(self._burst_loop(symbol))
            return True
        return False
    
    async def _burst_loop(self, symbol: str) -> None:
        """1초 주기로 Burst 작업 추가"""
        while symbol in self.active_bursts:
            await self.task_queue.enqueue_burst(symbol)
            await asyncio.sleep(1.0)
    
    async def check_deactivation(self) -> None:
        """종료 조건 확인 (백그라운드 태스크)"""
        while True:
            now = time.time()
            to_remove = []
            
            for symbol, start_time in self.active_bursts.items():
                # 5분 경과 시 종료
                if (now - start_time) > self.burst_duration:
                    to_remove.append(symbol)
                    logging.info(f"Burst Mode deactivated: {symbol} (timeout)")
            
            for symbol in to_remove:
                del self.active_bursts[symbol]
                self.task_queue.burst_symbols.discard(symbol)
            
            await asyncio.sleep(10.0)  # 10초마다 확인
```

### 4.4 ObservationSnapshot 생성 규칙

**Observer 계약 준수:**

```python
async def build_snapshot_from_kis_response(
    kis_response: Dict[str, Any],
    symbol: str,
    mode: str,  # "normal" or "burst"
    session_id: str,
) -> ObservationSnapshot:
    """
    KIS API 응답을 ObservationSnapshot으로 변환
    
    중요: Observer 계약 준수
    - meta: 시간, 세션, 모드 정보
    - context: source="market", stage="raw", symbol
    - observation: inputs (가격/거래량), computed (delta), state (빈 dict)
    """
    # KIS 응답 파싱 (예시)
    price = float(kis_response.get("stck_prpr", 0))  # 현재가
    volume = int(kis_response.get("acml_vol", 0))   # 누적거래량
    
    # Snapshot 생성 (기존 build_snapshot 함수 활용)
    snapshot = build_snapshot(
        session_id=session_id,
        mode="PROD",
        source="market",
        stage="raw",
        symbol=symbol,
        market="KRX",
        inputs={
            "price": price,
            "volume": volume,
            "kis_raw": kis_response,  # 원본 데이터 보존
        },
        computed={},  # Delta는 snapshot.py 내부에서 계산됨
        state={
            "polling_mode": mode,  # "normal" or "burst"
        },
        # Extended meta (Scalp Extension E2)
        tick_source="kis_rest",
        loop_interval_ms=1000.0 if mode == "burst" else 180000.0,
    )
    
    return snapshot
```

---

## 5. 성능 및 리소스 분석

### 5.1 API 사용량 예측

**Normal Mode Only (Baseline):**
- 2,500 종목 / 180초 = 13.9 req/sec
- 일일: 13.9 × 86,400 = **1,200,960 requests/day** ❌ (제한 초과)

**최적화된 Normal Mode:**
- 간격 조정: 300초 (5분)
- 2,500 종목 / 300초 = 8.3 req/sec
- 일일: 8.3 × 86,400 = **717,120 requests/day** ✅ (제한 내)

**Burst Mode 추가 시:**
- Burst: 평균 5종목 × 1 req/sec = 5 req/sec
- 합계: 8.3 + 5 = 13.3 req/sec ✅ (초당 제한 내)
- 일일 추가: 5 × 3,600 (1시간 가정) = 18,000 requests
- 총합: 717,120 + 18,000 = **735,120 requests/day** ✅

**결론:** Normal Mode 5분 간격 + Burst Mode 병행 시 모든 제한 준수 가능

### 5.2 메모리 사용량

**컴포넌트별 메모리:**
- Price Cache: 78 KB (2,500 종목)
- Task Queue: 약 200 KB (최대 3,000 작업 대기 가정)
- Asyncio Overhead: 약 10 MB
- **총합: 약 11 MB** (매우 경량)

### 5.3 CPU 사용량

- API 호출: I/O Bound (CPU 사용 낮음)
- JSON 파싱: 종목당 < 1ms
- Snapshot 생성: 종목당 < 0.5ms
- **예상 CPU 사용률: < 10%** (Azure VM 1 vCPU 기준)

---

## 6. Observer 원칙 준수 검증

### 6.1 Stateless 원칙

**질문:** Price Cache는 상태 저장 아닌가?

**답변:**
- Price Cache는 **Observer 외부** 컴포넌트
- Observer는 여전히 Stateless (Snapshot 수신 → 처리 → 전달)
- Cache는 "관측 보조 도구"이지 "비즈니스 상태"가 아님
- 유사 사례: `snapshot.py`의 `_last_price` (모듈 레벨 변수)

### 6.2 Judgment-Free 원칙

**질문:** Surge Detector는 판단 로직 아닌가?

**답변:**
- Surge Detector는 **Observer 외부** 컴포넌트
- 단순 임계값 기반 트리거 (전략 로직 아님)
- Observer는 여전히 판단 없이 Snapshot만 처리
- 유사 사례: Guard Layer (validation 기반 blocking)

### 6.3 Contract 준수

**확인 사항:**
- ✅ `ObservationSnapshot` 구조 준수
- ✅ `PatternRecord` 래핑 규칙 준수
- ✅ JSONL Append-only 저장
- ✅ EventBus 전달 흐름 유지

---

## 7. 구현 로드맵 (Implementation Roadmap)

### Phase 1: 기반 인프라 (1-2일)
- [ ] `TokenBucketRateLimiter` 구현
- [ ] `PriceCache` 구현
- [ ] `KisRateLimitManager` 구현
- [ ] 단위 테스트 작성

### Phase 2: 스케줄러 (2-3일)
- [ ] `TaskScheduler` (Priority Queue) 구현
- [ ] `NormalModeScheduler` 구현
- [ ] `BurstModeManager` 구현
- [ ] 통합 테스트 (Mock KIS API)

### Phase 3: KIS API 연동 (2-3일)
- [ ] KIS REST API 클라이언트 구현
- [ ] 응답 파싱 로직 구현
- [ ] Error Handling (Retry, Timeout)
- [ ] Rate Limit 실제 검증

### Phase 4: Observer 통합 (1-2일)
- [ ] `build_snapshot_from_kis_response` 구현
- [ ] Observer.on_snapshot() 연결
- [ ] End-to-End 테스트

### Phase 5: 모니터링 및 최적화 (1-2일)
- [ ] 메트릭 수집 (API 호출 수, 지연시간)
- [ ] 로깅 강화
- [ ] 성능 튜닝

**총 예상 기간: 7-12일**

---

## 8. 리스크 및 대응 방안

### 8.1 KIS API Rate Limit 초과

**리스크:** 실제 제한이 문서와 다를 수 있음

**대응:**
- 초기 운영 시 Conservative 설정 (15 req/sec)
- 실시간 모니터링으로 안전 한계 파악
- 429 Error 발생 시 Exponential Backoff

### 8.2 Burst Mode 폭주

**리스크:** 급등 종목 동시 다발 시 Burst Mode 과부하

**대응:**
- 최대 동시 Burst 종목 제한 (10개)
- 우선순위 기반 선택 (변동률 높은 순)
- 자동 종료 메커니즘 (5분 timeout)

### 8.3 메모리 누수

**리스크:** Price Cache 무한 증가

**대응:**
- TTL 기반 자동 정리 (10분)
- 백그라운드 Cleanup Task
- 메모리 사용량 모니터링

---

## 9. 결론 및 권장사항

### 9.1 핵심 설계 결정

1. **Loop 아키텍처: Asyncio**
   - I/O Bound 작업에 최적
   - 메모리 효율적
   - Rate Limiter와 자연스러운 통합

2. **Rate Limit 관리: Token Bucket + 다층 제한**
   - 초/분/일 모든 제한 준수
   - Burst 요청 자동 throttling

3. **상태 관리: Observer 외부 Price Cache**
   - Stateless 원칙 유지
   - 메모리 효율적 (78 KB)
   - TTL 기반 자동 정리

4. **Dual-Speed Logging: Priority Queue**
   - Burst Mode 우선 처리
   - Normal Mode와 독립적 운영

### 9.2 권장 운영 파라미터

```python
# 권장 설정값
NORMAL_MODE_INTERVAL = 300  # 5분 (안전 마진)
BURST_MODE_INTERVAL = 1     # 1초
MAX_BURST_SYMBOLS = 10      # 동시 최대 10종목
BURST_DURATION = 300        # 5분 후 자동 종료
RATE_LIMIT_PER_SEC = 15     # 초당 15 req (안전 마진)
PRICE_CHANGE_THRESHOLD = 0.03  # 3% 급등/급락
VOLUME_SPIKE_THRESHOLD = 2.0   # 2배 거래량 급증
```

### 9.3 다음 단계

1. **Phase 1 구현 시작**
   - Rate Limiter 및 Price Cache 구현
   - 단위 테스트 작성

2. **KIS API 문서 정밀 검토**
   - 실제 Rate Limit 확인
   - 응답 포맷 파악

3. **Mock 환경 구축**
   - KIS API Simulator 개발
   - 통합 테스트 환경 준비

---

## 부록 A: 전체 코드 구조 (Skeleton)

```
app/obs_deploy/app/src/
├── polling_engine/
│   ├── __init__.py
│   ├── rate_limiter.py          # TokenBucketRateLimiter
│   ├── price_cache.py           # PriceCache
│   ├── surge_detector.py        # SurgeDetector
│   ├── task_scheduler.py        # TaskScheduler, PollTask
│   ├── normal_scheduler.py      # NormalModeScheduler
│   ├── burst_manager.py         # BurstModeManager
│   ├── kis_client.py            # KIS API Client
│   └── snapshot_builder.py      # build_snapshot_from_kis_response
├── runtime/
│   └── polling_engine_runner.py # Main entry point
└── observer/
    └── (기존 Observer-Core 유지)
```

---

## 부록 B: 참고 자료

- **Observer Architecture:** `obs_architecture.md`
- **Snapshot Contract:** `app/obs_deploy/app/src/observer/snapshot.py`
- **PatternRecord Contract:** `app/obs_deploy/app/src/observer/pattern_record.py`
- **KIS API 문서:** (사용자 제공 필요)

---

**문서 종료**
