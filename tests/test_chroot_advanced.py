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
    
    @pytest.mark.asyncio
    async def test_chroot_required_mounts_list(self, chroot_backend):
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
            
            # Verify proc is mounted first
            proc_mount = next((c for c in mount_calls if "proc" in c and "-t" in c), None)
            assert proc_mount is not None
            
            # Verify dev is mounted
            dev_mount = next((c for c in mount_calls if "/dev" in c and "--rbind" in c), None)
            assert dev_mount is not None
    
    @pytest.mark.asyncio
    async def test_chroot_unmount_order(self, chroot_backend, sample_config):
        """Test unmount order is reverse of mount order."""
        # Setup fake active mounts
        chroot_backend._active_mounts["test-chroot"] = [
            str(sample_config.rootfs_path / "proc"),
            str(sample_config.rootfs_path / "sys"),
            str(sample_config.rootfs_path / "dev"),
            str(sample_config.rootfs_path / "dev" / "pts"),
            str(sample_config.rootfs_path / "dev" / "shm"),
        ]
        
        with patch.object(chroot_backend, '_run_cmd', new_callable=AsyncMock) as mock_run:
            await chroot_backend._cleanup_mounts(sample_config)
            
            # Get unmount order
            unmount_calls = [call.args[0] for call in mock_run.call_args_list]
            
            # Should unmount in reverse order
            # shm -> pts -> dev -> sys -> proc
            assert unmount_calls[0][-1].endswith("shm")
            assert unmount_calls[-1][-1].endswith("proc")


class TestChrootUnshareFeatures:
    """Test chroot unshare namespace features.
    
    These features exist in shell version but may be missing in Python.
    """
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    @pytest.mark.asyncio
    async def test_unshare_mode_enabled(self):
        """Test chroot with unshare namespace isolation.
        
        Shell version supports UNSHARE_ENABLED for namespace isolation:
        - UNSHARE_IPC: IPC namespace
        - UNSHARE_PID: PID namespace
        - UNSHARE_UTS: UTS namespace
        - UNSHARE_MOUNT: Mount namespace
        """
        backend = ChrootBackend()
        
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="amd64",
            unshare_enabled=True,
            unshare_ipc=True,
            unshare_pid=True,
            unshare_uts=True,
            unshare_mount=True,
        )
        
        # Should use unshare command wrapper
        # e.g., unshare --ipc --pid --uts --mount chroot ...
        pass
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    @pytest.mark.asyncio
    async def test_unshare_ipc_namespace(self):
        """Test IPC namespace isolation."""
        backend = ChrootBackend()
        
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="amd64",
            unshare_ipc=True,
        )
        
        # Should include --ipc flag
        pass
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    @pytest.mark.asyncio
    async def test_unshare_pid_namespace(self):
        """Test PID namespace isolation."""
        backend = ChrootBackend()
        
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="amd64",
            unshare_pid=True,
        )
        
        # Should include --pid and --fork flags
        pass
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    @pytest.mark.asyncio
    async def test_kill_child_processes(self):
        """Test kill child processes option.
        
        Shell version supports KILL_CHILD for cleaning up all child
        processes when the container stops.
        """
        backend = ChrootBackend()
        
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="amd64",
            kill_child=True,
        )
        
        # Should kill all child processes on exit
        pass


class TestChrootSystemdNspawnIntegration:
    """Test chroot integration with systemd-nspawn.
    
    Shell version has extensive systemd-nspawn support.
    """
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    @pytest.mark.asyncio
    async def test_systemd_nspawn_boot_mode(self):
        """Test systemd-nspawn boot mode.
        
        Shell version supports SYSTEMD_BOOT=true for running
        systemd as PID 1 inside the container.
        """
        backend = ChrootBackend()
        
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="amd64",
            systemd_boot=True,
        )
        
        # Should use systemd-nspawn with --boot
        pass
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    @pytest.mark.asyncio
    async def test_systemd_nspawn_user(self):
        """Test systemd-nspawn user configuration."""
        backend = ChrootBackend()
        
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="amd64",
            chroot_user="debian",
        )
        
        # Should use systemd-nspawn with --user
        pass
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    @pytest.mark.asyncio
    async def test_systemd_nspawn_gpu_mount(self):
        """Test GPU device mounting with systemd-nspawn."""
        backend = ChrootBackend()
        
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="amd64",
            mount_dev_dri=True,
            mount_nvidia_gpu=True,
        )
        
        # Should mount GPU devices
        pass


class TestChrootMountManagement:
    """Test chroot mount management features."""
    
    @pytest.mark.asyncio
    async def test_active_mounts_tracking(self, chroot_backend, sample_config):
        """Test that active mounts are tracked properly."""
        with patch.object(chroot_backend, '_run_cmd', new_callable=AsyncMock):
            # Initially empty
            assert len(chroot_backend._active_mounts) == 0
            
            # Setup mounts
            await chroot_backend._setup_mounts(sample_config)
            
            # Should track mounts
            assert "test-chroot" in chroot_backend._active_mounts
            assert len(chroot_backend._active_mounts["test-chroot"]) >= 5
    
    @pytest.mark.asyncio
    async def test_mount_cleanup_on_error(self, chroot_backend, sample_config):
        """Test mounts are cleaned up even on error."""
        with patch.object(chroot_backend, '_run_cmd', new_callable=AsyncMock) as mock_run:
            await chroot_backend._setup_mounts(sample_config)
            
            # Simulate an error
            mock_run.side_effect = RuntimeError("Mount failed")
            
            # Cleanup should still work
            try:
                await chroot_backend._cleanup_mounts(sample_config)
            except Exception:
                pass
            
            # Mounts should be cleared from tracking
            assert "test-chroot" not in chroot_backend._active_mounts
    
    @pytest.mark.asyncio
    async def test_mount_directory_creation(self, chroot_backend, sample_config):
        """Test mount directories are created if missing."""
        # Remove mount directories
        for subdir in ["proc", "sys", "dev", "dev/pts", "dev/shm"]:
            path = sample_config.rootfs_path / subdir
            if path.exists():
                path.rmdir()
        
        with patch.object(chroot_backend, '_run_cmd', new_callable=AsyncMock):
            await chroot_backend._setup_mounts(sample_config)
            
            # Directories should be created
            assert (sample_config.rootfs_path / "proc").exists()
            assert (sample_config.rootfs_path / "sys").exists()
            assert (sample_config.rootfs_path / "dev").exists()
            assert (sample_config.rootfs_path / "dev" / "pts").exists()
            assert (sample_config.rootfs_path / "dev" / "shm").exists()


class TestChrootStatusDetection:
    """Test chroot container status detection."""
    
    @pytest.mark.asyncio
    async def test_status_running_when_mounted(self, chroot_backend, tmp_path):
        """Test status is RUNNING when container is mounted."""
        chroot_backend.platform.chroot_dir = tmp_path / "chroot"
        chroot_backend.platform.get_container_dir = Mock(return_value=tmp_path / "chroot")
        
        # Create container directory
        container_path = tmp_path / "chroot" / "test-running"
        container_path.mkdir(parents=True, exist_ok=True)
        
        # Mock /proc/mounts to show container is mounted
        mounts_content = str(container_path / "proc") + " proc proc rw 0 0\n"
        
        with patch('pathlib.Path.read_text', return_value=mounts_content):
            status = await chroot_backend._get_status("test-running")
            assert status == ContainerStatus.RUNNING
    
    @pytest.mark.asyncio
    async def test_status_stopped_when_not_mounted(self, chroot_backend, tmp_path):
        """Test status is STOPPED when container is not mounted."""
        chroot_backend.platform.chroot_dir = tmp_path / "chroot"
        chroot_backend.platform.get_container_dir = Mock(return_value=tmp_path / "chroot")
        
        # Create container directory
        container_path = tmp_path / "chroot" / "test-stopped"
        container_path.mkdir(parents=True, exist_ok=True)
        
        # Mock /proc/mounts with no container mounts
        mounts_content = "none /proc proc rw 0 0\n"
        
        with patch('pathlib.Path.read_text', return_value=mounts_content):
            status = await chroot_backend._get_status("test-stopped")
            assert status == ContainerStatus.STOPPED


class TestChrootEnvironmentVariables:
    """Test chroot environment variable setup."""
    
    def test_chroot_env_vars_structure(self):
        """Test chroot environment variables structure."""
        backend = ChrootBackend()
        
        config = ContainerConfig(
            name="test-chroot",
            distro="ubuntu",
            arch="amd64",
            home="/home/user",
            user="user",
            display=":1",
        )
        
        env_vars = backend._get_env_vars(config)
        
        assert env_vars["HOSTNAME"] == "test-chroot"
        assert env_vars["HOME"] == "/home/user"
        assert env_vars["USER"] == "user"
        assert env_vars["DISPLAY"] == ":1"
        assert env_vars["TMOE_CHROOT"] == "true"
        assert env_vars["TMOE_PROOT"] == "false"
        assert env_vars["TMOE_CONTAINER_NAME"] == "test-chroot"
        assert env_vars["TMOE_CONTAINER_TYPE"] == "chroot"
    
    def test_chroot_env_terminal(self):
        """Test chroot TERM environment variable."""
        backend = ChrootBackend()
        
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="amd64",
        )
        
        env_vars = backend._get_env_vars(config)
        
        assert env_vars["TERM"] == "xterm-256color"


class TestChrootCommandExecution:
    """Test command execution in chroot containers."""
    
    @pytest.mark.asyncio
    async def test_exec_command(self, chroot_backend, sample_config):
        """Test executing a command in chroot."""
        # Save config file first so container exists
        config_path = sample_config.rootfs_path.parent / "config" / f"{sample_config.name}.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        config_path.write_text(json.dumps({
            "name": sample_config.name,
            "distro": sample_config.distro,
            "arch": sample_config.arch,
            "rootfs_path": str(sample_config.rootfs_path),
            "home": sample_config.home,
            "user": sample_config.user,
            "container_type": "chroot",
        }))
        
        with patch.object(chroot_backend, 'check_root'):
            with patch.object(chroot_backend, '_setup_mounts', new_callable=AsyncMock) as mock_setup:
                with patch.object(chroot_backend, '_cleanup_mounts', new_callable=AsyncMock) as mock_cleanup:
                    with patch('asyncio.create_subprocess_exec', new_callable=AsyncMock) as mock_proc:
                        mock_proc.return_value.communicate = AsyncMock(return_value=(b"output", b"error"))
                        mock_proc.return_value.returncode = 0
                        
                        returncode, stdout, stderr = await chroot_backend.exec(
                            sample_config.name,
                            ["ls", "-la"]
                        )
                        
                        assert returncode == 0
                        assert stdout == "output"
                        assert stderr == "error"
                        mock_setup.assert_called_once()
                        mock_cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_exec_cleanup_on_error(self, chroot_backend, sample_config):
        """Test cleanup happens even on exec error."""
        # Save config file first so container exists
        config_path = sample_config.rootfs_path.parent / "config" / f"{sample_config.name}.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        config_path.write_text(json.dumps({
            "name": sample_config.name,
            "distro": sample_config.distro,
            "arch": sample_config.arch,
            "rootfs_path": str(sample_config.rootfs_path),
            "home": sample_config.home,
            "user": sample_config.user,
            "container_type": "chroot",
        }))
        
        with patch.object(chroot_backend, 'check_root'):
            with patch.object(chroot_backend, '_setup_mounts', new_callable=AsyncMock):
                with patch.object(chroot_backend, '_cleanup_mounts', new_callable=AsyncMock) as mock_cleanup:
                    with patch('asyncio.create_subprocess_exec', side_effect=RuntimeError("Exec failed")):
                        
                        with pytest.raises(RuntimeError):
                            await chroot_backend.exec(sample_config.name, ["ls"])
                        
                        # Cleanup should still be called
                        mock_cleanup.assert_called_once()


class TestChrootSafetyFeatures:
    """Test chroot safety features."""
    
    @pytest.mark.asyncio
    async def test_proc_mounted_safety_check(self, chroot_backend, sample_config):
        """Test safety check prevents removal when /proc is mounted."""
        # Save config file first so container exists
        config_path = sample_config.rootfs_path.parent / "config" / f"{sample_config.name}.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        config_path.write_text(json.dumps({
            "name": sample_config.name,
            "distro": sample_config.distro,
            "arch": sample_config.arch,
            "rootfs_path": str(sample_config.rootfs_path),
            "home": sample_config.home,
            "user": sample_config.user,
            "container_type": "chroot",
        }))
        
        # Create fake /proc with content
        proc_dir = sample_config.rootfs_path / "proc"
        proc_dir.mkdir()
        (proc_dir / "1").mkdir()
        (proc_dir / "self").symlink_to("1")
        
        with patch.object(chroot_backend, 'check_root'):
            with patch.object(chroot_backend, '_get_status', return_value=ContainerStatus.STOPPED):
                with pytest.raises(RuntimeError, match="Safety check failed"):
                    await chroot_backend.remove(sample_config.name)
    
    @pytest.mark.asyncio
    async def test_remove_nonexistent_container(self, chroot_backend):
        """Test removing nonexistent container raises error."""
        with patch.object(chroot_backend, 'check_root'):
            with pytest.raises(ValueError, match="not found"):
                await chroot_backend.remove("nonexistent")
    
    @pytest.mark.asyncio
    async def test_remove_running_container_without_force(self, chroot_backend, sample_config):
        """Test removing running container without force raises error."""
        # Save config file first so container exists
        config_path = sample_config.rootfs_path.parent / "config" / f"{sample_config.name}.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        config_path.write_text(json.dumps({
            "name": sample_config.name,
            "distro": sample_config.distro,
            "arch": sample_config.arch,
            "rootfs_path": str(sample_config.rootfs_path),
            "home": sample_config.home,
            "user": sample_config.user,
            "container_type": "chroot",
        }))
        
        with patch.object(chroot_backend, 'check_root'):
            with patch.object(chroot_backend, '_get_status', return_value=ContainerStatus.RUNNING):
                with pytest.raises(RuntimeError, match="is running"):
                    await chroot_backend.remove(sample_config.name, force=False)
