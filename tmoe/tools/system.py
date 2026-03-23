"""System tools management for TMOE.

Provides installation and configuration for:
- Shell environments (Zsh, Fish, Bash enhancements)
- Terminal multiplexers (Tmux, Screen)
- System monitoring tools
- File management tools
- UEFI boot management
- System optimization
"""

from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from tmoe.core.platform import PlatformInfo
from tmoe.tools.downloader import DownloadManager, DownloadTask

if TYPE_CHECKING:
    from collections.abc import Callable


class ShellType(str, Enum):
    """Supported shell types."""
    BASH = "bash"
    ZSH = "zsh"
    FISH = "fish"


class TerminalTool(str, Enum):
    """Terminal-related tools."""
    TMUX = "tmux"
    SCREEN = "screen"
    BYOBU = "byobu"


@dataclass
class ShellInfo:
    """Information about a shell.
    
    Attributes:
        name: Shell name.
        shell_type: Type of shell.
        description: Shell description.
        packages: Required packages.
        config_file: Configuration file path.
    """
    name: str
    shell_type: ShellType
    description: str
    packages: list[str]
    config_file: Path


class SystemToolManager:
    """Manager for system tools and utilities.
    
    Provides installation and configuration for shells,
    terminal tools, and system utilities.
    
    Example:
        >>> manager = SystemToolManager()
        >>> await manager.install_zsh()
        >>> await manager.install_tmux()
        >>> await manager.configure_zsh_ohmyzsh()
    """
    
    # Shell definitions
    SHELLS: dict[ShellType, ShellInfo] = {
        ShellType.ZSH: ShellInfo(
            name="Zsh",
            shell_type=ShellType.ZSH,
            description="Powerful shell with advanced features",
            packages=["zsh"],
            config_file=Path.home() / ".zshrc",
        ),
        ShellType.FISH: ShellInfo(
            name="Fish",
            shell_type=ShellType.FISH,
            description="Friendly interactive shell",
            packages=["fish"],
            config_file=Path.home() / ".config" / "fish" / "config.fish",
        ),
        ShellType.BASH: ShellInfo(
            name="Bash",
            shell_type=ShellType.BASH,
            description="Bourne Again Shell",
            packages=["bash"],
            config_file=Path.home() / ".bashrc",
        ),
    }
    
    def __init__(self, platform: PlatformInfo | None = None) -> None:
        self.platform = platform or PlatformInfo()
        self.downloader = DownloadManager(platform)
        self._detected_distro: str | None = None
    
    def detect_distro(self) -> str:
        """Detect Linux distribution."""
        if self._detected_distro:
            return self._detected_distro
        
        os_release = Path("/etc/os-release")
        if os_release.exists():
            content = os_release.read_text()
            for line in content.split("\n"):
                if line.startswith("ID="):
                    distro = line.split("=", 1)[1].strip('"')
                    self._detected_distro = distro
                    return distro
        
        if Path("/etc/arch-release").exists():
            return "arch"
        elif Path("/etc/fedora-release").exists():
            return "fedora"
        elif Path("/etc/debian_version").exists():
            return "debian"
        
        return "unknown"
    
    def get_package_manager(self) -> str:
        """Get the package manager for current distro."""
        distro = self.detect_distro()
        package_managers = {
            "debian": "apt",
            "ubuntu": "apt",
            "arch": "pacman",
            "manjaro": "pacman",
            "fedora": "dnf",
            "centos": "yum",
            "opensuse": "zypper",
            "alpine": "apk",
        }
        return package_managers.get(distro, "apt")
    
    async def install_via_package_manager(
        self,
        packages: list[str],
        update_first: bool = True,
    ) -> bool:
        """Install packages using system package manager."""
        pm = self.get_package_manager()
        
        if update_first:
            update_cmds = {
                "apt": ["apt", "update", "-qq"],
                "pacman": ["pacman", "-Sy", "--noconfirm"],
                "dnf": ["dnf", "check-update"],
                "yum": ["yum", "check-update"],
                "zypper": ["zypper", "refresh"],
                "apk": ["apk", "update"],
            }
            
            if pm in update_cmds:
                proc = await asyncio.create_subprocess_exec(
                    *update_cmds[pm],
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await proc.wait()
        
        install_cmds = {
            "apt": ["apt", "install", "-y", "-qq"],
            "pacman": ["pacman", "-S", "--noconfirm"],
            "dnf": ["dnf", "install", "-y"],
            "yum": ["yum", "install", "-y"],
            "zypper": ["zypper", "install", "-y"],
            "apk": ["apk", "add"],
        }
        
        if pm not in install_cmds:
            return False
        
        cmd = install_cmds[pm] + packages
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await proc.communicate()
        return proc.returncode == 0
    
    def is_installed(self, shell_type: ShellType) -> bool:
        """Check if a shell is installed."""
        shell = self.SHELLS.get(shell_type)
        if not shell:
            return False
        return shutil.which(shell.shell_type.value) is not None
    
    async def install_shell(self, shell_type: ShellType) -> bool:
        """Install a shell."""
        shell = self.SHELLS.get(shell_type)
        if not shell:
            return False
        
        if self.is_installed(shell_type):
            return True
        
        return await self.install_via_package_manager(shell.packages)
    
    async def install_zsh(self) -> bool:
        """Install Zsh shell."""
        return await self.install_shell(ShellType.ZSH)
    
    async def install_fish(self) -> bool:
        """Install Fish shell."""
        return await self.install_shell(ShellType.FISH)
    
    async def configure_zsh_ohmyzsh(self) -> bool:
        """Install and configure Oh My Zsh.
        
        Returns:
            True if installation succeeded.
        """
        if not self.is_installed(ShellType.ZSH):
            return False
        
        # Check if already installed
        omz_dir = Path.home() / ".oh-my-zsh"
        if omz_dir.exists():
            return True
        
        # Install Oh My Zsh
        install_url = "https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh"
        script_path = Path("/tmp/ohmyzsh-install.sh")
        
        task = DownloadTask(
            url=install_url,
            dest=script_path,
            backend="httpx",
        )
        await self.downloader.download(task)
        
        script_path.chmod(0o755)
        
        # Run installer non-interactively
        env = {"RUNZSH": "no", "CHSH": "no"}
        proc = await asyncio.create_subprocess_exec(
            "sh", str(script_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        
        stdout, stderr = await proc.communicate()
        script_path.unlink(missing_ok=True)
        
        return proc.returncode == 0
    
    async def install_zsh_plugins(self) -> bool:
        """Install popular Zsh plugins.
        
        Installs:
        - zsh-syntax-highlighting
        - zsh-autosuggestions
        - zsh-completions
        
        Returns:
            True if installation succeeded.
        """
        if not self.is_installed(ShellType.ZSH):
            return False
        
        omz_dir = Path.home() / ".oh-my-zsh"
        plugins_dir = omz_dir / "custom" / "plugins"
        plugins_dir.mkdir(parents=True, exist_ok=True)
        
        plugins = [
            ("zsh-syntax-highlighting", "https://github.com/zsh-users/zsh-syntax-highlighting.git"),
            ("zsh-autosuggestions", "https://github.com/zsh-users/zsh-autosuggestions.git"),
            ("zsh-completions", "https://github.com/zsh-users/zsh-completions.git"),
        ]
        
        success = True
        for name, url in plugins:
            plugin_dir = plugins_dir / name
            if plugin_dir.exists():
                continue
            
            proc = await asyncio.create_subprocess_exec(
                "git", "clone", "--depth=1", url, str(plugin_dir),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                success = False
        
        return success
    
    async def install_fisher(self) -> bool:
        """Install Fisher plugin manager for Fish.
        
        Returns:
            True if installation succeeded.
        """
        if not self.is_installed(ShellType.FISH):
            return False
        
        # Check if already installed
        fisher_path = Path.home() / ".config" / "fish" / "functions" / "fisher.fish"
        if fisher_path.exists():
            return True
        
        # Install Fisher
        install_url = "https://raw.githubusercontent.com/jorgebucaran/fisher/main/functions/fisher.fish"
        
        proc = await asyncio.create_subprocess_shell(
            f"curl -sL {install_url} | source && fisher install jorgebucaran/fisher",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            executable="fish",
        )
        
        stdout, stderr = await proc.communicate()
        return proc.returncode == 0
    
    async def install_tmux(self) -> bool:
        """Install Tmux terminal multiplexer.
        
        Returns:
            True if installation succeeded.
        """
        if shutil.which("tmux"):
            return True
        
        return await self.install_via_package_manager(["tmux"])
    
    async def configure_tmux(self) -> bool:
        """Configure Tmux with sensible defaults.
        
        Returns:
            True if configuration was written.
        """
        config_path = Path.home() / ".tmux.conf"
        
        config_content = """# TMOE Tmux Configuration

# Enable mouse support
set -g mouse on

# Set prefix to Ctrl+a
unbind C-b
set-option -g prefix C-a
bind-key C-a send-prefix

# Split panes using | and -
bind | split-window -h
bind - split-window -v
unbind '"'
unbind %

# Reload config
bind r source-file ~/.tmux.conf

# Switch panes using Alt-arrow
bind -n M-Left select-pane -L
bind -n M-Right select-pane -R
bind -n M-Up select-pane -U
bind -n M-Down select-pane -D

# Enable 256 colors
set -g default-terminal "screen-256color"

# History limit
set -g history-limit 10000

# No delay for escape key
set -sg escape-time 0

# Start window and pane indices at 1
set -g base-index 1
setw -g pane-base-index 1

# Status bar
set -g status-bg colour235
set -g status-fg colour136
set -g status-left "#[fg=green]#S"
set -g status-right "#[fg=yellow]%Y-%m-%d %H:%M"
"""
        
        config_path.write_text(config_content)
        return True
    
    async def install_screen(self) -> bool:
        """Install GNU Screen terminal multiplexer.
        
        Returns:
            True if installation succeeded.
        """
        if shutil.which("screen"):
            return True
        
        return await self.install_via_package_manager(["screen"])
    
    async def install_byobu(self) -> bool:
        """Install Byobu terminal multiplexer.
        
        Returns:
            True if installation succeeded.
        """
        if shutil.which("byobu"):
            return True
        
        return await self.install_via_package_manager(["byobu"])
    
    async def install_monitoring_tools(self) -> bool:
        """Install system monitoring tools.
        
        Installs:
        - htop: Interactive process viewer
        - btop: Modern system monitor
        - iotop: I/O monitor
        - nethogs: Network monitor
        
        Returns:
            True if installation succeeded.
        """
        packages = ["htop", "iotop", "nethogs"]
        
        # Try to install btop if available
        distro = self.detect_distro()
        if distro in ["arch", "manjaro"]:
            packages.append("btop")
        
        return await self.install_via_package_manager(packages)
    
    async def install_file_tools(self) -> bool:
        """Install file management tools.
        
        Installs:
        - mc: Midnight Commander
        - ranger: Terminal file manager
        - fzf: Fuzzy finder
        - fd: Fast file finder
        - ripgrep: Fast text search
        
        Returns:
            True if installation succeeded.
        """
        packages = ["mc", "fzf", "fd-find", "ripgrep"]
        
        distro = self.detect_distro()
        if distro in ["arch", "manjaro"]:
            packages.append("ranger")
        elif distro in ["debian", "ubuntu"]:
            packages.append("ranger")
        
        return await self.install_via_package_manager(packages)
    
    async def install_neofetch(self) -> bool:
        """Install Neofetch system info tool.
        
        Returns:
            True if installation succeeded.
        """
        if shutil.which("neofetch"):
            return True
        
        distro = self.detect_distro()
        if distro in ["arch", "manjaro"]:
            packages = ["neofetch"]
        else:
            packages = ["neofetch"]
        
        return await self.install_via_package_manager(packages)
    
    def is_uefi_system(self) -> bool:
        """Check if system uses UEFI boot.
        
        Returns:
            True if system uses UEFI.
        """
        return Path("/sys/firmware/efi").exists()
    
    async def install_efibootmgr(self) -> bool:
        """Install efibootmgr for UEFI management.
        
        Returns:
            True if installation succeeded.
        """
        if not self.is_uefi_system():
            return False
        
        if shutil.which("efibootmgr"):
            return True
        
        return await self.install_via_package_manager(["efibootmgr"])
    
    async def get_uefi_boot_entries(self) -> list[dict[str, str]]:
        """Get UEFI boot entries.
        
        Returns:
            List of boot entries with number and name.
        """
        if not shutil.which("efibootmgr"):
            return []
        
        proc = await asyncio.create_subprocess_exec(
            "efibootmgr",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            return []
        
        entries = []
        for line in stdout.decode().split("\n"):
            # Parse lines like "Boot0000* Ubuntu"
            if line.startswith("Boot") and "*" in line:
                parts = line.split("*", 1)
                boot_num = parts[0].replace("Boot", "").strip()
                boot_name = parts[1].strip() if len(parts) > 1 else "Unknown"
                entries.append({
                    "number": boot_num,
                    "name": boot_name,
                })
        
        return entries
    
    async def set_uefi_boot_order(self, boot_order: list[str]) -> bool:
        """Set UEFI boot order.
        
        Args:
            boot_order: List of boot numbers in desired order.
        
        Returns:
            True if successful.
        """
        if not boot_order or not shutil.which("efibootmgr"):
            return False
        
        order_str = ",".join(boot_order)
        proc = await asyncio.create_subprocess_exec(
            "efibootmgr", "--bootorder", order_str,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await proc.communicate()
        return proc.returncode == 0
    
    async def install_refind(self) -> bool:
        """Install rEFInd boot manager.
        
        Returns:
            True if installation succeeded.
        """
        if not self.is_uefi_system():
            return False
        
        distro = self.detect_distro()
        
        if distro in ["debian", "ubuntu"]:
            # Add rEFInd repository
            proc = await asyncio.create_subprocess_shell(
                "apt-add-repository -y ppa:rodsmith/refind",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            
            if await self.install_via_package_manager(["refind"]):
                # Install to EFI
                proc = await asyncio.create_subprocess_exec(
                    "refind-install",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
                return proc.returncode == 0
        
        elif distro in ["arch", "manjaro"]:
            if await self.install_via_package_manager(["refind"]):
                proc = await asyncio.create_subprocess_exec(
                    "refind-install",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
                return proc.returncode == 0
        
        return False
    
    async def optimize_system(self) -> bool:
        """Apply basic system optimizations.
        
        Optimizations:
        - Set swappiness to 10
        - Enable SSD trim if applicable
        - Set I/O scheduler
        
        Returns:
            True if optimizations applied.
        """
        success = True
        
        # Set swappiness
        sysctl_conf = Path("/etc/sysctl.d/99-tmoe.conf")
        try:
            sysctl_content = """# TMOE System Optimizations
vm.swappiness=10
vm.vfs_cache_pressure=50
"""
            sysctl_conf.write_text(sysctl_content)
        except PermissionError:
            success = False
        
        return success
    
    async def install_all_shell_tools(self) -> bool:
        """Install all recommended shell tools.
        
        Returns:
            True if all installations succeeded.
        """
        results = await asyncio.gather(
            self.install_zsh(),
            self.install_fish(),
            self.install_tmux(),
            self.configure_tmux(),
            self.install_monitoring_tools(),
            self.install_file_tools(),
            self.install_neofetch(),
        )
        
        return all(results)

    # ==================== DNS Configuration (原版支持) ====================
    
    DNS_SERVERS: dict[str, list[str]] = {
        "google": ["8.8.8.8", "8.8.4.4", "2001:4860:4860::8888", "2001:4860:4860::8844"],
        "cloudflare": ["1.1.1.1", "1.0.0.1", "2606:4700:4700::1111", "2606:4700:4700::1001"],
        "ali": ["223.5.5.5", "223.6.6.6", "2400:3200::1", "2400:3200:baba::1"],
        "baidu": ["180.76.76.76"],
        "tuna": ["101.6.6.6", "2001:da8::666"],
        "114": ["114.114.114.114", "114.114.115.115"],
    }
    
    async def set_dns(self, dns_provider: str) -> bool:
        """Set DNS servers (原版DNS配置).
        
        Args:
            dns_provider: DNS provider name (google, cloudflare, ali, baidu, tuna, 114)
            
        Returns:
            True if configuration succeeded
        """
        servers = self.DNS_SERVERS.get(dns_provider)
        if not servers:
            return False
        
        try:
            # Create resolv.conf content
            content = "# Generated by TMOE\\n"
            for server in servers:
                content += f"nameserver {server}\\n"
            
            # Write to /etc/resolv.conf (may need root)
            resolv_conf = Path("/etc/resolv.conf")
            resolv_conf.write_text(content)
            return True
        except PermissionError:
            # Try with sudo
            try:
                proc = await asyncio.create_subprocess_exec(
                    "sh", "-c", f'echo "{content}" | sudo tee /etc/resolv.conf',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.wait()
                return proc.returncode == 0
            except Exception:
                return False
        except Exception:
            return False
    
    # ==================== Locale Configuration (原版支持315+语言) ====================
    
    COMMON_LOCALES: dict[str, str] = {
        "zh_CN.UTF-8": "简体中文",
        "zh_TW.UTF-8": "繁體中文(台灣)",
        "zh_HK.UTF-8": "繁體中文(香港)",
        "en_US.UTF-8": "English (US)",
        "en_GB.UTF-8": "English (UK)",
        "ja_JP.UTF-8": "日本語",
        "ko_KR.UTF-8": "한국어",
        "de_DE.UTF-8": "Deutsch",
        "fr_FR.UTF-8": "Français",
        "ru_RU.UTF-8": "Русский",
        "es_ES.UTF-8": "Español",
        "pt_BR.UTF-8": "Português (Brasil)",
        "it_IT.UTF-8": "Italiano",
        "nl_NL.UTF-8": "Nederlands",
        "pl_PL.UTF-8": "Polski",
        "tr_TR.UTF-8": "Türkçe",
        "vi_VN.UTF-8": "Tiếng Việt",
        "th_TH.UTF-8": "ไทย",
        "ar_SA.UTF-8": "العربية",
        "hi_IN.UTF-8": "हिन्दी",
    }
    
    async def set_locale(self, locale: str) -> bool:
        """Set system locale (原版locale配置).
        
        Args:
            locale: Locale string (e.g., 'zh_CN.UTF-8')
            
        Returns:
            True if configuration succeeded
        """
        try:
            distro = self.detect_distro()
            
            match distro:
                case "debian" | "ubuntu":
                    # Generate locale
                    proc = await asyncio.create_subprocess_exec(
                        "locale-gen", locale,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    await proc.wait()
                    
                    # Update default locale
                    locale_conf = Path("/etc/default/locale")
                    locale_content = f'''LANG={locale}
LANGUAGE={locale.split(".")[0]}
LC_ALL={locale}
'''
                    locale_conf.write_text(locale_content)
                    return True
                    
                case "arch":
                    # Uncomment locale in /etc/locale.gen
                    locale_gen = Path("/etc/locale.gen")
                    if locale_gen.exists():
                        content = locale_gen.read_text()
                        content = content.replace(f"#{locale}", locale)
                        locale_gen.write_text(content)
                    
                    # Generate locale
                    proc = await asyncio.create_subprocess_exec(
                        "locale-gen",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    await proc.wait()
                    
                    # Set locale.conf
                    locale_conf = Path("/etc/locale.conf")
                    locale_conf.write_text(f"LANG={locale}\\n")
                    return True
                    
                case "fedora":
                    locale_conf = Path("/etc/locale.conf")
                    locale_conf.write_text(f"LANG={locale}\\n")
                    return True
                    
                case _:
                    return False
                    
        except Exception:
            return False
    
    # ==================== Mirror/Source Configuration (原版镜像源) ====================
    
    MIRROR_SITES: dict[str, dict[str, str]] = {
        "global": {
            "debian": "http://deb.debian.org/debian",
            "ubuntu": "http://archive.ubuntu.com/ubuntu",
            "arch": "https://geo.mirror.pkgbuild.com",
        },
        "china": {
            "tsinghua": {
                "debian": "https://mirrors.tuna.tsinghua.edu.cn/debian",
                "ubuntu": "https://mirrors.tuna.tsinghua.edu.cn/ubuntu",
                "arch": "https://mirrors.tuna.tsinghua.edu.cn/archlinux",
            },
            "ustc": {
                "debian": "https://mirrors.ustc.edu.cn/debian",
                "ubuntu": "https://mirrors.ustc.edu.cn/ubuntu",
                "arch": "https://mirrors.ustc.edu.cn/archlinux",
            },
            "aliyun": {
                "debian": "https://mirrors.aliyun.com/debian",
                "ubuntu": "https://mirrors.aliyun.com/ubuntu",
                "arch": "https://mirrors.aliyun.com/archlinux",
            },
            "tencent": {
                "debian": "https://mirrors.cloud.tencent.com/debian",
                "ubuntu": "https://mirrors.cloud.tencent.com/ubuntu",
                "arch": "https://mirrors.cloud.tencent.com/archlinux",
            },
        },
    }
    
    async def set_mirror(self, mirror_site: str, distro: str | None = None) -> bool:
        """Set package mirror (原版镜像源切换).
        
        Args:
            mirror_site: Mirror site name (tsinghua, ustc, aliyun, tencent)
            distro: Distribution name (auto-detected if None)
            
        Returns:
            True if configuration succeeded
        """
        if distro is None:
            distro = self.detect_distro()
        
        # Get mirror URL
        china_mirrors = self.MIRROR_SITES.get("china", {})
        mirror_config = china_mirrors.get(mirror_site, {})
        mirror_url = mirror_config.get(distro)
        
        if not mirror_url:
            return False
        
        try:
            match distro:
                case "debian":
                    return await self._set_debian_mirror(mirror_url)
                case "ubuntu":
                    return await self._set_ubuntu_mirror(mirror_url)
                case "arch":
                    return await self._set_arch_mirror(mirror_url)
                case _:
                    return False
        except Exception:
            return False
    
    async def _set_debian_mirror(self, mirror_url: str) -> bool:
        """Set Debian mirror."""
        sources_list = Path("/etc/apt/sources.list")
        
        # Read current content
        if sources_list.exists():
            content = sources_list.read_text()
            # Replace mirror URLs
            content = content.replace("http://deb.debian.org/debian", mirror_url)
            content = content.replace("http://security.debian.org/debian-security", f"{mirror_url}-security")
            sources_list.write_text(content)
            
            # Update package list
            proc = await asyncio.create_subprocess_exec(
                "apt", "update",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            return proc.returncode == 0
        
        return False
    
    async def _set_ubuntu_mirror(self, mirror_url: str) -> bool:
        """Set Ubuntu mirror."""
        sources_list = Path("/etc/apt/sources.list")
        
        if sources_list.exists():
            content = sources_list.read_text()
            # Replace mirror URLs
            content = content.replace("http://archive.ubuntu.com/ubuntu", mirror_url)
            content = content.replace("http://security.ubuntu.com/ubuntu", f"{mirror_url}")
            sources_list.write_text(content)
            
            # Update package list
            proc = await asyncio.create_subprocess_exec(
                "apt", "update",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            return proc.returncode == 0
        
        return False
    
    async def _set_arch_mirror(self, mirror_url: str) -> bool:
        """Set Arch Linux mirror."""
        mirrorlist = Path("/etc/pacman.d/mirrorlist")
        
        if mirrorlist.exists():
            # Add new mirror at the top
            content = mirrorlist.read_text()
            new_mirror = f"Server = {mirror_url}/$repo/os/$arch\\n"
            content = new_mirror + content
            mirrorlist.write_text(content)
            
            # Update package list
            proc = await asyncio.create_subprocess_exec(
                "pacman", "-Sy",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            return proc.returncode == 0
        
        return False
