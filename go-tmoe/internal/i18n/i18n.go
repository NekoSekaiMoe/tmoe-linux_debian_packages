package i18n

import (
	"embed"
	"encoding/json"
	"fmt"
	"os"

	"github.com/nicksnyder/go-i18n/v2/i18n"
	"golang.org/x/text/language"
)

//go:embed translations/*.json
var translationsFS embed.FS

var (
	bundle    *i18n.Bundle
	localizer *i18n.Localizer
)

// Init initializes the i18n system
func Init() error {
	bundle = i18n.NewBundle(language.English)
	bundle.RegisterUnmarshalFunc("json", json.Unmarshal)

	// Load all translation files
	for _, lang := range []string{"en", "zh-CN", "zh-TW", "zh-HK"} {
		filename := fmt.Sprintf("translations/%s.json", lang)
		data, err := translationsFS.ReadFile(filename)
		if err != nil {
			return fmt.Errorf("failed to read translation file %s: %w", filename, err)
		}

		if _, err := bundle.ParseMessageFileBytes(data, filename); err != nil {
			return fmt.Errorf("failed to parse translation file %s: %w", filename, err)
		}
	}

	// Set default localizer
	lang := DetectLanguage()
	SetLanguage(lang)

	return nil
}

// SetLanguage sets the current language
func SetLanguage(lang string) {
	localizer = i18n.NewLocalizer(bundle, lang)
}

// DetectLanguage detects the system language
func DetectLanguage() string {
	// Try LANG environment variable
	if lang := os.Getenv("LANG"); lang != "" {
		// Parse locale (e.g., "zh_CN.UTF-8" -> "zh-CN")
		tag := parseLocale(lang)
		if tag != "" {
			return tag
		}
	}

	// Try LC_ALL
	if lang := os.Getenv("LC_ALL"); lang != "" {
		tag := parseLocale(lang)
		if tag != "" {
			return tag
		}
	}

	// Default to English
	return "en"
}

// parseLocale converts locale string to language tag
func parseLocale(locale string) string {
	// Remove encoding suffix (e.g., ".UTF-8")
	if idx := len(locale); idx > 0 {
		for i, c := range locale {
			if c == '.' {
				locale = locale[:i]
				break
			}
		}
	}

	// Map common locale formats
	switch locale {
	case "en_US", "en_GB", "en", "C":
		return "en"
	case "zh_CN", "zh_SG":
		return "zh-CN"
	case "zh_TW":
		return "zh-TW"
	case "zh_HK", "zh_MO":
		return "zh-HK"
	default:
		// Try to parse as language tag
		if len(locale) >= 2 {
			return locale[:2]
		}
		return "en"
	}
}

// T translates a message ID
func T(messageID string) string {
	if localizer == nil {
		return messageID
	}

	msg, err := localizer.Localize(&i18n.LocalizeConfig{
		MessageID: messageID,
	})
	if err != nil {
		return messageID
	}

	return msg
}

// Tf translates a message ID with template data
func Tf(messageID string, templateData map[string]interface{}) string {
	if localizer == nil {
		return messageID
	}

	msg, err := localizer.Localize(&i18n.LocalizeConfig{
		MessageID:    messageID,
		TemplateData: templateData,
	})
	if err != nil {
		return messageID
	}

	return msg
}

// GetAvailableLanguages returns list of available languages
func GetAvailableLanguages() []Language {
	return []Language{
		{Code: "en", Name: "English", NativeName: "English"},
		{Code: "zh-CN", Name: "Simplified Chinese", NativeName: "简体中文"},
		{Code: "zh-TW", Name: "Traditional Chinese", NativeName: "繁體中文"},
		{Code: "zh-HK", Name: "Hong Kong Chinese", NativeName: "繁體中文（香港）"},
	}
}

// Language represents a language
type Language struct {
	Code       string
	Name       string
	NativeName string
}
