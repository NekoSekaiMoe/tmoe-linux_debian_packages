"""Proot container management screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Label,
    ListItem,
    ListView,
    Static,
)

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
    """
    
    def __init__(self) -> None:
        self.platform = get_platform_info()
        self.config = get_config()
        super().__init__()
    
    def compose(self) -> ComposeResult:
        with Container(classes="main-container"):
            yield Static("🐳 Proot 容器管理", classes="title")
            yield Static("无需 root 权限的用户态容器", classes="subtitle")
            
            # Quick actions
            with Horizontal(classes="menu-grid"):
                yield Button("📦 创建容器 [c]", id="create", variant="primary")
                yield Button("📋 容器列表 [l]", id="list")
                yield Button("▶️  启动容器 [s]", id="start", variant="success")
                yield Button("🗑️  删除容器", id="remove", variant="error")
            
            # Container info
            with Container(classes="info-panel"):
                yield Static("📊 已安装容器:")
                yield self._create_container_table()
            
            # Instructions
            yield Static("\n[cyan]快捷键:[/] c=创建 l=列表 s=启动 Esc/q=返回", classes="subtitle")
        
        yield Footer()
    
    def _create_container_table(self) -> DataTable:
        """Create container info table."""
        table = DataTable(id="container_table")
        table.add_columns("名称", "发行版", "架构", "状态")
        
        # Add sample data (will be dynamic in real implementation)
        table.add_rows([
            ("debian-arm64", "debian", "arm64", "🟢 运行中"),
            ("ubuntu-test", "ubuntu", "arm64", "⚪ 已停止"),
        ])
        
        return table
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        match button_id:
            case "create":
                self.action_create()
            case "list":
                self.action_list()
            case "start":
                self.action_start()
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
        self.app.push_screen("container_manager")
    
    def action_start(self) -> None:
        """Start container."""
        self.app.push_screen("container_manager")
    
    def _remove_container(self) -> None:
        """Remove container."""
        self.notify("选择要删除的容器 - 功能开发中", severity="warning")
