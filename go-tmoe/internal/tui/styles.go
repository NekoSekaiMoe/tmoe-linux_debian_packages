package tui

import (
	"github.com/charmbracelet/lipgloss"
)

var (
	// Base colors matching TMOE theme
	primaryColor   = lipgloss.Color("#00D7FF") // Cyan
	secondaryColor = lipgloss.Color("#5FD7FF") // Light cyan
	accentColor    = lipgloss.Color("#00FF87") // Green
	errorColor     = lipgloss.Color("#FF5F5F") // Red
	warningColor   = lipgloss.Color("#FFD700") // Yellow
	mutedColor     = lipgloss.Color("#808080") // Gray

	// Title styles
	TitleStyle = lipgloss.NewStyle().
			Foreground(primaryColor).
			Bold(true).
			Padding(1, 2)

	// Menu styles
	MenuStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(primaryColor).
			Padding(1, 2).
			Width(60)

	// Selected item style
	SelectedItemStyle = lipgloss.NewStyle().
				Foreground(accentColor).
				Bold(true).
				PaddingLeft(2)

	// Normal item style
	NormalItemStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#FFFFFF")).
			PaddingLeft(2)

	// Description style
	DescStyle = lipgloss.NewStyle().
			Foreground(mutedColor).
			Italic(true).
			PaddingLeft(4)

	// Help style
	HelpStyle = lipgloss.NewStyle().
			Foreground(mutedColor).
			Padding(1, 0)

	// Status styles
	SuccessStyle = lipgloss.NewStyle().
			Foreground(accentColor).
			Bold(true)

	ErrorStyle = lipgloss.NewStyle().
			Foreground(errorColor).
			Bold(true)

	WarningStyle = lipgloss.NewStyle().
			Foreground(warningColor)

	// Info box style
	InfoBoxStyle = lipgloss.NewStyle().
			Border(lipgloss.NormalBorder()).
			BorderForeground(secondaryColor).
			Padding(1, 2).
			Width(60)

	// Container info style
	ContainerNameStyle = lipgloss.NewStyle().
				Foreground(primaryColor).
				Bold(true)

	ContainerTypeStyle = lipgloss.NewStyle().
				Foreground(secondaryColor)

	ContainerStatusRunning = lipgloss.NewStyle().
				Foreground(accentColor).
				Bold(true)

	ContainerStatusStopped = lipgloss.NewStyle().
				Foreground(mutedColor)
)

// RenderTitle renders a styled title
func RenderTitle(text string) string {
	return TitleStyle.Render(text)
}

// RenderMenu renders a menu box
func RenderMenu(content string) string {
	return MenuStyle.Render(content)
}

// RenderHelp renders help text
func RenderHelp(text string) string {
	return HelpStyle.Render(text)
}

// RenderSuccess renders success message
func RenderSuccess(text string) string {
	return SuccessStyle.Render("✓ " + text)
}

// RenderError renders error message
func RenderError(text string) string {
	return ErrorStyle.Render("✗ " + text)
}

// RenderWarning renders warning message
func RenderWarning(text string) string {
	return WarningStyle.Render("⚠ " + text)
}
