# src/ops/observer/usage_metrics.py

from __future__ import annotations

import json
import logging
import time
import threading
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque

from .snapshot import utc_now_ms

logger = logging.getLogger(__name__)


# ============================================================
# Usage Metrics Configuration
# ============================================================

@dataclass(frozen=True)
class UsageMetricsConfig:
    """Configuration for usage measurement."""
    
    # Time window for aggregation (milliseconds)
    window_ms: int = 60_000  # 1 minute default
    
    # Enable/disable metrics collection
    enable_metrics: bool = True
    
    # Metrics output format: 'json' | 'structured_log'
    output_format: str = 'json'
    
    # Output file for metrics (None for log-only)
    metrics_file: Optional[str] = None
    
    # Maximum history windows to keep in memory
    max_history_windows: int = 1440  # 24 hours at 1-minute windows


# ============================================================
# Metrics Data Structures
# ============================================================

@dataclass
class WindowMetrics:
    """Metrics for a single time window."""
    
    window_start_ms: int
    window_end_ms: int
    
    # Snapshot metrics
    snapshots_count: int = 0
    snapshots_tick_count: int = 0
    snapshots_loop_count: int = 0
    
    # Latency metrics (in milliseconds)
    latency_sum_ms: float = 0.0
    latency_count: int = 0
    min_latency_ms: Optional[float] = None
    max_latency_ms: Optional[float] = None
    
    # Buffer metrics
    flush_count: int = 0
    buffer_depth_sum: float = 0.0
    buffer_depth_count: int = 0
    max_buffer_depth: int = 0
    
    # Rotation metrics
    files_rotated: int = 0
    
    # I/O metrics
    bytes_written: int = 0
    records_written: int = 0
    
    def add_latency(self, latency_ms: float) -> None:
        """Add a latency measurement."""
        self.latency_sum_ms += latency_ms
        self.latency_count += 1
        
        if self.min_latency_ms is None or latency_ms < self.min_latency_ms:
            self.min_latency_ms = latency_ms
        if self.max_latency_ms is None or latency_ms > self.max_latency_ms:
            self.max_latency_ms = latency_ms
    
    def add_buffer_depth(self, depth: int) -> None:
        """Add a buffer depth measurement."""
        self.buffer_depth_sum += depth
        self.buffer_depth_count += 1
        
        if depth > self.max_buffer_depth:
            self.max_buffer_depth = depth
    
    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency."""
        return self.latency_sum_ms / max(1, self.latency_count)
    
    @property
    def avg_buffer_depth(self) -> float:
        """Calculate average buffer depth."""
        return self.buffer_depth_sum / max(1, self.buffer_depth_count)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "window_start_ms": self.window_start_ms,
            "window_end_ms": self.window_end_ms,
            "snapshots_per_minute": self.snapshots_count,
            "snapshots_tick_per_minute": self.snapshots_tick_count,
            "snapshots_loop_per_minute": self.snapshots_loop_count,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "min_latency_ms": self.min_latency_ms,
            "max_latency_ms": self.max_latency_ms,
            "flush_count_per_window": self.flush_count,
            "avg_buffer_depth": round(self.avg_buffer_depth, 2),
            "max_buffer_depth": self.max_buffer_depth,
            "files_rotated_per_window": self.files_rotated,
            "bytes_written_per_window": self.bytes_written,
            "records_written_per_window": self.records_written,
        }


# ============================================================
# Usage Metrics Collector
# ============================================================

class UsageMetricsCollector:
    """
    Lightweight usage metrics collector for Observer.
    
    This collector:
    - Aggregates metrics per time window
    - Emits metrics as logs or structured output
    - Does NOT influence behavior (record-only)
    - Thread-safe for concurrent access
    """
    
    def __init__(self, config: UsageMetricsConfig) -> None:
        self._config = config
        self._current_window: Optional[WindowMetrics] = None
        self._history: deque = deque(maxlen=config.max_history_windows)
        self._lock = threading.RLock()
        self._last_window_start_ms = 0
        
        # Counters for ongoing operations
        self._total_snapshots = 0
        self._total_bytes_written = 0
        self._start_time_ms = utc_now_ms()
        
        logger.info("UsageMetricsCollector initialized", extra={
            "window_ms": config.window_ms,
            "enable_metrics": config.enable_metrics,
            "output_format": config.output_format,
        })
    
    def record_snapshot(self, *, is_tick: bool = False, latency_ms: float = 0.0) -> None:
        """Record a snapshot generation."""
        if not self._config.enable_metrics:
            return
        
        with self._lock:
            window = self._get_current_window()
            
            window.snapshots_count += 1
            if is_tick:
                window.snapshots_tick_count += 1
            else:
                window.snapshots_loop_count += 1
            
            if latency_ms > 0:
                window.add_latency(latency_ms)
            
            self._total_snapshots += 1
    
    def record_flush(self, *, buffer_depth: int = 0, bytes_written: int = 0, records_written: int = 0) -> None:
        """Record a buffer flush operation."""
        if not self._config.enable_metrics:
            return
        
        with self._lock:
            window = self._get_current_window()
            
            window.flush_count += 1
            window.bytes_written += bytes_written
            window.records_written += records_written
            
            if buffer_depth >= 0:
                window.add_buffer_depth(buffer_depth)
            
            self._total_bytes_written += bytes_written
    
    def record_rotation(self, *, files_rotated: int = 1) -> None:
        """Record file rotation operations."""
        if not self._config.enable_metrics:
            return
        
        with self._lock:
            window = self._get_current_window()
            window.files_rotated += files_rotated
    
    def record_buffer_depth(self, depth: int) -> None:
        """Record buffer depth measurement."""
        if not self._config.enable_metrics:
            return
        
        with self._lock:
            window = self._get_current_window()
            window.add_buffer_depth(depth)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current aggregated metrics."""
        if not self._config.enable_metrics:
            return {"metrics_enabled": False}
        
        with self._lock:
            current_time_ms = utc_now_ms()
            runtime_ms = current_time_ms - self._start_time_ms
            
            # Get current window if it exists
            current_window_data = {}
            if self._current_window:
                current_window_data = self._current_window.to_dict()
            
            # Calculate overall averages
            total_minutes = max(1, runtime_ms / 60_000)
            snapshots_per_minute = self._total_snapshots / total_minutes
            
            return {
                "metrics_enabled": True,
                "runtime_ms": runtime_ms,
                "total_snapshots": self._total_snapshots,
                "total_bytes_written": self._total_bytes_written,
                "snapshots_per_minute_overall": round(snapshots_per_minute, 2),
                "current_window": current_window_data,
                "history_windows_count": len(self._history),
            }
    
    def emit_window_summary(self, window: WindowMetrics) -> None:
        """Emit a completed window summary as log."""
        if not self._config.enable_metrics:
            return
        
        metrics_data = window.to_dict()
        metrics_data["metric_type"] = "usage_window_summary"
        
        if self._config.output_format == 'json':
            # Emit as structured JSON log
            logger.info("Usage metrics window summary", extra=metrics_data)
        else:
            # Emit as structured log
            logger.info(f"Usage metrics: {json.dumps(metrics_data, ensure_ascii=False)}")
        
        # Also write to metrics file if configured
        if self._config.metrics_file:
            try:
                with open(self._config.metrics_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(metrics_data, ensure_ascii=False) + '\n')
            except Exception:
                logger.exception("Failed to write metrics to file", 
                               extra={"metrics_file": self._config.metrics_file})
    
    def _get_current_window(self) -> WindowMetrics:
        """Get or create the current time window."""
        current_time_ms = utc_now_ms()
        
        # Calculate window start time
        window_start_ms = (current_time_ms // self._config.window_ms) * self._config.window_ms
        window_end_ms = window_start_ms + self._config.window_ms
        
        # Check if we need a new window
        if (self._current_window is None or 
            window_start_ms != self._current_window.window_start_ms):
            
            # Emit previous window if it exists
            if self._current_window is not None:
                self.emit_window_summary(self._current_window)
                self._history.append(self._current_window)
            
            # Create new window
            self._current_window = WindowMetrics(
                window_start_ms=window_start_ms,
                window_end_ms=window_end_ms
            )
        
        return self._current_window
    
    def finalize(self) -> None:
        """Finalize metrics collection (emit final window)."""
        if not self._config.enable_metrics:
            return
        
        with self._lock:
            if self._current_window is not None:
                self.emit_window_summary(self._current_window)
                self._history.append(self._current_window)
                self._current_window = None
            
            # Emit final summary
            final_metrics = self.get_current_metrics()
            final_metrics["metric_type"] = "usage_final_summary"
            
            logger.info("Usage metrics final summary", extra=final_metrics)


# ============================================================
# Factory Functions
# ============================================================

def create_usage_metrics_collector(
    window_ms: int = 60_000,
    enable_metrics: bool = True,
    output_format: str = 'json',
    metrics_file: Optional[str] = None,
) -> UsageMetricsCollector:
    """Create a usage metrics collector with default configuration."""
    config = UsageMetricsConfig(
        window_ms=window_ms,
        enable_metrics=enable_metrics,
        output_format=output_format,
        metrics_file=metrics_file,
    )
    return UsageMetricsCollector(config)


def create_default_usage_metrics() -> UsageMetricsCollector:
    """Create a usage metrics collector with default settings."""
    return create_usage_metrics_collector()
