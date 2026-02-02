"""
Backup Manager - Daily backup with compression, manifest, and retention management

Key Responsibilities:
- Create tar.gz backups of all observer logs
- Generate backup manifest with metadata and checksums
- 21:00 KST daily backup schedule
- Maintain 30-day retention policy
- Support restore functionality
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import shutil
import tarfile
from dataclasses import dataclass, asdict
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List

from observer.paths import project_root, config_dir, observer_asset_dir, log_dir

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore

log = logging.getLogger("BackupManager")


@dataclass
class BackupManifest:
    """Backup metadata and checksums"""
    backup_id: str  # YYYYMMDD_HHMMSS format
    backup_at: datetime
    archive_path: str
    archive_size_bytes: int
    archive_sha256: str
    files_included: int
    total_files_size_bytes: int
    retention_until: datetime
    
    def to_dict(self) -> dict:
        return {
            "backup_id": self.backup_id,
            "backup_at": self.backup_at.isoformat(),
            "archive_path": self.archive_path,
            "archive_size_bytes": self.archive_size_bytes,
            "archive_sha256": self.archive_sha256,
            "files_included": self.files_included,
            "total_files_size_bytes": self.total_files_size_bytes,
            "retention_until": self.retention_until.isoformat()
        }


@dataclass
class BackupConfig:
    tz_name: str = "Asia/Seoul"
    backup_time: time = time(21, 0)  # 21:00 KST
    backup_schedule_check_interval_seconds: int = 300  # Check every 5 minutes
    source_dirs: Optional[List[str]] = None  # Directories to backup (absolute paths)
    backup_root_dir: Optional[str] = None  # Default: project_root/backups
    retention_days: int = 30

    def __post_init__(self):
        if self.backup_root_dir is None or "obs_deploy" in (self.backup_root_dir or ""):
            self.backup_root_dir = str(project_root() / "backups")
        if self.source_dirs is None or any("obs_deploy" in d for d in (self.source_dirs or [])):
            self.source_dirs = [
                str(config_dir()),
                str(observer_asset_dir()),
                str(log_dir()),
            ]


class BackupManager:
    """
    Manages daily backups of observer system.
    
    Features:
    - Daily backup at 21:00 KST
    - Tar.gz compression
    - SHA256 checksum generation
    - Manifest creation
    - 30-day retention policy
    - Restore capability
    """
    
    def __init__(self, config: Optional[BackupConfig] = None) -> None:
        self.cfg = config or BackupConfig()
        self._tz = ZoneInfo(self.cfg.tz_name) if ZoneInfo else None
        self._running = False
        
        # Ensure backup root directory exists
        self.backup_root = Path(self.cfg.backup_root_dir)
        self.backup_root.mkdir(parents=True, exist_ok=True)
        
        # Backup directory structure
        self.archives_dir = self.backup_root / "archives"
        self.manifests_dir = self.backup_root / "manifests"
        self.archives_dir.mkdir(parents=True, exist_ok=True)
        self.manifests_dir.mkdir(parents=True, exist_ok=True)
    
    # =====================================================================
    # Lifecycle
    # =====================================================================
    def _now(self) -> datetime:
        if self._tz:
            return datetime.now(self._tz)
        return datetime.now()
    
    async def start(self) -> None:
        """
        Start backup scheduler.
        
        Main loop:
        1. Check if backup time (21:00 KST)
        2. Execute backup if needed
        3. Clean old backups (retention policy)
        4. Sleep until next check
        """
        log.info("BackupManager started")
        self._running = True
        
        try:
            while self._running:
                now = self._now()
                
                # Check if backup time (5-minute window: 21:00~21:05)
                if self._should_backup(now):
                    log.info("🕘 BACKUP TIME (21:00 KST)")
                    await self._execute_backup()
                    
                    # Cleanup old backups
                    self._cleanup_old_backups()
                
                # Sleep until next check
                await asyncio.sleep(self.cfg.backup_schedule_check_interval_seconds)
        
        except Exception as e:
            log.error(f"BackupManager error: {e}", exc_info=True)
    
    def stop(self) -> None:
        """Stop the backup scheduler"""
        log.info("BackupManager stopping...")
        self._running = False
    
    # =====================================================================
    # Scheduling
    # =====================================================================
    def _should_backup(self, now: datetime) -> bool:
        """
        Check if current time is within backup window.
        
        Window: 21:00 ~ 21:05 KST (5-minute window)
        Only backup once per day.
        """
        current_time = now.time()
        target_time = self.cfg.backup_time
        
        # 5-minute window
        window_start = target_time
        window_end = (datetime.combine(now.date(), target_time) + timedelta(minutes=5)).time()
        
        # Check if within window
        if not (window_start <= current_time <= window_end):
            return False
        
        # Check if backup already done today
        today_backup = self.archives_dir / f"observer_{now.strftime('%Y%m%d')}_*.tar.gz"
        existing_backups = list(self.archives_dir.glob(f"observer_{now.strftime('%Y%m%d')}_*.tar.gz"))
        
        return len(existing_backups) == 0
    
    # =====================================================================
    # Backup Execution
    # =====================================================================
    async def _execute_backup(self) -> bool:
        """
        Execute full system backup.
        
        Steps:
        1. Collect all files from source directories
        2. Create tar.gz archive
        3. Calculate SHA256 checksum
        4. Generate manifest
        5. Log completion
        
        Returns:
            True if backup successful, False otherwise
        """
        now = self._now()
        backup_id = now.strftime("%Y%m%d_%H%M%S")
        
        log.info(f"Starting backup: {backup_id}")
        
        try:
            # Step 1: Validate source directories
            source_paths = []
            for src_str in self.cfg.source_dirs:
                src_path = Path(src_str)
                if src_path.exists():
                    source_paths.append(src_path)
                    log.debug(f"Including: {src_path}")
                else:
                    log.warning(f"Source not found: {src_path}")
            
            if not source_paths:
                log.error("No source directories available for backup")
                return False
            
            # Step 2: Create tar.gz archive
            archive_path = self.archives_dir / f"observer_{backup_id}.tar.gz"
            
            log.info(f"Creating archive: {archive_path.name}")
            
            file_count = 0
            total_size = 0
            
            with tarfile.open(archive_path, "w:gz") as tar:
                for src_path in source_paths:
                    if src_path.is_dir():
                        # Add directory recursively
                        for item in src_path.rglob("*"):
                            if item.is_file():
                                # Add to archive with relative path
                                arcname = item.relative_to(src_path.parent)
                                tar.add(item, arcname=arcname)
                                file_count += 1
                                total_size += item.stat().st_size
                    else:
                        # Add single file
                        tar.add(src_path, arcname=src_path.name)
                        file_count += 1
                        total_size += src_path.stat().st_size
            
            # Step 3: Calculate SHA256 checksum
            log.info("Calculating SHA256 checksum...")
            archive_sha256 = self._calculate_sha256(archive_path)
            
            # Step 4: Create manifest
            archive_size = archive_path.stat().st_size
            retention_until = now + timedelta(days=self.cfg.retention_days)
            
            manifest = BackupManifest(
                backup_id=backup_id,
                backup_at=now,
                archive_path=str(archive_path),
                archive_size_bytes=archive_size,
                archive_sha256=archive_sha256,
                files_included=file_count,
                total_files_size_bytes=total_size,
                retention_until=retention_until
            )
            
            self._save_manifest(manifest)
            
            log.info(
                f"✅ BACKUP COMPLETED: {backup_id}\n"
                f"  Files: {file_count}\n"
                f"  Original size: {total_size / 1024 / 1024:.2f} MB\n"
                f"  Compressed size: {archive_size / 1024 / 1024:.2f} MB\n"
                f"  Compression ratio: {100 * archive_size / total_size:.1f}%\n"
                f"  Retention until: {retention_until.isoformat()}"
            )
            
            return True
        
        except Exception as e:
            log.error(f"Backup failed: {e}", exc_info=True)
            return False
    
    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def _save_manifest(self, manifest: BackupManifest) -> None:
        """Save backup manifest to JSON file"""
        manifest_file = self.manifests_dir / f"manifest_{manifest.backup_id}.json"
        
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest.to_dict(), f, indent=2, ensure_ascii=False)
        
        log.debug(f"Manifest saved: {manifest_file.name}")
    
    # =====================================================================
    # Retention & Cleanup
    # =====================================================================
    def _cleanup_old_backups(self) -> None:
        """
        Clean up backups older than retention period.
        
        Removes both archive and manifest files.
        """
        try:
            now = self._now()
            cutoff_date = now - timedelta(days=self.cfg.retention_days)
            
            removed_count = 0
            
            # Check archive files
            for archive_file in self.archives_dir.glob("observer_*.tar.gz"):
                # Extract backup_id from filename (observer_YYYYMMDD_HHMMSS.tar.gz)
                try:
                    # Remove "observer_" prefix and ".tar.gz" suffix
                    backup_id = archive_file.name.replace("observer_", "").replace(".tar.gz", "")
                    
                    # Extract date from backup_id (YYYYMMDD_HHMMSS)
                    date_str = backup_id.split("_")[0]  # YYYYMMDD
                    file_date = datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=self._tz)
                    
                    if file_date < cutoff_date:
                        log.info(f"Removing old backup: {archive_file.name}")
                        archive_file.unlink()
                        
                        # Also remove corresponding manifest
                        manifest_file = self.manifests_dir / f"manifest_{backup_id}.json"
                        if manifest_file.exists():
                            manifest_file.unlink()
                        
                        removed_count += 1
                
                except (IndexError, ValueError) as e:
                    log.warning(f"Could not parse backup date from {archive_file.name}: {e}")
            
            if removed_count > 0:
                log.info(f"Cleaned up {removed_count} old backup(s)")
        
        except Exception as e:
            log.error(f"Cleanup failed: {e}", exc_info=True)
    
    # =====================================================================
    # Restore
    # =====================================================================
    def restore_from_backup(
        self, 
        backup_id: str, 
        restore_path: Optional[Path] = None
    ) -> bool:
        """
        Restore from a backup archive.
        
        Args:
            backup_id: Backup ID (YYYYMMDD_HHMMSS format)
            restore_path: Destination path (default: current directory)
        
        Returns:
            True if restore successful, False otherwise
        """
        try:
            # Find archive
            archive_files = list(self.archives_dir.glob(f"observer_{backup_id}.tar.gz"))
            
            if not archive_files:
                log.error(f"Backup not found: {backup_id}")
                return False
            
            archive_path = archive_files[0]
            
            # Verify checksum
            log.info(f"Verifying backup integrity...")
            manifest_file = self.manifests_dir / f"manifest_{backup_id}.json"
            
            if not manifest_file.exists():
                log.error(f"Manifest not found: {manifest_file}")
                return False
            
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
            
            archive_sha256 = self._calculate_sha256(archive_path)
            if archive_sha256 != manifest_data["archive_sha256"]:
                log.error("Checksum mismatch - backup may be corrupted")
                return False
            
            log.info("✅ Checksum verified")
            
            # Extract archive
            if restore_path is None:
                restore_path = Path.cwd()
            
            restore_path.mkdir(parents=True, exist_ok=True)
            
            log.info(f"Extracting to: {restore_path}")
            
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(restore_path)
            
            log.info(f"✅ RESTORE COMPLETED: {backup_id}")
            return True
        
        except Exception as e:
            log.error(f"Restore failed: {e}", exc_info=True)
            return False
    
    # =====================================================================
    # Status
    # =====================================================================
    def get_status(self) -> Dict[str, Any]:
        """Get backup manager status"""
        backups = list(self.archives_dir.glob("observer_*.tar.gz"))
        
        total_backup_size = sum(b.stat().st_size for b in backups)
        
        return {
            "running": self._running,
            "total_backups": len(backups),
            "total_backup_size_bytes": total_backup_size,
            "total_backup_size_gb": total_backup_size / 1024 / 1024 / 1024,
            "next_backup_time": f"{self.cfg.backup_time} KST",
            "retention_days": self.cfg.retention_days,
            "backup_root": str(self.backup_root)
        }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups"""
        backups = []
        
        for manifest_file in sorted(self.manifests_dir.glob("manifest_*.json")):
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)
                
                backups.append(manifest_data)
            
            except Exception as e:
                log.warning(f"Failed to read manifest {manifest_file}: {e}")
        
        return sorted(backups, key=lambda x: x["backup_id"], reverse=True)


# ---- CLI for Testing ----

async def main():
    """CLI for testing BackupManager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Backup Manager Test CLI")
    parser.add_argument("--backup-now", action="store_true", help="Execute immediate backup")
    parser.add_argument("--list", action="store_true", help="List all backups")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--restore", type=str, help="Restore from backup (backup_id)")
    parser.add_argument("--restore-to", type=str, help="Restore destination path")
    args = parser.parse_args()
    
    manager = BackupManager()
    
    if args.backup_now:
        print("🧪 Executing immediate backup...")
        print()
        
        success = await manager._execute_backup()
        
        if success:
            print("✅ Backup successful")
        else:
            print("❌ Backup failed")
        
        print()
        status = manager.get_status()
        print(f"📊 Status: {json.dumps(status, indent=2)}")
    
    elif args.list:
        print("📋 Available Backups:")
        print("-" * 80)
        
        backups = manager.list_backups()
        
        if not backups:
            print("  No backups found")
        else:
            for backup in backups:
                print(f"\n  ID: {backup['backup_id']}")
                print(f"  Created: {backup['backup_at']}")
                print(f"  Files: {backup['files_included']}")
                print(f"  Original: {backup['total_files_size_bytes'] / 1024 / 1024:.2f} MB")
                print(f"  Compressed: {backup['archive_size_bytes'] / 1024 / 1024:.2f} MB")
                print(f"  Retention: {backup['retention_until']}")
    
    elif args.restore:
        print(f"🔄 Restoring from backup: {args.restore}")
        
        restore_to = Path(args.restore_to) if args.restore_to else None
        success = manager.restore_from_backup(args.restore, restore_to)
        
        if success:
            print("✅ Restore successful")
        else:
            print("❌ Restore failed")
    
    elif args.status:
        print("📊 BackupManager Status:")
        print("-" * 80)
        
        status = manager.get_status()
        print(json.dumps(status, indent=2))
        
        print()
        backups = manager.list_backups()
        print(f"Total Backups: {len(backups)}")
        
        if backups:
            print(f"Latest: {backups[0]['backup_id']}")
    
    else:
        print("BackupManager initialized")
        print("Run with --backup-now, --list, --status, or --restore to perform operations")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    asyncio.run(main())
