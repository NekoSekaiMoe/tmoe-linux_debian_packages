package vnc

import (
	"fmt"
	"os"
	"os/exec"
	"strconv"
	"strings"
)

// Manager manages VNC and noVNC services
type Manager struct {
	vncPort    int
	novncPort  int
	vncProcess *os.Process
}

// NewManager creates a new VNC manager
func NewManager() *Manager {
	return &Manager{
		vncPort:   5900,
		novncPort: 6080,
	}
}

// StartVNC starts the VNC server
func (m *Manager) StartVNC(port int) error {
	if port > 0 {
		m.vncPort = port
	}

	// Check if VNC server is already running
	if running, _ := m.isVNCRunning(); running {
		return fmt.Errorf("VNC server is already running on port %d", m.vncPort)
	}

	// Try different VNC servers
	servers := []string{"vncserver", "x11vnc", "tigervncserver"}
	var vncCmd string

	for _, server := range servers {
		if _, err := exec.LookPath(server); err == nil {
			vncCmd = server
			break
		}
	}

	if vncCmd == "" {
		return fmt.Errorf("no VNC server found, please install tigervnc or x11vnc")
	}

	// Start VNC server
	display := m.vncPort - 5900
	var cmd *exec.Cmd

	switch vncCmd {
	case "vncserver", "tigervncserver":
		cmd = exec.Command(vncCmd, fmt.Sprintf(":%d", display))
	case "x11vnc":
		cmd = exec.Command(vncCmd, "-display", fmt.Sprintf(":%d", display), "-forever", "-shared")
	}

	if err := cmd.Start(); err != nil {
		return fmt.Errorf("failed to start VNC server: %w", err)
	}

	m.vncProcess = cmd.Process
	fmt.Printf("VNC server started on port %d (display :%d)\n", m.vncPort, display)

	return nil
}

// StartNoVNC starts the noVNC web service
func (m *Manager) StartNoVNC(port int) error {
	if port > 0 {
		m.novncPort = port
	}

	// First ensure VNC is running
	if running, _ := m.isVNCRunning(); !running {
		if err := m.StartVNC(0); err != nil {
			return err
		}
	}

	// Check if noVNC is available
	novncPath, err := exec.LookPath("novnc")
	if err != nil {
		return fmt.Errorf("noVNC not found, please install novnc package")
	}

	// Start noVNC
	cmd := exec.Command(novncPath,
		"--vnc", fmt.Sprintf("localhost:%d", m.vncPort),
		"--listen", fmt.Sprintf("%d", m.novncPort))

	if err := cmd.Start(); err != nil {
		return fmt.Errorf("failed to start noVNC: %w", err)
	}

	fmt.Printf("noVNC web service started on http://localhost:%d\n", m.novncPort)
	return nil
}

// Stop stops the VNC server
func (m *Manager) Stop() error {
	// Kill VNC server process
	if m.vncProcess != nil {
		if err := m.vncProcess.Kill(); err != nil {
			return fmt.Errorf("failed to stop VNC server: %w", err)
		}
		m.vncProcess = nil
	}

	// Try to kill via vncserver command
	cmd := exec.Command("vncserver", "-kill", ":1")
	_ = cmd.Run() // Ignore error

	fmt.Println("VNC server stopped")
	return nil
}

// Status returns the current VNC server status
func (m *Manager) Status() (string, error) {
	running, port := m.isVNCRunning()
	if !running {
		return "VNC server is not running", nil
	}

	return fmt.Sprintf("VNC server is running on port %d", port), nil
}

// isVNCRunning checks if VNC server is running
func (m *Manager) isVNCRunning() (bool, int) {
	// Check for VNC process
	cmd := exec.Command("ps", "aux")
	output, err := cmd.Output()
	if err != nil {
		return false, 0
	}

	lines := strings.Split(string(output), "\n")
	for _, line := range lines {
		if strings.Contains(line, "vnc") || strings.Contains(line, "Xvnc") {
			// Try to extract port number
			fields := strings.Fields(line)
			for _, field := range fields {
				if strings.Contains(field, ":") {
					parts := strings.Split(field, ":")
					if len(parts) > 1 {
						if display, err := strconv.Atoi(parts[1]); err == nil {
							return true, 5900 + display
						}
					}
				}
			}
			return true, m.vncPort
		}
	}

	return false, 0
}
