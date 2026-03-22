# TMOE Python 重写版

TMOE (More Optional Environments) 的 Python 3.10+ 重写版本，提供现代化的 Linux 容器和 GUI 桌面管理工具。

## 特性

- **多容器后端支持**: proot (无需root), chroot, systemd-nspawn
- **跨架构运行**: 支持 QEMU user-mode 跨架构模拟
- **远程桌面**: VNC/X11/noVNC 配置管理
- **应用中心**: 一键安装浏览器、办公软件、开发工具
- **镜像源管理**: 快速切换国内/国际镜像源
- **现代化 TUI**: 使用 Textual 构建的交互式界面
- **全平台支持**: Android/Termux, Linux 桌面, WSL

## 安装

### 依赖

- Python 3.10+
- Poetry (推荐)

### 从源码安装

```bash
cd python
poetry install
poetry run tmoe
```

### 开发模式

```bash
cd python
poetry install --with dev
poetry run pytest
```

## 使用方法

### 启动 TUI 管理器

```bash
tmoe
tmoe m
```

### 命令行模式

```bash
# Proot 容器
tmoe p debian
tmoe p ubuntu jammy arm64

# Chroot 容器 (需要 root)
tmoe c debian

# 列出已安装容器
tmoe ls

# 工具菜单
tmoe t
```

## 项目结构

```
tmoe/
├── __main__.py          # 入口点
├── cli.py               # 命令行接口
├── core/                # 核心模块
│   ├── platform.py      # 平台检测
│   ├── config.py        # 配置管理
│   └── constants.py     # 常量定义
├── tui/                 # TUI 界面
│   └── app.py           # Textual 主应用
├── container/           # 容器管理
│   ├── base.py          # 抽象基类
│   ├── proot.py         # Proot 后端
│   ├── chroot.py        # Chroot 后端
│   └── install.py       # 容器安装
├── gui/                 # GUI/VNC 管理
│   └── vnc.py           # VNC 管理器
├── app/                 # 应用中心
│   └── center.py        # 应用管理
└── sources/             # 镜像源管理
    └── mirrors.py       # 镜像管理器
```

## 架构

### 平台检测

自动检测运行环境：
- Android/Termux
- GNU/Linux
- WSL (Windows Subsystem for Linux)

### 容器管理

抽象基类 `ContainerBackend` 定义统一接口：
- `list_containers()` - 列出容器
- `create()` - 创建容器
- `start()` - 启动容器
- `stop()` - 停止容器
- `remove()` - 删除容器
- `exec()` - 执行命令

具体实现：
- `ProotBackend` - 用户态容器
- `ChrootBackend` - 传统 chroot

### 配置管理

使用 Pydantic 进行类型安全的配置管理：
- 支持环境变量 (`TMOE_*`)
- 配置文件自动加载/保存
- 平台差异化配置

## 开发

### 运行测试

```bash
poetry run pytest
```

### 代码检查

```bash
poetry run ruff check .
poetry run mypy tmoe/
```

## 许可

Apache-2.0 License

## 相关链接

- 原版 TMOE: https://github.com/2moe/tmoe
- 文档: https://doc.tmoe.me
