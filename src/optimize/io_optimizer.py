"""
I/O Optimization Module

Purpose:
- Optimize disk I/O operations
- Implement efficient buffering
- Use batch writes to reduce syscalls
- Optimize file access patterns

Features:
1. Buffered Writer - Batch writes with auto-flush
2. Memory-Mapped I/O - Fast random access
3. Sequential Reader - Optimized sequential reading
4. I/O Metrics - Monitor I/O performance
"""
from __future__ import annotations

import asyncio
import json
import logging
import mmap
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Any, BinaryIO
import gzip

log = logging.getLogger("IOOptimization")


@dataclass
class IOMetrics:
    """I/O operation metrics"""
    total_writes: int = 0
    total_bytes_written: int = 0
    total_reads: int = 0
    total_bytes_read: int = 0
    
    buffer_flushes: int = 0
    buffer_efficiency: float = 0.0  # bytes per flush
    
    elapsed_seconds: float = 0.0
    throughput_mbps: float = 0.0


class BufferedWriter:
    """
    Efficient buffered writer with batch operations
    
    Features:
    - Accumulate writes in memory
    - Batch flush to disk
    - Async-friendly
    - Configurable buffer size
    """
    
    def __init__(
        self,
        filepath: Path,
        buffer_size: int = 65536,  # 64KB
        max_writes_before_flush: int = 1000
    ) -> None:
        self.filepath = Path(filepath)
        self.buffer_size = buffer_size
        self.max_writes_before_flush = max_writes_before_flush
        
        self._buffer: List[bytes] = []
        self._buffer_bytes = 0
        self._write_count = 0
        self._lock = asyncio.Lock()
        self._metrics = IOMetrics()
        self._file: Optional[BinaryIO] = None
    
    async def write(self, data: bytes) -> None:
        """
        Write data (may be buffered)
        
        Args:
            data: Bytes to write
        """
        async with self._lock:
            self._buffer.append(data)
            self._buffer_bytes += len(data)
            self._write_count += 1
            
            # Auto-flush on threshold
            if (
                self._buffer_bytes >= self.buffer_size or
                self._write_count >= self.max_writes_before_flush
            ):
                await self._flush_internal()
    
    async def write_text(self, text: str) -> None:
        """Write text data"""
        await self.write(text.encode("utf-8"))
    
    async def write_json(self, obj: Any) -> None:
        """Write JSON object"""
        text = json.dumps(obj, ensure_ascii=False) + "\n"
        await self.write_text(text)
    
    async def write_jsonl(self, objects: List[Any]) -> None:
        """Write multiple JSON objects (JSONL format)"""
        buffer = []
        for obj in objects:
            line = json.dumps(obj, ensure_ascii=False) + "\n"
            buffer.append(line.encode("utf-8"))
        
        total_bytes = sum(len(b) for b in buffer)
        
        async with self._lock:
            self._buffer.extend(buffer)
            self._buffer_bytes += total_bytes
            self._write_count += len(objects)
            
            if (
                self._buffer_bytes >= self.buffer_size or
                self._write_count >= self.max_writes_before_flush
            ):
                await self._flush_internal()
    
    async def flush(self) -> None:
        """Flush all buffered data"""
        async with self._lock:
            await self._flush_internal()
    
    async def _flush_internal(self) -> None:
        """Internal flush (must be called with lock held)"""
        if not self._buffer:
            return
        
        # Open file if needed
        if not self._file:
            self._file = open(self.filepath, "ab")
        
        # Write all buffered data
        for data in self._buffer:
            self._file.write(data)
            self._metrics.total_writes += 1
            self._metrics.total_bytes_written += len(data)
        
        # Sync to disk
        self._file.flush()
        os.fsync(self._file.fileno())
        
        # Update metrics
        self._metrics.buffer_flushes += 1
        if self._metrics.buffer_flushes > 0:
            self._metrics.buffer_efficiency = (
                self._metrics.total_bytes_written / self._metrics.buffer_flushes
            )
        
        # Clear buffer
        self._buffer.clear()
        self._buffer_bytes = 0
        self._write_count = 0
        
        log.debug(f"✓ Flushed {self._metrics.total_bytes_written} bytes")
    
    async def close(self) -> None:
        """Close and flush"""
        await self.flush()
        if self._file:
            self._file.close()
            self._file = None
    
    def get_metrics(self) -> IOMetrics:
        """Get I/O metrics"""
        return self._metrics


class MemoryMappedReader:
    """
    Memory-mapped file reader for fast random access
    
    Features:
    - Zero-copy reading
    - Random access without seek overhead
    - Memory efficient
    """
    
    def __init__(self, filepath: Path) -> None:
        self.filepath = Path(filepath)
        self._file: Optional[BinaryIO] = None
        self._mmap: Optional[mmap.mmap] = None
        self._metrics = IOMetrics()
    
    async def open(self) -> None:
        """Open file for memory-mapped reading"""
        if not self.filepath.exists():
            raise FileNotFoundError(f"File not found: {self.filepath}")
        
        self._file = open(self.filepath, "rb")
        self._mmap = mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)
        log.info(f"✓ Opened memory-mapped file: {self.filepath}")
    
    async def read_bytes(self, offset: int, size: int) -> bytes:
        """
        Read bytes at offset
        
        Args:
            offset: Byte offset
            size: Number of bytes to read
        
        Returns:
            Bytes read
        """
        if not self._mmap:
            await self.open()
        
        self._mmap.seek(offset)
        data = self._mmap.read(size)
        
        self._metrics.total_reads += 1
        self._metrics.total_bytes_read += len(data)
        
        return data
    
    async def read_range(self, start: int, end: int) -> bytes:
        """Read range of bytes"""
        return await self.read_bytes(start, end - start)
    
    async def read_all(self) -> bytes:
        """Read entire file"""
        if not self._mmap:
            await self.open()
        
        self._mmap.seek(0)
        data = self._mmap.read()
        
        self._metrics.total_reads += 1
        self._metrics.total_bytes_read += len(data)
        
        return data
    
    async def read_lines(self) -> List[bytes]:
        """Read all lines"""
        if not self._mmap:
            await self.open()
        
        self._mmap.seek(0)
        lines = self._mmap.readlines()
        
        self._metrics.total_reads += len(lines)
        self._metrics.total_bytes_read += sum(len(line) for line in lines)
        
        return lines
    
    async def close(self) -> None:
        """Close memory-mapped file"""
        if self._mmap:
            self._mmap.close()
            self._mmap = None
        
        if self._file:
            self._file.close()
            self._file = None
    
    def get_metrics(self) -> IOMetrics:
        """Get metrics"""
        return self._metrics


class CompressedWriter:
    """
    Compressed file writer for efficient storage
    
    Features:
    - Gzip compression
    - Buffered writes
    - JSONL support
    """
    
    def __init__(
        self,
        filepath: Path,
        compression_level: int = 6,
        buffer_size: int = 65536
    ) -> None:
        self.filepath = Path(filepath)
        self.compression_level = compression_level
        self.buffer_size = buffer_size
        
        self._file: Optional[gzip.GzipFile] = None
        self._buffer: List[bytes] = []
        self._buffer_bytes = 0
    
    async def open(self) -> None:
        """Open compressed file"""
        self._file = gzip.open(
            self.filepath,
            "wb",
            compresslevel=self.compression_level
        )
        log.info(f"✓ Opened compressed file: {self.filepath}")
    
    async def write(self, data: bytes) -> None:
        """Write data"""
        if not self._file:
            await self.open()
        
        self._buffer.append(data)
        self._buffer_bytes += len(data)
        
        if self._buffer_bytes >= self.buffer_size:
            await self.flush()
    
    async def write_text(self, text: str) -> None:
        """Write text"""
        await self.write(text.encode("utf-8"))
    
    async def write_jsonl(self, objects: List[Any]) -> None:
        """Write JSONL"""
        for obj in objects:
            line = json.dumps(obj, ensure_ascii=False) + "\n"
            await self.write_text(line)
    
    async def flush(self) -> None:
        """Flush buffer"""
        if self._buffer and self._file:
            for data in self._buffer:
                self._file.write(data)
            
            self._file.flush()
            self._buffer.clear()
            self._buffer_bytes = 0
    
    async def close(self) -> None:
        """Close file"""
        await self.flush()
        if self._file:
            self._file.close()
            self._file = None


# ---- CLI Entry Point ----

async def main():
    """Test I/O optimization components"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    print("\n🧪 I/O Optimization Test\n")
    
    from observer.paths import project_root
    test_dir = project_root() / "docs" / "test_io"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Test 1: Buffered Writer
    print("=" * 60)
    print("1. BUFFERED WRITER TEST")
    print("=" * 60)
    
    output_file = test_dir / "buffered_test.jsonl"
    writer = BufferedWriter(output_file, buffer_size=10240)
    
    # Write 100 JSON objects
    test_data = [
        {"id": i, "value": f"data_{i}", "timestamp": datetime.now().isoformat()}
        for i in range(100)
    ]
    
    for item in test_data:
        await writer.write_json(item)
    
    await writer.close()
    
    metrics = writer.get_metrics()
    print(f"✓ Wrote {metrics.total_writes} items")
    print(f"  - Total bytes: {metrics.total_bytes_written}")
    print(f"  - Flushes: {metrics.buffer_flushes}")
    print(f"  - Efficiency: {metrics.buffer_efficiency:.0f} bytes/flush")
    
    # Test 2: Memory-Mapped Reader
    print("\n" + "=" * 60)
    print("2. MEMORY-MAPPED READER TEST")
    print("=" * 60)
    
    reader = MemoryMappedReader(output_file)
    
    data = await reader.read_all()
    
    r_metrics = reader.get_metrics()
    print(f"✓ Read file ({len(data)} bytes)")
    print(f"  - Reads: {r_metrics.total_reads}")
    print(f"  - Bytes: {r_metrics.total_bytes_read}")
    
    await reader.close()
    
    # Test 3: Compressed Writer
    print("\n" + "=" * 60)
    print("3. COMPRESSED WRITER TEST")
    print("=" * 60)
    
    compressed_file = test_dir / "compressed_test.jsonl.gz"
    comp_writer = CompressedWriter(compressed_file)
    
    await comp_writer.write_jsonl(test_data)
    await comp_writer.close()
    
    original_size = output_file.stat().st_size if output_file.exists() else 0
    compressed_size = compressed_file.stat().st_size if compressed_file.exists() else 0
    
    ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
    
    print(f"✓ Compressed file")
    print(f"  - Original: {original_size} bytes")
    print(f"  - Compressed: {compressed_size} bytes")
    print(f"  - Compression: {ratio:.1f}%")
    
    print("\n✅ I/O Optimization tests complete!")


if __name__ == "__main__":
    asyncio.run(main())
