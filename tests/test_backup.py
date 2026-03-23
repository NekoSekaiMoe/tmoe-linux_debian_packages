"""Tests for container backup."""

import pytest
from pathlib import Path
from datetime import datetime

from tmoe.container.backup import BackupInfo, BackupManager
from tmoe.container.proot import ProotBackend


class TestBackupInfo:
    """Test backup info dataclass."""
    
    def test_backup_info_creation(self):
        """Test backup info creation."""
        info = BackupInfo(
            path=Path("/backup/test.tar.xz"),
            name="test.tar.xz",
            container_name="test",
            container_type="proot",
            distro="debian",
            arch="arm64",
            size=1024 * 1024 * 100,  # 100 MB
            created_at=datetime.now(),
            compression="xz",
        )
        
        assert info.name == "test.tar.xz"
        assert info.container_name == "test"
        assert info.compression == "xz"
    
    def test_backup_info_size(self):
        """Test size field."""
        info = BackupInfo(
            path=Path("/backup/test.tar.xz"),
            name="test.tar.xz",
            container_name="test",
            container_type="proot",
            distro="debian",
            arch="arm64",
            size=1024 * 1024 * 100,  # 100 MB
            created_at=datetime.now(),
            compression="xz",
        )
        
        assert info.size == 1024 * 1024 * 100


class TestBackupManager:
    """Test backup manager."""
    
    def test_manager_creation(self):
        """Test manager creation."""
        from tmoe.core.platform import PlatformInfo
        platform = PlatformInfo()
        manager = BackupManager(platform)
        
        assert manager is not None
        assert "backups" in str(manager._backup_dir)
    
    def test_get_backup_path(self):
        """Test backup path generation."""
        from tmoe.core.platform import PlatformInfo
        platform = PlatformInfo()
        manager = BackupManager(platform)
        
        path = manager._get_backup_path("my-container")
        assert "my-container" in str(path)
        assert str(path).endswith(".tar.zst")
