package cli

import (
	"fmt"

	"github.com/spf13/cobra"
)

var (
	version   string
	commit    string
	buildTime string
)

// SetVersion sets version information
func SetVersion(v, c, bt string) {
	version = v
	commit = c
	buildTime = bt
}

var rootCmd = &cobra.Command{
	Use:   "tmoe",
	Short: "TMOE - More Optional Environments",
	Long: `TMOE is a container management tool for Linux environments.
It supports proot, chroot, systemd-nspawn, and QEMU containers.

Complete documentation is available at https://doc.tmoe.me`,
	Version: version,
}

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Print version information",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Printf("TMOE %s\n", version)
		fmt.Printf("Commit: %s\n", commit)
		fmt.Printf("Built: %s\n", buildTime)
	},
}

func init() {
	rootCmd.AddCommand(versionCmd)
	rootCmd.AddCommand(menuCmd)
	rootCmd.AddCommand(prootCmd)
	rootCmd.AddCommand(chrootCmd)
	rootCmd.AddCommand(nspawnCmd)
	rootCmd.AddCommand(vncCmd)
	rootCmd.AddCommand(listCmd)
	rootCmd.AddCommand(mirrorCmd)
	rootCmd.AddCommand(installCmd)
}

// Execute runs the root command
func Execute() error {
	return rootCmd.Execute()
}
