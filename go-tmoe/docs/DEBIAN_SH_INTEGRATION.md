# debian.sh 集成完成

## 修改内容

### 1. 添加的函数 (文件开头)

```sh
# Detect architecture for Go binary
detect_go_arch() {
    _arch=$(uname -m)
    case "$_arch" in
        x86_64|amd64) pln "amd64" ;;
        aarch64|arm64) pln "arm64" ;;
        armv7l) pln "armv7" ;;
        i386|i686) pln "386" ;;
        mips64el) pln "mips64le" ;;
        riscv64) pln "riscv64" ;;
        *) pln "" ;;
    esac
}

# Check if Go binary exists and is working
check_go_binary() {
    command -v tmoe >/dev/null 2>&1 || return 1
    if tmoe version 2>/dev/null | grep -qE 'TMOE.*([0-9]\.[0-9]|dev)'; then
        return 0
    fi
    return 1
}

# Try to use Go binary if available
try_go_binary() {
    bif "${TMOE_USE_BASH:-0}" && return 1
    bif "${TMOE_SKIP_GO:-0}" && return 1
    
    if check_go_binary; then
        pln "✓ Using TMOE Go edition"
        exec tmoe "$@"
    fi
    return 1
}
```

### 2. 修改的 main 函数

```sh
main() {
    # Try Go binary first
    try_go_binary "$@" && return 0
    
    # Fallback to bash/AWK version
    run_old_file || {
        _tmp_awk_file=$(get_temp_file)
        _tmp_awk_uri=$(get_awk_uri gh)
        get_awk_file
        check_file_size
        run_awk_program
    }
}
```

## 工作流程

1. **检查环境变量**
   - `TMOE_USE_BASH=1` - 强制使用 bash 版本
   - `TMOE_SKIP_GO=1` - 跳过 Go 版本检查

2. **检查 Go 二进制**
   - 查找 `tmoe` 命令
   - 验证是 Go 版本 (检查版本输出)
   - 如果找到，执行并退出

3. **后备方案**
   - 运行旧的 bash manager (如果存在)
   - 下载并运行 AWK 脚本

## 使用示例

### 场景 1: 自动使用 Go 版本

```bash
# 用户已安装 Go 版本
$ sh debian.sh
✓ Using TMOE Go edition
[Go 版本的 TUI 界面]
```

### 场景 2: 强制使用 Bash 版本

```bash
$ TMOE_USE_BASH=1 sh debian.sh
[Bash/AWK 版本]
```

### 场景 3: Go 版本不存在

```bash
# tmoe 命令不在 PATH
$ sh debian.sh
[自动下载 AWK 脚本并运行]
```

## 向后兼容性

✅ **完全兼容**

- 如果 Go 版本不存在，自动使用 bash 版本
- 用户可以选择使用哪个版本
- 所有现有功能保持不变

## 测试

```bash
# 测试 1: 正常流程
sh debian.sh

# 测试 2: 强制 bash
TMOE_USE_BASH=1 sh debian.sh

# 测试 3: 语法检查
sh -n debian.sh
```

## 集成完成 ✅

debian.sh 现在支持：
- ✅ 自动检测和使用 Go 版本
- ✅ 完全向后兼容
- ✅ 用户可控制
- ✅ 优雅降级

**状态**: 🟢 Ready to merge!
