package cli

import (
	"fmt"

	"github.com/2moe/tmoe/internal/installer"
	"github.com/2moe/tmoe/internal/mirror"
	"github.com/spf13/cobra"
)

var installCmd = &cobra.Command{
	Use:   "install",
	Short: "Install a new container",
	Long:  `Install a new Linux container with interactive or command-line configuration.`,
}

var installContainerCmd = &cobra.Command{
	Use:   "container",
	Short: "Install a Linux container",
	RunE: func(cmd *cobra.Command, args []string) error {
		// Get flags
		distroName, _ := cmd.Flags().GetString("distro")
		codename, _ := cmd.Flags().GetString("release")
		arch, _ := cmd.Flags().GetString("arch")
		mirrorName, _ := cmd.Flags().GetString("mirror")
		name, _ := cmd.Flags().GetString("name")
		minimal, _ := cmd.Flags().GetBool("minimal")

		// Show supported distributions if none specified
		if distroName == "" {
			fmt.Println("Supported distributions:")
			for _, d := range installer.GetSupportedDistros() {
				fmt.Printf("  - %s %s (%s)\n", d.Name, d.Codename, d.Arch)
			}
			return fmt.Errorf("please specify a distribution with --distro")
		}

		// Detect host architecture if not specified
		if arch == "" {
			detected, err := installer.DetectHostArch()
			if err != nil {
				return err
			}
			arch = detected.ToDebianArch()
			fmt.Printf("Detected architecture: %s\n", arch)
		}

		// Set default codename based on distro
		if codename == "" {
			switch distroName {
			case "debian":
				codename = "bookworm"
			case "ubuntu":
				codename = "jammy"
			case "kali":
				codename = "kali-rolling"
			case "arch":
				codename = "latest"
			case "alpine":
				codename = "latest"
			default:
				return fmt.Errorf("unknown distribution: %s", distroName)
			}
		}

		// Get mirror URL
		var mirrorURL string
		if mirrorName != "" {
			mgr := mirror.NewMirrorManager(mirror.DistroType(distroName))
			mirrors := mgr.ListMirrors()
			for _, m := range mirrors {
				if m.Name == mirrorName {
					mirrorURL = m.URL
					break
				}
			}
			if mirrorURL == "" {
				return fmt.Errorf("mirror '%s' not found", mirrorName)
			}
		}

		// Generate container name
		if name == "" {
			name = fmt.Sprintf("%s-%s", distroName, codename)
		}

		// Create installer config
		config := installer.InstallerConfig{
			Distro: installer.Distro{
				Name:     distroName,
				Codename: codename,
				Arch:     arch,
			},
			Mirror:  mirrorURL,
			Minimal: minimal,
		}

		// Install
		inst := installer.NewContainerInstaller(config)
		fmt.Printf("\nInstalling %s %s (%s)...\n", distroName, codename, arch)
		if mirrorURL != "" {
			fmt.Printf("Mirror: %s\n", mirrorURL)
		}
		fmt.Println()

		if err := inst.Install(); err != nil {
			return fmt.Errorf("installation failed: %w", err)
		}

		fmt.Printf("\n✓ Container '%s' installed successfully!\n", name)
		fmt.Printf("\nTo start the container:\n")
		fmt.Printf("  tmoe proot %s\n", name)

		return nil
	},
}

func init() {
	installContainerCmd.Flags().StringP("distro", "d", "", "Distribution (debian, ubuntu, kali, arch, alpine)")
	installContainerCmd.Flags().StringP("release", "r", "", "Release codename (bookworm, jammy, etc.)")
	installContainerCmd.Flags().StringP("arch", "a", "", "Architecture (auto-detect if not specified)")
	installContainerCmd.Flags().StringP("mirror", "m", "", "Mirror name (from 'tmoe mirror list')")
	installContainerCmd.Flags().StringP("name", "n", "", "Container name (auto-generated if not specified)")
	installContainerCmd.Flags().BoolP("minimal", "", false, "Minimal installation")

	installCmd.AddCommand(installContainerCmd)
}
