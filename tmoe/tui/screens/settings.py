"""Settings configuration screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.screen import Screen
from textual.widgets import (
    Button,
    Checkbox,
    Footer,
    Header,
    Input,
    Label,
    RadioSet,
    RadioButton,
    Select,
    Static,
    Switch,
)

from tmoe.core.config import get_config, reload_config
from tmoe.core.platform import get_platform_info


class SettingsScreen(Screen):
    """Settings configuration screen."""
    
    BINDINGS = [
        Binding("escape", "back", "返回"),
        Binding("q", "back", "返回"),
        Binding("s", "save", "保存"),
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
    
    .setting-row {
        height: auto;
        margin: 1 0;
    }
    
    .button-row {
        height: auto;
        margin-top: 2;
    }
    
    Select {
        width: 40;
    }
    
    Input {
        width: 40;
    }
    
    Switch {
        margin: 0 1;
    }
    """
    
    def __init__(self) -> None:
        self.platform = get_platform_info()
        self.config = get_config()
        super().__init__()
    
    def compose(self) -> ComposeResult:
        with Container(classes="main-container"):
            yield Static("⚙️ 设置", classes="title")
            
            # Language settings
            with Container(classes="section"):
                yield Static("🌐 语言设置", classes="section-title")
                with Horizontal(classes="setting-row"):
                    yield Label("界面语言: ")
                    yield Select(
                        [
                            ("简体中文 (zh_CN)", "zh_CN"),
                            ("繁體中文 (zh_TW)", "zh_TW"),
                            ("English (en_US)", "en_US"),
                            ("日本語 (ja_JP)", "ja_JP"),
                        ],
                        value=self.config.language,
                        id="language_select",
                    )
            
            # Container defaults
            with Container(classes="section"):
                yield Static("📦 容器默认设置", classes="section-title")
                with Horizontal(classes="setting-row"):
                    yield Label("默认架构: ")
                    yield Select(
                        [
                            ("ARM64 (aarch64)", "arm64"),
                            ("AMD64 (x86_64)", "amd64"),
                            ("ARMHF (armv7)", "armhf"),
                            ("i386 (x86)", "i386"),
                        ],
                        value=self.config.default_arch or "arm64",
                        id="arch_select",
                    )
                with Horizontal(classes="setting-row"):
                    yield Label("默认发行版: ")
                    yield Select(
                        [
                            ("Debian", "debian"),
                            ("Ubuntu", "ubuntu"),
                            ("Arch Linux", "arch"),
                            ("Alpine", "alpine"),
                            ("Fedora", "fedora"),
                        ],
                        value=self.config.default_distro,
                        id="distro_select",
                    )
            
            # VNC settings
            with Container(classes="section"):
                yield Static("🖥️ VNC 设置", classes="section-title")
                with Horizontal(classes="setting-row"):
                    yield Label("VNC 服务器: ")
                    yield RadioSet(
                        RadioButton("TigerVNC", id="vnc_tiger", value=self.config.vnc_server == "tiger"),
                        RadioButton("TightVNC", id="vnc_tight", value=self.config.vnc_server == "tight"),
                        id="vnc_server_radio",
                    )
                with Horizontal(classes="setting-row"):
                    yield Label("分辨率: ")
                    yield Select(
                        [
                            ("1920x1080 (全高清)", "1920x1080"),
                            ("1440x720 (推荐)", "1440x720"),
                            ("1280x720 (HD)", "1280x720"),
                            ("1024x768 (XGA)", "1024x768"),
                            ("800x600 (SVGA)", "800x600"),
                        ],
                        value=self.config.vnc_resolution,
                        id="resolution_select",
                    )
                with Horizontal(classes="setting-row"):
                    yield Label("显示号: ")
                    yield Input(
                        value=str(self.config.vnc_display),
                        id="display_input",
                    )
                with Horizontal(classes="setting-row"):
                    yield Label("仅本地访问: ")
                    yield Switch(
                        value=self.config.vnc_localhost,
                        id="localhost_switch",
                    )
            
            # Feature flags
            with Container(classes="section"):
                yield Static("🔧 功能设置", classes="section-title")
                with Horizontal(classes="setting-row"):
                    yield Label("自动检查更新: ")
                    yield Switch(
                        value=self.config.auto_update,
                        id="autoupdate_switch",
                    )
                with Horizontal(classes="setting-row"):
                    yield Label("详细输出: ")
                    yield Switch(
                        value=self.config.verbose,
                        id="verbose_switch",
                    )
                with Horizontal(classes="setting-row"):
                    yield Label("调试模式: ")
                    yield Switch(
                        value=self.config.debug,
                        id="debug_switch",
                    )
            
            # Buttons
            with Horizontal(classes="button-row"):
                yield Button("💾 保存设置 [s]", id="save", variant="success")
                yield Button("🔄 重置", id="reset", variant="warning")
                yield Button("❌ 取消", id="cancel", variant="error")
        
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        match button_id:
            case "save":
                self.action_save()
            case "reset":
                self._reset_settings()
            case "cancel":
                self.action_back()
    
    def _collect_settings(self) -> dict:
        """Collect settings from UI."""
        settings = {}
        
        # Language
        language_select = self.query_one("#language_select", Select)
        if language_select.value:
            settings["language"] = str(language_select.value)
        
        # Container defaults
        arch_select = self.query_one("#arch_select", Select)
        if arch_select.value:
            settings["default_arch"] = str(arch_select.value)
        
        distro_select = self.query_one("#distro_select", Select)
        if distro_select.value:
            settings["default_distro"] = str(distro_select.value)
        
        # VNC settings
        resolution_select = self.query_one("#resolution_select", Select)
        if resolution_select.value:
            settings["vnc_resolution"] = str(resolution_select.value)
        
        display_input = self.query_one("#display_input", Input)
        try:
            settings["vnc_display"] = int(display_input.value)
        except ValueError:
            pass
        
        localhost_switch = self.query_one("#localhost_switch", Switch)
        settings["vnc_localhost"] = localhost_switch.value
        
        # Feature flags
        autoupdate_switch = self.query_one("#autoupdate_switch", Switch)
        settings["auto_update"] = autoupdate_switch.value
        
        verbose_switch = self.query_one("#verbose_switch", Switch)
        settings["verbose"] = verbose_switch.value
        
        debug_switch = self.query_one("#debug_switch", Switch)
        settings["debug"] = debug_switch.value
        
        return settings
    
    def action_save(self) -> None:
        """Save settings."""
        settings = self._collect_settings()
        
        # Update config
        for key, value in settings.items():
            setattr(self.config, key, value)
        
        # Save to file
        self.config.save()
        
        self.notify("设置已保存", severity="success")
    
    def _reset_settings(self) -> None:
        """Reset to defaults."""
        self.config = reload_config()
        self.notify("设置已重置", severity="information")
        self.refresh()
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
