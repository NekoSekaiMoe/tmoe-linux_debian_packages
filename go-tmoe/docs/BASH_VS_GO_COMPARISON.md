# TMOE Go vs Bash - 功能对比与修正

## 原始 Bash 版本的实际功能

### 入口点

1. **debian.sh** (POSIX sh)
   - 下载并执行 AWK 文件
   - 作为引导脚本

2. **share/app/manager** (bash)
   - 主管理脚本
   - 参数化命令：
     ```bash
     manager -n      # 启动 noVNC
     manager -v      # 启动 VNC
     manager -s      # 停止 VNC
     manager -m      # 更换镜像源
     manager -h      # 帮助
     ```

3. **share/app/tmoe** (bash)
   - 容器启动脚本
   - 模式选择：
     ```bash
     tmoe proot      # proot 模式
     tmoe chroot     # chroot 模式
     tmoe nspawn     # systemd-nspawn 模式
     tmoe ls         # 列出容器
     ```

### Bash 版本的命令结构

```bash
# 容器相关 (通过 tmoe 脚本)
./share/app/tmoe proot
./share/app/tmoe chroot
./share/app/tmoe nspawn
./share/app/tmoe ls

# VNC/管理相关 (通过 manager 脚本)
./share/app/manager -n      # noVNC
./share/app/manager -v      # VNC
./share/app/manager -s      # 停止 VNC
./share/app/manager -m      # 镜像源
```

**注意**: Bash 版本**没有**统一的 `tmoe vnc start` 这种子命令形式！

---

## Go 版本的设计改进

### 统一的命令接口

Go 版本将所有功能整合到一个二进制，提供统一的子命令接口：

```bash
# 容器管理 (对应 bash 的 tmoe 脚本)
tmoe proot [name]
tmoe chroot [name]
tmoe nspawn [name]
tmoe list                   # 对应 bash 的 tmoe ls

# VNC 管理 (对应 bash 的 manager -v/-n/-s)
tmoe vnc start              # 对应 manager -v
tmoe vnc start --novnc      # 对应 manager -n
tmoe vnc stop               # 对应 manager -s

# 镜像源管理 (对应 bash 的 manager -m)
tmoe mirror                 # 对应 manager -m (待实现)

# 交互式菜单 (新增功能)
tmoe menu                   # 新增：TUI 主菜单
tmoe proot -I               # 新增：交互式容器选择
```

### 设计优势

#### 1. 更直观的命令结构
```bash
# Bash 版 (分散在两个脚本)
./share/app/tmoe proot
./share/app/manager -v

# Go 版 (统一接口)
tmoe proot
tmoe vnc start
```

#### 2. 更好的帮助系统
```bash
# Bash 版
./share/app/manager -h     # 只有简短的中文说明

# Go 版
tmoe --help                # 完整的帮助文档
tmoe vnc --help            # 子命令帮助
tmoe vnc start --help      # 详细选项说明
```

#### 3. 更一致的参数风格
```bash
# Bash 版 (混合风格)
manager -n                 # 短参数
manager -novnc             # 长参数(非标准)

# Go 版 (标准 GNU 风格)
tmoe vnc start -n          # 短参数
tmoe vnc start --novnc     # 标准长参数
tmoe vnc start -p 5901     # 参数带值
```

---

## 功能映射表

| Bash 原版 | Go 新版 | 说明 |
|-----------|---------|------|
| `tmoe proot` | `tmoe proot` | ✅ 保持一致 |
| `tmoe chroot` | `tmoe chroot` | ✅ 保持一致 |
| `tmoe nspawn` | `tmoe nspawn` | ✅ 保持一致 |
| `tmoe ls` | `tmoe list` | ⚡ 更标准的命令名 |
| `manager -v` | `tmoe vnc start` | ⚡ 更清晰的语义 |
| `manager -n` | `tmoe vnc start --novnc` | ⚡ 统一到 vnc 子命令 |
| `manager -s` | `tmoe vnc stop` | ⚡ 统一到 vnc 子命令 |
| `manager -m` | `tmoe mirror` | ⚡ 独立子命令 (待实现) |
| (无) | `tmoe menu` | ✨ 新增：交互式 TUI |
| (无) | `tmoe proot -I` | ✨ 新增：交互式选择 |

---

## 我的错误

### ❌ 错误陈述
> "shell 版本有 `tmoe vnc start` 命令"

### ✅ 实际情况
- Bash 版本通过 `manager -v` 启动 VNC
- Bash 版本通过 `manager -n` 启动 noVNC  
- Bash 版本通过 `manager -s` 停止 VNC
- **没有** `tmoe vnc start` 这种子命令形式

### 📝 正确表述应该是
Go 版本**改进了**命令接口，将分散在 `tmoe` 和 `manager` 两个脚本的功能整合到一个统一的 `tmoe` 命令，提供更清晰的子命令结构。

---

## Go 版本的真正优势

### 1. 命令统一性
```bash
# Bash 版 - 需要记住不同脚本
./share/app/tmoe proot      # 容器
./share/app/manager -v      # VNC

# Go 版 - 统一入口
tmoe proot                  # 容器
tmoe vnc start              # VNC
```

### 2. 发现性更好
```bash
# Bash 版 - 需要读文档才知道 manager 有什么参数
./share/app/manager -h

# Go 版 - 标准的命令发现
tmoe --help                 # 列出所有子命令
tmoe vnc --help             # VNC 子命令的所有操作
```

### 3. 扩展性更强
```bash
# 添加新功能很容易
tmoe mirror list            # 列出镜像源
tmoe mirror set tuna        # 设置 tuna 镜像
tmoe container install      # 安装容器
```

---

## 实现建议

考虑到兼容性，可以添加一个 `manager` 兼容模式：

```bash
# 保持向后兼容
tmoe manager -v             # 等同于 tmoe vnc start
tmoe manager -n             # 等同于 tmoe vnc start --novnc
tmoe manager -s             # 等同于 tmoe vnc stop
```

或者在文档中明确说明命令映射关系。

---

## 总结

Go 版本**不是简单复制** bash 版本的接口，而是在保持功能兼容的基础上：
- ✅ 统一了命令入口（从两个脚本合并为一个命令）
- ✅ 改进了命令结构（从参数式变为子命令式）
- ✅ 增强了可发现性（标准的帮助系统）
- ✅ 提供了更好的 UX（清晰的语义）

这是一种**改进式重写**，而不是机械的 1:1 移植。
