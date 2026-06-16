package container

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"

	"github.com/2moe/tmoe/internal/config"
)

// ChrootManager manages chroot containers
type ChrootManager struct {
	cfg *config.Config
}

// NewChrootManager creates a new chroot manager
func NewChrootManager() *ChrootManager {
	return &ChrootManager{
		cfg: config.Get(),
	}
}

// Start starts a chroot container
func (m *ChrootManager) Start(name string) error {
	// Check if running as root
	if os.Geteuid() != 0 {
		return fmt.Errorf("chroot requires root privileges, try using 'sudo' or 'proot' instead")
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

	// Mount essential filesystems
	if err := m.mountEssential(containerPath); err != nil {
		return fmt.Errorf("failed to mount filesystems: %w", err)
	}

	fmt.Printf("Starting chroot container: %s\n", name)

	// Chroot and execute shell
	if err := syscall.Chroot(containerPath); err != nil {
		return fmt.Errorf("chroot failed: %w", err)
	}

	if err := os.Chdir("/"); err != nil {
		return fmt.Errorf("chdir failed: %w", err)
	}

	// Execute shell
	shell := "/bin/bash"
	cmd := exec.Command(shell, "--login")
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Env = []string{
		"HOME=/root",
		"TERM=" + os.Getenv("TERM"),
		"LANG=en_US.UTF-8",
		"PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
	}

	return cmd.Run()
}

// mountEssential mounts /dev, /proc, /sys
func (m *ChrootManager) mountEssential(containerPath string) error {
	mounts := map[string]string{
		"dev":  "/dev",
		"proc": "/proc",
		"sys":  "/sys",
	}

	for target, source := range mounts {
		targetPath := filepath.Join(containerPath, target)
		if err := os.MkdirAll(targetPath, 0755); err != nil {
			return err
		}

		// Check if already mounted
		// TODO: Implement proper mount check
		if err := syscall.Mount(source, targetPath, "", syscall.MS_BIND, ""); err != nil {
			// Ignore if already mounted
			if err != syscall.EBUSY {
				return fmt.Errorf("mount %s failed: %w", target, err)
			}
		}
	}

	return nil
}

// Stop stops a chroot container
func (m *ChrootManager) Stop(name string) error {
	// Unmount filesystems
	containerPath := filepath.Join(m.cfg.ContainerDir, name)
	return m.umountEssential(containerPath)
}

// umountEssential unmounts /dev, /proc, /sys
func (m *ChrootManager) umountEssential(containerPath string) error {
	targets := []string{"dev", "proc", "sys"}

	for _, target := range targets {
		targetPath := filepath.Join(containerPath, target)
		if err := syscall.Unmount(targetPath, 0); err != nil {
			// Ignore if not mounted
			if err != syscall.EINVAL {
				return fmt.Errorf("unmount %s failed: %w", target, err)
			}
		}
	}

	return nil
}

// Install installs a new chroot container
func (m *ChrootManager) Install(distro, arch string) error {
	return fmt.Errorf("installation not implemented yet")
}

// Remove removes a chroot container
func (m *ChrootManager) Remove(name string) error {
	// First try to unmount
	if err := m.Stop(name); err != nil {
		fmt.Fprintf(os.Stderr, "Warning: failed to unmount: %v\n", err)
	}

	containerPath := filepath.Join(m.cfg.ContainerDir, name)
	return os.RemoveAll(containerPath)
}

// List returns all chroot containers
func (m *ChrootManager) List() ([]Container, error) {
	return List()
}
