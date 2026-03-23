"""Chroot container backend for TMOE.

Chroot provides traditional chroot containers that require root privileges.
This backend is suitable for Linux desktop/server environments.
"""

from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from tmoe.container.base import ContainerBackend, ContainerInfo, ContainerStatus
from tmoe.core.config import ContainerConfig, get_config
from tmoe.core.platform import PlatformInfo

if TYPE_CHECKING:
    from collections.abc import Sequence


class ChrootBackend(ContainerBackend):
    """Chroot container backend implementation.
    
    Chroot changes the root filesystem for a process and its children.
    This backend requires root privileges but provides better isolation
    and performance compared to proot.
    
    Features:
    - True kernel-level isolation
    - Better performance than proot
    - Support for systemd inside containers
    - Requires root privileges
    
    Example:
        >>> backend = ChrootBackend()
        >>> config = await backend.create("my-debian", "debian", "amd64")
        >>> await backend.start("my-debian")
    """
    
    # Required mount points for chroot
    REQUIRED_MOUNTS = ["proc", "sys", "dev", "dev/pts", "dev/shm"]
    
    def __init__(self, platform: PlatformInfo | None = None) -> None:
        super().__init__(platform)
        self._active_mounts: dict[str, list[str]] = {}
    
    @property
    def backend_type(self) -> str:
        return "chroot"
    
    @property
    def requires_root(self) -> bool:
        return True
    
    async def list_containers(self) -> list[ContainerInfo]:
        """List all chroot containers."""
        self.check_root()
        
        containers: list[ContainerInfo] = []
        config_dir = self.platform.config_dir / "containers"
        
        if not config_dir.exists():
            return containers
        
        for path in config_dir.iterdir():
            if path.is_file() and path.suffix == ".json":
                name = path.stem
                config = self.load_container_config(name)
                if config and config.container_type == "chroot":
                    info = ContainerInfo(
                        name=name,
                        config=config,
                        status=await self._get_status(name),
                    )
                    containers.append(info)
        
        return containers
    
    async def _get_status(self, name: str) -> ContainerStatus:
        """Get container status."""
        # Check if chroot is active by looking at mounts
        container_path = self.get_container_path(name)
        proc_mounts = Path("/proc/mounts").read_text()
        
        if str(container_path) in proc_mounts:
            return ContainerStatus.RUNNING
        return ContainerStatus.STOPPED
    
    async def exists(self, name: str) -> bool:
        """Check if a chroot container exists."""
        config_path = self.get_container_config_path(name)
        return config_path.exists()
    
    async def get_info(self, name: str) -> ContainerInfo | None:
        """Get information about a chroot container."""
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
        """Create a new chroot container configuration."""
        self.check_root()
        
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
            container_type="chroot",
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
        """Install a new chroot container with rootfs."""
        from tmoe.container.install import ContainerInstaller
        
        # Create config first
        config = await self.create(name, distro, arch, codename)
        
        # Download and install rootfs
        installer = ContainerInstaller(self.platform)
        await installer.install_chroot(config)
        
        return config
    
    async def _setup_mounts(self, config: ContainerConfig) -> None:
        """Setup required mounts for chroot."""
        if config.rootfs_path is None:
            raise ValueError("Container rootfs path not set")
        
        rootfs = config.rootfs_path
        mounts: list[str] = []
        
        # Mount proc
        proc_path = rootfs / "proc"
        proc_path.mkdir(parents=True, exist_ok=True)
        await self._run_cmd(["mount", "-t", "proc", "proc", str(proc_path)])
        mounts.append(str(proc_path))
        
        # Mount sys
        sys_path = rootfs / "sys"
        sys_path.mkdir(parents=True, exist_ok=True)
        await self._run_cmd(["mount", "--rbind", "/sys", str(sys_path)])
        mounts.append(str(sys_path))
        
        # Mount dev
        dev_path = rootfs / "dev"
        dev_path.mkdir(parents=True, exist_ok=True)
        await self._run_cmd(["mount", "--rbind", "/dev", str(dev_path)])
        mounts.append(str(dev_path))
        
        # Mount devpts
        pts_path = rootfs / "dev" / "pts"
        pts_path.mkdir(parents=True, exist_ok=True)
        await self._run_cmd(["mount", "-t", "devpts", "devpts", str(pts_path)])
        mounts.append(str(pts_path))
        
        # Mount shm
        shm_path = rootfs / "dev" / "shm"
        shm_path.mkdir(parents=True, exist_ok=True)
        await self._run_cmd(["mount", "-t", "tmpfs", "tmpfs", str(shm_path)])
        mounts.append(str(shm_path))
        
        self._active_mounts[config.name] = mounts
    
    async def _cleanup_mounts(self, config: ContainerConfig) -> None:
        """Cleanup mounts for chroot."""
        if config.rootfs_path is None:
            return
        
        # Unmount in reverse order
        mounts = self._active_mounts.get(config.name, [])
        for mount_point in reversed(mounts):
            try:
                await self._run_cmd(["umount", "-l", mount_point])
            except Exception:
                pass
        
        if config.name in self._active_mounts:
            del self._active_mounts[config.name]
    
    async def start(
        self,
        name: str,
        command: list[str] | None = None,
    ) -> None:
        """Start a chroot container."""
        self.check_root()
        
        config = self.load_container_config(name)
        if not config:
            raise ValueError(f"Container '{name}' not found")
        
        if not config.rootfs_path or not config.rootfs_path.exists():
            raise ValueError(f"Container '{name}' rootfs not found")
        
        # Setup mounts
        await self._setup_mounts(config)
        
        try:
            # Build chroot command
            cmd = ["chroot", str(config.rootfs_path)]
            
            if command:
                cmd.extend(command)
            else:
                cmd.extend(["/bin/bash", "-l"])
            
            # Setup environment
            env = os.environ.copy()
            env.update(self._get_env_vars(config))
            
            # Execute chroot
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdin=asyncio.subprocess.PIPE if not command else None,
                stdout=asyncio.subprocess.PIPE if not command else None,
                stderr=asyncio.subprocess.PIPE if not command else None,
            )
            
            if not command:
                await proc.wait()
        finally:
            # Cleanup mounts
            await self._cleanup_mounts(config)
    
    async def stop(self, name: str) -> None:
        """Stop a chroot container."""
        self.check_root()
        
        config = self.load_container_config(name)
        if not config:
            return
        
        await self._cleanup_mounts(config)
    
    async def remove(self, name: str, force: bool = False) -> None:
        """Remove a chroot container."""
        self.check_root()
        
        config = self.load_container_config(name)
        if not config:
            raise ValueError(f"Container '{name}' not found")
        
        # Check if running
        status = await self._get_status(name)
        if status == ContainerStatus.RUNNING:
            if not force:
                raise RuntimeError(f"Container '{name}' is running. Use force=True to remove.")
            await self.stop(name)
        
        # Safety check: ensure /proc is not mounted
        if config.rootfs_path:
            proc_path = config.rootfs_path / "proc"
            if proc_path.exists() and any(proc_path.iterdir()):
                raise RuntimeError("Safety check failed: /proc appears to be mounted. Please unmount manually.")
        
        # Remove rootfs directory
        if config.rootfs_path and config.rootfs_path.exists():
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
        """Execute a command in a chroot container."""
        self.check_root()
        
        config = self.load_container_config(name)
        if not config:
            raise ValueError(f"Container '{name}' not found")
        
        # Setup mounts
        await self._setup_mounts(config)
        
        try:
            cmd = ["chroot", str(config.rootfs_path)]
            cmd.extend(command)
            
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
        finally:
            await self._cleanup_mounts(config)
    
    def _get_env_vars(self, config: ContainerConfig) -> dict[str, str]:
        """Get environment variables for container."""
        return {
            "HOSTNAME": config.name,
            "HOME": config.home,
            "USER": config.user,
            "TERM": "xterm-256color",
            "DISPLAY": config.display,
            "TMOE_CHROOT": "true",
            "TMOE_PROOT": "false",
            "TMOE_CONTAINER_NAME": config.name,
            "TMOE_CONTAINER_TYPE": "chroot",
        }
    
    async def _run_cmd(self, cmd: list[str]) -> None:
        """Run a command and wait for completion."""
        proc = await asyncio.create_subprocess_exec(*cmd)
        await proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"Command failed: {' '.join(cmd)}")
