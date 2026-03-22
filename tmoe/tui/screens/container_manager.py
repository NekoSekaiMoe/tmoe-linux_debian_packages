"""Container manager screen for lifecycle operations."""

from __future__ import annotations

import asyncio

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
    Log,
    Static,
)

from tmoe.container.proot import ProotBackend
from tmoe.container.base import ContainerInfo, ContainerStatus
from tmoe.core.config import get_config
from tmoe.core.platform import get_platform_info


class ContainerManagerScreen(Screen):
    """Screen for managing container lifecycle."""
    
    BINDINGS = [
        Binding("escape", "back", "返回"),
        Binding("q", "back", "返回"),
        Binding("r", "refresh", "刷新"),
        Binding("s", "start", "启动"),
        Binding("t", "stop", "停止"),
        Binding("d", "delete", "删除"),
        Binding("e", "enter", "进入"),
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
    
    .toolbar {
        height: auto;
        margin: 1 0;
    }
    
    DataTable {
        height: 1fr;
        margin: 1 0;
    }
    
    .log-panel {
        height: 20%;
        border: solid $primary;
        padding: 0 1;
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
        self.backend = ProotBackend()
        self.containers: list[ContainerInfo] = []
        super().__init__()
    
    def compose(self) -> ComposeResult:
        with Container(classes="main-container"):
            yield Static("🐳 容器管理", classes="title")
            
            # Toolbar
            with Horizontal(classes="toolbar"):
                yield Button("🔄 刷新 [r]", id="refresh", variant="primary")
                yield Button("▶️  启动 [s]", id="start", variant="success")
                yield Button("⏹️  停止 [t]", id="stop", variant="warning")
                yield Button("🗑️  删除 [d]", id="delete", variant="error")
                yield Button("🔲 进入 [e]", id="enter")
            
            # Container table
            yield self._create_container_table()
            
            # Log panel
            with Container(classes="log-panel"):
                yield Static("操作日志:")
                yield Log(id="operation_log")
            
            # Status bar
            yield Static("就绪", classes="status-bar", id="status_bar")
        
        yield Footer()
    
    def _create_container_table(self) -> DataTable:
        """Create the container data table."""
        table = DataTable(id="containers")
        table.add_columns("类型", "名称", "发行版", "架构", "状态", "大小")
        table.cursor_type = "row"
        return table
    
    async def on_mount(self) -> None:
        """Called when screen is mounted."""
        await self._refresh_containers()
    
    async def _refresh_containers(self) -> None:
        """Refresh container list."""
        self._log("正在刷新容器列表...")
        
        try:
            self.containers = await self.backend.list_containers()
            table = self.query_one("#containers", DataTable)
            table.clear()
            
            for info in self.containers:
                status_icon = "🟢" if info.status == ContainerStatus.RUNNING else "⚪"
                table.add_row(
                    "🐳",
                    info.name,
                    info.config.distro,
                    info.config.arch,
                    f"{status_icon} {info.status.name}",
                    info.size_human,
                )
            
            self._update_status(f"共 {len(self.containers)} 个容器")
            self._log(f"找到 {len(self.containers)} 个容器")
            
        except Exception as e:
            self._log(f"刷新失败: {e}", level="error")
            self._update_status(f"错误: {e}")
    
    def _get_selected_container(self) -> ContainerInfo | None:
        """Get the currently selected container."""
        table = self.query_one("#containers", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self.containers):
            return self.containers[table.cursor_row]
        return None
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        match button_id:
            case "refresh":
                self.run_worker(self._refresh_containers())
            case "start":
                self.run_worker(self._start_container())
            case "stop":
                self.run_worker(self._stop_container())
            case "delete":
                self.run_worker(self._delete_container())
            case "enter":
                self.run_worker(self._enter_container())
    
    async def _start_container(self) -> None:
        """Start selected container."""
        container = self._get_selected_container()
        if not container:
            self.notify("请先选择一个容器", severity="warning")
            return
        
        self._log(f"正在启动容器: {container.name}...")
        self._update_status(f"正在启动 {container.name}...")
        
        try:
            await self.backend.start(container.name)
            self._log(f"容器 {container.name} 已启动")
            self.notify(f"容器 {container.name} 已启动", severity="success")
            await self._refresh_containers()
        except Exception as e:
            self._log(f"启动失败: {e}", level="error")
            self.notify(f"启动失败: {e}", severity="error")
    
    async def _stop_container(self) -> None:
        """Stop selected container."""
        container = self._get_selected_container()
        if not container:
            self.notify("请先选择一个容器", severity="warning")
            return
        
        self._log(f"正在停止容器: {container.name}...")
        self._update_status(f"正在停止 {container.name}...")
        
        try:
            await self.backend.stop(container.name)
            self._log(f"容器 {container.name} 已停止")
            self.notify(f"容器 {container.name} 已停止", severity="success")
            await self._refresh_containers()
        except Exception as e:
            self._log(f"停止失败: {e}", level="error")
            self.notify(f"停止失败: {e}", severity="error")
    
    async def _delete_container(self) -> None:
        """Delete selected container."""
        container = self._get_selected_container()
        if not container:
            self.notify("请先选择一个容器", severity="warning")
            return
        
        # In real implementation, show confirmation dialog
        self._log(f"正在删除容器: {container.name}...")
        self._update_status(f"正在删除 {container.name}...")
        
        try:
            await self.backend.remove(container.name, force=True)
            self._log(f"容器 {container.name} 已删除")
            self.notify(f"容器 {container.name} 已删除", severity="success")
            await self._refresh_containers()
        except Exception as e:
            self._log(f"删除失败: {e}", level="error")
            self.notify(f"删除失败: {e}", severity="error")
    
    async def _enter_container(self) -> None:
        """Enter selected container."""
        container = self._get_selected_container()
        if not container:
            self.notify("请先选择一个容器", severity="warning")
            return
        
        self._log(f"正在进入容器: {container.name}...")
        self.notify(f"进入容器 {container.name} - 功能开发中", severity="information")
    
    def _log(self, message: str, level: str = "info") -> None:
        """Add message to log."""
        log = self.query_one("#operation_log", Log)
        prefix = {
            "info": "[INFO]",
            "error": "[ERROR]",
            "warning": "[WARN]",
        }.get(level, "[INFO]")
        log.write_line(f"{prefix} {message}")
    
    def _update_status(self, message: str) -> None:
        """Update status bar."""
        status = self.query_one("#status_bar", Static)
        status.update(message)
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
    
    def action_refresh(self) -> None:
        """Refresh container list."""
        self.run_worker(self._refresh_containers())
    
    def action_start(self) -> None:
        """Start selected container."""
        self.run_worker(self._start_container())
    
    def action_stop(self) -> None:
        """Stop selected container."""
        self.run_worker(self._stop_container())
    
    def action_delete(self) -> None:
        """Delete selected container."""
        self.run_worker(self._delete_container())
    
    def action_enter(self) -> None:
        """Enter selected container."""
        self.run_worker(self._enter_container())
