"""Application installer screen."""

from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Label,
    ListItem,
    ListView,
    Log,
    Static,
    TabbedContent,
    TabPane,
)

from tmoe.app.center import AppCenter, AppCategory
from tmoe.core.config import get_config
from tmoe.core.platform import get_platform_info


class AppInstallerScreen(Screen):
    """Screen for installing applications."""
    
    BINDINGS = [
        Binding("escape", "back", "返回"),
        Binding("q", "back", "返回"),
        Binding("i", "install", "安装"),
    ]
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    .main-container {
        width: 100;
        height: 95%;
        border: thick $background 80%;
        padding: 1 2;
    }
    
    .title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    
    TabbedContent {
        height: 1fr;
        margin: 1 0;
    }
    
    .app-grid {
        grid-size: 2;
        grid-gutter: 1;
        padding: 1;
    }
    
    .app-button {
        width: 100%;
        height: 3;
        content-align: center middle;
    }
    
    .log-panel {
        height: 20%;
        border: solid $surface-lighten-1;
        padding: 0 1;
    }
    """
    
    def __init__(self) -> None:
        self.platform = get_platform_info()
        self.config = get_config()
        self.center = AppCenter()
        self.selected_app: str | None = None
        super().__init__()
    
    def compose(self) -> ComposeResult:
        with Container(classes="main-container"):
            yield Static("📦 应用中心", classes="title")
            
            # Tabbed content
            with TabbedContent():
                with TabPane("🌐 浏览器", id="tab_browser"):
                    with Grid(classes="app-grid"):
                        for btn in self._create_app_buttons(AppCategory.BROWSER):
                            yield btn
                
                with TabPane("📝 办公", id="tab_office"):
                    with Grid(classes="app-grid"):
                        for btn in self._create_app_buttons(AppCategory.OFFICE):
                            yield btn
                
                with TabPane("💻 开发", id="tab_dev"):
                    with Grid(classes="app-grid"):
                        for btn in self._create_app_buttons(AppCategory.DEVELOPMENT):
                            yield btn
                
                with TabPane("🎬 多媒体", id="tab_media"):
                    with Grid(classes="app-grid"):
                        for btn in self._create_app_buttons(AppCategory.MULTIMEDIA):
                            yield btn
                
                with TabPane("🔧 工具", id="tab_tools"):
                    yield self._create_simple_tools()
            
            # Status and log
            with Container(classes="log-panel"):
                yield Static("安装日志:")
                yield Log(id="install_log")
        
        yield Footer()
    
    def _create_app_buttons(self, category: AppCategory) -> list[Button]:
        """Create app buttons for the grid.
        
        Returns a list of buttons to be yielded in compose.
        """
        import re
        
        buttons = []
        apps = self.center.get_apps_by_category(category)
        for app in apps:
            # Generate legal ID: only letters, numbers, underscores, hyphens
            # and must not begin with a number
            safe_name = app.name.lower().replace(' ', '_')
            # Remove illegal characters (keep only letters, numbers, underscores, hyphens)
            safe_name = re.sub(r'[^a-z0-9_-]', '', safe_name)
            # Ensure it doesn't start with a number
            if safe_name and safe_name[0].isdigit():
                safe_name = 'app_' + safe_name
            
            btn = Button(
                f"{app.name}\n[yellow]{app.description}[/]",
                id=f"app_{safe_name}",
                classes="app-button",
            )
            buttons.append(btn)
        return buttons
    
    def _create_simple_tools(self) -> Vertical:
        """Create simple tools section."""
        return Vertical(
            Static("常用命令行工具:"),
            Button("📝 Vim 编辑器", id="app_vim_simple", variant="primary"),
            Button("🐙 Git 版本控制", id="app_git_simple", variant="primary"),
            Button("🐍 Python3", id="app_python3_simple", variant="primary"),
            Button("🐳 Docker", id="app_docker_simple", variant="primary"),
            Button("📊 htop 系统监视器", id="app_htop"),
            Button("📡 curl 下载工具", id="app_curl"),
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id and button_id.startswith("app_"):
            app_name = button_id.replace("app_", "")
            self.run_worker(self._install_app(app_name))
    
    async def _install_app(self, app_name: str) -> None:
        """Install an application."""
        self._log(f"正在安装 {app_name}...")
        
        # Map button IDs to app names (must match generated IDs)
        app_map = {
            # Browsers
            "firefox": "firefox",
            "chromium": "chromium",
            "microsoft_edge": "edge",
            # Office
            "libreoffice": "libreoffice",
            "wps_office": "wps",
            # Development
            "visual_studio_code": "vscode",
            "pycharm": "pycharm",
            "intellij_idea": "idea",
            "android_studio": "android_studio",
            "vim": "vim",
            "neovim": "neovim",
            "git": "git",
            "docker": "docker",
            "nodejs": "nodejs",
            "python3": "python3",
            # Multimedia
            "mpv": "mpv",
            "vlc": "vlc",
            "gimp": "gimp",
            "audacity": "audacity",
            "spotify": "spotify",
            "clementine": "clementine",
            # Social
            "linux_qq": "linuxqq",
            "wechat": "wechat",
            "skype": "skype",
            "thunderbird": "thunderbird",
            # Games
            "steam": "steam",
            "kde_games": "kdegames",
            "retroarch": "retroarch",
            # Utilities
            "aria2": "aria2",
            "baidu_netdisk": "baidunetdisk",
            "synaptic": "synaptic",
            "bleachbit": "bleachbit",
            # Simple tools
            "vim_simple": "vim",
            "git_simple": "git",
            "python3_simple": "python3",
            "docker_simple": "docker",
            "htop": "htop",
            "curl": "curl",
        }
        
        actual_name = app_map.get(app_name, app_name)
        
        try:
            # In real implementation, this would call package manager
            # For demo, simulate installation
            self._log(f"正在检测发行版...")
            await asyncio.sleep(0.5)
            
            distro = self._detect_distro()
            self._log(f"检测到发行版: {distro}")
            
            self._log(f"正在安装 {actual_name}...")
            await asyncio.sleep(1)
            
            # Try to actually install if possible
            if actual_name in ["vim", "git", "curl", "htop"]:
                success = await self._try_install(actual_name)
                if success:
                    self._log(f"✅ {actual_name} 安装成功!")
                    self.notify(f"{actual_name} 安装成功!", severity="success")
                else:
                    self._log(f"⚠️  {actual_name} 安装失败或已安装")
            else:
                self._log(f"✅ {actual_name} 安装完成 (演示模式)")
                self.notify(f"{actual_name} 安装演示完成", severity="success")
                
        except Exception as e:
            self._log(f"❌ 安装失败: {e}")
            self.notify(f"安装失败: {e}", severity="error")
    
    async def _try_install(self, package: str) -> bool:
        """Try to install a package."""
        try:
            distro = self._detect_distro()
            
            match distro:
                case "debian" | "ubuntu":
                    cmd = ["apt", "install", "-y", package]
                case "arch":
                    cmd = ["pacman", "-S", "--noconfirm", package]
                case "fedora":
                    cmd = ["dnf", "install", "-y", package]
                case "alpine":
                    cmd = ["apk", "add", package]
                case _:
                    return False
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await proc.communicate()
            return proc.returncode == 0
            
        except Exception:
            return False
    
    def _detect_distro(self) -> str:
        """Detect current distribution."""
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
        
        return "debian"
    
    def _log(self, message: str) -> None:
        """Add message to log."""
        log = self.query_one("#install_log", Log)
        log.write_line(message)
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
    
    def action_install(self) -> None:
        """Install selected app."""
        self.notify("请在标签页中选择应用", severity="information")
