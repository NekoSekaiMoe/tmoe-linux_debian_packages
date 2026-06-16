package cli

import (
	"github.com/2moe/tmoe/internal/container"
	"github.com/2moe/tmoe/internal/tui"
	"github.com/spf13/cobra"
)

var prootCmd = &cobra.Command{
	Use:   "proot [container-name]",
	Short: "Start a container using proot",
	Long: `Start a Linux container using proot (rootless mode).
Proot provides user-space implementation of chroot without requiring root privileges.`,
	Args: cobra.MaximumNArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		var containerName string
		interactive, _ := cmd.Flags().GetBool("interactive")

		// If no container name provided and interactive mode, show TUI
		if len(args) == 0 && interactive {
			// Show container selection menu
			selected, err := selectContainerInteractive()
			if err != nil {
				return err
			}
			if selected == "" {
				return nil // User cancelled
			}
			containerName = selected
		} else if len(args) > 0 {
			containerName = args[0]
		}

		mgr := container.NewProotManager()
		return mgr.Start(containerName)
	},
}

func init() {
	// Add flags for proot command
	prootCmd.Flags().StringP("distro", "d", "", "Specify distribution (debian, ubuntu, kali, arch, alpine)")
	prootCmd.Flags().StringP("arch", "a", "", "Specify architecture (amd64, arm64, armhf, i386)")
	prootCmd.Flags().BoolP("install", "i", false, "Install a new container")
	prootCmd.Flags().BoolP("interactive", "I", false, "Show interactive container selection menu")
}

// selectContainerInteractive shows an interactive menu to select a container
func selectContainerInteractive() (string, error) {
	return tui.RunContainerMenu()
}
