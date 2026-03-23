"""Download management for TMOE.

Provides unified interface for downloading files using various backends:
- aria2 (with RPC support)
- curl
- wget
- Python httpx (fallback)
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

import httpx

from tmoe.core.platform import PlatformInfo

if TYPE_CHECKING:
    from collections.abc import Callable


class DownloadBackend(str, Enum):
    """Available download backends."""
    ARIA2 = "aria2"
    CURL = "curl"
    WGET = "wget"
    HTTpx = "httpx"


@dataclass
class DownloadTask:
    """Represents a download task.
    
    Attributes:
        url: URL to download from.
        dest: Destination path for the file.
        backend: Preferred download backend.
        headers: Optional HTTP headers.
        cookies: Optional HTTP cookies.
        concurrent: Number of concurrent connections (for aria2).
        max_speed: Maximum download speed (e.g., "1M", "500K").
        resume: Whether to resume partial downloads.
    """
    url: str
    dest: Path
    backend: DownloadBackend = DownloadBackend.ARIA2
    headers: dict[str, str] = field(default_factory=dict)
    cookies: dict[str, str] = field(default_factory=dict)
    concurrent: int = 4
    max_speed: str | None = None
    resume: bool = True


@dataclass
class Aria2Config:
    """Configuration for aria2 daemon.
    
    Attributes:
        enabled: Whether aria2 daemon is enabled.
        rpc_port: RPC port for aria2 daemon.
        rpc_secret: RPC secret token.
        max_connections: Maximum connections per server.
        split: Number of splits for single file.
        min_split_size: Minimum split size.
        dir: Default download directory.
        config_file: Path to aria2 configuration file.
    """
    enabled: bool = False
    rpc_port: int = 6800
    rpc_secret: str = "tmoe"
    max_connections: int = 16
    split: int = 16
    min_split_size: str = "1M"
    dir: Path = field(default_factory=lambda: Path.home() / "Downloads")
    config_file: Path = field(
        default_factory=lambda: Path("/usr/local/etc/tmoe-linux/aria2/aria2.conf"),
    )


class DownloadManager:
    """Unified download manager supporting multiple backends.
    
    Automatically selects the best available backend and provides
    progress tracking for downloads.
    
    Example:
        >>> manager = DownloadManager()
        >>> task = DownloadTask(
        ...     url="https://example.com/file.zip",
        ...     dest=Path("/tmp/file.zip"),
        ... )
        >>> await manager.download(task)
    """
    
    def __init__(self, platform: PlatformInfo | None = None) -> None:
        self.platform = platform or PlatformInfo()
        self._progress_callback: Callable[[str, int, int], None] | None = None
        self._aria2_config: Aria2Config | None = None
    
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
    
    def detect_backends(self) -> list[DownloadBackend]:
        """Detect available download backends.
        
        Returns:
            List of available backends in order of preference.
        """
        available: list[DownloadBackend] = []
        
        if shutil.which("aria2c"):
            available.append(DownloadBackend.ARIA2)
        if shutil.which("curl"):
            available.append(DownloadBackend.CURL)
        if shutil.which("wget"):
            available.append(DownloadBackend.WGET)
        
        # Python httpx is always available
        available.append(DownloadBackend.HTTpx)
        
        return available
    
    def get_best_backend(self) -> DownloadBackend:
        """Get the best available backend.
        
        Returns:
            The best available download backend.
        """
        available = self.detect_backends()
        return available[0] if available else DownloadBackend.HTTpx
    
    async def download(
        self,
        task: DownloadTask,
        backend: DownloadBackend | None = None,
    ) -> Path:
        """Download a file using specified or best available backend.
        
        Args:
            task: Download task configuration.
            backend: Specific backend to use (auto-detected if None).
        
        Returns:
            Path to the downloaded file.
        
        Raises:
            RuntimeError: If download fails.
        """
        use_backend = backend or task.backend or self.get_best_backend()
        
        # Ensure destination directory exists
        task.dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if already exists and not resuming
        if task.dest.exists() and not task.resume:
            task.dest.unlink()
        
        try:
            if use_backend == DownloadBackend.ARIA2:
                return await self._download_aria2(task)
            elif use_backend == DownloadBackend.CURL:
                return await self._download_curl(task)
            elif use_backend == DownloadBackend.WGET:
                return await self._download_wget(task)
            else:
                return await self._download_httpx(task)
        except Exception as e:
            raise RuntimeError(f"Download failed with {use_backend}: {e}") from e
    
    async def _download_aria2(self, task: DownloadTask) -> Path:
        """Download using aria2.
        
        Args:
            task: Download task configuration.
        
        Returns:
            Path to downloaded file.
        """
        cmd = [
            "aria2c",
            "--console-log-level=warn",
            f"--split={task.concurrent}",
            f"--max-connection-per-server={task.concurrent}",
            "--min-split-size=1M",
        ]
        
        if task.resume:
            cmd.append("--continue=true")
        
        if task.max_speed:
            cmd.extend([f"--max-download-limit={task.max_speed}"])
        
        if task.dest.exists() and task.resume:
            # Resume from existing file
            cmd.extend(["-o", str(task.dest.name)])
            cmd.extend(["--dir", str(task.dest.parent)])
        else:
            cmd.extend(["-o", str(task.dest.name)])
            cmd.extend(["--dir", str(task.dest.parent)])
        
        # Add headers
        for key, value in task.headers.items():
            cmd.extend(["--header", f"{key}: {value}"])
        
        cmd.append(task.url)
        
        self._report_progress(f"Downloading {task.dest.name} with aria2...", 0, 0)
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"aria2 failed: {stderr.decode()}")
        
        self._report_progress(f"Downloaded {task.dest.name}", 100, 100)
        return task.dest
    
    async def _download_curl(self, task: DownloadTask) -> Path:
        """Download using curl.
        
        Args:
            task: Download task configuration.
        
        Returns:
            Path to downloaded file.
        """
        cmd = ["curl", "-fSL", "--progress-bar"]
        
        if task.resume and task.dest.exists():
            cmd.extend(["-C", "-"])
        
        if task.max_speed:
            cmd.extend(["--limit-rate", task.max_speed])
        
        # Add headers
        for key, value in task.headers.items():
            cmd.extend(["-H", f"{key}: {value}"])
        
        cmd.extend(["-o", str(task.dest), task.url])
        
        self._report_progress(f"Downloading {task.dest.name} with curl...", 0, 0)
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"curl failed: {stderr.decode()}")
        
        self._report_progress(f"Downloaded {task.dest.name}", 100, 100)
        return task.dest
    
    async def _download_wget(self, task: DownloadTask) -> Path:
        """Download using wget.
        
        Args:
            task: Download task configuration.
        
        Returns:
            Path to downloaded file.
        """
        cmd = ["wget", "--progress=bar:force"]
        
        if task.resume and task.dest.exists():
            cmd.append("-c")
        
        # wget doesn't have direct rate limit option, use curl instead
        cmd.extend(["-O", str(task.dest), task.url])
        
        self._report_progress(f"Downloading {task.dest.name} with wget...", 0, 0)
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"wget failed: {stderr.decode()}")
        
        self._report_progress(f"Downloaded {task.dest.name}", 100, 100)
        return task.dest
    
    async def _download_httpx(self, task: DownloadTask) -> Path:
        """Download using Python httpx (fallback).
        
        Args:
            task: Download task configuration.
        
        Returns:
            Path to downloaded file.
        """
        headers = dict(task.headers)
        
        # Set resume position if file exists
        resume_pos = 0
        if task.resume and task.dest.exists():
            resume_pos = task.dest.stat().st_size
            headers["Range"] = f"bytes={resume_pos}-"
        
        self._report_progress(f"Downloading {task.dest.name}...", 0, 0)
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            async with client.stream("GET", task.url, headers=headers) as response:
                response.raise_for_status()
                
                total = int(response.headers.get("content-length", 0))
                if resume_pos > 0:
                    total += resume_pos
                
                mode = "ab" if resume_pos > 0 else "wb"
                downloaded = resume_pos
                
                with open(task.dest, mode) as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        self._report_progress(
                            f"Downloading {task.dest.name}",
                            downloaded,
                            total,
                        )
        
        self._report_progress(f"Downloaded {task.dest.name}", 100, 100)
        return task.dest
    
    def get_aria2_config(self) -> Aria2Config:
        """Get or create aria2 configuration.
        
        Returns:
            Current aria2 configuration.
        """
        if self._aria2_config is None:
            config_file = Path("/usr/local/etc/tmoe-linux/aria2/aria2.conf")
            if config_file.exists():
                self._aria2_config = self._load_aria2_config(config_file)
            else:
                self._aria2_config = Aria2Config()
        return self._aria2_config
    
    def _load_aria2_config(self, config_file: Path) -> Aria2Config:
        """Load aria2 configuration from file.
        
        Args:
            config_file: Path to aria2 configuration file.
        
        Returns:
            Parsed aria2 configuration.
        """
        config = Aria2Config()
        
        try:
            content = config_file.read_text()
            for line in content.split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == "rpc-listen-port":
                        config.rpc_port = int(value)
                    elif key == "rpc-secret":
                        config.rpc_secret = value
                    elif key == "max-connection-per-server":
                        config.max_connections = int(value)
                    elif key == "split":
                        config.split = int(value)
                    elif key == "min-split-size":
                        config.min_split_size = value
                    elif key == "dir":
                        config.dir = Path(value)
        except Exception:
            pass  # Use defaults if parsing fails
        
        return config
    
    def save_aria2_config(self, config: Aria2Config) -> None:
        """Save aria2 configuration to file.
        
        Args:
            config: Aria2 configuration to save.
        """
        config.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        content = f"""# TMOE aria2 Configuration
# Generated by tmoe

# Basic Settings
enable-rpc=true
rpc-listen-port={config.rpc_port}
rpc-secret={config.rpc_secret}

# Download Settings
max-connection-per-server={config.max_connections}
split={config.split}
min-split-size={config.min_split_size}
dir={config.dir}

# Session Management
input-file={config.config_file.parent}/aria2.session
save-session={config.config_file.parent}/aria2.session
save-session-interval=60

# Advanced Settings
continue=true
max-concurrent-downloads=5
max-overall-download-limit=0
max-download-limit=0
max-overall-upload-limit=0
max-upload-limit=0

# BT Settings
bt-enable-lpd=true
bt-max-peers=55
follow-torrent=true
enable-dht=true
enable-dht6=true
enable-peer-exchange=true
seed-time=0
"""
        
        config.config_file.write_text(content)
        self._aria2_config = config
    
    def update_bt_trackers(self) -> bool:
        """Update BitTorrent tracker list.
        
        Fetches the latest BT tracker list from public sources
        and updates the aria2 configuration.
        
        Returns:
            True if update was successful.
        """
        try:
            # Fetch tracker list from ngosang/trackerslist
            url = "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_best.txt"
            result = subprocess.run(
                ["curl", "-fsSL", url],
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            if result.returncode != 0:
                return False
            
            trackers = [t.strip() for t in result.stdout.strip().split("\n") if t.strip()]
            if not trackers:
                return False
            
            # Update aria2 config with new trackers
            config = self.get_aria2_config()
            tracker_line = ",".join(trackers)
            
            config_content = config.config_file.read_text()
            
            # Replace or Add bt-tracker line
            lines = config_content.split("\n")
            bt_tracker_found = False
            for i, line in enumerate(lines):
                if line.strip().startswith("bt-tracker="):
                    lines[i] = f"bt-tracker={tracker_line}"
                    bt_tracker_found = True
                    break
            
            if not bt_tracker_found:
                lines.append(f"bt-tracker={tracker_line}")
            
            config.config_file.write_text("\n".join(lines))
            return True
            
        except Exception:
            return False
    
    async def download_batch(
        self,
        tasks: list[DownloadTask],
        max_concurrent: int = 3,
    ) -> list[Path]:
        """Download multiple files concurrently.
        
        Args:
            tasks: List of download tasks.
            max_concurrent: Maximum number of concurrent downloads.
        
        Returns:
            List of paths to downloaded files.
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def download_with_limit(task: DownloadTask) -> Path:
            async with semaphore:
                return await self.download(task)
        
        results = await asyncio.gather(
            *[download_with_limit(task) for task in tasks],
            return_exceptions=True,
        )
        
        # Check for errors
        for result in results:
            if isinstance(result, Exception):
                raise result
        
        return [r for r in results if isinstance(r, Path)]
