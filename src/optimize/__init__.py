"""
Optimization Module

Submodules:
- performance_profiler: CPU, memory, I/O profiling
- asyncio_optimizer: Task pool, batch processing, rate limiting
- io_optimizer: Buffered I/O, memory-mapped files, compression
- test_performance_optimization: Integration tests
"""

from .performance_profiler import (
    PerformanceProfiler,
    PerformanceMetrics
)

from .asyncio_optimizer import (
    TaskPool,
    TaskPoolConfig,
    BatchProcessor,
    TokenBucketLimiter
)

from .io_optimizer import (
    BufferedWriter,
    MemoryMappedReader,
    CompressedWriter
)

__all__ = [
    # Performance Profiler
    "PerformanceProfiler",
    "PerformanceMetrics",
    
    # Asyncio Optimization
    "TaskPool",
    "TaskPoolConfig",
    "BatchProcessor",
    "TokenBucketLimiter",
    
    # I/O Optimization
    "BufferedWriter",
    "MemoryMappedReader",
    "CompressedWriter",
]
