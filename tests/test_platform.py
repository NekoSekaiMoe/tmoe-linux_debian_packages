"""Tests for platform detection."""

import pytest

from tmoe.core.platform import PlatformInfo


class TestPlatformInfo:
    """Test platform detection."""
    
    def test_platform_info_creation(self):
        """Test PlatformInfo can be created."""
        info = PlatformInfo()
        assert info.machine is not None
        assert info.normalized_arch is not None
    
    def test_normalized_arch(self):
        """Test architecture normalization."""
        info = PlatformInfo()
        arch = info.normalized_arch
        
        # Should be one of supported architectures
        assert arch in [
            "arm64", "amd64", "armhf", "armel",
            "i386", "mips64el", "mipsel", "ppc64el",
            "s390x", "riscv64",
        ]
    
    def test_is_android_detection(self):
        """Test Android detection."""
        info = PlatformInfo()
        # This will depend on the test environment
        assert isinstance(info.is_android, bool)
    
    def test_is_wsl_detection(self):
        """Test WSL detection."""
        info = PlatformInfo()
        assert isinstance(info.is_wsl, bool)
    
    def test_is_linux(self):
        """Test Linux detection."""
        info = PlatformInfo()
        # On Linux test environment, should be True
        assert isinstance(info.is_linux, bool)
    
    def test_config_dir(self):
        """Test config directory path."""
        info = PlatformInfo()
        config_dir = info.config_dir
        
        assert config_dir is not None
        assert config_dir.name == "tmoe-linux"
    
    def test_container_dir(self):
        """Test container directory path."""
        info = PlatformInfo()
        container_dir = info.container_dir
        
        assert container_dir is not None
        assert "containers" in str(container_dir)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        info = PlatformInfo()
        data = info.to_dict()
        
        assert isinstance(data, dict)
        assert "machine" in data
        assert "normalized_arch" in data
        assert "is_android" in data
        assert "is_wsl" in data
