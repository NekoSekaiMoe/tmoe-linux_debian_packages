"""noVNC Web client integration for TMOE.

Provides Web-based VNC access using noVNC and websockify.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class NoVncConfig:
    """noVNC configuration."""
    web_port: int = 36080
    vnc_host: str = "localhost"
    vnc_port: int = 5902
    base_path: str = "/novnc"


class NoVncManager:
    """Manager for noVNC Web VNC client.
    
    noVNC provides a web-based VNC client that can be accessed
    through a web browser.
    
    Example:
        >>> manager = NoVncManager()
        >>> await manager.start()
        >>> # Open browser to http://localhost:36080/vnc.html
        >>> await manager.stop()
    """
    
    NOVNC_REPO = "https://github.com/novnc/noVNC.git"
    WEBSOCKIFY_REPO = "https://github.com/novnc/websockify.git"
    
    def __init__(self, data_dir: Path | None = None) -> None:
        from tmoe.core.platform import PlatformInfo
        
        self.platform = PlatformInfo()
        self.data_dir = data_dir or self.platform.data_dir
        self.novnc_dir = self.data_dir / "novnc"
        self.websockify_dir = self.data_dir / "websockify"
        
        self.config = NoVncConfig()
        self._websockify_proc: asyncio.subprocess.Process | None = None
    
    @property
    def is_installed(self) -> bool:
        """Check if noVNC is installed."""
        return (
            self.novnc_dir.exists() and
            (self.novnc_dir / "vnc.html").exists()
        )
    
    async def install(self) -> bool:
        """Install noVNC and websockify.
        
        Returns:
            True if installation succeeded.
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Install noVNC
        if not self.is_installed:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "git", "clone", "--depth", "1", self.NOVNC_REPO,
                    str(self.novnc_dir),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.wait()
                
                if proc.returncode != 0:
                    return False
            except Exception:
                return False
        
        # Install websockify
        if not self.websockify_dir.exists():
            try:
                proc = await asyncio.create_subprocess_exec(
                    "git", "clone", "--depth", "1", self.WEBSOCKIFY_REPO,
                    str(self.websockify_dir),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.wait()
                
                if proc.returncode != 0:
                    return False
            except Exception:
                return False
        
        return True
    
    def _get_websockify_cmd(self) -> list[str]:
        """Build websockify command."""
        # Check for system websockify first
        websockify_bin = shutil.which("websockify")
        
        if websockify_bin:
            return [
                websockify_bin,
                f"{self.config.web_port}",
                f"{self.config.vnc_host}:{self.config.vnc_port}",
                "--web", str(self.novnc_dir),
                "--cert", "self.pem",
            ]
        else:
            # Use bundled websockify
            websockify_py = self.websockify_dir / "websockify.py"
            return [
                "python3", str(websockify_py),
                f"{self.config.web_port}",
                f"{self.config.vnc_host}:{self.config.vnc_port}",
                "--web", str(self.novnc_dir),
            ]
    
    async def start(self) -> str:
        """Start noVNC server.
        
        Returns:
            URL to access noVNC.
        """
        if not self.is_installed:
            success = await self.install()
            if not success:
                raise RuntimeError("Failed to install noVNC")
        
        # Stop existing instance
        if self._websockify_proc:
            await self.stop()
        
        # Start websockify
        cmd = self._get_websockify_cmd()
        
        self._websockify_proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        # Wait a moment for server to start
        await asyncio.sleep(1)
        
        # Check if process is running
        if self._websockify_proc.returncode is not None:
            stdout, stderr = await self._websockify_proc.communicate()
            error = stderr.decode("utf-8", errors="replace")
            raise RuntimeError(f"Failed to start noVNC: {error}")
        
        # Return access URL
        return f"http://localhost:{self.config.web_port}/vnc.html?host=localhost&port={self.config.web_port}"
    
    async def stop(self) -> None:
        """Stop noVNC server."""
        if self._websockify_proc:
            self._websockify_proc.terminate()
            try:
                await asyncio.wait_for(self._websockify_proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._websockify_proc.kill()
                await self._websockify_proc.wait()
            self._websockify_proc = None
    
    async def is_running(self) -> bool:
        """Check if noVNC is running."""
        if self._websockify_proc is None:
            return False
        
        # Check if process is still running
        if self._websockify_proc.returncode is None:
            return True
        
        return False
    
    def get_url(self) -> str:
        """Get noVNC access URL."""
        return f"http://localhost:{self.config.web_port}/vnc.html"
