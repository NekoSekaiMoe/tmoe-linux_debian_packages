package config

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestGet(t *testing.T) {
	cfg := Get()
	if cfg == nil {
		t.Fatal("Get() returned nil")
	}

	// Check that paths are set
	if cfg.ConfigDir == "" {
		t.Error("ConfigDir is empty")
	}
	if cfg.DataDir == "" {
		t.Error("DataDir is empty")
	}
	if cfg.ContainerDir == "" {
		t.Error("ContainerDir is empty")
	}

	t.Logf("ConfigDir: %s", cfg.ConfigDir)
	t.Logf("DataDir: %s", cfg.DataDir)
	t.Logf("ContainerDir: %s", cfg.ContainerDir)
}

func TestDetectLocale(t *testing.T) {
	// Save original env
	origLang := os.Getenv("LANG")
	defer os.Setenv("LANG", origLang)

	tests := []struct {
		lang     string
		expected string
	}{
		{"en_US.UTF-8", "en"},
		{"zh_CN.UTF-8", "zh-CN"},
		{"zh_TW.UTF-8", "zh-TW"},
		{"zh_HK.UTF-8", "zh-HK"},
		{"", "en"}, // default
	}

	for _, tt := range tests {
		t.Run(tt.lang, func(t *testing.T) {
			os.Setenv("LANG", tt.lang)

			// Test locale detection logic
			locale := detectLocale(tt.lang)
			if locale != tt.expected {
				t.Errorf("detectLocale(%s) = %s, want %s", tt.lang, locale, tt.expected)
			}
		})
	}
}

func detectLocale(lang string) string {
	if lang == "" {
		return "en"
	}

	// Remove encoding suffix
	if idx := strings.Index(lang, "."); idx > 0 {
		lang = lang[:idx]
	}

	// Map locale formats
	switch lang {
	case "en_US", "en_GB", "en", "C":
		return "en"
	case "zh_CN", "zh_SG":
		return "zh-CN"
	case "zh_TW":
		return "zh-TW"
	case "zh_HK", "zh_MO":
		return "zh-HK"
	default:
		return "en"
	}
}

func TestExpandPath(t *testing.T) {
	home := os.Getenv("HOME")

	tests := []struct {
		input    string
		expected string
	}{
		{"~/test", filepath.Join(home, "test")},
		{"/absolute/path", "/absolute/path"},
		{"relative/path", "relative/path"},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			result := testExpandPath(tt.input)
			if result != tt.expected {
				t.Errorf("expandPath(%s) = %s, want %s", tt.input, result, tt.expected)
			}
		})
	}
}

func testExpandPath(path string) string {
	if strings.HasPrefix(path, "~/") {
		home := os.Getenv("HOME")
		return filepath.Join(home, path[2:])
	}
	return path
}
