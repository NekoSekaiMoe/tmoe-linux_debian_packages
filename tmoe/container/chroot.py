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
    
    # Required mount points for chroot (原版挂载点)
    REQUIRED_MOUNTS = ["proc", "sys", "dev", "dev/pts", "dev/shm"]
    
    def __init__(self, platform: PlatformInfo | None = None) -> None:
        super().__init__(platform)
        self._mounts_file = self.platform.config_dir / "chroot_mounts.json"
    
    def _load_mounts_state(self) -> dict[str, list[str]]:
        """Load mounts state from file (持久化挂载状态)."""
        import json
        if self._mounts_file.exists():
            try:
                return json.loads(self._mounts_file.read_text())
            except Exception:
                pass
        return {}
    
    def _save_mounts_state(self, state: dict[str, list[str]]) -> None:
        """Save mounts state to file (持久化挂载状态)."""
        import json
        self._mounts_file.parent.mkdir(parents=True, exist_ok=True)
        self._mounts_file.write_text(json.dumps(state, indent=2))
    
    def _get_container_mounts(self, name: str) -> list[str]:
        """Get active mounts for a container."""
        state = self._load_mounts_state()
        return state.get(name, [])
    
    def _set_container_mounts(self, name: str, mounts: list[str]) -> None:
        """Set active mounts for a container."""
        state = self._load_mounts_state()
        state[name] = mounts
        self._save_mounts_state(state)
    
    def _clear_container_mounts(self, name: str) -> None:
        """Clear mounts for a container."""
        state = self._load_mounts_state()
        if name in state:
            del state[name]
            self._save_mounts_state(state)
    
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
        """Setup required mounts for chroot (原版挂载逻辑)."""
        if config.rootfs_path is None:
            raise ValueError("Container rootfs path not set")
        
        rootfs = config.rootfs_path
        mounts: list[str] = []
        
        # 1. Mount rootfs itself with rbind (原版: mount --rbind rootfs rootfs)
        await self._run_cmd(["mount", "--rbind", str(rootfs), str(rootfs)])
        await self._run_cmd([
            "mount", "-o", "remount,exec,suid,relatime,dev",
            str(rootfs)
        ])
        mounts.append(str(rootfs))
        
        # 2. Mount dev (原版: mount -o bind /dev rootfs/dev)
        dev_path = rootfs / "dev"
        dev_path.mkdir(parents=True, exist_ok=True)
        await self._run_cmd(["mount", "-o", "bind", "/dev", str(dev_path)])
        mounts.append(str(dev_path))
        
        # 3. Mount proc (原版: mount -t proc proc rootfs/proc)
        proc_path = rootfs / "proc"
        proc_path.mkdir(parents=True, exist_ok=True)
        await self._run_cmd(["mount", "-t", "proc", "proc", str(proc_path)])
        mounts.append(str(proc_path))
        
        # 4. Mount sys (原版: mount -t sysfs sysfs rootfs/sys)
        sys_path = rootfs / "sys"
        sys_path.mkdir(parents=True, exist_ok=True)
        await self._run_cmd(["mount", "-t", "sysfs", "sysfs", str(sys_path)])
        mounts.append(str(sys_path))
        
        # 5. Mount devpts (原版: mount -t devpts devpts rootfs/dev/pts)
        pts_path = rootfs / "dev" / "pts"
        pts_path.mkdir(parents=True, exist_ok=True)
        await self._run_cmd(["mount", "-t", "devpts", "devpts", str(pts_path)])
        mounts.append(str(pts_path))
        
        # 6. Mount shm (原版: mount -t tmpfs tmpfs rootfs/dev/shm)
        shm_path = rootfs / "dev" / "shm"
        shm_path.mkdir(parents=True, exist_ok=True)
        await self._run_cmd(["mount", "-t", "tmpfs", "tmpfs", str(shm_path)])
        mounts.append(str(shm_path))
        
        # 7. Additional mounts (原版支持)
        # Mount /dev/pts/ptmx for pseudo-terminal support
        ptmx_path = rootfs / "dev" / "ptmx"
        if not ptmx_path.exists():
            # Create symlink to /dev/pts/ptmx
            pass  # Will be handled by devpts mount
        
        # Save mounts state (持久化)
        self._set_container_mounts(config.name, mounts)
    
    async def _cleanup_mounts(self, config: ContainerConfig) -> None:
        """Cleanup mounts for chroot (原版卸载顺序)."""
        if config.rootfs_path is None:
            return
        
        # Get mounts from persistent state
        mounts = self._get_container_mounts(config.name)
        
        # Unmount in reverse order (important!)
        for mount_point in reversed(mounts):
            try:
                await self._run_cmd(["umount", "-l", mount_point])
            except Exception:
                pass
        
        # Clear mounts state
        self._clear_container_mounts(config.name)
    
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
    
    async def start_nspawn(
        self,
        name: str,
        command: list[str] | None = None,
    ) -> None:
        """Start container using systemd-nspawn (原版支持).
        
        systemd-nspawn provides better isolation than chroot
        and supports systemd inside containers.
        
        Args:
            name: Container name
            command: Optional command to execute
        """
        self.check_root()
        
        config = self.load_container_config(name)
        if not config:
            raise ValueError(f"Container '{name}' not found")
        
        if not config.rootfs_path or not config.rootfs_path.exists():
            raise ValueError(f"Container '{name}' rootfs not found")
        
        # Check if systemd-nspawn is available
        nspawn_bin = shutil.which("systemd-nspawn")
        if not nspawn_bin:
            raise RuntimeError("systemd-nspawn not found. Please install systemd-container package.")
        
        # Build nspawn command (原版 nspawn 参数)
        cmd = [
            nspawn_bin,
            f"--directory={config.rootfs_path}",
            f"--machine={config.name}",
            "--capability=all",
            "--bind=/dev:/dev",
            "--bind=/proc:/proc",
            "--bind=/sys:/sys",
        ]
        
        # Add network configuration
        cmd.extend([
            "--network-veth",  # Create virtual ethernet interface
            "--private-network",  # Private network namespace
        ])
        
        # Add user configuration
        if config.user != "root":
            cmd.append(f"--user={config.user}")
        
        # Environment variables
        env = os.environ.copy()
        env.update(self._get_env_vars(config))
        
        # Command to execute
        if command:
            cmd.extend(command)
        else:
            cmd.extend(["/bin/bash", "-l"])
        
        # Execute nspawn
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdin=asyncio.subprocess.PIPE if not command else None,
            stdout=asyncio.subprocess.PIPE if not command else None,
            stderr=asyncio.subprocess.PIPE if not command else None,
        )
        
        if not command:
            await proc.wait()
    
    def _get_env_vars(self, config: ContainerConfig) -> dict[str, str]:
        """Get environment variables for container (原版环境变量)."""
        env_vars: dict[str, str] = {
            "HOSTNAME": config.name,
            "HOME": config.home,
            "USER": config.user,
            "TERM": os.environ.get("TERM", "xterm-256color"),
            "TMOE_CHROOT": "true",
            "TMOE_PROOT": "false",
            "TMOE_CONTAINER_NAME": config.name,
            "TMOE_CONTAINER_TYPE": "chroot",
            "TMOE_NSPAWN": "false",
        }
        
        if config.display:
            env_vars["DISPLAY"] = config.display
        
        return env_vars
    
    async def _run_cmd(self, cmd: list[str]) -> None:
        """Run a command and wait for completion."""
        proc = await asyncio.create_subprocess_exec(*cmd)
        await proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"Command failed: {' '.join(cmd)}")

    def generate_startup_script(self, name: str, use_nspawn: bool = False) -> str:
        """Generate startup script for container (原版启动脚本格式).

        Args:
            name: Container name
            use_nspawn: Use systemd-nspawn instead of chroot

        Returns:
            Shell script content for starting container
        """
        config = self.load_container_config(name)
        if not config:
            raise ValueError(f"Container '{name}' not found")

        if use_nspawn:
            # systemd-nspawn script
            script = f'''#!/bin/bash
# TMOE systemd-nspawn Container Startup Script
# Generated automatically - do not edit manually

TMOE_CONTAINER_NAME="{config.name}"
TMOE_CONTAINER_TYPE="nspawn"
TMOE_DISTRO="{config.distron}"
TMOE_ARCH="{config.arch}"

# Check for systemd-nspawn
if ! command -v systemd-nspawn &> /dev/null; then
    echo "Error: systemd-nspawn not found"
    echo "Please install: apt install systemd-container"
    exit 1
fi

# Environment
export HOME="{config.home}"
export USER="{config.user}"

# Start container
echo "Starting TMOE systemd-nspawn container: {config.name}"
systemd-nspawn \\
    --directory="{config.rootfs_path}" \\
    --machine="{config.name}" \\
    --capability=all \\
    --bind=/dev:/dev \\
    --bind=/proc:/proc \\
    --bind=/sys:/sys \\
    --network-veth \\
    --user="{config.user}" \\
    /bin/bash -l
'''
        else:
            # chroot script (原版格式)
            script = f'''#!/bin/bash
# TMOE Chroot Container Startup Script
# Generated automatically - do not edit manually

TMOE_CONTAINER_NAME="{config.name}"
TMOE_CONTAINER_TYPE="chroot"
TMOE_DISTRO="{config.distro}"
TMOE_ARCH="{config.arch}"

ROOTFS="{config.rootfs_path}"

# Check root
if [ "$(id -u)" -ne 0 ]; then
    echo "Error: Chroot requires root privileges"
    exit 1
fi

# Mount filesystems
echo "Mounting filesystems..."
mount --rbind "$ROOTFS" "$ROOTFS/"
mount -o remount,exec,suid,relatime,dev "$ROOTFS"
mount -o bind /dev "$ROOTFS/dev"
mount -t proc proc "$ROOTFS/proc"
mount -t sysfs sysfs "$ROOTFS/sys"
mount -t devpts devpts "$ROOTFS/dev/pts"
mount -t tmpfs tmpfs "$ROOTFS/dev/shm"

# Cleanup function
cleanup() {{
    echo "Unmounting filesystems..."
    umount -l "$ROOTFS/dev/shm" 2>/dev/null || true
    umount -l "$ROOTFS/dev/pts" 2>/dev/null || true
    umount -l "$ROOTFS/sys" 2>/dev/null || true
    umount -l "$ROOTFS/proc" 2>/dev/null || true
    umount -l "$ROOTFS/dev" 2>/dev/null || true
    umount -l "$ROOTFS" 2>/dev/null || true
}}
trap cleanup EXIT

# Environment setup
export HOME="{config.home}"
export USER="{config.user}"
export TERM="{os.environ.get('TERM', 'xterm-256color')}"
export LANG="C.UTF-8"
export TMOE_CHROOT=true
export TMOE_PROOT=false
export TMOE_CONTAINER_NAME="{config.name}"

# Start container
echo "Starting TMOE chroot container: {config.name}"
echo "Distribution: {config.distro} ({config.arch})"
echo "User: {config.user}"
echo ""

chroot "$ROOTFS" /usr/bin/env -i \\
    HOME="{config.home}" \\
    USER="{config.user}" \\
    TERM="$TERM" \\
    LANG="$LANG" \\
    TMOE_CHROOT=true \\
    TMOE_PROOT=false \\
    TMOE_CONTAINER_NAME="{config.name}" \\
    PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \\
    /bin/bash -l
'''
        return script
