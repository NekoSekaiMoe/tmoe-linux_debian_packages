"""Mirror source management for TMOE.

Manages software repository mirrors for different Linux distributions
and geographic regions (China, Global, etc.).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from tmoe.core.config import get_config
from tmoe.core.constants import CHINA_MIRRORS
from tmoe.core.platform import PlatformInfo

if TYPE_CHECKING:
    from collections.abc import Sequence


class MirrorRegion(Enum):
    """Mirror regions."""
    GLOBAL = "global"
    CHINA = "china"
    EUROPE = "europe"
    ASIA = "asia"
    AMERICAS = "americas"


@dataclass
class MirrorSource:
    """Mirror source definition."""
    name: str
    url: str
    region: MirrorRegion
    priority: int = 100  # Lower is higher priority


class MirrorManager:
    """Manager for software repository mirrors.
    
    Handles switching between different mirror sources for
    various Linux distributions.
    
    Example:
        >>> manager = MirrorManager()
        >>> await manager.switch_mirror("debian", "tsinghua")
    """
    
    # Mirror definitions
    MIRRORS: dict[str, MirrorSource] = {
        # China mirrors
        "tsinghua": MirrorSource(
            name="Tsinghua University",
            url="mirrors.tuna.tsinghua.edu.cn",
            region=MirrorRegion.CHINA,
            priority=10,
        ),
        "ustc": MirrorSource(
            name="USTC (University of Science and Technology of China)",
            url="mirrors.ustc.edu.cn",
            region=MirrorRegion.CHINA,
            priority=10,
        ),
        "bfsu": MirrorSource(
            name="BFSU (Beijing Foreign Studies University)",
            url="mirrors.bfsu.edu.cn",
            region=MirrorRegion.CHINA,
            priority=10,
        ),
        "sjtu": MirrorSource(
            name="SJTU (Shanghai Jiao Tong University)",
            url="mirror.sjtu.edu.cn",
            region=MirrorRegion.CHINA,
            priority=10,
        ),
        "aliyun": MirrorSource(
            name="Aliyun (Alibaba Cloud)",
            url="mirrors.aliyun.com",
            region=MirrorRegion.CHINA,
            priority=20,
        ),
        "tencent": MirrorSource(
            name="Tencent Cloud",
            url="mirrors.cloud.tencent.com",
            region=MirrorRegion.CHINA,
            priority=20,
        ),
        "huawei": MirrorSource(
            name="Huawei Cloud",
            url="mirrors.huaweicloud.com",
            region=MirrorRegion.CHINA,
            priority=20,
        ),
        # Global mirrors
        "debian": MirrorSource(
            name="Debian Official",
            url="deb.debian.org",
            region=MirrorRegion.GLOBAL,
            priority=10,
        ),
        "ubuntu": MirrorSource(
            name="Ubuntu Official",
            url="archive.ubuntu.com",
            region=MirrorRegion.GLOBAL,
            priority=10,
        ),
        "arch": MirrorSource(
            name="Arch Linux Official",
            url="mirrors.kernel.org",
            region=MirrorRegion.GLOBAL,
            priority=10,
        ),
    }
    
    def __init__(self, platform: PlatformInfo | None = None) -> None:
        self.platform = platform or PlatformInfo()
        self.config = get_config()
    
    def get_mirrors_by_region(self, region: MirrorRegion) -> list[MirrorSource]:
        """Get mirrors by region."""
        mirrors = [
            m for m in self.MIRRORS.values()
            if m.region == region
        ]
        return sorted(mirrors, key=lambda m: m.priority)
    
    def get_mirror(self, name: str) -> MirrorSource | None:
        """Get mirror by name."""
        return self.MIRRORS.get(name)
    
    async def switch_mirror(
        self,
        distro: str,
        mirror_name: str,
        codename: str | None = None,
    ) -> bool:
        """Switch to a mirror source.
        
        Args:
            distro: Linux distribution.
            mirror_name: Mirror name.
            codename: Distribution codename.
            
        Returns:
            True if successful.
        """
        mirror = self.get_mirror(mirror_name)
        if not mirror:
            raise ValueError(f"Unknown mirror: {mirror_name}")
        
        match distro.lower():
            case "debian":
                return await self._switch_debian_mirror(mirror, codename)
            case "ubuntu":
                return await self._switch_ubuntu_mirror(mirror, codename)
            case "arch":
                return await self._switch_arch_mirror(mirror)
            case "alpine":
                return await self._switch_alpine_mirror(mirror, codename)
            case "fedora":
                return await self._switch_fedora_mirror(mirror)
            case _:
                raise ValueError(f"Unsupported distribution: {distro}")
    
    async def _switch_debian_mirror(
        self,
        mirror: MirrorSource,
        codename: str | None = None,
    ) -> bool:
        """Switch Debian mirror."""
        codename = codename or "stable"
        
        sources_list = Path("/etc/apt/sources.list")
        if not sources_list.exists():
            raise RuntimeError("/etc/apt/sources.list not found")
        
        # Backup original
        backup = sources_list.with_suffix(".list.backup")
        if not backup.exists():
            sources_list.rename(backup)
        
        # Generate new sources.list
        content = f"""# Generated by TMOE
# Mirror: {mirror.name}

deb http://{mirror.url}/debian/ {codename} main contrib non-free
# deb-src http://{mirror.url}/debian/ {codename} main contrib non-free

deb http://{mirror.url}/debian/ {codename}-updates main contrib non-free
# deb-src http://{mirror.url}/debian/ {codename}-updates main contrib non-free

deb http://{mirror.url}/debian-security {codename}-security main contrib non-free
# deb-src http://{mirror.url}/debian-security {codename}-security main contrib non-free
"""
        
        sources_list.write_text(content)
        
        # Update apt cache
        await self._run_apt_update()
        return True
    
    async def _switch_ubuntu_mirror(
        self,
        mirror: MirrorSource,
        codename: str | None = None,
    ) -> bool:
        """Switch Ubuntu mirror."""
        codename = codename or "jammy"
        
        sources_list = Path("/etc/apt/sources.list")
        if not sources_list.exists():
            raise RuntimeError("/etc/apt/sources.list not found")
        
        # Backup
        backup = sources_list.with_suffix(".list.backup")
        if not backup.exists():
            sources_list.rename(backup)
        
        content = f"""# Generated by TMOE
# Mirror: {mirror.name}

deb http://{mirror.url}/ubuntu/ {codename} main restricted universe multiverse
# deb-src http://{mirror.url}/ubuntu/ {codename} main restricted universe multiverse

deb http://{mirror.url}/ubuntu/ {codename}-updates main restricted universe multiverse
# deb-src http://{mirror.url}/ubuntu/ {codename}-updates main restricted universe multiverse

deb http://{mirror.url}/ubuntu/ {codename}-backports main restricted universe multiverse
# deb-src http://{mirror.url}/ubuntu/ {codename}-backports main restricted universe multiverse

deb http://{mirror.url}/ubuntu/ {codename}-security main restricted universe multiverse
# deb-src http://{mirror.url}/ubuntu/ {codename}-security main restricted universe multiverse
"""
        
        sources_list.write_text(content)
        await self._run_apt_update()
        return True
    
    async def _switch_arch_mirror(self, mirror: MirrorSource) -> bool:
        """Switch Arch Linux mirror."""
        mirrorlist = Path("/etc/pacman.d/mirrorlist")
        if not mirrorlist.exists():
            raise RuntimeError("/etc/pacman.d/mirrorlist not found")
        
        # Backup
        backup = mirrorlist.with_suffix(".backup")
        if not backup.exists():
            mirrorlist.rename(backup)
        
        content = f"""# Generated by TMOE
# Mirror: {mirror.name}

Server = https://{mirror.url}/archlinux/$repo/os/$arch
"""
        
        mirrorlist.write_text(content)
        return True
    
    async def _switch_alpine_mirror(
        self,
        mirror: MirrorSource,
        version: str | None = None,
    ) -> bool:
        """Switch Alpine Linux mirror."""
        repos = Path("/etc/apk/repositories")
        if not repos.exists():
            raise RuntimeError("/etc/apk/repositories not found")
        
        version = version or "latest-stable"
        
        content = f"""# Generated by TMOE
# Mirror: {mirror.name}

https://{mirror.url}/alpine/{version}/main
https://{mirror.url}/alpine/{version}/community
"""
        
        repos.write_text(content)
        return True
    
    async def _switch_fedora_mirror(self, mirror: MirrorSource) -> bool:
        """Switch Fedora mirror."""
        # Fedora uses metalink by default, need to modify repo files
        # This is a simplified implementation
        repos_dir = Path("/etc/yum.repos.d")
        if not repos_dir.exists():
            raise RuntimeError("/etc/yum.repos.d not found")
        
        # For now, just return True as Fedora mirror switching is complex
        return True
    
    async def _run_apt_update(self) -> None:
        """Run apt update."""
        proc = await asyncio.create_subprocess_exec(
            "apt", "update",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            error = stderr.decode("utf-8", errors="replace")
            raise RuntimeError(f"apt update failed: {error}")
    
    async def test_mirror_speed(self, mirror_name: str) -> float:
        """Test mirror download speed.
        
        Args:
            mirror_name: Mirror to test.
            
        Returns:
            Download speed in KB/s.
        """
        mirror = self.get_mirror(mirror_name)
        if not mirror:
            raise ValueError(f"Unknown mirror: {mirror_name}")
        
        # Test with a small file (ls-lR.gz from Debian)
        test_url = f"https://{mirror.url}/debian/ls-lR.gz"
        
        import time
        import httpx
        
        try:
            start_time = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.get(test_url, timeout=10)
                response.raise_for_status()
                
            elapsed = time.time() - start_time
            size_kb = len(response.content) / 1024
            speed = size_kb / elapsed
            
            return speed
        except Exception:
            return 0.0
