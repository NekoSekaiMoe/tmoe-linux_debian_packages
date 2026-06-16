package tui

import (
	"fmt"
	"io"

	"github.com/charmbracelet/bubbles/list"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// MenuItem represents a menu item
type MenuItem struct {
	title       string
	description string
	action      string
}

func (i MenuItem) Title() string       { return i.title }
func (i MenuItem) Description() string { return i.description }
func (i MenuItem) FilterValue() string { return i.title }

// NewMenuItem creates a new menu item
func NewMenuItem(title, description, action string) MenuItem {
	return MenuItem{
		title:       title,
		description: description,
		action:      action,
	}
}

// MainMenuModel represents the main menu state
type MainMenuModel struct {
	list     list.Model
	choice   string
	quitting bool
}

// InitMainMenu initializes the main menu
func InitMainMenu() MainMenuModel {
	items := []list.Item{
		NewMenuItem(
			"🐳 Container Management",
			"Start, stop, and manage containers (proot/chroot/nspawn)",
			"container",
		),
		NewMenuItem(
			"📦 Install Container",
			"Install a new Linux container (Debian, Ubuntu, Arch, etc.)",
			"install",
		),
		NewMenuItem(
			"🖥️  VNC Services",
			"Start/stop VNC or noVNC (web-based) services",
			"vnc",
		),
		NewMenuItem(
			"🌐 Mirror Sources",
			"Change package mirror sources for faster downloads",
			"mirror",
		),
		NewMenuItem(
			"⚙️  Configuration",
			"Configure TMOE settings and preferences",
			"config",
		),
		NewMenuItem(
			"ℹ️  About / Help",
			"View version info and help documentation",
			"about",
		),
		NewMenuItem(
			"🚪 Exit",
			"Exit TMOE",
			"exit",
		),
	}

	const defaultWidth = 70
	const listHeight = 18

	l := list.New(items, itemDelegate{}, defaultWidth, listHeight)
	l.Title = "TMOE - More Optional Environments"
	l.SetShowStatusBar(false)
	l.SetFilteringEnabled(false)
	l.Styles.Title = lipgloss.NewStyle().
		Foreground(lipgloss.Color("#00D7FF")).
		Bold(true).
		Padding(0, 0, 1, 2)

	return MainMenuModel{
		list: l,
	}
}

func (m MainMenuModel) Init() tea.Cmd {
	return nil
}

func (m MainMenuModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.list.SetWidth(msg.Width)
		return m, nil

	case tea.KeyMsg:
		switch keypress := msg.String(); keypress {
		case "q", "ctrl+c":
			m.quitting = true
			return m, tea.Quit

		case "enter":
			i, ok := m.list.SelectedItem().(MenuItem)
			if ok {
				m.choice = i.action
				if i.action == "exit" {
					m.quitting = true
					return m, tea.Quit
				}
				// For now, just show the choice
				// TODO: Navigate to sub-menus
			}
		}
	}

	var cmd tea.Cmd
	m.list, cmd = m.list.Update(msg)
	return m, cmd
}

func (m MainMenuModel) View() string {
	if m.quitting {
		return "\n  👋 Goodbye!\n\n"
	}

	if m.choice != "" && m.choice != "exit" {
		return fmt.Sprintf("\n  Selected: %s\n  (Implementation in progress...)\n\n  Press q to quit.\n\n", m.choice)
	}

	return "\n" + m.list.View() + "\n\n" +
		HelpStyle.Render("  ↑/↓: navigate • enter: select • q: quit") + "\n"
}

// GetChoice returns the selected choice
func (m MainMenuModel) GetChoice() string {
	return m.choice
}

// Custom item delegate for styling
type itemDelegate struct{}

func (d itemDelegate) Height() int                             { return 2 }
func (d itemDelegate) Spacing() int                            { return 1 }
func (d itemDelegate) Update(_ tea.Msg, _ *list.Model) tea.Cmd { return nil }
func (d itemDelegate) Render(w io.Writer, m list.Model, index int, listItem list.Item) {
	i, ok := listItem.(MenuItem)
	if !ok {
		return
	}

	// Style based on selection
	var (
		title string
		desc  string
	)

	if index == m.Index() {
		title = SelectedItemStyle.Render("▶ " + i.Title())
		descStyle := DescStyle.Foreground(lipgloss.Color("#00FF87"))
		desc = descStyle.Render(i.Description())
	} else {
		title = NormalItemStyle.Render("  " + i.Title())
		desc = DescStyle.Render(i.Description())
	}

	fmt.Fprintf(w, "%s\n%s", title, desc)
}
