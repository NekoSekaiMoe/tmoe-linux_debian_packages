"""Mirror source management screen."""

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
    RadioSet,
    RadioButton,
    Static,
)

from tmoe.core.config import get_config
from tmoe.core.constants import CHINA_MIRRORS
from tmoe.sources.mirrors import MirrorManager, MirrorRegion
from tmoe.core.platform import get_platform_info


class MirrorManagerScreen(Screen):
    """Screen for managing software repository mirrors."""
    
    BINDINGS = [
        Binding("escape", "back", "返回"),
        Binding("q", "back", "返回"),
        Binding("t", "test", "测速"),
        Binding("a", "apply", "应用"),
    ]
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    .main-container {
        width: 90;
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
    
    .button-row {
        height: auto;
        margin: 1 0;
    }
    
    .log-panel {
        height: 15%;
        border: solid $surface-lighten-1;
        padding: 0 1;
    }
    """
    
    def __init__(self) -> None:
        self.platform = get_platform_info()
        self.config = get_config()
        self.manager = MirrorManager()
        self.selected_mirror: str | None = None
        self.mirror_speeds: dict[str, float] = {}
        super().__init__()
    
    def compose(self) -> ComposeResult:
        with Container(classes="main-container"):
            yield Static("🪞 镜像源管理", classes="title")
            
            # Mirror list
            with Container(classes="section"):
                yield Static("📋 可用镜像源", classes="section-title")
                yield self._create_mirror_table()
            
            # Quick select
            with Container(classes="section"):
                yield Static("⚡ 快速选择 (国内镜像)", classes="section-title")
                with RadioSet(id="mirror_radio"):
                    yield RadioButton("清华大学 (Tsinghua)", id="tsinghua", value=True)
                    yield RadioButton("中科大 (USTC)", id="ustc")
                    yield RadioButton("阿里云 (Aliyun)", id="aliyun")
                    yield RadioButton("腾讯云 (Tencent)", id="tencent")
                    yield RadioButton("华为云 (Huawei)", id="huawei")
                    yield RadioButton("官方源 (Official)", id="debian")
            
            # Buttons
            with Horizontal(classes="button-row"):
                yield Button("🧪 测速 [t]", id="test", variant="primary")
                yield Button("✅ 应用 [a]", id="apply", variant="success")
                yield Button("🔄 恢复默认", id="reset", variant="warning")
            
            # Log panel
            with Container(classes="log-panel"):
                yield Static("操作日志:")
                yield Log(id="mirror_log")
        
        yield Footer()
    
    def _create_mirror_table(self) -> DataTable:
        """Create mirror list table."""
        table = DataTable(id="mirrors")
        table.add_columns("名称", "URL", "地区", "速度")
        
        # Add China mirrors
        for name, url in CHINA_MIRRORS.items():
            table.add_row(
                name.capitalize(),
                url,
                "🇨🇳 中国",
                "未测试",
            )
        
        # Add global mirrors
        table.add_row("Debian", "deb.debian.org", "🌍 全球", "-")
        table.add_row("Ubuntu", "archive.ubuntu.com", "🌍 全球", "-")
        
        return table
    
    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle mirror selection."""
        if event.radio_set.id == "mirror_radio":
            self.selected_mirror = event.pressed.id
            self._log(f"选择镜像: {self.selected_mirror}")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        match button_id:
            case "test":
                self.run_worker(self._test_mirrors())
            case "apply":
                self.run_worker(self._apply_mirror())
            case "reset":
                self.run_worker(self._reset_mirror())
    
    async def _test_mirrors(self) -> None:
        """Test mirror speeds."""
        self._log("开始测试镜像速度...")
        
        mirrors_to_test = list(CHINA_MIRRORS.keys())[:4]
        
        for mirror_name in mirrors_to_test:
            self._log(f"正在测试 {mirror_name}...")
            try:
                speed = await self.manager.test_mirror_speed(mirror_name)
                self.mirror_speeds[mirror_name] = speed
                
                if speed > 0:
                    self._log(f"{mirror_name}: {speed:.1f} KB/s")
                else:
                    self._log(f"{mirror_name}: 无法连接")
                    
            except Exception as e:
                self._log(f"{mirror_name} 测试失败: {e}")
        
        # Find fastest
        if self.mirror_speeds:
            fastest = max(self.mirror_speeds.items(), key=lambda x: x[1])
            self._log(f"最快镜像: {fastest[0]} ({fastest[1]:.1f} KB/s)")
    
    async def _apply_mirror(self) -> None:
        """Apply selected mirror."""
        if not self.selected_mirror:
            self.notify("请先选择一个镜像", severity="warning")
            return
        
        # Detect distro
        distro = self._detect_distro()
        if not distro:
            self.notify("无法检测发行版", severity="error")
            return
        
        self._log(f"正在应用镜像 {self.selected_mirror} 到 {distro}...")
        
        try:
            await self.manager.switch_mirror(distro, self.selected_mirror)
            self._log(f"镜像源已切换至 {self.selected_mirror}")
            self.notify(f"镜像源已切换至 {self.selected_mirror}", severity="success")
        except Exception as e:
            self._log(f"切换失败: {e}", level="error")
            self.notify(f"切换失败: {e}", severity="error")
    
    async def _reset_mirror(self) -> None:
        """Reset to default mirror."""
        self._log("正在恢复默认镜像源...")
        
        distro = self._detect_distro()
        if distro:
            try:
                # Reset to official mirror
                await self.manager.switch_mirror(distro, distro)
                self._log("已恢复默认镜像源")
                self.notify("已恢复默认镜像源", severity="success")
            except Exception as e:
                self._log(f"恢复失败: {e}", level="error")
    
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
        
        return "debian"  # Default
    
    def _log(self, message: str, level: str = "info") -> None:
        """Add message to log."""
        log = self.query_one("#mirror_log", Log)
        prefix = {
            "info": "[INFO]",
            "error": "[ERROR]",
            "warning": "[WARN]",
        }.get(level, "[INFO]")
        log.write_line(f"{prefix} {message}")
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
    
    def action_test(self) -> None:
        """Test mirror speeds."""
        self.run_worker(self._test_mirrors())
    
    def action_apply(self) -> None:
        """Apply selected mirror."""
        self.run_worker(self._apply_mirror())
