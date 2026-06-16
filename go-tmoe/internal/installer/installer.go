package installer

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/2moe/tmoe/internal/config"
	"github.com/2moe/tmoe/internal/system"
)

// Distro represents a Linux distribution
type Distro struct {
	Name    string
	Codename string
	Arch    string
}

// InstallerConfig holds installation configuration
type InstallerConfig struct {
	Distro      Distro
	Mirror      string
	InstallPath string
	Minimal     bool
}

// ContainerInstaller handles container installation
type ContainerInstaller struct {
	cfg    *config.Config
	config InstallerConfig
}

// NewContainerInstaller creates a new container installer
func NewContainerInstaller(installConfig InstallerConfig) *ContainerInstaller {
	return &ContainerInstaller{
		cfg:    config.Get(),
		config: installConfig,
	}
}

// GetSupportedDistros returns supported distributions
func GetSupportedDistros() []Distro {
	return []Distro{
		{Name: "debian", Codename: "bookworm", Arch: "amd64"},
		{Name: "debian", Codename: "bookworm", Arch: "arm64"},
		{Name: "debian", Codename: "bullseye", Arch: "amd64"},
		{Name: "ubuntu", Codename: "jammy", Arch: "amd64"},
		{Name: "ubuntu", Codename: "jammy", Arch: "arm64"},
		{Name: "ubuntu", Codename: "focal", Arch: "amd64"},
		{Name: "kali", Codename: "kali-rolling", Arch: "amd64"},
		{Name: "kali", Codename: "kali-rolling", Arch: "arm64"},
		{Name: "arch", Codename: "latest", Arch: "amd64"},
		{Name: "alpine", Codename: "latest", Arch: "amd64"},
		{Name: "alpine", Codename: "latest", Arch: "arm64"},
	}
}

// DetectHostArch detects the host architecture
func DetectHostArch() (system.ArchType, error) {
	return system.DetectArch()
}

// Install installs a container
func (i *ContainerInstaller) Install() error {
	// Create installation directory
	installPath := i.config.InstallPath
	if installPath == "" {
		installPath = filepath.Join(i.cfg.ContainerDir,
			fmt.Sprintf("%s-%s", i.config.Distro.Name, i.config.Distro.Codename))
	}

	if err := os.MkdirAll(installPath, 0755); err != nil {
		return fmt.Errorf("failed to create install directory: %w", err)
	}

	// Check for installation method
	switch i.config.Distro.Name {
	case "debian", "ubuntu", "kali":
		return i.installWithDebootstrap(installPath)
	case "arch":
		return i.installWithPacstrap(installPath)
	case "alpine":
		return i.installAlpine(installPath)
	default:
		return fmt.Errorf("unsupported distribution: %s", i.config.Distro.Name)
	}
}

// installWithDebootstrap installs using debootstrap
func (i *ContainerInstaller) installWithDebootstrap(installPath string) error {
	// Check if debootstrap is available
	debootstrap, err := exec.LookPath("debootstrap")
	if err != nil {
		return fmt.Errorf("debootstrap not found, please install it: apt install debootstrap")
	}

	// Build debootstrap command
	args := []string{
		"--arch=" + i.config.Distro.Arch,
		i.config.Distro.Codename,
		installPath,
	}

	if i.config.Mirror != "" {
		args = append(args, i.config.Mirror)
	}

	if i.config.Minimal {
		args = append(args, "--variant=minbase")
	}

	fmt.Printf("Installing %s %s...\n", i.config.Distro.Name, i.config.Distro.Codename)
	fmt.Printf("Command: %s %v\n", debootstrap, args)

	cmd := exec.Command(debootstrap, args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Run(); err != nil {
		return fmt.Errorf("debootstrap failed: %w", err)
	}

	fmt.Printf("✓ Installation complete: %s\n", installPath)
	return nil
}

// installWithPacstrap installs Arch Linux using pacstrap
func (i *ContainerInstaller) installWithPacstrap(installPath string) error {
	pacstrap, err := exec.LookPath("pacstrap")
	if err != nil {
		return fmt.Errorf("pacstrap not found, please install arch-install-scripts")
	}

	packages := []string{"base"}
	if !i.config.Minimal {
		packages = append(packages, "base-devel")
	}

	args := append([]string{installPath}, packages...)

	fmt.Printf("Installing Arch Linux...\n")
	cmd := exec.Command(pacstrap, args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Run(); err != nil {
		return fmt.Errorf("pacstrap failed: %w", err)
	}

	fmt.Printf("✓ Installation complete: %s\n", installPath)
	return nil
}

// installAlpine installs Alpine Linux
func (i *ContainerInstaller) installAlpine(installPath string) error {
	return fmt.Errorf("Alpine installation not yet implemented")
}

// ValidateInstallation validates the installation
func (i *ContainerInstaller) ValidateInstallation() error {
	// Check if essential files exist
	essentialPaths := []string{
		filepath.Join(i.config.InstallPath, "bin/sh"),
		filepath.Join(i.config.InstallPath, "etc"),
		filepath.Join(i.config.InstallPath, "usr"),
	}

	for _, path := range essentialPaths {
		if _, err := os.Stat(path); os.IsNotExist(err) {
			return fmt.Errorf("installation validation failed: %s does not exist", path)
		}
	}

	return nil
}
