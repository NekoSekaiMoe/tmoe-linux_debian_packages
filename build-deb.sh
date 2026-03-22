#!/bin/bash
# Build script for tmoe-python Debian package

set -e

echo "=================================="
echo "TMOE Python Debian Package Builder"
echo "=================================="

# Check for required tools
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "Error: $1 is not installed"
        exit 1
    fi
}

echo "Checking dependencies..."
check_command dpkg-buildpackage
check_command python3
check_command poetry

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Update changelog with current date
if command -v dch &> /dev/null; then
    echo "Updating changelog..."
    dch -D unstable "Build for $(date +%Y-%m-%d)"
fi

# Build the package
echo ""
echo "Building Debian package..."
dpkg-buildpackage -us -uc -b -tc

# Check result
if [ -f ../tmoe-python_*.deb ]; then
    echo ""
    echo "=================================="
    echo "Build successful!"
    echo "=================================="
    ls -lh ../tmoe-python_*.deb
    echo ""
    echo "Install with:"
    echo "  sudo dpkg -i ../tmoe-python_*.deb"
    echo "  sudo apt-get install -f"
else
    echo "Error: Build failed or .deb file not found"
    exit 1
fi
