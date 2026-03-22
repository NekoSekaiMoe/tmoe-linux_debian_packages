"""Desktop environment installation for TMOE.

Installs and configures GUI desktop environments.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tmoe.container.base import ContainerBackend


class DesktopEnvironment(Enum):
    """Supported desktop environments."""
    XFCE = ("xfce", "XFCE", "轻量级桌面，适合低配置")
    LXDE = ("lxde", "LXDE", "超轻量级桌面")
    LXQT = ("lxqt", "LXQt", "现代轻量级桌面")
    MATE = ("mate", "MATE", "传统 GNOME 2 风格")
    KDE = ("kde", "KDE Plasma", "现代美观的桌面")
    GNOME = ("gnome", "GNOME", "现代化桌面环境")
    CINNAMON = ("cinnamon", "Cinnamon", "Linux Mint 默认桌面")
    BUDGIE = ("budgie", "Budgie", "Solus 桌面环境")
    DEEPIN = ("deepin", "Deepin", "深度桌面环境")
    
    def __init__(self, id: str, display_name: str, description: str) -> None:
        self.id = id
        self.display_name = display_name
        self.description = description


@dataclass
class DesktopPackage:
    """Desktop environment package info."""
    name: str
    packages: dict[str, list[str]]  # distro -> packages
    recommends: dict[str, list[str]] = None
    
    def __post_init__(self) -> None:
        if self.recommends is None:
            self.recommends = {}


class DesktopInstaller:
    """Installer for desktop environments.
    
    Installs various desktop environments on containers.
    
    Example:
        >>> installer = DesktopInstaller(backend)
        >>> await installer.install_desktop(DesktopEnvironment.XFCE)
    """
    
    # Desktop environment package definitions
    DESKTOPS: dict[DesktopEnvironment, DesktopPackage] = {
        DesktopEnvironment.XFCE: DesktopPackage(
            name="XFCE",
            packages={
                "debian": ["task-xfce-desktop"],
                "ubuntu": ["xfce4", "xfce4-goodies"],
                "arch": ["xfce4", "xfce4-goodies"],
                "fedora": ["@xfce-desktop-environment"],
                "alpine": ["xfce4"],
            },
        ),
        DesktopEnvironment.LXDE: DesktopPackage(
            name="LXDE",
            packages={
                "debian": ["task-lxde-desktop"],
                "ubuntu": ["lxde", "lxde-common"],
                "arch": ["lxde"],
                "fedora": ["@lxde-desktop"],
                "alpine": ["lxde"],
            },
        ),
        DesktopEnvironment.LXQT: DesktopPackage(
            name="LXQt",
            packages={
                "debian": ["task-lxqt-desktop"],
                "ubuntu": ["lxqt", "lxqt-core"],
                "arch": ["lxqt"],
                "fedora": ["@lxqt-desktop"],
                "alpine": ["lxqt"],
            },
        ),
        DesktopEnvironment.MATE: DesktopPackage(
            name="MATE",
            packages={
                "debian": ["task-mate-desktop"],
                "ubuntu": ["mate-desktop", "mate-core"],
                "arch": ["mate", "mate-extra"],
                "fedora": ["@mate-desktop"],
                "alpine": ["mate"],
            },
        ),
        DesktopEnvironment.KDE: DesktopPackage(
            name="KDE Plasma",
            packages={
                "debian": ["task-kde-desktop"],
                "ubuntu": ["kubuntu-desktop"],
                "arch": ["plasma", "kde-applications"],
                "fedora": ["@kde-desktop"],
                "alpine": ["plasma"],
            },
        ),
        DesktopEnvironment.GNOME: DesktopPackage(
            name="GNOME",
            packages={
                "debian": ["task-gnome-desktop"],
                "ubuntu": ["ubuntu-desktop"],
                "arch": ["gnome", "gnome-extra"],
                "fedora": ["@gnome-desktop"],
                "alpine": ["gnome"],
            },
        ),
        DesktopEnvironment.CINNAMON: DesktopPackage(
            name="Cinnamon",
            packages={
                "debian": ["task-cinnamon-desktop"],
                "ubuntu": ["cinnamon-desktop-environment"],
                "arch": ["cinnamon"],
                "fedora": ["@cinnamon-desktop"],
                "alpine": [],
            },
        ),
        DesktopEnvironment.BUDGIE: DesktopPackage(
            name="Budgie",
            packages={
                "debian": ["task-budgie-desktop"],
                "ubuntu": ["ubuntu-budgie-desktop"],
                "arch": ["budgie-desktop"],
                "fedora": ["@budgie-desktop"],
                "alpine": [],
            },
        ),
    }
    
    # Additional packages for better experience
    COMMON_PACKAGES: dict[str, list[str]] = {
        "debian": [
            "xfonts-base",
            "xfonts-100dpi",
            "xfonts-75dpi",
            "fonts-noto",
            "fonts-noto-cjk",
            "fcitx5",
            "fcitx5-chinese-addons",
        ],
        "ubuntu": [
            "fonts-noto",
            "fonts-noto-cjk",
            "fcitx",
            "fcitx-config-gtk",
        ],
        "arch": [
            "noto-fonts",
            "noto-fonts-cjk",
            "fcitx5",
            "fcitx5-chinese-addons",
        ],
        "fedora": [
            "google-noto-sans-cjk-fonts",
            "fcitx5",
            "fcitx5-chinese-addons",
        ],
    }
    
    def __init__(self, backend: ContainerBackend) -> None:
        self.backend = backend
    
    def get_supported_desktops(self, distro: str) -> list[DesktopEnvironment]:
        """Get supported desktop environments for distribution.
        
        Args:
            distro: Distribution name
            
        Returns:
            List of supported desktop environments.
        """
        supported = []
        for desktop, package in self.DESKTOPS.items():
            if distro in package.packages and package.packages[distro]:
                supported.append(desktop)
        return supported
    
    async def install_desktop(
        self,
        desktop: DesktopEnvironment,
        distro: str | None = None,
    ) -> bool:
        """Install a desktop environment.
        
        Args:
            desktop: Desktop environment to install
            distro: Distribution (auto-detected if None)
            
        Returns:
            True if installation succeeded.
        """
        if distro is None:
            distro = self._detect_distro()
        
        package = self.DESKTOPS.get(desktop)
        if not package:
            raise ValueError(f"Unknown desktop: {desktop}")
        
        packages = package.packages.get(distro)
        if not packages:
            raise RuntimeError(f"Desktop {desktop.name} not available for {distro}")
        
        # Add common packages
        common = self.COMMON_PACKAGES.get(distro, [])
        all_packages = packages + common
        
        # Install packages
        return await self._install_packages(distro, all_packages)
    
    async def _install_packages(self, distro: str, packages: list[str]) -> bool:
        """Install packages using the appropriate package manager."""
        cmd = self._get_install_command(distro, packages)
        
        # Execute in container
        exit_code, stdout, stderr = await self.backend.exec(self.backend.name, cmd)
        
        return exit_code == 0
    
    def _get_install_command(self, distro: str, packages: list[str]) -> list[str]:
        """Get package install command for distribution."""
        match distro:
            case "debian" | "ubuntu":
                return ["apt", "install", "-y"] + packages
            case "arch":
                return ["pacman", "-S", "--noconfirm"] + packages
            case "fedora":
                return ["dnf", "install", "-y"] + packages
            case "alpine":
                return ["apk", "add"] + packages
            case _:
                return ["apt", "install", "-y"] + packages
    
    def _detect_distro(self) -> str:
        """Detect distribution in container."""
        # This would normally check /etc/os-release in the container
        return "debian"
    
    async def setup_vnc_startup(
        self,
        desktop: DesktopEnvironment,
        user: str = "root",
    ) -> None:
        """Setup VNC startup script for desktop.
        
        Creates a .vnc/xstartup script to launch the desktop.
        
        Args:
            desktop: Desktop environment
            user: User to configure for
        """
        home = f"/home/{user}" if user != "root" else "/root"
        vnc_dir = f"{home}/.vnc"
        xstartup = f"{vnc_dir}/xstartup"
        
        # Create VNC directory
        await self.backend.exec(
            self.backend.name,
            ["mkdir", "-p", vnc_dir]
        )
        
        # Create xstartup script
        startup_script = self._get_xstartup_script(desktop)
        
        # Write script
        await self.backend.exec(
            self.backend.name,
            ["tee", xstartup],
            input=startup_script.encode(),
        )
        
        # Make executable
        await self.backend.exec(
            self.backend.name,
            ["chmod", "+x", xstartup]
        )
    
    def _get_xstartup_script(self, desktop: DesktopEnvironment) -> str:
        """Generate xstartup script for desktop."""
        scripts = {
            DesktopEnvironment.XFCE: """#!/bin/bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
exec startxfce4
""",
            DesktopEnvironment.LXDE: """#!/bin/bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
exec startlxde
""",
            DesktopEnvironment.LXQT: """#!/bin/bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
exec startlxqt
""",
            DesktopEnvironment.MATE: """#!/bin/bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
exec mate-session
""",
            DesktopEnvironment.KDE: """#!/bin/bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
exec startplasma-x11
""",
            DesktopEnvironment.GNOME: """#!/bin/bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
exec gnome-session
""",
        }
        
        return scripts.get(desktop, scripts[DesktopEnvironment.XFCE])
