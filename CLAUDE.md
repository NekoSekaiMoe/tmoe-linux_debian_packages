# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TMOE (More Optional Environments) is a container/environment management tool primarily written in POSIX-compliant shell scripts and AWK. The project is in transition - the current edition has been archived, and a new edition is planned to be written in a more powerful language.

**Current Status**: The old edition (bash/sh scripts) is in maintenance mode and located in `share/old-version/`. New development will use a different architecture.

## Architecture

### Entry Points

1. **debian.sh** - Main bootstrap script (POSIX sh-compliant)
   - Downloads and executes an AWK file from remote sources
   - Fallback mechanism: tries GitHub → Gitee → gi.tmoe.me
   - Can optionally run legacy bash scripts if found in XDG or BSD directories
   - Priority order for AWK implementations: gawk > mawk > nawk > awk

2. **share/app/tmoe** - Symlink to `share/old-version/share/app/tmoe` (bash script)
   - Main application entry point for the old edition
   - Modes: proot, chroot, systemd-nspawn

3. **share/old-version/share/app/manager** - Container manager (bash script)
   - Handles VNC/noVNC, sources list management, container installation

### Directory Structure

```
tmoe/
├── debian.sh              # POSIX sh bootstrap script
├── share/
│   ├── app/               # Application symlinks
│   ├── container/         # Container configs (proot, etc.)
│   ├── doc/              # Multi-language docs (en, zh, zh-HK, zh-TW)
│   ├── icons/            # Icons
│   ├── sed/              # sed scripts
│   └── old-version/      # Archived old edition
│       ├── share/
│       │   ├── app/              # Main app scripts (tmoe, manager)
│       │   ├── container/        # Container implementations (proot, chroot, nspawn, qemu)
│       │   ├── configuration/    # Config files
│       │   ├── compression/      # Compression utilities
│       │   └── environment/      # Environment setup
│       └── tools/
│           ├── gui/              # GUI tools
│           ├── virtualization/   # VMs, Wine, ISO handling
│           ├── webserver/        # Web server configs
│           └── sources/          # Package sources management
└── assets/                # Images, maps, previews
```

### Key Components

- **Container Support**: proot, chroot, systemd-nspawn, QEMU
- **Distribution Focus**: Debian, Ubuntu, Kali, Alpine, Arch
- **GUI Support**: VNC, noVNC, XSDL
- **Localization**: Full i18n support (en, zh-CN, zh-HK, zh-TW)

## Running and Testing

### Quick Start (User Perspective)

```sh
# Standard invocation
curl -LO https://l.tmoe.me/2.awk
awk -f 2.awk

# With specific locale
awk -f 2.awk -v lang=en-us

# Alternative sources
curl -LO https://raw.githubusercontent.com/2moe/tmoe/2/2.awk
curl -LO https://gitee.com/mo2/linux/raw/2/2.awk
```

### Development

**No build system**: This is a script-based project with no compilation step. Changes to shell scripts are immediately executable.

**Testing approach**:
- Run the modified script directly in a container environment
- The project is designed for container environments (proot/chroot/nspawn)
- Manual testing is primary verification method

### Container Modes

```sh
# Via tmoe script
./share/app/tmoe proot    # proot mode
./share/app/tmoe chroot   # chroot mode
./share/app/tmoe nspawn   # systemd-nspawn mode
./share/app/tmoe ls       # list containers
```

## Code Standards

### Shell Script Compliance

- **debian.sh**: POSIX.1-2017 compliant sh
  - No `local`, `declare`, or `typeset` keywords
  - Use functions for reusability
  - Proper error handling with `panic()` and `warning()`

- **Old edition scripts**: bash-specific
  - Can use bash features
  - Located in `share/old-version/`

### AWK Compatibility

Priority order: gawk > mawk > nawk > awk. Code should work with POSIX-compliant AWK implementations. Busybox awk is supported.

## Important Notes

- **Windows is NOT supported** - Do not run on Windows (WSL/WSLg may work but unsupported)
- **Character encoding**: UTF-8 required for proper i18n display
- **Network sources**: Multiple mirror fallbacks (GitHub, Gitee, gi.tmoe.me) for reliability
- **File size validation**: Downloaded AWK files must be > 4 KiB (integrity check)
- **License**: Apache-2.0 (with GPL-2 for mlocate.postinst)
- **Target environment**: Linux containers (especially Debian-based)

## Future Direction

The project maintainer plans to:
1. Rewrite modules in a more powerful language
2. Gradually integrate new implementations
3. Eventually complete a full rewrite

Current edition has known bugs and is maintenance-only. New features will likely go into the rewrite.
