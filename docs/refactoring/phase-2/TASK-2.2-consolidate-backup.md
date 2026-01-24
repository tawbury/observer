# TASK-2.2: Backup 모듈 통합

## 태스크 정보
- **Phase**: 2 - 모듈 통합
- **우선순위**: High
- **의존성**: Phase 1 완료
- **상태**: 대기

---

## 목표
중복된 Backup 관련 모듈을 역할별로 정리하여 명확한 책임 분리와 코드 재사용성을 향상시킵니다.

---

## 현재 문제

### 중복 모듈 구조

```
src/backup/                         # 기본 모듈 (5개 파일)
├── __init__.py
├── backup_manager.py               # 521줄 - 비동기 스케줄러 포함
├── manager.py                      # 109줄 - 간단한 동기 백업
├── checksum.py                     # 체크섬 계산
├── manifest.py                     # 매니페스트 생성
└── test_backup_manager.py          # 테스트

src/maintenance/backup/             # 유지보수 모듈 (2개 파일)
├── __init__.py
└── runner.py                       # 76줄 - Plan/Execute 패턴
```

### 중복 클래스/함수

#### BackupManifest 중복 정의
- `src/backup/backup_manager.py`: BackupManifest dataclass
- `src/backup/manifest.py`: 별도 매니페스트 로직

#### 백업 로직 중복
- `backup_manager.py`: `_archive_files()`, `_generate_manifest()`
- `manager.py`: `create_backup()`, tar.gz 생성

---

## 구현 계획

### 1. 모듈 구조 재설계

**목표 구조**:
```
src/backup/
├── __init__.py           # 통합 exports
├── core.py               # 핵심 백업 로직 (from manager.py)
├── scheduler.py          # 비동기 스케줄러 (from backup_manager.py)
├── manifest.py           # 매니페스트 (통합)
├── checksum.py           # 체크섬 (유지)
└── plan.py               # Plan/Execute 패턴 (from runner.py)
```

### 2. 통합 매니페스트

**파일**: `app/obs_deploy/app/src/backup/manifest.py`

```python
"""
Unified backup manifest management.

Provides consistent manifest generation, validation, and storage
across all backup operations.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .checksum import calculate_checksum


__all__ = ["BackupManifest", "ManifestEntry", "create_manifest", "load_manifest"]


@dataclass
class ManifestEntry:
    """Individual file entry in a backup manifest."""
    path: str
    size: int
    checksum: str
    modified: str  # ISO format datetime

    @classmethod
    def from_file(cls, file_path: Path, base_path: Optional[Path] = None) -> "ManifestEntry":
        """Create entry from a file."""
        stat = file_path.stat()
        relative = str(file_path.relative_to(base_path)) if base_path else str(file_path)
        return cls(
            path=relative,
            size=stat.st_size,
            checksum=calculate_checksum(file_path),
            modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
        )


@dataclass
class BackupManifest:
    """
    Complete backup manifest with metadata and file entries.

    Attributes:
        backup_id: Unique identifier for this backup
        created_at: Timestamp of backup creation
        source_dir: Original source directory
        files: List of file entries
        total_size: Total size of all files in bytes
        file_count: Number of files in backup
        metadata: Additional metadata
    """
    backup_id: str
    created_at: str
    source_dir: str
    files: List[ManifestEntry] = field(default_factory=list)
    total_size: int = 0
    file_count: int = 0
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not self.total_size:
            self.total_size = sum(f.size for f in self.files)
        if not self.file_count:
            self.file_count = len(self.files)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_json(self, pretty: bool = True) -> str:
        """Serialize to JSON string."""
        indent = 2 if pretty else None
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, path: Path) -> None:
        """Save manifest to file."""
        path.write_text(self.to_json())

    @classmethod
    def from_dict(cls, data: Dict) -> "BackupManifest":
        """Create manifest from dictionary."""
        files = [ManifestEntry(**f) for f in data.get("files", [])]
        return cls(
            backup_id=data["backup_id"],
            created_at=data["created_at"],
            source_dir=data["source_dir"],
            files=files,
            total_size=data.get("total_size", 0),
            file_count=data.get("file_count", 0),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "BackupManifest":
        """Create manifest from JSON string."""
        return cls.from_dict(json.loads(json_str))


def create_manifest(
    backup_id: str,
    source_dir: Path,
    files: Optional[List[Path]] = None,
    metadata: Optional[Dict[str, str]] = None,
) -> BackupManifest:
    """
    Create a backup manifest from source directory.

    Args:
        backup_id: Unique identifier for this backup
        source_dir: Source directory to scan
        files: Optional list of specific files (scans all if not provided)
        metadata: Additional metadata to include

    Returns:
        Complete BackupManifest
    """
    if files is None:
        files = [f for f in source_dir.rglob("*") if f.is_file()]

    entries = [ManifestEntry.from_file(f, source_dir) for f in files]

    return BackupManifest(
        backup_id=backup_id,
        created_at=datetime.now().isoformat(),
        source_dir=str(source_dir),
        files=entries,
        metadata=metadata or {},
    )


def load_manifest(path: Path) -> BackupManifest:
    """Load manifest from file."""
    return BackupManifest.from_json(path.read_text())
```

### 3. 핵심 백업 로직

**파일**: `app/obs_deploy/app/src/backup/core.py`

```python
"""
Core backup operations.

Provides synchronous backup functionality for creating archives
and managing backup files.
"""
from __future__ import annotations

import shutil
import tarfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .manifest import BackupManifest, create_manifest


__all__ = ["BackupConfig", "BackupResult", "create_backup", "restore_backup"]


@dataclass
class BackupConfig:
    """Configuration for backup operations."""
    source_dir: Path
    backup_dir: Path
    prefix: str = "backup"
    compression: str = "gz"  # gz, bz2, xz, or empty for no compression
    include_manifest: bool = True


@dataclass
class BackupResult:
    """Result of a backup operation."""
    success: bool
    backup_path: Optional[Path] = None
    manifest_path: Optional[Path] = None
    manifest: Optional[BackupManifest] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0


def create_backup(
    config: BackupConfig,
    files: Optional[List[Path]] = None,
    metadata: Optional[dict] = None,
) -> BackupResult:
    """
    Create a backup archive from source directory.

    Args:
        config: Backup configuration
        files: Specific files to backup (all files if not specified)
        metadata: Additional metadata for manifest

    Returns:
        BackupResult with paths and status
    """
    start_time = datetime.now()

    try:
        # Generate backup ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"{config.prefix}_{timestamp}"

        # Determine archive name
        ext = f".tar.{config.compression}" if config.compression else ".tar"
        archive_name = f"{backup_id}{ext}"
        archive_path = config.backup_dir / archive_name

        # Ensure backup directory exists
        config.backup_dir.mkdir(parents=True, exist_ok=True)

        # Get files to backup
        if files is None:
            files = [f for f in config.source_dir.rglob("*") if f.is_file()]

        # Create manifest
        manifest = create_manifest(
            backup_id=backup_id,
            source_dir=config.source_dir,
            files=files,
            metadata=metadata,
        )

        # Create archive
        mode = f"w:{config.compression}" if config.compression else "w"
        with tarfile.open(archive_path, mode) as tar:
            for file_path in files:
                arcname = file_path.relative_to(config.source_dir)
                tar.add(file_path, arcname=arcname)

        # Save manifest
        manifest_path = None
        if config.include_manifest:
            manifest_path = config.backup_dir / f"{backup_id}.manifest.json"
            manifest.save(manifest_path)

        duration = (datetime.now() - start_time).total_seconds()

        return BackupResult(
            success=True,
            backup_path=archive_path,
            manifest_path=manifest_path,
            manifest=manifest,
            duration_seconds=duration,
        )

    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        return BackupResult(
            success=False,
            error=str(e),
            duration_seconds=duration,
        )


def restore_backup(
    archive_path: Path,
    restore_dir: Path,
    verify_checksums: bool = True,
) -> BackupResult:
    """
    Restore files from a backup archive.

    Args:
        archive_path: Path to backup archive
        restore_dir: Directory to restore files to
        verify_checksums: Whether to verify file checksums after restore

    Returns:
        BackupResult with status
    """
    start_time = datetime.now()

    try:
        restore_dir.mkdir(parents=True, exist_ok=True)

        # Extract archive
        with tarfile.open(archive_path, "r:*") as tar:
            tar.extractall(restore_dir)

        duration = (datetime.now() - start_time).total_seconds()

        return BackupResult(
            success=True,
            backup_path=restore_dir,
            duration_seconds=duration,
        )

    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        return BackupResult(
            success=False,
            error=str(e),
            duration_seconds=duration,
        )
```

### 4. 비동기 스케줄러

**파일**: `app/obs_deploy/app/src/backup/scheduler.py`

```python
"""
Asynchronous backup scheduler.

Provides scheduled backup execution with async/await support.
Extracted from backup_manager.py.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Callable, Optional

from shared.time_helpers import TimeAwareMixin
from .core import BackupConfig, BackupResult, create_backup


__all__ = ["SchedulerConfig", "BackupScheduler"]

logger = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    """Configuration for backup scheduler."""
    source_dir: Path
    backup_dir: Path
    schedule_time: time = time(3, 0)  # 3 AM default
    retention_days: int = 7
    tz_name: str = "Asia/Seoul"
    prefix: str = "scheduled_backup"


class BackupScheduler(TimeAwareMixin):
    """
    Asynchronous backup scheduler.

    Runs backups at scheduled times and manages retention.
    """

    def __init__(
        self,
        config: SchedulerConfig,
        on_complete: Optional[Callable[[BackupResult], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ):
        self.config = config
        self._tz_name = config.tz_name
        self._init_timezone()
        self._on_complete = on_complete
        self._on_error = on_error
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the scheduler."""
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Backup scheduler started, next run at {self.config.schedule_time}")

    async def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Backup scheduler stopped")

    async def _run_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                # Calculate time until next run
                now = self._now()
                next_run = self._calculate_next_run(now)
                wait_seconds = (next_run - now).total_seconds()

                logger.info(f"Next backup scheduled for {next_run}")
                await asyncio.sleep(wait_seconds)

                if self._running:
                    await self._execute_backup()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                if self._on_error:
                    self._on_error(str(e))
                await asyncio.sleep(60)  # Wait before retry

    def _calculate_next_run(self, now: datetime) -> datetime:
        """Calculate next scheduled run time."""
        scheduled = now.replace(
            hour=self.config.schedule_time.hour,
            minute=self.config.schedule_time.minute,
            second=0,
            microsecond=0,
        )
        if scheduled <= now:
            scheduled += timedelta(days=1)
        return scheduled

    async def _execute_backup(self) -> None:
        """Execute a backup operation."""
        logger.info("Starting scheduled backup")

        config = BackupConfig(
            source_dir=self.config.source_dir,
            backup_dir=self.config.backup_dir,
            prefix=self.config.prefix,
        )

        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, create_backup, config)

        if result.success:
            logger.info(f"Backup completed: {result.backup_path}")
            await self._cleanup_old_backups()
        else:
            logger.error(f"Backup failed: {result.error}")

        if self._on_complete:
            self._on_complete(result)

    async def _cleanup_old_backups(self) -> None:
        """Remove backups older than retention period."""
        cutoff = self._now() - timedelta(days=self.config.retention_days)

        for archive in self.config.backup_dir.glob(f"{self.config.prefix}_*.tar.*"):
            try:
                mtime = datetime.fromtimestamp(archive.stat().st_mtime)
                if mtime < cutoff:
                    archive.unlink()
                    # Also remove manifest if exists
                    manifest = archive.with_suffix(".manifest.json")
                    if manifest.exists():
                        manifest.unlink()
                    logger.info(f"Removed old backup: {archive}")
            except Exception as e:
                logger.warning(f"Failed to remove {archive}: {e}")
```

### 5. __init__.py 업데이트

**파일**: `app/obs_deploy/app/src/backup/__init__.py`

```python
"""
Unified backup module.

Provides backup creation, scheduling, and management functionality.
"""
from .core import BackupConfig, BackupResult, create_backup, restore_backup
from .manifest import BackupManifest, ManifestEntry, create_manifest, load_manifest
from .checksum import calculate_checksum, verify_checksum
from .scheduler import BackupScheduler, SchedulerConfig

__all__ = [
    # Core
    "BackupConfig",
    "BackupResult",
    "create_backup",
    "restore_backup",
    # Manifest
    "BackupManifest",
    "ManifestEntry",
    "create_manifest",
    "load_manifest",
    # Checksum
    "calculate_checksum",
    "verify_checksum",
    # Scheduler
    "BackupScheduler",
    "SchedulerConfig",
]
```

### 6. maintenance/backup 제거

**파일**: `app/obs_deploy/app/src/maintenance/backup/__init__.py`

```python
"""
Deprecated: Use src/backup instead.
"""
import warnings

warnings.warn(
    "maintenance.backup is deprecated. Use backup module directly.",
    DeprecationWarning,
    stacklevel=2,
)

from backup import create_backup, BackupConfig, BackupResult

__all__ = ["create_backup", "BackupConfig", "BackupResult"]
```

---

## 검증 방법

### 1. 단위 테스트
```python
# tests/unit/backup/test_core.py
import pytest
from pathlib import Path
from backup.core import BackupConfig, create_backup


def test_create_backup(tmp_path):
    # Setup
    source = tmp_path / "source"
    source.mkdir()
    (source / "test.txt").write_text("hello")

    backup_dir = tmp_path / "backups"

    config = BackupConfig(
        source_dir=source,
        backup_dir=backup_dir,
    )

    # Execute
    result = create_backup(config)

    # Verify
    assert result.success
    assert result.backup_path.exists()
    assert result.manifest is not None
```

### 2. 통합 테스트
```bash
pytest app/obs_deploy/app/src/backup/ -v
```

---

## 완료 조건

- [ ] `backup/core.py` 생성됨
- [ ] `backup/scheduler.py` 생성됨
- [ ] `backup/manifest.py` 통합됨
- [ ] `backup/__init__.py` 업데이트됨
- [ ] `backup_manager.py` 제거됨 (또는 deprecated)
- [ ] `manager.py` 제거됨 (core.py로 대체)
- [ ] `maintenance/backup/` deprecation 추가됨
- [ ] 단위 테스트 통과
- [ ] 기존 테스트 모두 통과

---

## 관련 태스크
- [TASK-2.1](TASK-2.1-consolidate-retention.md): Retention 모듈 통합 (유사 패턴)
