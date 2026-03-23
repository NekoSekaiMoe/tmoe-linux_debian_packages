"""Tests for desktop environment installation.

These tests verify desktop environment package definitions,
installation commands, and VNC startup script generation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from tmoe.gui.desktop import (
    DesktopEnvironment,
    DesktopPackage,
    DesktopInstaller,
    DesktopManager,
)


@pytest.fixture
def mock_backend():
    """Create a mock container backend."""
    backend = Mock()
    backend.name = "test-container"
    backend.exec = AsyncMock(return_value=(0, "", ""))
    return backend


@pytest.fixture
def desktop_installer(mock_backend):
    """Create a desktop installer with mock backend."""
    return DesktopInstaller(mock_backend)


@pytest.fixture
def desktop_manager():
    """Create a desktop manager."""
    return DesktopManager()


class TestDesktopEnvironmentEnum:
    """Test DesktopEnvironment enum definitions."""
    
    def test_xfce_properties(self):
        """Test XFCE desktop environment properties."""
        xfce = DesktopEnvironment.XFCE
        assert xfce.id == "xfce"
        assert xfce.display_name == "XFCE"
        assert "轻量级" in xfce.description
    
    def test_lxde_properties(self):
        """Test LXDE desktop environment properties."""
        lxde = DesktopEnvironment.LXDE
        assert lxde.id == "lxde"
        assert lxde.display_name == "LXDE"
        assert "超轻量级" in lxde.description
    
    def test_lxqt_properties(self):
        """Test LXQt desktop environment properties."""
        lxqt = DesktopEnvironment.LXQT
        assert lxqt.id == "lxqt"
        assert lxqt.display_name == "LXQt"
    
    def test_mate_properties(self):
        """Test MATE desktop environment properties."""
        mate = DesktopEnvironment.MATE
        assert mate.id == "mate"
        assert mate.display_name == "MATE"
    
    def test_kde_properties(self):
        """Test KDE desktop environment properties."""
        kde = DesktopEnvironment.KDE
        assert kde.id == "kde"
        assert kde.display_name == "KDE Plasma"
    
    def test_gnome_properties(self):
        """Test GNOME desktop environment properties."""
        gnome = DesktopEnvironment.GNOME
        assert gnome.id == "gnome"
        assert gnome.display_name == "GNOME"
    
    def test_cinnamon_properties(self):
        """Test Cinnamon desktop environment properties."""
        cinnamon = DesktopEnvironment.CINNAMON
        assert cinnamon.id == "cinnamon"
        assert cinnamon.display_name == "Cinnamon"
    
    def test_budgie_properties(self):
        """Test Budgie desktop environment properties."""
        budgie = DesktopEnvironment.BUDGIE
        assert budgie.id == "budgie"
        assert budgie.display_name == "Budgie"
    
    def test_deepin_properties(self):
        """Test Deepin desktop environment properties."""
        deepin = DesktopEnvironment.DEEPIN
        assert deepin.id == "deepin"
        assert deepin.display_name == "Deepin"


class TestDesktopManager:
    """Test DesktopManager functionality."""
    
    def test_manager_creation(self, desktop_manager):
        """Test manager creation."""
        assert desktop_manager is not None
        assert desktop_manager.installer is not None
    
    def test_get_desktop_choices(self, desktop_manager):
        """Test getting desktop choices."""
        choices = desktop_manager.get_desktop_choices()
        assert len(choices) > 0
        # Check that XFCE is included
        xfce_choice = next((c for c in choices if c[0] == "xfce"), None)
        assert xfce_choice is not None
        assert xfce_choice[1] == "XFCE"
    
    def test_get_desktop_choices_structure(self, desktop_manager):
        """Test desktop choices return correct structure."""
        choices = desktop_manager.get_desktop_choices()
        for choice in choices:
            assert len(choice) == 3
            assert isinstance(choice[0], str)  # id
            assert isinstance(choice[1], str)  # name
            assert isinstance(choice[2], str)  # description


class TestDesktopInstaller:
    """Test DesktopInstaller functionality."""
    
    def test_installer_creation(self, desktop_installer):
        """Test installer creation."""
        assert desktop_installer is not None
        assert desktop_installer.backend is not None
    
    def test_get_install_command(self, desktop_installer):
        """Test getting install command for different distros."""
        # Test Debian/Ubuntu
        cmd = desktop_installer._get_install_command("debian", ["pkg1", "pkg2"])
        assert cmd == ["apt", "install", "-y", "pkg1", "pkg2"]
        
        # Test Arch
        cmd = desktop_installer._get_install_command("arch", ["pkg1", "pkg2"])
        assert cmd == ["pacman", "-S", "--noconfirm", "pkg1", "pkg2"]
        
        # Test Fedora
        cmd = desktop_installer._get_install_command("fedora", ["pkg1", "pkg2"])
        assert cmd == ["dnf", "install", "-y", "pkg1", "pkg2"]
