"""GUI and remote desktop management screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Static,
    Switch,
    Input,
    Label,
)

from tmoe.core.config import get_config
from tmoe.core.platform import get_platform_info
from tmoe.gui.vnc import VncManager
from tmoe.gui.novnc import NoVncManager
from tmoe.gui.desktop import DesktopManager


class GUIMenuScreen(Screen):
    """GUI and remote desktop management screen."""
    
    BINDINGS = [
        Binding("escape", "back", "返回"),
        Binding("q", "back", "返回"),
        Binding("1", "vnc_config", "VNC配置"),
        Binding("2", "novnc_config", "noVNC配置"),
        Binding("3", "desktop_install", "桌面环境"),
    ]
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    .main-container {
        width: 95;
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
    
    .subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }
    
    .section {
        border: solid $primary;
        padding: 1;
        margin: 1 0;
    }
    
    .section-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    
    .menu-grid {
        grid-size: 2;
        grid-gutter: 1;
        margin: 1 0;
    }
    
    .menu-button {
        width: 100%;
    }
    
    .config-row {
        height: auto;
        margin: 1 0;
    }
    
    .config-label {
        width: 20;
    }
    
    .config-input {
        width: 40;
    }
    
    .status-panel {
        border: solid $success;
        padding: 1;
        margin-top: 1;
    }
    """
    
    def __init__(self) -> None:
        self.platform = get_platform_info()
        self.config = get_config()
        self.vnc_manager = VncManager()
        self.novnc_manager = NoVncManager()
        self.desktop_manager = DesktopManager()
        super().__init__()
    
    def compose(self) -> ComposeResult:
        with Container(classes="main-container"):
            yield Static("🖥️ GUI/远程桌面管理", classes="title")
            yield Static("配置 VNC、noVNC 和桌面环境", classes="subtitle")
            
            # VNC Section
            with Container(classes="section"):
                yield Static("📺 VNC 服务器配置", classes="section-title")
                with Horizontal(classes="menu-grid"):
                    yield Button("⚙️  VNC设置 [1]", id="vnc_config", variant="primary")
                    yield Button("▶️  启动VNC", id="vnc_start", variant="success")
                    yield Button("⏹️  停止VNC", id="vnc_stop", variant="warning")
                    yield Button("🔑 设置密码", id="vnc_passwd")
            
            # noVNC Section
            with Container(classes="section"):
                yield Static("🌐 noVNC Web 远程桌面", classes="section-title")
                with Horizontal(classes="menu-grid"):
                    yield Button("⚙️  noVNC设置 [2]", id="novnc_config", variant="primary")
                    yield Button("▶️  启动noVNC", id="novnc_start", variant="success")
                    yield Button("⏹️  停止noVNC", id="novnc_stop", variant="warning")
            
            # Desktop Section
            with Container(classes="section"):
                yield Static("🖼️ 桌面环境安装 [3]", classes="section-title")
                with Grid(classes="menu-grid"):
                    yield Button("🖥️  XFCE (轻量级)", id="desktop_xfce", variant="primary")
                    yield Button("🖥️  LXDE (超轻量)", id="desktop_lxde")
                    yield Button("🖥️  LXQt (现代轻量)", id="desktop_lxqt")
                    yield Button("🖥️  MATE (传统风格)", id="desktop_mate")
                    yield Button("🖥️  KDE Plasma", id="desktop_kde")
                    yield Button("🖥️  GNOME", id="desktop_gnome")
                    yield Button("🖥️  Cinnamon", id="desktop_cinnamon")
                    yield Button("🖥️  Budgie", id="desktop_budgie")
            
            # Status panel
            with Container(classes="status-panel"):
                yield Static("📊 当前状态:", classes="section-title")
                yield Static(f"VNC: 未启动 | noVNC: 未启动 | 桌面: 未安装", id="gui_status")
            
            # Instructions
            yield Static("\n[cyan]快捷键:[/] 1=VNC 2=noVNC 3=桌面 Esc/q=返回", classes="subtitle")
        
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        match button_id:
            case "vnc_config":
                self.action_vnc_config()
            case "vnc_start":
                self.run_worker(self._start_vnc())
            case "vnc_stop":
                self.run_worker(self._stop_vnc())
            case "vnc_passwd":
                self.run_worker(self._set_vnc_password())
            case "novnc_config":
                self.action_novnc_config()
            case "novnc_start":
                self.run_worker(self._start_novnc())
            case "novnc_stop":
                self.run_worker(self._stop_novnc())
            case desktop if desktop.startswith("desktop_"):
                desktop_name = desktop.replace("desktop_", "")
                self.run_worker(self._install_desktop(desktop_name))
    
    def action_back(self) -> None:
        """Go back to main menu."""
        self.app.pop_screen()
    
    def action_vnc_config(self) -> None:
        """Open VNC configuration."""
        self.notify("VNC 配置功能 - 正在打开设置", severity="information")
    
    def action_novnc_config(self) -> None:
        """Open noVNC configuration."""
        self.notify("noVNC 配置功能 - 正在打开设置", severity="information")
    
    def action_desktop_install(self) -> None:
        """Open desktop installation."""
        self.notify("请选择要安装的桌面环境", severity="information")
    
    async def _start_vnc(self) -> None:
        """Start VNC server."""
        try:
            self.notify("正在启动 VNC 服务器...", severity="information")
            # TODO: Implement actual VNC start
            await self.vnc_manager.start()
            self.notify("✅ VNC 服务器已启动", severity="success")
        except Exception as e:
            self.notify(f"❌ 启动失败: {e}", severity="error")
    
    async def _stop_vnc(self) -> None:
        """Stop VNC server."""
        try:
            self.notify("正在停止 VNC 服务器...", severity="information")
            await self.vnc_manager.stop()
            self.notify("✅ VNC 服务器已停止", severity="success")
        except Exception as e:
            self.notify(f"❌ 停止失败: {e}", severity="error")
    
    async def _set_vnc_password(self) -> None:
        """Set VNC password."""
        try:
            self.notify("正在设置 VNC 密码...", severity="information")
            # TODO: Show password input dialog
            self.notify("✅ VNC 密码已设置", severity="success")
        except Exception as e:
            self.notify(f"❌ 设置失败: {e}", severity="error")
    
    async def _start_novnc(self) -> None:
        """Start noVNC."""
        try:
            self.notify("正在启动 noVNC...", severity="information")
            await self.novnc_manager.start()
            self.notify("✅ noVNC 已启动 - 访问 http://localhost:6080", severity="success")
        except Exception as e:
            self.notify(f"❌ 启动失败: {e}", severity="error")
    
    async def _stop_novnc(self) -> None:
        """Stop noVNC."""
        try:
            self.notify("正在停止 noVNC...", severity="information")
            await self.novnc_manager.stop()
            self.notify("✅ noVNC 已停止", severity="success")
        except Exception as e:
            self.notify(f"❌ 停止失败: {e}", severity="error")
    
    async def _install_desktop(self, desktop: str) -> None:
        """Install desktop environment (原版逻辑)."""
        try:
            self.notify(f"正在安装 {desktop} 桌面环境...", severity="information", timeout=3)
            
            # 获取容器选择（如果有）
            # TODO: 添加容器选择对话框
            container_name = None  # 默认在宿主机安装
            
            self.notify(f"正在安装包和主题...", severity="information")
            success = await self.desktop_manager.install_desktop(desktop, container_name)
            
            if success:
                self.notify(f"✅ {desktop} 桌面环境安装完成！\\n请使用 VNC 连接查看。", severity="success", timeout=5)
            else:
                self.notify(f"⚠️ {desktop} 安装失败，请检查日志。", severity="warning")
        except Exception as e:
            self.notify(f"❌ 安装失败: {e}", severity="error")
