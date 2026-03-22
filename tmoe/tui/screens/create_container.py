"""Container creation wizard screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    RadioSet,
    RadioButton,
    Select,
    Static,
)

from tmoe.core.config import get_config
from tmoe.core.constants import SUPPORTED_ARCHITECTURES, SUPPORTED_DISTROS
from tmoe.core.platform import get_platform_info


class CreateContainerScreen(Screen):
    """Container creation wizard."""
    
    BINDINGS = [
        Binding("escape", "back", "返回"),
        Binding("q", "back", "返回"),
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
    
    .step-container {
        border: solid $primary;
        padding: 1;
        margin: 1 0;
    }
    
    .step-title {
        text-style: bold;
        color: $text-accent;
        margin-bottom: 1;
    }
    
    RadioSet {
        margin: 1 0;
    }
    
    Select {
        margin: 1 0;
    }
    
    Input {
        margin: 1 0;
    }
    
    .button-row {
        height: auto;
        margin-top: 1;
    }
    
    .preview {
        background: $surface-darken-1;
        padding: 1;
        margin: 1 0;
        border: solid $success;
    }
    """
    
    def __init__(self) -> None:
        self.platform = get_platform_info()
        self.config = get_config()
        
        # Wizard state
        self.container_name: str = ""
        self.selected_distro: str = ""
        self.selected_codename: str = ""
        self.selected_arch: str = self.platform.normalized_arch
        
        super().__init__()
    
    def compose(self) -> ComposeResult:
        with Container(classes="main-container"):
            yield Static("📦 创建新容器", classes="title")
            
            # Step 1: Container name
            with Container(classes="step-container"):
                yield Static("步骤 1: 容器名称", classes="step-title")
                yield Input(
                    placeholder="输入容器名称 (如: my-debian)",
                    id="name_input",
                )
            
            # Step 2: Distribution selection
            with Container(classes="step-container"):
                yield Static("步骤 2: 选择发行版", classes="step-title")
                yield RadioSet(
                    RadioButton("Debian (推荐)", id="debian", value=True),
                    RadioButton("Ubuntu", id="ubuntu"),
                    RadioButton("Arch Linux", id="arch"),
                    RadioButton("Alpine (轻量级)", id="alpine"),
                    RadioButton("Fedora", id="fedora"),
                    RadioButton("Kali Linux", id="kali"),
                    id="distro_radio",
                )
            
            # Step 3: Version/Codename
            with Container(classes="step-container"):
                yield Static("步骤 3: 版本/代号", classes="step-title")
                yield Select(
                    [
                        ("stable (稳定版)", "stable"),
                        ("testing (测试版)", "testing"),
                        ("sid (滚动版)", "sid"),
                    ],
                    id="codename_select",
                    value="stable",
                )
            
            # Step 4: Architecture
            with Container(classes="step-container"):
                yield Static("步骤 4: 架构", classes="step-title")
                yield RadioSet(
                    RadioButton(f"{self.platform.normalized_arch} (本机)", 
                               id=f"arch_{self.platform.normalized_arch}", value=True),
                    RadioButton("arm64 (ARM 64位)", id="arch_arm64"),
                    RadioButton("amd64 (x86 64位)", id="arch_amd64"),
                    RadioButton("armhf (ARM 32位)", id="arch_armhf"),
                    id="arch_radio",
                )
            
            # Preview
            with Container(classes="preview"):
                yield Static("📋 配置预览", classes="step-title")
                yield Static(
                    f"名称: [未设置]\n"
                    f"发行版: Debian (stable)\n"
                    f"架构: {self.platform.normalized_arch}\n"
                    f"类型: proot (无需root)",
                    id="preview_text",
                )
            
            # Buttons
            with Horizontal(classes="button-row"):
                yield Button("✅ 创建容器", id="create", variant="success")
                yield Button("❌ 取消", id="cancel", variant="error")
        
        yield Footer()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle name input changes."""
        if event.input.id == "name_input":
            self.container_name = event.value
            self._update_preview()
    
    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle radio button changes."""
        if event.radio_set.id == "distro_radio":
            self.selected_distro = event.pressed.id or "debian"
            self._update_codename_options()
            self._update_preview()
        elif event.radio_set.id == "arch_radio":
            arch_id = event.pressed.id or ""
            self.selected_arch = arch_id.replace("arch_", "")
            self._update_preview()
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select changes."""
        if event.select.id == "codename_select":
            self.selected_codename = str(event.value) if event.value else "stable"
            self._update_preview()
    
    def _update_codename_options(self) -> None:
        """Update codename options based on selected distro."""
        select = self.query_one("#codename_select", Select)
        
        options = []
        match self.selected_distro:
            case "debian":
                options = [
                    ("stable (稳定版)", "stable"),
                    ("testing (测试版)", "testing"),
                    ("sid (滚动版)", "sid"),
                ]
            case "ubuntu":
                options = [
                    ("noble (24.04 LTS)", "noble"),
                    ("jammy (22.04 LTS)", "jammy"),
                    ("focal (20.04 LTS)", "focal"),
                ]
            case "arch":
                options = [("latest (滚动版)", "latest")]
            case "alpine":
                options = [
                    ("latest (最新版)", "latest"),
                    ("3.19", "3.19"),
                    ("3.18", "3.18"),
                ]
            case "fedora":
                options = [
                    ("40", "40"),
                    ("39", "39"),
                    ("rawhide (开发版)", "rawhide"),
                ]
            case "kali":
                options = [("rolling (滚动版)", "rolling")]
            case _:
                options = [("stable", "stable")]
        
        # Update select options
        select.set_options(options)
        if options:
            select.value = options[0][1]
            self.selected_codename = options[0][1]
    
    def _update_preview(self) -> None:
        """Update preview text."""
        preview = self.query_one("#preview_text", Static)
        
        name = self.container_name or "[未设置]"
        distro = self.selected_distro.capitalize() if self.selected_distro else "Debian"
        codename = self.selected_codename or "stable"
        arch = self.selected_arch or self.platform.normalized_arch
        
        preview.update(
            f"名称: {name}\n"
            f"发行版: {distro} ({codename})\n"
            f"架构: {arch}\n"
            f"类型: proot (无需root)"
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        match button_id:
            case "create":
                self._create_container()
            case "cancel":
                self.action_back()
    
    def _create_container(self) -> None:
        """Create the container."""
        if not self.container_name:
            self.notify("请输入容器名称", severity="error")
            return
        
        if not self.selected_distro:
            self.selected_distro = "debian"
        
        if not self.selected_codename:
            self.selected_codename = "stable"
        
        # Validate container name
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', self.container_name):
            self.notify("容器名称只能包含字母、数字、下划线和横线", severity="error")
            return
        
        # Show creation message
        self.notify(
            f"正在创建容器: {self.container_name}\n"
            f"发行版: {self.selected_distro} ({self.selected_codename})\n"
            f"架构: {self.selected_arch}",
            severity="information",
            timeout=5,
        )
        
        # In a real implementation, this would:
        # 1. Create container config
        # 2. Download rootfs
        # 3. Setup environment
        
        # For demo, just go back
        self.app.call_later(self.action_back)
    
    def action_back(self) -> None:
        """Go back to previous screen."""
        self.app.pop_screen()
