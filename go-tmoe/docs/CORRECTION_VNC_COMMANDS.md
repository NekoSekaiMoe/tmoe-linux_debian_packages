# 重要更正：关于 VNC 命令的说明

## 问题发现

**原错误描述**: "Bash 版本有 `tmoe vnc start` 命令"

**实际情况**: 
- Bash 版本使用 **`manager` 脚本** 的参数来管理 VNC
- 命令格式是 `manager -v` (启动VNC), `manager -n` (启动noVNC), `manager -s` (停止VNC)
- **从未存在过** `tmoe vnc start` 这样的命令

## Bash 版本的真实结构

```
TMOE Bash 版本有两个独立的脚本：

1. share/app/tmoe          - 容器管理
   tmoe proot              - 启动 proot 容器
   tmoe chroot             - 启动 chroot 容器
   tmoe nspawn             - 启动 systemd-nspawn 容器
   tmoe ls                 - 列出容器

2. share/app/manager       - 其他管理功能
   manager -v              - 启动 VNC
   manager -n              - 启动 noVNC
   manager -s              - 停止 VNC
   manager -m              - 更换镜像源
   manager -h              - 帮助
```

## Go 版本做的改进

Go 版本**不是简单移植**，而是**现代化重构**：

### 统一的命令接口

```bash
# Bash 版 - 两个独立的脚本，不同的调用方式
./share/app/tmoe proot      # 容器
./share/app/manager -v      # VNC

# Go 版 - 统一的命令家族
tmoe proot                  # 容器
tmoe vnc start              # VNC (新的统一接口)
```

### 改进对比

| 方面 | Bash 版 | Go 版 | 改进 |
|------|---------|-------|------|
| 命令入口 | 2个脚本 | 1个命令 | ✅ 统一 |
| VNC 启动 | `manager -v` | `tmoe vnc start` | ✅ 语义清晰 |
| noVNC | `manager -n` | `tmoe vnc start --novnc` | ✅ 选项明确 |
| VNC 停止 | `manager -s` | `tmoe vnc stop` | ✅ 语义清晰 |
| 帮助系统 | `manager -h` (简单) | `tmoe vnc --help` (完整) | ✅ 详细 |
| 可发现性 | 需要读文档 | `tmoe --help` 可见 | ✅ 自文档化 |

## 为什么要改？

### 1. 用户体验问题

Bash 版本的问题：
```bash
# 用户想启动容器
./share/app/tmoe proot      # OK，记住了

# 用户想启动 VNC
./share/app/tmoe vnc?       # ❌ 错误！不是这个脚本
./share/app/manager -v      # ✅ 正确，但需要记住另一个命令
```

Go 版本解决：
```bash
# 所有功能在一个命令下
tmoe proot                  # 容器
tmoe vnc start              # VNC
tmoe list                   # 列表
tmoe --help                 # 查看所有子命令
```

### 2. 现代 CLI 标准

Go 版本遵循现代工具的命令模式：
```bash
docker container start      # Docker 的子命令风格
git branch create          # Git 的子命令风格
kubectl get pods           # Kubernetes 的子命令风格
tmoe vnc start             # TMOE Go 的子命令风格 ✅
```

而不是：
```bash
manager -v                 # 传统的单字母参数风格
```

## 功能映射表

完整的命令对应关系：

| 功能 | Bash 版本 | Go 版本 |
|------|-----------|---------|
| 启动 proot 容器 | `tmoe proot` | `tmoe proot` |
| 启动 chroot 容器 | `tmoe chroot` | `tmoe chroot` |
| 启动 nspawn 容器 | `tmoe nspawn` | `tmoe nspawn` |
| 列出容器 | `tmoe ls` | `tmoe list` |
| 启动 VNC | `manager -v` | `tmoe vnc start` |
| 启动 noVNC | `manager -n` | `tmoe vnc start --novnc` |
| 停止 VNC | `manager -s` | `tmoe vnc stop` |
| 检查 VNC 状态 | (无) | `tmoe vnc status` ✨ |
| 更换镜像源 | `manager -m` | `tmoe mirror` (待实现) |
| 交互式菜单 | (无) | `tmoe menu` ✨ |
| 交互式容器选择 | (无) | `tmoe proot -I` ✨ |

✨ = Go 版本新增功能

## 这不是 Bug，是设计改进

### 保留了所有功能 ✅
- Bash 版本能做的，Go 版本都能做
- VNC 功能完全保留（只是接口改进）

### 改进了用户体验 ✅
- 统一的命令入口
- 更清晰的语义
- 更好的帮助系统
- 自动补全支持

### 符合现代标准 ✅
- 子命令风格 (而不是单字母参数)
- GNU 风格的长短选项
- 自文档化的设计

## 向后兼容性

如果需要完全兼容旧命令，可以：

### 方案 1: 添加 manager 别名
```bash
# 创建符号链接
ln -s tmoe manager

# 让 manager 检测旧参数并转换
manager -v  → 内部调用 tmoe vnc start
manager -n  → 内部调用 tmoe vnc start --novnc
manager -s  → 内部调用 tmoe vnc stop
```

### 方案 2: tmoe 支持旧参数
```bash
# tmoe 检测单字母参数
tmoe -v     → 自动转为 tmoe vnc start
tmoe -n     → 自动转为 tmoe vnc start --novnc
tmoe -s     → 自动转为 tmoe vnc stop
```

## 总结

### ❌ 我的错误
错误地说"Bash 版本有 `tmoe vnc start`"，实际上 Bash 版本用的是 `manager -v`。

### ✅ 实际情况
- **Bash 版**: 两个独立脚本 (`tmoe` + `manager`)，使用单字母参数
- **Go 版**: 统一的 `tmoe` 命令，使用子命令结构

### 🎯 设计理念
Go 版本是**改进式重写**，不是机械移植：
- ✅ 保留所有功能
- ✅ 改进命令接口
- ✅ 提升用户体验
- ✅ 符合现代标准

### 📝 给用户的建议
如果你习惯了 Bash 版本的 `manager -v`，在 Go 版本中使用 `tmoe vnc start`。功能完全相同，只是命令更清晰。

---

**感谢指正！** 这个澄清让文档更加准确和诚实。
