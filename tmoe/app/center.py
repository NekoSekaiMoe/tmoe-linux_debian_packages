"""Application center for TMOE.

Manages installation of applications across different Linux distributions.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

from tmoe.core.config import get_config
from tmoe.core.platform import PlatformInfo

if TYPE_CHECKING:
    from collections.abc import Sequence


class AppCategory(Enum):
    """Application categories."""
    BROWSER = auto()
    OFFICE = auto()
    DEVELOPMENT = auto()
    MULTIMEDIA = auto()
    GAME = auto()
    SOCIAL = auto()
    UTILITY = auto()


@dataclass
class Application:
    """Application definition."""
    name: str
    category: AppCategory
    description: str
    packages: dict[str, list[str]]  # distro -> packages
    electron: bool = False
    external_url: str | None = None


class AppCenter:
    """Application center for installing software.
    
    Provides a unified interface for installing applications
    across different Linux distributions.
    
    Example:
        >>> center = AppCenter()
        >>> await center.install_browser("firefox")
    """
    
    # Application definitions
    APPLICATIONS: dict[str, Application] = {
        # Browsers
        "firefox": Application(
            name="Firefox",
            category=AppCategory.BROWSER,
            description="Mozilla Firefox web browser",
            packages={
                "debian": ["firefox", "firefox-l10n-zh-cn"],
                "ubuntu": ["firefox"],
                "arch": ["firefox"],
                "fedora": ["firefox"],
                "alpine": ["firefox"],
            },
        ),
        "chromium": Application(
            name="Chromium",
            category=AppCategory.BROWSER,
            description="Open source Chrome browser",
            packages={
                "debian": ["chromium", "chromium-l10n"],
                "ubuntu": ["chromium-browser"],
                "arch": ["chromium"],
                "fedora": ["chromium"],
                "alpine": ["chromium"],
            },
        ),
        "edge": Application(
            name="Microsoft Edge",
            category=AppCategory.BROWSER,
            description="Microsoft Edge browser",
            packages={
                "debian": ["microsoft-edge-stable"],
                "ubuntu": ["microsoft-edge-stable"],
            },
            external_url="https://packages.microsoft.com/repos/edge",
        ),
        
        # Office
        "libreoffice": Application(
            name="LibreOffice",
            category=AppCategory.OFFICE,
            description="Open source office suite",
            packages={
                "debian": ["libreoffice", "libreoffice-l10n-zh-cn"],
                "ubuntu": ["libreoffice"],
                "arch": ["libreoffice-fresh"],
                "fedora": ["libreoffice"],
            },
        ),
        
        # Development
        "vscode": Application(
            name="VS Code",
            category=AppCategory.DEVELOPMENT,
            description="Visual Studio Code editor",
            packages={
                "debian": ["code"],
                "ubuntu": ["code"],
                "arch": ["visual-studio-code-bin"],
                "fedora": ["code"],
            },
            external_url="https://packages.microsoft.com/repos/code",
        ),
        "vim": Application(
            name="Vim",
            category=AppCategory.DEVELOPMENT,
            description="Vi IMproved text editor",
            packages={
                "debian": ["vim"],
                "ubuntu": ["vim"],
                "arch": ["vim"],
                "fedora": ["vim-enhanced"],
                "alpine": ["vim"],
            },
        ),
        "git": Application(
            name="Git",
            category=AppCategory.DEVELOPMENT,
            description="Distributed version control system",
            packages={
                "debian": ["git"],
                "ubuntu": ["git"],
                "arch": ["git"],
                "fedora": ["git"],
                "alpine": ["git"],
            },
        ),
        
        # Multimedia
        "mpv": Application(
            name="MPV",
            category=AppCategory.MULTIMEDIA,
            description="Command line video player",
            packages={
                "debian": ["mpv"],
                "ubuntu": ["mpv"],
                "arch": ["mpv"],
                "fedora": ["mpv"],
                "alpine": ["mpv"],
            },
        ),
        "gimp": Application(
            name="GIMP",
            category=AppCategory.MULTIMEDIA,
            description="GNU Image Manipulation Program",
            packages={
                "debian": ["gimp"],
                "ubuntu": ["gimp"],
                "arch": ["gimp"],
                "fedora": ["gimp"],
            },
        ),
    }
    
    def __init__(self, platform: PlatformInfo | None = None) -> None:
        self.platform = platform or PlatformInfo()
        self.config = get_config()
    
    def get_apps_by_category(self, category: AppCategory) -> list[Application]:
        """Get applications by category."""
        return [
            app for app in self.APPLICATIONS.values()
            if app.category == category
        ]
    
    def get_app(self, name: str) -> Application | None:
        """Get application by name."""
        return self.APPLICATIONS.get(name)
    
    async def install(
        self,
        app_name: str,
        distro: str | None = None,
    ) -> bool:
        """Install an application.
        
        Args:
            app_name: Application name.
            distro: Target distribution (auto-detected if None).
            
        Returns:
            True if installation succeeded.
        """
        app = self.get_app(app_name)
        if not app:
            raise ValueError(f"Unknown application: {app_name}")
        
        distro = distro or self._detect_distro()
        packages = app.packages.get(distro)
        
        if not packages:
            raise RuntimeError(f"Application '{app_name}' not available for {distro}")
        
        # Install using package manager
        return await self._install_packages(distro, packages)
    
    async def install_browser(self, browser: str) -> bool:
        """Install a web browser."""
        return await self.install(browser)
    
    async def install_office(self, office: str = "libreoffice") -> bool:
        """Install an office suite."""
        return await self.install(office)
    
    async def install_dev_tool(self, tool: str) -> bool:
        """Install a development tool."""
        return await self.install(tool)
    
    def _detect_distro(self) -> str:
        """Detect the current Linux distribution."""
        # Try to detect from /etc/os-release
        try:
            with open("/etc/os-release") as f:
                content = f.read().lower()
                if "debian" in content:
                    return "debian"
                elif "ubuntu" in content:
                    return "ubuntu"
                elif "arch" in content:
                    return "arch"
                elif "fedora" in content:
                    return "fedora"
                elif "alpine" in content:
                    return "alpine"
        except Exception:
            pass
        
        # Default to debian
        return "debian"
    
    async def _install_packages(self, distro: str, packages: list[str]) -> bool:
        """Install packages using the appropriate package manager."""
        cmd = self._get_install_command(distro, packages)
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            error = stderr.decode("utf-8", errors="replace")
            raise RuntimeError(f"Installation failed: {error}")
        
        return True
    
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
