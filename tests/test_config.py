"""Tests for configuration management."""

import pytest

from tmoe.core.config import ContainerConfig, TmoeConfig


class TestContainerConfig:
    """Test container configuration."""
    
    def test_container_config_creation(self):
        """Test ContainerConfig can be created."""
        config = ContainerConfig(
            name="test-debian",
            distro="debian",
            arch="arm64",
        )
        
        assert config.name == "test-debian"
        assert config.distro == "debian"
        assert config.arch == "arm64"
    
    def test_container_config_validation(self):
        """Test architecture validation."""
        with pytest.raises(ValueError):
            ContainerConfig(
                name="test",
                distro="debian",
                arch="invalid-arch",
            )
    
    def test_default_values(self):
        """Test default values."""
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="arm64",
        )
        
        assert config.user == "root"
        assert config.uid == 0
        assert config.gid == 0
        assert config.container_type == "proot"


class TestTmoeConfig:
    """Test global configuration."""
    
    def test_tmoe_config_creation(self):
        """Test TmoeConfig can be created."""
        config = TmoeConfig()
        
        assert config.version is not None
        assert config.locale is not None
    
    def test_locale_validation(self):
        """Test locale validation."""
        config = TmoeConfig(locale="zh_CN")
        assert "zh_CN" in config.locale
    
    def test_config_paths(self):
        """Test configuration paths."""
        config = TmoeConfig()
        
        assert config.config_file is not None
        assert config.config_file.suffix == ".json"
