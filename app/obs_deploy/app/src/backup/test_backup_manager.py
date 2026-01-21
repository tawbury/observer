"""
BackupManager Test Suite

Tests:
1. Backup creation and archive generation
2. SHA256 checksum calculation
3. Manifest generation
4. Schedule detection (21:00 window)
5. Retention policy and cleanup
6. Restore functionality
"""
import asyncio
import json
import tarfile
import tempfile
from datetime import datetime, time, timedelta
from pathlib import Path

import pytest

from backup_manager import BackupManager, BackupConfig, BackupManifest


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create source directories
        source_dir = tmpdir / "source"
        source_dir.mkdir()
        
        config_dir = source_dir / "config"
        logs_dir = source_dir / "logs"
        config_dir.mkdir()
        logs_dir.mkdir()
        
        # Create test files
        (config_dir / "test_config.json").write_text('{"test": "data"}')
        (logs_dir / "test_log.jsonl").write_text('{"event": "test"}\n')
        
        # Backup directory
        backup_dir = tmpdir / "backups"
        
        yield {
            "root": tmpdir,
            "source": source_dir,
            "config": config_dir,
            "logs": logs_dir,
            "backup": backup_dir
        }


def test_backup_manager_init(temp_dirs):
    """Test BackupManager initialization"""
    cfg = BackupConfig(
        source_dirs=[str(temp_dirs["config"]), str(temp_dirs["logs"])],
        backup_root_dir=str(temp_dirs["backup"])
    )
    
    manager = BackupManager(cfg)
    
    assert manager.cfg.source_dirs == [
        str(temp_dirs["config"]), 
        str(temp_dirs["logs"])
    ]
    assert manager.archives_dir.exists()
    assert manager.manifests_dir.exists()


@pytest.mark.asyncio
async def test_execute_backup(temp_dirs):
    """Test backup execution with archive creation"""
    cfg = BackupConfig(
        source_dirs=[str(temp_dirs["config"]), str(temp_dirs["logs"])],
        backup_root_dir=str(temp_dirs["backup"] / "app" / "obs_deploy" / "app" / "config" / "backups")
    )
    
    manager = BackupManager(cfg)
    
    success = await manager._execute_backup()
    
    assert success
    
    # Check archive was created
    archives = list(manager.archives_dir.glob("observer_*.tar.gz"))
    assert len(archives) == 1
    
    archive_path = archives[0]
    assert archive_path.stat().st_size > 0
    
    # Check manifest was created
    manifests = list(manager.manifests_dir.glob("manifest_*.json"))
    assert len(manifests) == 1
    
    # Verify archive contents
    with tarfile.open(archive_path, "r:gz") as tar:
        members = tar.getmembers()
        assert len(members) > 0


@pytest.mark.asyncio
async def test_checksum_calculation(temp_dirs):
    """Test SHA256 checksum calculation"""
    cfg = BackupConfig(
        source_dirs=[str(temp_dirs["config"])],
        backup_root_dir=str(temp_dirs["backup"])
    )
    
    manager = BackupManager(cfg)
    
    # Create a backup
    success = await manager._execute_backup()
    assert success
    
    # Get archive path
    archives = list(manager.archives_dir.glob("observer_*.tar.gz"))
    archive_path = archives[0]
    
    # Calculate checksum twice
    checksum1 = manager._calculate_sha256(archive_path)
    checksum2 = manager._calculate_sha256(archive_path)
    
    # Should be identical
    assert checksum1 == checksum2
    assert len(checksum1) == 64  # SHA256 is 64 hex characters


def test_manifest_generation(temp_dirs):
    """Test manifest creation and saving"""
    cfg = BackupConfig(backup_root_dir=str(temp_dirs["backup"]))
    manager = BackupManager(cfg)
    
    manifest = BackupManifest(
        backup_id="20260122_210000",
        backup_at=datetime(2026, 1, 22, 21, 0, 0),
        archive_path="/backups/observer_20260122_210000.tar.gz",
        archive_size_bytes=1024 * 1024,  # 1 MB
        archive_sha256="a" * 64,
        files_included=42,
        total_files_size_bytes=5 * 1024 * 1024,  # 5 MB
        retention_until=datetime(2026, 2, 21, 21, 0, 0)
    )
    
    manager._save_manifest(manifest)
    
    # Check manifest file was created
    manifest_file = manager.manifests_dir / "manifest_20260122_210000.json"
    assert manifest_file.exists()
    
    # Verify manifest content
    with open(manifest_file) as f:
        data = json.load(f)
    
    assert data["backup_id"] == "20260122_210000"
    assert data["files_included"] == 42
    assert data["archive_size_bytes"] == 1024 * 1024


def test_should_backup_at_21_00():
    """Test backup scheduling at 21:00 KST"""
    cfg = BackupConfig()
    manager = BackupManager(cfg)
    
    # Test: 21:00 (should backup)
    test_time = datetime(2026, 1, 22, 21, 0, 0)
    assert manager._should_backup(test_time) == True
    
    # Test: 21:02 (within 5-minute window, should backup)
    test_time = datetime(2026, 1, 22, 21, 2, 0)
    assert manager._should_backup(test_time) == True
    
    # Test: 20:59 (before window, should not backup)
    test_time = datetime(2026, 1, 22, 20, 59, 0)
    assert manager._should_backup(test_time) == False
    
    # Test: 21:06 (after window, should not backup)
    test_time = datetime(2026, 1, 22, 21, 6, 0)
    assert manager._should_backup(test_time) == False


@pytest.mark.asyncio
async def test_cleanup_old_backups(temp_dirs):
    """Test retention policy and cleanup"""
    cfg = BackupConfig(
        source_dirs=[str(temp_dirs["config"])],
        backup_root_dir=str(temp_dirs["backup"]),
        retention_days=2  # Very short for testing
    )
    
    manager = BackupManager(cfg)
    
    # Create two backups manually
    now = manager._now()
    
    # Old backup (3 days ago)
    old_manifest = BackupManifest(
        backup_id="20260119_210000",  # 3 days ago
        backup_at=now - timedelta(days=3),
        archive_path="/backups/observer_20260119_210000.tar.gz",
        archive_size_bytes=1024 * 1024,
        archive_sha256="b" * 64,
        files_included=10,
        total_files_size_bytes=5 * 1024 * 1024,
        retention_until=now - timedelta(days=3) + timedelta(days=2)
    )
    manager._save_manifest(old_manifest)
    
    # Create dummy archive file
    old_archive = manager.archives_dir / "observer_20260119_210000.tar.gz"
    old_archive.write_bytes(b"dummy")
    
    # Recent backup (1 day ago)
    recent_manifest = BackupManifest(
        backup_id="20260121_210000",  # 1 day ago
        backup_at=now - timedelta(days=1),
        archive_path="/backups/observer_20260121_210000.tar.gz",
        archive_size_bytes=1024 * 1024,
        archive_sha256="c" * 64,
        files_included=20,
        total_files_size_bytes=5 * 1024 * 1024,
        retention_until=now - timedelta(days=1) + timedelta(days=2)
    )
    manager._save_manifest(recent_manifest)
    
    # Create dummy archive file
    recent_archive = manager.archives_dir / "observer_20260121_210000.tar.gz"
    recent_archive.write_bytes(b"dummy")
    
    # Run cleanup
    manager._cleanup_old_backups()
    
    # Check that old backup was deleted
    assert not old_archive.exists()
    assert not (manager.manifests_dir / "manifest_20260119_210000.json").exists()
    
    # Check that recent backup still exists
    assert recent_archive.exists()
    assert (manager.manifests_dir / "manifest_20260121_210000.json").exists()


@pytest.mark.asyncio
async def test_restore_from_backup(temp_dirs):
    """Test restore functionality"""
    cfg = BackupConfig(
        source_dirs=[str(temp_dirs["config"])],
        backup_root_dir=str(temp_dirs["backup"])
    )
    
    manager = BackupManager(cfg)
    
    # Create backup
    success = await manager._execute_backup()
    assert success
    
    # Get backup ID
    archives = list(manager.archives_dir.glob("observer_*.tar.gz"))
    archive_name = archives[0].name
    backup_id = archive_name.replace("observer_", "").replace(".tar.gz", "")
    
    # Restore to temp directory
    restore_dir = temp_dirs["root"] / "restored"
    success = manager.restore_from_backup(backup_id, restore_dir)
    
    assert success
    assert restore_dir.exists()


def test_get_status(temp_dirs):
    """Test status reporting"""
    cfg = BackupConfig(backup_root_dir=str(temp_dirs["backup"]))
    manager = BackupManager(cfg)
    
    status = manager.get_status()
    
    assert "running" in status
    assert "total_backups" in status
    assert "total_backup_size_bytes" in status
    assert "next_backup_time" in status
    assert "retention_days" in status
    assert status["next_backup_time"] == "21:00:00 KST"
    assert status["retention_days"] == 30


def test_list_backups(temp_dirs):
    """Test listing available backups"""
    cfg = BackupConfig(backup_root_dir=str(temp_dirs["backup"]))
    manager = BackupManager(cfg)
    
    # Should be empty initially
    backups = manager.list_backups()
    assert len(backups) == 0
    
    # Add a manifest
    manifest = BackupManifest(
        backup_id="20260122_210000",
        backup_at=datetime(2026, 1, 22, 21, 0, 0),
        archive_path="/backups/observer_20260122_210000.tar.gz",
        archive_size_bytes=1024 * 1024,
        archive_sha256="a" * 64,
        files_included=42,
        total_files_size_bytes=5 * 1024 * 1024,
        retention_until=datetime(2026, 2, 21)
    )
    manager._save_manifest(manifest)
    
    # List should now have one backup
    backups = manager.list_backups()
    assert len(backups) == 1
    assert backups[0]["backup_id"] == "20260122_210000"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
