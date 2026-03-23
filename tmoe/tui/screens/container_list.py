"""Container list screen."""

from __future__ import annotations

import asyncio

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

from tmoe.container.chroot import ChrootBackend
from tmoe.container.proot import ProotBackend
from tmoe.core.config import get_config
from tmoe.core.platform import get_platform_info


class ContainerListScreen(Screen):
    """Screen showing list of all containers."""
    
    BINDINGS = [
        Binding("escape", "back", "返回"),
        Binding("q", "back", "返回"),
        Binding("r", "refresh", "刷新"),
        Binding("d", "details", "详情"),
        Binding("c", "create", "创建"),
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
    
    .empty-message {
        text-align: center;
        color: $text-muted;
        margin: 2 0;
    }
    """
    
    def __init__(self) -> None:
        self.platform = get_platform_info()
        self.config = get_config()
        self.proot_backend = ProotBackend(self.platform)
        self.chroot_backend = ChrootBackend(self.platform)
        self.containers: list[dict] = []
        super().__init__()
    
    async def on_mount(self) -> None:
        """Called when screen is mounted."""
        await self._refresh_containers()
    
    def compose(self) -> ComposeResult:
        with Container(classes="main-container"):
            yield Static("📋 容器列表", classes="title")
            
            # Toolbar
            with Horizontal(classes="toolbar"):
                yield Button("🔄 刷新 [r]", id="refresh", variant="primary")
                yield Button("➕ 创建 [c]", id="create", variant="success")
                yield Button("📖 详情 [d]", id="details")
                yield Button("▶️  启动", id="start", variant="success")
                yield Button("⏹️  停止", id="stop", variant="warning")
                yield Button("🗑️  删除", id="delete", variant="error")
            
            # Container table
            yield self._create_container_table()
            
            # Status bar
            yield Static("正在加载容器列表...", id="status_bar", classes="status-bar")
        
        yield Footer()
    
    def _create_container_table(self) -> DataTable:
        """Create the container data table."""
        table = DataTable(id="containers")
        table.add_columns("类型", "名称", "发行版", "架构", "状态", "大小")
        return table
    
    async def _refresh_containers(self) -> None:
        """Refresh container list from backends."""
        self.containers = []
        
        try:
            # Get proot containers
            proot_containers = await self.proot_backend.list_containers()
            for info in proot_containers:
                self.containers.append({
                    "type": "🐳",
                    "backend": "proot",
                    "name": info.name,
                    "distro": info.config.distro,
                    "arch": info.config.arch,
                    "status": info.status,
                    "size": await self._get_container_size(info.config.rootfs_path),
                })
            
            # Get chroot containers
            chroot_containers = await self.chroot_backend.list_containers()
            for info in chroot_containers:
                self.containers.append({
                    "type": "🔒",
                    "backend": "chroot",
                    "name": info.name,
                    "distro": info.config.distro,
                    "arch": info.config.arch,
                    "status": info.status,
                    "size": await self._get_container_size(info.config.rootfs_path),
                })
        except Exception as e:
            self.notify(f"获取容器列表失败: {e}", severity="error")
        
        # Update UI
        self._update_table()
        self._update_status_bar()
    
    async def _get_container_size(self, rootfs_path) -> str:
        """Get container size in human readable format."""
        if not rootfs_path or not rootfs_path.exists():
            return "Unknown"
        
        try:
            # Use du command to get size
            proc = await asyncio.create_subprocess_exec(
                "du", "-sh", str(rootfs_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await proc.communicate()
            size = stdout.decode().split()[0] if stdout else "Unknown"
            return size
        except Exception:
            return "Unknown"
    
    def _update_table(self) -> None:
        """Update the container table."""
        table = self.query_one("#containers", DataTable)
        table.clear()
        
        if not self.containers:
            self.notify("暂无容器，请按 'c' 创建新容器", severity="information")
            return
        
        for container in self.containers:
            status_icon = "🟢 运行中" if container["status"].value == "running" else "⚪ 已停止"
            table.add_row(
                container["type"],
                container["name"],
                container["distro"],
                container["arch"],
                status_icon,
                container["size"],
            )
    
    def _update_status_bar(self) -> None:
        """Update status bar."""
        status_bar = self.query_one("#status_bar", Static)
        proot_count = sum(1 for c in self.containers if c["backend"] == "proot")
        chroot_count = sum(1 for c in self.containers if c["backend"] == "chroot")
        status_bar.update(f"Proot: {proot_count} | Chroot: {chroot_count} | 总计: {len(self.containers)}")
    
    def _get_selected_container(self) -> dict | None:
        """Get the currently selected container."""
        table = self.query_one("#containers", DataTable)
        if table.cursor_row is not None and 0 <= table.cursor_row < len(self.containers):
            return self.containers[table.cursor_row]
        return None
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        match button_id:
            case "refresh":
                self.action_refresh()
            case "create":
                self.action_create()
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
    
    async def action_refresh(self) -> None:
        """Refresh container list."""
        self.notify("正在刷新容器列表...", severity="information")
        await self._refresh_containers()
    
    def action_create(self) -> None:
        """Create new container."""
        self.app.push_screen("create_container")
    
    def action_details(self) -> None:
        """Show container details."""
        container = self._get_selected_container()
        if container:
            self.notify(
                f"容器: {container['name']}\n"
                f"类型: {container['backend']}\n"
                f"发行版: {container['distro']}\n"
                f"架构: {container['arch']}",
                severity="information",
                timeout=5,
            )
        else:
            self.notify("请先选择一个容器", severity="warning")
    
    async def _start_container(self) -> None:
        """Start selected container."""
        container = self._get_selected_container()
        if not container:
            self.notify("请先选择一个容器", severity="warning")
            return
        
        self.notify(f"正在启动 {container['name']}...", severity="success")
        
        try:
            if container["backend"] == "proot":
                await self.proot_backend.start(container["name"])
            else:
                await self.chroot_backend.start(container["name"])
            await self._refresh_containers()
        except Exception as e:
            self.notify(f"启动失败: {e}", severity="error")
    
    async def _stop_container(self) -> None:
        """Stop selected container."""
        container = self._get_selected_container()
        if not container:
            self.notify("请先选择一个容器", severity="warning")
            return
        
        self.notify(f"正在停止 {container['name']}...", severity="warning")
        
        try:
            if container["backend"] == "proot":
                await self.proot_backend.stop(container["name"])
            else:
                await self.chroot_backend.stop(container["name"])
            await self._refresh_containers()
        except Exception as e:
            self.notify(f"停止失败: {e}", severity="error")
    
    async def _delete_container(self) -> None:
        """Delete selected container."""
        container = self._get_selected_container()
        if not container:
            self.notify("请先选择一个容器", severity="warning")
            return
        
        # TODO: Add confirmation dialog
        self.notify(f"正在删除 {container['name']}...", severity="error")
        
        try:
            if container["backend"] == "proot":
                await self.proot_backend.remove(container["name"], force=True)
            else:
                await self.chroot_backend.remove(container["name"], force=True)
            await self._refresh_containers()
        except Exception as e:
            self.notify(f"删除失败: {e}", severity="error")