"""Platform detection and information for TMOE.

Supports Android/Termux, GNU/Linux, and WSL environments.
"""

from __future__ import annotations

import os
import platform
from functools import lru_cache
from pathlib import Path
from typing import Self


class PlatformInfo:
    """Detect and provide platform information.
    
    This class detects whether we're running on:
    - Android (via Termux or other terminal apps)
    - GNU/Linux desktop/server
    - WSL (Windows Subsystem for Linux)
    
    Example:
        >>> info = PlatformInfo()
        >>> info.is_android
        True
        >>> info.config_dir
        PosixPath('/data/data/com.termux/files/home/.config/tmoe-linux')
    """
    
    def __init__(self) -> None:
        self._machine = platform.machine()
        self._system = platform.system()
        self._platform = platform.platform()
        self._release = platform.release()
    
    @property
    def machine(self) -> str:
        """Machine hardware name (e.g., 'aarch64', 'x86_64')."""
        return self._machine
    
    @property
    def normalized_arch(self) -> str:
        """Normalized architecture name for TMOE.
        
        Maps various architecture names to standard names:
        - aarch64 -> arm64
        - x86_64 -> amd64
        - armv7l -> armhf
        - i686 -> i386
        """
        arch_map = {
            "aarch64": "arm64",
            "arm64": "arm64",
            "x86_64": "amd64",
            "amd64": "amd64",
            "armv7l": "armhf",
            "armv7": "armhf",
            "armhf": "armhf",
            "i686": "i386",
            "i386": "i386",
            "mips64": "mips64el",
            "mips": "mipsel",
            "riscv64": "riscv64",
            "ppc64le": "ppc64el",
        }
        return arch_map.get(self._machine.lower(), self._machine.lower())
    
    @property
    def is_android(self) -> bool:
        """Check if running on Android (via Termux or other terminal apps).
        
        Detects Android by checking:
        1. Platform string contains 'Android'
        2. /system/bin/app_process exists
        3. TERMUX_VERSION environment variable is set
        """
        return (
            "Android" in self._platform
            or os.path.exists("/system/bin/app_process")
            or "TERMUX_VERSION" in os.environ
            or "TERMUX_APP_PID" in os.environ
        )
    
    @property
    def is_termux(self) -> bool:
        """Check if running inside Termux app specifically."""
        return "TERMUX_VERSION" in os.environ
    
    @property
    def termux_version(self) -> str | None:
        """Get Termux version if available."""
        return os.environ.get("TERMUX_VERSION")
    
    @property
    def is_wsl(self) -> bool:
        """Check if running in Windows Subsystem for Linux.
        
        Detects WSL by checking:
        1. WSL_DISTRO_NAME environment variable
        2. 'microsoft' in kernel release string
        3. /proc/sys/fs/binfmt_misc/WSLInterop exists
        """
        return (
            "WSL_DISTRO_NAME" in os.environ
            or "microsoft" in self._release.lower()
            or os.path.exists("/proc/sys/fs/binfmt_misc/WSLInterop")
        )
    
    @property
    def wsl_distro_name(self) -> str | None:
        """Get WSL distro name if running in WSL."""
        return os.environ.get("WSL_DISTRO_NAME")
    
    @property
    def is_linux(self) -> bool:
        """Check if running on GNU/Linux (not Android)."""
        return self._system == "Linux" and not self.is_android
    
    @property
    def is_root(self) -> bool:
        """Check if running as root user."""
        return os.geteuid() == 0
    
    @property
    def config_dir(self) -> Path:
        """Get the configuration directory.
        
        Returns:
            Path to the TMOE configuration directory.
            For Android: ~/.config/tmoe-linux
            For Linux: /usr/local/etc/tmoe-linux (if root) or ~/.config/tmoe-linux
        """
        if self.is_android or not self.is_root:
            return Path.home() / ".config/tmoe-linux"
        return Path("/usr/local/etc/tmoe-linux")
    
    @property
    def data_dir(self) -> Path:
        """Get the data directory for containers and files.
        
        Returns:
            Path to the TMOE data directory.
            For Android: ~/.local/share/tmoe-linux
            For Linux: /usr/local/etc/tmoe-linux
        """
        if self.is_android:
            return Path.home() / ".local/share/tmoe-linux"
        return Path("/usr/local/etc/tmoe-linux")
    
    @property
    def container_dir(self) -> Path:
        """Get the container root directory."""
        return self.data_dir / "containers"
    
    @property
    def proot_dir(self) -> Path:
        """Get the proot container directory."""
        return self.container_dir / "proot"
    
    @property
    def chroot_dir(self) -> Path:
        """Get the chroot container directory."""
        return self.container_dir / "chroot"
    
    @property
    def cache_dir(self) -> Path:
        """Get the cache directory."""
        if self.is_android:
            return Path.home() / ".cache/tmoe-linux"
        return Path("/var/cache/tmoe-linux")
    
    @property
    def has_proot(self) -> bool:
        """Check if proot is available."""
        return self._is_command_available("proot")
    
    @property
    def has_chroot(self) -> bool:
        """Check if chroot is available (requires root)."""
        return self.is_root and self._is_command_available("chroot")
    
    @property
    def has_systemd_nspawn(self) -> bool:
        """Check if systemd-nspawn is available."""
        return self._is_command_available("systemd-nspawn")
    
    @property
    def has_docker(self) -> bool:
        """Check if Docker is available."""
        return self._is_command_available("docker")
    
    @property
    def has_qemu(self) -> bool:
        """Check if QEMU is available."""
        return self._is_command_available("qemu-system-x86_64")
    
    @staticmethod
    def _is_command_available(cmd: str) -> bool:
        """Check if a command is available in PATH."""
        return os.system(f"command -v {cmd} >/dev/null 2>&1") == 0
    
    def ensure_directories(self) -> None:
        """Create all necessary directories if they don't exist."""
        dirs_to_create = [
            self.config_dir,
            self.data_dir,
            self.container_dir,
            self.proot_dir,
            self.chroot_dir,
            self.cache_dir,
        ]
        for directory in dirs_to_create:
            directory.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> dict[str, str | bool | None]:
        """Convert platform info to dictionary."""
        return {
            "machine": self.machine,
            "normalized_arch": self.normalized_arch,
            "system": self._system,
            "platform": self._platform,
            "release": self._release,
            "is_android": self.is_android,
            "is_termux": self.is_termux,
            "termux_version": self.termux_version,
            "is_wsl": self.is_wsl,
            "wsl_distro_name": self.wsl_distro_name,
            "is_linux": self.is_linux,
            "is_root": self.is_root,
            "config_dir": str(self.config_dir),
            "data_dir": str(self.data_dir),
            "has_proot": self.has_proot,
            "has_chroot": self.has_chroot,
            "has_systemd_nspawn": self.has_systemd_nspawn,
            "has_docker": self.has_docker,
        }
    
    @classmethod
    @lru_cache(maxsize=1)
    def get(cls) -> Self:
        """Get singleton instance of PlatformInfo."""
        return cls()


def get_platform_info() -> PlatformInfo:
    """Get platform information singleton."""
    return PlatformInfo.get()
