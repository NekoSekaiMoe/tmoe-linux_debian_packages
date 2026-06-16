package pkg

import (
	"fmt"
	"os/exec"
	"strings"
)

// PackageManager is the interface for package managers
type PackageManager interface {
	Update() error
	Install(packages ...string) error
	Remove(packages ...string) error
	Search(query string) ([]Package, error)
	IsInstalled(packageName string) bool
}

// Package represents a package
type Package struct {
	Name        string
	Version     string
	Description string
	Installed   bool
}

// APTManager implements PackageManager for APT (Debian/Ubuntu)
type APTManager struct{}

// NewAPT creates a new APT package manager
func NewAPT() *APTManager {
	return &APTManager{}
}

// Update updates package lists
func (a *APTManager) Update() error {
	cmd := exec.Command("apt", "update")
	return cmd.Run()
}

// Install installs packages
func (a *APTManager) Install(packages ...string) error {
	if len(packages) == 0 {
		return nil
	}
	args := append([]string{"install", "-y"}, packages...)
	cmd := exec.Command("apt", args...)
	return cmd.Run()
}

// Remove removes packages
func (a *APTManager) Remove(packages ...string) error {
	if len(packages) == 0 {
		return nil
	}
	args := append([]string{"remove", "-y"}, packages...)
	cmd := exec.Command("apt", args...)
	return cmd.Run()
}

// Search searches for packages
func (a *APTManager) Search(query string) ([]Package, error) {
	cmd := exec.Command("apt", "search", query)
	output, err := cmd.Output()
	if err != nil {
		return nil, err
	}

	// Parse apt search output (simplified)
	lines := strings.Split(string(output), "\n")
	var packages []Package
	for _, line := range lines {
		if strings.TrimSpace(line) == "" {
			continue
		}
		// Simplified parsing
		parts := strings.Fields(line)
		if len(parts) >= 2 {
			packages = append(packages, Package{
				Name: parts[0],
			})
		}
	}

	return packages, nil
}

// IsInstalled checks if a package is installed
func (a *APTManager) IsInstalled(packageName string) bool {
	cmd := exec.Command("dpkg", "-s", packageName)
	err := cmd.Run()
	return err == nil
}

// PacmanManager implements PackageManager for Pacman (Arch Linux)
type PacmanManager struct{}

// NewPacman creates a new Pacman package manager
func NewPacman() *PacmanManager {
	return &PacmanManager{}
}

// Update updates package lists
func (p *PacmanManager) Update() error {
	cmd := exec.Command("pacman", "-Sy")
	return cmd.Run()
}

// Install installs packages
func (p *PacmanManager) Install(packages ...string) error {
	if len(packages) == 0 {
		return nil
	}
	args := append([]string{"-S", "--noconfirm"}, packages...)
	cmd := exec.Command("pacman", args...)
	return cmd.Run()
}

// Remove removes packages
func (p *PacmanManager) Remove(packages ...string) error {
	if len(packages) == 0 {
		return nil
	}
	args := append([]string{"-R", "--noconfirm"}, packages...)
	cmd := exec.Command("pacman", args...)
	return cmd.Run()
}

// Search searches for packages
func (p *PacmanManager) Search(query string) ([]Package, error) {
	cmd := exec.Command("pacman", "-Ss", query)
	output, err := cmd.Output()
	if err != nil {
		return nil, err
	}

	// Parse output
	lines := strings.Split(string(output), "\n")
	var packages []Package
	for _, line := range lines {
		if strings.TrimSpace(line) == "" {
			continue
		}
		parts := strings.Fields(line)
		if len(parts) >= 1 {
			packages = append(packages, Package{
				Name: parts[0],
			})
		}
	}

	return packages, nil
}

// IsInstalled checks if a package is installed
func (p *PacmanManager) IsInstalled(packageName string) bool {
	cmd := exec.Command("pacman", "-Q", packageName)
	err := cmd.Run()
	return err == nil
}

// APKManager implements PackageManager for APK (Alpine Linux)
type APKManager struct{}

// NewAPK creates a new APK package manager
func NewAPK() *APKManager {
	return &APKManager{}
}

// Update updates package lists
func (a *APKManager) Update() error {
	cmd := exec.Command("apk", "update")
	return cmd.Run()
}

// Install installs packages
func (a *APKManager) Install(packages ...string) error {
	if len(packages) == 0 {
		return nil
	}
	args := append([]string{"add"}, packages...)
	cmd := exec.Command("apk", args...)
	return cmd.Run()
}

// Remove removes packages
func (a *APKManager) Remove(packages ...string) error {
	if len(packages) == 0 {
		return nil
	}
	args := append([]string{"del"}, packages...)
	cmd := exec.Command("apk", args...)
	return cmd.Run()
}

// Search searches for packages
func (a *APKManager) Search(query string) ([]Package, error) {
	cmd := exec.Command("apk", "search", query)
	output, err := cmd.Output()
	if err != nil {
		return nil, err
	}

	lines := strings.Split(string(output), "\n")
	var packages []Package
	for _, line := range lines {
		if strings.TrimSpace(line) == "" {
			continue
		}
		packages = append(packages, Package{
			Name: line,
		})
	}

	return packages, nil
}

// IsInstalled checks if a package is installed
func (a *APKManager) IsInstalled(packageName string) bool {
	cmd := exec.Command("apk", "info", "-e", packageName)
	err := cmd.Run()
	return err == nil
}

// DetectPackageManager detects the package manager
func DetectPackageManager() (PackageManager, error) {
	// Check for APT
	if _, err := exec.LookPath("apt"); err == nil {
		return NewAPT(), nil
	}

	// Check for Pacman
	if _, err := exec.LookPath("pacman"); err == nil {
		return NewPacman(), nil
	}

	// Check for APK
	if _, err := exec.LookPath("apk"); err == nil {
		return NewAPK(), nil
	}

	return nil, fmt.Errorf("no supported package manager found")
}
