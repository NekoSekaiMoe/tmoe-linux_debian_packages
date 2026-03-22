"""Main TUI application for TMOE using Textual.

This module provides the main Textual application with screens for:
- Main menu
- Container management
- GUI/VNC configuration
- Application center
- System tools
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Footer,
    Header,
    Label,
    ListItem,
    ListView,
    Static,
)

from tmoe.core.config import get_config
from tmoe.core.platform import get_platform_info
from tmoe.tui.screens.proot_menu import ProotMenuScreen
from tmoe.tui.screens.container_list import ContainerListScreen
from tmoe.tui.screens.create_container import CreateContainerScreen
from tmoe.tui.screens.container_manager import ContainerManagerScreen
from tmoe.tui.screens.mirror_manager import MirrorManagerScreen
from tmoe.tui.screens.app_installer import AppInstallerScreen
from tmoe.tui.screens.settings import SettingsScreen
from tmoe.tui.screens.backup_manager import BackupManagerScreen


class MainMenuScreen(Screen):
    """Main menu screen with all primary options."""
    
    BINDINGS = [
        Binding("q", "quit", "退出"),
        Binding("1", "proot", "Proot容器"),
        Binding("2", "chroot", "Chroot容器"),
        Binding("3", "gui", "GUI/远程桌面"),
        Binding("4", "apps", "应用中心"),
        Binding("5", "tools", "系统工具"),
    ]
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    .main-container {
        width: 80;
        height: auto;
        border: thick $background 80%;
        padding: 1 2;
    }
    
    .title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    
    .subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }
    
    .platform-info {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }
    
    ListView {
        width: 100%;
        height: auto;
        border: solid $primary;
    }
    
    ListItem {
        padding: 0 1;
    }
    
    ListItem:hover {
        background: $primary 10%;
    }
    
    .menu-item {
        padding: 0 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        platform = get_platform_info()
        config = get_config()
        
        with Container(classes="main-container"):
            yield Static("🐧 TMOE Linux 管理器", classes="title")
            yield Static(f"v{config.version} - More Optional Environments", classes="subtitle")
            
            # Platform info
            platform_text = f"📱 {platform.normalized_arch}"
            if platform.is_android:
                platform_text += " | Android"
                if platform.is_termux:
                    platform_text += f" (Termux {platform.termux_version or ''})"
            elif platform.is_wsl:
                platform_text += f" | WSL ({platform.wsl_distro_name or 'Unknown'})"
            else:
                platform_text += " | Linux"
            
            yield Static(platform_text, classes="platform-info")
            
            # Main menu
            yield ListView(
                ListItem(
                    Static("🐳 [1] Proot 容器 (无需root)"),
                    id="proot",
                ),
                ListItem(
                    Static("🔒 [2] Chroot 容器 (需要root)"),
                    id="chroot",
                ),
                ListItem(
                    Static("🖥️  [3] GUI/远程桌面"),
                    id="gui",
                ),
                ListItem(
                    Static("📦 [4] 应用中心"),
                    id="apps",
                ),
                ListItem(
                    Static("🔧 [5] 系统工具"),
                    id="tools",
                ),
                ListItem(
                    Static("📋 [l] 列出已安装容器"),
                    id="list",
                ),
                ListItem(
                    Static("⚙️  [s] 设置"),
                    id="settings",
                ),
                ListItem(
                    Static("❓ [h] 帮助"),
                    id="help",
                ),
                ListItem(
                    Static("🚪 [q] 退出"),
                    id="quit",
                ),
            )
        
        yield Footer()
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle menu selection."""
        item_id = event.item.id
        
        match item_id:
            case "proot":
                self.app.push_screen("proot_menu")
            case "chroot":
                self.app.push_screen("chroot_menu")
            case "gui":
                self.app.push_screen("gui_menu")
            case "apps":
                self.app.push_screen("apps_menu")
            case "tools":
                self.app.push_screen("tools_menu")
            case "list":
                self.action_list()
            case "settings":
                self.app.push_screen("settings")
            case "help":
                self.app.push_screen("help")
            case "quit":
                self.app.action_quit()
    
    def action_proot(self) -> None:
        """Action for proot container."""
        self.app.push_screen("proot_menu")
    
    def action_chroot(self) -> None:
        """Action for chroot container."""
        platform = get_platform_info()
        if not platform.is_root:
            self.notify("Chroot 需要 root 权限", severity="error")
            return
        self.app.push_screen("chroot_menu")
    
    def action_gui(self) -> None:
        """Action for GUI menu."""
        self.app.push_screen("gui_menu")
    
    def action_apps(self) -> None:
        """Action for apps menu."""
        self.app.push_screen("apps_menu")
    
    def action_tools(self) -> None:
        """Action for tools menu (mirror manager)."""
        self.app.push_screen("tools_menu")
    
    def action_list(self) -> None:
        """Action for list containers."""
        self.app.push_screen("container_list")


class PlaceholderScreen(Screen):
    """Placeholder screen for unimplemented features."""
    
    CSS = """
    Screen {
        align: center middle;
    }
    .placeholder {
        text-align: center;
    }
    """
    
    def __init__(self, name: str, message: str) -> None:
        self.message = message
        super().__init__(name=name)
    
    def compose(self) -> ComposeResult:
        with Container():
            yield Static(self.message, classes="placeholder")
            yield Static("按 [b]Escape[/b] 或 [b]q[/b] 返回主菜单")
        yield Footer()
    
    def action_quit(self) -> None:
        """Go back to main menu."""
        self.app.pop_screen()


class TmoeApp(App):
    """Main TMOE Textual application.
    
    Provides a modern TUI for managing Linux containers and GUI desktops.
    """
    
    CSS = """
    Screen {
        align: center middle;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "退出"),
        Binding("escape", "back", "返回"),
    ]
    
    SCREENS = {
        "main": MainMenuScreen,
        "proot_menu": ProotMenuScreen,
        "chroot_menu": lambda: PlaceholderScreen("chroot_menu", "🔒 Chroot 容器管理\n\n功能开发中..."),
        "gui_menu": lambda: PlaceholderScreen("gui_menu", "🖥️ GUI/远程桌面\n\n功能开发中..."),
        "apps_menu": AppInstallerScreen,
        "tools_menu": MirrorManagerScreen,
        "container_list": ContainerListScreen,
        "create_container": CreateContainerScreen,
        "container_manager": ContainerManagerScreen,
        "settings": SettingsScreen,
        "backup_manager": BackupManagerScreen,
        "help": lambda: PlaceholderScreen("help", """
❓ TMOE 帮助

快捷键:
  1-5    快速选择菜单项
  q      退出/返回
  Escape 返回上级菜单

支持的操作:
  - Proot 容器 (无需 root)
  - Chroot 容器 (需要 root)
  - GUI/远程桌面配置
  - 应用安装管理
  - 系统工具

更多信息: https://doc.tmoe.me
        """),
    }
    
    def __init__(self) -> None:
        super().__init__()
        self.platform = get_platform_info()
        self.config = get_config()
    
    def on_mount(self) -> None:
        """Called when app is mounted."""
        # Ensure directories exist
        self.platform.ensure_directories()
        
        # Push main screen
        self.push_screen("main")
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        if len(self.screen_stack) > 1:
            self.pop_screen()
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
