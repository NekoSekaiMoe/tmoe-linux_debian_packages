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
                    yield self._create_app_grid(AppCategory.BROWSER)
                
                with TabPane("📝 办公", id="tab_office"):
                    yield self._create_app_grid(AppCategory.OFFICE)
                
                with TabPane("💻 开发", id="tab_dev"):
                    yield self._create_app_grid(AppCategory.DEVELOPMENT)
                
                with TabPane("🎬 多媒体", id="tab_media"):
                    yield self._create_app_grid(AppCategory.MULTIMEDIA)
                
                with TabPane("🔧 工具", id="tab_tools"):
                    yield self._create_simple_tools()
            
            # Status and log
            with Container(classes="log-panel"):
                yield Static("安装日志:")
                yield Log(id="install_log")
        
        yield Footer()
    
    def _create_app_grid(self, category: AppCategory) -> Grid:
        """Create app buttons grid."""
        grid = Grid(classes="app-grid")
        
        apps = self.center.get_apps_by_category(category)
        for app in apps:
            btn = Button(
                f"{app.name}\n[yellow]{app.description}[/]",
                id=f"app_{app.name.lower().replace(' ', '_')}",
                classes="app-button",
            )
            grid.mount(btn)
        
        return grid
    
    def _create_simple_tools(self) -> Vertical:
        """Create simple tools section."""
        return Vertical(
            Static("常用命令行工具:"),
            Button("📝 Vim 编辑器", id="app_vim", variant="primary"),
            Button("🐙 Git 版本控制", id="app_git", variant="primary"),
            Button("🐍 Python3", id="app_python3", variant="primary"),
            Button("🐳 Docker", id="app_docker", variant="primary"),
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
        
        # Map button IDs to app names
        app_map = {
            "firefox": "firefox",
            "chromium": "chromium",
            "microsoft_edge": "edge",
            "libreoffice": "libreoffice",
            "visual_studio_code": "vscode",
            "vim": "vim",
            "git": "git",
            "mpv": "mpv",
            "gimp": "gimp",
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
