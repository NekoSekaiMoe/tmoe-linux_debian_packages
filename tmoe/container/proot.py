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
from tmoe.container.qemu import QEMUManager
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
        config_dir = self.platform.config_dir / "containers"
        
        if not config_dir.exists():
            return containers
        
        for path in config_dir.iterdir():
            if path.is_file() and path.suffix == ".json":
                name = path.stem
                config = self.load_container_config(name)
                if config and config.container_type == "proot":
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
        config_path = self.get_container_config_path(name)
        return config_path.exists()
    
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
        """Build proot command with all necessary options (原版兼容)."""
        # Determine proot binary to use
        proot_binary = self._get_proot_binary(config)
        cmd = [proot_binary]
        
        # Basic options
        cmd.extend([
            f"--rootfs={config.rootfs_path}",
            f"--pwd={config.home}",
        ])
        
        # User options (原版: --root-id 或 --change-id=uid:gid)
        if config.user == "root":
            cmd.append("--root-id")
        else:
            cmd.append(f"--change-id={config.uid}:{config.gid}")
        
        # Feature flags (原版支持)
        if config.kill_on_exit:
            cmd.append("--kill-on-exit")
        if config.sysvipc:
            cmd.append("--sysvipc")
        if config.link2symlink:
            cmd.append("--link2symlink")
        
        # Fake kernel version (原版支持)
        if config.fake_kernel:
            kernel_version = config.fake_kernel_version or "6.1.0-tmoe"
            cmd.append(f"--kernel-release={kernel_version}")
        
        # Fix lowercase (-L flag for case-insensitive filesystem, 原版支持)
        if config.fix_lowercase:
            cmd.append("-L")
        
        # QEMU cross-architecture support
        if config.qemu_enabled and config.qemu_bin:
            cmd.append(f"--qemu={config.qemu_bin}")
        
        # Mounts (原版支持的所有挂载点)
        mounts = self._get_mounts(config)
        for mount in mounts:
            cmd.append(f"--mount={mount}")
        
        # Environment variables (原版环境变量格式)
        env_vars = self._get_env_vars(config)
        for key, value in env_vars.items():
            cmd.append(f"--env={key}={value}")
        
        # Command to execute
        if command:
            cmd.extend(command)
        else:
            # Default to login shell (原版使用 -l)
            shell = self._get_shell(config)
            cmd.append(shell)
            cmd.append("-l")
        
        return cmd
    
    def _get_proot_binary(self, config: ContainerConfig) -> str:
        """Get proot binary path based on config (原版支持多种proot二进制)."""
        proot_bin = config.proot_bin or "proot"
        
        if proot_bin == "proot":
            return self.proot_bin
        elif proot_bin == "32":
            # 32-bit proot for compatibility
            return shutil.which("proot32") or self.proot_bin
        elif proot_bin == "compatible":
            # Compatible mode proot
            return shutil.which("proot-compatible") or self.proot_bin
        
        return proot_bin if shutil.which(proot_bin) else self.proot_bin
    
    def _get_shell(self, config: ContainerConfig) -> str:
        """Get default shell for container (原版逻辑)."""
        # Check for common shells in order of preference
        possible_shells = [
            "/bin/zsh",
            "/usr/bin/zsh",
            "/bin/bash",
            "/usr/bin/bash",
            "/bin/sh",
        ]
        
        if config.rootfs_path:
            for shell in possible_shells:
                if (config.rootfs_path / shell.lstrip("/")).exists():
                    return shell
        
        return "/bin/bash"
    
    def _get_mounts(self, config: ContainerConfig) -> list[str]:
        """Get list of mounts for proot (原版挂载逻辑)."""
        mounts = []
        
        # Android system mounts (原版支持)
        if self.platform.is_android:
            if config.mount_system and os.path.exists("/system"):
                mounts.append("/system")
            if config.mount_apex and os.path.exists("/apex"):
                mounts.append("/apex")
            # Mount /vendor for some devices
            if os.path.exists("/vendor"):
                mounts.append("/vendor")
            # Mount /odm for some devices
            if os.path.exists("/odm"):
                mounts.append("/odm")
        
        # Device mounts (原版支持)
        mounts.append("/dev")
        mounts.append("/proc")
        mounts.append("/sys")  # 原版也挂载 /sys
        
        # Storage mounts (原版支持)
        if self.platform.is_termux:
            termux_prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
            termux_home = f"{termux_prefix}/.."
            
            if config.mount_termux:
                mounts.append(f"{termux_home}:/media/termux")  # 原版映射到 /media/termux
            
            # SD Card mount (原版支持)
            if config.mount_sd:
                sd_path = "/storage/self/primary"
                if os.path.exists(sd_path):
                    mounts.append(f"{sd_path}:/media/sd")  # 原版映射到 /media/sd
                
                # External storage
                for i in range(10):
                    ext_sd = f"/storage/{i}"
                    if os.path.exists(ext_sd) and os.path.ismount(ext_sd):
                        mounts.append(f"{ext_sd}:/media/tf{i}")
        
        # Custom mounts (用户自定义)
        for mount_config in config.custom_mounts:
            source = mount_config.get("source", "")
            target = mount_config.get("target", "")
            if source and target:
                mounts.append(f"{source}:{target}")
        
        return mounts
    
    def _get_env_vars(self, config: ContainerConfig) -> dict[str, str]:
        """Get environment variables for container (原版环境变量格式)."""
        env_vars: dict[str, str] = {
            # Basic environment (原版格式)
            "HOSTNAME": config.name,
            "HOME": config.home,
            "USER": config.user,
            "TERM": os.environ.get("TERM", "xterm-256color"),
            "TMPDIR": "/tmp",
            "TMP": "/tmp",
            
            # TMOE specific (原版变量)
            "TMOE_CHROOT": "false",
            "TMOE_PROOT": "true",
            "TMOE_CONTAINER_NAME": config.name,
            "TMOE_CONTAINER_TYPE": "proot",
            "TMOE_DISTRO": config.distro,
            "TMOE_ARCH": config.arch,
        }
        
        # Display settings (if GUI enabled)
        if config.display:
            env_vars["DISPLAY"] = config.display
        
        # PulseAudio settings (原版支持)
        if self.config.pulse_server:
            env_vars["PULSE_SERVER"] = f"tcp:{self.config.pulse_server}:{self.config.pulse_port}"
        
        # Input method settings (原版fcitx配置)
        env_vars.update({
            "GTK_IM_MODULE": "fcitx",
            "QT_IM_MODULE": "fcitx",
            "XMODIFIERS": "@im=fcitx",
            "SDL_IM_MODULE": "fcitx",
            "QT_QPA_PLATFORMTHEME": "gtk2",
        })
        
        # Locale settings
        env_vars["LANG"] = self.config.locale
        env_vars["LANGUAGE"] = self.config.language
        
        # PATH (原版PATH顺序)
        paths = [
            "/usr/local/sbin",
            "/usr/local/bin",
            "/usr/sbin",
            "/usr/bin",
            "/sbin",
            "/bin",
            "/usr/games",
            "/usr/local/games",
            "/opt/bin",
        ]
        
        # Add Termux paths if applicable
        if self.platform.is_termux:
            termux_prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
            paths.insert(0, f"{termux_prefix}/bin")
        
        env_vars["PATH"] = ":".join(paths)
        
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
    
    async def configure_qemu(self, name: str, enabled: bool = True) -> bool:
        """Configure QEMU cross-architecture support for container.
        
        Args:
            name: Container name
            enabled: Whether to enable QEMU
            
        Returns:
            True if configuration succeeded
        """
        config = self.load_container_config(name)
        if not config:
            raise ValueError(f"Container '{name}' not found")
        
        # Check if cross-arch is needed
        qemu_manager = QEMUManager(self.platform)
        if not qemu_manager.is_cross_arch(self.platform.normalized_arch, config.arch):
            # Same architecture, no QEMU needed
            config.qemu_enabled = False
            config.qemu_arch = None
            config.qemu_bin = None
            self.save_container_config(config)
            return True
        
        if enabled:
            # Check if QEMU is available
            qemu_bin = await qemu_manager.get_qemu_binary(config.arch)
            if not qemu_bin:
                # Try to install QEMU
                if await qemu_manager.install_qemu(config.arch):
                    qemu_bin = await qemu_manager.get_qemu_binary(config.arch)
            
            if qemu_bin:
                config.qemu_enabled = True
                config.qemu_arch = config.arch
                config.qemu_bin = str(qemu_bin)
                self.save_container_config(config)
                return True
            else:
                return False
        else:
            config.qemu_enabled = False
            config.qemu_arch = None
            config.qemu_bin = None
            self.save_container_config(config)
            return True
    
    def generate_startup_script(self, name: str) -> str:
        """Generate startup script for container (原版启动脚本格式).
        
        Args:
            name: Container name
            
        Returns:
            Shell script content for starting container
        """
        config = self.load_container_config(name)
        if not config:
            raise ValueError(f"Container '{name}' not found")
        
        # Build proot command
        cmd_parts = self._build_proot_cmd(config)
        proot_cmd = " ".join(cmd_parts)
        
        # Generate script matching original TMOE format
        script = f'''#!/bin/bash
# TMOE Proot Container Startup Script
# Generated automatically - do not edit manually

# Container configuration
TMOE_CONTAINER_NAME="{config.name}"
TMOE_CONTAINER_TYPE="proot"
TMOE_DISTRO="{config.distro}"
TMOE_ARCH="{config.arch}"

# Environment setup
export HOME="{config.home}"
export USER="{config.user}"
export TERM="{os.environ.get('TERM', 'xterm-256color')}"
export LANG="{self.config.locale}"
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Input method
export GTK_IM_MODULE=fcitx
export QT_IM_MODULE=fcitx
export XMODIFIERS=@im=fcitx

# TMOE specific
export TMOE_CHROOT=false
export TMOE_PROOT=true
export TMOE_CONTAINER_NAME="{config.name}"

# Display settings
export DISPLAY="{config.display}"

# Proot command
PROOT_CMD="{proot_cmd}"

# Execute proot
echo "Starting TMOE proot container: {config.name}"
echo "Distribution: {config.distro} ({config.arch})"
echo "User: {config.user}"
echo "Home: {config.home}"
echo ""

exec {proot_cmd}
'''
        return script
