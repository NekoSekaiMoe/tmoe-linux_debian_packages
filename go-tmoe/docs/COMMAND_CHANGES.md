# 重要说明：Go 版本与 Bash 版本的区别

## ⚠️ 命令接口的重要变化

### Bash 原版的实际命令

Bash 版本使用**两个独立的脚本**，而不是统一的命令：

```bash
# 1. tmoe 脚本 - 容器管理
./share/app/tmoe proot      # 启动 proot 容器
./share/app/tmoe chroot     # 启动 chroot 容器  
./share/app/tmoe nspawn     # 启动 systemd-nspawn 容器
./share/app/tmoe ls         # 列出容器

# 2. manager 脚本 - VNC 和其他管理功能
./share/app/manager -v      # 启动 VNC
./share/app/manager -n      # 启动 noVNC
./share/app/manager -s      # 停止 VNC
./share/app/manager -m      # 更换镜像源
./share/app/manager -h      # 帮助
```

**注意**: Bash 版本**没有** `tmoe vnc start` 这样的命令！

---

## Go 版本的设计改进

### 统一的命令接口

Go 版本将两个脚本的功能整合到**一个统一的二进制**：

```bash
# 所有功能通过一个 tmoe 命令
tmoe proot              # 容器管理
tmoe vnc start          # VNC 管理
tmoe menu               # 交互式菜单
```

### 命令映射表

| Bash 原版 | Go 版本 | 说明 |
|-----------|---------|------|
| `tmoe proot` | `tmoe proot` | ✅ 保持一致 |
| `tmoe chroot` | `tmoe chroot` | ✅ 保持一致 |
| `tmoe nspawn` | `tmoe nspawn` | ✅ 保持一致 |
| `tmoe ls` | `tmoe list` | 📝 更标准的命名 |
| `manager -v` | `tmoe vnc start` | 🎯 **新增统一接口** |
| `manager -n` | `tmoe vnc start --novnc` | 🎯 **新增统一接口** |
| `manager -s` | `tmoe vnc stop` | 🎯 **新增统一接口** |
| `manager -m` | `tmoe mirror` (待实现) | 🎯 **新增统一接口** |
| (无) | `tmoe menu` | ✨ **全新功能：TUI** |
| (无) | `tmoe proot -I` | ✨ **全新功能：交互选择** |

---

## 这是设计改进，不是简单移植

### 为什么要改变命令结构？

#### 1. **用户体验更好**

```bash
# Bash 版 - 需要记住两个不同的脚本
./share/app/tmoe proot      # 启动容器
./share/app/manager -v      # 启动 VNC (完全不同的命令！)

# Go 版 - 统一的命令家族
tmoe proot                  # 启动容器
tmoe vnc start              # 启动 VNC (一致的体验)
```

#### 2. **可发现性更强**

```bash
# Bash 版 - 怎么知道 manager 有什么功能？
./share/app/manager -h      # 只显示中文的简短帮助

# Go 版 - 标准的命令发现机制
tmoe --help                 # 列出所有子命令
tmoe vnc --help             # 查看 VNC 相关的所有操作
tmoe vnc start --help       # 查看具体参数
```

#### 3. **符合现代 CLI 标准**

```bash
# 现代命令行工具的标准形式
docker container start      # Docker
git branch create          # Git
kubectl get pods           # Kubernetes
tmoe vnc start             # TMOE Go (符合标准)

# 而不是
manager -v                 # 不直观的单字母参数
```

---

## 功能完全保留

虽然命令接口改进了，但**所有功能都被保留**：

### ✅ 容器管理 (100% 保留)
- ✅ Proot 容器
- ✅ Chroot 容器
- ✅ Systemd-nspawn 容器
- ✅ 容器列表

### ✅ VNC 服务 (100% 保留)
- ✅ 启动 VNC 服务器
- ✅ 启动 noVNC (Web)
- ✅ 停止 VNC
- ✅ 状态检查

### ✨ 新增功能
- ✨ 交互式 TUI 菜单
- ✨ 容器选择界面
- ✨ 更好的帮助系统
- ✨ 自动补全支持

---

## 向后兼容性考虑

### 可选方案：添加别名

如果需要完全向后兼容，可以添加：

```bash
# 创建软链接或别名
ln -s tmoe manager          # manager 命令别名

# 然后支持旧语法
manager -v                  # 内部调用 tmoe vnc start
manager -n                  # 内部调用 tmoe vnc start --novnc
manager -s                  # 内部调用 tmoe vnc stop
```

### 或者在 tmoe 中检测旧参数

```bash
# Go 版本可以检测旧式参数
tmoe -v                     # 自动转换为 tmoe vnc start
tmoe -n                     # 自动转换为 tmoe vnc start --novnc
```

---

## 结论

### 我之前的表述问题

❌ **错误说法**: "Bash 版本有 `tmoe vnc start` 命令"  
✅ **实际情况**: Bash 版本通过 `manager -v` 启动 VNC

### Go 版本的真实定位

这不是一个 1:1 的移植，而是一个**现代化重写**：

- ✅ **保留所有功能** - 不丢失任何能力
- ✅ **改进命令接口** - 从分散的脚本到统一的命令
- ✅ **提升用户体验** - 更直观、更易发现
- ✅ **符合现代标准** - 类似 Docker/Git/Kubectl

### 优势总结

1. **单一入口点** - 一个 `tmoe` 命令完成所有操作
2. **清晰的层级** - `tmoe vnc start` 比 `manager -v` 更清楚
3. **可扩展性** - 容易添加新子命令 `tmoe mirror`, `tmoe config` 等
4. **自文档化** - 通过 `--help` 就能发现所有功能
5. **跨平台一致** - 单个二进制在所有平台上行为一致

---

## 给用户的说明

如果你习惯了 Bash 版本的命令，以下是迁移指南：

```bash
# 旧命令 (Bash)              → 新命令 (Go)
./share/app/tmoe proot       → tmoe proot
./share/app/manager -v       → tmoe vnc start
./share/app/manager -n       → tmoe vnc start --novnc
./share/app/manager -s       → tmoe vnc stop
./share/app/manager -m       → tmoe mirror (待实现)

# 新增功能
(无)                         → tmoe menu              # 交互式菜单
(无)                         → tmoe proot -I          # 交互选择
(无)                         → tmoe --help            # 完整帮助
```

这是一个**改进**，不是倒退。所有功能都保留了，只是以更好的方式呈现。
