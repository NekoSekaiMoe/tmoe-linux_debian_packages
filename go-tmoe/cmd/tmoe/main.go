package main

import (
	"fmt"
	"os"

	"github.com/2moe/tmoe/internal/cli"
	"github.com/2moe/tmoe/internal/i18n"
)

var (
	// Version will be set by build flags
	Version = "2.0.0-dev"
	// Commit will be set by build flags
	Commit = "unknown"
	// BuildTime will be set by build flags
	BuildTime = "unknown"
)

func main() {
	// Initialize i18n
	if err := i18n.Init(); err != nil {
		fmt.Fprintf(os.Stderr, "Warning: Failed to initialize i18n: %v\n", err)
		// Continue anyway with English fallback
	}

	// Set version info
	cli.SetVersion(Version, Commit, BuildTime)

	// Execute root command
	if err := cli.Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
