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
            # terminate() is a sync method on asyncio.subprocess.Process
            self._websockify_proc.terminate()
            try:
                await asyncio.wait_for(self._websockify_proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                # kill() is also a sync method
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

    def generate_start_script(
        self,
        container_name: str | None = None,
    ) -> str:
        """Generate noVNC startup script (原版 novnc 脚本格式).
        
        Args:
            container_name: Optional container name
            
        Returns:
            Shell script content
        """
        novnc_dir = self.novnc_dir
        websockify_dir = self.websockify_dir
        web_port = self.config.web_port
        vnc_port = self.config.vnc_port
        
        script = f'''#!/bin/bash
# TMOE noVNC Startup Script
# Generated automatically - do not edit manually

# Configuration
NOVNC_DIR="{novnc_dir}"
WEBSOCKIFY_DIR="{websockify_dir}"
NOVNC_PORT={web_port}
VNC_PORT={vnc_port}
NOVNC_ADDR="localhost:${{VNC_PORT}}"

# Colors
GREEN='\\033[32m'
YELLOW='\\033[33m'
BLUE='\\033[34m'
RESET='\\033[m'

# Check if noVNC is installed
if [ ! -d "$NOVNC_DIR" ]; then
    echo "Error: noVNC not found at $NOVNC_DIR"
    echo "Please install noVNC first"
    exit 1
fi

# Check for websockify
if command -v websockify &> /dev/null; then
    WEBSOCKIFY_CMD="websockify"
elif [ -f "$WEBSOCKIFY_DIR/websockify.py" ]; then
    WEBSOCKIFY_CMD="python3 $WEBSOCKIFY_DIR/websockify.py"
else
    echo "Error: websockify not found"
    exit 1
fi

# Get current VNC port (in case VNC is running)
CURRENT_VNC_PORT=${{VNC_PORT}}
if [ -f "$HOME/.vnc/*:1.pid" ]; then
    # Try to detect actual VNC port
    for i in 1 2 3 4 5; do
        if [ -f "$HOME/.vnc/*:${{i}}.pid" ]; then
            CURRENT_VNC_PORT=$((5900 + i))
            break
        fi
    done
fi

echo -e "${{GREEN}}Starting noVNC...${{RESET}}"
echo -e "VNC backend: ${{YELLOW}}localhost:${{CURRENT_VNC_PORT}}${{RESET}}"
echo -e "Web interface: ${{BLUE}}http://localhost:${{NOVNC_PORT}}/vnc.html${{RESET}}"

# Kill existing websockify
pkill -f "websockify.*${{NOVNC_PORT}}" 2>/dev/null || true

# Start websockify
$WEBSOCKIFY_CMD \\
    --web "$NOVNC_DIR" \\
    --cert "$HOME/.vnc/self.pem" \\
    "$NOVNC_PORT" \\
    "localhost:${{CURRENT_VNC_PORT}}" &

WEBSOCKIFY_PID=$!
echo $WEBSOCKIFY_PID > "$HOME/.vnc/novnc_{container_name or 'default'}.pid"

sleep 2

echo -e "${{GREEN}}noVNC started!${{RESET}}"
echo -e "Access URL: ${{BLUE}}http://localhost:${{NOVNC_PORT}}/vnc.html${{RESET}}"
echo -e "Or: ${{BLUE}}http://localhost:${{NOVNC_PORT}}/vnc.html?host=localhost&port=${{NOVNC_PORT}}${{RESET}}"
'''
        return script
