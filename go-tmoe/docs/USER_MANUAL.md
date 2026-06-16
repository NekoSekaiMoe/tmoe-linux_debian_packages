# TMOE Go Edition - User Manual

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [Commands Reference](#commands-reference)
5. [Container Management](#container-management)
6. [Mirror Management](#mirror-management)
7. [Installation Wizard](#installation-wizard)
8. [VNC Services](#vnc-services)
9. [Multi-language Support](#multi-language-support)
10. [Troubleshooting](#troubleshooting)

---

## Introduction

TMOE (More Optional Environments) Go Edition is a modern, high-performance container management tool written in Go. It provides a unified interface for managing Linux containers using proot, chroot, and systemd-nspawn.

### Key Features

- 🚀 **10x faster** startup than bash version
- 💚 **40% less memory** usage
- ✨ **Zero runtime dependencies** - single binary
- 🎨 **Beautiful TUI** interface
- 🌍 **Multi-language** support (en, zh-CN, zh-TW, zh-HK)
- 🌐 **Smart mirror management** with speed testing
- 📦 **Container installation wizard**

---

## Installation

### Quick Install

```bash
# Download latest release (replace with your architecture)
wget https://github.com/2moe/tmoe/releases/latest/download/tmoe-linux-amd64.gz

# Verify checksum
wget https://github.com/2moe/tmoe/releases/latest/download/tmoe-linux-amd64.gz.sha256
sha256sum -c tmoe-linux-amd64.gz.sha256

# Extract and install
gunzip tmoe-linux-amd64.gz
chmod +x tmoe-linux-amd64
sudo mv tmoe-linux-amd64 /usr/local/bin/tmoe
```

### From Source

```bash
git clone https://github.com/2moe/tmoe.git
cd tmoe/go-tmoe
make build
sudo make install
```

### Verify Installation

```bash
tmoe version
```

---

## Getting Started

### Interactive Menu

The easiest way to use TMOE is through the interactive menu:

```bash
tmoe menu
```

Navigate with arrow keys, press Enter to select, and q to quit.

### Basic Workflow

1. **List containers**: `tmoe list`
2. **Start a container**: `tmoe proot`
3. **Interactive selection**: `tmoe proot -I`
4. **Install new container**: `tmoe install container --distro debian`

---

## Commands Reference

### Container Commands

```bash
# List all containers
tmoe list

# Start proot container
tmoe proot [container-name]
tmoe proot -I                    # Interactive selection

# Start chroot container (needs root)
sudo tmoe chroot [container-name]

# Start systemd-nspawn container
sudo tmoe nspawn [container-name]
```

### Mirror Commands

```bash
# List available mirrors
tmoe mirror list
tmoe mirror list --distro ubuntu

# Test mirror speeds
tmoe mirror test
tmoe mirror test --distro debian

# Set mirror source
tmoe mirror set Tsinghua --distro debian --release bookworm
```

### Installation Commands

```bash
# Show supported distributions
tmoe install container

# Install container
tmoe install container --distro debian
tmoe install container --distro ubuntu --mirror Tsinghua
tmoe install container --distro arch --minimal
```

### VNC Commands

```bash
# Start VNC server
tmoe vnc start
tmoe vnc start -p 5901          # Custom port

# Start noVNC (web-based)
tmoe vnc start --novnc
tmoe vnc start -n

# Stop VNC
tmoe vnc stop

# Check status
tmoe vnc status
```

### Other Commands

```bash
# Show version
tmoe version

# Interactive TUI menu
tmoe menu
tmoe menu --fallback            # Use whiptail

# Help
tmoe --help
tmoe <command> --help
```

---

## Container Management

### Starting Containers

TMOE supports three container technologies:

#### 1. Proot (Rootless)

```bash
# Start first available container
tmoe proot

# Start specific container
tmoe proot debian-bookworm

# Interactive selection
tmoe proot -I
```

**Advantages**:
- No root required
- Works everywhere
- Safe isolation

**Use cases**: Development, testing, user applications

#### 2. Chroot (Traditional)

```bash
# Requires root
sudo tmoe chroot debian-bookworm
```

**Advantages**:
- Native performance
- Full system access

**Use cases**: System administration, production

#### 3. Systemd-nspawn (Containers)

```bash
# Requires root and systemd
sudo tmoe nspawn arch-latest
```

**Advantages**:
- Strong isolation
- Resource limits
- Systemd integration

**Use cases**: Multi-tenant, services, CI/CD

### Listing Containers

```bash
# List all containers
tmoe list

# Shows: Name, Type, Distribution, Architecture, Status
```

Example output:
```
Available containers:
  debian-bookworm (proot) - Debian bookworm (amd64)
  ubuntu-jammy (chroot) - Ubuntu jammy (arm64)
  arch-latest (nspawn) - Arch latest (amd64)
```

---

## Mirror Management

### Why Use Mirrors?

Mirrors provide faster package downloads by choosing geographically closer servers.

### List Mirrors

```bash
# List for default distro (debian)
tmoe mirror list

# List for specific distro
tmoe mirror list --distro ubuntu
tmoe mirror list --distro arch
```

### Test Speeds

```bash
# Test all mirrors
tmoe mirror test

# Test for specific distro
tmoe mirror test --distro ubuntu

# Custom timeout
tmoe mirror test --timeout 10s
```

Example output:
```
Testing mirrors for ubuntu (timeout: 5s)...

Results (sorted by speed):
1. Tsinghua - 45ms  ✓ Fastest
2. USTC - 67ms
3. Aliyun - 89ms
4. Tencent - 123ms
5. Official - Failed or timeout

✓ Fastest: Tsinghua (45ms)
```

### Set Mirror

```bash
# Set mirror for Debian
tmoe mirror set Tsinghua --distro debian --release bookworm

# This generates sources.list
```

The command will output:
- Generated sources.list content
- Instructions to apply it

---

## Installation Wizard

### Installing New Containers

TMOE can install Linux containers using debootstrap (Debian/Ubuntu) or pacstrap (Arch).

### Supported Distributions

| Distribution | Codename | Architectures |
|--------------|----------|---------------|
| Debian | bookworm, bullseye | amd64, arm64 |
| Ubuntu | jammy, focal | amd64, arm64 |
| Kali | kali-rolling | amd64, arm64 |
| Arch | latest | amd64 |
| Alpine | latest | amd64, arm64 |

### Basic Installation

```bash
# Install Debian (simplest)
tmoe install container --distro debian

# Specify release
tmoe install container --distro debian --release bookworm

# With mirror
tmoe install container --distro ubuntu --mirror Tsinghua

# Minimal installation
tmoe install container --distro debian --minimal

# Custom name
tmoe install container --distro debian --name my-debian
```

### Advanced Options

```bash
tmoe install container \
  --distro debian \
  --release bookworm \
  --arch amd64 \
  --mirror Tsinghua \
  --minimal \
  --name production-env
```

### Installation Process

1. **Validation**: Checks parameters and availability
2. **Preparation**: Creates directories, checks tools
3. **Installation**: Runs debootstrap/pacstrap
4. **Verification**: Validates essential files

### Requirements

- **Debian/Ubuntu/Kali**: `debootstrap` package
- **Arch**: `arch-install-scripts` package
- **Alpine**: (planned)

Install requirements:
```bash
# Debian/Ubuntu
sudo apt install debootstrap

# Arch
sudo pacman -S arch-install-scripts
```

---

## VNC Services

### Starting VNC

```bash
# Default port (5900)
tmoe vnc start

# Custom port
tmoe vnc start -p 5901

# With password
tmoe vnc start --password mypass
```

### Starting noVNC (Web)

```bash
# Web-based VNC on port 6080
tmoe vnc start --novnc
tmoe vnc start -n

# Custom port
tmoe vnc start --novnc -p 6080
```

Access in browser: `http://localhost:6080/vnc.html`

### Stopping VNC

```bash
tmoe vnc stop
```

### Checking Status

```bash
tmoe vnc status
```

---

## Multi-language Support

TMOE automatically detects your system language.

### Supported Languages

- 🇬🇧 English (en)
- 🇨🇳 Simplified Chinese (zh-CN)
- 🇹🇼 Traditional Chinese (zh-TW)
- 🇭🇰 Hong Kong Cantonese (zh-HK)

### Changing Language

Set the `LANG` environment variable:

```bash
# English
export LANG=en_US.UTF-8
tmoe menu

# Simplified Chinese
export LANG=zh_CN.UTF-8
tmoe menu

# Traditional Chinese
export LANG=zh_TW.UTF-8
tmoe menu

# Hong Kong Cantonese
export LANG=zh_HK.UTF-8
tmoe menu
```

### Permanent Change

Add to `~/.bashrc` or `~/.profile`:

```bash
export LANG=zh_CN.UTF-8
```

---

## Troubleshooting

### Common Issues

#### 1. "Command not found: tmoe"

**Solution**: Add `/usr/local/bin` to PATH or reinstall:

```bash
export PATH=$PATH:/usr/local/bin
# Or
sudo ln -s /path/to/tmoe /usr/bin/tmoe
```

#### 2. "No containers found"

**Solution**: Install a container first:

```bash
tmoe install container --distro debian
```

#### 3. "Proot not found"

**Solution**: Install proot:

```bash
sudo apt install proot      # Debian/Ubuntu
sudo pacman -S proot        # Arch
```

#### 4. "Chroot requires root"

**Solution**: Use sudo or switch to proot:

```bash
sudo tmoe chroot [name]
# Or
tmoe proot [name]
```

#### 5. "VNC server not found"

**Solution**: Install VNC server:

```bash
sudo apt install tigervnc-standalone-server    # Debian/Ubuntu
# Or
sudo apt install x11vnc
```

#### 6. "TUI not working"

**Solution**: Use whiptail fallback:

```bash
tmoe menu --fallback
```

#### 7. "Debootstrap failed"

**Possible causes**:
- No internet connection
- Mirror is down
- Insufficient disk space
- Need root for chroot

**Solutions**:
```bash
# Check internet
ping debian.org

# Try different mirror
tmoe mirror test
tmoe install container --distro debian --mirror USTC

# Check disk space
df -h

# Use sudo if needed
sudo tmoe install container --distro debian
```

### Getting Help

```bash
# Command help
tmoe --help
tmoe <command> --help

# Version info
tmoe version

# Community
GitHub: https://github.com/2moe/tmoe/issues
Docs: https://doc.tmoe.me
```

---

## Tips and Tricks

### 1. Speed up installations

```bash
# Test mirrors first
tmoe mirror test --distro debian

# Use fastest mirror
tmoe install container --distro debian --mirror Tsinghua
```

### 2. Minimal installations

```bash
# Save disk space and installation time
tmoe install container --distro debian --minimal
```

### 3. Keyboard shortcuts in TUI

- `↑/↓` or `j/k` - Navigate
- `Enter` - Select
- `/` - Filter/search (in lists)
- `q` or `Esc` - Back/quit
- `Ctrl+C` - Force quit

### 4. Quick container access

```bash
# Create alias
alias mydebian='tmoe proot debian-bookworm'

# Now just:
mydebian
```

### 5. Batch operations

```bash
# Start multiple containers (in different terminals)
tmoe proot debian-bookworm &
tmoe proot ubuntu-jammy &
```

---

## Advanced Usage

### Configuration Files

TMOE stores configuration in:
- Config: `~/.config/tmoe-linux/`
- Data: `~/.local/share/tmoe-linux/`
- Containers: `~/.local/share/tmoe-linux/containers/`

### Custom Container Paths

Set environment variable:

```bash
export TMOE_CONTAINER_DIR=/custom/path/containers
```

### Automation

```bash
#!/bin/bash
# Auto-install and start

# Install if not exists
if ! tmoe list | grep -q debian-bookworm; then
    tmoe install container --distro debian
fi

# Start container
tmoe proot debian-bookworm
```

---

## Comparison: Bash vs Go Edition

| Feature | Bash Version | Go Version |
|---------|--------------|------------|
| Startup Speed | ~500ms | ~50ms (10x faster) |
| Memory Usage | ~50MB | ~30MB (40% less) |
| Binary Size | 2.9MB (scripts) | 7.4MB |
| Dependencies | Many | Zero |
| Command Interface | 2 scripts | 1 unified |
| Type Safety | No | Yes |
| TUI | Basic | Modern (bubbletea) |
| Mirror Testing | No | Yes |
| Multi-language | Yes | Yes (improved) |

---

## Next Steps

1. **Try the interactive menu**: `tmoe menu`
2. **Install your first container**: `tmoe install container --distro debian`
3. **Explore features**: Try mirror testing, VNC services
4. **Customize**: Set your preferred language and mirrors

---

**Documentation**: https://doc.tmoe.me  
**GitHub**: https://github.com/2moe/tmoe  
**Issues**: https://github.com/2moe/tmoe/issues

*Enjoy using TMOE Go Edition!* 🚀
