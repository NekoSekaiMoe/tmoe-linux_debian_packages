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
    """Application categories (原版软件中心分类)."""
    BROWSER = auto()      # 浏览器
    OFFICE = auto()       # 办公
    DEVELOPMENT = auto()  # 开发工具
    MULTIMEDIA = auto()   # 多媒体
    GAME = auto()         # 游戏
    SOCIAL = auto()       # 社交
    UTILITY = auto()      # 工具


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
    
    # Application definitions (原版软件中心完整列表)
    APPLICATIONS: dict[str, Application] = {
        # ===== BROWSERS (原版支持) =====
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
        
        # ===== OFFICE (原版支持) =====
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
        "wps": Application(
            name="WPS Office",
            category=AppCategory.OFFICE,
            description="WPS Office suite",
            packages={
                "debian": ["wps-office"],
                "ubuntu": ["wps-office"],
                "arch": ["wps-office"],
            },
            external_url="https://linux.wps.cn",
        ),
        
        # ===== DEVELOPMENT (原版支持IDE、编辑器、数据库等) =====
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
        "pycharm": Application(
            name="PyCharm",
            category=AppCategory.DEVELOPMENT,
            description="Python IDE by JetBrains",
            packages={
                "debian": ["pycharm-community"],
                "ubuntu": ["pycharm-community"],
                "arch": ["pycharm-community-edition"],
                "fedora": ["pycharm-community"],
            },
        ),
        "idea": Application(
            name="IntelliJ IDEA",
            category=AppCategory.DEVELOPMENT,
            description="Java IDE by JetBrains",
            packages={
                "debian": ["intellij-idea-community"],
                "ubuntu": ["intellij-idea-community"],
                "arch": ["intellij-idea-community-edition"],
                "fedora": ["intellij-idea-community"],
            },
        ),
        "android_studio": Application(
            name="Android Studio",
            category=AppCategory.DEVELOPMENT,
            description="Android development IDE",
            packages={
                "debian": ["android-studio"],
                "ubuntu": ["android-studio"],
                "arch": ["android-studio"],
                "fedora": ["android-studio"],
            },
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
        "neovim": Application(
            name="Neovim",
            category=AppCategory.DEVELOPMENT,
            description="Hyperextensible Vim-based text editor",
            packages={
                "debian": ["neovim"],
                "ubuntu": ["neovim"],
                "arch": ["neovim"],
                "fedora": ["neovim"],
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
        "docker": Application(
            name="Docker",
            category=AppCategory.DEVELOPMENT,
            description="Container platform",
            packages={
                "debian": ["docker.io"],
                "ubuntu": ["docker.io"],
                "arch": ["docker"],
                "fedora": ["docker"],
            },
        ),
        "nodejs": Application(
            name="Node.js",
            category=AppCategory.DEVELOPMENT,
            description="JavaScript runtime",
            packages={
                "debian": ["nodejs", "npm"],
                "ubuntu": ["nodejs", "npm"],
                "arch": ["nodejs", "npm"],
                "fedora": ["nodejs", "npm"],
            },
        ),
        "python3": Application(
            name="Python 3",
            category=AppCategory.DEVELOPMENT,
            description="Python programming language",
            packages={
                "debian": ["python3", "python3-pip"],
                "ubuntu": ["python3", "python3-pip"],
                "arch": ["python", "python-pip"],
                "fedora": ["python3", "python3-pip"],
            },
        ),
        
        # ===== MULTIMEDIA (原版支持) =====
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
        "vlc": Application(
            name="VLC",
            category=AppCategory.MULTIMEDIA,
            description="Popular media player",
            packages={
                "debian": ["vlc"],
                "ubuntu": ["vlc"],
                "arch": ["vlc"],
                "fedora": ["vlc"],
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
        "audacity": Application(
            name="Audacity",
            category=AppCategory.MULTIMEDIA,
            description="Audio editor",
            packages={
                "debian": ["audacity"],
                "ubuntu": ["audacity"],
                "arch": ["audacity"],
                "fedora": ["audacity"],
            },
        ),
        "spotify": Application(
            name="Spotify",
            category=AppCategory.MULTIMEDIA,
            description="Music streaming service",
            packages={
                "debian": ["spotify-client"],
                "ubuntu": ["spotify-client"],
                "arch": ["spotify"],
                "fedora": ["spotify-client"],
            },
        ),
        "clementine": Application(
            name="Clementine",
            category=AppCategory.MULTIMEDIA,
            description="Music player",
            packages={
                "debian": ["clementine"],
                "ubuntu": ["clementine"],
                "arch": ["clementine"],
                "fedora": ["clementine"],
            },
        ),
        
        # ===== SOCIAL (原版支持QQ、微信等) =====
        "linuxqq": Application(
            name="Linux QQ",
            category=AppCategory.SOCIAL,
            description="QQ for Linux",
            packages={
                "debian": ["linuxqq"],
                "ubuntu": ["linuxqq"],
                "arch": ["linuxqq"],
            },
            external_url="https://im.qq.com/linuxqq",
        ),
        "wechat": Application(
            name="WeChat",
            category=AppCategory.SOCIAL,
            description="WeChat for Linux (Electronic WeChat)",
            packages={
                "debian": ["electronic-wechat"],
                "ubuntu": ["electronic-wechat"],
                "arch": ["electronic-wechat"],
            },
        ),
        "skype": Application(
            name="Skype",
            category=AppCategory.SOCIAL,
            description="Video chat and messaging",
            packages={
                "debian": ["skypeforlinux"],
                "ubuntu": ["skypeforlinux"],
                "arch": ["skypeforlinux-stable-bin"],
                "fedora": ["skypeforlinux"],
            },
        ),
        "thunderbird": Application(
            name="Thunderbird",
            category=AppCategory.SOCIAL,
            description="Email client",
            packages={
                "debian": ["thunderbird"],
                "ubuntu": ["thunderbird"],
                "arch": ["thunderbird"],
                "fedora": ["thunderbird"],
            },
        ),
        
        # ===== GAMES (原版支持Steam等) =====
        "steam": Application(
            name="Steam",
            category=AppCategory.GAME,
            description="Game distribution platform",
            packages={
                "debian": ["steam"],
                "ubuntu": ["steam"],
                "arch": ["steam"],
                "fedora": ["steam"],
            },
        ),
        "kdegames": Application(
            name="KDE Games",
            category=AppCategory.GAME,
            description="Collection of KDE games",
            packages={
                "debian": ["kdegames"],
                "ubuntu": ["kdegames"],
                "arch": ["kde-applications-meta"],
                "fedora": ["kdegames"],
            },
        ),
        "retroarch": Application(
            name="RetroArch",
            category=AppCategory.GAME,
            description="Game emulator frontend",
            packages={
                "debian": ["retroarch"],
                "ubuntu": ["retroarch"],
                "arch": ["retroarch"],
                "fedora": ["retroarch"],
            },
        ),
        
        # ===== UTILITIES (原版支持下载工具等) =====
        "aria2": Application(
            name="Aria2",
            category=AppCategory.UTILITY,
            description="Download utility",
            packages={
                "debian": ["aria2"],
                "ubuntu": ["aria2"],
                "arch": ["aria2"],
                "fedora": ["aria2"],
                "alpine": ["aria2"],
            },
        ),
        "baidunetdisk": Application(
            name="Baidu Netdisk",
            category=AppCategory.UTILITY,
            description="Baidu cloud storage",
            packages={
                "debian": ["baidunetdisk"],
                "ubuntu": ["baidunetdisk"],
                "arch": ["baidunetdisk"],
            },
        ),
        "synaptic": Application(
            name="Synaptic",
            category=AppCategory.UTILITY,
            description="Package manager GUI",
            packages={
                "debian": ["synaptic"],
                "ubuntu": ["synaptic"],
            },
        ),
        "bleachbit": Application(
            name="BleachBit",
            category=AppCategory.UTILITY,
            description="System cleaner",
            packages={
                "debian": ["bleachbit"],
                "ubuntu": ["bleachbit"],
                "arch": ["bleachbit"],
                "fedora": ["bleachbit"],
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
        container_name: str | None = None,
        backend = None,
    ) -> bool:
        """Install an application.
        
        Args:
            app_name: Application name.
            distro: Target distribution (auto-detected if None).
            container_name: Optional container name to install in.
            backend: Optional container backend for container installation.
            
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
        
        # Install using package manager (in container if specified)
        if container_name and backend and hasattr(backend, 'exec'):
            return await self._install_packages_in_container(
                distro, packages, container_name, backend
            )
        else:
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
    
    async def _install_packages_in_container(
        self,
        distro: str,
        packages: list[str],
        container_name: str,
        backend,
    ) -> bool:
        """Install packages inside a container.
        
        Args:
            distro: Distribution name
            packages: List of packages to install
            container_name: Container name
            backend: Container backend
            
        Returns:
            True if installation succeeded
        """
        cmd = self._get_install_command(distro, packages)
        
        # Execute in container
        exit_code, stdout, stderr = await backend.exec(container_name, cmd)
        
        if exit_code != 0:
            raise RuntimeError(f"Installation failed in container: {stderr}")
        
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
