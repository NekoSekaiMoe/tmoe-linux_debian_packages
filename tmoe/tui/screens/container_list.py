"""Container list screen."""

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
    Static,
)

from tmoe.core.config import get_config
from tmoe.core.platform import get_platform_info


class ContainerListScreen(Screen):
    """Screen showing list of all containers."""
    
    BINDINGS = [
        Binding("escape", "back", "返回"),
        Binding("q", "back", "返回"),
        Binding("r", "refresh", "刷新"),
        Binding("d", "details", "详情"),
    ]
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    .main-container {
        width: 100;
        height: 90%;
        border: thick $background 80%;
        padding: 1 2;
    }
    
    .title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    
    .toolbar {
        height: auto;
        margin: 1 0;
    }
    
    DataTable {
        height: 1fr;
        margin: 1 0;
    }
    
    .status-bar {
        height: auto;
        background: $surface-darken-1;
        padding: 0 1;
    }
    """
    
    def __init__(self) -> None:
        self.platform = get_platform_info()
        self.config = get_config()
        self.containers: list[dict] = []
        super().__init__()
    
    def compose(self) -> ComposeResult:
        with Container(classes="main-container"):
            yield Static("📋 容器列表", classes="title")
            
            # Toolbar
            with Horizontal(classes="toolbar"):
                yield Button("🔄 刷新 [r]", id="refresh", variant="primary")
                yield Button("📖 详情 [d]", id="details")
                yield Button("▶️  启动", id="start", variant="success")
                yield Button("⏹️  停止", id="stop", variant="warning")
                yield Button("🗑️  删除", id="delete", variant="error")
            
            # Container table
            yield self._create_container_table()
            
            # Status bar
            yield Static(f"Proot: 2 | Chroot: 0 | 总计: 2", classes="status-bar")
        
        yield Footer()
    
    def _create_container_table(self) -> DataTable:
        """Create the container data table."""
        table = DataTable(id="containers")
        table.add_columns("类型", "名称", "发行版", "架构", "状态", "大小")
        
        # Sample data
        table.add_rows([
            ("🐳", "debian-arm64", "debian", "arm64", "🟢 运行中", "2.1 GB"),
            ("🐳", "ubuntu-test", "ubuntu", "arm64", "⚪ 已停止", "1.8 GB"),
            ("🔒", "arch-root", "arch", "arm64", "⚪ 已停止", "3.2 GB"),
        ])
        
        return table
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        match button_id:
            case "refresh":
                self.action_refresh()
            case "details":
                self.action_details()
            case "start":
                self._start_container()
            case "stop":
                self._stop_container()
            case "delete":
                self._delete_container()
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
    
    def action_refresh(self) -> None:
        """Refresh container list."""
        self.notify("正在刷新容器列表...", severity="information")
        # TODO: Implement actual refresh
    
    def action_details(self) -> None:
        """Show container details."""
        table = self.query_one("#containers", DataTable)
        if table.cursor_row is not None:
            row_key = table.cursor_row
            self.notify(f"查看第 {row_key + 1} 个容器的详情", severity="information")
        else:
            self.notify("请先选择一个容器", severity="warning")
    
    def _start_container(self) -> None:
        """Start selected container."""
        table = self.query_one("#containers", DataTable)
        if table.cursor_row is not None:
            self.notify("正在启动容器...", severity="success")
        else:
            self.notify("请先选择一个容器", severity="warning")
    
    def _stop_container(self) -> None:
        """Stop selected container."""
        table = self.query_one("#containers", DataTable)
        if table.cursor_row is not None:
            self.notify("正在停止容器...", severity="warning")
        else:
            self.notify("请先选择一个容器", severity="warning")
    
    def _delete_container(self) -> None:
        """Delete selected container."""
        table = self.query_one("#containers", DataTable)
        if table.cursor_row is not None:
            self.notify("正在删除容器...", severity="error")
        else:
            self.notify("请先选择一个容器", severity="warning")
