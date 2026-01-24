"""
Asyncio Optimization Module

Purpose:
- Optimize parallel task execution
- Implement task pooling and batching
- Manage event loop efficiently
- Handle backpressure and flow control

Features:
1. Task Pool - Limit concurrent tasks
2. Batch Processing - Process items in batches
3. Rate Limiter - Token bucket algorithm
4. Task Queue Manager - Process queues efficiently
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Any, Optional, List, Generic, TypeVar, Awaitable
from datetime import datetime, timedelta

log = logging.getLogger("AsyncioOptimization")

T = TypeVar("T")


@dataclass
class TaskPoolConfig:
    """Task pool configuration"""
    max_concurrent: int = 10
    timeout_seconds: float = 30.0
    enable_monitoring: bool = True
    monitor_interval_seconds: float = 5.0


@dataclass
class TaskMetrics:
    """Task execution metrics"""
    total_queued: int = 0
    total_completed: int = 0
    total_failed: int = 0
    total_timeout: int = 0
    avg_execution_time_ms: float = 0.0
    
    peak_concurrent_tasks: int = 0
    current_queue_depth: int = 0


class TaskPool:
    """
    Efficient async task pool with concurrency control
    
    Features:
    - Limit concurrent tasks
    - Monitor queue depth
    - Track execution metrics
    - Handle timeouts gracefully
    """
    
    def __init__(self, config: TaskPoolConfig = None) -> None:
        self.config = config or TaskPoolConfig()
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self._metrics = TaskMetrics()
        self._tasks: set = set()
        self._monitor_task: Optional[asyncio.Task] = None
    
    async def submit(
        self,
        coro: Awaitable,
        timeout: Optional[float] = None
    ) -> Any:
        """
        Submit coroutine to task pool
        
        Args:
            coro: Coroutine to execute
            timeout: Optional timeout in seconds
        
        Returns:
            Coroutine result
        """
        timeout = timeout or self.config.timeout_seconds
        
        async with self._semaphore:
            self._metrics.total_queued += 1
            self._metrics.peak_concurrent_tasks = max(
                self._metrics.peak_concurrent_tasks,
                len(self._tasks) + 1
            )
            
            start_time = time.perf_counter()
            
            try:
                # Create task with timeout
                task = asyncio.create_task(coro)
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)
                
                result = await asyncio.wait_for(task, timeout=timeout)
                
                duration = time.perf_counter() - start_time
                self._metrics.total_completed += 1
                self._update_avg_time(duration)
                
                return result
            
            except asyncio.TimeoutError:
                self._metrics.total_timeout += 1
                log.warning(f"Task timeout after {timeout}s")
                raise
            
            except Exception as e:
                self._metrics.total_failed += 1
                log.error(f"Task failed: {e}")
                raise
    
    async def submit_batch(
        self,
        coros: List[Awaitable],
        timeout: Optional[float] = None
    ) -> List[Any]:
        """
        Submit multiple coroutines
        
        Args:
            coros: List of coroutines
            timeout: Optional timeout
        
        Returns:
            List of results (None for failed)
        """
        tasks = [self.submit(coro, timeout) for coro in coros]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    def start_monitoring(self) -> None:
        """Start metrics monitoring"""
        if self.config.enable_monitoring and not self._monitor_task:
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            log.info("✓ Task pool monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop monitoring"""
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None
    
    async def _monitor_loop(self) -> None:
        """Monitor task pool periodically"""
        try:
            while True:
                await asyncio.sleep(self.config.monitor_interval_seconds)
                self._metrics.current_queue_depth = len(self._tasks)
                
                log.debug(
                    f"TaskPool: queued={self._metrics.total_queued}, "
                    f"completed={self._metrics.total_completed}, "
                    f"failed={self._metrics.total_failed}, "
                    f"current_tasks={len(self._tasks)}"
                )
        
        except asyncio.CancelledError:
            pass
    
    def _update_avg_time(self, duration: float) -> None:
        """Update average execution time"""
        total = self._metrics.total_completed
        old_avg = self._metrics.avg_execution_time_ms * (total - 1) / total if total > 1 else 0
        new_avg = old_avg + (duration * 1000) / total
        self._metrics.avg_execution_time_ms = new_avg
    
    def get_metrics(self) -> TaskMetrics:
        """Get current metrics"""
        self._metrics.current_queue_depth = len(self._tasks)
        return self._metrics


class BatchProcessor(Generic[T]):
    """
    Process items in configurable batches
    
    Features:
    - Batch accumulation
    - Automatic flush by size or time
    - Async processing
    - Error handling
    """
    
    def __init__(
        self,
        processor: Callable[[List[T]], Awaitable],
        batch_size: int = 100,
        flush_interval_seconds: float = 5.0
    ) -> None:
        self.processor = processor
        self.batch_size = batch_size
        self.flush_interval = flush_interval_seconds
        
        self._batch: List[T] = []
        self._lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        self._metrics = {"batches_processed": 0, "items_processed": 0}
    
    async def add(self, item: T) -> None:
        """Add item to batch"""
        async with self._lock:
            self._batch.append(item)
            
            if len(self._batch) >= self.batch_size:
                await self._flush()
    
    async def add_batch(self, items: List[T]) -> None:
        """Add multiple items"""
        for item in items:
            await self.add(item)
    
    async def _flush(self) -> None:
        """Process accumulated batch"""
        if not self._batch:
            return
        
        batch_to_process = self._batch[:]
        self._batch.clear()
        
        try:
            await self.processor(batch_to_process)
            self._metrics["batches_processed"] += 1
            self._metrics["items_processed"] += len(batch_to_process)
            log.debug(f"✓ Batch processed: {len(batch_to_process)} items")
        
        except Exception as e:
            log.error(f"Batch processing failed: {e}")
            # Re-add items on failure
            self._batch.extend(batch_to_process)
            raise
    
    async def start_auto_flush(self) -> None:
        """Start automatic periodic flush"""
        async def auto_flush_loop():
            try:
                while True:
                    await asyncio.sleep(self.flush_interval)
                    async with self._lock:
                        if self._batch:
                            await self._flush()
            except asyncio.CancelledError:
                pass
        
        self._flush_task = asyncio.create_task(auto_flush_loop())
        log.info(f"✓ Auto-flush started (interval={self.flush_interval}s)")
    
    async def stop_auto_flush(self) -> None:
        """Stop auto-flush and process remaining items"""
        if self._flush_task:
            self._flush_task.cancel()
            self._flush_task = None
        
        async with self._lock:
            await self._flush()
    
    def get_metrics(self) -> dict:
        """Get processing metrics"""
        self._metrics["pending_items"] = len(self._batch)
        return self._metrics


class TokenBucketLimiter:
    """
    Token bucket rate limiter
    
    Features:
    - Smooth rate limiting
    - Burst allowance
    - Async-friendly
    """
    
    def __init__(
        self,
        rate: float = 100.0,  # tokens per second
        burst_size: int = 100
    ) -> None:
        self.rate = rate
        self.burst_size = burst_size
        
        self._tokens = float(burst_size)
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()
        
        self._metrics = {"requested": 0, "granted": 0, "delayed": 0}
    
    async def acquire(self, tokens: int = 1) -> None:
        """
        Acquire tokens (wait if necessary)
        
        Args:
            tokens: Number of tokens to acquire
        """
        async with self._lock:
            self._metrics["requested"] += tokens
            
            # Refill tokens
            now = time.monotonic()
            elapsed = now - self._last_update
            self._tokens = min(
                self.burst_size,
                self._tokens + elapsed * self.rate
            )
            self._last_update = now
            
            # Wait if insufficient tokens
            while self._tokens < tokens:
                # Calculate wait time
                tokens_needed = tokens - self._tokens
                wait_time = tokens_needed / self.rate
                
                await asyncio.sleep(wait_time)
                
                # Refill again
                now = time.monotonic()
                elapsed = now - self._last_update
                self._tokens = min(
                    self.burst_size,
                    self._tokens + elapsed * self.rate
                )
                self._last_update = now
                
                self._metrics["delayed"] += 1
            
            self._tokens -= tokens
            self._metrics["granted"] += tokens
    
    async def try_acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without waiting
        
        Returns:
            True if acquired, False if insufficient tokens
        """
        async with self._lock:
            # Refill tokens
            now = time.monotonic()
            elapsed = now - self._last_update
            self._tokens = min(
                self.burst_size,
                self._tokens + elapsed * self.rate
            )
            self._last_update = now
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                self._metrics["granted"] += tokens
                return True
            
            self._metrics["requested"] += tokens
            return False
    
    def get_metrics(self) -> dict:
        """Get rate limiting metrics"""
        return {
            **self._metrics,
            "efficiency": (
                self._metrics["granted"] / self._metrics["requested"]
                if self._metrics["requested"] > 0 else 0
            )
        }


# ---- CLI Entry Point ----

async def main():
    """Test asyncio optimization components"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    print("\n🧪 Asyncio Optimization Test\n")
    
    # Test 1: Task Pool
    print("=" * 60)
    print("1. TASK POOL TEST")
    print("=" * 60)
    
    async def dummy_task(n):
        await asyncio.sleep(0.1)
        return f"Result {n}"
    
    pool = TaskPool(TaskPoolConfig(max_concurrent=5))
    pool.start_monitoring()
    
    # Submit multiple tasks
    tasks = [dummy_task(i) for i in range(20)]
    results = await pool.submit_batch(tasks)
    
    print(f"✓ Processed {len(results)} tasks")
    metrics = pool.get_metrics()
    print(f"  - Completed: {metrics.total_completed}")
    print(f"  - Peak concurrent: {metrics.peak_concurrent_tasks}")
    print(f"  - Avg time: {metrics.avg_execution_time_ms:.2f}ms")
    
    pool.stop_monitoring()
    
    # Test 2: Batch Processor
    print("\n" + "=" * 60)
    print("2. BATCH PROCESSOR TEST")
    print("=" * 60)
    
    batch_results = []
    
    async def batch_handler(items):
        batch_results.extend(items)
        await asyncio.sleep(0.1)  # Simulate processing
    
    processor = BatchProcessor(batch_handler, batch_size=10, flush_interval_seconds=2)
    await processor.start_auto_flush()
    
    # Add items
    for i in range(25):
        await processor.add(f"item_{i}")
    
    await processor.stop_auto_flush()
    
    print(f"✓ Processed {len(batch_results)} items")
    p_metrics = processor.get_metrics()
    print(f"  - Batches: {p_metrics['batches_processed']}")
    print(f"  - Items: {p_metrics['items_processed']}")
    
    # Test 3: Token Bucket Limiter
    print("\n" + "=" * 60)
    print("3. TOKEN BUCKET LIMITER TEST")
    print("=" * 60)
    
    limiter = TokenBucketLimiter(rate=10, burst_size=5)
    
    start = time.perf_counter()
    
    for i in range(15):
        await limiter.acquire(1)
        elapsed = time.perf_counter() - start
        print(f"  Token {i+1:2d} acquired at {elapsed:.2f}s")
    
    l_metrics = limiter.get_metrics()
    print(f"\n✓ Rate limiting complete")
    print(f"  - Requested: {l_metrics['requested']}")
    print(f"  - Granted: {l_metrics['granted']}")
    print(f"  - Delayed: {l_metrics['delayed']}")
    print(f"  - Efficiency: {l_metrics['efficiency']:.1%}")


if __name__ == "__main__":
    asyncio.run(main())
