package tui

import (
	"fmt"
	"io"

	"github.com/charmbracelet/bubbles/list"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/2moe/tmoe/internal/container"
)

// ContainerItem represents a container in the list
type ContainerItem struct {
	container container.Container
}

func (i ContainerItem) Title() string {
	return fmt.Sprintf("%s (%s)", i.container.Name, i.container.Type)
}

func (i ContainerItem) Description() string {
	return fmt.Sprintf("Distro: %s | Arch: %s | Status: %s",
		i.container.Distro, i.container.Arch, i.container.Status)
}

func (i ContainerItem) FilterValue() string {
	return i.container.Name
}

// ContainerMenuModel represents the container selection menu
type ContainerMenuModel struct {
	list       list.Model
	containers []container.Container
	selected   *container.Container
	quitting   bool
	err        error
}

// InitContainerMenu initializes the container selection menu
func InitContainerMenu() (*ContainerMenuModel, error) {
	containers, err := container.List()
	if err != nil {
		return nil, fmt.Errorf("failed to list containers: %w", err)
	}

	if len(containers) == 0 {
		return &ContainerMenuModel{
			containers: containers,
			err:        fmt.Errorf("no containers found"),
		}, nil
	}

	// Convert to list items
	items := make([]list.Item, len(containers))
	for i, c := range containers {
		items[i] = ContainerItem{container: c}
	}

	const defaultWidth = 80
	const listHeight = 15

	l := list.New(items, containerDelegate{}, defaultWidth, listHeight)
	l.Title = "Select a Container"
	l.SetShowStatusBar(true)
	l.SetFilteringEnabled(true)
	l.Styles.Title = lipgloss.NewStyle().
		Foreground(lipgloss.Color("#00D7FF")).
		Bold(true).
		Padding(0, 0, 1, 2)

	return &ContainerMenuModel{
		list:       l,
		containers: containers,
	}, nil
}

func (m ContainerMenuModel) Init() tea.Cmd {
	return nil
}

func (m ContainerMenuModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.list.SetWidth(msg.Width)
		return m, nil

	case tea.KeyMsg:
		switch msg.String() {
		case "q", "ctrl+c", "esc":
			m.quitting = true
			return m, tea.Quit

		case "enter":
			i, ok := m.list.SelectedItem().(ContainerItem)
			if ok {
				m.selected = &i.container
				m.quitting = true
				return m, tea.Quit
			}
		}
	}

	var cmd tea.Cmd
	m.list, cmd = m.list.Update(msg)
	return m, cmd
}

func (m ContainerMenuModel) View() string {
	if m.err != nil {
		return ErrorStyle.Render(fmt.Sprintf("\n  Error: %v\n\n", m.err))
	}

	if m.quitting {
		if m.selected != nil {
			return fmt.Sprintf("\n  Starting container: %s\n\n", m.selected.Name)
		}
		return "\n  Cancelled.\n\n"
	}

	return "\n" + m.list.View() + "\n\n" +
		HelpStyle.Render("  ↑/↓: navigate • /: filter • enter: select • q/esc: back") + "\n"
}

// GetSelected returns the selected container
func (m ContainerMenuModel) GetSelected() *container.Container {
	return m.selected
}

// Custom delegate for container items
type containerDelegate struct{}

func (d containerDelegate) Height() int                             { return 2 }
func (d containerDelegate) Spacing() int                            { return 1 }
func (d containerDelegate) Update(_ tea.Msg, _ *list.Model) tea.Cmd { return nil }
func (d containerDelegate) Render(w io.Writer, m list.Model, index int, listItem list.Item) {
	i, ok := listItem.(ContainerItem)
	if !ok {
		return
	}

	c := i.container
	var (
		title  string
		status string
	)

	// Format title
	containerName := fmt.Sprintf("%s", c.Name)
	containerType := fmt.Sprintf("(%s)", c.Type)

	// Format status
	statusStyle := ContainerStatusStopped
	if c.Status == "running" {
		statusStyle = ContainerStatusRunning
	}
	status = statusStyle.Render(c.Status)

	if index == m.Index() {
		// Selected style
		title = SelectedItemStyle.Render(fmt.Sprintf("▶ %s %s", containerName, containerType))
		descStyle := DescStyle.Foreground(lipgloss.Color("#00FF87"))
		desc := descStyle.Render(fmt.Sprintf("Distro: %s | Arch: %s | Status: %s",
			c.Distro, c.Arch, status))
		fmt.Fprintf(w, "%s\n%s", title, desc)
	} else {
		// Normal style
		title = NormalItemStyle.Render(fmt.Sprintf("  %s %s", containerName, containerType))
		desc := DescStyle.Render(fmt.Sprintf("Distro: %s | Arch: %s | Status: %s",
			c.Distro, c.Arch, status))
		fmt.Fprintf(w, "%s\n%s", title, desc)
	}
}
