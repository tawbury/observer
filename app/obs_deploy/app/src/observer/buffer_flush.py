# observer/buffer_flush.py

from __future__ import annotations

import json
import logging
import threading
import time
from typing import List, Optional
from dataclasses import dataclass, field

from .pattern_record import PatternRecord
from .snapshot import utc_now_ms
from .log_rotation import RotationManager
from .usage_metrics import UsageMetricsCollector
from .performance_metrics import get_metrics, LatencyTimer

logger = logging.getLogger(__name__)


# ============================================================
# Buffer Configuration
# ============================================================

@dataclass(frozen=True)
class BufferConfig:
    """Configuration for time-based buffer flushing."""
    flush_interval_ms: float = 1000.0  # Flush interval in milliseconds
    max_buffer_size: int = 10000      # Maximum buffer size (safety limit)
    enable_buffering: bool = True      # Enable/disable buffering


# ============================================================
# In-Memory Buffer
# ============================================================

@dataclass
class BufferedRecord:
    """A buffered record with metadata."""
    record: PatternRecord
    received_at_ms: int
    buffer_depth_at_time: int


class SnapshotBuffer:
    """
    In-memory buffer for PatternRecords with time-based flushing.
    
    This buffer:
    - Accepts snapshots immediately (non-blocking)
    - Flushes to disk at configurable time intervals
    - Populates buffer_depth and flush_reason metadata
    - Does not block snapshot generation timing
    - Collects usage metrics for cost observability (Task 05)
    """
    
    def __init__(
        self, 
        config: BufferConfig, 
        sink_file_path: str,
        rotation_manager: Optional[RotationManager] = None,
        metrics_collector: Optional[UsageMetricsCollector] = None,
    ) -> None:
        self._config = config
        self._sink_file_path = sink_file_path
        self._rotation_manager = rotation_manager
        self._metrics_collector = metrics_collector
        self._buffer: List[BufferedRecord] = []
        self._lock = threading.RLock()
        self._last_flush_ms = utc_now_ms()
        self._flush_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
    
    def start(self) -> None:
        """Start the buffer and flush thread."""
        if not self._config.enable_buffering:
            logger.info("Buffering disabled, using direct write")
            return
        
        with self._lock:
            if self._running:
                return
            
            self._running = True
            self._stop_event.clear()
            self._flush_thread = threading.Thread(
                target=self._flush_loop,
                name="SnapshotBufferFlush",
                daemon=True,
            )
            self._flush_thread.start()
            
            logger.info(
                "Snapshot buffer started",
                extra={
                    "flush_interval_ms": self._config.flush_interval_ms,
                    "max_buffer_size": self._config.max_buffer_size,
                },
            )
    
    def stop(self) -> None:
        """Stop the buffer and flush remaining records."""
        if not self._running:
            return
        
        with self._lock:
            self._running = False
            self._stop_event.set()
        
        if self._flush_thread and self._flush_thread.is_alive():
            self._flush_thread.join(timeout=5.0)
        
        # Flush any remaining records
        self._flush_remaining()
        
        logger.info("Snapshot buffer stopped")
    
    def add_record(self, record: PatternRecord) -> None:
        """
        Add a record to the buffer (non-blocking).
        
        This method must return immediately and not block snapshot generation.
        """
        if not self._config.enable_buffering:
            # Direct write if buffering is disabled
            self._write_record_direct(record)
            return
        
        current_time_ms = utc_now_ms()
        
        with self._lock:
            buffer_depth = len(self._buffer)
            
            # Create buffered record with metadata
            buffered_record = BufferedRecord(
                record=record,
                received_at_ms=current_time_ms,
                buffer_depth_at_time=buffer_depth,
            )
            
            self._buffer.append(buffered_record)
            
            # Record usage metrics (Task 05)
            if self._metrics_collector:
                self._metrics_collector.record_buffer_depth(buffer_depth)
            
            # Record performance metrics (Task 06)
            # SAFETY: Metrics are purely observational, do NOT affect behavior
            get_metrics().set_gauge("buffer_depth", buffer_depth)
            get_metrics().increment_counter("records_buffered")
            
            # Safety check for buffer size
            if len(self._buffer) >= self._config.max_buffer_size:
                logger.warning(
                    "Buffer size exceeded safety limit, forcing immediate flush",
                    extra={"buffer_size": len(self._buffer), "max_size": self._config.max_buffer_size},
                )
                self._flush_buffer()
    
    def _flush_loop(self) -> None:
        """Background thread loop for time-based flushing."""
        while self._running and not self._stop_event.is_set():
            try:
                current_time_ms = utc_now_ms()
                time_since_last_flush = current_time_ms - self._last_flush_ms
                
                if time_since_last_flush >= self._config.flush_interval_ms:
                    self._flush_buffer()
                
                # Sleep for a short interval to avoid busy waiting
                sleep_time_ms = min(100.0, self._config.flush_interval_ms / 10.0)
                self._stop_event.wait(sleep_time_ms / 1000.0)
                
            except Exception:
                logger.exception("Error in flush loop")
                time.sleep(1.0)  # Back off on error
    
    def _flush_buffer(self) -> None:
        """Flush all buffered records to disk."""
        with LatencyTimer("flush_operation"):
            with self._lock:
                if not self._buffer:
                    return
                
                # Copy buffer and clear it
                records_to_flush = self._buffer.copy()
                buffer_depth = len(self._buffer)
                self._buffer.clear()
                self._last_flush_ms = utc_now_ms()
            
            # Write records outside of lock to minimize blocking
            bytes_written, records_written = self._write_records_to_disk(records_to_flush)
            
            # Record usage metrics (Task 05)
            if self._metrics_collector:
                self._metrics_collector.record_flush(
                    buffer_depth=buffer_depth,
                    bytes_written=bytes_written,
                    records_written=records_written
                )
            
            # Record performance metrics (Task 06)
            # SAFETY: Metrics are purely observational, do NOT affect behavior
            get_metrics().increment_counter("flush_operations")
            get_metrics().increment_counter("records_flushed", records_written)
            get_metrics().set_gauge("buffer_depth", 0)  # Reset after flush
            
            logger.debug(
                "Flush completed",
                extra={"records_flushed": len(records_to_flush)},
            )
    
    def _flush_remaining(self) -> None:
        """Flush any remaining records when stopping."""
        with self._lock:
            if self._buffer:
                records_to_flush = self._buffer.copy()
                self._buffer.clear()
                self._write_records_to_disk(records_to_flush)
                logger.info(
                    "Final flush completed",
                    extra={"records_flushed": len(records_to_flush)},
                )
    
    def _write_records_to_disk(self, buffered_records: List[BufferedRecord]) -> tuple[int, int]:
        """Write buffered records to disk with metadata updates and rotation support.
        
        Returns:
            Tuple of (bytes_written, records_written)
        """
        bytes_written = 0
        records_written = 0
        
        try:
            # Group records by time window if rotation is enabled
            if self._rotation_manager is not None:
                bytes_written, records_written = self._write_records_with_rotation(buffered_records)
            else:
                bytes_written, records_written = self._write_records_to_single_file(buffered_records, self._sink_file_path)
                    
        except Exception:
            logger.exception(
                "Failed to write buffered records to disk",
                extra={"file_path": self._sink_file_path, "record_count": len(buffered_records)},
            )
        
        return bytes_written, records_written
    
    def _write_records_with_rotation(self, buffered_records: List[BufferedRecord]) -> tuple[int, int]:
        """Write records to appropriate files based on rotation time windows.
        
        Returns:
            Tuple of (bytes_written, records_written)
        """
        total_bytes = 0
        total_records = 0
        
        # Group records by their target file based on rotation window
        records_by_file = {}
        
        for buffered_record in buffered_records:
            # Use the record's received time to determine the correct file
            target_file_path = str(self._rotation_manager.get_current_file_path(buffered_record.received_at_ms))
            
            if target_file_path not in records_by_file:
                records_by_file[target_file_path] = []
            
            records_by_file[target_file_path].append(buffered_record)
        
        # Write each group to its respective file
        for file_path, records in records_by_file.items():
            bytes_written, records_written = self._write_records_to_single_file(records, file_path)
            total_bytes += bytes_written
            total_records += records_written
        
        # Record rotation metrics (Task 05)
        if self._metrics_collector and len(records_by_file) > 1:
            self._metrics_collector.record_rotation(files_rotated=len(records_by_file))
        
        # Log rotation activity if we wrote to multiple files
        if len(records_by_file) > 1:
            logger.info(
                "Rotated during flush - wrote to multiple files",
                extra={
                    "files_written": len(records_by_file),
                    "total_records": len(buffered_records),
                    "file_paths": list(records_by_file.keys()),
                },
            )
        
        return total_bytes, total_records
    
    def _write_records_to_single_file(self, buffered_records: List[BufferedRecord], file_path: str) -> tuple[int, int]:
        """Write buffered records to a single file with metadata updates.
        
        Returns:
            Tuple of (bytes_written, records_written)
        """
        bytes_written = 0
        
        with open(file_path, "a", encoding="utf-8") as f:
            for buffered_record in buffered_records:
                record = buffered_record.record
                
                # Create a copy of the record with updated metadata
                # Since PatternRecord is frozen, we need to create a new one
                updated_metadata = record.metadata.copy()
                updated_metadata['buffer_depth'] = buffered_record.buffer_depth_at_time
                updated_metadata['flush_reason'] = "time_based"
                
                # Create new record with updated metadata
                from .pattern_record import PatternRecord
                updated_record = PatternRecord(
                    snapshot=record.snapshot,
                    regime_tags=record.regime_tags,
                    condition_tags=record.condition_tags,
                    outcome_labels=record.outcome_labels,
                    metadata=updated_metadata,
                )
                
                # Write to file
                line = json.dumps(updated_record.to_dict(), ensure_ascii=False) + "\n"
                f.write(line)
                bytes_written += len(line.encode('utf-8'))
        
        return bytes_written, len(buffered_records)
    
    def _write_record_direct(self, record: PatternRecord) -> None:
        """Write a single record directly to disk (no buffering) with rotation support."""
        try:
            # Update metadata for direct write
            updated_metadata = record.metadata.copy()
            updated_metadata['buffer_depth'] = 0
            updated_metadata['flush_reason'] = "direct"
            
            # Create new record with updated metadata
            from .pattern_record import PatternRecord
            updated_record = PatternRecord(
                snapshot=record.snapshot,
                regime_tags=record.regime_tags,
                condition_tags=record.condition_tags,
                outcome_labels=record.outcome_labels,
                metadata=updated_metadata,
            )
            
            # Determine target file path based on rotation
            if self._rotation_manager is not None:
                target_file_path = str(self._rotation_manager.get_current_file_path())
            else:
                target_file_path = self._sink_file_path
            
            with open(target_file_path, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(updated_record.to_dict(), ensure_ascii=False) + "\n"
                )
                
        except Exception:
            logger.exception(
                "Failed to write record directly to disk",
                extra={"file_path": self._sink_file_path},
            )
    
    def _update_record_metadata(self, record: PatternRecord, buffer_depth: int, flush_reason: str) -> None:
        """Update record metadata with buffer and flush information."""
        # Update buffer_depth in metadata
        if hasattr(record, 'metadata') and record.metadata is not None:
            record.metadata['buffer_depth'] = buffer_depth
            record.metadata['flush_reason'] = flush_reason
        else:
            # If metadata doesn't exist, create it
            if not hasattr(record, 'metadata'):
                record.metadata = {}
            record.metadata['buffer_depth'] = buffer_depth
            record.metadata['flush_reason'] = flush_reason
    
    def get_buffer_stats(self) -> dict:
        """Get current buffer statistics for monitoring."""
        with self._lock:
            return {
                "buffer_size": len(self._buffer),
                "max_buffer_size": self._config.max_buffer_size,
                "flush_interval_ms": self._config.flush_interval_ms,
                "last_flush_ms": self._last_flush_ms,
                "running": self._running,
                "time_since_last_flush_ms": utc_now_ms() - self._last_flush_ms if self._last_flush_ms > 0 else 0,
            }
    
    def set_metrics_collector(self, collector: UsageMetricsCollector) -> None:
        """Set the usage metrics collector (Task 05)."""
        self._metrics_collector = collector
