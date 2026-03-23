"""Tests for container lifecycle operations.

These tests verify the complete lifecycle of containers including
creation, installation, starting, stopping, and removal.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from tmoe.container.proot import ProotBackend
from tmoe.container.chroot import ChrootBackend
from tmoe.container.base import ContainerStatus
from tmoe.core.config import ContainerConfig


@pytest.fixture
def proot_backend(tmp_path):
    """Create a proot backend with temp directories."""
    platform = Mock()
    platform.proot_dir = tmp_path / "proot"
    platform.config_dir = tmp_path / "config"
    platform.proot_dir.mkdir(parents=True, exist_ok=True)
    platform.config_dir.mkdir(parents=True, exist_ok=True)
    platform.normalized_arch = "arm64"
    platform.is_android = True
    platform.is_termux = True
    platform.get_container_dir = Mock(return_value=tmp_path / "proot")
    
    backend = ProotBackend(platform)
    backend.config = Mock()
    backend.config.default_codename = "stable"
    backend.config.pulse_server = "127.0.0.1"
    backend.config.pulse_port = 4713
    
    return backend


class TestProotContainerLifecycle:
    """Test proot container full lifecycle."""
    
    @pytest.mark.asyncio
    async def test_container_create(self, proot_backend):
        """Test container creation."""
        config = await proot_backend.create(
            name="test-debian",
            distro="debian",
            arch="arm64",
            codename="bookworm"
        )
        
        assert config.name == "test-debian"
        assert config.distro == "debian"
        assert config.arch == "arm64"
        assert config.codename == "bookworm"
        assert config.container_type == "proot"
        assert config.rootfs_path is not None
    
    @pytest.mark.asyncio
    async def test_container_create_duplicate(self, proot_backend):
        """Test creating duplicate container raises error."""
        await proot_backend.create("test-dup", "debian")
        
        with pytest.raises(ValueError, match="already exists"):
            await proot_backend.create("test-dup", "debian")
    
    @pytest.mark.asyncio
    async def test_container_exists(self, proot_backend):
        """Test container existence check."""
        # Initially doesn't exist
        assert not await proot_backend.exists("nonexistent")
        
        # Create container
        await proot_backend.create("test-exists", "debian")
        
        # Now exists
        assert await proot_backend.exists("test-exists")
    
    @pytest.mark.asyncio
    async def test_container_get_info(self, proot_backend):
        """Test getting container info."""
        # Create container
        await proot_backend.create("test-info", "ubuntu", "amd64")
        
        # Get info
        info = await proot_backend.get_info("test-info")
        
        assert info is not None
        assert info.name == "test-info"
        assert info.config.distro == "ubuntu"
        assert info.config.arch == "amd64"
        assert info.status in [ContainerStatus.RUNNING, ContainerStatus.STOPPED]
    
    @pytest.mark.asyncio
    async def test_container_get_info_nonexistent(self, proot_backend):
        """Test getting info for nonexistent container returns None."""
        info = await proot_backend.get_info("nonexistent")
        assert info is None
    
    @pytest.mark.asyncio
    async def test_container_list(self, proot_backend):
        """Test listing containers."""
        # Initially empty
        containers = await proot_backend.list_containers()
        assert len(containers) == 0
        
        # Create some containers
        await proot_backend.create("container-1", "debian")
        await proot_backend.create("container-2", "ubuntu")
        await proot_backend.create("container-3", "arch")
        
        # List containers
        containers = await proot_backend.list_containers()
        assert len(containers) == 3
        
        names = {c.name for c in containers}
        assert names == {"container-1", "container-2", "container-3"}
    
    @pytest.mark.asyncio
    async def test_container_remove(self, proot_backend):
        """Test container removal."""
        # Create container
        await proot_backend.create("test-remove", "debian")
        assert await proot_backend.exists("test-remove")
        
        # Remove container
        await proot_backend.remove("test-remove")
        
        # Should not exist anymore
        assert not await proot_backend.exists("test-remove")
    
    @pytest.mark.asyncio
    async def test_container_remove_nonexistent(self, proot_backend):
        """Test removing nonexistent container raises error."""
        with pytest.raises(ValueError, match="not found"):
            await proot_backend.remove("nonexistent")
    
    @pytest.mark.asyncio
    async def test_container_remove_running_with_force(self, proot_backend):
        """Test removing running container with force flag."""
        await proot_backend.create("test-running", "debian")
        
        # Mock running status
        with patch.object(proot_backend, '_get_status', return_value=ContainerStatus.RUNNING):
            with patch.object(proot_backend, 'stop', new_callable=AsyncMock) as mock_stop:
                await proot_backend.remove("test-running", force=True)
                mock_stop.assert_called_once_with("test-running")


@pytest.fixture
def chroot_backend(tmp_path):
    """Create a chroot backend with temp directories."""
    platform = Mock()
    platform.chroot_dir = tmp_path / "chroot"
    platform.config_dir = tmp_path / "config"
    platform.chroot_dir.mkdir(parents=True, exist_ok=True)
    platform.config_dir.mkdir(parents=True, exist_ok=True)
    platform.normalized_arch = "amd64"
    platform.get_container_dir = Mock(return_value=tmp_path / "chroot")
    
    backend = ChrootBackend(platform)
    backend.config = Mock()
    backend.config.default_codename = "stable"
    
    return backend


class TestChrootContainerLifecycle:
    """Test chroot container full lifecycle."""
    
    @pytest.mark.asyncio
    async def test_chroot_requires_root(self, chroot_backend):
        """Test chroot backend requires root."""
        assert chroot_backend.requires_root is True
    
    @pytest.mark.asyncio
    async def test_chroot_create(self, chroot_backend):
        """Test chroot container creation."""
        with patch.object(chroot_backend, 'check_root'):
            config = await chroot_backend.create(
                name="test-chroot",
                distro="debian",
                arch="amd64"
            )
            
            assert config.name == "test-chroot"
            assert config.distro == "debian"
            assert config.arch == "amd64"
            assert config.container_type == "chroot"
    
    @pytest.mark.asyncio
    async def test_chroot_create_checks_root(self, chroot_backend):
        """Test chroot creation checks for root."""
        with patch.object(chroot_backend, 'check_root', side_effect=PermissionError("Root required")):
            with pytest.raises(PermissionError):
                await chroot_backend.create("test", "debian")
    
    @pytest.mark.asyncio
    async def test_chroot_mounts_setup(self, chroot_backend):
        """Test chroot mount setup."""
        with patch.object(chroot_backend, 'check_root'):
            config = await chroot_backend.create("test-mounts", "debian")
            
            # Create mock rootfs structure
            config.rootfs_path.mkdir(parents=True, exist_ok=True)
            
            with patch.object(chroot_backend, '_run_cmd', new_callable=AsyncMock) as mock_run:
                await chroot_backend._setup_mounts(config)
                
                # Should mount proc, sys, dev, dev/pts, dev/shm
                assert mock_run.call_count >= 5
                
                # Verify mounts are tracked
                assert "test-mounts" in chroot_backend._active_mounts
                assert len(chroot_backend._active_mounts["test-mounts"]) >= 5
    
    @pytest.mark.asyncio
    async def test_chroot_mounts_cleanup(self, chroot_backend):
        """Test chroot mount cleanup."""
        with patch.object(chroot_backend, 'check_root'):
            config = await chroot_backend.create("test-cleanup", "debian")
            config.rootfs_path.mkdir(parents=True, exist_ok=True)
            
            # Setup fake active mounts
            chroot_backend._active_mounts["test-cleanup"] = [
                str(config.rootfs_path / "proc"),
                str(config.rootfs_path / "sys"),
                str(config.rootfs_path / "dev"),
            ]
            
            with patch.object(chroot_backend, '_run_cmd', new_callable=AsyncMock) as mock_run:
                await chroot_backend._cleanup_mounts(config)
                
                # Should unmount in reverse order
                assert mock_run.call_count == 3
                
                # Verify mounts are cleared
                assert "test-cleanup" not in chroot_backend._active_mounts
    
    @pytest.mark.asyncio
    async def test_chroot_remove_safety_check(self, chroot_backend):
        """Test chroot remove safety check for mounted /proc."""
        with patch.object(chroot_backend, 'check_root'):
            config = await chroot_backend.create("test-safety", "debian")
            config.rootfs_path.mkdir(parents=True, exist_ok=True)
            
            # Create fake /proc directory with content (simulating mounted)
            proc_path = config.rootfs_path / "proc"
            proc_path.mkdir()
            (proc_path / "1").mkdir()  # PID 1 directory
            
            with patch.object(chroot_backend, '_get_status', return_value=ContainerStatus.STOPPED):
                with pytest.raises(RuntimeError, match="Safety check failed"):
                    await chroot_backend.remove("test-safety")


class TestContainerEnvironmentPropagation:
    """Test environment variable propagation to containers."""
    
    def test_proot_env_vars(self):
        """Test proot environment variables."""
        backend = ProotBackend()
        
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="arm64",
            home="/home/debian",
            user="debian",
            display=":1",
        )
        
        env_vars = backend._get_env_vars(config)
        
        assert env_vars["HOSTNAME"] == "test"
        assert env_vars["HOME"] == "/home/debian"
        assert env_vars["USER"] == "debian"
        assert env_vars["DISPLAY"] == ":1"
        assert env_vars["TMOE_PROOT"] == "true"
        assert env_vars["TMOE_CHROOT"] == "false"
        assert env_vars["TMOE_CONTAINER_NAME"] == "test"
        
        # Input method settings
        assert env_vars["GTK_IM_MODULE"] == "fcitx"
        assert env_vars["QT_IM_MODULE"] == "fcitx"
        assert env_vars["XMODIFIERS"] == "@im=fcitx"
    
    def test_chroot_env_vars(self):
        """Test chroot environment variables."""
        backend = ChrootBackend()
        
        config = ContainerConfig(
            name="test-chroot",
            distro="ubuntu",
            arch="amd64",
            home="/root",
            user="root",
            display=":0",
        )
        
        env_vars = backend._get_env_vars(config)
        
        assert env_vars["HOSTNAME"] == "test-chroot"
        assert env_vars["HOME"] == "/root"
        assert env_vars["USER"] == "root"
        assert env_vars["DISPLAY"] == ":0"
        assert env_vars["TMOE_PROOT"] == "false"
        assert env_vars["TMOE_CHROOT"] == "true"


class TestContainerMounts:
    """Test container mount management."""
    
    def test_proot_mounts_android(self):
        """Test proot mounts on Android."""
        backend = ProotBackend()
        backend.platform = Mock()
        backend.platform.is_android = True
        backend.platform.is_termux = True
        
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="arm64",
            mount_system=True,
            mount_apex=True,
            mount_termux=True,
        )
        
        mounts = backend._get_mounts(config)
        
        assert "/system" in mounts
        assert "/dev" in mounts
        assert "/proc" in mounts
    
    def test_proot_custom_mounts(self):
        """Test proot custom mounts."""
        backend = ProotBackend()
        backend.platform = Mock()
        backend.platform.is_android = False
        backend.platform.is_termux = False
        
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="arm64",
            custom_mounts=[
                {"source": "/host/data", "target": "/data"},
                {"source": "/host/media", "target": "/media"},
            ]
        )
        
        mounts = backend._get_mounts(config)
        
        assert "/host/data:/data" in mounts
        assert "/host/media:/media" in mounts
    
    @pytest.mark.asyncio
    async def test_chroot_required_mounts(self):
        """Test chroot required mounts."""
        backend = ChrootBackend()
        
        assert "proc" in backend.REQUIRED_MOUNTS
        assert "sys" in backend.REQUIRED_MOUNTS
        assert "dev" in backend.REQUIRED_MOUNTS
        assert "dev/pts" in backend.REQUIRED_MOUNTS
        assert "dev/shm" in backend.REQUIRED_MOUNTS
