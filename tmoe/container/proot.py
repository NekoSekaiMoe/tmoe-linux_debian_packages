"""Proot container backend for TMOE.

Proot provides user-mode containers that don't require root privileges,
making them ideal for Android/Termux environments.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from tmoe.container.base import ContainerBackend, ContainerInfo, ContainerStatus
from tmoe.core.config import ContainerConfig, get_config
from tmoe.core.constants import ARCH_MAPPINGS
from tmoe.core.platform import PlatformInfo

if TYPE_CHECKING:
    from collections.abc import Sequence


class ProotBackend(ContainerBackend):
    """Proot container backend implementation.
    
    Proot is a user-space implementation of chroot that doesn't require
    root privileges. It works by intercepting system calls and redirecting
    file system operations.
    
    Features:
    - No root required
    - Works on Android/Termux
    - Cross-architecture support via QEMU
    - link2symlink for better compatibility
    
    Example:
        >>> backend = ProotBackend()
        >>> config = await backend.create("my-debian", "debian", "arm64")
        >>> await backend.start("my-debian")
    """
    
    def __init__(self, platform: PlatformInfo | None = None) -> None:
        super().__init__(platform)
        self._proot_bin: str | None = None
    
    @property
    def backend_type(self) -> str:
        return "proot"
    
    @property
    def requires_root(self) -> bool:
        return False
    
    @property
    def proot_bin(self) -> str:
        """Get proot binary path."""
        if self._proot_bin is None:
            self._proot_bin = shutil.which("proot") or "proot"
        return self._proot_bin
    
    async def list_containers(self) -> list[ContainerInfo]:
        """List all proot containers.
        
        Returns:
            List of ContainerInfo objects for proot containers.
        """
        containers: list[ContainerInfo] = []
        proot_dir = self.platform.proot_dir
        
        if not proot_dir.exists():
            return containers
        
        for path in proot_dir.iterdir():
            if path.is_dir():
                name = path.name
                config = self.load_container_config(name)
                if config:
                    info = ContainerInfo(
                        name=name,
                        config=config,
                        status=await self._get_status(name),
                    )
                    containers.append(info)
        
        return containers
    
    async def _get_status(self, name: str) -> ContainerStatus:
        """Get container status."""
        # Check if proot process exists
        cmd = ["pgrep", "-f", f"proot.*{name}"]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
            if proc.returncode == 0:
                return ContainerStatus.RUNNING
        except Exception:
            pass
        return ContainerStatus.STOPPED
    
    async def exists(self, name: str) -> bool:
        """Check if a proot container exists."""
        container_path = self.get_container_path(name)
        return container_path.exists()
    
    async def get_info(self, name: str) -> ContainerInfo | None:
        """Get information about a proot container."""
        if not await self.exists(name):
            return None
        
        config = self.load_container_config(name)
        if not config:
            return None
        
        return ContainerInfo(
            name=name,
            config=config,
            status=await self._get_status(name),
        )
    
    async def create(
        self,
        name: str,
        distro: str,
        arch: str | None = None,
        codename: str | None = None,
    ) -> ContainerConfig:
        """Create a new proot container configuration.
        
        Note: This only creates the configuration. Use install() to
        actually download and set up the rootfs.
        
        Args:
            name: Container name.
            distro: Linux distribution (e.g., 'debian', 'ubuntu').
            arch: Architecture (defaults to host arch).
            codename: Distribution codename (e.g., 'stable', 'jammy').
            
        Returns:
            ContainerConfig for the new container.
        """
        if await self.exists(name):
            raise ValueError(f"Container '{name}' already exists")
        
        arch = arch or self.platform.normalized_arch
        codename = codename or self.config.default_codename
        
        container_path = self.get_container_path(name)
        
        config = ContainerConfig(
            name=name,
            distro=distro,
            arch=arch,
            codename=codename,
            rootfs_path=container_path,
            container_type="proot",
            home=f"/home/{distro}" if distro != "root" else "/root",
        )
        
        self.save_container_config(config)
        return config
    
    async def install(
        self,
        name: str,
        distro: str,
        arch: str | None = None,
        codename: str | None = None,
    ) -> ContainerConfig:
        """Install a new proot container with rootfs.
        
        This method downloads and sets up the container rootfs.
        
        Args:
            name: Container name.
            distro: Linux distribution.
            arch: Architecture.
            codename: Distribution codename.
            
        Returns:
            ContainerConfig for the installed container.
        """
        from tmoe.container.install import ContainerInstaller
        
        # Create config first
        config = await self.create(name, distro, arch, codename)
        
        # Download and install rootfs
        installer = ContainerInstaller(self.platform)
        await installer.install_proot(config)
        
        return config
    
    def _build_proot_cmd(
        self,
        config: ContainerConfig,
        command: Sequence[str] | None = None,
    ) -> list[str]:
        """Build proot command with all necessary options."""
        cmd = [self.proot_bin]
        
        # Basic options
        cmd.extend([
            f"--rootfs={config.rootfs_path}",
            f"--pwd={config.home}",
        ])
        
        # User options
        if config.user != "root":
            cmd.append(f"--user={config.uid}:{config.gid}")
        
        # Feature flags
        if config.kill_on_exit:
            cmd.append("--kill-on-exit")
        if config.sysvipc:
            cmd.append("--sysvipc")
        if config.link2symlink:
            cmd.append("--link2symlink")
        
        # Fake kernel version for compatibility
        if config.fake_kernel:
            cmd.append("--kernel-release=6.1.0-tmoe")
        
        # Mounts
        mounts = self._get_mounts(config)
        for mount in mounts:
            cmd.append(f"--mount={mount}")
        
        # Environment variables
        env_vars = self._get_env_vars(config)
        for key, value in env_vars.items():
            cmd.append(f"--env={key}={value}")
        
        # Command to execute
        if command:
            cmd.extend(command)
        else:
            # Default to login shell
            cmd.append("/bin/bash")
            cmd.append("-l")
        
        return cmd
    
    def _get_mounts(self, config: ContainerConfig) -> list[str]:
        """Get list of mounts for proot."""
        mounts = []
        
        # Standard system mounts
        if config.mount_system and self.platform.is_android:
            mounts.append("/system")
        
        if config.mount_apex and self.platform.is_android:
            if os.path.exists("/apex"):
                mounts.append("/apex")
        
        # Device mounts
        mounts.append("/dev")
        mounts.append("/proc")
        
        # Storage mounts
        if config.mount_termux and self.platform.is_termux:
            termux_prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
            mounts.append(f"{termux_prefix}/..")
        
        # Custom mounts
        for mount_config in config.custom_mounts:
            source = mount_config.get("source", "")
            target = mount_config.get("target", "")
            if source and target:
                mounts.append(f"{source}:{target}")
        
        return mounts
    
    def _get_env_vars(self, config: ContainerConfig) -> dict[str, str]:
        """Get environment variables for container."""
        env_vars = {
            "HOSTNAME": config.name,
            "HOME": config.home,
            "USER": config.user,
            "TERM": "xterm-256color",
            "DISPLAY": config.display,
            "PULSE_SERVER": f"tcp:{self.config.pulse_server}:{self.config.pulse_port}",
            "TMOE_CHROOT": "false",
            "TMOE_PROOT": "true",
            "TMOE_CONTAINER_NAME": config.name,
            "TMOE_CONTAINER_TYPE": "proot",
            "TMPDIR": "/tmp",
            # Input method settings
            "GTK_IM_MODULE": "fcitx",
            "QT_IM_MODULE": "fcitx",
            "XMODIFIERS": "@im=fcitx",
            "SDL_IM_MODULE": "fcitx",
        }
        
        # PATH
        env_vars["PATH"] = ":".join([
            "/usr/local/sbin",
            "/usr/local/bin",
            "/usr/sbin",
            "/usr/bin",
            "/sbin",
            "/bin",
            "/usr/games",
            "/usr/local/games",
        ])
        
        return env_vars
    
    async def start(
        self,
        name: str,
        command: list[str] | None = None,
    ) -> None:
        """Start a proot container."""
        config = self.load_container_config(name)
        if not config:
            raise ValueError(f"Container '{name}' not found")
        
        if not config.rootfs_path or not config.rootfs_path.exists():
            raise ValueError(f"Container '{name}' rootfs not found")
        
        # Build proot command
        cmd = self._build_proot_cmd(config, command)
        
        # Execute proot
        env = os.environ.copy()
        env.update(self._get_env_vars(config))
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdin=asyncio.subprocess.PIPE if not command else None,
            stdout=asyncio.subprocess.PIPE if not command else None,
            stderr=asyncio.subprocess.PIPE if not command else None,
        )
        
        if not command:
            # Interactive shell - wait for it to complete
            await proc.wait()
    
    async def stop(self, name: str) -> None:
        """Stop a proot container."""
        # Find proot processes for this container
        cmd = ["pkill", "-f", f"proot.*{name}"]
        proc = await asyncio.create_subprocess_exec(*cmd)
        await proc.wait()
    
    async def remove(self, name: str, force: bool = False) -> None:
        """Remove a proot container."""
        config = self.load_container_config(name)
        if not config:
            raise ValueError(f"Container '{name}' not found")
        
        # Check if running
        status = await self._get_status(name)
        if status == ContainerStatus.RUNNING:
            if not force:
                raise RuntimeError(f"Container '{name}' is running. Use force=True to remove.")
            await self.stop(name)
        
        # Remove rootfs directory
        if config.rootfs_path and config.rootfs_path.exists():
            import shutil
            shutil.rmtree(config.rootfs_path)
        
        # Remove config file
        config_path = self.get_container_config_path(name)
        if config_path.exists():
            config_path.unlink()
    
    async def exec(
        self,
        name: str,
        command: list[str],
    ) -> tuple[int, str, str]:
        """Execute a command in a proot container."""
        config = self.load_container_config(name)
        if not config:
            raise ValueError(f"Container '{name}' not found")
        
        cmd = self._build_proot_cmd(config, command)
        env = os.environ.copy()
        env.update(self._get_env_vars(config))
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await proc.communicate()
        return (
            proc.returncode or 0,
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
        )
