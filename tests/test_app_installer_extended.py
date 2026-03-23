"""Extended tests for app installer.

These tests cover additional applications and features that exist
in the shell version but may be missing in the Python version.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, mock_open

from tmoe.app.center import AppCenter, AppCategory, Application


class TestAppInstallerBrowsers:
    """Test browser installation features."""
    
    @pytest.fixture
    def app_center(self):
        """Create an app center instance."""
        center = AppCenter()
        return center
    
    def test_firefox_app_definition(self, app_center):
        """Test Firefox application definition."""
        app = app_center.get_app("firefox")
        
        assert app is not None
        assert app.name == "Firefox"
        assert app.category == AppCategory.BROWSER
        assert "debian" in app.packages
        assert "ubuntu" in app.packages
        assert "firefox" in app.packages["debian"]
    
    def test_chromium_app_definition(self, app_center):
        """Test Chromium application definition."""
        app = app_center.get_app("chromium")
        
        assert app is not None
        assert app.name == "Chromium"
        assert app.category == AppCategory.BROWSER
    
    def test_edge_app_definition(self, app_center):
        """Test Microsoft Edge application definition."""
        app = app_center.get_app("edge")
        
        assert app is not None
        assert app.name == "Microsoft Edge"
        assert app.external_url == "https://packages.microsoft.com/repos/edge"
    
    @pytest.mark.asyncio
    async def test_install_browser_firefox(self, app_center):
        """Test installing Firefox browser."""
        with patch.object(app_center, '_install_packages', new_callable=AsyncMock, return_value=True) as mock_install:
            result = await app_center.install_browser("firefox")
            
            assert result is True
            mock_install.assert_called_once()
            
            # Check correct packages for distro
            args = mock_install.call_args[0]
            assert len(args) == 2
            assert args[1] == app_center.get_app("firefox").packages[args[0]]
    
    @pytest.mark.asyncio
    async def test_install_unknown_browser(self, app_center):
        """Test installing unknown browser raises error."""
        with pytest.raises(ValueError, match="Unknown application"):
            await app_center.install_browser("unknown-browser")


class TestAppInstallerOffice:
    """Test office suite installation features."""
    
    def test_libreoffice_app_definition(self):
        """Test LibreOffice application definition."""
        center = AppCenter()
        app = center.get_app("libreoffice")
        
        assert app is not None
        assert app.name == "LibreOffice"
        assert app.category == AppCategory.OFFICE
        assert "debian" in app.packages
        assert "libreoffice" in app.packages["debian"]
    
    @pytest.mark.asyncio
    async def test_install_office_default(self):
        """Test installing default office suite (LibreOffice)."""
        center = AppCenter()
        
        with patch.object(center, '_install_packages', new_callable=AsyncMock, return_value=True) as mock_install:
            result = await center.install_office()
            
            assert result is True
            mock_install.assert_called_once()
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    def test_wps_office_app_definition(self):
        """Test WPS Office application definition.
        
        Shell version supports WPS Office installation.
        """
        center = AppCenter()
        app = center.get_app("wps-office")
        
        assert app is not None
        assert app.name == "WPS Office"
        assert app.category == AppCategory.OFFICE
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    def test_yongzhong_office_app_definition(self):
        """Test 永中 Office application definition.
        
        Shell version supports 永中 Office installation.
        """
        center = AppCenter()
        app = center.get_app("yongzhong-office")
        
        assert app is not None
        assert app.name == "永中 Office"


class TestAppInstallerDevelopment:
    """Test development tool installation features."""
    
    def test_vscode_app_definition(self):
        """Test VS Code application definition."""
        center = AppCenter()
        app = center.get_app("vscode")
        
        assert app is not None
        assert app.name == "VS Code"
        assert app.category == AppCategory.DEVELOPMENT
    
    def test_vim_app_definition(self):
        """Test Vim application definition."""
        center = AppCenter()
        app = center.get_app("vim")
        
        assert app is not None
        assert app.name == "Vim"
    
    def test_git_app_definition(self):
        """Test Git application definition."""
        center = AppCenter()
        app = center.get_app("git")
        
        assert app is not None
        assert app.name == "Git"
    
    @pytest.mark.asyncio
    async def test_install_dev_tool(self):
        """Test installing development tool."""
        center = AppCenter()
        
        with patch.object(center, '_install_packages', new_callable=AsyncMock, return_value=True):
            result = await center.install_dev_tool("git")
            assert result is True
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    def test_jetbrains_ide_definitions(self):
        """Test JetBrains IDE application definitions.
        
        Shell version supports:
        - IntelliJ IDEA
        - PyCharm
        - WebStorm
        - CLion
        - GoLand
        - Android Studio
        """
        center = AppCenter()
        
        jetbrains_ides = [
            "intellij-idea",
            "pycharm",
            "webstorm",
            "clion",
            "goland",
            "android-studio",
        ]
        
        for ide in jetbrains_ides:
            app = center.get_app(ide)
            assert app is not None, f"Missing {ide} definition"
            assert app.category == AppCategory.DEVELOPMENT


class TestAppInstallerMultimedia:
    """Test multimedia application installation features."""
    
    def test_mpv_app_definition(self):
        """Test MPV application definition."""
        center = AppCenter()
        app = center.get_app("mpv")
        
        assert app is not None
        assert app.name == "MPV"
        assert app.category == AppCategory.MULTIMEDIA
    
    def test_gimp_app_definition(self):
        """Test GIMP application definition."""
        center = AppCenter()
        app = center.get_app("gimp")
        
        assert app is not None
        assert app.name == "GIMP"
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    def test_spotify_app_definition(self):
        """Test Spotify application definition."""
        center = AppCenter()
        app = center.get_app("spotify")
        
        assert app is not None
        assert app.name == "Spotify"
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    def test_audacity_app_definition(self):
        """Test Audacity application definition."""
        center = AppCenter()
        app = center.get_app("audacity")
        
        assert app is not None
        assert app.name == "Audacity"


class TestAppInstallerInputMethods:
    """Test input method installation features.
    
    Shell version has extensive input method support.
    """
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    def test_fcitx4_app_definition(self):
        """Test Fcitx4 input method definition."""
        center = AppCenter()
        app = center.get_app("fcitx4")
        
        assert app is not None
        assert app.name == "Fcitx4"
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    def test_fcitx5_app_definition(self):
        """Test Fcitx5 input method definition."""
        center = AppCenter()
        app = center.get_app("fcitx5")
        
        assert app is not None
        assert app.name == "Fcitx5"
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    def test_sogou_pinyin_app_definition(self):
        """Test Sogou Pinyin input method definition."""
        center = AppCenter()
        app = center.get_app("sogou-pinyin")
        
        assert app is not None
        assert app.name == "搜狗拼音"
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    def test_baidu_pinyin_app_definition(self):
        """Test Baidu Pinyin input method definition."""
        center = AppCenter()
        app = center.get_app("baidu-pinyin")
        
        assert app is not None
        assert app.name == "百度拼音"
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    def test_rime_app_definition(self):
        """Test Rime input method definition."""
        center = AppCenter()
        app = center.get_app("rime")
        
        assert app is not None
        assert app.name == "Rime"


class TestAppInstallerGames:
    """Test game installation features.
    
    Shell version supports various games and game platforms.
    """
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    def test_steam_app_definition(self):
        """Test Steam application definition."""
        center = AppCenter()
        app = center.get_app("steam")
        
        assert app is not None
        assert app.name == "Steam"
        assert app.category == AppCategory.GAME
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    def test_retroarch_app_definition(self):
        """Test RetroArch application definition."""
        center = AppCenter()
        app = center.get_app("retroarch")
        
        assert app is not None
        assert app.name == "RetroArch"
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    def test_dolphin_emulator_app_definition(self):
        """Test Dolphin emulator application definition."""
        center = AppCenter()
        app = center.get_app("dolphin-emu")
        
        assert app is not None
        assert app.name == "Dolphin"


class TestAppInstallerSocial:
    """Test social/communication app installation features."""
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    def test_linuxqq_app_definition(self):
        """Test Linux QQ application definition."""
        center = AppCenter()
        app = center.get_app("linuxqq")
        
        assert app is not None
        assert app.name == "Linux QQ"
        assert app.category == AppCategory.SOCIAL
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    def test_wechat_app_definition(self):
        """Test WeChat application definition."""
        center = AppCenter()
        app = center.get_app("wechat")
        
        assert app is not None
        assert app.name == "WeChat"
    
    @pytest.mark.skip(reason="Feature not yet implemented in Python version")
    def test_telegram_app_definition(self):
        """Test Telegram application definition."""
        center = AppCenter()
        app = center.get_app("telegram")
        
        assert app is not None
        assert app.name == "Telegram"


class TestAppInstallerCategories:
    """Test app category management."""
    
    def test_get_apps_by_category_browser(self):
        """Test getting browser applications."""
        center = AppCenter()
        browsers = center.get_apps_by_category(AppCategory.BROWSER)
        
        browser_names = {app.name for app in browsers}
        assert "Firefox" in browser_names
        assert "Chromium" in browser_names
        assert "Microsoft Edge" in browser_names
    
    def test_get_apps_by_category_development(self):
        """Test getting development applications."""
        center = AppCenter()
        dev_tools = center.get_apps_by_category(AppCategory.DEVELOPMENT)
        
        tool_names = {app.name for app in dev_tools}
        assert "VS Code" in tool_names
        assert "Vim" in tool_names
        assert "Git" in tool_names
    
    def test_get_apps_by_category_empty(self):
        """Test getting apps from category with no apps."""
        center = AppCenter()
        
        # Check if GAME category is empty (not implemented yet)
        games = center.get_apps_by_category(AppCategory.GAME)
        assert len(games) == 0  # Expected to be empty until implemented


class TestAppInstallerDistroDetection:
    """Test Linux distribution detection."""
    
    def test_detect_distro_debian(self):
        """Test Debian detection."""
        center = AppCenter()
        
        os_release = 'PRETTY_NAME="Debian GNU/Linux 12"\nID=debian'
        with patch('builtins.open', mock_open(read_data=os_release)):
            distro = center._detect_distro()
            assert distro == "debian"
    
    def test_detect_distro_ubuntu(self):
        """Test Ubuntu detection."""
        center = AppCenter()
        
        os_release = 'PRETTY_NAME="Ubuntu 22.04"\nID=ubuntu'
        with patch('builtins.open', mock_open(read_data=os_release)):
            distro = center._detect_distro()
            assert distro == "ubuntu"
    
    def test_detect_distro_arch(self):
        """Test Arch Linux detection."""
        center = AppCenter()
        
        os_release = 'PRETTY_NAME="Arch Linux"\nID=arch'
        with patch('builtins.open', mock_open(read_data=os_release)):
            distro = center._detect_distro()
            assert distro == "arch"
    
    def test_detect_distro_fedora(self):
        """Test Fedora detection."""
        center = AppCenter()
        
        os_release = 'PRETTY_NAME="Fedora Linux 39"\nID=fedora'
        with patch('builtins.open', mock_open(read_data=os_release)):
            distro = center._detect_distro()
            assert distro == "fedora"
    
    def test_detect_distro_fallback(self):
        """Test fallback to debian when detection fails."""
        center = AppCenter()
        
        with patch('builtins.open', side_effect=FileNotFoundError()):
            distro = center._detect_distro()
            assert distro == "debian"


class TestAppInstallerPackageCommands:
    """Test package manager command generation."""
    
    def test_install_command_debian(self):
        """Test Debian/Ubuntu install command."""
        center = AppCenter()
        
        cmd = center._get_install_command("debian", ["git", "vim"])
        assert cmd == ["apt", "install", "-y", "git", "vim"]
    
    def test_install_command_ubuntu(self):
        """Test Ubuntu install command."""
        center = AppCenter()
        
        cmd = center._get_install_command("ubuntu", ["htop"])
        assert cmd == ["apt", "install", "-y", "htop"]
    
    def test_install_command_arch(self):
        """Test Arch install command."""
        center = AppCenter()
        
        cmd = center._get_install_command("arch", ["firefox"])
        assert cmd == ["pacman", "-S", "--noconfirm", "firefox"]
    
    def test_install_command_fedora(self):
        """Test Fedora install command."""
        center = AppCenter()
        
        cmd = center._get_install_command("fedora", ["chromium"])
        assert cmd == ["dnf", "install", "-y", "chromium"]
    
    def test_install_command_alpine(self):
        """Test Alpine install command."""
        center = AppCenter()
        
        cmd = center._get_install_command("alpine", ["curl"])
        assert cmd == ["apk", "add", "curl"]
    
    def test_install_command_unknown(self):
        """Test unknown distro falls back to apt."""
        center = AppCenter()
        
        cmd = center._get_install_command("unknown", ["package"])
        assert cmd == ["apt", "install", "-y", "package"]


class TestAppInstallerErrorHandling:
    """Test app installer error handling."""
    
    @pytest.mark.asyncio
    async def test_install_failure_handling(self):
        """Test handling of installation failure."""
        center = AppCenter()
        
        with patch.object(center, '_install_packages', new_callable=AsyncMock) as mock_install:
            mock_install.side_effect = RuntimeError("Package not found")
            
            with pytest.raises(RuntimeError, match="Package not found"):
                await center.install("firefox")
    
    @pytest.mark.asyncio
    async def test_app_not_available_for_distro(self):
        """Test app not available for specific distro."""
        center = AppCenter()
        
        # Edge is only available for debian/ubuntu
        with pytest.raises(RuntimeError, match="not available"):
            await center.install("edge", distro="alpine")
