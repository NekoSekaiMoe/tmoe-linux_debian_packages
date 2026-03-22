"""LXC image downloading for TMOE.

Downloads container rootfs from LXC image servers.
"""

from __future__ import annotations

import asyncio
import lzma
import os
import re
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class LXCImageInfo:
    """LXC image information."""
    distro: str
    release: str
    arch: str
    variant: str = "default"
    build_date: str = ""
    url: str = ""
    filename: str = ""


class LXCImageClient:
    """Client for downloading LXC images.
    
    Downloads container rootfs from LXC image servers:
    - images.linuxcontainers.org (official)
    - Custom mirrors
    
    Example:
        >>> client = LXCImageClient()
        >>> image = await client.find_image("debian", "stable", "arm64")
        >>> await client.download_image(image, Path("/path/to/rootfs"))
    """
    
    # LXC official image server
    DEFAULT_MIRROR = "https://images.linuxcontainers.org/images"
    
    # Alternative mirrors
    MIRRORS = {
        "official": "https://images.linuxcontainers.org/images",
        "tsinghua": "https://mirrors.tuna.tsinghua.edu.cn/lxc-images/images",
        "ustc": "https://mirrors.ustc.edu.cn/lxc-images/images",
    }
    
    # Architecture mappings (normalized -> LXC name)
    ARCH_MAPPINGS = {
        "arm64": "arm64",
        "amd64": "amd64",
        "armhf": "armhf",
        "armel": "armel",
        "i386": "i386",
        "mips64el": "mips64el",
        "mipsel": "mipsel",
        "ppc64el": "ppc64el",
        "s390x": "s390x",
        "riscv64": "riscv64",
    }
    
    def __init__(self, mirror: str | None = None) -> None:
        self.mirror = mirror or self.DEFAULT_MIRROR
        self._progress_callback: Callable[[str, int, int], None] | None = None
    
    def set_progress_callback(
        self,
        callback: Callable[[str, int, int], None],
    ) -> None:
        """Set callback for download progress."""
        self._progress_callback = callback
    
    def _report_progress(self, message: str, current: int, total: int) -> None:
        """Report download progress."""
        if self._progress_callback:
            self._progress_callback(message, current, total)
    
    def _get_lxc_arch(self, arch: str) -> str:
        """Convert normalized arch to LXC arch name."""
        return self.ARCH_MAPPINGS.get(arch, arch)
    
    async def list_images(
        self,
        distro: str,
        release: str,
        arch: str,
    ) -> list[LXCImageInfo]:
        """List available images for distribution.
        
        Args:
            distro: Distribution name (e.g., 'debian', 'ubuntu')
            release: Release name (e.g., 'stable', 'jammy')
            arch: Architecture
            
        Returns:
            List of available image builds.
        """
        lxc_arch = self._get_lxc_arch(arch)
        
        # Build directory URL
        dir_url = f"{self.mirror}/{distro}/{release}/{lxc_arch}/default/"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(dir_url, timeout=30)
                response.raise_for_status()
                
                # Parse HTML to find directories
                html = response.text
                builds = self._parse_build_list(html)
                
                images = []
                for build in builds:
                    info = LXCImageInfo(
                        distro=distro,
                        release=release,
                        arch=arch,
                        variant="default",
                        build_date=build,
                        url=f"{dir_url}{build}/rootfs.tar.xz",
                        filename=f"rootfs.tar.xz",
                    )
                    images.append(info)
                
                return sorted(images, key=lambda x: x.build_date, reverse=True)
                
        except Exception as e:
            raise RuntimeError(f"Failed to list images: {e}")
    
    def _parse_build_list(self, html: str) -> list[str]:
        """Parse HTML to find build directories."""
        # Look for directory links (e.g., "20240101_00:00/")
        pattern = r'href="(\d{8}_\d{2}:\d{2})/"'
        matches = re.findall(pattern, html)
        return matches
    
    async def find_latest_image(
        self,
        distro: str,
        release: str,
        arch: str,
    ) -> LXCImageInfo | None:
        """Find the latest image for distribution.
        
        Args:
            distro: Distribution name
            release: Release name
            arch: Architecture
            
        Returns:
            Latest image info or None if not found.
        """
        images = await self.list_images(distro, release, arch)
        return images[0] if images else None
    
    async def download_image(
        self,
        image: LXCImageInfo,
        dest_path: Path,
    ) -> Path:
        """Download image rootfs.
        
        Args:
            image: Image info
            dest_path: Destination directory for rootfs
            
        Returns:
            Path to downloaded tar.xz file
        """
        dest_path.mkdir(parents=True, exist_ok=True)
        tar_path = dest_path / "rootfs.tar.xz"
        
        self._report_progress(f"Downloading {image.distro} {image.release}...", 0, 0)
        
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", image.url, timeout=300) as response:
                response.raise_for_status()
                
                total = int(response.headers.get("content-length", 0))
                downloaded = 0
                
                with open(tar_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        self._report_progress(
                            f"Downloading {image.distro} {image.release}",
                            downloaded,
                            total,
                        )
        
        self._report_progress(f"Downloaded {image.distro} {image.release}", downloaded, downloaded)
        return tar_path
    
    async def extract_rootfs(
        self,
        tar_path: Path,
        rootfs_path: Path,
    ) -> None:
        """Extract rootfs tar.xz to destination.
        
        Args:
            tar_path: Path to tar.xz file
            rootfs_path: Destination directory
        """
        self._report_progress("Extracting rootfs...", 0, 100)
        
        rootfs_path.mkdir(parents=True, exist_ok=True)
        
        # Extract using tarfile with lzma
        with lzma.open(tar_path, "rb") as xz_file:
            with tarfile.open(fileobj=xz_file, mode="r|") as tar:
                # Filter for security (Python 3.12+)
                if hasattr(tarfile, 'data_filter'):
                    tar.extraction_filter = getattr(tarfile, 'data_filter', None)
                tar.extractall(path=rootfs_path)
        
        self._report_progress("Extraction complete", 100, 100)
    
    async def download_and_extract(
        self,
        distro: str,
        release: str,
        arch: str,
        rootfs_path: Path,
    ) -> None:
        """Download and extract rootfs in one step.
        
        Args:
            distro: Distribution name
            release: Release name
            arch: Architecture
            rootfs_path: Destination for rootfs
        """
        # Find latest image
        image = await self.find_latest_image(distro, release, arch)
        if not image:
            raise RuntimeError(f"No image found for {distro} {release} {arch}")
        
        # Download to temp location
        cache_dir = Path.home() / ".cache" / "tmoe-linux" / "downloads"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        tar_path = await self.download_image(image, cache_dir)
        
        # Extract
        await self.extract_rootfs(tar_path, rootfs_path)
        
        # Optionally remove tar file to save space
        # tar_path.unlink()


class LXCImageManager:
    """High-level manager for LXC images."""
    
    def __init__(self) -> None:
        self.client = LXCImageClient()
    
    async def install_container(
        self,
        distro: str,
        release: str,
        arch: str,
        rootfs_path: Path,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> None:
        """Install a container from LXC image.
        
        Args:
            distro: Distribution name
            release: Release name
            arch: Architecture
            rootfs_path: Destination path
            progress_callback: Optional progress callback
        """
        if progress_callback:
            self.client.set_progress_callback(progress_callback)
        
        await self.client.download_and_extract(
            distro, release, arch, rootfs_path
        )
    
    def list_available_distros(self) -> list[str]:
        """List available distributions.
        
        Returns:
            List of distribution names.
        """
        # Known working distributions
        return [
            "debian",
            "ubuntu",
            "alpine",
            "archlinux",
            "fedora",
            "centos",
            "opensuse",
            "kali",
        ]
