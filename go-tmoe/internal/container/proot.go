package container

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/2moe/tmoe/internal/config"
)

// ProotManager manages proot containers
type ProotManager struct {
	cfg *config.Config
}

// NewProotManager creates a new proot manager
func NewProotManager() *ProotManager {
	return &ProotManager{
		cfg: config.Get(),
	}
}

// Start starts a proot container
func (m *ProotManager) Start(name string) error {
	if name == "" {
		// Interactive selection
		containers, err := m.List()
		if err != nil {
			return err
		}
		if len(containers) == 0 {
			return fmt.Errorf("no containers found, use --install to create one")
		}
		// TODO: Show interactive menu
		name = containers[0].Name
	}

	containerPath := filepath.Join(m.cfg.ContainerDir, name)
	if _, err := os.Stat(containerPath); os.IsNotExist(err) {
		return fmt.Errorf("container %s not found", name)
	}

	// Check if proot is available
	prootPath, err := exec.LookPath("proot")
	if err != nil {
		return fmt.Errorf("proot not found, please install it first")
	}

	// Build proot command
	args := []string{
		"-r", containerPath,
		"-b", "/dev",
		"-b", "/proc",
		"-b", "/sys",
		"-w", "/root",
		"/usr/bin/env", "-i",
		"HOME=/root",
		"TERM=" + os.Getenv("TERM"),
		"LANG=en_US.UTF-8",
		"/bin/bash", "--login",
	}

	fmt.Printf("Starting proot container: %s\n", name)
	fmt.Printf("Container path: %s\n", containerPath)

	// Execute proot
	cmd := exec.Command(prootPath, args...)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	return cmd.Run()
}

// Stop stops a proot container (proot doesn't need explicit stop)
func (m *ProotManager) Stop(name string) error {
	return fmt.Errorf("proot containers stop automatically when shell exits")
}

// Install installs a new proot container
func (m *ProotManager) Install(distro, arch string) error {
	// TODO: Implement container installation
	return fmt.Errorf("installation not implemented yet")
}

// Remove removes a proot container
func (m *ProotManager) Remove(name string) error {
	containerPath := filepath.Join(m.cfg.ContainerDir, name)
	return os.RemoveAll(containerPath)
}

// List returns all proot containers
func (m *ProotManager) List() ([]Container, error) {
	return List()
}
