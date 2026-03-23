"""Tests for desktop environment installation.

These tests verify desktop environment package definitions,
installation commands, and VNC startup script generation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from tmoe.gui.desktop import (
    DesktopEnvironment,
    DesktopPackage,
    DesktopInstaller,
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
        assert "GNOME 2" in mate.description
    
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
    
    def test_all_desktops_have_required_properties(self):
        """Test that all desktop environments have required properties."""
        for desktop in DesktopEnvironment:
            assert hasattr(desktop, 'id')
            assert hasattr(desktop, 'display_name')
            assert hasattr(desktop, 'description')
            assert isinstance(desktop.id, str)
            assert isinstance(desktop.display_name, str)
            assert isinstance(desktop.description, str)
            assert len(desktop.id) > 0
            assert len(desktop.display_name) > 0


class TestDesktopPackageDefinitions:
    """Test desktop environment package definitions."""
    
    def test_xfce_packages(self):
        """Test XFCE package definitions."""
        pkg = DesktopInstaller.DESKTOPS[DesktopEnvironment.XFCE]
        
        assert "debian" in pkg.packages
        assert "task-xfce-desktop" in pkg.packages["debian"]
        assert "ubuntu" in pkg.packages
        assert "xfce4" in pkg.packages["ubuntu"]
        assert "arch" in pkg.packages
        assert "fedora" in pkg.packages
    
    def test_lxde_packages(self):
        """Test LXDE package definitions."""
        pkg = DesktopInstaller.DESKTOPS[DesktopEnvironment.LXDE]
        
        assert "debian" in pkg.packages
        assert "task-lxde-desktop" in pkg.packages["debian"]
        assert "ubuntu" in pkg.packages
    
    def test_lxqt_packages(self):
        """Test LXQt package definitions."""
        pkg = DesktopInstaller.DESKTOPS[DesktopEnvironment.LXQT]
        
        assert "debian" in pkg.packages
        assert "arch" in pkg.packages
    
    def test_mate_packages(self):
        """Test MATE package definitions."""
        pkg = DesktopInstaller.DESKTOPS[DesktopEnvironment.MATE]
        
        assert "debian" in pkg.packages
        assert "task-mate-desktop" in pkg.packages["debian"]
        assert "fedora" in pkg.packages
    
    def test_kde_packages(self):
        """Test KDE package definitions."""
        pkg = DesktopInstaller.DESKTOPS[DesktopEnvironment.KDE]
        
        assert "debian" in pkg.packages
        assert "task-kde-desktop" in pkg.packages["debian"]
        assert "ubuntu" in pkg.packages
        assert "kubuntu-desktop" in pkg.packages["ubuntu"]
    
    def test_gnome_packages(self):
        """Test GNOME package definitions."""
        pkg = DesktopInstaller.DESKTOPS[DesktopEnvironment.GNOME]
        
        assert "debian" in pkg.packages
        assert "task-gnome-desktop" in pkg.packages["debian"]
        assert "ubuntu" in pkg.packages
        assert "ubuntu-desktop" in pkg.packages["ubuntu"]
    
    def test_cinnamon_packages(self):
        """Test Cinnamon package definitions."""
        pkg = DesktopInstaller.DESKTOPS[DesktopEnvironment.CINNAMON]
        
        assert "debian" in pkg.packages
        assert "task-cinnamon-desktop" in pkg.packages["debian"]
        assert "alpine" in pkg.packages
        assert pkg.packages["alpine"] == []  # Not available on Alpine
    
    def test_budgie_packages(self):
        """Test Budgie package definitions."""
        pkg = DesktopInstaller.DESKTOPS[DesktopEnvironment.BUDGIE]
        
        assert "debian" in pkg.packages
        assert "alpine" in pkg.packages
        assert pkg.packages["alpine"] == []  # Not available on Alpine
    
    def test_deepin_not_in_desktops(self):
        """Test Deepin is not in DESKTOPS (not yet implemented)."""
        assert DesktopEnvironment.DEEPIN not in DesktopInstaller.DESKTOPS


class TestCommonPackages:
    """Test common packages definitions."""
    
    def test_common_packages_structure(self):
        """Test common packages are defined for supported distros."""
        supported_distros = ["debian", "ubuntu", "arch", "fedora"]
        
        for distro in supported_distros:
            assert distro in DesktopInstaller.COMMON_PACKAGES
            assert isinstance(DesktopInstaller.COMMON_PACKAGES[distro], list)
            assert len(DesktopInstaller.COMMON_PACKAGES[distro]) > 0
    
    def test_debian_common_packages(self):
        """Test Debian common packages."""
        pkgs = DesktopInstaller.COMMON_PACKAGES["debian"]
        
        assert "fonts-noto" in pkgs
        assert "fonts-noto-cjk" in pkgs
        assert "fcitx5" in pkgs
    
    def test_ubuntu_common_packages(self):
        """Test Ubuntu common packages."""
        pkgs = DesktopInstaller.COMMON_PACKAGES["ubuntu"]
        
        assert "fonts-noto" in pkgs
        assert "fcitx" in pkgs
    
    def test_arch_common_packages(self):
        """Test Arch common packages."""
        pkgs = DesktopInstaller.COMMON_PACKAGES["arch"]
        
        assert "noto-fonts" in pkgs
        assert "fcitx5" in pkgs


class TestDesktopInstallerSupport:
    """Test desktop installer support detection."""
    
    def test_get_supported_desktops_debian(self, desktop_installer):
        """Test getting supported desktops for Debian."""
        supported = desktop_installer.get_supported_desktops("debian")
        
        assert DesktopEnvironment.XFCE in supported
        assert DesktopEnvironment.LXDE in supported
        assert DesktopEnvironment.MATE in supported
        assert DesktopEnvironment.KDE in supported
        assert DesktopEnvironment.GNOME in supported
    
    def test_get_supported_desktops_ubuntu(self, desktop_installer):
        """Test getting supported desktops for Ubuntu."""
        supported = desktop_installer.get_supported_desktops("ubuntu")
        
        assert DesktopEnvironment.XFCE in supported
        assert DesktopEnvironment.LXDE in supported
    
    def test_get_supported_desktops_alpine(self, desktop_installer):
        """Test getting supported desktops for Alpine."""
        supported = desktop_installer.get_supported_desktops("alpine")
        
        # Alpine has limited support
        assert DesktopEnvironment.XFCE in supported
        # Cinnamon and Budgie are empty lists
        assert DesktopEnvironment.CINNAMON not in supported
        assert DesktopEnvironment.BUDGIE not in supported
    
    def test_get_supported_desktops_unknown(self, desktop_installer):
        """Test getting supported desktops for unknown distro."""
        supported = desktop_installer.get_supported_desktops("unknown-os")
        
        assert supported == []


class TestDesktopInstallerCommands:
    """Test desktop installer command generation."""
    
    def test_get_install_command_debian(self, desktop_installer):
        """Test install command for Debian."""
        cmd = desktop_installer._get_install_command("debian", ["package1", "package2"])
        
        assert cmd[0] == "apt"
        assert "install" in cmd
        assert "-y" in cmd
        assert "package1" in cmd
        assert "package2" in cmd
    
    def test_get_install_command_ubuntu(self, desktop_installer):
        """Test install command for Ubuntu."""
        cmd = desktop_installer._get_install_command("ubuntu", ["test-pkg"])
        
        assert cmd[0] == "apt"
    
    def test_get_install_command_arch(self, desktop_installer):
        """Test install command for Arch."""
        cmd = desktop_installer._get_install_command("arch", ["test-pkg"])
        
        assert cmd[0] == "pacman"
        assert "--noconfirm" in cmd
    
    def test_get_install_command_fedora(self, desktop_installer):
        """Test install command for Fedora."""
        cmd = desktop_installer._get_install_command("fedora", ["test-pkg"])
        
        assert cmd[0] == "dnf"
        assert "-y" in cmd
    
    def test_get_install_command_alpine(self, desktop_installer):
        """Test install command for Alpine."""
        cmd = desktop_installer._get_install_command("alpine", ["test-pkg"])
        
        assert cmd[0] == "apk"
        assert "add" in cmd
    
    def test_get_install_command_unknown(self, desktop_installer):
        """Test install command defaults to apt for unknown distro."""
        cmd = desktop_installer._get_install_command("unknown", ["test-pkg"])
        
        assert cmd[0] == "apt"


class TestDesktopInstallation:
    """Test desktop installation process."""
    
    @pytest.mark.asyncio
    async def test_install_desktop_success(self, desktop_installer):
        """Test successful desktop installation."""
        desktop_installer.backend.exec = AsyncMock(return_value=(0, "", ""))
        
        result = await desktop_installer.install_desktop(
            DesktopEnvironment.XFCE,
            distro="debian"
        )
        
        assert result is True
        desktop_installer.backend.exec.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_install_desktop_failure(self, desktop_installer):
        """Test desktop installation failure."""
        desktop_installer.backend.exec = AsyncMock(return_value=(1, "", "error"))
        
        result = await desktop_installer.install_desktop(
            DesktopEnvironment.XFCE,
            distro="debian"
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_install_desktop_unknown(self, desktop_installer):
        """Test installing unknown desktop raises error."""
        with pytest.raises(ValueError, match="Unknown desktop"):
            await desktop_installer.install_desktop(
                DesktopEnvironment.DEEPIN,  # Not in DESKTOPS
                distro="debian"
            )
    
    @pytest.mark.asyncio
    async def test_install_desktop_not_available(self, desktop_installer):
        """Test installing desktop not available for distro."""
        with pytest.raises(RuntimeError, match="not available"):
            await desktop_installer.install_desktop(
                DesktopEnvironment.CINNAMON,
                distro="alpine"  # Cinnamon not available on Alpine
            )
    
    @pytest.mark.asyncio
    async def test_install_desktop_includes_common_packages(self, desktop_installer):
        """Test that installation includes common packages."""
        desktop_installer.backend.exec = AsyncMock(return_value=(0, "", ""))
        
        await desktop_installer.install_desktop(
            DesktopEnvironment.XFCE,
            distro="debian"
        )
        
        # Check that exec was called with combined packages
        call_args = desktop_installer.backend.exec.call_args[0]
        cmd = call_args[1]  # Second positional arg is the command
        
        # Should include both desktop and common packages
        assert "task-xfce-desktop" in cmd or "xfce4" in cmd
        assert "fonts-noto" in cmd or any("fonts" in str(c) for c in cmd)
    
    @pytest.mark.asyncio
    async def test_install_desktop_auto_detect_distro(self, desktop_installer):
        """Test auto-detecting distro when not specified."""
        desktop_installer.backend.exec = AsyncMock(return_value=(0, "", ""))
        desktop_installer._detect_distro = Mock(return_value="ubuntu")
        
        await desktop_installer.install_desktop(DesktopEnvironment.XFCE)
        
        desktop_installer._detect_distro.assert_called_once()


class TestVncStartupScript:
    """Test VNC startup script generation."""
    
    def test_xfce_startup_script(self, desktop_installer):
        """Test XFCE startup script."""
        script = desktop_installer._get_xstartup_script(DesktopEnvironment.XFCE)
        
        assert "#!/bin/bash" in script
        assert "unset SESSION_MANAGER" in script
        assert "unset DBUS_SESSION_BUS_ADDRESS" in script
        assert "exec startxfce4" in script
    
    def test_lxde_startup_script(self, desktop_installer):
        """Test LXDE startup script."""
        script = desktop_installer._get_xstartup_script(DesktopEnvironment.LXDE)
        
        assert "exec startlxde" in script
    
    def test_lxqt_startup_script(self, desktop_installer):
        """Test LXQt startup script."""
        script = desktop_installer._get_xstartup_script(DesktopEnvironment.LXQT)
        
        assert "exec startlxqt" in script
    
    def test_mate_startup_script(self, desktop_installer):
        """Test MATE startup script."""
        script = desktop_installer._get_xstartup_script(DesktopEnvironment.MATE)
        
        assert "exec mate-session" in script
    
    def test_kde_startup_script(self, desktop_installer):
        """Test KDE startup script."""
        script = desktop_installer._get_xstartup_script(DesktopEnvironment.KDE)
        
        assert "exec startplasma-x11" in script
    
    def test_gnome_startup_script(self, desktop_installer):
        """Test GNOME startup script."""
        script = desktop_installer._get_xstartup_script(DesktopEnvironment.GNOME)
        
        assert "exec gnome-session" in script
    
    def test_unknown_desktop_defaults_to_xfce(self, desktop_installer):
        """Test unknown desktop defaults to XFCE script."""
        script = desktop_installer._get_xstartup_script(DesktopEnvironment.CINNAMON)
        
        # Cinnamon doesn't have a script defined, should fallback to XFCE
        assert "exec startxfce4" in script
    
    @pytest.mark.asyncio
    async def test_setup_vnc_startup_root(self, desktop_installer):
        """Test VNC startup setup for root user."""
        desktop_installer.backend.exec = AsyncMock(return_value=(0, "", ""))
        
        await desktop_installer.setup_vnc_startup(DesktopEnvironment.XFCE, user="root")
        
        # Should create .vnc directory
        calls = desktop_installer.backend.exec.call_args_list
        
        # First call creates directory
        assert calls[0][0][1][0] == "mkdir"
        assert "/root/.vnc" in calls[0][0][1]
    
    @pytest.mark.asyncio
    async def test_setup_vnc_startup_regular_user(self, desktop_installer):
        """Test VNC startup setup for regular user."""
        desktop_installer.backend.exec = AsyncMock(return_value=(0, "", ""))
        
        await desktop_installer.setup_vnc_startup(DesktopEnvironment.XFCE, user="debian")
        
        # Should create .vnc directory in user's home
        calls = desktop_installer.backend.exec.call_args_list
        assert "/home/debian/.vnc" in calls[0][0][1]


class TestDesktopInstallerEdgeCases:
    """Test desktop installer edge cases."""
    
    @pytest.mark.asyncio
    async def test_install_all_supported_desktops(self, desktop_installer):
        """Test that all supported desktops can be installed."""
        desktop_installer.backend.exec = AsyncMock(return_value=(0, "", ""))
        
        supported = desktop_installer.get_supported_desktops("debian")
        
        for desktop in supported:
            result = await desktop_installer.install_desktop(desktop, distro="debian")
            assert result is True, f"Failed to install {desktop.display_name}"
    
    def test_desktop_package_post_init(self):
        """Test DesktopPackage post_init handles None recommends."""
        pkg = DesktopPackage(
            name="Test",
            packages={"debian": ["test"]},
            recommends=None
        )
        
        assert pkg.recommends == {}
    
    def test_desktop_package_with_recommends(self):
        """Test DesktopPackage with recommendations."""
        pkg = DesktopPackage(
            name="Test",
            packages={"debian": ["test"]},
            recommends={"debian": ["recommend1"]}
        )
        
        assert "debian" in pkg.recommends
        assert "recommend1" in pkg.recommends["debian"]
