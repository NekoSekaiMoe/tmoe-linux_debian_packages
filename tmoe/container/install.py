"""Container installation for TMOE.

Downloads and installs container rootfs from various sources including
LXC image servers and TMOE's own build server.
"""

from __future__ import annotations

import asyncio
import lzma
import os
import tarfile
from pathlib import Path
from typing import TYPE_CHECKING

import httpx

from tmoe.core.config import ContainerConfig
from tmoe.core.platform import PlatformInfo

if TYPE_CHECKING:
    from collections.abc import Callable


class ContainerInstaller:
    """Installer for container rootfs.
    
    Downloads and installs Linux distribution rootfs from:
    - LXC image server (images.linuxcontainers.org)
    - TMOE build server
    - Custom URLs
    
    Example:
        >>> installer = ContainerInstaller()
        >>> await installer.install_proot(config)
    """
    
    # LXC image server
    LXC_BASE_URL = "https://images.linuxcontainers.org/images"
    
    # TMOE build server
    TMOE_BASE_URL = "https://cdn.tmoe.me"
    
    def __init__(self, platform: PlatformInfo | None = None) -> None:
        self.platform = platform or PlatformInfo()
        self._progress_callback: Callable[[str, int, int], None] | None = None
    
    def set_progress_callback(
        self,
        callback: Callable[[str, int, int], None],
    ) -> None:
        """Set callback for download progress.
        
        Args:
            callback: Function called with (message, current_bytes, total_bytes)
        """
        self._progress_callback = callback
    
    def _report_progress(self, message: str, current: int, total: int) -> None:
        """Report download progress."""
        if self._progress_callback:
            self._progress_callback(message, current, total)
    
    async def install_proot(self, config: ContainerConfig) -> None:
        """Install a proot container.
        
        Args:
            config: Container configuration.
        """
        # Create rootfs directory
        rootfs_path = config.rootfs_path
        if rootfs_path is None:
            raise ValueError("Container rootfs path not set")
        
        rootfs_path.mkdir(parents=True, exist_ok=True)
        
        # Download rootfs
        await self._download_rootfs(config, rootfs_path)
        
        # Setup container environment
        await self._setup_container(config, rootfs_path)
    
    async def _download_rootfs(
        self,
        config: ContainerConfig,
        rootfs_path: Path,
    ) -> None:
        """Download container rootfs.
        
        Downloads from LXC image server with fallback to TMOE server.
        """
        # Build download URL
        distro = config.distro
        arch = config.arch
        codename = config.codename or "stable"
        
        # Try LXC first
        url = self._build_lxc_url(distro, codename, arch)
        
        try:
            await self._download_file(url, rootfs_path)
        except Exception as e:
            # Fallback to TMOE server
            url = self._build_tmoe_url(distro, codename, arch)
            await self._download_file(url, rootfs_path)
    
    def _build_lxc_url(self, distro: str, codename: str, arch: str) -> str:
        """Build LXC image download URL."""
        # Map tmoe arch names to LXC names
        arch_map = {
            "arm64": "arm64",
            "amd64": "amd64",
            "armhf": "armhf",
            "i386": "i386",
        }
        lxc_arch = arch_map.get(arch, arch)
        
        # Build URL
        return (
            f"{self.LXC_BASE_URL}/{distro}/{codename}/{lxc_arch}/default/"
            f"{self._get_latest_lxc_build(distro, codename, lxc_arch)}/rootfs.tar.xz"
        )
    
    def _build_tmoe_url(self, distro: str, codename: str, arch: str) -> str:
        """Build TMOE image download URL."""
        return f"{self.TMOE_BASE_URL}/rootfs/{distro}/{codename}/{arch}/rootfs.tar.xz"
    
    def _get_latest_lxc_build(
        self,
        distro: str,
        codename: str,
        arch: str,
    ) -> str:
        """Get latest LXC build timestamp.
        
        In a real implementation, this would fetch the directory listing
        and find the latest build. For now, we return a placeholder.
        """
        # TODO: Implement actual latest build detection
        return "20240101_00:00"
    
    async def _download_file(self, url: str, dest_path: Path) -> None:
        """Download a file with progress reporting.
        
        Args:
            url: URL to download.
            dest_path: Destination path for the file.
        """
        temp_file = dest_path / "rootfs.tar.xz.tmp"
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                
                total = int(response.headers.get("content-length", 0))
                downloaded = 0
                
                with open(temp_file, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        self._report_progress(
                            f"Downloading {url.split('/')[-1]}",
                            downloaded,
                            total,
                        )
        
        # Extract the tar.xz file
        await self._extract_rootfs(temp_file, dest_path)
        
        # Remove temp file
        temp_file.unlink()
    
    async def _extract_rootfs(self, tar_path: Path, dest_path: Path) -> None:
        """Extract rootfs tar.xz file.
        
        Args:
            tar_path: Path to tar.xz file.
            dest_path: Destination directory.
        """
        self._report_progress("Extracting rootfs...", 0, 100)
        
        # Open xz compressed tar
        with lzma.open(tar_path, "rb") as xz_file:
            with tarfile.open(fileobj=xz_file, mode="r|") as tar:
                tar.extractall(path=dest_path)
        
        self._report_progress("Extraction complete", 100, 100)
    
    async def _setup_container(self, config: ContainerConfig, rootfs_path: Path) -> None:
        """Setup container after rootfs extraction.
        
        Configures:
        - DNS resolution
        - User accounts
        - Environment variables
        - TMOE-specific files
        """
        # Setup DNS
        await self._setup_dns(rootfs_path)
        
        # Setup users
        await self._setup_users(config, rootfs_path)
        
        # Setup TMOE environment
        await self._setup_tmoe_env(config, rootfs_path)
    
    async def _setup_dns(self, rootfs_path: Path) -> None:
        """Setup DNS configuration."""
        resolv_conf = rootfs_path / "etc" / "resolv.conf"
        resolv_conf.parent.mkdir(parents=True, exist_ok=True)
        
        # Use Google DNS as default
        dns_content = """nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 2001:4860:4860::8888
nameserver 2001:4860:4860::8844
"""
        resolv_conf.write_text(dns_content)
    
    async def _setup_users(self, config: ContainerConfig, rootfs_path: Path) -> None:
        """Setup user accounts."""
        # Create non-root user if needed
        if config.user != "root":
            passwd_file = rootfs_path / "etc" / "passwd"
            if passwd_file.exists():
                # Check if user exists
                content = passwd_file.read_text()
                if f"{config.user}:" not in content:
                    # Add user
                    user_line = f"{config.user}:x:{config.uid}:{config.gid}:{config.user}:{config.home}:/bin/bash\n"
                    passwd_file.write_text(content + user_line)
            
            # Create home directory
            home_path = rootfs_path / config.home.lstrip("/")
            home_path.mkdir(parents=True, exist_ok=True)
    
    async def _setup_tmoe_env(self, config: ContainerConfig, rootfs_path: Path) -> None:
        """Setup TMOE-specific environment."""
        # Create TMOE environment directory
        tmoe_env_dir = rootfs_path / "usr" / "local" / "etc" / "tmoe-linux" / "environment"
        tmoe_env_dir.mkdir(parents=True, exist_ok=True)
        
        # Create environment file
        env_file = tmoe_env_dir / "container.env"
        env_content = f"""# TMOE Container Environment
export TMOE_CONTAINER_NAME="{config.name}"
export TMOE_CONTAINER_TYPE="{config.container_type}"
export TMOE_CHROOT="false"
export TMOE_PROOT="true"
export TMOE_ARCH="{config.arch}"
export TMOE_DISTRO="{config.distro}"
"""
        env_file.write_text(env_content)
        
        # Create profile.d entry
        profile_d = rootfs_path / "etc" / "profile.d"
        profile_d.mkdir(parents=True, exist_ok=True)
        
        profile_file = profile_d / "000_tmoe_env.sh"
        profile_file.write_text(f'source "{env_file}"\n')
        
        # Make executable
        os.chmod(profile_file, 0o644)
