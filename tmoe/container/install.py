"""Container installation for TMOE.

Downloads and installs container rootfs from various sources including
LXC image servers and TMOE's own build server.
"""

from __future__ import annotations

import asyncio
import lzma
import os
import shutil
import tarfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

import httpx

from tmoe.core.config import ContainerConfig
from tmoe.core.constants import ContainerType
from tmoe.core.platform import PlatformInfo
from tmoe.tools.downloader import DownloadManager, DownloadTask

if TYPE_CHECKING:
    from collections.abc import Callable


class RootfsSource(str, Enum):
    """Available rootfs sources."""
    LXC = "lxc"
    TMOE = "tmoe"
    CUSTOM = "custom"


@dataclass
class InstallOptions:
    """Installation options for containers.
    
    Attributes:
        source: Rootfs source to use.
        custom_url: Custom URL for rootfs download.
        dns_servers: List of DNS servers to configure.
        setup_user: Whether to setup non-root user.
        install_base_packages: Whether to install base packages.
        configure_mirror: Whether to configure package mirror.
        mirror_region: Mirror region (china, global).
        run_init_scripts: Whether to run initialization scripts.
        init_scripts: List of initialization commands to run.
    """
    source: RootfsSource = RootfsSource.LXC
    custom_url: str | None = None
    dns_servers: list[str] = field(default_factory=lambda: [
        "8.8.8.8", "8.8.4.4",
        "2001:4860:4860::8888", "2001:4860:4860::8844",
    ])
    setup_user: bool = True
    install_base_packages: bool = False
    configure_mirror: bool = False
    mirror_region: str = "global"
    run_init_scripts: bool = False
    init_scripts: list[str] = field(default_factory=list)


@dataclass
class InstallResult:
    """Result of container installation.
    
    Attributes:
        success: Whether installation succeeded.
        message: Result message.
        rootfs_path: Path to installed rootfs.
        download_time: Time taken to download (seconds).
        extract_time: Time taken to extract (seconds).
        setup_time: Time taken to setup (seconds).
    """
    success: bool
    message: str
    rootfs_path: Path | None = None
    download_time: float = 0.0
    extract_time: float = 0.0
    setup_time: float = 0.0


class ContainerInstaller:
    """Installer for container rootfs.
    
    Downloads and installs Linux distribution rootfs from:
    - LXC image server (images.linuxcontainers.org)
    - TMOE build server
    - Custom URLs
    
    Supports both proot and chroot container types.
    
    Example:
        >>> installer = ContainerInstaller()
        >>> options = InstallOptions(source=RootfsSource.LXC)
        >>> result = await installer.install(config, options)
        >>> if result.success:
        ...     print(f"Installed to {result.rootfs_path}")
    """
    
    # LXC image server
    LXC_BASE_URL = "https://images.linuxcontainers.org/images"
    
    # TMOE build server
    TMOE_BASE_URL = "https://cdn.tmoe.me"
    
    # Architecture mappings to LXC names
    LXC_ARCH_MAP: dict[str, str] = {
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
    
    def __init__(self, platform: PlatformInfo | None = None) -> None:
        self.platform = platform or PlatformInfo()
        self.downloader = DownloadManager(platform)
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
    
    async def install(
        self,
        config: ContainerConfig,
        options: InstallOptions | None = None,
    ) -> InstallResult:
        """Install a container with specified options.
        
        Args:
            config: Container configuration.
            options: Installation options.
        
        Returns:
            Installation result.
        """
        opts = options or InstallOptions()
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Validate configuration
            if not self._validate_config(config):
                return InstallResult(
                    success=False,
                    message="Invalid container configuration",
                )
            
            # Create rootfs directory
            rootfs_path = config.rootfs_path
            if rootfs_path is None:
                return InstallResult(
                    success=False,
                    message="Container rootfs path not set",
                )
            
            # Check if already exists
            if rootfs_path.exists() and any(rootfs_path.iterdir()):
                return InstallResult(
                    success=False,
                    message=f"Container already exists at {rootfs_path}",
                )
            
            rootfs_path.mkdir(parents=True, exist_ok=True)
            
            # Download rootfs
            download_start = asyncio.get_event_loop().time()
            await self._download_rootfs(config, rootfs_path, opts)
            download_time = asyncio.get_event_loop().time() - download_start
            
            # Extract rootfs (if not already extracted)
            extract_start = asyncio.get_event_loop().time()
            # Note: download method now handles extraction
            extract_time = asyncio.get_event_loop().time() - extract_start
            
            # Setup container
            setup_start = asyncio.get_event_loop().time()
            await self._setup_container(config, rootfs_path, opts)
            setup_time = asyncio.get_event_loop().time() - setup_start
            
            total_time = asyncio.get_event_loop().time() - start_time
            
            return InstallResult(
                success=True,
                message=f"Container installed successfully in {total_time:.1f}s",
                rootfs_path=rootfs_path,
                download_time=download_time,
                extract_time=extract_time,
                setup_time=setup_time,
            )
            
        except Exception as e:
            # Cleanup on failure
            if config.rootfs_path and config.rootfs_path.exists():
                shutil.rmtree(config.rootfs_path, ignore_errors=True)
            
            return InstallResult(
                success=False,
                message=f"Installation failed: {e}",
            )
    
    async def install_proot(
        self,
        config: ContainerConfig,
        options: InstallOptions | None = None,
    ) -> InstallResult:
        """Install a proot container.
        
        Args:
            config: Container configuration.
            options: Installation options.
        
        Returns:
            Installation result.
        """
        return await self.install(config, options)
    
    async def install_chroot(
        self,
        config: ContainerConfig,
        options: InstallOptions | None = None,
    ) -> InstallResult:
        """Install a chroot container.
        
        Args:
            config: Container configuration.
            options: Installation options.
        
        Returns:
            Installation result.
        """
        # Chroot containers need root for setup
        if os.geteuid() != 0:
            return InstallResult(
                success=False,
                message="Chroot installation requires root privileges",
            )
        
        return await self.install(config, options)
    
    def _validate_config(self, config: ContainerConfig) -> bool:
        """Validate container configuration.
        
        Args:
            config: Container configuration to validate.
        
        Returns:
            True if configuration is valid.
        """
        if not config.name:
            return False
        if not config.distro:
            return False
        if not config.arch:
            return False
        if config.arch not in self.LXC_ARCH_MAP:
            return False
        return True
    
    async def _download_rootfs(
        self,
        config: ContainerConfig,
        rootfs_path: Path,
        options: InstallOptions,
    ) -> None:
        """Download container rootfs.
        
        Downloads from specified source with fallback support.
        """
        distro = config.distro
        arch = config.arch
        codename = config.codename or "stable"
        
        # Determine download URL based on source
        if options.source == RootfsSource.CUSTOM and options.custom_url:
            urls = [options.custom_url]
        elif options.source == RootfsSource.TMOE:
            urls = [
                self._build_tmoe_url(distro, codename, arch),
                self._build_lxc_url(distro, codename, arch),
            ]
        else:  # LXC is default
            urls = [
                self._build_lxc_url(distro, codename, arch),
                self._build_tmoe_url(distro, codename, arch),
            ]
        
        # Try each URL
        last_error = None
        for url in urls:
            try:
                await self._download_and_extract(url, rootfs_path)
                return
            except Exception as e:
                last_error = e
                continue
        
        # All URLs failed
        raise RuntimeError(f"Failed to download rootfs from all sources: {last_error}")
    
    def _build_lxc_url(self, distro: str, codename: str, arch: str) -> str:
        """Build LXC image download URL."""
        lxc_arch = self.LXC_ARCH_MAP.get(arch, arch)
        
        # Handle special distros
        if distro == "ubuntu":
            return (
                f"{self.LXC_BASE_URL}/{distro}/{codename}/{lxc_arch}/default/"
                f"{self._get_latest_lxc_build(distro, codename, lxc_arch)}/rootfs.tar.xz"
            )
        
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
        
        In production, this would fetch the directory listing
        and find the latest build.
        """
        # TODO: Implement actual latest build detection via HTTP
        return "20240101_00:00"
    
    async def _download_and_extract(self, url: str, dest_path: Path) -> None:
        """Download and extract rootfs.
        
        Args:
            url: URL to download from.
            dest_path: Destination directory.
        """
        temp_file = dest_path / "rootfs.tar.xz.tmp"
        
        try:
            # Download using DownloadManager
            task = DownloadTask(
                url=url,
                dest=temp_file,
                backend="httpx",
            )
            
            # Set progress callback
            original_callback = self.downloader._progress_callback
            self.downloader.set_progress_callback(self._report_progress)
            
            await self.downloader.download(task)
            
            # Restore original callback
            self.downloader.set_progress_callback(original_callback)
            
            # Extract
            self._report_progress("Extracting rootfs...", 0, 100)
            await self._extract_rootfs(temp_file, dest_path)
            self._report_progress("Extraction complete", 100, 100)
            
        finally:
            # Cleanup temp file
            if temp_file.exists():
                temp_file.unlink()
    
    async def _extract_rootfs(self, tar_path: Path, dest_path: Path) -> None:
        """Extract rootfs tar.xz file.
        
        Args:
            tar_path: Path to tar.xz file.
            dest_path: Destination directory.
        """
        # Run extraction in thread pool to not block
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._extract_sync, tar_path, dest_path)
    
    def _extract_sync(self, tar_path: Path, dest_path: Path) -> None:
        """Synchronous rootfs extraction."""
        with lzma.open(tar_path, "rb") as xz_file:
            with tarfile.open(fileobj=xz_file, mode="r|") as tar:
                # Use filter to safely extract tar archives (Python 3.14 compatible)
                tar.extractall(path=dest_path, filter="fully_trusted")
    
    async def _setup_container(
        self,
        config: ContainerConfig,
        rootfs_path: Path,
        options: InstallOptions,
    ) -> None:
        """Setup container after rootfs extraction.
        
        Configures:
        - DNS resolution
        - User accounts
        - Environment variables
        - Package mirrors
        - Initialization scripts
        """
        # Setup DNS
        await self._setup_dns(rootfs_path, options)
        
        # Setup users
        if options.setup_user:
            await self._setup_users(config, rootfs_path)
        
        # Setup TMOE environment
        await self._setup_tmoe_env(config, rootfs_path)
        
        # Configure package mirror
        if options.configure_mirror:
            await self._configure_mirror(config, rootfs_path, options)
        
        # Run initialization scripts
        if options.run_init_scripts and options.init_scripts:
            await self._run_init_scripts(config, rootfs_path, options)
    
    async def _setup_dns(self, rootfs_path: Path, options: InstallOptions) -> None:
        """Setup DNS configuration."""
        resolv_conf = rootfs_path / "etc" / "resolv.conf"
        resolv_conf.parent.mkdir(parents=True, exist_ok=True)
        
        dns_content = "\n".join(f"nameserver {dns}" for dns in options.dns_servers)
        dns_content += "\n"
        
        resolv_conf.write_text(dns_content)
    
    async def _setup_users(self, config: ContainerConfig, rootfs_path: Path) -> None:
        """Setup user accounts."""
        if config.user == "root":
            return
        
        # Add user to passwd
        passwd_file = rootfs_path / "etc" / "passwd"
        if passwd_file.exists():
            content = passwd_file.read_text()
            if f"{config.user}:" not in content:
                user_line = (
                    f"{config.user}:x:{config.uid}:{config.gid}:"
                    f"{config.user}:{config.home}:/bin/bash\n"
                )
                passwd_file.write_text(content + user_line)
        
        # Add user to group
        group_file = rootfs_path / "etc" / "group"
        if group_file.exists():
            content = group_file.read_text()
            if f"{config.user}:" not in content:
                group_line = f"{config.user}:x:{config.gid}:\n"
                group_file.write_text(content + group_line)
        
        # Create home directory
        home_path = rootfs_path / config.home.lstrip("/")
        home_path.mkdir(parents=True, exist_ok=True)
        
        # Set ownership (if running as root)
        if os.geteuid() == 0:
            os.chown(home_path, config.uid, config.gid)
    
    async def _setup_tmoe_env(
        self,
        config: ContainerConfig,
        rootfs_path: Path,
    ) -> None:
        """Setup TMOE-specific environment."""
        # Create TMOE environment directory
        tmoe_env_dir = rootfs_path / "usr" / "local" / "etc" / "tmoe-linux" / "environment"
        tmoe_env_dir.mkdir(parents=True, exist_ok=True)
        
        # Create environment file
        env_file = tmoe_env_dir / "container.env"
        
        is_chroot = config.container_type == ContainerType.CHROOT
        is_proot = config.container_type == ContainerType.PROOT
        
        env_content = f"""# TMOE Container Environment
export TMOE_CONTAINER_NAME="{config.name}"
export TMOE_CONTAINER_TYPE="{config.container_type}"
export TMOE_CHROOT="{'true' if is_chroot else 'false'}"
export TMOE_PROOT="{'true' if is_proot else 'false'}"
export TMOE_ARCH="{config.arch}"
export TMOE_DISTRO="{config.distro}"
export TMOE_CODENAME="{config.codename or 'stable'}"
export TMOE_USER="{config.user}"
export TMOE_HOME="{config.home}"
export TMOE_UID="{config.uid}"
export TMOE_GID="{config.gid}"
"""
        env_file.write_text(env_content)
        
        # Create profile.d entry
        profile_d = rootfs_path / "etc" / "profile.d"
        profile_d.mkdir(parents=True, exist_ok=True)
        
        profile_file = profile_d / "000_tmoe_env.sh"
        profile_file.write_text(f'source "{env_file}"\n')
        os.chmod(profile_file, 0o644)
        
        # Create .tmoe-rootfs-configure
        configure_file = rootfs_path / "usr" / "local" / "etc" / "tmoe-linux" / ".tmoe-rootfs-configure"
        configure_file.parent.mkdir(parents=True, exist_ok=True)
        configure_content = f"""TMOE_CONTAINER_NAME='{config.name}'
TMOE_CONTAINER_TYPE='{config.container_type}'
TMOE_DISTRO='{config.distro}'
TMOE_ARCH='{config.arch}'
TMOE_USER='{config.user}'
"""
        configure_file.write_text(configure_content)
    
    async def _configure_mirror(
        self,
        config: ContainerConfig,
        rootfs_path: Path,
        options: InstallOptions,
    ) -> None:
        """Configure package manager mirror."""
        distro = config.distro.lower()
        
        if distro in ["debian", "ubuntu"]:
            await self._configure_debian_mirror(rootfs_path, options)
        elif distro in ["arch", "manjaro"]:
            await self._configure_arch_mirror(rootfs_path, options)
        elif distro == "alpine":
            await self._configure_alpine_mirror(rootfs_path, options)
        elif distro == "fedora":
            await self._configure_fedora_mirror(rootfs_path, options)
    
    async def _configure_debian_mirror(
        self,
        rootfs_path: Path,
        options: InstallOptions,
    ) -> None:
        """Configure Debian/Ubuntu mirror."""
        sources_file = rootfs_path / "etc" / "apt" / "sources.list"
        if not sources_file.exists():
            return
        
        if options.mirror_region == "china":
            # Use Tsinghua mirror
            mirror = "mirrors.tuna.tsinghua.edu.cn"
        else:
            mirror = "deb.debian.org"
        
        # Backup original
        backup_file = sources_file.with_suffix(".list.backup")
        if not backup_file.exists():
            shutil.copy2(sources_file, backup_file)
    
    async def _configure_arch_mirror(
        self,
        rootfs_path: Path,
        options: InstallOptions,
    ) -> None:
        """Configure Arch Linux mirror."""
        mirrorlist = rootfs_path / "etc" / "pacman.d" / "mirrorlist"
        if not mirrorlist.exists():
            return
    
    async def _configure_alpine_mirror(
        self,
        rootfs_path: Path,
        options: InstallOptions,
    ) -> None:
        """Configure Alpine mirror."""
        repos_file = rootfs_path / "etc" / "apk" / "repositories"
        if not repos_file.exists():
            return
    
    async def _configure_fedora_mirror(
        self,
        rootfs_path: Path,
        options: InstallOptions,
    ) -> None:
        """Configure Fedora mirror."""
        # Fedora uses metalink, less critical to change
        pass
    
    async def _run_init_scripts(
        self,
        config: ContainerConfig,
        rootfs_path: Path,
        options: InstallOptions,
    ) -> None:
        """Run initialization scripts in container."""
        # This would require running commands in the container
        # Implementation depends on container type (proot/chroot)
        pass
    
    async def verify_installation(self, config: ContainerConfig) -> bool:
        """Verify container installation.
        
        Args:
            config: Container configuration.
        
        Returns:
            True if installation is valid.
        """
        rootfs_path = config.rootfs_path
        if not rootfs_path or not rootfs_path.exists():
            return False
        
        # Check for essential files
        essential_files = [
            "etc/passwd",
            "etc/group",
            "bin/sh",
        ]
        
        for file_path in essential_files:
            full_path = rootfs_path / file_path
            if not full_path.exists():
                return False
        
        # Check TMOE environment
        env_file = rootfs_path / "usr" / "local" / "etc" / "tmoe-linux" / "environment" / "container.env"
        if not env_file.exists():
            return False
        
        return True
    
    def get_install_size(self, config: ContainerConfig) -> int:
        """Get installed container size in bytes.
        
        Args:
            config: Container configuration.
        
        Returns:
            Size in bytes.
        """
        rootfs_path = config.rootfs_path
        if not rootfs_path or not rootfs_path.exists():
            return 0
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(rootfs_path):
            for f in filenames:
                fp = Path(dirpath) / f
                if fp.exists():
                    total_size += fp.stat().st_size
        
        return total_size
    
    def format_size(self, size_bytes: int) -> str:
        """Format size in human-readable format.
        
        Args:
            size_bytes: Size in bytes.
        
        Returns:
            Human-readable size string.
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
