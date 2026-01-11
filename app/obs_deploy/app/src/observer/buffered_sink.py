# src/ops/observer/buffered_sink.py

from __future__ import annotations

import logging
from typing import Optional, Dict, Any

from .buffer_flush import BufferConfig, SnapshotBuffer
from .pattern_record import PatternRecord
from .log_rotation import RotationConfig, RotationManager
from .usage_metrics import UsageMetricsCollector
from .event_bus import SnapshotSink
from paths import observer_asset_file

logger = logging.getLogger(__name__)

# ============================================================
# Buffered File Sink
# ============================================================

class BufferedJsonlFileSink(SnapshotSink):
    """
    Buffered JsonlFileSink that uses time-based flushing.
    
    This sink:
    - Accepts PatternRecords immediately (non-blocking)
    - Buffers records in memory
    - Flushes to disk at configurable time intervals
    - Maintains compatibility with existing EventBus interface
    - Supports time-based log rotation (Task 04)
    - Collects usage metrics for cost observability (Task 05)
    """
    
    def __init__(
        self,
        filename: str = "observer.jsonl",
        *,
        flush_interval_ms: float = 1000.0,
        max_buffer_size: int = 10000,
        enable_buffering: bool = True,
        rotation_config: Optional[RotationConfig] = None,
    ) -> None:
        """
        Initialize buffered sink with configuration.
        
        Args:
            filename: Output JSONL filename (used only if rotation is disabled)
            flush_interval_ms: Time-based flush interval in milliseconds
            max_buffer_size: Maximum buffer size (safety limit)
            enable_buffering: Enable/disable buffering
            rotation_config: Time-based rotation configuration (optional)
        """
        self.filename = filename
        self.file_path = observer_asset_file(filename)
        
        # Create buffer configuration
        self._config = BufferConfig(
            flush_interval_ms=flush_interval_ms,
            max_buffer_size=max_buffer_size,
            enable_buffering=enable_buffering,
        )
        
        # Rotation setup
        if rotation_config is not None:
            from .log_rotation import validate_rotation_config
            validate_rotation_config(rotation_config)
            self._rotation_manager = RotationManager(rotation_config)
        else:
            self._rotation_manager = None
        
        # Usage metrics (Task 05)
        self._metrics_collector: Optional[UsageMetricsCollector] = None
        
        # Initialize buffer
        self._buffer: Optional[SnapshotBuffer] = None
        self._started = False
    
    def start(self) -> None:
        """Start the buffered sink."""
        if self._started:
            return
        
        self._buffer = SnapshotBuffer(
            self._config, 
            str(self.file_path),
            rotation_manager=self._rotation_manager,
            metrics_collector=self._metrics_collector
        )
        self._buffer.start()
        self._started = True
        
        logger.info(
            "BufferedJsonlFileSink started",
            extra={
                "sink_filename": self.filename,
                "file_path": str(self.file_path),
                "flush_interval_ms": self._config.flush_interval_ms,
                "enable_buffering": self._config.enable_buffering,
                "rotation_enabled": self._rotation_manager is not None,
                "rotation_window_ms": self._rotation_manager._config.window_ms if self._rotation_manager else None,
                "usage_metrics_enabled": self._metrics_collector is not None,
            },
        )
    
    def stop(self) -> None:
        """Stop the buffered sink and flush remaining records."""
        if not self._started or self._buffer is None:
            return
        
        self._buffer.stop()
        self._started = False
        
        logger.info(
            "BufferedJsonlFileSink stopped",
            extra={"sink_filename": self.filename},
        )
    
    def set_metrics_collector(self, collector: UsageMetricsCollector) -> None:
        """Set the usage metrics collector (Task 05)."""
        self._metrics_collector = collector
        
        # If buffer is already running, update it too
        if self._buffer is not None and hasattr(self._buffer, 'set_metrics_collector'):
            self._buffer.set_metrics_collector(collector)
    
    def publish(self, record: PatternRecord) -> None:
        """
        Publish a PatternRecord to the buffer.
        
        This method is non-blocking and returns immediately.
        """
        if not self._started or self._buffer is None:
            # Auto-start if not started
            self.start()
        
        try:
            self._buffer.add_record(record)
        except Exception:
            logger.exception(
                "Failed to add record to buffer",
                extra={"sink_filename": self.filename},
            )
    
    def get_buffer_stats(self) -> dict:
        """Get current buffer statistics."""
        if not self._started or self._buffer is None:
            return {"running": False}
        
        stats = self._buffer.get_buffer_stats()
        
        # Add rotation stats if available
        if self._rotation_manager is not None:
            stats["rotation"] = self._rotation_manager.get_rotation_stats()
        else:
            stats["rotation"] = {"rotation_enabled": False}
        
        return stats
    
    def get_rotation_stats(self) -> dict:
        """Get current rotation statistics for monitoring."""
        if self._rotation_manager is None:
            return {"rotation_enabled": False}
        
        return self._rotation_manager.get_rotation_stats()
