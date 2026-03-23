"""QEMU user-mode support for cross-architecture containers.

This module provides QEMU user-mode emulation for running containers
with different architectures than the host.
"""

from __future__ import annotations

import asyncio
import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from tmoe.core.config import get_config
from tmoe.core.platform import PlatformInfo

if TYPE_CHECKING:
    pass


# Architecture mapping for QEMU
QEMU_ARCH_MAP = {
    "arm64": "aarch64",
    "aarch64": "aarch64",
    "amd64": "x86_64",
    "x86_64": "x86_64",
    "armhf": "arm",
    "armv7l": "arm",
    "i386": "i386",
    "i686": "i386",
    "riscv64": "riscv64",
    "ppc64el": "ppc64le",
    "s390x": "s390x",
    "mips64el": "mips64el",
    "mipsel": "mipsel",
}

# Architecture compatibility matrix (host -> guest)
# Based on original TMOE's architecture support chart
ARCH_COMPATIBILITY = {
    "arm64": ["arm64", "armhf", "amd64", "i386"],
    "amd64": ["amd64", "i386", "arm64", "armhf"],
    "armhf": ["armhf"],
    "i386": ["i386"],
    "riscv64": ["riscv64"],
}


class QEMUManager:
    """QEMU user-mode manager for cross-architecture support.
    
    Provides functionality to:
    - Detect if cross-architecture is needed
    - Download/install QEMU user-mode binaries
    - Configure proot to use QEMU
    - Manage QEMU versions
    
    Example:
        >>> manager = QEMUManager()
        >>> if manager.is_cross_arch("arm64", "amd64"):
        ...     qemu_bin = await manager.get_qemu_binary("amd64")
    """
    
    # Debian repository URL for QEMU packages
    DEBIAN_REPO_URL = "https://mirrors.bfsu.edu.cn/debian/pool/main/q/qemu/"
    DEBIAN_REPO_BACKUP = "https://ftp.debian.org/debian/pool/main/q/qemu/"
    
    def __init__(self, platform: PlatformInfo | None = None) -> None:
        self.platform = platform or PlatformInfo()
        self.config = get_config()
        self._qemu_dir = self.platform.data_dir / "qemu"
        self._version_file = self._qemu_dir / "version.txt"
    
    def get_qemu_arch(self, arch: str) -> str:
        """Convert architecture name to QEMU format.
        
        Args:
            arch: Architecture name (e.g., 'arm64', 'amd64')
            
        Returns:
            QEMU architecture name (e.g., 'aarch64', 'x86_64')
        """
        return QEMU_ARCH_MAP.get(arch, arch)
    
    def is_cross_arch(self, host_arch: str, guest_arch: str) -> bool:
        """Check if guest architecture differs from host.
        
        Args:
            host_arch: Host architecture
            guest_arch: Target/guest architecture
            
        Returns:
            True if cross-architecture emulation is needed
        """
        # Normalize architectures
        host_normalized = self._normalize_arch(host_arch)
        guest_normalized = self._normalize_arch(guest_arch)
        
        return host_normalized != guest_normalized
    
    def _normalize_arch(self, arch: str) -> str:
        """Normalize architecture name."""
        arch = arch.lower()
        if arch in ("arm64", "aarch64"):
            return "arm64"
        elif arch in ("amd64", "x86_64"):
            return "amd64"
        elif arch in ("armhf", "armv7l", "arm"):
            return "armhf"
        elif arch in ("i386", "i686"):
            return "i386"
        return arch
    
    def is_arch_supported(self, host_arch: str, guest_arch: str) -> bool:
        """Check if host can emulate guest architecture.
        
        Args:
            host_arch: Host architecture
            guest_arch: Target/guest architecture
            
        Returns:
            True if emulation is supported
        """
        host_normalized = self._normalize_arch(host_arch)
        guest_normalized = self._normalize_arch(guest_arch)
        
        supported = ARCH_COMPATIBILITY.get(host_normalized, [host_normalized])
        return guest_normalized in supported
    
    def get_qemu_binary_name(self, arch: str) -> str:
        """Get QEMU binary name for architecture.
        
        Args:
            arch: Target architecture
            
        Returns:
            QEMU binary name (e.g., 'qemu-x86_64-static')
        """
        qemu_arch = self.get_qemu_arch(arch)
        return f"qemu-{qemu_arch}-static"
    
    def get_system_qemu_path(self, arch: str) -> Path | None:
        """Get path to system-installed QEMU binary.
        
        Args:
            arch: Target architecture
            
        Returns:
            Path to QEMU binary or None if not found
        """
        binary_name = self.get_qemu_binary_name(arch)
        
        # Search in common locations
        search_paths = [
            Path(f"/usr/bin/{binary_name}"),
            Path(f"/usr/local/bin/{binary_name}"),
        ]
        
        if self.platform.is_termux:
            termux_prefix = self.platform.termux_prefix or "/data/data/com.termux/files/usr"
            search_paths.insert(0, Path(f"{termux_prefix}/bin/{binary_name}"))
        
        for path in search_paths:
            if path.exists():
                return path
        
        # Try to find with shutil
        system_path = shutil.which(binary_name)
        if system_path:
            return Path(system_path)
        
        return None
    
    def get_local_qemu_path(self, arch: str) -> Path:
        """Get path to locally downloaded QEMU binary.
        
        Args:
            arch: Target architecture
            
        Returns:
            Path to local QEMU binary
        """
        binary_name = self.get_qemu_binary_name(arch)
        return self._qemu_dir / binary_name
    
    async def get_qemu_binary(self, arch: str) -> Path | None:
        """Get QEMU binary path (system or local).
        
        Tries system installation first, then falls back to local.
        
        Args:
            arch: Target architecture
            
        Returns:
            Path to QEMU binary or None if not available
        """
        # First try system installation
        system_path = self.get_system_qemu_path(arch)
        if system_path:
            return system_path
        
        # Then try local download
        local_path = self.get_local_qemu_path(arch)
        if local_path.exists():
            return local_path
        
        return None
    
    async def install_qemu(self, arch: str) -> bool:
        """Install QEMU user-mode for architecture.
        
        Tries package manager first, then downloads from Debian repo.
        
        Args:
            arch: Target architecture
            
        Returns:
            True if installation succeeded
        """
        # Try package manager first
        if await self._install_via_package_manager(arch):
            return True
        
        # Fall back to downloading
        return await self._download_qemu(arch)
    
    async def _install_via_package_manager(self, arch: str) -> bool:
        """Try to install QEMU via package manager."""
        try:
            distro = self._detect_distro()
            
            match distro:
                case "debian" | "ubuntu":
                    cmd = ["apt", "install", "-y", "qemu-user-static"]
                case "arch":
                    cmd = ["pacman", "-Sy", "--noconfirm", "qemu-user-static", "qemu-user-static-binfmt"]
                case "fedora":
                    cmd = ["dnf", "install", "-y", "qemu-user-static"]
                case "alpine":
                    cmd = ["apk", "add", "qemu-user-static"]
                case _:
                    return False
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            
            return proc.returncode == 0 and self.get_system_qemu_path(arch) is not None
            
        except Exception:
            return False
    
    async def _download_qemu(self, arch: str) -> bool:
        """Download QEMU binary from Debian repository."""
        # This is a simplified version - in production would parse repo HTML
        # to find latest version and download the correct deb package
        qemu_arch = self.get_qemu_arch(arch)
        binary_name = f"qemu-{qemu_arch}-static"
        
        self._qemu_dir.mkdir(parents=True, exist_ok=True)
        
        # For now, just notify that manual installation is needed
        # Full implementation would download and extract from .deb
        return False
    
    def _detect_distro(self) -> str:
        """Detect Linux distribution."""
        try:
            with open("/etc/os-release") as f:
                content = f.read().lower()
                if "debian" in content:
                    return "debian"
                elif "ubuntu" in content:
                    return "ubuntu"
                elif "arch" in content:
                    return "arch"
                elif "fedora" in content:
                    return "fedora"
                elif "alpine" in content:
                    return "alpine"
        except Exception:
            pass
        return "debian"
    
    def get_proot_qemu_arg(self, arch: str) -> str | None:
        """Get QEMU argument for proot command.
        
        Args:
            arch: Target architecture
            
        Returns:
            QEMU argument string for proot or None
        """
        qemu_path = self.get_system_qemu_path(arch)
        if qemu_path:
            return f"--qemu={qemu_path}"
        return None
    
    def get_version(self) -> str | None:
        """Get installed QEMU version."""
        # Try to get version from system QEMU
        qemu_path = self.get_system_qemu_path(self.platform.normalized_arch)
        if not qemu_path:
            # Check version file
            if self._version_file.exists():
                return self._version_file.read_text().strip()
            return None
        
        try:
            import subprocess
            result = subprocess.run(
                [str(qemu_path), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                # Parse version from output
                match = re.search(r'version\s+([\d.]+)', result.stdout)
                if match:
                    return match.group(1)
        except Exception:
            pass
        
        return None
