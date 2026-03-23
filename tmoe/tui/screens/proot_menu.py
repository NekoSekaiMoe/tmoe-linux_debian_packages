"""Proot container management screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Static,
)

from tmoe.container.proot import ProotBackend
from tmoe.core.config import get_config
from tmoe.core.platform import get_platform_info


class ProotMenuScreen(Screen):
    """Proot container management screen."""
    
    BINDINGS = [
        Binding("escape", "back", "返回"),
        Binding("q", "back", "返回"),
        Binding("c", "create", "创建"),
        Binding("l", "list", "列表"),
        Binding("s", "start", "启动"),
        Binding("r", "refresh", "刷新"),
    ]
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    .main-container {
        width: 90;
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
    
    .menu-grid {
        grid-size: 2;
        grid-gutter: 1;
        margin: 1 0;
    }
    
    .menu-button {
        width: 100%;
    }
    
    .info-panel {
        border: solid $primary;
        padding: 1;
        margin-top: 1;
    }
    
    DataTable {
        height: auto;
        max-height: 10;
        margin: 1 0;
    }
    
    .empty-message {
        text-align: center;
        color: $text-muted;
        margin: 1 0;
    }
    """
    
    def __init__(self) -> None:
        self.platform = get_platform_info()
        self.config = get_config()
        self.proot_backend = ProotBackend(self.platform)
        self.containers: list[dict] = []
        super().__init__()
    
    async def on_mount(self) -> None:
        """Called when screen is mounted."""
        await self._refresh_containers()
    
    def compose(self) -> ComposeResult:
        with Container(classes="main-container"):
            yield Static("🐳 Proot 容器管理", classes="title")
            yield Static("无需 root 权限的用户态容器", classes="subtitle")
            
            # Quick actions
            with Horizontal(classes="menu-grid"):
                yield Button("📦 创建容器 [c]", id="create", variant="primary")
                yield Button("📋 容器列表 [l]", id="list")
                yield Button("🔄 刷新 [r]", id="refresh")
                yield Button("🗑️  删除容器", id="remove", variant="error")
            
            # Container info
            with Container(classes="info-panel"):
                yield Static("📊 已安装容器:")
                yield self._create_container_table()
            
            # Instructions
            yield Static("\n[cyan]快捷键:[/] c=创建 l=列表 r=刷新 Esc/q=返回", classes="subtitle")
        
        yield Footer()
    
    def _create_container_table(self) -> DataTable:
        """Create container info table."""
        table = DataTable(id="container_table")
        table.add_columns("名称", "发行版", "架构", "状态")
        return table
    
    async def _refresh_containers(self) -> None:
        """Refresh container list from backend."""
        self.containers = []
        
        try:
            proot_containers = await self.proot_backend.list_containers()
            for info in proot_containers:
                self.containers.append({
                    "name": info.name,
                    "distro": info.config.distro,
                    "arch": info.config.arch,
                    "status": "🟢 运行中" if info.status.value == "running" else "⚪ 已停止",
                })
        except Exception as e:
            self.notify(f"获取容器列表失败: {e}", severity="error")
        
        # Update UI
        self._update_table()
    
    def _update_table(self) -> None:
        """Update the container table."""
        table = self.query_one("#container_table", DataTable)
        table.clear()
        
        if not self.containers:
            # Show empty message
            pass
        else:
            for container in self.containers:
                table.add_row(
                    container["name"],
                    container["distro"],
                    container["arch"],
                    container["status"],
                )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        match button_id:
            case "create":
                self.action_create()
            case "list":
                self.action_list()
            case "refresh":
                self.action_refresh()
            case "remove":
                self._remove_container()
    
    def action_back(self) -> None:
        """Go back to main menu."""
        self.app.pop_screen()
    
    def action_create(self) -> None:
        """Create new container."""
        self.app.push_screen("create_container")
    
    def action_list(self) -> None:
        """Show container list."""
        self.app.push_screen("container_list")
    
    async def action_refresh(self) -> None:
        """Refresh container list."""
        self.notify("正在刷新...", severity="information")
        await self._refresh_containers()
    
    async def _remove_container(self) -> None:
        """Remove container."""
        # TODO: Implement with proper selection
        self.notify("请在容器列表中选择要删除的容器", severity="warning")
        self.app.push_screen("container_list")