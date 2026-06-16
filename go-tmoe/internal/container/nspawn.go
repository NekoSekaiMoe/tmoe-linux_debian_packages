package container

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/2moe/tmoe/internal/config"
)

// NspawnManager manages systemd-nspawn containers
type NspawnManager struct {
	cfg *config.Config
}

// NewNspawnManager creates a new systemd-nspawn manager
func NewNspawnManager() *NspawnManager {
	return &NspawnManager{
		cfg: config.Get(),
	}
}

// Start starts a systemd-nspawn container
func (m *NspawnManager) Start(name string) error {
	// Check if systemd-nspawn is available
	nspawnPath, err := exec.LookPath("systemd-nspawn")
	if err != nil {
		return fmt.Errorf("systemd-nspawn not found, please install systemd-container package")
	}

	if name == "" {
		containers, err := m.List()
		if err != nil {
			return err
		}
		if len(containers) == 0 {
			return fmt.Errorf("no containers found")
		}
		name = containers[0].Name
	}

	containerPath := filepath.Join(m.cfg.ContainerDir, name)
	if _, err := os.Stat(containerPath); os.IsNotExist(err) {
		return fmt.Errorf("container %s not found", name)
	}

	// Build systemd-nspawn command
	args := []string{
		"--directory=" + containerPath,
		"--bind=/tmp",
	}

	// Add optional bind mounts from config
	// TODO: Read from config file

	fmt.Printf("Starting systemd-nspawn container: %s\n", name)

	// Execute systemd-nspawn
	cmd := exec.Command(nspawnPath, args...)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	return cmd.Run()
}

// Stop stops a systemd-nspawn container
func (m *NspawnManager) Stop(name string) error {
	// Find the machine name
	cmd := exec.Command("machinectl", "list", "--no-pager")
	output, err := cmd.Output()
	if err != nil {
		return fmt.Errorf("failed to list machines: %w", err)
	}

	// Check if container is running
	if !strings.Contains(string(output), name) {
		return fmt.Errorf("container %s is not running", name)
	}

	// Terminate the machine
	stopCmd := exec.Command("machinectl", "terminate", name)
	return stopCmd.Run()
}

// Install installs a new systemd-nspawn container
func (m *NspawnManager) Install(distro, arch string) error {
	return fmt.Errorf("installation not implemented yet")
}

// Remove removes a systemd-nspawn container
func (m *NspawnManager) Remove(name string) error {
	// Stop if running
	_ = m.Stop(name) // Ignore error if not running

	containerPath := filepath.Join(m.cfg.ContainerDir, name)
	return os.RemoveAll(containerPath)
}

// List returns all systemd-nspawn containers
func (m *NspawnManager) List() ([]Container, error) {
	return List()
}
