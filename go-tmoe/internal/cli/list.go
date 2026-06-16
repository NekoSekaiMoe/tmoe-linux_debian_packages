package cli

import (
	"fmt"

	"github.com/2moe/tmoe/internal/container"
	"github.com/spf13/cobra"
)

var listCmd = &cobra.Command{
	Use:     "list",
	Aliases: []string{"ls"},
	Short:   "List all installed containers",
	Long:    `List all installed TMOE containers with their type, distribution, and status.`,
	RunE: func(cmd *cobra.Command, args []string) error {
		containers, err := container.List()
		if err != nil {
			return err
		}

		if len(containers) == 0 {
			fmt.Println("No containers found.")
			return nil
		}

		// Print table header
		fmt.Printf("%-20s %-10s %-15s %-10s\n", "NAME", "TYPE", "DISTRO", "STATUS")
		fmt.Println("------------------------------------------------------------")

		// Print each container
		for _, c := range containers {
			fmt.Printf("%-20s %-10s %-15s %-10s\n",
				c.Name, c.Type, c.Distro, c.Status)
		}

		return nil
	},
}
