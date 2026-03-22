"""VNC server management for TMOE.

Manages VNC server configuration, startup, and desktop environments.
Supports TigerVNC and TightVNC backends.
"""

from __future__ import annotations

import asyncio
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from tmoe.core.config import get_config
from tmoe.core.platform import PlatformInfo

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class VncConfig:
    """VNC configuration."""
    server: str = "tiger"
    resolution: str = "1440x720"
    display: int = 2
    depth: int = 24
    localhost: bool = False
    password: str | None = None


class VncManager:
    """VNC server manager.
    
    Manages VNC server lifecycle and configuration.
    
    Example:
        >>> manager = VncManager()
        >>> await manager.start_vnc(desktop="xfce")
    """
    
    def __init__(self, platform: PlatformInfo | None = None) -> None:
        self.platform = platform or PlatformInfo()
        self.config = get_config()
        self._vnc_config = VncConfig(
            server=self.config.vnc_server,
            resolution=self.config.vnc_resolution,
            display=self.config.vnc_display,
            depth=self.config.vnc_depth,
            localhost=self.config.vnc_localhost,
        )
    
    @property
    def vnc_config(self) -> VncConfig:
        """Get current VNC configuration."""
        return self._vnc_config
    
    def get_vnc_bin(self) -> str | None:
        """Get VNC server binary."""
        if self._vnc_config.server == "tiger":
            return shutil.which("tigervncserver") or shutil.which("Xtigervnc")
        elif self._vnc_config.server == "tight":
            return shutil.which("tightvncserver") or shutil.which("Xvnc")
        return None
    
    def get_display_port(self) -> int:
        """Get the VNC port for the current display."""
        return 5900 + self._vnc_config.display
    
    async def start_vnc(
        self,
        desktop: str | None = None,
        command: Sequence[str] | None = None,
    ) -> tuple[int, str]:
        """Start VNC server.
        
        Args:
            desktop: Desktop environment to start.
            command: Custom command to run instead of desktop.
            
        Returns:
            Tuple of (port, display_info).
        """
        vnc_bin = self.get_vnc_bin()
        if not vnc_bin:
            raise RuntimeError(f"VNC server '{self._vnc_config.server}' not found")
        
        # Build VNC command
        if self._vnc_config.server == "tiger":
            cmd = self._build_tiger_cmd(desktop, command)
        else:
            cmd = self._build_tight_cmd(desktop, command)
        
        # Start VNC
        proc = await asyncio.create_subprocess_exec(*cmd)
        await asyncio.sleep(1)  # Wait for server to start
        
        # Check if running
        if await self.is_running():
            port = self.get_display_port()
            display = f":{self._vnc_config.display}"
            return port, display
        else:
            raise RuntimeError("Failed to start VNC server")
    
    def _build_tiger_cmd(
        self,
        desktop: str | None,
        command: Sequence[str] | None,
    ) -> list[str]:
        """Build TigerVNC command."""
        display = f":{self._vnc_config.display}"
        
        cmd = [
            "Xtigervnc",
            display,
            "-geometry", self._vnc_config.resolution,
            "-depth", str(self._vnc_config.depth),
            "-pn",
            "-localhost", "yes" if self._vnc_config.localhost else "no",
        ]
        
        if desktop:
            # Add desktop session
            cmd.extend(["-Session", desktop])
        
        return cmd
    
    def _build_tight_cmd(
        self,
        desktop: str | None,
        command: Sequence[str] | None,
    ) -> list[str]:
        """Build TightVNC command."""
        display = f":{self._vnc_config.display}"
        
        cmd = [
            "Xvnc",
            display,
            "-geometry", self._vnc_config.resolution,
            "-depth", str(self._vnc_config.depth),
        ]
        
        if self._vnc_config.localhost:
            cmd.append("-localhost")
        
        return cmd
    
    async def stop_vnc(self) -> None:
        """Stop VNC server."""
        display = f":{self._vnc_config.display}"
        
        if self._vnc_config.server == "tiger":
            cmd = ["tigervncserver", "-kill", display]
        else:
            cmd = ["tightvncserver", "-kill", display]
        
        proc = await asyncio.create_subprocess_exec(*cmd)
        await proc.wait()
    
    async def is_running(self) -> bool:
        """Check if VNC server is running."""
        port = self.get_display_port()
        
        # Check if port is in use
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def configure(
        self,
        server: str | None = None,
        resolution: str | None = None,
        display: int | None = None,
        depth: int | None = None,
        localhost: bool | None = None,
    ) -> None:
        """Configure VNC settings.
        
        Args:
            server: VNC server type ('tiger' or 'tight').
            resolution: Display resolution (e.g., '1440x720').
            display: Display number.
            depth: Color depth (16 or 24).
            localhost: Only allow localhost connections.
        """
        if server:
            self._vnc_config.server = server
        if resolution:
            self._vnc_config.resolution = resolution
        if display is not None:
            self._vnc_config.display = display
        if depth:
            self._vnc_config.depth = depth
        if localhost is not None:
            self._vnc_config.localhost = localhost
        
        # Save to config
        self.config.vnc_server = self._vnc_config.server
        self.config.vnc_resolution = self._vnc_config.resolution
        self.config.vnc_display = self._vnc_config.display
        self.config.vnc_depth = self._vnc_config.depth
        self.config.vnc_localhost = self._vnc_config.localhost
        self.config.save()
