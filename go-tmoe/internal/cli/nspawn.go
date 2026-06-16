package cli

import (
	"github.com/2moe/tmoe/internal/container"
	"github.com/spf13/cobra"
)

var nspawnCmd = &cobra.Command{
	Use:     "nspawn [container-name]",
	Aliases: []string{"systemd", "sd"},
	Short:   "Start a container using systemd-nspawn",
	Long: `Start a Linux container using systemd-nspawn.
Provides full systemd support with proper isolation and resource management.`,
	Args: cobra.MaximumNArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		var containerName string
		if len(args) > 0 {
			containerName = args[0]
		}

		mgr := container.NewNspawnManager()
		return mgr.Start(containerName)
	},
}

func init() {
	nspawnCmd.Flags().StringP("distro", "d", "", "Specify distribution")
	nspawnCmd.Flags().StringP("arch", "a", "", "Specify architecture")
	nspawnCmd.Flags().BoolP("boot", "b", false, "Boot the container (start systemd)")
	nspawnCmd.Flags().StringSliceP("bind", "B", nil, "Bind mount directories")
}
