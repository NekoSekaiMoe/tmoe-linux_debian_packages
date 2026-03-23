"""Tests for chroot advanced features.

These tests verify advanced chroot features that were available in the
shell version but may be missing or incomplete in the Python version.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from tmoe.container.chroot import ChrootBackend
from tmoe.container.base import ContainerStatus
from tmoe.core.config import ContainerConfig


@pytest.fixture
def chroot_backend(tmp_path):
    """Create a chroot backend."""
    backend = ChrootBackend()
    backend.platform = Mock()
    backend.platform.chroot_dir = tmp_path / "chroot"
    backend.platform.config_dir = tmp_path / "config"
    backend.platform.get_container_dir = Mock(return_value=tmp_path / "chroot")
    return backend


@pytest.fixture
def sample_config(tmp_path):
    """Create a sample container config."""
    rootfs = tmp_path / "rootfs"
    rootfs.mkdir()
    
    return ContainerConfig(
        name="test-chroot",
        distro="debian",
        arch="amd64",
        rootfs_path=rootfs,
        home="/root",
        user="root",
    )


class TestChrootAdvancedFeatures:
    """Test chroot advanced configuration options."""
    
    def test_chroot_required_mounts_list(self, chroot_backend):
        """Test that required mounts are properly defined."""
        required = ChrootBackend.REQUIRED_MOUNTS
        
        assert "proc" in required
        assert "sys" in required
        assert "dev" in required
        assert "dev/pts" in required
        assert "dev/shm" in required
    
    @pytest.mark.asyncio
    async def test_chroot_mount_order(self, chroot_backend, sample_config):
        """Test mount order is correct (reverse on unmount)."""
        with patch.object(chroot_backend, '_run_cmd', new_callable=AsyncMock) as mock_run:
            await chroot_backend._setup_mounts(sample_config)
            
            # Get mount order
            mount_calls = [call.args[0] for call in mock_run.call_args_list]
            
            # Verify proc is mounted
            proc_mount = next((c for c in mount_calls if "proc" in c and "-t" in c), None)
            assert proc_mount is not None
            
            # Verify dev is mounted with bind
            dev_mount = next((c for c in mount_calls if "/dev" in str(c) and "bind" in str(c)), None)
            assert dev_mount is not None


class TestChrootNspawnSupport:
    """Test systemd-nspawn support."""
    
    def test_nspawn_binary_detection(self, chroot_backend):
        """Test detection of systemd-nspawn binary."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = "/usr/bin/systemd-nspawn"
            result = chroot_backend._get_nspawn_bin()
            assert result == "/usr/bin/systemd-nspawn"


class TestChrootMountPersistence:
    """Test mount state persistence."""
    
    def test_mount_state_file_path(self, chroot_backend):
        """Test mount state file path generation."""
        path = chroot_backend._get_mount_state_path("test-container")
        assert "mounts.json" in str(path)
        assert "test-container" in str(path)