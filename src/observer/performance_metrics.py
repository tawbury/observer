"""
performance_metrics.py

Internal performance metrics collection for Observer operations.

ROLE & BOUNDARY DECLARATION:
- THIS IS NOT Observer-Core component
- Layer: Utility (Supports Observer but not part of Core)
- Ownership: Ops/Observer utility module
- Access: Internal Observer components ONLY
- Must NOT be accessed: External decision systems, strategy engines

This module provides additive-only performance monitoring that does NOT
influence Observer behavior or decision-making. All metrics are purely
observational and stored internally for external access.

NON-PERSISTENCE DECLARATION:
- Metrics are IN-MEMORY ONLY
- Metrics are RESET on process restart
- NO PERSISTENCE is intended in Task 06
- Persistence decisions are DEFERRED to later tasks

SAFETY CONFIRMATION:
- Metrics do NOT affect Observer behavior
- Metrics do NOT influence decision flow
- Metrics do NOT alter Snapshot/PatternRecord
- Metrics do NOT imply Scalp adaptive behavior

Constraints from Observer_Architecture.md:
- No decision, judgment, or execution logic
- No modification of snapshot processing behavior
- Append-only data collection

Constraints from observer_scalp_task_06_performance_monitoring.md:
- No performance-based decision logic
- No automatic system tuning based on metrics
- Additive field changes only
"""

import time
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from collections import defaultdict, deque
import logging

from shared.timezone import now_kst

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """
    Internal performance metrics container for Observer operations.
    
    ROLE & BOUNDARY:
    - NOT part of Observer-Core
    - Layer: Utility supporting Observer operations
    - Ownership: Internal to Observer module
    - Access: Observer internal components ONLY
    - Must NOT be accessed: External systems, decision engines
    
    All metrics are purely observational and do NOT influence behavior.
    Thread-safe for concurrent access during high-frequency operations.
    
    NON-PERSISTENCE:
    - All metrics are IN-MEMORY ONLY
    - Automatically RESET on process restart
    - No persistence mechanism provided
    """
    
    def __init__(self, max_history: int = 1000):
        self._lock = threading.RLock()
        self._max_history = max_history
        
        # Counters (monotonically increasing)
        self._counters = defaultdict(int)
        
        # Gauges (current values)
        self._gauges = defaultdict(float)
        
        # Timing data (recent history)
        self._timings = defaultdict(lambda: deque(maxlen=max_history))
        
        # Start time for uptime calculation
        self._start_time = time.time()
    
    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a counter metric."""
        with self._lock:
            self._counters[name] += value
    
    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge metric value."""
        with self._lock:
            self._gauges[name] = value
    
    def record_timing(self, name: str, duration_ms: float) -> None:
        """Record a timing measurement in milliseconds."""
        with self._lock:
            self._timings[name].append({
                "duration_ms": duration_ms,
                "timestamp": now_kst().isoformat()
            })
    
    def get_snapshot_count(self) -> int:
        """Get total number of snapshots processed."""
        with self._lock:
            return self._counters["snapshots_processed"]
    
    def get_buffer_depth(self) -> float:
        """Get current buffer depth gauge."""
        with self._lock:
            return self._gauges["buffer_depth"]
    
    def get_uptime_seconds(self) -> float:
        """Get observer uptime in seconds."""
        return time.time() - self._start_time
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive metrics summary for external access.
        
        Returns:
            Dictionary containing all current metrics
        """
        with self._lock:
            # Calculate timing statistics
            timing_stats = {}
            for name, history in self._timings.items():
                if history:
                    durations = [entry["duration_ms"] for entry in history]
                    timing_stats[name] = {
                        "count": len(durations),
                        "latest_ms": durations[-1],
                        "avg_ms": sum(durations) / len(durations),
                        "min_ms": min(durations),
                        "max_ms": max(durations)
                    }
            
            return {
                "timestamp": now_kst().isoformat(),
                "uptime_seconds": self.get_uptime_seconds(),
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "timing_stats": timing_stats
            }


# Global metrics instance (singleton pattern for Observer)
_global_metrics: Optional[PerformanceMetrics] = None


def get_metrics() -> PerformanceMetrics:
    """
    Get the global performance metrics instance.
    
    NON-PERSISTENCE: Returns in-memory metrics that reset on process restart.
    """
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = PerformanceMetrics()
    return _global_metrics


def reset_metrics() -> None:
    """
    Reset global metrics instance (for testing only).
    
    NON-PERSISTENCE: Demonstrates that metrics are not persistent.
    """
    global _global_metrics
    _global_metrics = None


class LatencyTimer:
    """
    Context manager for measuring operation latency.
    
    ROLE & BOUNDARY:
    - NOT Observer-Core component
    - Layer: Utility for performance measurement
    - Ownership: Observer internal use ONLY
    - Access: Observer internal components ONLY
    - Must NOT be used for: Decision timing, strategy execution
    
    SAFETY: Does NOT alter execution path or behavior.
    
    Usage:
        with LatencyTimer("snapshot_processing"):
            # ... operation to measure ...
    """
    
    def __init__(self, metric_name: str):
        self.metric_name = metric_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration_ms = (time.time() - self.start_time) * 1000
            get_metrics().record_timing(self.metric_name, duration_ms)
