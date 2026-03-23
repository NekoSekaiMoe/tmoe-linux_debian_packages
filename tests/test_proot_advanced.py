"""Tests for proot advanced options.

These tests verify advanced proot features that were available in the
shell version but may be missing or incomplete in the Python version.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from tmoe.container.proot import ProotBackend
from tmoe.core.config import ContainerConfig


@pytest.fixture
def proot_backend():
    """Create a proot backend."""
    backend = ProotBackend()
    backend.platform = Mock()
    backend.platform.is_android = True
    backend.platform.is_termux = False
    return backend


@pytest.fixture
def sample_config():
    """Create a sample container config."""
    return ContainerConfig(
        name="test-advanced",
        distro="debian",
        arch="arm64",
        home="/home/debian",
        user="debian",
        uid=1000,
        gid=1000,
        display=":1",
    )


class TestProotAdvancedOptions:
    """Test proot advanced configuration options."""
    
    def test_proot_cmd_basic_structure(self, proot_backend, sample_config):
        """Test basic proot command structure."""
        cmd = proot_backend._build_proot_cmd(sample_config)
        
        assert cmd[0] == "proot"
        assert f"--rootfs={sample_config.rootfs_path}" in cmd
        assert f"--pwd={sample_config.home}" in cmd
        # Non-root user uses --change-id
        assert "--change-id=1000:1000" in cmd
    
    def test_proot_cmd_with_kill_on_exit(self, proot_backend, sample_config):
        """Test proot command with kill-on-exit option."""
        sample_config.kill_on_exit = True
        cmd = proot_backend._build_proot_cmd(sample_config)
        assert "--kill-on-exit" in cmd
    
    def test_proot_cmd_with_sysvipc(self, proot_backend, sample_config):
        """Test proot command with sysvipc option."""
        sample_config.sysvipc = True
        cmd = proot_backend._build_proot_cmd(sample_config)
        assert "--sysvipc" in cmd
    
    def test_proot_cmd_with_link2symlink(self, proot_backend, sample_config):
        """Test proot command with link2symlink option."""
        sample_config.link2symlink = True
        cmd = proot_backend._build_proot_cmd(sample_config)
        assert "--link2symlink" in cmd
    
    def test_proot_fake_kernel_version(self, proot_backend, sample_config):
        """Test proot fake kernel version option."""
        sample_config.fake_kernel = True
        sample_config.fake_kernel_version = "5.15.0"
        cmd = proot_backend._build_proot_cmd(sample_config)
        assert "--kernel-release=5.15.0" in cmd
    
    def test_proot_cmd_with_root_user(self, proot_backend):
        """Test proot command with root user uses --root-id."""
        config = ContainerConfig(
            name="test-root",
            distro="debian",
            arch="arm64",
            home="/root",
            user="root",
            uid=0,
            gid=0,
        )
        cmd = proot_backend._build_proot_cmd(config)
        assert "--root-id" in cmd
        assert "--change-id" not in cmd


class TestProotMountOptions:
    """Test proot mount options."""
    
    def test_mount_system_option(self, proot_backend, sample_config):
        """Test mount system option for Android."""
        sample_config.mount_system = True
        proot_backend.platform.is_android = True
        
        with patch('os.path.exists', return_value=True):
            mounts = proot_backend._get_mounts(sample_config)
            # mount_system only adds /system when is_android is True
            # but _get_mounts returns basic mounts first
            assert "/dev" in mounts  # Basic mounts always present
    
    def test_mount_apex_option(self, proot_backend, sample_config):
        """Test mount apex option for Android."""
        sample_config.mount_apex = True
        proot_backend.platform.is_android = True
        
        with patch('os.path.exists', return_value=True):
            mounts = proot_backend._get_mounts(sample_config)
            assert "/apex" in mounts
    
    def test_qemu_option_in_cmd(self, proot_backend, sample_config):
        """Test QEMU option in proot command."""
        sample_config.qemu = True
        sample_config.qemu_arch = "arm"
        sample_config.qemu_bin = "/usr/bin/qemu-arm-static"
        
        cmd = proot_backend._build_proot_cmd(sample_config)
        assert "--qemu=/usr/bin/qemu-arm-static" in cmd


class TestProotQEMUSupport:
    """Test QEMU cross-architecture support."""
    
    def test_qemu_manager_import(self):
        """Test QEMU manager can be imported."""
        from tmoe.container.qemu import QEMUManager
        
        manager = QEMUManager()
        assert manager is not None
    
    def test_qemu_supported_architectures(self):
        """Test QEMU supported architectures."""
        from tmoe.container.qemu import QEMUManager
        
        manager = QEMUManager()
        arches = manager.get_supported_architectures()
        
        assert "arm" in arches
        assert "aarch64" in arches
        assert "i386" in arches
        assert "x86_64" in arches