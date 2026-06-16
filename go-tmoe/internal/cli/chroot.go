package cli

import (
	"github.com/2moe/tmoe/internal/container"
	"github.com/spf13/cobra"
)

var chrootCmd = &cobra.Command{
	Use:   "chroot [container-name]",
	Short: "Start a container using chroot",
	Long: `Start a Linux container using chroot (requires root privileges).
Chroot provides a proper isolated root filesystem environment.`,
	Args: cobra.MaximumNArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		var containerName string
		if len(args) > 0 {
			containerName = args[0]
		}

		mgr := container.NewChrootManager()
		return mgr.Start(containerName)
	},
}

func init() {
	chrootCmd.Flags().StringP("distro", "d", "", "Specify distribution")
	chrootCmd.Flags().StringP("arch", "a", "", "Specify architecture")
	chrootCmd.Flags().BoolP("install", "i", false, "Install a new container")
}
