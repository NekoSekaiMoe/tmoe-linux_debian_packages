"""Desktop environment installation for TMOE.

Installs and configures GUI desktop environments.
完全复刻原版 TMOE 的桌面环境安装逻辑。
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

from tmoe.core.config import get_config
from tmoe.core.platform import PlatformInfo

if TYPE_CHECKING:
    from tmoe.container.base import ContainerBackend


class DesktopEnvironment(Enum):
    """Supported desktop environments (原版支持)."""
    XFCE = ("xfce", "XFCE", "轻量级桌面，适合低配置")
    LXDE = ("lxde", "LXDE", "超轻量级桌面")
    LXQT = ("lxqt", "LXQt", "现代轻量级桌面")
    MATE = ("mate", "MATE", "传统 GNOME 2 风格")
    KDE = ("kde", "KDE Plasma", "现代美观的桌面")
    GNOME = ("gnome", "GNOME", "现代化桌面环境")
    CINNAMON = ("cinnamon", "Cinnamon", "Linux Mint 默认桌面")
    BUDGIE = ("budgie", "Budgie", "Solus 桌面环境")
    DEEPIN = ("deepin", "Deepin", "深度桌面环境")
    UKUI = ("ukui", "UKUI", "Ubuntu Kylin 桌面")
    CUTEFISH = ("cutefish", "Cutefish", "Cutefish 桌面")
    
    def __init__(self, id: str, display_name: str, description: str) -> None:
        self.id = id
        self.display_name = display_name
        self.description = description


@dataclass
class DesktopPackage:
    """Desktop environment package info."""
    name: str
    packages: dict[str, list[str]]  # distro -> packages
    session_name: str  # REMOTE_DESKTOP_SESSION_01
    start_command: str  # REMOTE_DESKTOP_SESSION_02
    
    def __post_init__(self) -> None:
        pass


# 原版桌面环境包定义
DESKTOP_PACKAGES: dict[DesktopEnvironment, DesktopPackage] = {
    DesktopEnvironment.XFCE: DesktopPackage(
        name="XFCE",
        packages={
            "debian": ["xfce4", "xfce4-goodies", "xfce4-terminal"],
            "ubuntu": ["xfce4", "xfce4-goodies", "xfce4-terminal"],
            "linuxmint": ["mint-meta-xfce", "mint-meta-core", "mint-artwork"],
            "arch": ["xfce4", "xfce4-terminal", "xfce4-goodies"],
            "fedora": ["@xfce", "xfce*-plugin", "xfce4-panel-profiles"],
            "alpine": ["faenza-icon-theme", "xfce4-whiskermenu-plugin", "xfce4", "xfce4-terminal"],
            "void": ["xfce4"],
            "gentoo": ["xfce4-meta", "x11-terms/xfce4-terminal"],
            "opensuse": ["patterns-xfce-xfce", "xfce4-terminal"],
        },
        session_name="xfce4-session",
        start_command="startxfce4",
    ),
    DesktopEnvironment.LXDE: DesktopPackage(
        name="LXDE",
        packages={
            "debian": ["lxde", "lxde-core", "lxterminal"],
            "ubuntu": ["lxde", "lxde-core", "lxterminal"],
            "arch": ["lxde"],
            "fedora": ["@lxde-desktop"],
            "alpine": ["lxde"],
        },
        session_name="LXDE",
        start_command="startlxde",
    ),
    DesktopEnvironment.LXQT: DesktopPackage(
        name="LXQt",
        packages={
            "debian": ["lxqt", "lxqt-core", "qterminal"],
            "ubuntu": ["lxqt", "lxqt-core", "qterminal"],
            "arch": ["lxqt"],
            "fedora": ["@lxqt-desktop"],
            "alpine": ["lxqt"],
        },
        session_name="lxqt-session",
        start_command="startlxqt",
    ),
    DesktopEnvironment.MATE: DesktopPackage(
        name="MATE",
        packages={
            "debian": ["mate-desktop", "mate-core", "mate-terminal"],
            "ubuntu": ["mate-desktop", "mate-core", "mate-terminal"],
            "arch": ["mate", "mate-extra"],
            "fedora": ["@mate-desktop"],
            "alpine": ["mate"],
        },
        session_name="mate-session",
        start_command="mate-session",
    ),
    DesktopEnvironment.KDE: DesktopPackage(
        name="KDE Plasma",
        packages={
            "debian": ["task-kde-desktop", "konsole"],
            "ubuntu": ["kubuntu-desktop", "konsole"],
            "arch": ["plasma", "kde-applications", "konsole"],
            "fedora": ["@kde-desktop", "konsole"],
            "alpine": ["plasma", "konsole"],
        },
        session_name="plasma-session",
        start_command="startplasma-x11",
    ),
    DesktopEnvironment.GNOME: DesktopPackage(
        name="GNOME",
        packages={
            "debian": ["task-gnome-desktop", "gnome-terminal"],
            "ubuntu": ["ubuntu-desktop", "gnome-terminal"],
            "arch": ["gnome", "gnome-extra", "gnome-terminal"],
            "fedora": ["@gnome-desktop", "gnome-terminal"],
            "alpine": ["gnome", "gnome-terminal"],
        },
        session_name="gnome-session",
        start_command="gnome-session",
    ),
    DesktopEnvironment.CINNAMON: DesktopPackage(
        name="Cinnamon",
        packages={
            "debian": ["task-cinnamon-desktop", "gnome-terminal"],
            "ubuntu": ["cinnamon-desktop-environment", "gnome-terminal"],
            "arch": ["cinnamon", "gnome-terminal"],
            "fedora": ["@cinnamon-desktop", "gnome-terminal"],
        },
        session_name="cinnamon-session",
        start_command="cinnamon-session",
    ),
    DesktopEnvironment.BUDGIE: DesktopPackage(
        name="Budgie",
        packages={
            "debian": ["task-budgie-desktop", "gnome-terminal"],
            "ubuntu": ["ubuntu-budgie-desktop", "gnome-terminal"],
            "arch": ["budgie-desktop", "gnome-terminal"],
            "fedora": ["@budgie-desktop", "gnome-terminal"],
        },
        session_name="budgie-session",
        start_command="budgie-session",
    ),
    DesktopEnvironment.DEEPIN: DesktopPackage(
        name="Deepin",
        packages={
            "debian": ["deepin-desktop", "deepin-terminal"],
            "ubuntu": ["deepin-desktop", "deepin-terminal"],
            "arch": ["deepin", "deepin-extra", "deepin-terminal"],
        },
        session_name="deepin-session",
        start_command="startdde",
    ),
    DesktopEnvironment.UKUI: DesktopPackage(
        name="UKUI",
        packages={
            "debian": ["ukui-desktop-environment", "ukui-terminal"],
            "ubuntu": ["ukui-desktop-environment", "ukui-terminal"],
        },
        session_name="ukui-session",
        start_command="ukui-session",
    ),
}


class DesktopInstaller:
    """Installer for desktop environments.
    
    完全复刻原版 TMOE 的桌面环境安装逻辑，包括：
    - 包安装
    - 主题、图标、光标安装
    - xfce4 面板配置
    - 壁纸设置
    - 字体安装
    - VNC 启动脚本创建
    - 输入法配置
    """
    
    # 原版主题和图标包
    THEME_PACKAGES: dict[str, list[str]] = {
        "debian": [
            "fonts-noto",
            "fonts-noto-cjk",
            "breeze-cursor-theme",
            "papirus-icon-theme",
        ],
        "ubuntu": [
            "fonts-noto",
            "fonts-noto-cjk",
            "breeze-cursor-theme",
            "papirus-icon-theme",
        ],
        "arch": [
            "noto-fonts",
            "noto-fonts-cjk",
            "breeze",
            "papirus-icon-theme",
        ],
        "fedora": [
            "google-noto-sans-cjk-fonts",
            "breeze-cursor-theme",
            "papirus-icon-theme",
        ],
    }
    
    # 输入法包
    IME_PACKAGES: dict[str, list[str]] = {
        "debian": ["fcitx5", "fcitx5-chinese-addons", "fcitx5-frontend-gtk4"],
        "ubuntu": ["fcitx", "fcitx-config-gtk", "fcitx-frontend-gtk4"],
        "arch": ["fcitx5", "fcitx5-chinese-addons", "fcitx5-gtk"],
        "fedora": ["fcitx5", "fcitx5-chinese-addons", "fcitx5-gtk"],
    }
    
    def __init__(self, backend: ContainerBackend | None = None) -> None:
        self.backend = backend
        self.platform = PlatformInfo()
    
    def get_supported_desktops(self, distro: str) -> list[DesktopEnvironment]:
        """Get supported desktop environments for distribution."""
        supported = []
        for desktop, package in DESKTOP_PACKAGES.items():
            # Check if any key matches the distro
            for key in package.packages.keys():
                if key in distro.lower() or distro.lower() in key:
                    supported.append(desktop)
                    break
        return supported
    
    async def install_desktop(
        self,
        desktop: DesktopEnvironment,
        distro: str | None = None,
        container_name: str | None = None,
        auto_install: bool = True,
    ) -> bool:
        """Install a desktop environment (原版安装逻辑).
        
        Args:
            desktop: Desktop environment to install
            distro: Distribution (auto-detected if None)
            container_name: Optional container name to install in
            auto_install: Whether to use auto-install mode (原版 AUTO_INSTALL_GUI)
            
        Returns:
            True if installation succeeded.
        """
        if distro is None:
            distro = self._detect_distro()
        
        package = DESKTOP_PACKAGES.get(desktop)
        if not package:
            raise ValueError(f"Unknown desktop: {desktop}")
        
        # Get packages for distro (原版逻辑：匹配最合适的包列表)
        packages = self._get_packages_for_distro(package, distro)
        if not packages:
            raise RuntimeError(f"Desktop {desktop.name} not available for {distro}")
        
        # 1. 安装桌面包 (原版 beta_features_quick_install / different_distro_software_install)
        self._log(f"Installing {desktop.name} desktop packages...")
        success = await self._install_packages(distro, packages, container_name)
        if not success:
            return False
        
        # 2. 安装主题和字体 (原版 git_clone_kali_themes_common, download_arch_breeze_adapta_cursor_theme)
        self._log("Installing themes and fonts...")
        await self._install_themes_and_fonts(distro, container_name)
        
        # 3. 安装输入法 (原版 do_you_want_to_install_fcitx4)
        if not auto_install:
            self._log("Installing input method...")
            await self._install_input_method(distro, container_name)
        
        # 4. 配置桌面环境 (原版 debian_xfce4_extras, auto_configure_xfce4_panel 等)
        if desktop == DesktopEnvironment.XFCE:
            await self._configure_xfce4(container_name)
        
        # 5. 配置 VNC xstartup (原版 configure_vnc_xstartup)
        self._log("Configuring VNC xstartup...")
        await self._configure_vnc_xstartup(desktop, container_name)
        
        # 6. 在 proot 环境中移除不必要的包 (原版 xfce4-power-manager 移除)
        if self.platform.is_android or container_name:
            await self._remove_unnecessary_packages(distro, desktop, container_name)
        
        return True
    
    def _get_packages_for_distro(self, package: DesktopPackage, distro: str) -> list[str]:
        """Get packages for a specific distribution (原版逻辑)."""
        distro_lower = distro.lower()
        
        # 精确匹配
        if distro_lower in package.packages:
            return package.packages[distro_lower]
        
        # 模糊匹配
        for key, pkgs in package.packages.items():
            if key in distro_lower or distro_lower in key:
                return pkgs
        
        # 默认使用 debian 包列表
        return package.packages.get("debian", [])
    
    async def _install_themes_and_fonts(self, distro: str, container_name: str | None) -> None:
        """Install themes and fonts (原版主题安装逻辑)."""
        theme_packages = self.THEME_PACKAGES.get(distro, self.THEME_PACKAGES["debian"])
        await self._install_packages(distro, theme_packages, container_name)
    
    async def _install_input_method(self, distro: str, container_name: str | None) -> None:
        """Install input method (原版 fcitx 安装逻辑)."""
        ime_packages = self.IME_PACKAGES.get(distro, self.IME_PACKAGES["debian"])
        await self._install_packages(distro, ime_packages, container_name)
    
    async def _configure_xfce4(self, container_name: str | None) -> None:
        """Configure XFCE4 (原版 xfce4 配置逻辑)."""
        home_dir = "/root"  # 默认 root 用户
        
        # 创建 xfce4 配置目录
        config_dir = f"{home_dir}/.config/xfce4/xfconf/xfce-perchannel-xml"
        
        if container_name and self.backend:
            # 在容器中执行
            await self.backend.exec(container_name, ["mkdir", "-p", config_dir])
        else:
            Path(config_dir).mkdir(parents=True, exist_ok=True)
        
        # 设置光标主题 (原版 Breeze-Adapta-Cursor)
        cursor_theme_cmd = [
            "dbus-launch", "xfconf-query", "-c", "xsettings",
            "-t", "string", "-np", "/Gtk/CursorThemeName", "-s", "Breeze-Adapta-Cursor"
        ]
        
        # 设置图标主题 (原版 Flat-Remix-Blue-Light 或 Papirus)
        icon_theme_cmd = [
            "dbus-launch", "xfconf-query", "-c", "xsettings",
            "-np", "/Net/IconThemeName", "-s", "Flat-Remix-Blue-Light"
        ]
        
        # 设置工作区数量 (原版 workspace_count = 2)
        workspace_cmd = [
            "dbus-launch", "xfconf-query", "-c", "xfwm4",
            "-t", "int", "-np", "/general/workspace_count", "-s", "2"
        ]
        
        if container_name and self.backend:
            await self.backend.exec(container_name, cursor_theme_cmd)
            await self.backend.exec(container_name, icon_theme_cmd)
            await self.backend.exec(container_name, workspace_cmd)
        else:
            # 在宿主机上执行
            for cmd in [cursor_theme_cmd, icon_theme_cmd, workspace_cmd]:
                try:
                    await asyncio.create_subprocess_exec(*cmd)
                except Exception:
                    pass
    
    async def _configure_vnc_xstartup(
        self,
        desktop: DesktopEnvironment,
        container_name: str | None,
    ) -> None:
        """Configure VNC xstartup script (原版 configure_vnc_xstartup)."""
        package = DESKTOP_PACKAGES.get(desktop)
        if not package:
            return
        
        home_dir = "/root"
        vnc_dir = f"{home_dir}/.vnc"
        xstartup_path = f"{vnc_dir}/xstartup"
        
        # 创建 VNC 目录
        if container_name and self.backend:
            await self.backend.exec(container_name, ["mkdir", "-p", vnc_dir])
        else:
            Path(vnc_dir).mkdir(parents=True, exist_ok=True)
        
        # 创建 xstartup 脚本 (原版格式)
        xstartup_content = f'''#!/bin/bash
# TMOE VNC Xstartup Script
# Generated automatically - do not edit manually

unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS

# Start dbus
if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
    eval $(dbus-launch --sh-syntax --exit-with-session)
fi

# Input method
export GTK_IM_MODULE=fcitx
export QT_IM_MODULE=fcitx
export XMODIFIERS=@im=fcitx

# Start desktop session
exec {package.start_command}
'''
        
        # 写入脚本
        if container_name and self.backend:
            # 在容器中写入
            await self._write_file_in_container(
                container_name, xstartup_path, xstartup_content, mode=0o755
            )
        else:
            # 在宿主机上写入
            Path(xstartup_path).write_text(xstartup_content)
            Path(xstartup_path).chmod(0o755)
    
    async def _remove_unnecessary_packages(
        self,
        distro: str,
        desktop: DesktopEnvironment,
        container_name: str | None,
    ) -> None:
        """Remove unnecessary packages for proot (原版 proot 包移除逻辑)."""
        if desktop != DesktopEnvironment.XFCE:
            return
        
        # 在 proot 中移除 xfce4-power-manager
        packages_to_remove = ["xfce4-power-manager"]
        
        if distro in ["debian", "ubuntu"]:
            cmd = ["apt", "autoremove", "--purge", "-y"] + packages_to_remove
        elif distro == "arch":
            cmd = ["pacman", "-Rsc", "--noconfirm"] + packages_to_remove
        elif distro == "fedora":
            cmd = ["dnf", "remove", "-y"] + packages_to_remove
        else:
            return
        
        await self._install_packages(distro, cmd, container_name)
    
    async def _install_packages(
        self,
        distro: str,
        packages: list[str],
        container_name: str | None,
    ) -> bool:
        """Install packages (原版安装命令)."""
        cmd = self._get_install_command(distro, packages)
        
        if container_name and self.backend:
            # 在容器中安装
            exit_code, stdout, stderr = await self.backend.exec(container_name, cmd)
            return exit_code == 0
        else:
            # 在宿主机上安装
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            return proc.returncode == 0
    
    def _get_install_command(self, distro: str, packages: list[str]) -> list[str]:
        """Get package install command (原版命令)."""
        distro_lower = distro.lower()
        
        if distro_lower in ["debian", "ubuntu", "linuxmint"]:
            return ["apt", "install", "-y"] + packages
        elif distro_lower in ["arch", "manjaro"]:
            return ["pacman", "-S", "--noconfirm"] + packages
        elif distro_lower in ["fedora", "centos", "rhel"]:
            return ["dnf", "install", "-y"] + packages
        elif distro_lower == "alpine":
            return ["apk", "add"] + packages
        elif distro_lower == "opensuse":
            return ["zypper", "install", "-y"] + packages
        elif distro_lower == "void":
            return ["xbps-install", "-y"] + packages
        elif distro_lower == "gentoo":
            return ["emerge"] + packages
        else:
            return ["apt", "install", "-y"] + packages
    
    async def _write_file_in_container(
        self,
        container_name: str,
        path: str,
        content: str,
        mode: int = 0o644,
    ) -> None:
        """Write file in container using tee command."""
        if not self.backend:
            return
        
        # 使用 echo 和 tee 写入文件
        encoded_content = content.replace("'", "'\"'\"'")
        cmd = ["sh", "-c", f"echo '{encoded_content}' | tee {path}"]
        await self.backend.exec(container_name, cmd)
        
        # 设置权限
        await self.backend.exec(container_name, ["chmod", oct(mode)[2:], path])
    
    def _detect_distro(self) -> str:
        """Detect Linux distribution."""
        os_release = Path("/etc/os-release")
        if os_release.exists():
            content = os_release.read_text()
            for line in content.split("\n"):
                if line.startswith("ID="):
                    return line.split("=", 1)[1].strip('"').lower()
        
        if Path("/etc/arch-release").exists():
            return "arch"
        elif Path("/etc/fedora-release").exists():
            return "fedora"
        elif Path("/etc/debian_version").exists():
            return "debian"
        
        return "debian"
    
    def _log(self, message: str) -> None:
        """Log message."""
        print(f"[DesktopInstaller] {message}")
    
    async def setup_vnc_startup(
        self,
        desktop: DesktopEnvironment,
        user: str = "root",
        container_name: str | None = None,
    ) -> None:
        """Setup VNC startup script (原版 configure_vnc_xstartup)."""
        await self._configure_vnc_xstartup(desktop, container_name)


class DesktopManager:
    """Desktop environment manager for use without ContainerBackend."""
    
    def __init__(self) -> None:
        self.platform = PlatformInfo()
        self.installer = DesktopInstaller()
    
    async def install_desktop(
        self,
        desktop_name: str,
        container_name: str | None = None,
    ) -> bool:
        """Install desktop environment by name."""
        # Map name to enum
        desktop_map = {
            "xfce": DesktopEnvironment.XFCE,
            "lxde": DesktopEnvironment.LXDE,
            "lxqt": DesktopEnvironment.LXQT,
            "mate": DesktopEnvironment.MATE,
            "kde": DesktopEnvironment.KDE,
            "plasma": DesktopEnvironment.KDE,
            "gnome": DesktopEnvironment.GNOME,
            "cinnamon": DesktopEnvironment.CINNAMON,
            "budgie": DesktopEnvironment.BUDGIE,
            "deepin": DesktopEnvironment.DEEPIN,
            "ukui": DesktopEnvironment.UKUI,
            "cutefish": DesktopEnvironment.CUTEFISH,
        }
        
        desktop = desktop_map.get(desktop_name.lower())
        if not desktop:
            raise ValueError(f"Unknown desktop: {desktop_name}")
        
        return await self.installer.install_desktop(
            desktop,
            container_name=container_name,
        )
    
    def get_desktop_choices(self) -> list[tuple[str, str, str]]:
        """Get list of available desktop choices."""
        return [
            (de.id, de.display_name, de.description)
            for de in DesktopEnvironment
        ]