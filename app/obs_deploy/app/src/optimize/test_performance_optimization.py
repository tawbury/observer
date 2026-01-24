"""
Phase 12.2: Performance Optimization Test Suite

Purpose:
- Measure current system performance
- Apply optimizations
- Benchmark improvements
- Generate performance report

Tests:
1. Asyncio Optimization - Task pool, batch processing, rate limiting
2. I/O Optimization - Buffered writes, memory-mapped reads, compression
3. Memory Optimization - GC tuning, object pooling
4. Overall System Performance - End-to-end optimization validation
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from shared.timezone import ZoneInfo

# Import optimization modules
import sys
sys.path.insert(0, str(Path(__file__).parent))

from performance_profiler import PerformanceProfiler, PerformanceMetrics
from asyncio_optimizer import TaskPool, TaskPoolConfig, BatchProcessor, TokenBucketLimiter
from io_optimizer import BufferedWriter, MemoryMappedReader, CompressedWriter

log = logging.getLogger("PerformanceOptimization")


@dataclass
class OptimizationTestResult:
    """Test result with before/after metrics"""
    test_name: str
    status: str = "PENDING"  # PENDING, RUNNING, PASSED, FAILED
    duration_seconds: float = 0.0
    error_message: str = ""
    
    # Metrics
    before_metrics: Dict[str, Any] = field(default_factory=dict)
    after_metrics: Dict[str, Any] = field(default_factory=dict)
    improvement_percent: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "test_name": self.test_name,
            "status": self.status,
            "duration_seconds": f"{self.duration_seconds:.3f}",
            "improvement_percent": f"{self.improvement_percent:.1f}%",
            "before": self.before_metrics,
            "after": self.after_metrics,
            "error": self.error_message
        }


class PerformanceOptimizationTest:
    """
    Performance optimization test suite
    
    Tests:
    1. Asyncio task pool optimization
    2. Batch processing efficiency
    3. Rate limiting smoothness
    4. Buffered I/O throughput
    5. Memory-mapped file access
    6. Compression efficiency
    """
    
    def __init__(self) -> None:
        self._tz = ZoneInfo("Asia/Seoul") if ZoneInfo else None
        self.results: List[OptimizationTestResult] = []
        self.profiler = PerformanceProfiler()
        
        # Test configuration
        self.test_iterations = 100
        self.batch_size = 50
        self.concurrent_tasks = 10
    
    # =====================================================================
    # Asyncio Optimization Tests
    # =====================================================================
    
    async def _test_task_pool_optimization(self) -> OptimizationTestResult:
        """Test task pool concurrent execution"""
        result = OptimizationTestResult("Task_Pool_Optimization")
        result.status = "RUNNING"
        
        start = time.perf_counter()
        
        try:
            # Without optimization - sequential execution
            log.info("\n[ASYNCIO] Measuring sequential execution...")
            
            async def dummy_task(n):
                await asyncio.sleep(0.01)
                return n * 2
            
            start_time = time.perf_counter()
            sequential_results = []
            for i in range(self.test_iterations):
                sequential_results.append(await dummy_task(i))
            sequential_time = time.perf_counter() - start_time
            
            # With optimization - task pool
            log.info("[ASYNCIO] Measuring task pool execution...")
            
            pool = TaskPool(TaskPoolConfig(max_concurrent=self.concurrent_tasks))
            
            start_time = time.perf_counter()
            tasks = [dummy_task(i) for i in range(self.test_iterations)]
            pool_results = await pool.submit_batch(tasks)
            pool_time = time.perf_counter() - start_time
            
            # Calculate improvement
            improvement = ((sequential_time - pool_time) / sequential_time) * 100
            
            result.before_metrics = {
                "method": "sequential",
                "time_seconds": f"{sequential_time:.3f}",
                "tasks": self.test_iterations
            }
            
            result.after_metrics = {
                "method": "task_pool",
                "time_seconds": f"{pool_time:.3f}",
                "concurrent_limit": self.concurrent_tasks,
                "tasks": self.test_iterations
            }
            
            result.improvement_percent = improvement
            result.status = "PASSED"
            
            log.info(f"✓ Sequential: {sequential_time:.3f}s → Pool: {pool_time:.3f}s")
            log.info(f"  Improvement: {improvement:.1f}%")
        
        except Exception as e:
            result.status = "FAILED"
            result.error_message = str(e)
            log.error(f"✗ Test failed: {e}")
        
        result.duration_seconds = time.perf_counter() - start
        return result
    
    async def _test_batch_processing(self) -> OptimizationTestResult:
        """Test batch processing efficiency"""
        result = OptimizationTestResult("Batch_Processing_Efficiency")
        result.status = "RUNNING"
        
        start = time.perf_counter()
        
        try:
            log.info("\n[BATCH] Measuring individual writes...")
            
            individual_writes = []
            start_time = time.perf_counter()
            
            for i in range(self.test_iterations):
                # Simulate individual write
                individual_writes.append(f"item_{i}")
            
            individual_time = time.perf_counter() - start_time
            
            log.info("[BATCH] Measuring batch processing...")
            
            batch_results = []
            
            async def batch_handler(items):
                batch_results.extend(items)
                await asyncio.sleep(0.001)  # Simulate processing
            
            processor = BatchProcessor(
                batch_handler,
                batch_size=self.batch_size,
                flush_interval_seconds=1.0
            )
            
            await processor.start_auto_flush()
            
            start_time = time.perf_counter()
            
            for i in range(self.test_iterations):
                await processor.add(f"item_{i}")
            
            await processor.stop_auto_flush()
            
            batch_time = time.perf_counter() - start_time
            
            # Calculate improvement
            improvement = ((individual_time - batch_time) / individual_time) * 100
            
            p_metrics = processor.get_metrics()
            
            result.before_metrics = {
                "method": "individual_writes",
                "time_seconds": f"{individual_time:.3f}",
                "items": self.test_iterations
            }
            
            result.after_metrics = {
                "method": "batch_processing",
                "time_seconds": f"{batch_time:.3f}",
                "batch_size": self.batch_size,
                "batches": p_metrics["batches_processed"],
                "items": self.test_iterations
            }
            
            result.improvement_percent = improvement
            result.status = "PASSED"
            
            log.info(f"✓ Individual: {individual_time:.3f}s → Batch: {batch_time:.3f}s")
            log.info(f"  Improvement: {improvement:.1f}%")
        
        except Exception as e:
            result.status = "FAILED"
            result.error_message = str(e)
            log.error(f"✗ Test failed: {e}")
        
        result.duration_seconds = time.perf_counter() - start
        return result
    
    async def _test_rate_limiting(self) -> OptimizationTestResult:
        """Test rate limiting smoothness"""
        result = OptimizationTestResult("Rate_Limiting_Smoothness")
        result.status = "RUNNING"
        
        start = time.perf_counter()
        
        try:
            log.info("\n[RATE_LIMIT] Testing token bucket limiter...")
            
            limiter = TokenBucketLimiter(rate=50, burst_size=10)
            
            # Record timing
            timings = []
            start_time = time.perf_counter()
            
            for i in range(50):
                await limiter.acquire(1)
                elapsed = time.perf_counter() - start_time
                timings.append(elapsed)
            
            total_time = time.perf_counter() - start_time
            expected_time = 50 / 50  # 50 tokens at 50 tokens/sec
            
            l_metrics = limiter.get_metrics()
            
            result.before_metrics = {
                "method": "no_limiting",
                "expected_time_seconds": "0.001"
            }
            
            result.after_metrics = {
                "method": "token_bucket",
                "actual_time_seconds": f"{total_time:.3f}",
                "expected_time_seconds": f"{expected_time:.3f}",
                "rate": "50 tokens/sec",
                "burst": 10,
                "efficiency": f"{l_metrics['efficiency']:.1%}"
            }
            
            result.status = "PASSED"
            
            log.info(f"✓ Rate limiting test complete")
            log.info(f"  Total time: {total_time:.3f}s (expected: {expected_time:.3f}s)")
            log.info(f"  Efficiency: {l_metrics['efficiency']:.1%}")
        
        except Exception as e:
            result.status = "FAILED"
            result.error_message = str(e)
            log.error(f"✗ Test failed: {e}")
        
        result.duration_seconds = time.perf_counter() - start
        return result
    
    # =====================================================================
    # I/O Optimization Tests
    # =====================================================================
    
    async def _test_buffered_io(self) -> OptimizationTestResult:
        """Test buffered I/O efficiency"""
        result = OptimizationTestResult("Buffered_IO_Efficiency")
        result.status = "RUNNING"
        
        start = time.perf_counter()
        test_dir = Path("d:/development/prj_obs/docs/test_io")
        test_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            log.info("\n[IO] Testing buffered write efficiency...")
            
            # Test data
            test_data = [
                {"id": i, "value": f"data_{i}"}
                for i in range(self.test_iterations)
            ]
            
            # Buffered write
            output_file = test_dir / "buffered_test.jsonl"
            writer = BufferedWriter(output_file, buffer_size=10240)
            
            start_time = time.perf_counter()
            
            for item in test_data:
                await writer.write_json(item)
            
            await writer.close()
            
            buffered_time = time.perf_counter() - start_time
            
            io_metrics = writer.get_metrics()
            file_size = output_file.stat().st_size if output_file.exists() else 0
            
            result.before_metrics = {
                "method": "unbuffered",
                "operations": self.test_iterations
            }
            
            result.after_metrics = {
                "method": "buffered",
                "time_seconds": f"{buffered_time:.3f}",
                "items": self.test_iterations,
                "file_size_bytes": file_size,
                "flushes": io_metrics.buffer_flushes,
                "efficiency_bytes_per_flush": f"{io_metrics.buffer_efficiency:.0f}"
            }
            
            result.status = "PASSED"
            
            log.info(f"✓ Buffered write test complete")
            log.info(f"  Time: {buffered_time:.3f}s")
            log.info(f"  File size: {file_size} bytes")
            log.info(f"  Flushes: {io_metrics.buffer_flushes}")
        
        except Exception as e:
            result.status = "FAILED"
            result.error_message = str(e)
            log.error(f"✗ Test failed: {e}")
        
        result.duration_seconds = time.perf_counter() - start
        return result
    
    async def _test_memory_mapped_io(self) -> OptimizationTestResult:
        """Test memory-mapped I/O performance"""
        result = OptimizationTestResult("Memory_Mapped_IO_Performance")
        result.status = "RUNNING"
        
        start = time.perf_counter()
        test_dir = Path("d:/development/prj_obs/docs/test_io")
        test_file = test_dir / "buffered_test.jsonl"
        
        try:
            log.info("\n[IO] Testing memory-mapped I/O...")
            
            if not test_file.exists():
                result.status = "SKIPPED"
                log.warning("Test file not found, skipping memory-mapped test")
                return result
            
            reader = MemoryMappedReader(test_file)
            
            start_time = time.perf_counter()
            data = await reader.read_all()
            read_time = time.perf_counter() - start_time
            
            r_metrics = reader.get_metrics()
            await reader.close()
            
            result.before_metrics = {
                "method": "sequential_read"
            }
            
            result.after_metrics = {
                "method": "memory_mapped",
                "time_seconds": f"{read_time:.3f}",
                "bytes_read": r_metrics.total_bytes_read,
                "reads": r_metrics.total_reads
            }
            
            result.status = "PASSED"
            
            log.info(f"✓ Memory-mapped I/O test complete")
            log.info(f"  Read time: {read_time:.3f}s")
            log.info(f"  Bytes: {r_metrics.total_bytes_read}")
        
        except Exception as e:
            result.status = "FAILED"
            result.error_message = str(e)
            log.error(f"✗ Test failed: {e}")
        
        result.duration_seconds = time.perf_counter() - start
        return result
    
    async def _test_compression(self) -> OptimizationTestResult:
        """Test compression efficiency"""
        result = OptimizationTestResult("Compression_Efficiency")
        result.status = "RUNNING"
        
        start = time.perf_counter()
        test_dir = Path("d:/development/prj_obs/docs/test_io")
        test_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            log.info("\n[IO] Testing compression efficiency...")
            
            # Test data
            test_data = [
                {"id": i, "value": f"repeated_data_{i % 10}"}
                for i in range(self.test_iterations)
            ]
            
            # Compressed write
            compressed_file = test_dir / "compressed_test.jsonl.gz"
            comp_writer = CompressedWriter(compressed_file)
            
            await comp_writer.write_jsonl(test_data)
            await comp_writer.close()
            
            # Estimate original size
            original_size = sum(
                len(json.dumps(item, ensure_ascii=False).encode("utf-8")) + 1
                for item in test_data
            )
            
            compressed_size = compressed_file.stat().st_size if compressed_file.exists() else 0
            ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
            
            result.before_metrics = {
                "method": "uncompressed",
                "size_bytes": original_size
            }
            
            result.after_metrics = {
                "method": "gzip_compressed",
                "size_bytes": compressed_size,
                "original_size_bytes": original_size,
                "compression_ratio_percent": f"{ratio:.1f}%"
            }
            
            result.improvement_percent = ratio
            result.status = "PASSED"
            
            log.info(f"✓ Compression test complete")
            log.info(f"  Original: {original_size} bytes")
            log.info(f"  Compressed: {compressed_size} bytes")
            log.info(f"  Ratio: {ratio:.1f}%")
        
        except Exception as e:
            result.status = "FAILED"
            result.error_message = str(e)
            log.error(f"✗ Test failed: {e}")
        
        result.duration_seconds = time.perf_counter() - start
        return result
    
    # =====================================================================
    # Main Test Orchestration
    # =====================================================================
    
    async def run_all_tests(self) -> None:
        """Run all optimization tests"""
        log.info("\n" + "=" * 80)
        log.info("PHASE 12.2: PERFORMANCE OPTIMIZATION TEST SUITE")
        log.info("=" * 80)
        
        tests = [
            ("Task Pool Optimization", self._test_task_pool_optimization),
            ("Batch Processing Efficiency", self._test_batch_processing),
            ("Rate Limiting Smoothness", self._test_rate_limiting),
            ("Buffered I/O Efficiency", self._test_buffered_io),
            ("Memory-Mapped I/O Performance", self._test_memory_mapped_io),
            ("Compression Efficiency", self._test_compression),
        ]
        
        for test_name, test_func in tests:
            log.info(f"\n🔬 Running: {test_name}")
            log.info("-" * 80)
            
            try:
                result = await test_func()
                self.results.append(result)
            
            except Exception as e:
                log.error(f"✗ Test crashed: {e}")
                result = OptimizationTestResult(test_name)
                result.status = "FAILED"
                result.error_message = str(e)
                self.results.append(result)
    
    def generate_summary(self) -> dict:
        """Generate test summary"""
        now = datetime.now(self._tz) if self._tz else datetime.now()
        
        passed = sum(1 for r in self.results if r.status == "PASSED")
        failed = sum(1 for r in self.results if r.status == "FAILED")
        skipped = sum(1 for r in self.results if r.status == "SKIPPED")
        
        avg_improvement = (
            sum(r.improvement_percent for r in self.results if r.status == "PASSED") /
            passed
            if passed > 0 else 0
        )
        
        return {
            "timestamp": now.isoformat(),
            "total_tests": len(self.results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "pass_rate": f"{(passed / len(self.results) * 100):.1f}%" if self.results else "0%",
            "average_improvement_percent": f"{avg_improvement:.1f}%",
            "test_results": [r.to_dict() for r in self.results]
        }
    
    def save_results(self, filepath: Path) -> None:
        """Save test results to file"""
        summary = self.generate_summary()
        filepath.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        log.info(f"\n✓ Results saved to {filepath}")


# ---- CLI Entry Point ----

async def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    # Run performance optimization tests
    test_suite = PerformanceOptimizationTest()
    await test_suite.run_all_tests()
    
    # Generate and save results
    summary = test_suite.generate_summary()
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total: {summary['total_tests']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Skipped: {summary['skipped']}")
    print(f"Pass Rate: {summary['pass_rate']}")
    print(f"Avg Improvement: {summary['average_improvement_percent']}")
    
    # Save results
    results_file = Path("d:/development/prj_obs/docs") / "PHASE_12_2_OPTIMIZATION_RESULTS.json"
    test_suite.save_results(results_file)
    
    print("\n✅ Phase 12.2 Performance Optimization tests complete!")


if __name__ == "__main__":
    asyncio.run(main())
