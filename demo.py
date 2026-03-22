#!/usr/bin/env python3
"""Demo script for TMOE Python.

This script demonstrates the core functionality of TMOE Python:
- Platform detection
- Configuration management
- Container operations (simulated)
"""

import asyncio
from pathlib import Path


def demo_platform():
    """Demonstrate platform detection."""
    print("=" * 60)
    print("🖥️  平台检测演示")
    print("=" * 60)
    
    from tmoe.core.platform import PlatformInfo
    
    platform = PlatformInfo()
    
    print(f"机器架构: {platform.machine}")
    print(f"标准化架构: {platform.normalized_arch}")
    print(f"是否是 Android: {platform.is_android}")
    print(f"是否是 Termux: {platform.is_termux}")
    print(f"是否是 WSL: {platform.is_wsl}")
    print(f"是否是 Linux: {platform.is_linux}")
    print(f"是否是 Root: {platform.is_root}")
    print(f"配置目录: {platform.config_dir}")
    print(f"容器目录: {platform.container_dir}")
    print()


def demo_config():
    """Demonstrate configuration management."""
    print("=" * 60)
    print("⚙️  配置管理演示")
    print("=" * 60)
    
    from tmoe.core.config import TmoeConfig, ContainerConfig, get_config
    
    # Global config
    config = TmoeConfig()
    print(f"TMOE 版本: {config.version}")
    print(f"默认架构: {config.default_arch}")
    print(f"默认发行版: {config.default_distro}")
    print(f"语言: {config.locale}")
    print(f"VNC 服务器: {config.vnc_server}")
    print(f"VNC 分辨率: {config.vnc_resolution}")
    print()
    
    # Container config
    container = ContainerConfig(
        name="demo-debian",
        distro="debian",
        arch="arm64",
        codename="stable",
    )
    print(f"容器名称: {container.name}")
    print(f"发行版: {container.distro}")
    print(f"架构: {container.arch}")
    print(f"容器类型: {container.container_type}")
    print(f"默认用户: {container.user}")
    print(f"Home 目录: {container.home}")
    print()


def demo_constants():
    """Demonstrate constants."""
    print("=" * 60)
    print("📋 常量定义演示")
    print("=" * 60)
    
    from tmoe.core.constants import (
        SUPPORTED_ARCHITECTURES,
        SUPPORTED_DISTROS,
        CHINA_MIRRORS,
    )
    
    print(f"支持的架构 ({len(SUPPORTED_ARCHITECTURES)} 个):")
    print(", ".join(SUPPORTED_ARCHITECTURES))
    print()
    
    print(f"支持的发行版 ({len(SUPPORTED_DISTROS)} 个):")
    for distro, codenames in list(SUPPORTED_DISTROS.items())[:5]:
        print(f"  - {distro}: {', '.join(codenames[:3])}")
    print("  ...")
    print()
    
    print("国内镜像站:")
    for name, url in list(CHINA_MIRRORS.items())[:4]:
        print(f"  - {name}: {url}")
    print()


async def demo_container():
    """Demonstrate container operations."""
    print("=" * 60)
    print("🐳 容器操作演示 (模拟)")
    print("=" * 60)
    
    from tmoe.container.proot import ProotBackend
    from tmoe.container.base import ContainerInfo, ContainerStatus
    
    backend = ProotBackend()
    
    print(f"后端类型: {backend.backend_type}")
    print(f"需要 Root: {backend.requires_root}")
    print(f"Proot 路径: {backend.proot_bin}")
    print()
    
    # List containers (will be empty if none exist)
    print("列出容器:")
    containers = await backend.list_containers()
    if containers:
        for info in containers:
            print(f"  - {info.name} ({info.config.distro}, {info.status.name})")
    else:
        print("  (暂无容器)")
    print()


def demo_app_center():
    """Demonstrate app center."""
    print("=" * 60)
    print("📦 应用中心演示")
    print("=" * 60)
    
    from tmoe.app.center import AppCenter, AppCategory
    
    center = AppCenter()
    
    print("应用分类:")
    for category in AppCategory:
        apps = center.get_apps_by_category(category)
        print(f"  - {category.name}: {len(apps)} 个应用")
    print()
    
    print("浏览器应用:")
    browsers = center.get_apps_by_category(AppCategory.BROWSER)
    for app in browsers:
        print(f"  - {app.name}: {app.description}")
    print()


def demo_mirrors():
    """Demonstrate mirror management."""
    print("=" * 60)
    print("🪞 镜像源管理演示")
    print("=" * 60)
    
    from tmoe.sources.mirrors import MirrorManager, MirrorRegion
    
    manager = MirrorManager()
    
    print("按区域列出镜像:")
    for region in [MirrorRegion.CHINA, MirrorRegion.GLOBAL]:
        mirrors = manager.get_mirrors_by_region(region)
        print(f"  {region.value}: {len(mirrors)} 个镜像")
        for mirror in mirrors[:3]:
            print(f"    - {mirror.name}")
    print()


def demo_vnc():
    """Demonstrate VNC management."""
    print("=" * 60)
    print("🖥️  VNC 管理演示")
    print("=" * 60)
    
    from tmoe.gui.vnc import VncManager
    
    manager = VncManager()
    config = manager.vnc_config
    
    print(f"VNC 服务器: {config.server}")
    print(f"分辨率: {config.resolution}")
    print(f"显示号: {config.display}")
    print(f"端口: {manager.get_display_port()}")
    print(f"颜色深度: {config.depth}")
    print(f"仅本地: {config.localhost}")
    print()


async def demo_novnc():
    """Demonstrate noVNC."""
    print("=" * 60)
    print("🌐 noVNC Web 远程桌面演示")
    print("=" * 60)
    
    from tmoe.gui.novnc import NoVncManager
    
    manager = NoVncManager()
    config = manager.config
    
    print(f"noVNC 目录: {manager.novnc_dir}")
    print(f"Web 端口: {config.web_port}")
    print(f"VNC 后端: {config.vnc_host}:{config.vnc_port}")
    print(f"访问地址: http://localhost:{config.web_port}/vnc.html")
    print(f"已安装: {manager.is_installed}")
    print()


async def demo_lxc():
    """Demonstrate LXC image client."""
    print("=" * 60)
    print("📦 LXC 镜像下载演示")
    print("=" * 60)
    
    from tmoe.container.lxc import LXCImageClient, LXCImageManager
    
    client = LXCImageClient()
    manager = LXCImageManager()
    
    print(f"镜像服务器: {client.DEFAULT_MIRROR}")
    print(f"支持的架构: {', '.join(list(client.ARCH_MAPPINGS.keys())[:5])}...")
    
    # List available distros
    distros = manager.list_available_distros()
    print(f"可用发行版 ({len(distros)} 个):")
    for distro in distros[:5]:
        print(f"  - {distro}")
    print("  ...")
    print()


def demo_desktop():
    """Demonstrate desktop environment installer."""
    print("=" * 60)
    print("🖥️  桌面环境安装演示")
    print("=" * 60)
    
    from tmoe.gui.desktop import DesktopEnvironment, DesktopInstaller
    from tmoe.container.proot import ProotBackend
    
    backend = ProotBackend()
    installer = DesktopInstaller(backend)
    
    print("支持的桌面环境:")
    for desktop in DesktopEnvironment:
        print(f"  - {desktop.display_name}: {desktop.description}")
    
    print()
    print("安装命令示例:")
    print(f"  await installer.install_desktop(DesktopEnvironment.XFCE)")
    print()


def demo_backup():
    """Demonstrate backup manager."""
    print("=" * 60)
    print("💾 容器备份管理演示")
    print("=" * 60)
    
    from tmoe.container.backup import ContainerBackupManager, BackupInfo
    from tmoe.container.proot import ProotBackend
    import tempfile
    
    backend = ProotBackend()
    # Use temp directory for demo
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ContainerBackupManager(backend, Path(tmpdir))
        
        print(f"备份目录: {manager.backup_dir}")
        print("支持的压缩格式:")
        print("  - xz: 高压缩率 (推荐)")
        print("  - gz: 快速压缩")
        print("  - bz2: 平衡")
        print("  - none: 无压缩")
        print()
        print("操作示例:")
        print("  await manager.backup_container('my-container', 'xz')")
        print("  await manager.restore_backup('/path/to/backup.tar.xz')")
        print()


def demo_i18n():
    """Demonstrate internationalization."""
    print("=" * 60)
    print("🌍 国际化支持演示")
    print("=" * 60)
    
    from tmoe.core.i18n import I18n, get_i18n, _
    
    print("支持的语言:")
    for code, name in I18n.LANGUAGES.items():
        print(f"  - {code}: {name}")
    
    print()
    print("翻译示例:")
    for lang in ["en", "zh_CN", "zh_TW", "ja"]:
        i18n = I18n(lang)
        print(f"  [{lang}] main_menu: {i18n.t('main_menu')}")
    print()


def demo_docker():
    """Demonstrate Docker backend."""
    print("=" * 60)
    print("🐳 Docker 容器后端演示")
    print("=" * 60)
    
    from tmoe.container.docker import DockerBackend
    
    backend = DockerBackend()
    
    print(f"后端类型: {backend.backend_type}")
    print(f"Docker 可用: {backend.is_available}")
    print(f"需要 root: {backend.requires_root}")
    print()
    print("支持的发行版镜像:")
    for distro, image in list(backend.DISTRO_IMAGES.items())[:5]:
        print(f"  - {distro}: {image}")
    print("  ...")
    print()


async def demo_container_lifecycle():
    """Demonstrate container lifecycle."""
    print("=" * 60)
    print("🔄 容器生命周期演示")
    print("=" * 60)
    
    from tmoe.container.proot import ProotBackend
    from tmoe.container.base import ContainerStatus
    
    backend = ProotBackend()
    
    print(f"后端: {backend.backend_type}")
    print(f"需要 root: {backend.requires_root}")
    print(f"Proot 路径: {backend.proot_bin}")
    print()
    
    # Simulate lifecycle
    print("容器生命周期操作:")
    print("  1. create() - 创建容器配置")
    print("  2. install() - 下载并安装 rootfs")
    print("  3. start() - 启动容器")
    print("  4. exec() - 在容器中执行命令")
    print("  5. stop() - 停止容器")
    print("  6. remove() - 删除容器")
    print()


async def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("🚀 TMOE Python 演示")
    print("=" * 60)
    print()
    
    demo_platform()
    demo_config()
    demo_constants()
    await demo_container()
    await demo_container_lifecycle()
    demo_app_center()
    demo_mirrors()
    demo_vnc()
    await demo_novnc()
    await demo_lxc()
    demo_desktop()
    demo_backup()
    demo_i18n()
    demo_docker()
    
    print("=" * 60)
    print("✅ 演示完成!")
    print("=" * 60)
    print()
    print("🎮 启动 TUI 界面:")
    print("  cd /home/user/tmoe/python")
    print("  python3 -m tmoe")
    print()
    print("📦 TUI 功能:")
    print("  - 容器创建向导")
    print("  - 容器管理 (启动/停止/删除/备份)")
    print("  - 应用中心")
    print("  - 镜像源管理")
    print("  - 设置")
    print()
    print("🐳 支持的容器后端:")
    print("  - Proot (无需 root)")
    print("  - Chroot (需要 root)")
    print("  - Docker")
    print()
    print("🖥️  GUI/远程桌面:")
    print("  - VNC 服务器管理")
    print("  - noVNC Web 客户端")
    print("  - 桌面环境安装 (XFCE/LXDE/MATE/KDE/GNOME)")


if __name__ == "__main__":
    asyncio.run(main())
