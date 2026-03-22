"""Container backup manager screen."""

from __future__ import annotations

import asyncio
from pathlib import Path

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
    RadioSet,
    RadioButton,
    Static,
)

from tmoe.container.backup import ContainerBackupManager, BackupInfo
from tmoe.container.proot import ProotBackend
from tmoe.core.config import get_config
from tmoe.core.platform import get_platform_info


class BackupManagerScreen(Screen):
    """Screen for managing container backups."""
    
    BINDINGS = [
        Binding("escape", "back", "返回"),
        Binding("q", "back", "返回"),
        Binding("b", "backup", "备份"),
        Binding("r", "restore", "恢复"),
        Binding("d", "delete", "删除"),
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
    
    .section {
        border: solid $primary;
        padding: 1;
        margin: 1 0;
    }
    
    .section-title {
        text-style: bold;
        color: $text-accent;
        margin-bottom: 1;
    }
    
    DataTable {
        height: auto;
        max-height: 15;
        margin: 1 0;
    }
    
    .toolbar {
        height: auto;
        margin: 1 0;
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
        self.backend = ProotBackend()
        self.manager = ContainerBackupManager(self.backend)
        self.backups: list[BackupInfo] = []
        super().__init__()
    
    def compose(self) -> ComposeResult:
        with Container(classes="main-container"):
            yield Static("💾 容器备份管理", classes="title")
            
            # Container selection
            with Container(classes="section"):
                yield Static("📦 选择容器", classes="section-title")
                yield self._create_container_table()
            
            # Backup list
            with Container(classes="section"):
                yield Static("💾 备份列表", classes="section-title")
                yield self._create_backup_table()
            
            # Compression selection
            with Container(classes="section"):
                yield Static("🗜️  压缩选项", classes="section-title")
                with RadioSet(id="compression_radio"):
                    yield RadioButton("XZ (推荐，高压缩)", id="xz", value=True)
                    yield RadioButton("GZ (快速压缩)", id="gz")
                    yield RadioButton("BZ2 (平衡)", id="bz2")
                    yield RadioButton("无压缩", id="none")
            
            # Toolbar
            with Horizontal(classes="toolbar"):
                yield Button("💾 备份 [b]", id="backup", variant="success")
                yield Button("📂 恢复 [r]", id="restore", variant="primary")
                yield Button("🗑️  删除 [d]", id="delete", variant="error")
                yield Button("🔄 刷新", id="refresh")
            
            # Log panel
            with Container(classes="log-panel"):
                yield Static("操作日志:")
                yield Log(id="backup_log")
        
        yield Footer()
    
    def _create_container_table(self) -> DataTable:
        """Create container list table."""
        table = DataTable(id="containers")
        table.add_columns("名称", "发行版", "架构", "大小")
        
        # Add sample data
        table.add_rows([
            ("debian-arm64", "debian", "arm64", "2.1 GB"),
            ("ubuntu-test", "ubuntu", "arm64", "1.8 GB"),
        ])
        
        return table
    
    def _create_backup_table(self) -> DataTable:
        """Create backup list table."""
        table = DataTable(id="backups")
        table.add_columns("备份文件", "原容器", "创建时间", "大小", "压缩")
        table.cursor_type = "row"
        
        # Add sample data
        table.add_rows([
            ("debian-arm64_20240322_120000.tar.xz", "debian-arm64", "2024-03-22 12:00", "850 MB", "xz"),
            ("ubuntu-test_20240321_100000.tar.gz", "ubuntu-test", "2024-03-21 10:00", "920 MB", "gz"),
        ])
        
        return table
    
    async def on_mount(self) -> None:
        """Called when screen is mounted."""
        await self._refresh_backups()
    
    async def _refresh_backups(self) -> None:
        """Refresh backup list."""
        try:
            self.backups = self.manager.list_backups()
            
            table = self.query_one("#backups", DataTable)
            table.clear()
            
            for backup in self.backups:
                table.add_row(
                    backup.name,
                    backup.container_name,
                    backup.created_at.strftime("%Y-%m-%d %H:%M"),
                    backup.size_human,
                    backup.compression,
                )
            
            self._log(f"找到 {len(self.backups)} 个备份")
            
        except Exception as e:
            self._log(f"刷新失败: {e}", level="error")
    
    def _get_selected_container(self) -> str | None:
        """Get selected container name."""
        table = self.query_one("#containers", DataTable)
        if table.cursor_row is not None:
            # Return container name from row
            row = table.get_row_at(table.cursor_row)
            return str(row[0]) if row else None
        return None
    
    def _get_selected_backup(self) -> BackupInfo | None:
        """Get selected backup info."""
        table = self.query_one("#backups", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self.backups):
            return self.backups[table.cursor_row]
        return None
    
    def _get_compression(self) -> str:
        """Get selected compression type."""
        radio = self.query_one("#compression_radio", RadioSet)
        # Get pressed button
        if radio.pressed_button:
            return radio.pressed_button.id or "xz"
        return "xz"
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        match button_id:
            case "backup":
                self.run_worker(self._backup_container())
            case "restore":
                self.run_worker(self._restore_backup())
            case "delete":
                self.run_worker(self._delete_backup())
            case "refresh":
                self.run_worker(self._refresh_backups())
    
    async def _backup_container(self) -> None:
        """Backup selected container."""
        container_name = self._get_selected_container()
        if not container_name:
            self.notify("请先选择一个容器", severity="warning")
            return
        
        compression = self._get_compression()
        
        self._log(f"正在备份容器: {container_name} (压缩: {compression})...")
        
        try:
            backup = await self.manager.backup_container(container_name, compression)
            self._log(f"备份完成: {backup.name} ({backup.size_human})")
            self.notify(f"备份完成: {backup.name}", severity="success")
            await self._refresh_backups()
        except Exception as e:
            self._log(f"备份失败: {e}", level="error")
            self.notify(f"备份失败: {e}", severity="error")
    
    async def _restore_backup(self) -> None:
        """Restore selected backup."""
        backup = self._get_selected_backup()
        if not backup:
            self.notify("请先选择一个备份", severity="warning")
            return
        
        self._log(f"正在恢复备份: {backup.name}...")
        
        try:
            await self.manager.restore_container(backup.path)
            self._log(f"恢复完成: {backup.container_name}")
            self.notify(f"恢复完成: {backup.container_name}", severity="success")
        except Exception as e:
            self._log(f"恢复失败: {e}", level="error")
            self.notify(f"恢复失败: {e}", severity="error")
    
    async def _delete_backup(self) -> None:
        """Delete selected backup."""
        backup = self._get_selected_backup()
        if not backup:
            self.notify("请先选择一个备份", severity="warning")
            return
        
        self._log(f"正在删除备份: {backup.name}...")
        
        try:
            await self.manager.delete_backup(backup.path)
            self._log(f"删除完成: {backup.name}")
            self.notify(f"删除完成: {backup.name}", severity="success")
            await self._refresh_backups()
        except Exception as e:
            self._log(f"删除失败: {e}", level="error")
            self.notify(f"删除失败: {e}", severity="error")
    
    def _log(self, message: str, level: str = "info") -> None:
        """Add message to log."""
        log = self.query_one("#backup_log", Log)
        prefix = {
            "info": "[INFO]",
            "error": "[ERROR]",
            "warning": "[WARN]",
        }.get(level, "[INFO]")
        log.write_line(f"{prefix} {message}")
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
    
    def action_backup(self) -> None:
        """Backup container."""
        self.run_worker(self._backup_container())
    
    def action_restore(self) -> None:
        """Restore backup."""
        self.run_worker(self._restore_backup())
    
    def action_delete(self) -> None:
        """Delete backup."""
        self.run_worker(self._delete_backup())