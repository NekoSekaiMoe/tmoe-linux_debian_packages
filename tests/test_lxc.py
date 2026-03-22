"""Tests for LXC image client."""

import pytest
from pathlib import Path

from tmoe.container.lxc import LXCImageClient, LXCImageManager, LXCImageInfo


class TestLXCImageClient:
    """Test LXC image client."""
    
    def test_client_creation(self):
        """Test client can be created."""
        client = LXCImageClient()
        assert client is not None
        assert client.mirror == LXCImageClient.DEFAULT_MIRROR
    
    def test_arch_mapping(self):
        """Test architecture mappings."""
        client = LXCImageClient()
        
        assert client._get_lxc_arch("arm64") == "arm64"
        assert client._get_lxc_arch("amd64") == "amd64"
        assert client._get_lxc_arch("armhf") == "armhf"
        assert client._get_lxc_arch("i386") == "i386"
    
    def test_custom_mirror(self):
        """Test custom mirror."""
        custom_mirror = "https://custom.mirror.com/images"
        client = LXCImageClient(mirror=custom_mirror)
        assert client.mirror == custom_mirror


class TestLXCImageInfo:
    """Test LXC image info dataclass."""
    
    def test_image_info_creation(self):
        """Test image info creation."""
        info = LXCImageInfo(
            distro="debian",
            release="stable",
            arch="arm64",
            build_date="20240101_00:00",
        )
        
        assert info.distro == "debian"
        assert info.release == "stable"
        assert info.arch == "arm64"
    
    def test_image_info_defaults(self):
        """Test image info defaults."""
        info = LXCImageInfo(
            distro="ubuntu",
            release="jammy",
            arch="amd64",
        )
        
        assert info.variant == "default"
        assert info.build_date == ""
        assert info.url == ""


class TestLXCImageManager:
    """Test LXC image manager."""
    
    def test_manager_creation(self):
        """Test manager creation."""
        manager = LXCImageManager()
        assert manager is not None
        assert manager.client is not None
    
    def test_list_available_distros(self):
        """Test listing available distributions."""
        manager = LXCImageManager()
        distros = manager.list_available_distros()
        
        assert isinstance(distros, list)
        assert len(distros) > 0
        assert "debian" in distros
        assert "ubuntu" in distros
