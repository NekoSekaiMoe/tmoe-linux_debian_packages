"""Tests for container backup."""

import pytest
from pathlib import Path
from datetime import datetime

from tmoe.container.backup import BackupInfo, ContainerBackupManager
from tmoe.container.proot import ProotBackend


class TestBackupInfo:
    """Test backup info dataclass."""
    
    def test_backup_info_creation(self):
        """Test backup info creation."""
        info = BackupInfo(
            path=Path("/backup/test.tar.xz"),
            name="test.tar.xz",
            container_name="test",
            created_at=datetime.now(),
            size_bytes=1024 * 1024 * 100,  # 100 MB
            compression="xz",
        )
        
        assert info.name == "test.tar.xz"
        assert info.container_name == "test"
        assert info.compression == "xz"
    
    def test_backup_info_size_human(self):
        """Test human-readable size."""
        info = BackupInfo(
            path=Path("/backup/test.tar.xz"),
            name="test.tar.xz",
            container_name="test",
            created_at=datetime.now(),
            size_bytes=1024 * 1024 * 100,  # 100 MB
            compression="xz",
        )
        
        assert "MB" in info.size_human
        assert "100" in info.size_human
    
    def test_backup_info_size_human_gb(self):
        """Test human-readable size in GB."""
        info = BackupInfo(
            path=Path("/backup/test.tar.xz"),
            name="test.tar.xz",
            container_name="test",
            created_at=datetime.now(),
            size_bytes=1024 * 1024 * 1024 * 2,  # 2 GB
            compression="xz",
        )
        
        assert "GB" in info.size_human


class TestContainerBackupManager:
    """Test backup manager."""
    
    def test_manager_creation(self, tmp_path):
        """Test manager creation."""
        backend = ProotBackend()
        manager = ContainerBackupManager(backend, tmp_path)
        
        assert manager is not None
        assert manager.backend == backend
        assert manager.backup_dir == tmp_path
    
    def test_manager_with_custom_dir(self, tmp_path):
        """Test manager with custom backup directory."""
        backend = ProotBackend()
        manager = ContainerBackupManager(backend, tmp_path)
        
        assert manager.backup_dir == tmp_path
    
    def test_generate_backup_name(self, tmp_path):
        """Test backup name generation."""
        backend = ProotBackend()
        manager = ContainerBackupManager(backend, tmp_path)
        
        name = manager._generate_backup_name("my-container")
        assert name.startswith("my-container_")
        assert len(name) > len("my-container_")
