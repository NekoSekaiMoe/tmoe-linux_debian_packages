# Bootstrap Integration for Go Edition

## Overview

This document describes how to integrate the TMOE Go edition binary download into the existing debian.sh bootstrap script.

## Architecture Detection

The Go binary naming convention:
- `tmoe-linux-amd64` - Intel/AMD 64-bit
- `tmoe-linux-arm64` - ARM 64-bit
- `tmoe-linux-armv7` - ARM 32-bit v7
- `tmoe-linux-386` - Intel/AMD 32-bit
- `tmoe-linux-mips64le` - MIPS 64-bit LE
- `tmoe-linux-riscv64` - RISC-V 64-bit

## Integration Plan

### Phase 1: Add Go Binary Detection (debian.sh)

```sh
# Detect architecture for Go binary
detect_go_arch() {
    local arch
    arch=$(uname -m)
    
    case "$arch" in
        x86_64|amd64)
            echo "amd64"
            ;;
        aarch64|arm64)
            echo "arm64"
            ;;
        armv7l)
            echo "armv7"
            ;;
        i386|i686)
            echo "386"
            ;;
        mips64el)
            echo "mips64le"
            ;;
        riscv64)
            echo "riscv64"
            ;;
        *)
            echo ""
            ;;
    esac
}

# Download Go binary
download_go_binary() {
    local arch version base_url binary_name
    
    arch=$(detect_go_arch)
    if [ -z "$arch" ]; then
        return 1
    fi
    
    version="${TMOE_GO_VERSION:-latest}"
    base_url="https://github.com/2moe/tmoe/releases"
    binary_name="tmoe-linux-${arch}"
    
    # Try GitHub releases
    if [ "$version" = "latest" ]; then
        download_url="${base_url}/latest/download/${binary_name}.gz"
    else
        download_url="${base_url}/download/${version}/${binary_name}.gz"
    fi
    
    # Download with fallback
    if command -v curl >/dev/null 2>&1; then
        curl -fSL "$download_url" -o "/tmp/${binary_name}.gz" || return 1
    elif command -v wget >/dev/null 2>&1; then
        wget -q "$download_url" -O "/tmp/${binary_name}.gz" || return 1
    else
        return 1
    fi
    
    # Verify and extract
    if [ -f "/tmp/${binary_name}.gz" ]; then
        gunzip "/tmp/${binary_name}.gz" || return 1
        chmod +x "/tmp/${binary_name}"
        
        # Install to user bin
        local install_dir="${HOME}/.local/bin"
        mkdir -p "$install_dir"
        mv "/tmp/${binary_name}" "${install_dir}/tmoe"
        
        # Add to PATH if not already
        case ":$PATH:" in
            *":${install_dir}:"*) ;;
            *) export PATH="${install_dir}:$PATH" ;;
        esac
        
        return 0
    fi
    
    return 1
}

# Check for Go binary
check_go_binary() {
    if command -v tmoe >/dev/null 2>&1; then
        # Verify it's the Go version
        if tmoe version 2>/dev/null | grep -q "TMOE.*dev\|TMOE.*[0-9]"; then
            return 0
        fi
    fi
    return 1
}
```

### Phase 2: Integration Logic

```sh
# Main bootstrap logic
main() {
    # Try Go binary first
    if check_go_binary; then
        echo "✓ TMOE Go edition found"
        exec tmoe "$@"
    fi
    
    # Try to download Go binary
    echo "Downloading TMOE Go edition..."
    if download_go_binary; then
        echo "✓ TMOE Go edition installed"
        exec tmoe "$@"
    fi
    
    # Fallback to AWK/bash version
    echo "Falling back to bash version..."
    # ... existing debian.sh logic ...
}
```

### Phase 3: Environment Variables

Users can control behavior:

```sh
# Use specific version
export TMOE_GO_VERSION="v2.0.0"

# Force bash version
export TMOE_USE_BASH=1

# Skip Go binary check
export TMOE_SKIP_GO=1
```

## Implementation Strategy

### Option 1: Minimal Integration (Recommended)

Modify debian.sh to:
1. Check if `tmoe` (Go binary) exists in PATH
2. If yes, execute it and exit
3. If no, continue with existing AWK logic

```sh
# At the beginning of debian.sh
if command -v tmoe >/dev/null 2>&1 && [ -z "$TMOE_USE_BASH" ]; then
    if tmoe version 2>/dev/null | grep -q "2\."; then
        exec tmoe "$@"
    fi
fi

# ... rest of debian.sh ...
```

### Option 2: Full Integration

Complete replacement with download logic:
1. Try to find Go binary
2. Try to download Go binary
3. Fall back to AWK version

### Option 3: Separate Script

Create `tmoe-bootstrap.sh`:
- Downloads and installs Go binary
- Can be run independently
- debian.sh checks for it

## Download Sources

### Primary: GitHub Releases

```
https://github.com/2moe/tmoe/releases/latest/download/tmoe-linux-amd64.gz
https://github.com/2moe/tmoe/releases/latest/download/tmoe-linux-arm64.gz
...
```

### Fallback: Custom CDN

```
https://dl.tmoe.me/go/latest/tmoe-linux-amd64.gz
https://dl.tmoe.me/go/latest/tmoe-linux-arm64.gz
...
```

### Mirror: Gitee

```
https://gitee.com/mo2/tmoe/releases/latest/download/tmoe-linux-amd64.gz
...
```

## Verification

### Checksum Verification

```sh
# Download checksum
curl -fSL "${download_url}.sha256" -o "/tmp/${binary_name}.gz.sha256"

# Verify
cd /tmp
sha256sum -c "${binary_name}.gz.sha256" || return 1
```

### Signature Verification (Future)

```sh
# Download signature
curl -fSL "${download_url}.sig" -o "/tmp/${binary_name}.gz.sig"

# Verify with GPG
gpg --verify "/tmp/${binary_name}.gz.sig" "/tmp/${binary_name}.gz"
```

## User Experience

### First Run

```
$ curl -L https://l.tmoe.me/2.awk | awk -f -

Downloading TMOE Go edition...
✓ Downloaded tmoe-linux-amd64 (7.4 MB)
✓ Verified checksum
✓ Installed to ~/.local/bin/tmoe

TMOE Go Edition - More Optional Environments

[Interactive menu appears]
```

### Subsequent Runs

```
$ tmoe menu

TMOE Go Edition
[Menu loads instantly]
```

## Backwards Compatibility

The integration maintains full backwards compatibility:

1. **Existing users**: AWK version continues to work
2. **New users**: Get Go version by default
3. **Opt-out**: Set `TMOE_USE_BASH=1`
4. **Gradual migration**: Both versions coexist

## Testing Plan

### Test Matrix

| Scenario | Expected Behavior |
|----------|-------------------|
| Go binary exists | Use Go binary |
| Go binary missing | Download, then use |
| Download fails | Fall back to bash |
| Forced bash mode | Skip Go, use bash |
| Offline mode | Use bash version |
| Custom version | Download specific version |

### Test Script

```sh
#!/bin/bash
# test-bootstrap.sh

# Test 1: Go binary exists
export PATH="/tmp/test-bin:$PATH"
echo "test" > /tmp/test-bin/tmoe
./debian.sh --version
# Expected: Uses /tmp/test-bin/tmoe

# Test 2: Download new binary
rm /tmp/test-bin/tmoe
./debian.sh --version
# Expected: Downloads and uses new binary

# Test 3: Force bash
export TMOE_USE_BASH=1
./debian.sh --version
# Expected: Uses bash/AWK version

# Test 4: Offline mode
unset http_proxy https_proxy
export TMOE_OFFLINE=1
./debian.sh --version
# Expected: Falls back to bash version
```

## Rollout Plan

### Phase 1: Soft Launch (Week 1-2)

- Add Go binary check to debian.sh
- No automatic download yet
- Users can manually install Go binary

### Phase 2: Beta (Week 3-4)

- Enable automatic download
- Limited to opt-in users
- Collect feedback

### Phase 3: Full Release (Week 5+)

- Enable for all users
- Announce on GitHub
- Update documentation

## Configuration

### User Configuration

Location: `~/.config/tmoe-linux/config`

```sh
# Prefer Go edition
TMOE_PREFER_GO=1

# Go binary version
TMOE_GO_VERSION=latest

# Download timeout (seconds)
TMOE_DOWNLOAD_TIMEOUT=30

# Mirror preference
TMOE_MIRROR=github  # github, gitee, custom
```

### System Configuration

Location: `/etc/tmoe/config`

```sh
# System-wide settings
TMOE_DEFAULT_BINARY=go
TMOE_DOWNLOAD_URL=https://dl.tmoe.me/go
```

## Security Considerations

### 1. Checksum Verification

Always verify checksums before execution.

### 2. HTTPS Only

All downloads must use HTTPS.

### 3. Signature Verification

Plan to add GPG signature verification.

### 4. Limited Permissions

Install to user directory, not system-wide.

### 5. Safe Defaults

Fall back to bash version on any security concern.

## Performance Impact

### Download Time

- **7.4 MB binary**: ~2-5 seconds on typical connection
- **Compressed (.gz)**: ~2.5 MB, ~1-2 seconds

### First Run Overhead

- Download: 1-5 seconds
- Extract: <1 second
- Verify: <1 second
- **Total**: 2-7 seconds

### Subsequent Runs

- No overhead
- Instant startup (50ms)

## Monitoring

### Metrics to Track

- Download success rate
- Download time by region
- Binary version distribution
- Fallback frequency
- Error types

### Logging

```sh
# Log location
~/.local/share/tmoe-linux/bootstrap.log

# Log format
2026-06-16 12:00:00 INFO Checking for Go binary
2026-06-16 12:00:00 INFO Downloading from GitHub
2026-06-16 12:00:02 INFO Download complete (7.4 MB)
2026-06-16 12:00:02 INFO Checksum verified
2026-06-16 12:00:03 INFO Installed to ~/.local/bin/tmoe
```

## Future Enhancements

### Auto-Update

```sh
# Check for updates
tmoe update check

# Auto-update
tmoe update install
```

### Delta Updates

Only download changed parts of binary.

### Multi-version Support

```sh
# Install specific version
tmoe-bootstrap install v2.1.0

# Switch versions
tmoe-version use v2.0.0
tmoe-version use v2.1.0
```

## Documentation Updates

After integration, update:

1. **README.md**: Add Go binary as primary installation method
2. **Installation docs**: Show both methods
3. **debian.sh comments**: Explain the flow
4. **CHANGELOG.md**: Document the integration

## Conclusion

The bootstrap integration provides:
- ✅ Seamless transition to Go edition
- ✅ Automatic download and installation
- ✅ Full backwards compatibility
- ✅ User choice and control
- ✅ Graceful fallback

**Recommendation**: Start with Option 1 (Minimal Integration) for safety, then evolve to Option 2 (Full Integration) based on feedback.
