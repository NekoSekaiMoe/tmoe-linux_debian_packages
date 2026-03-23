"""System tools menu screen."""

from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Label,
    Static,
    TabbedContent,
    TabPane,
    Select,
    Log,
)

from tmoe.core.config import get_config
from tmoe.core.platform import get_platform_info
from tmoe.tools.system import SystemToolManager


class ToolsMenuScreen(Screen):
    """System tools menu screen with DNS, Locale, Mirror, and other utilities."""
    
    BINDINGS = [
        Binding("escape", "back", "返回"),
        Binding("q", "back", "返回"),
        Binding("1", "dns_tab", "DNS"),
        Binding("2", "locale_tab", "Locale"),
        Binding("3", "mirror_tab", "镜像"),
        Binding("4", "shell_tab", "Shell"),
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
    
    .button-grid {
        grid-size: 2;
        grid-gutter: 1;
        margin: 1 0;
    }
    
    .menu-button {
        width: 100%;
    }
    
    .log-panel {
        height: 20%;
        border: solid $surface-lighten-1;
        padding: 0 1;
        margin-top: 1;
    }
    """
    
    def __init__(self) -> None:
        self.platform = get_platform_info()
        self.config = get_config()
        self.tool_manager = SystemToolManager()
        super().__init__()
    
    def compose(self) -> ComposeResult:
        with Container(classes="main-container"):
            yield Static("🔧 系统工具", classes="title")
            
            with TabbedContent():
                # DNS Tab
                with TabPane("🌐 DNS配置 [1]", id="tab_dns"):
                    yield self._create_dns_section()
                
                # Locale Tab
                with TabPane("🌍 Locale语言 [2]", id="tab_locale"):
                    yield self._create_locale_section()
                
                # Mirror Tab
                with TabPane("🪞 镜像源 [3]", id="tab_mirror"):
                    yield self._create_mirror_section()
                
                # Shell Tab
                with TabPane("🐚 Shell工具 [4]", id="tab_shell"):
                    yield self._create_shell_section()
                
                # System Tab
                with TabPane("⚙️ 系统优化", id="tab_system"):
                    yield self._create_system_section()
            
            # Log panel
            with Container(classes="log-panel"):
                yield Static("操作日志:")
                yield Log(id="tools_log")
        
        yield Footer()
    
    def _create_dns_section(self) -> Container:
        """Create DNS configuration section."""
        return Container(
            Static("🌐 DNS 服务器配置", classes="section-title"),
            Static("选择 DNS 服务器:"),
            Grid(
                Button("🔍 Google DNS (8.8.8.8)", id="dns_google", variant="primary"),
                Button("☁️ Cloudflare (1.1.1.1)", id="dns_cloudflare", variant="primary"),
                Button("🇨🇳 阿里 DNS (223.5.5.5)", id="dns_ali"),
                Button("🇨🇳 百度 DNS (180.76.76.76)", id="dns_baidu"),
                Button("🇨🇳 清华 TUNA", id="dns_tuna"),
                Button("📋 114 DNS", id="dns_114"),
                classes="button-grid",
            ),
            classes="section",
        )
    
    def _create_locale_section(self) -> Container:
        """Create Locale configuration section."""
        return Container(
            Static("🌍 Locale 语言配置", classes="section-title"),
            Static("选择系统语言:"),
            Grid(
                Button("🇨🇳 简体中文 (zh_CN.UTF-8)", id="locale_zh_cn", variant="primary"),
                Button("🇹🇼 繁體中文 (zh_TW.UTF-8)", id="locale_zh_tw"),
                Button("🇭🇰 香港繁體 (zh_HK.UTF-8)", id="locale_zh_hk"),
                Button("🇺🇸 English (en_US.UTF-8)", id="locale_en_us"),
                Button("🇬🇧 English UK (en_GB.UTF-8)", id="locale_en_gb"),
                Button("🇯🇵 日本語 (ja_JP.UTF-8)", id="locale_ja_jp"),
                Button("🇰🇷 한국어 (ko_KR.UTF-8)", id="locale_ko_kr"),
                Button("🇩🇪 Deutsch (de_DE.UTF-8)", id="locale_de_de"),
                classes="button-grid",
            ),
            classes="section",
        )
    
    def _create_mirror_section(self) -> Container:
        """Create mirror source section."""
        return Container(
            Static("🪞 软件源镜像配置", classes="section-title"),
            Static("选择镜像源 (中国境内推荐):"),
            Grid(
                Button("🎓 清华大学 (TUNA)", id="mirror_tsinghua", variant="primary"),
                Button("🔬 中科大 (USTC)", id="mirror_ustc", variant="primary"),
                Button("☁️ 阿里云", id="mirror_aliyun"),
                Button("🐧 腾讯云", id="mirror_tencent"),
                Button("🌐 华为云", id="mirror_huawei"),
                Button("📡 网易", id="mirror_163"),
                Button("🌍 官方源 (Global)", id="mirror_global"),
                Button("🔄 自动测速选择", id="mirror_auto"),
                classes="button-grid",
            ),
            classes="section",
        )
    
    def _create_shell_section(self) -> Container:
        """Create shell tools section."""
        return Container(
            Static("🐚 Shell 与终端工具", classes="section-title"),
            Grid(
                Button("🐚 安装 Zsh", id="shell_zsh", variant="primary"),
                Button("🐟 安装 Fish", id="shell_fish", variant="primary"),
                Button("✨ Oh My Zsh", id="shell_ohmyzsh"),
                Button("🎣 Fisher (Fish插件)", id="shell_fisher"),
                Button("📟 Tmux", id="shell_tmux"),
                Button("🖥️ htop", id="shell_htop"),
                classes="button-grid",
            ),
            classes="section",
        )
    
    def _create_system_section(self) -> Container:
        """Create system optimization section."""
        return Container(
            Static("⚙️ 系统优化", classes="section-title"),
            Grid(
                Button("🧹 清理系统垃圾", id="sys_clean", variant="primary"),
                Button("💾 设置 SWAP", id="sys_swap"),
                Button("🚀 优化内核参数", id="sys_optimize"),
                Button("📊 系统信息", id="sys_info"),
                classes="button-grid",
            ),
            classes="section",
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        if not button_id:
            return
        
        if button_id.startswith("dns_"):
            dns_provider = button_id.replace("dns_", "")
            self.run_worker(self._set_dns(dns_provider))
        elif button_id.startswith("locale_"):
            locale = button_id.replace("locale_", "").replace("_", "_")
            locale_map = {
                "zh_cn": "zh_CN.UTF-8",
                "zh_tw": "zh_TW.UTF-8",
                "zh_hk": "zh_HK.UTF-8",
                "en_us": "en_US.UTF-8",
                "en_gb": "en_GB.UTF-8",
                "ja_jp": "ja_JP.UTF-8",
                "ko_kr": "ko_KR.UTF-8",
                "de_de": "de_DE.UTF-8",
            }
            full_locale = locale_map.get(locale, locale)
            self.run_worker(self._set_locale(full_locale))
        elif button_id.startswith("mirror_"):
            mirror = button_id.replace("mirror_", "")
            self.run_worker(self._set_mirror(mirror))
        elif button_id.startswith("shell_"):
            tool = button_id.replace("shell_", "")
            self.run_worker(self._install_shell_tool(tool))
        elif button_id.startswith("sys_"):
            action = button_id.replace("sys_", "")
            self.run_worker(self._system_action(action))
    
    async def _set_dns(self, provider: str) -> None:
        """Set DNS server."""
        self._log(f"正在设置 DNS: {provider}...")
        try:
            success = await self.tool_manager.set_dns(provider)
            if success:
                self._log(f"✅ DNS 已设置为 {provider}")
                self.notify(f"DNS 已设置为 {provider}", severity="success")
            else:
                self._log(f"⚠️ DNS 设置失败")
                self.notify("DNS 设置失败", severity="error")
        except Exception as e:
            self._log(f"❌ 错误: {e}")
            self.notify(f"错误: {e}", severity="error")
    
    async def _set_locale(self, locale: str) -> None:
        """Set system locale."""
        self._log(f"正在设置 Locale: {locale}...")
        try:
            success = await self.tool_manager.set_locale(locale)
            if success:
                self._log(f"✅ Locale 已设置为 {locale}")
                self.notify(f"Locale 已设置为 {locale}", severity="success")
            else:
                self._log(f"⚠️ Locale 设置失败")
                self.notify("Locale 设置失败", severity="error")
        except Exception as e:
            self._log(f"❌ 错误: {e}")
            self.notify(f"错误: {e}", severity="error")
    
    async def _set_mirror(self, mirror: str) -> None:
        """Set package mirror."""
        self._log(f"正在设置镜像源: {mirror}...")
        try:
            if mirror == "auto":
                self._log("正在测速选择最快镜像...")
                # TODO: Implement auto mirror selection
                self.notify("自动测速功能开发中", severity="information")
            else:
                success = await self.tool_manager.set_mirror(mirror)
                if success:
                    self._log(f"✅ 镜像源已设置为 {mirror}")
                    self.notify(f"镜像源已设置为 {mirror}", severity="success")
                else:
                    self._log(f"⚠️ 镜像源设置失败")
                    self.notify("镜像源设置失败", severity="error")
        except Exception as e:
            self._log(f"❌ 错误: {e}")
            self.notify(f"错误: {e}", severity="error")
    
    async def _install_shell_tool(self, tool: str) -> None:
        """Install shell tool."""
        self._log(f"正在安装 {tool}...")
        try:
            match tool:
                case "zsh":
                    success = await self.tool_manager.install_zsh()
                case "fish":
                    success = await self.tool_manager.install_fish()
                case "ohmyzsh":
                    success = await self.tool_manager.configure_zsh_ohmyzsh()
                case "fisher":
                    success = await self.tool_manager.install_fisher()
                case "tmux":
                    success = await self.tool_manager.install_tmux()
                    if success:
                        await self.tool_manager.configure_tmux()
                case "htop":
                    success = await self.tool_manager.install_monitoring_tools()
                case _:
                    success = False
            
            if success:
                self._log(f"✅ {tool} 安装完成")
                self.notify(f"{tool} 安装完成", severity="success")
            else:
                self._log(f"⚠️ {tool} 安装失败")
                self.notify(f"{tool} 安装失败", severity="error")
        except Exception as e:
            self._log(f"❌ 错误: {e}")
            self.notify(f"错误: {e}", severity="error")
    
    async def _system_action(self, action: str) -> None:
        """Perform system action."""
        self._log(f"正在执行: {action}...")
        try:
            match action:
                case "clean":
                    self._log("清理系统垃圾...")
                    # TODO: Implement system cleanup
                    self.notify("系统清理功能开发中", severity="information")
                case "swap":
                    self._log("配置 SWAP...")
                    # TODO: Implement SWAP configuration
                    self.notify("SWAP 配置功能开发中", severity="information")
                case "optimize":
                    success = await self.tool_manager.optimize_system()
                    if success:
                        self._log("✅ 系统优化完成")
                        self.notify("系统优化完成", severity="success")
                    else:
                        self._log("⚠️ 系统优化失败")
                        self.notify("系统优化失败", severity="error")
                case "info":
                    self._log(f"系统信息:")
                    self._log(f"  平台: {self.platform.normalized_arch}")
                    self._log(f"  Android: {self.platform.is_android}")
                    self._log(f"  Termux: {self.platform.is_termux}")
                    self._log(f"  WSL: {self.platform.is_wsl}")
                    self.notify("系统信息已显示", severity="information")
        except Exception as e:
            self._log(f"❌ 错误: {e}")
            self.notify(f"错误: {e}", severity="error")
    
    def _log(self, message: str) -> None:
        """Add message to log."""
        log = self.query_one("#tools_log", Log)
        log.write_line(message)
    
    def action_back(self) -> None:
        """Go back to main menu."""
        self.app.pop_screen()
    
    def action_dns_tab(self) -> None:
        """Switch to DNS tab."""
        tabs = self.query_one(TabbedContent)
        tabs.active = "tab_dns"
    
    def action_locale_tab(self) -> None:
        """Switch to Locale tab."""
        tabs = self.query_one(TabbedContent)
        tabs.active = "tab_locale"
    
    def action_mirror_tab(self) -> None:
        """Switch to Mirror tab."""
        tabs = self.query_one(TabbedContent)
        tabs.active = "tab_mirror"
    
    def action_shell_tab(self) -> None:
        """Switch to Shell tab."""
        tabs = self.query_one(TabbedContent)
        tabs.active = "tab_shell"
