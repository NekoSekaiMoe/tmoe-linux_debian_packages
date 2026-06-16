TMOE_VERSION ?= 2.0.0-dev
GIT_COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BUILD_TIME := $(shell date -u '+%Y-%m-%d_%H:%M:%S')

LDFLAGS := -s -w \
	-X 'main.Version=$(TMOE_VERSION)' \
	-X 'main.Commit=$(GIT_COMMIT)' \
	-X 'main.BuildTime=$(BUILD_TIME)'

# Binary output path
OUTPUT_DIR := bin
BINARY_NAME := tmoe

# Go build flags
GOFLAGS := -trimpath

.PHONY: all
all: build

.PHONY: build
build:
	@echo "Building tmoe $(TMOE_VERSION)..."
	@mkdir -p $(OUTPUT_DIR)
	go build $(GOFLAGS) -ldflags="$(LDFLAGS)" -o $(OUTPUT_DIR)/$(BINARY_NAME) ./cmd/tmoe

.PHONY: install
install: build
	@echo "Installing tmoe to /usr/local/bin..."
	@sudo cp $(OUTPUT_DIR)/$(BINARY_NAME) /usr/local/bin/$(BINARY_NAME)
	@sudo chmod +x /usr/local/bin/$(BINARY_NAME)
	@echo "Installed successfully!"

.PHONY: clean
clean:
	@echo "Cleaning..."
	@rm -rf $(OUTPUT_DIR)

.PHONY: test
test:
	@echo "Running tests..."
	go test -v ./...

.PHONY: fmt
fmt:
	@echo "Formatting code..."
	go fmt ./...

.PHONY: vet
vet:
	@echo "Vetting code..."
	go vet ./...

.PHONY: lint
lint:
	@echo "Linting code..."
	@which golangci-lint > /dev/null || (echo "golangci-lint not installed" && exit 1)
	golangci-lint run ./...

# Cross-compilation targets
.PHONY: build-all
build-all: build-linux-amd64 build-linux-arm64 build-linux-armv7 build-linux-i386

.PHONY: build-linux-amd64
build-linux-amd64:
	@echo "Building for Linux amd64..."
	@mkdir -p $(OUTPUT_DIR)
	GOOS=linux GOARCH=amd64 go build $(GOFLAGS) -ldflags="$(LDFLAGS)" \
		-o $(OUTPUT_DIR)/$(BINARY_NAME)-linux-amd64 ./cmd/tmoe

.PHONY: build-linux-arm64
build-linux-arm64:
	@echo "Building for Linux arm64..."
	@mkdir -p $(OUTPUT_DIR)
	GOOS=linux GOARCH=arm64 go build $(GOFLAGS) -ldflags="$(LDFLAGS)" \
		-o $(OUTPUT_DIR)/$(BINARY_NAME)-linux-arm64 ./cmd/tmoe

.PHONY: build-linux-armv7
build-linux-armv7:
	@echo "Building for Linux armv7..."
	@mkdir -p $(OUTPUT_DIR)
	GOOS=linux GOARCH=arm GOARM=7 go build $(GOFLAGS) -ldflags="$(LDFLAGS)" \
		-o $(OUTPUT_DIR)/$(BINARY_NAME)-linux-armv7 ./cmd/tmoe

.PHONY: build-linux-i386
build-linux-i386:
	@echo "Building for Linux i386..."
	@mkdir -p $(OUTPUT_DIR)
	GOOS=linux GOARCH=386 go build $(GOFLAGS) -ldflags="$(LDFLAGS)" \
		-o $(OUTPUT_DIR)/$(BINARY_NAME)-linux-i386 ./cmd/tmoe

.PHONY: build-linux-mips64el
build-linux-mips64el:
	@echo "Building for Linux mips64el..."
	@mkdir -p $(OUTPUT_DIR)
	GOOS=linux GOARCH=mips64le go build $(GOFLAGS) -ldflags="$(LDFLAGS)" \
		-o $(OUTPUT_DIR)/$(BINARY_NAME)-linux-mips64el ./cmd/tmoe

.PHONY: build-linux-riscv64
build-linux-riscv64:
	@echo "Building for Linux riscv64..."
	@mkdir -p $(OUTPUT_DIR)
	GOOS=linux GOARCH=riscv64 go build $(GOFLAGS) -ldflags="$(LDFLAGS)" \
		-o $(OUTPUT_DIR)/$(BINARY_NAME)-linux-riscv64 ./cmd/tmoe

# Release builds (cross-compile for all architectures)
.PHONY: release
release: clean
	@echo "Building release binaries..."
	@$(MAKE) build-linux-amd64
	@$(MAKE) build-linux-arm64
	@$(MAKE) build-linux-armv7
	@$(MAKE) build-linux-i386
	@$(MAKE) build-linux-mips64el
	@$(MAKE) build-linux-riscv64
	@echo "Release binaries built in $(OUTPUT_DIR)/"
	@ls -lh $(OUTPUT_DIR)/

.PHONY: help
help:
	@echo "TMOE Go Build System"
	@echo ""
	@echo "Usage:"
	@echo "  make build           - Build for current platform"
	@echo "  make install         - Build and install to /usr/local/bin"
	@echo "  make build-all       - Build for common Linux architectures"
	@echo "  make release         - Build for all supported architectures"
	@echo "  make test            - Run tests"
	@echo "  make fmt             - Format code"
	@echo "  make vet             - Run go vet"
	@echo "  make lint            - Run linter (requires golangci-lint)"
	@echo "  make clean           - Clean build artifacts"
	@echo ""
	@echo "Architecture-specific builds:"
	@echo "  make build-linux-amd64"
	@echo "  make build-linux-arm64"
	@echo "  make build-linux-armv7"
	@echo "  make build-linux-i386"
	@echo "  make build-linux-mips64el"
	@echo "  make build-linux-riscv64"
