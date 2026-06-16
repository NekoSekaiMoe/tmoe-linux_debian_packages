package config

import (
	"os"
	"path/filepath"
	"runtime"
	"sync"
)

var (
	instance *Config
	once     sync.Once
)

// Config holds the application configuration
type Config struct {
	// Paths
	ConfigDir    string
	ContainerDir string
	DataDir      string

	// Locale
	Language string

	// System info
	Arch   string
	OS     string
	IsRoot bool
}

// Get returns the global configuration instance
func Get() *Config {
	once.Do(func() {
		instance = load()
	})
	return instance
}

// load initializes the configuration
func load() *Config {
	cfg := &Config{
		Arch:   runtime.GOARCH,
		OS:     runtime.GOOS,
		IsRoot: os.Geteuid() == 0,
	}

	// Determine base directories based on OS
	var baseDir string
	if runtime.GOOS == "android" {
		// Android/Termux
		baseDir = filepath.Join(os.Getenv("HOME"), ".local/share")
	} else {
		// Standard Linux
		if cfg.IsRoot {
			baseDir = "/usr/local/etc"
		} else {
			baseDir = filepath.Join(os.Getenv("HOME"), ".local/share")
		}
	}

	// Set paths
	tmoeDir := filepath.Join(baseDir, "tmoe-linux")
	cfg.DataDir = tmoeDir
	cfg.ContainerDir = filepath.Join(tmoeDir, "containers")
	cfg.ConfigDir = filepath.Join(os.Getenv("HOME"), ".config", "tmoe-linux")

	// Create directories if they don't exist
	for _, dir := range []string{cfg.DataDir, cfg.ContainerDir, cfg.ConfigDir} {
		os.MkdirAll(dir, 0755)
	}

	// Load language from config file or environment
	cfg.Language = detectLanguage()

	return cfg
}

// detectLanguage detects the user's preferred language
func detectLanguage() string {
	// Check locale file
	localeFile := filepath.Join(os.Getenv("HOME"), ".config", "tmoe-linux", "locale.txt")
	if data, err := os.ReadFile(localeFile); err == nil {
		return string(data)
	}

	// Fallback to LANG environment variable
	lang := os.Getenv("LANG")
	if lang == "" {
		lang = "en_US.UTF-8"
	}

	return lang
}

// Save saves the configuration to disk
func (c *Config) Save() error {
	// Save locale
	localeFile := filepath.Join(c.ConfigDir, "locale.txt")
	return os.WriteFile(localeFile, []byte(c.Language), 0644)
}
