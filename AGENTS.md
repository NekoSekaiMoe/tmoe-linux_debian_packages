# TMOE Python 项目指南

## 项目概述

**TMOE (More Optional Environments)** 是一个用于管理 Linux 容器和 GUI 桌面环境的 Python 工具，特别针对 Android/Termux 环境优化。这是原版 TMOE 的 Python 3.10+ 完整重写版本，提供现代化的 TUI 界面和更强大的功能。

### 主要特性

- **多容器后端支持**: proot (无需 root), chroot, systemd-nspawn, Docker
- **跨架构运行**: 支持 QEMU user-mode 跨架构模拟
- **远程桌面**: VNC/X11/noVNC 配置管理
- **应用中心**: 一键安装浏览器、办公软件、开发工具
- **镜像源管理**: 快速切换国内/国际镜像源
- **现代化 TUI**: 使用 Textual 构建的交互式界面
- **全平台支持**: Android/Termux, Linux 桌面, WSL

## 技术栈

- **Python**: 3.10+
- **TUI 框架**: Textual (≥0.52.0)
- **配置管理**: Pydantic (≥2.5.0)
- **HTTP 客户端**: httpx (≥0.27.0)
- **终端美化**: Rich (≥13.7.0)
- **构建工具**: Poetry / setuptools
- **测试框架**: pytest
- **代码检查**: ruff, mypy

## 项目结构

```
tmoe/
├── __init__.py           # 包初始化，版本信息
├── __main__.py           # 入口点
├── cli.py                # 命令行接口 (argparse)
├── core/                 # 核心模块
│   ├── platform.py       # 平台检测 (Android/Termux/Linux/WSL)
│   ├── config.py         # 配置管理 (Pydantic dataclasses)
│   ├── constants.py      # 常量定义 (架构、发行版、镜像源)
│   └── i18n.py           # 国际化支持
├── tui/                  # TUI 界面 (Textual)
│   ├── app.py            # 主应用和主菜单
│   └── screens/          # 各个功能屏幕
│       ├── proot_menu.py
│       ├── container_list.py
│       ├── create_container.py
│       ├── app_installer.py
│       ├── mirror_manager.py
│       ├── settings.py
│       └── backup_manager.py
├── container/            # 容器管理
│   ├── base.py           # 抽象基类 ContainerBackend
│   ├── proot.py          # Proot 后端实现
│   ├── chroot.py         # Chroot 后端实现
│   ├── docker.py         # Docker 后端
│   ├── lxc.py            # LXC 支持
│   ├── install.py        # 容器安装逻辑
│   └── backup.py         # 备份/恢复功能
├── gui/                  # GUI/VNC 管理
│   ├── vnc.py            # VNC 服务器管理
│   ├── novnc.py          # noVNC Web 界面
│   └── desktop.py        # 桌面环境安装
├── app/                  # 应用中心
│   └── center.py         # 应用管理器
├── sources/              # 镜像源管理
│   └── mirrors.py        # 镜像源切换
└── tools/                # 系统工具
    ├── dev.py            # 开发工具
    ├── system.py         # 系统工具
    └── downloader.py     # 下载管理

tests/                    # 测试目录
debian/                   # Debian 打包文件
```

## 构建和运行

### 开发环境设置

```bash
# 使用 Poetry (推荐)
cd /home/user/tmoe-linux_debian_packages
poetry install
poetry run tmoe

# 使用 pip
pip install -e .
tmoe
```

### 运行测试

```bash
# 运行所有测试
poetry run pytest

# 运行特定测试
poetry run pytest tests/test_platform.py

# 带覆盖率报告
poetry run pytest --cov=tmoe
```

### 代码检查

```bash
# 代码风格检查
poetry run ruff check .

# 类型检查
poetry run mypy tmoe/

# 自动修复代码风格问题
poetry run ruff check --fix .
```

### 构建 Debian 包

```bash
# 使用构建脚本
./build-deb.sh

# 手动构建
dpkg-buildpackage -us -uc -b -tc
```

## 使用方法

### 启动 TUI 管理器

```bash
tmoe          # 默认启动 TUI
tmoe m        # 显式启动管理器
```

### 命令行模式

```bash
# Proot 容器 (无需 root)
tmoe p debian                    # 启动默认 Debian
tmoe p ubuntu jammy arm64        # 指定版本和架构

# Chroot 容器 (需要 root)
tmoe c debian

# 列出已安装容器
tmoe ls

# 工具菜单
tmoe t
```

## 开发规范

### 代码风格

- **行长度**: 100 字符 (ruff 配置)
- **引号**: 双引号
- **缩进**: 4 空格
- **类型注解**: 强制使用，mypy strict 模式
- **文档字符串**: Google 风格

### 项目架构模式

#### 容器后端抽象

所有容器后端必须继承 `ContainerBackend` 抽象基类：

```python
from tmoe.container.base import ContainerBackend

class ProotBackend(ContainerBackend):
    @property
    def backend_type(self) -> str:
        return "proot"
    
    @property
    def requires_root(self) -> bool:
        return False
    
    async def list_containers(self) -> list[ContainerInfo]:
        # 实现列出容器
        pass
    
    async def create(self, name: str, distro: str, ...) -> ContainerConfig:
        # 实现创建容器
        pass
    
    # ... 其他抽象方法
```

#### 平台检测

使用 `PlatformInfo` 类自动检测运行环境：

```python
from tmoe.core.platform import get_platform_info

platform = get_platform_info()
if platform.is_android:
    # Android/Termux 特定逻辑
elif platform.is_wsl:
    # WSL 特定逻辑
```

#### 配置管理

使用 Pydantic dataclasses 进行类型安全的配置：

```python
from tmoe.core.config import get_config, ContainerConfig

config = get_config()
container_config = ContainerConfig(
    name="debian-test",
    distro="debian",
    arch="arm64"
)
```

### 测试规范

- 测试文件命名: `test_*.py`
- 使用 pytest-asyncio 测试异步代码
- 测试覆盖率目标: >80%

### Git 提交规范

- 使用中文或英文提交信息
- 格式: `<type>: <description>`
- 常用类型: feat, fix, docs, style, refactor, test, chore

## 关键常量

### 支持的架构

- `arm64` / `aarch64` - ARM 64位
- `amd64` / `x86_64` - x86 64位
- `armhf` / `armv7l` - ARM 32位硬浮点
- `i386` / `i686` - x86 32位
- `mips64el`, `mipsel` - MIPS
- `ppc64el` - PowerPC
- `s390x` - IBM Z
- `riscv64` - RISC-V

### 支持的发行版

- Debian (sid, testing, stable, bookworm, bullseye)
- Ubuntu (noble, jammy, focal, bionic)
- Kali, Arch, Manjaro, Alpine
- Fedora, CentOS, openSUSE
- Gentoo, Void, openEuler

### 中国镜像源

- 清华 (tsinghua)
- 中科大 (ustc)
- 北外 (bfsu)
- 上海交大 (sjtu)
- 阿里云 (aliyun)
- 腾讯云 (tencent)
- 华为云 (huawei)
- 网易 (163)

## 文件路径约定

### Android/Termux

- 配置: `~/.config/tmoe-linux/`
- 数据: `~/.local/share/tmoe-linux/`
- 缓存: `~/.cache/tmoe-linux/`

### Linux (root)

- 配置: `/usr/local/etc/tmoe-linux/`
- 数据: `/usr/local/etc/tmoe-linux/`
- 缓存: `/var/cache/tmoe-linux/`

## 依赖项

### 运行时依赖

- `proot` (>= 5.1.0) - 用户态容器
- `curl` 或 `wget` - 下载工具
- `tar`, `xz-utils` - 压缩工具

### 推荐依赖

- `qemu-user-static` - 跨架构支持
- `docker.io` 或 `docker-ce` - Docker 支持
- `tigervnc-standalone-server` - VNC 服务器
- `x11vnc`, `websockify` - noVNC 支持

## 相关链接

- 原版 TMOE: https://github.com/2moe/tmoe
- 文档: https://doc.tmoe.me
- 许可证: Apache-2.0

## 常见任务

### 添加新的容器后端

1. 在 `tmoe/container/` 创建新文件
2. 继承 `ContainerBackend` 基类
3. 实现所有抽象方法
4. 在 `tmoe/container/__init__.py` 导出

### 添加新的 TUI 屏幕

1. 在 `tmoe/tui/screens/` 创建新文件
2. 继承 `textual.screen.Screen`
3. 在 `TmoeApp.SCREENS` 字典中注册
4. 添加导航绑定

### 添加新架构支持

1. 更新 `tmoe/core/constants.py`:
   - `SUPPORTED_ARCHITECTURES`
   - `ARCH_MAPPINGS`
   - `QEMU_ARCH_MAPPINGS`

### 添加新发行版支持

1. 更新 `SUPPORTED_DISTROS` 字典
2. 在 `tmoe/container/install.py` 添加安装逻辑
3. 添加镜像源配置到 `tmoe/sources/mirrors.py`
