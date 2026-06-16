package cli

import (
	"fmt"

	"github.com/2moe/tmoe/internal/vnc"
	"github.com/spf13/cobra"
)

var vncCmd = &cobra.Command{
	Use:   "vnc",
	Short: "Manage VNC and noVNC services",
	Long:  `Start, stop, or check status of VNC and noVNC (web-based VNC) services.`,
}

var vncStartCmd = &cobra.Command{
	Use:   "start",
	Short: "Start VNC server",
	RunE: func(cmd *cobra.Command, args []string) error {
		noVNC, _ := cmd.Flags().GetBool("novnc")
		port, _ := cmd.Flags().GetInt("port")

		mgr := vnc.NewManager()
		if noVNC {
			return mgr.StartNoVNC(port)
		}
		return mgr.StartVNC(port)
	},
}

var vncStopCmd = &cobra.Command{
	Use:   "stop",
	Short: "Stop VNC server",
	RunE: func(cmd *cobra.Command, args []string) error {
		mgr := vnc.NewManager()
		return mgr.Stop()
	},
}

var vncStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Check VNC server status",
	RunE: func(cmd *cobra.Command, args []string) error {
		mgr := vnc.NewManager()
		status, err := mgr.Status()
		if err != nil {
			return err
		}
		fmt.Println(status)
		return nil
	},
}

func init() {
	vncStartCmd.Flags().BoolP("novnc", "n", false, "Start noVNC (web-based VNC)")
	vncStartCmd.Flags().IntP("port", "p", 5900, "VNC port number")

	vncCmd.AddCommand(vncStartCmd)
	vncCmd.AddCommand(vncStopCmd)
	vncCmd.AddCommand(vncStatusCmd)
}
