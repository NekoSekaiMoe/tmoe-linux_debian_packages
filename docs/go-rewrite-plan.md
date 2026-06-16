# TMOE Go Rewrite Plan

## Project Overview

Rewrite TMOE container management tool in Go while keeping `debian.sh` as the bootstrap entry point.

## Architecture Design

```
┌─────────────────────────────────────────────────────────────┐
│                         debian.sh                            │
│              (POSIX sh bootstrap, unchanged)                 │
└──────────────────┬──────────────────────────────────────────┘
                   │ downloads & executes
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                      tmoe (Go binary)                        │
├─────────────────────────────────────────────────────────────┤
│  CLI Layer (cobra)                                           │
│    ├── tmoe proot                                            │
│    ├── tmoe chroot                                           │
│    ├── tmoe nspawn                                           │
│    ├── tmoe vnc {start|stop}                                 │
│    ├── tmoe list                                             │
│    └── tmoe config                                           │
├─────────────────────────────────────────────────────────────┤
│  TUI Layer (bubbletea / fallback to whiptail)               │
│    ├── Main Menu                                             │
│    ├── Container Selection                                   │
│    └── Configuration Wizard                                  │
├─────────────────────────────────────────────────────────────┤
│  Business Logic                                              │
│    ├── Container Manager (proot/chroot/nspawn)              │
│    ├── VNC Service Manager                                   │
│    ├── Package Manager Integration                           │
│    ├── Architecture Detection                                │
│    └── Locale/i18n                                           │
├─────────────────────────────────────────────────────────────┤
│  Storage Layer                                               │
│    ├── Config Files (~/.config/tmoe-linux/)                 │
│    ├── Container Storage (~/.local/share/tmoe-linux/)       │
│    └── Compatibility with existing structure                │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
tmoe/
├── cmd/
│   └── tmoe/
│       └── main.go                 # Entry point
├── internal/
│   ├── app/
│   │   └── app.go                  # Application context
│   ├── cli/
│   │   ├── root.go                 # Root command
│   │   ├── proot.go                # Proot command
│   │   ├── chroot.go               # Chroot command
│   │   ├── nspawn.go               # Systemd-nspawn command
│   │   ├── vnc.go                  # VNC commands
│   │   └── list.go                 # List containers
│   ├── tui/
│   │   ├── menu.go                 # Main menu
│   │   ├── styles.go               # TUI styles
│   │   └── whiptail.go             # Fallback to whiptail
│   ├── container/
│   │   ├── manager.go              # Container manager interface
│   │   ├── proot.go                # Proot implementation
│   │   ├── chroot.go               # Chroot implementation
│   │   ├── nspawn.go               # Nspawn implementation
│   │   └── qemu.go                 # QEMU implementation
│   ├── vnc/
│   │   ├── server.go               # VNC server management
│   │   └── novnc.go                # NoVNC web service
│   ├── pkg/
│   │   ├── apt.go                  # APT integration
│   │   └── mirrors.go              # Mirror management
│   ├── system/
│   │   ├── arch.go                 # Architecture detection
│   │   ├── distro.go               # Distribution detection
│   │   └── mount.go                # Mount operations
│   ├── config/
│   │   ├── config.go               # Configuration management
│   │   ├── paths.go                # Path constants
│   │   └── migration.go            # Migrate old configs
│   └── i18n/
│       ├── locale.go               # Locale management
│       └── translations/
│           ├── en_US.yaml
│           ├── zh_CN.yaml
│           ├── zh_TW.yaml
│           └── zh_HK.yaml
├── pkg/                            # Public packages (if needed)
├── scripts/
│   ├── build.sh                    # Build script
│   └── release.sh                  # Cross-compile for all archs
├── debian.sh                       # Existing bootstrap (modified)
├── go.mod
├── go.sum
├── Makefile
└── README.md
```

## Technology Stack

### Core Libraries

- **CLI Framework**: `github.com/spf13/cobra` - Industry standard
- **TUI Framework**: `github.com/charmbracelet/bubbletea` - Modern, beautiful
- **Configuration**: `github.com/spf13/viper` - Config management
- **Logging**: `github.com/sirupsen/logrus` or `go.uber.org/zap`
- **i18n**: `github.com/nicksnyder/go-i18n/v2`
- **Process Management**: `os/exec` (stdlib)
- **System Calls**: `golang.org/x/sys/unix`

### Optional Libraries

- **Progress Bars**: `github.com/schollz/progressbar/v3`
- **Colors**: `github.com/fatih/color`
- **Prompts**: `github.com/AlecAivazis/survey/v2`

## Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Goal**: Basic CLI structure and architecture detection

- [x] Set up Go module and project structure
- [x] Implement CLI framework with cobra
- [x] Architecture detection (arch.go)
- [x] Path and config management
- [x] Logging infrastructure
- [x] Basic error handling

**Deliverable**: `tmoe --help` works, shows all commands

### Phase 2: Container Management (Week 3-5)

**Goal**: Core container operations

- [ ] Container manager interface
- [ ] Proot integration
- [ ] Chroot integration  
- [ ] Systemd-nspawn integration
- [ ] Container listing and status
- [ ] Configuration file compatibility

**Deliverable**: `tmoe proot`, `tmoe chroot`, `tmoe nspawn` work

### Phase 3: TUI Interface (Week 6-7)

**Goal**: Interactive menus

- [ ] Main menu with bubbletea
- [ ] Container selection UI
- [ ] Configuration wizard
- [ ] Fallback to whiptail for compatibility
- [ ] Color scheme matching original

**Deliverable**: Beautiful interactive menus

### Phase 4: VNC Services (Week 8)

**Goal**: VNC/noVNC management

- [ ] VNC server start/stop
- [ ] NoVNC web service
- [ ] Process management
- [ ] Port management

**Deliverable**: `tmoe vnc start` works

### Phase 5: Package Management (Week 9)

**Goal**: APT integration and mirrors

- [ ] APT command wrappers
- [ ] Mirror source management
- [ ] Distribution detection (Debian/Ubuntu/Kali)
- [ ] Package installation wizard

**Deliverable**: Mirror switching works

### Phase 6: i18n & Localization (Week 10)

**Goal**: Multi-language support

- [ ] Locale detection
- [ ] Translation files (en, zh-CN, zh-TW, zh-HK)
- [ ] Language switching
- [ ] Compatibility with existing locale files

**Deliverable**: All menus support 4+ languages

### Phase 7: Integration & Testing (Week 11-12)

**Goal**: End-to-end testing

- [ ] Integration tests
- [ ] Multi-architecture testing (arm64, amd64, armhf)
- [ ] Migration testing (old configs → new)
- [ ] Performance benchmarking
- [ ] Documentation

**Deliverable**: Production-ready release

### Phase 8: Bootstrap Integration (Week 13)

**Goal**: Seamless deployment

- [ ] Modify debian.sh to download Go binary
- [ ] Set up release artifacts (GitHub Releases)
- [ ] Binary hosting (dl.tmoe.me)
- [ ] Checksum verification
- [ ] Auto-update mechanism

**Deliverable**: `curl | sh` installation works

## Binary Distribution

### Cross-Compilation Targets

```bash
# Linux
GOOS=linux GOARCH=amd64   → tmoe-linux-amd64
GOOS=linux GOARCH=arm64   → tmoe-linux-arm64
GOOS=linux GOARCH=arm     GOARM=7 → tmoe-linux-armv7
GOOS=linux GOARCH=386     → tmoe-linux-i386
GOOS=linux GOARCH=mips64le → tmoe-linux-mips64el
GOOS=linux GOARCH=riscv64 → tmoe-linux-riscv64
```

### Binary Size Optimization

```bash
# Build flags for minimal size
go build -ldflags="-s -w" -trimpath

# Further compression with UPX
upx --best --lzma tmoe
```

**Expected sizes**:
- Uncompressed: 8-15 MB
- UPX compressed: 3-6 MB

## Compatibility Strategy

### Configuration Migration

```go
// Migrate old bash configs to new format
type ConfigMigrator struct {
    oldPaths []string
    newPath  string
}

func (m *ConfigMigrator) Migrate() error {
    // Read ~/.config/tmoe-linux/chroot.conf
    // Convert SYSTEMD_NSPAWN=true → yaml/toml
    // Preserve existing containers
}
```

### Gradual Rollout

1. **v2.0.0-beta**: Go binary, opt-in via `debian.sh --beta`
2. **v2.0.0-rc**: Default to Go, fallback to bash with `--legacy`
3. **v2.0.0**: Full Go release, bash scripts deprecated

## Testing Strategy

### Unit Tests
```bash
go test ./internal/... -v -cover
```

### Integration Tests
```bash
# Test in Docker containers
docker run --rm -it debian:bookworm bash -c "
  curl -L https://l.tmoe.me/debian.sh | sh
"
```

### Architecture Tests
```bash
# QEMU user-mode emulation
for arch in amd64 arm64 armhf; do
  qemu-$arch-static ./tmoe-$arch --version
done
```

## Performance Targets

| Metric | Bash (current) | Go (target) | Improvement |
|--------|----------------|-------------|-------------|
| Cold start | ~500ms | <100ms | 5x faster |
| Container launch | ~2s | ~1.5s | 25% faster |
| Binary size | 2.9MB (scripts) | 5-8MB | Similar |
| Memory usage | ~50MB (bash) | ~20MB (Go) | 60% less |

## Risk Mitigation

### Risk: TUI looks different
- **Mitigation**: Keep whiptail fallback, match color schemes exactly

### Risk: Missing features during transition  
- **Mitigation**: Feature parity checklist, beta testing period

### Risk: Users reject new version
- **Mitigation**: Easy rollback via `--legacy` flag, clear migration guide

### Risk: Architecture compatibility issues
- **Mitigation**: Test on 6+ architectures, QEMU CI pipeline

## Success Metrics

- ✅ 100% feature parity with bash version
- ✅ <100ms startup time
- ✅ Works on 6+ architectures (amd64, arm64, armhf, i386, mips64el, riscv64)
- ✅ 4+ languages supported
- ✅ Zero runtime dependencies (static binary)
- ✅ User adoption >50% within 3 months

## Timeline

**Total**: ~13 weeks (3 months)

- Weeks 1-2: Foundation
- Weeks 3-5: Core containers
- Weeks 6-7: TUI
- Week 8: VNC
- Week 9: Package management
- Week 10: i18n
- Weeks 11-12: Testing
- Week 13: Deployment

**Estimated effort**: ~260 hours (full-time) or ~520 hours (part-time)
