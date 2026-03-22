"""Tests for internationalization."""

import pytest

from tmoe.core.i18n import I18n, get_i18n, _


class TestI18n:
    """Test internationalization."""
    
    def test_i18n_creation(self):
        """Test I18n can be created."""
        i18n = I18n("en")
        assert i18n.language == "en"
    
    def test_i18n_translation(self):
        """Test translation."""
        i18n = I18n("zh_CN")
        
        # Test existing key
        assert i18n.t("ok") == "确定"
        assert i18n.t("cancel") == "取消"
        
        # Test missing key (returns key)
        assert i18n.t("nonexistent") == "nonexistent"
    
    def test_i18n_default_value(self):
        """Test default value for missing keys."""
        i18n = I18n("en")
        
        # With default
        assert i18n.t("nonexistent", default="Default") == "Default"
        
        # Without default
        assert i18n.t("nonexistent") == "nonexistent"
    
    def test_i18n_language_switch(self):
        """Test language switching."""
        i18n = I18n("en")
        
        # Switch to Chinese
        i18n.set_language("zh_CN")
        assert i18n.language == "zh_CN"
        assert i18n.t("ok") == "确定"
        
        # Switch to Japanese
        i18n.set_language("ja")
        assert i18n.language == "ja"
        assert i18n.t("ok") == "OK"
    
    def test_get_available_languages(self):
        """Test getting available languages."""
        i18n = I18n()
        languages = i18n.get_available_languages()
        
        assert isinstance(languages, dict)
        assert "en" in languages
        assert "zh_CN" in languages
        assert "zh_TW" in languages
        assert "ja" in languages
    
    def test_underscore_function(self):
        """Test underscore shorthand."""
        # Note: This will use the singleton which might be in English
        result = _("ok")
        assert isinstance(result, str)
