"""Configuration management for TMOE.

Uses Pydantic for type-safe configuration.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from tmoe.core.constants import (
    DEFAULT_LOCALES,
    SUPPORTED_ARCHITECTURES,
)
from tmoe.core.platform import PlatformInfo


@dataclass
class ContainerConfig:
    """Configuration for a single container."""
    
    name: str
    distro: str
    arch: str
    codename: str | None = None
    rootfs_path: Path | None = None
    container_type: str = "proot"
    
    # User settings
    user: str = "root"
    uid: int = 0
    gid: int = 0
    home: str = "/root"
    
    # Display settings
    display: str = ":2"
    vnc_port: int = 5902
    novnc_port: int = 36080
    
    # Mount settings
    mount_sd: bool = True
    mount_termux: bool = True
    mount_system: bool = True
    mount_apex: bool = True
    custom_mounts: list[dict[str, str]] = field(default_factory=list)
    
    # Feature flags (原版支持的高级配置)
    link2symlink: bool = True
    sysvipc: bool = True
    kill_on_exit: bool = True
    fake_kernel: bool = True
    fake_kernel_version: str = "6.1.0-tmoe"
    fix_lowercase: bool = True  # -L flag for case-insensitive filesystem
    
    # QEMU cross-architecture support
    qemu_enabled: bool = False
    qemu_arch: str | None = None
    qemu_bin: str | None = None
    
    # Proot binary settings (原版支持自定义proot路径)
    proot_bin: str = "proot"  # default, 32, compatible
    
    # User/identity settings
    fix_id: bool = True  # 修复 uid/gid
    fake_id: str | None = None  # 伪装用户ID
    
    # Network settings
    isolated_network: bool = False
    
    # .Net 6+ compatible mode
    dotnet_compatible: bool = False
    
    def __post_init__(self) -> None:
        """Validate architecture."""
        normalized = self.arch.lower().replace("-", "_")
        if normalized not in SUPPORTED_ARCHITECTURES:
            raise ValueError(f"Unsupported architecture: {self.arch}")
        self.arch = normalized
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "distro": self.distro,
            "arch": self.arch,
            "codename": self.codename,
            "rootfs_path": str(self.rootfs_path) if self.rootfs_path else None,
            "container_type": self.container_type,
            "user": self.user,
            "uid": self.uid,
            "gid": self.gid,
            "home": self.home,
            "display": self.display,
            "vnc_port": self.vnc_port,
            "novnc_port": self.novnc_port,
            "mount_sd": self.mount_sd,
            "mount_termux": self.mount_termux,
            "mount_system": self.mount_system,
            "mount_apex": self.mount_apex,
            "custom_mounts": self.custom_mounts,
            "link2symlink": self.link2symlink,
            "sysvipc": self.sysvipc,
            "kill_on_exit": self.kill_on_exit,
            "fake_kernel": self.fake_kernel,
            "fake_kernel_version": self.fake_kernel_version,
            "fix_lowercase": self.fix_lowercase,
            "qemu_enabled": self.qemu_enabled,
            "qemu_arch": self.qemu_arch,
            "qemu_bin": self.qemu_bin,
            "proot_bin": self.proot_bin,
            "fix_id": self.fix_id,
            "fake_id": self.fake_id,
            "isolated_network": self.isolated_network,
            "dotnet_compatible": self.dotnet_compatible,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContainerConfig:
        """Create from dictionary."""
        if data.get("rootfs_path"):
            data["rootfs_path"] = Path(data["rootfs_path"])
        return cls(**data)


@dataclass
class TmoeConfig:
    """Global TMOE configuration."""
    
    # Version
    version: str = "2.0.0"
    
    # Locale settings
    locale: str = "zh_CN.UTF-8"
    language: str = "zh_CN"
    
    # Default container settings
    default_container_type: str = "proot"
    default_arch: str | None = None
    default_distro: str = "debian"
    default_codename: str = "stable"
    
    # VNC settings
    vnc_server: str = "tiger"
    vnc_resolution: str = "1440x720"
    vnc_display: int = 2
    vnc_depth: int = 24
    vnc_localhost: bool = False
    
    # GUI settings
    default_desktop: str = "xfce"
    
    # Mirror settings
    mirror_region: str = "global"
    mirror_site: str | None = None
    
    # Network settings
    pulse_server: str = "127.0.0.1"
    pulse_port: int = 4713
    
    # Feature flags
    auto_update: bool = True
    verbose: bool = False
    debug: bool = False
    
    def __post_init__(self) -> None:
        """Initialize derived values."""
        if self.default_arch is None:
            platform = PlatformInfo()
            self.default_arch = platform.normalized_arch
        
        # Validate locale
        base_locale = self.locale.replace(".UTF-8", "").replace(".utf8", "")
        if base_locale in DEFAULT_LOCALES:
            self.locale = DEFAULT_LOCALES[base_locale]
    
    @property
    def platform(self) -> PlatformInfo:
        """Get platform info."""
        return PlatformInfo()
    
    @property
    def config_file(self) -> Path:
        """Path to the configuration file."""
        return self.platform.config_dir / "config.json"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "locale": self.locale,
            "language": self.language,
            "default_container_type": self.default_container_type,
            "default_arch": self.default_arch,
            "default_distro": self.default_distro,
            "default_codename": self.default_codename,
            "vnc_server": self.vnc_server,
            "vnc_resolution": self.vnc_resolution,
            "vnc_display": self.vnc_display,
            "vnc_depth": self.vnc_depth,
            "vnc_localhost": self.vnc_localhost,
            "default_desktop": self.default_desktop,
            "mirror_region": self.mirror_region,
            "mirror_site": self.mirror_site,
            "pulse_server": self.pulse_server,
            "pulse_port": self.pulse_port,
            "auto_update": self.auto_update,
            "verbose": self.verbose,
            "debug": self.debug,
        }
    
    def save(self) -> None:
        """Save configuration to file."""
        self.platform.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(json.dumps(self.to_dict(), indent=2))
    
    @classmethod
    def load(cls) -> TmoeConfig:
        """Load configuration from file."""
        platform = PlatformInfo()
        config_file = platform.config_dir / "config.json"
        if config_file.exists():
            data = json.loads(config_file.read_text())
            return cls(**data)
        return cls()
    
    def get_container_dir(self, container_type: str) -> Path:
        """Get directory for a specific container type."""
        return self.platform.container_dir / container_type
    
    def get_container_config_path(self, name: str) -> Path:
        """Get path to container configuration file."""
        return self.platform.config_dir / "containers" / f"{name}.json"


@lru_cache(maxsize=1)
def get_config() -> TmoeConfig:
    """Get the global configuration singleton."""
    return TmoeConfig.load()


def reload_config() -> TmoeConfig:
    """Reload configuration from file."""
    get_config.cache_clear()
    return get_config()