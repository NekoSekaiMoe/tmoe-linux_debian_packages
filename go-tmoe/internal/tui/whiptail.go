package tui

import (
	"fmt"
	"os/exec"
	"strings"
)

// WhiptailFallback provides a fallback to whiptail/dialog for compatibility
type WhiptailFallback struct {
	binary string // "whiptail" or "dialog"
}

// NewWhiptailFallback creates a new whiptail fallback
func NewWhiptailFallback() (*WhiptailFallback, error) {
	// Try to find whiptail or dialog
	for _, bin := range []string{"whiptail", "dialog"} {
		if _, err := exec.LookPath(bin); err == nil {
			return &WhiptailFallback{binary: bin}, nil
		}
	}

	return nil, fmt.Errorf("neither whiptail nor dialog found")
}

// ShowMenu shows a menu using whiptail/dialog
func (w *WhiptailFallback) ShowMenu(title, text string, items []string) (string, error) {
	if len(items)%2 != 0 {
		return "", fmt.Errorf("items must be in pairs (tag, description)")
	}

	args := []string{
		"--title", title,
		"--menu", text,
		"20", "60", // height, width
		fmt.Sprintf("%d", len(items)/2), // menu height
	}
	args = append(args, items...)

	cmd := exec.Command(w.binary, args...)

	// whiptail outputs to stderr
	output, err := cmd.CombinedOutput()
	if err != nil {
		return "", err
	}

	return strings.TrimSpace(string(output)), nil
}

// ShowYesNo shows a yes/no dialog
func (w *WhiptailFallback) ShowYesNo(title, text string) (bool, error) {
	cmd := exec.Command(w.binary,
		"--title", title,
		"--yesno", text,
		"10", "60")

	err := cmd.Run()
	if err != nil {
		// Exit code 1 means "No" was selected
		if exitErr, ok := err.(*exec.ExitError); ok {
			if exitErr.ExitCode() == 1 {
				return false, nil
			}
		}
		return false, err
	}

	return true, nil
}

// ShowInputBox shows an input dialog
func (w *WhiptailFallback) ShowInputBox(title, text, defaultValue string) (string, error) {
	cmd := exec.Command(w.binary,
		"--title", title,
		"--inputbox", text,
		"10", "60",
		defaultValue)

	output, err := cmd.CombinedOutput()
	if err != nil {
		return "", err
	}

	return strings.TrimSpace(string(output)), nil
}

// ShowMessageBox shows a message box
func (w *WhiptailFallback) ShowMessageBox(title, text string) error {
	cmd := exec.Command(w.binary,
		"--title", title,
		"--msgbox", text,
		"10", "60")

	return cmd.Run()
}

// IsAvailable checks if whiptail/dialog is available
func IsWhiptailAvailable() bool {
	for _, bin := range []string{"whiptail", "dialog"} {
		if _, err := exec.LookPath(bin); err == nil {
			return true
		}
	}
	return false
}
