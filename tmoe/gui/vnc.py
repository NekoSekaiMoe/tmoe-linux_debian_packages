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
    """VNC configuration (原版配置项)."""
    server: str = "tiger"  # tiger or tight
    resolution: str = "1440x720"
    display: int = 2  # 显示编号，端口 = 5900 + display
    depth: int = 24  # 色彩深度: 16, 24, 32
    localhost: bool = False  # 仅允许本地连接
    password: str | None = None
    zlib_level: int = 0  # 压缩级别 0-9
    always_shared: bool = True  # 总是共享连接
    auto_start_dbus: bool = True  # 自动启动 dbus
    auto_stop_vnc: bool = True  # 启动前停止已有 VNC
    vnc_user: str | None = None  # VNC 运行用户
    desktop_name: str | None = None  # 桌面名称


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

    async def set_password(self, password: str) -> None:
        """Set VNC password (原版 vncpasswd 功能).
        
        Args:
            password: VNC password (max 8 characters for standard VNC)
        """
        # Create .vnc directory
        vnc_dir = Path.home() / ".vnc"
        vnc_dir.mkdir(parents=True, exist_ok=True)
        
        passwd_file = vnc_dir / "passwd"
        
        # Use vncpasswd command if available
        vncpasswd_bin = shutil.which("vncpasswd")
        if vncpasswd_bin:
            # Write password to stdin of vncpasswd
            proc = await asyncio.create_subprocess_exec(
                vncpasswd_bin,
                str(passwd_file),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            # Send password twice (for confirmation)
            input_data = f"{password}\n{password}\n".encode()
            await proc.communicate(input=input_data)
        else:
            # Fallback: store password in file (less secure, for demo only)
            # In production, should use proper VNC password encryption
            import base64
            encoded = base64.b64encode(password.encode()).decode()
            passwd_file.write_text(encoded)
            passwd_file.chmod(0o600)
        
        self._vnc_config.password = password
    
    def generate_start_script(
        self,
        container_name: str | None = None,
        desktop: str = "xfce",
    ) -> str:
        """Generate VNC startup script (原版 startvnc 脚本格式).
        
        Args:
            container_name: Optional container name for container-specific script
            desktop: Desktop environment to start
            
        Returns:
            Shell script content
        """
        display = self._vnc_config.display
        port = 5900 + display
        resolution = self._vnc_config.resolution
        depth = self._vnc_config.depth
        
        script = f'''#!/bin/bash
# TMOE VNC Startup Script
# Generated automatically - do not edit manually

# PulseAudio settings
export PULSE_SERVER=${{PULSE_SERVER:-127.0.0.1}}

# VNC configuration
VNC_RESOLUTION="{resolution}"
VNC_DISPLAY={display}
RFB_PORT={port}
VNC_USER=$(id -un)
VNC_LOCALHOST={'true' if self._vnc_config.localhost else 'false'}
VNC_SERVER={self._vnc_config.server}
ZLIB_LEVEL={self._vnc_config.zlib_level}
PIXEL_DEPTH={depth}
ALWAYS_SHARED={'true' if self._vnc_config.always_shared else 'false'}
AUTO_START_DBUS={'true' if self._vnc_config.auto_start_dbus else 'false'}
AUTO_STOP_VNC={'true' if self._vnc_config.auto_stop_vnc else 'false'}

# Display settings
unset WAYLAND_DISPLAY
export DISPLAY=:{display}

# VNC files
VNC_LOG_FILE=$HOME/.vnc/vnc.log
TMOE_VNC_PASSWD_FILE="$HOME/.vnc/passwd"
XSESSION_FILE="/etc/X11/xinit/Xsession"

# Colors for output
RED='\\033[31m'
GREEN='\\033[32m'
YELLOW='\\033[33m'
BLUE='\\033[34m'
RESET='\\033[m'

echo -e "${{GREEN}}Starting ${{YELLOW}}vnc server${{RESET}} ..."
echo -e "VNC port is ${{YELLOW}}${{RFB_PORT}}${{RESET}}, address is ${{GREEN}}localhost${{YELLOW}}:${{RFB_PORT}}${{RESET}}"

# Auto stop existing VNC
if [ "$AUTO_STOP_VNC" = "true" ]; then
    vncserver -kill :{display} 2>/dev/null || true
fi

# Start dbus if needed
if [ "$AUTO_START_DBUS" = "true" ]; then
    if command -v dbus-launch &> /dev/null; then
        eval $(dbus-launch --sh-syntax --exit-with-session)
    fi
fi

# Start VNC server
if [ "$VNC_SERVER" = "tiger" ]; then
    Xtigervnc :{display} \\
        -geometry "$VNC_RESOLUTION" \\
        -depth "$PIXEL_DEPTH" \\
        -ZlibLevel="$ZLIB_LEVEL" \\
        -pn \\
        {'-localhost yes' if self._vnc_config.localhost else '-localhost no'} \\
        -rfbauth "$TMOE_VNC_PASSWD_FILE" \\
        -desktop "tmoe_{desktop}_desktop" &
else
    tightvncserver :{display} \\
        -geometry "$VNC_RESOLUTION" \\
        -depth "$PIXEL_DEPTH" \\
        {'-localhost' if self._vnc_config.localhost else ''} &
fi

VNC_PID=$!
echo $VNC_PID > "$HOME/.vnc/{container_name or 'default'}_{display}.pid"

# Wait for VNC to start
sleep 2

# Start desktop session
if [ -f "$XSESSION_FILE" ]; then
    bash "$XSESSION_FILE" &
else
    # Fallback: try to start desktop directly
    case "{desktop}" in
        xfce) startxfce4 & ;;
        lxde) startlxde & ;;
        lxqt) startlxqt & ;;
        mate) mate-session & ;;
        kde|plasma) startplasma-x11 & ;;
        gnome) gnome-session & ;;
        cinnamon) cinnamon-session & ;;
    esac
fi

echo -e "${{GREEN}}VNC server started on port ${{YELLOW}}${{RFB_PORT}}${{RESET}}"
echo -e "Access with: vncviewer localhost:${{RFB_PORT}}"
'''
        return script
    
    async def install_vnc_server(self, server_type: str = "tiger") -> bool:
        """Install VNC server package.
        
        Args:
            server_type: 'tiger' or 'tight'
            
        Returns:
            True if installation succeeded
        """
        try:
            # Detect distribution
            distro = "debian"
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release") as f:
                    content = f.read().lower()
                    if "arch" in content:
                        distro = "arch"
                    elif "fedora" in content:
                        distro = "fedora"
                    elif "alpine" in content:
                        distro = "alpine"
            
            if server_type == "tiger":
                packages = ["tigervnc-standalone-server", "tigervnc-viewer"]
            else:
                packages = ["tightvncserver"]
            
            match distro:
                case "debian" | "ubuntu":
                    cmd = ["apt", "install", "-y"] + packages
                case "arch":
                    cmd = ["pacman", "-S", "--noconfirm", "tigervnc"]
                case "fedora":
                    cmd = ["dnf", "install", "-y", "tigervnc-server"]
                case "alpine":
                    cmd = ["apk", "add", "tigervnc"]
                case _:
                    return False
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            return proc.returncode == 0
            
        except Exception:
            return False
