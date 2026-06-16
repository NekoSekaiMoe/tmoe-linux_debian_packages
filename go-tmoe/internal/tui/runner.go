package tui

import (
	tea "github.com/charmbracelet/bubbletea"
)

// RunMainMenu runs the main menu TUI
func RunMainMenu() (string, error) {
	model := InitMainMenu()
	p := tea.NewProgram(model)

	finalModel, err := p.Run()
	if err != nil {
		return "", err
	}

	m, ok := finalModel.(MainMenuModel)
	if !ok {
		return "", nil
	}

	return m.GetChoice(), nil
}

// RunContainerMenu runs the container selection menu
func RunContainerMenu() (string, error) {
	model, err := InitContainerMenu()
	if err != nil {
		return "", err
	}

	// If there's an error (like no containers), show it
	if model.err != nil {
		// Could show a message or return to main menu
		return "", model.err
	}

	p := tea.NewProgram(model)
	finalModel, err := p.Run()
	if err != nil {
		return "", err
	}

	m, ok := finalModel.(*ContainerMenuModel)
	if !ok {
		return "", nil
	}

	selected := m.GetSelected()
	if selected == nil {
		return "", nil // User cancelled
	}

	return selected.Name, nil
}
