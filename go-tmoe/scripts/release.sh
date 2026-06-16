#!/usr/bin/env bash
# Release script for Go TMOE
# Builds binaries for all architectures and creates release artifacts

set -e

VERSION=${1:-"2.0.0-dev"}
OUTPUT_DIR="release"

echo "Building TMOE Go Edition v${VERSION}"
echo "======================================="

# Clean previous builds
rm -rf ${OUTPUT_DIR}
mkdir -p ${OUTPUT_DIR}

# Build for all architectures
echo ""
echo "Building binaries..."
TMOE_VERSION=${VERSION} make release

# Move binaries to release directory
mv bin/* ${OUTPUT_DIR}/

# Generate checksums
echo ""
echo "Generating checksums..."
cd ${OUTPUT_DIR}
sha256sum tmoe-* > SHA256SUMS
cd ..

# Create tarballs
echo ""
echo "Creating release archives..."
for binary in ${OUTPUT_DIR}/tmoe-*; do
    if [ -f "$binary" ] && [ "$binary" != "${OUTPUT_DIR}/SHA256SUMS" ]; then
        basename=$(basename $binary)
        tar -czf ${OUTPUT_DIR}/${basename}.tar.gz -C ${OUTPUT_DIR} ${basename}
        echo "  Created: ${basename}.tar.gz"
    fi
done

echo ""
echo "Release artifacts:"
ls -lh ${OUTPUT_DIR}/

echo ""
echo "Release v${VERSION} ready in ${OUTPUT_DIR}/"
echo ""
echo "To upload to GitHub releases:"
echo "  gh release create v${VERSION} ${OUTPUT_DIR}/*.tar.gz ${OUTPUT_DIR}/SHA256SUMS"
