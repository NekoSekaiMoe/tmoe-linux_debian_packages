package container

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/2moe/tmoe/internal/config"
)

// ContainerType represents the type of container
type ContainerType string

const (
	TypeProot  ContainerType = "proot"
	TypeChroot ContainerType = "chroot"
	TypeNspawn ContainerType = "nspawn"
	TypeQEMU   ContainerType = "qemu"
)

// Container represents a TMOE container instance
type Container struct {
	Name   string
	Type   ContainerType
	Distro string
	Arch   string
	Path   string
	Status string
}

// Manager is the interface for container operations
type Manager interface {
	Start(name string) error
	Stop(name string) error
	Install(distro, arch string) error
	Remove(name string) error
	List() ([]Container, error)
}

// List returns all installed containers
func List() ([]Container, error) {
	cfg := config.Get()
	containerDir := cfg.ContainerDir

	// Check if container directory exists
	if _, err := os.Stat(containerDir); os.IsNotExist(err) {
		return []Container{}, nil
	}

	// Read container directories
	entries, err := os.ReadDir(containerDir)
	if err != nil {
		return nil, fmt.Errorf("failed to read container directory: %w", err)
	}

	var containers []Container
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}

		// Parse container info from directory name or config
		// TODO: Read container metadata
		containers = append(containers, Container{
			Name:   entry.Name(),
			Type:   TypeProot, // TODO: detect from config
			Distro: "unknown",
			Arch:   "unknown",
			Path:   filepath.Join(containerDir, entry.Name()),
			Status: "stopped",
		})
	}

	return containers, nil
}
