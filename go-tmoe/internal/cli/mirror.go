package cli

import (
	"fmt"
	"time"

	"github.com/2moe/tmoe/internal/mirror"
	"github.com/spf13/cobra"
)

var mirrorCmd = &cobra.Command{
	Use:   "mirror",
	Short: "Manage package mirror sources",
	Long:  `List, test, and switch package mirror sources for faster downloads.`,
}

var mirrorListCmd = &cobra.Command{
	Use:   "list",
	Short: "List available mirrors",
	RunE: func(cmd *cobra.Command, args []string) error {
		distro, _ := cmd.Flags().GetString("distro")
		if distro == "" {
			distro = "debian" // Default
		}

		mgr := mirror.NewMirrorManager(mirror.DistroType(distro))
		mirrors := mgr.ListMirrors()

		fmt.Printf("Available mirrors for %s:\n\n", distro)
		for i, m := range mirrors {
			fmt.Printf("%d. %s (%s)\n", i+1, m.Name, m.Country)
			fmt.Printf("   URL: %s\n", m.URL)
			fmt.Printf("   %s\n", m.Description)
			if m.Speed > 0 {
				fmt.Printf("   Speed: %v\n", m.Speed)
			}
			fmt.Println()
		}

		return nil
	},
}

var mirrorTestCmd = &cobra.Command{
	Use:   "test",
	Short: "Test mirror speeds",
	RunE: func(cmd *cobra.Command, args []string) error {
		distro, _ := cmd.Flags().GetString("distro")
		if distro == "" {
			distro = "debian"
		}

		timeout, _ := cmd.Flags().GetDuration("timeout")

		mgr := mirror.NewMirrorManager(mirror.DistroType(distro))

		fmt.Printf("Testing mirrors for %s (timeout: %v)...\n\n", distro, timeout)

		mgr.TestAllSpeeds(timeout)
		sorted := mgr.GetSortedBySpeed()

		fmt.Println("Results (sorted by speed):")
		for i, m := range sorted {
			if m.Speed == 0 {
				fmt.Printf("%d. %s - Failed or timeout\n", i+1, m.Name)
			} else {
				fmt.Printf("%d. %s - %v\n", i+1, m.Name, m.Speed)
			}
		}

		fastest := mgr.GetFastest()
		if fastest != nil {
			fmt.Printf("\n✓ Fastest: %s (%v)\n", fastest.Name, fastest.Speed)
		}

		return nil
	},
}

var mirrorSetCmd = &cobra.Command{
	Use:   "set [mirror-name]",
	Short: "Set mirror source",
	Long:  `Set the package mirror source. This will generate and apply sources.list.`,
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		mirrorName := args[0]
		distro, _ := cmd.Flags().GetString("distro")
		if distro == "" {
			distro = "debian"
		}

		mgr := mirror.NewMirrorManager(mirror.DistroType(distro))
		mirrors := mgr.ListMirrors()

		// Find mirror by name
		var selected *mirror.Mirror
		for i := range mirrors {
			if mirrors[i].Name == mirrorName {
				selected = &mirrors[i]
				break
			}
		}

		if selected == nil {
			return fmt.Errorf("mirror '%s' not found", mirrorName)
		}

		// Generate sources.list
		release, _ := cmd.Flags().GetString("release")
		if release == "" {
			release = "bookworm" // Default Debian release
		}

		components := []string{"main", "contrib", "non-free", "non-free-firmware"}
		sourcesList := mgr.GenerateSourcesList(*selected, release, components)

		fmt.Printf("Generated sources.list:\n")
		fmt.Println("---")
		fmt.Println(sourcesList)
		fmt.Println("---")
		fmt.Printf("\nTo apply, run:\n")
		fmt.Printf("  sudo tee /etc/apt/sources.list << 'EOF'\n%sEOF\n", sourcesList)
		fmt.Printf("  sudo apt update\n")

		return nil
	},
}

func init() {
	// Add distro flag to all mirror commands
	for _, cmd := range []*cobra.Command{mirrorListCmd, mirrorTestCmd, mirrorSetCmd} {
		cmd.Flags().StringP("distro", "d", "", "Distribution (debian, ubuntu, arch, alpine, kali)")
	}

	mirrorTestCmd.Flags().DurationP("timeout", "t", 5*time.Second, "Timeout for each mirror test")
	mirrorSetCmd.Flags().StringP("release", "r", "", "Release codename (e.g., bookworm, jammy)")

	mirrorCmd.AddCommand(mirrorListCmd)
	mirrorCmd.AddCommand(mirrorTestCmd)
	mirrorCmd.AddCommand(mirrorSetCmd)
}
