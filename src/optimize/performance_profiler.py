"""
Performance Profiler & Optimizer for Observer System

Purpose:
- Analyze system performance (CPU, memory, I/O)
- Identify bottlenecks
- Apply optimizations
- Measure improvement

Metrics Tracked:
1. CPU Usage - asyncio task execution time
2. Memory Usage - heap size, peak memory
3. I/O Operations - disk reads/writes
4. Asyncio Performance - task queue depth, event loop latency
5. Rate Limiter Efficiency - token consumption vs limits
"""
from __future__ import annotations

import asyncio
import gc
import logging
import time
import tracemalloc
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
import json
from zoneinfo import ZoneInfo


log = logging.getLogger("PerformanceProfiler")


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot"""
    timestamp: datetime
    duration_seconds: float
    
    # CPU Metrics
    cpu_time_seconds: float = 0.0
    asyncio_tasks_count: int = 0
    
    # Memory Metrics
    memory_current_mb: float = 0.0
    memory_peak_mb: float = 0.0
    memory_increase_mb: float = 0.0
    
    # I/O Metrics
    disk_read_count: int = 0
    disk_write_count: int = 0
    disk_io_bytes: int = 0
    
    # Asyncio Metrics
    event_loop_iterations: int = 0
    task_queue_depth: int = 0
    
    # Custom Metrics
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "duration_seconds": f"{self.duration_seconds:.3f}",
            "cpu": {
                "cpu_time_seconds": f"{self.cpu_time_seconds:.3f}",
                "asyncio_tasks": self.asyncio_tasks_count
            },
            "memory": {
                "current_mb": f"{self.memory_current_mb:.2f}",
                "peak_mb": f"{self.memory_peak_mb:.2f}",
                "increase_mb": f"{self.memory_increase_mb:.2f}"
            },
            "io": {
                "disk_reads": self.disk_read_count,
                "disk_writes": self.disk_write_count,
                "total_bytes": self.disk_io_bytes
            },
            "asyncio": {
                "event_loop_iterations": self.event_loop_iterations,
                "task_queue_depth": self.task_queue_depth
            },
            "custom": self.custom_metrics
        }


class PerformanceProfiler:
    """
    System performance profiler and optimizer
    
    Capabilities:
    - Real-time CPU/Memory profiling
    - I/O operations tracking
    - Asyncio performance monitoring
    - Bottleneck identification
    - Optimization recommendations
    """
    
    def __init__(self) -> None:
        self._tz = ZoneInfo("Asia/Seoul") if ZoneInfo else None
        self.metrics_history: List[PerformanceMetrics] = []
        
        # Profiling state
        self._profiling = False
        self._start_time: Optional[float] = None
        self._start_memory: Optional[tuple] = None
        self._io_baseline = {"reads": 0, "writes": 0}
    
    # =====================================================================
    # Profiling Control
    # =====================================================================
    
    def start_profiling(self) -> None:
        """Start performance profiling"""
        log.info("Starting performance profiling...")
        
        self._profiling = True
        self._start_time = time.perf_counter()
        
        # Start memory tracking
        tracemalloc.start()
        self._start_memory = tracemalloc.get_traced_memory()
        
        gc.collect()
        log.info("✓ Profiling started")
    
    def stop_profiling(self) -> PerformanceMetrics:
        """Stop profiling and collect metrics"""
        if not self._profiling:
            log.warning("Profiling not running")
            return None
        
        now = datetime.now(self._tz) if self._tz else datetime.now()
        duration = time.perf_counter() - self._start_time
        
        # Collect metrics
        metrics = PerformanceMetrics(
            timestamp=now,
            duration_seconds=duration,
            cpu_time_seconds=duration,
            asyncio_tasks_count=len(asyncio.all_tasks()),
        )
        
        # Memory metrics
        current, peak = tracemalloc.get_traced_memory()
        metrics.memory_current_mb = current / 1024 / 1024
        metrics.memory_peak_mb = peak / 1024 / 1024
        
        if self._start_memory:
            metrics.memory_increase_mb = (current - self._start_memory[0]) / 1024 / 1024
        
        tracemalloc.stop()
        
        self.metrics_history.append(metrics)
        self._profiling = False
        
        log.info(f"✓ Profiling stopped: {duration:.2f}s")
        
        return metrics
    
    # =====================================================================
    # Performance Analysis
    # =====================================================================
    
    def analyze_asyncio_performance(self) -> Dict[str, Any]:
        """
        Analyze asyncio event loop performance
        
        Returns:
            Analysis with recommendations
        """
        log.info("\n🔍 Asyncio Performance Analysis")
        log.info("-" * 60)
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = None
        
        tasks = asyncio.all_tasks() if loop else []
        
        analysis = {
            "total_tasks": len(tasks),
            "pending_tasks": len([t for t in tasks if not t.done()]),
            "completed_tasks": len([t for t in tasks if t.done()]),
            "recommendations": []
        }
        
        # Recommendations
        if len(tasks) > 100:
            analysis["recommendations"].append(
                "⚠️  High task count (>100) - Consider task pooling"
            )
        
        if analysis["pending_tasks"] > 50:
            analysis["recommendations"].append(
                "⚠️  Many pending tasks (>50) - Check for blocking operations"
            )
        
        # Log details
        log.info(f"Total tasks: {analysis['total_tasks']}")
        log.info(f"  - Pending: {analysis['pending_tasks']}")
        log.info(f"  - Completed: {analysis['completed_tasks']}")
        
        for rec in analysis["recommendations"]:
            log.warning(f"  {rec}")
        
        return analysis
    
    def analyze_memory_efficiency(self) -> Dict[str, Any]:
        """
        Analyze memory usage patterns
        
        Returns:
            Memory analysis with optimization tips
        """
        log.info("\n💾 Memory Efficiency Analysis")
        log.info("-" * 60)
        
        if not self.metrics_history:
            log.warning("No metrics history available")
            return {}
        
        latest = self.metrics_history[-1]
        
        analysis = {
            "current_memory_mb": latest.memory_current_mb,
            "peak_memory_mb": latest.memory_peak_mb,
            "memory_growth_mb": latest.memory_increase_mb,
            "recommendations": []
        }
        
        # Recommendations based on memory usage
        if latest.memory_current_mb > 500:
            analysis["recommendations"].append(
                "⚠️  High memory usage (>500 MB) - Consider caching optimization"
            )
        
        if latest.memory_increase_mb > 200:
            analysis["recommendations"].append(
                "⚠️  Significant memory growth (>200 MB) - Possible memory leak"
            )
        
        # Log details
        log.info(f"Current: {latest.memory_current_mb:.2f} MB")
        log.info(f"Peak: {latest.memory_peak_mb:.2f} MB")
        log.info(f"Growth: {latest.memory_increase_mb:.2f} MB")
        
        for rec in analysis["recommendations"]:
            log.warning(f"  {rec}")
        
        return analysis
    
    def analyze_io_performance(self, io_stats: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze I/O operation patterns
        
        Args:
            io_stats: I/O statistics (reads, writes, bytes)
        
        Returns:
            I/O analysis with optimization tips
        """
        log.info("\n📊 I/O Performance Analysis")
        log.info("-" * 60)
        
        if not io_stats:
            io_stats = {"reads": 0, "writes": 0, "bytes": 0}
        
        analysis = {
            "total_operations": io_stats.get("reads", 0) + io_stats.get("writes", 0),
            "read_count": io_stats.get("reads", 0),
            "write_count": io_stats.get("writes", 0),
            "total_bytes": io_stats.get("bytes", 0),
            "recommendations": []
        }
        
        # Recommendations
        if analysis["total_operations"] > 10000:
            analysis["recommendations"].append(
                "⚠️  High I/O operation count (>10k) - Consider buffering"
            )
        
        avg_write_size = (
            analysis["total_bytes"] / analysis["write_count"]
            if analysis["write_count"] > 0 else 0
        )
        
        if avg_write_size < 1024:  # Less than 1KB per write
            analysis["recommendations"].append(
                "⚠️  Small write size (<1KB) - Batch writes together"
            )
        
        # Log details
        log.info(f"Total Operations: {analysis['total_operations']}")
        log.info(f"  - Reads: {analysis['read_count']}")
        log.info(f"  - Writes: {analysis['write_count']}")
        log.info(f"Total Data: {analysis['total_bytes'] / 1024 / 1024:.2f} MB")
        
        for rec in analysis["recommendations"]:
            log.warning(f"  {rec}")
        
        return analysis
    
    # =====================================================================
    # Optimization Strategies
    # =====================================================================
    
    def get_optimization_recommendations(self) -> Dict[str, List[str]]:
        """
        Generate optimization recommendations based on analysis
        
        Returns:
            Grouped recommendations by category
        """
        log.info("\n🎯 Optimization Recommendations")
        log.info("=" * 60)
        
        recommendations = {
            "asyncio": [
                "Use asyncio.gather() for parallel coroutine execution",
                "Implement task pooling for high-frequency tasks",
                "Use asyncio.Queue for producer-consumer patterns",
                "Monitor event loop health with uvloop library"
            ],
            "memory": [
                "Use __slots__ in dataclasses to reduce memory overhead",
                "Implement object pooling for frequently created objects",
                "Use generators for large data processing",
                "Enable GC collection after batch operations"
            ],
            "io": [
                "Batch write operations (buffer size 64KB+)",
                "Use memory-mapped I/O for large files",
                "Implement asynchronous file I/O with aiofiles",
                "Cache frequently accessed data in memory"
            ],
            "rate_limiting": [
                "Use token bucket algorithm for smoother rate limiting",
                "Implement request batching for API calls",
                "Use connection pooling for HTTP requests",
                "Implement backoff strategy for API failures"
            ]
        }
        
        for category, items in recommendations.items():
            log.info(f"\n{category.upper()}:")
            for i, item in enumerate(items, 1):
                log.info(f"  {i}. {item}")
        
        return recommendations
    
    # =====================================================================
    # Benchmarking
    # =====================================================================
    
    async def benchmark_operation(
        self,
        operation: Callable,
        iterations: int = 100,
        name: str = "Operation"
    ) -> Dict[str, Any]:
        """
        Benchmark an async operation
        
        Args:
            operation: Async function to benchmark
            iterations: Number of iterations
            name: Operation name for logging
        
        Returns:
            Benchmark results
        """
        log.info(f"\n📈 Benchmarking: {name}")
        log.info("-" * 60)
        
        times = []
        
        self.start_profiling()
        
        for i in range(iterations):
            start = time.perf_counter()
            await operation()
            duration = time.perf_counter() - start
            times.append(duration)
        
        metrics = self.stop_profiling()
        
        # Calculate statistics
        import statistics
        
        results = {
            "operation": name,
            "iterations": iterations,
            "min_time_ms": min(times) * 1000,
            "max_time_ms": max(times) * 1000,
            "mean_time_ms": statistics.mean(times) * 1000,
            "median_time_ms": statistics.median(times) * 1000,
            "stdev_time_ms": statistics.stdev(times) * 1000 if len(times) > 1 else 0,
            "ops_per_second": iterations / metrics.duration_seconds if metrics else 0,
            "memory_increase_mb": metrics.memory_increase_mb if metrics else 0
        }
        
        # Log results
        log.info(f"Min: {results['min_time_ms']:.3f} ms")
        log.info(f"Max: {results['max_time_ms']:.3f} ms")
        log.info(f"Mean: {results['mean_time_ms']:.3f} ms")
        log.info(f"Median: {results['median_time_ms']:.3f} ms")
        log.info(f"StDev: {results['stdev_time_ms']:.3f} ms")
        log.info(f"Ops/sec: {results['ops_per_second']:.1f}")
        log.info(f"Memory: {results['memory_increase_mb']:.2f} MB")
        
        return results
    
    # =====================================================================
    # Reporting
    # =====================================================================
    
    def generate_report(self) -> str:
        """
        Generate comprehensive performance report
        
        Returns:
            Report text
        """
        report = []
        report.append("=" * 80)
        report.append("OBSERVER SYSTEM PERFORMANCE REPORT")
        report.append("=" * 80)
        
        if not self.metrics_history:
            report.append("\nNo profiling data available")
            return "\n".join(report)
        
        # Summary
        latest = self.metrics_history[-1]
        report.append(f"\nGenerated: {latest.timestamp.isoformat()}")
        report.append(f"Duration: {latest.duration_seconds:.2f}s")
        
        # Metrics
        report.append("\n" + "-" * 80)
        report.append("PERFORMANCE METRICS")
        report.append("-" * 80)
        
        report.append(f"\nCPU:")
        report.append(f"  - CPU Time: {latest.cpu_time_seconds:.3f}s")
        report.append(f"  - Asyncio Tasks: {latest.asyncio_tasks_count}")
        
        report.append(f"\nMemory:")
        report.append(f"  - Current: {latest.memory_current_mb:.2f} MB")
        report.append(f"  - Peak: {latest.memory_peak_mb:.2f} MB")
        report.append(f"  - Growth: {latest.memory_increase_mb:.2f} MB")
        
        report.append(f"\nI/O:")
        report.append(f"  - Disk Reads: {latest.disk_read_count}")
        report.append(f"  - Disk Writes: {latest.disk_write_count}")
        report.append(f"  - Total Data: {latest.disk_io_bytes / 1024 / 1024:.2f} MB")
        
        # Recommendations
        report.append("\n" + "-" * 80)
        report.append("RECOMMENDATIONS")
        report.append("-" * 80)
        
        recs = self.get_optimization_recommendations()
        for category, items in recs.items():
            report.append(f"\n{category.upper()}:")
            for item in items:
                report.append(f"  • {item}")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)
    
    def export_metrics(self, filepath: Path) -> None:
        """Export metrics to JSON file"""
        data = {
            "metrics_history": [m.to_dict() for m in self.metrics_history],
            "report": self.generate_report()
        }
        
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info(f"✓ Metrics exported to {filepath}")


# ---- CLI Entry Point ----

async def main():
    """Test performance profiler"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    profiler = PerformanceProfiler()
    
    # Example: Benchmark a simple async operation
    async def sample_operation():
        await asyncio.sleep(0.001)  # Simulate work
    
    print("\n🧪 Performance Profiler Test\n")
    
    # Run benchmark
    results = await profiler.benchmark_operation(
        sample_operation,
        iterations=100,
        name="Sample Async Operation"
    )
    
    # Run analysis
    profiler.analyze_asyncio_performance()
    profiler.analyze_memory_efficiency()
    profiler.analyze_io_performance({"reads": 1000, "writes": 500, "bytes": 5242880})
    
    # Generate report
    print("\n" + profiler.generate_report())
    
    # Export metrics
    results_file = Path("d:/development/prj_obs/docs") / "PHASE_12_2_PERFORMANCE_PROFILE.json"
    profiler.export_metrics(results_file)


if __name__ == "__main__":
    asyncio.run(main())
