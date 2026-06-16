package cli

import (
	"fmt"

	"github.com/2moe/tmoe/internal/tui"
	"github.com/spf13/cobra"
)

var menuCmd = &cobra.Command{
	Use:   "menu",
	Short: "Show interactive TUI menu",
	Long:  `Launch the interactive text user interface (TUI) menu for TMOE.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		fallback, _ := cmd.Flags().GetBool("fallback")

		// Try whiptail fallback if requested or if bubbletea fails
		if fallback || !isTerminalSupported() {
			if !tui.IsWhiptailAvailable() {
				return fmt.Errorf("neither TUI nor whiptail/dialog is available")
			}
			return runWhiptailMenu()
		}

		// Run bubbletea TUI
		choice, err := tui.RunMainMenu()
		if err != nil {
			return err
		}

		if choice != "" && choice != "exit" {
			fmt.Printf("\nSelected: %s\n", choice)
			fmt.Println("(Feature implementation in progress...)")
		}

		return nil
	},
}

func init() {
	menuCmd.Flags().BoolP("fallback", "f", false, "Use whiptail/dialog instead of modern TUI")
}

// isTerminalSupported checks if the terminal supports bubbletea
func isTerminalSupported() bool {
	// TODO: Add proper terminal detection
	return true
}

// runWhiptailMenu runs the menu using whiptail fallback
func runWhiptailMenu() error {
	w, err := tui.NewWhiptailFallback()
	if err != nil {
		return err
	}

	items := []string{
		"container", "Container Management",
		"install", "Install Container",
		"vnc", "VNC Services",
		"mirror", "Mirror Sources",
		"config", "Configuration",
		"about", "About / Help",
		"exit", "Exit",
	}

	choice, err := w.ShowMenu("TMOE", "Select an option:", items)
	if err != nil {
		return err
	}

	if choice != "" && choice != "exit" {
		fmt.Printf("\nSelected: %s\n", choice)
		fmt.Println("(Feature implementation in progress...)")
	}

	return nil
}
