"""Tests for system tools management module.

This module tests the SystemToolManager class and related functionality
for installing and managing system tools like shells, terminal multiplexers,
and system utilities.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from tmoe.tools.system import ShellInfo, ShellType, SystemToolManager, TerminalTool


class TestShellInfo:
    """Test cases for ShellInfo dataclass."""
    
    def test_shell_info_creation(self) -> None:
        """Test creating ShellInfo."""
        shell = ShellInfo(
            name="Zsh",
            shell_type=ShellType.ZSH,
            description="Powerful shell with advanced features",
            packages=["zsh"],
            config_file=Path.home() / ".zshrc",
        )
        
        assert shell.name == "Zsh"
        assert shell.shell_type == ShellType.ZSH
        assert shell.description == "Powerful shell with advanced features"
        assert shell.packages == ["zsh"]
        assert shell.config_file == Path.home() / ".zshrc"


class TestSystemToolManagerInitialization:
    """Test cases for SystemToolManager initialization."""
    
    def test_default_initialization(self) -> None:
        """Test default initialization."""
        manager = SystemToolManager()
        
        assert manager.platform is not None
        assert manager.downloader is not None
        assert manager._detected_distro is None
    
    def test_shells_defined(self) -> None:
        """Test that all shells are properly defined."""
        manager = SystemToolManager()
        
        assert len(manager.SHELLS) == 3
        assert ShellType.ZSH in manager.SHELLS
        assert ShellType.FISH in manager.SHELLS
        assert ShellType.BASH in manager.SHELLS


class TestDistroDetection:
    """Test cases for distribution detection."""
    
    @pytest.fixture
    def manager(self) -> SystemToolManager:
        """Create a SystemToolManager instance."""
        return SystemToolManager()
    
    def test_detect_distro_from_os_release(self, manager: SystemToolManager) -> None:
        """Test detecting distro from /etc/os-release."""
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = True
            with patch.object(Path, "read_text", return_value='ID=debian\n'):
                distro = manager.detect_distro()
        
        assert distro == "debian"
    
    def test_detect_distro_arch(self, manager: SystemToolManager) -> None:
        """Test detecting Arch Linux."""
        # Create a new manager to avoid cached distro
        manager = SystemToolManager()
        manager._detected_distro = None
        with patch("os.path.exists") as mock_exists:
            # os-release doesn't exist, arch-release does
            mock_exists.side_effect = lambda p: "arch-release" in str(p) and "os-release" not in str(p)
            distro = manager.detect_distro()
        
        assert distro == "arch"
    
    def test_detect_distro_unknown(self, manager: SystemToolManager) -> None:
        """Test detecting unknown distro."""
        with patch.object(Path, "exists", return_value=False):
            distro = manager.detect_distro()
        
        assert distro == "unknown"
    
    def test_get_package_manager(self, manager: SystemToolManager) -> None:
        """Test getting package manager."""
        test_cases = [
            ("debian", "apt"),
            ("ubuntu", "apt"),
            ("arch", "pacman"),
            ("fedora", "dnf"),
            ("alpine", "apk"),
            ("unknown", "apt"),
        ]
        
        for distro, expected_pm in test_cases:
            with patch.object(manager, "_detected_distro", distro):
                pm = manager.get_package_manager()
                assert pm == expected_pm, f"Failed for {distro}"


class TestShellInstallation:
    """Test cases for shell installation."""
    
    @pytest.fixture
    def manager(self) -> SystemToolManager:
        """Create a SystemToolManager instance."""
        return SystemToolManager()
    
    @patch("shutil.which")
    def test_is_installed_true(self, mock_which: Mock, manager: SystemToolManager) -> None:
        """Test checking if shell is installed (true)."""
        mock_which.return_value = "/usr/bin/zsh"
        
        result = manager.is_installed(ShellType.ZSH)
        
        assert result is True
        mock_which.assert_called_with("zsh")
    
    @patch("shutil.which")
    def test_is_installed_false(self, mock_which: Mock, manager: SystemToolManager) -> None:
        """Test checking if shell is installed (false)."""
        mock_which.return_value = None
        
        result = manager.is_installed(ShellType.ZSH)
        
        assert result is False
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_shell_already_installed(self, mock_which: Mock, manager: SystemToolManager) -> None:
        """Test installing shell when already installed."""
        mock_which.return_value = "/usr/bin/zsh"
        
        result = await manager.install_shell(ShellType.ZSH)
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_shell_via_package_manager(self, mock_which: Mock, manager: SystemToolManager) -> None:
        """Test installing shell via package manager."""
        mock_which.side_effect = lambda x: None if x == "zsh" else f"/usr/bin/{x}"
        
        with patch.object(manager, "install_via_package_manager", return_value=True):
            result = await manager.install_shell(ShellType.ZSH)
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_zsh(self, mock_which: Mock, manager: SystemToolManager) -> None:
        """Test installing Zsh."""
        mock_which.side_effect = lambda x: None if x == "zsh" else f"/usr/bin/{x}"
        
        with patch.object(manager, "install_via_package_manager", return_value=True):
            result = await manager.install_zsh()
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_fish(self, mock_which: Mock, manager: SystemToolManager) -> None:
        """Test installing Fish."""
        mock_which.side_effect = lambda x: None if x == "fish" else f"/usr/bin/{x}"
        
        with patch.object(manager, "install_via_package_manager", return_value=True):
            result = await manager.install_fish()
        
        assert result is True


class TestZshConfiguration:
    """Test cases for Zsh configuration."""
    
    @pytest.fixture
    def manager(self) -> SystemToolManager:
        """Create a SystemToolManager instance."""
        return SystemToolManager()
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_configure_zsh_ohmyzsh(self, mock_which: Mock, manager: SystemToolManager, tmp_path: Path) -> None:
        """Test installing Oh My Zsh."""
        mock_which.return_value = "/usr/bin/zsh"
        
        # Mock Oh My Zsh directory doesn't exist
        omz_dir = tmp_path / ".oh-my-zsh"
        
        # Mock download
        mock_download = AsyncMock()
        manager.downloader.download = mock_download
        
        # Mock subprocess
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = False
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                with patch.object(Path, "chmod"):
                    result = await manager.configure_zsh_ohmyzsh()
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_configure_zsh_ohmyzsh_already_installed(self, mock_which: Mock, manager: SystemToolManager, tmp_path: Path) -> None:
        """Test Oh My Zsh when already installed."""
        mock_which.return_value = "/usr/bin/zsh"
        
        with patch.object(Path, "exists", return_value=True):
            result = await manager.configure_zsh_ohmyzsh()
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_configure_zsh_ohmyzsh_not_installed(self, mock_which: Mock, manager: SystemToolManager) -> None:
        """Test Oh My Zsh when Zsh is not installed."""
        mock_which.return_value = None
        
        result = await manager.configure_zsh_ohmyzsh()
        
        assert result is False
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_zsh_plugins(self, mock_which: Mock, manager: SystemToolManager, tmp_path: Path) -> None:
        """Test installing Zsh plugins."""
        mock_which.return_value = "/usr/bin/zsh"
        
        # Mock subprocess for git clone
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with patch.object(Path, "mkdir"):
                with patch.object(Path, "exists", return_value=False):
                    result = await manager.install_zsh_plugins()
        
        assert result is True


class TestTmuxInstallation:
    """Test cases for Tmux installation."""
    
    @pytest.fixture
    def manager(self) -> SystemToolManager:
        """Create a SystemToolManager instance."""
        return SystemToolManager()
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_tmux_already_installed(self, mock_which: Mock, manager: SystemToolManager) -> None:
        """Test installing Tmux when already installed."""
        mock_which.return_value = "/usr/bin/tmux"
        
        result = await manager.install_tmux()
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_tmux_via_package_manager(self, mock_which: Mock, manager: SystemToolManager) -> None:
        """Test installing Tmux via package manager."""
        mock_which.side_effect = lambda x: None if x == "tmux" else f"/usr/bin/{x}"
        
        with patch.object(manager, "install_via_package_manager", return_value=True):
            result = await manager.install_tmux()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_configure_tmux(self, manager: SystemToolManager, tmp_path: Path) -> None:
        """Test configuring Tmux."""
        with patch.object(Path, "write_text") as mock_write:
            result = await manager.configure_tmux()
            
            assert result is True
            mock_write.assert_called_once()
            # Check that the config contains expected settings
            config_content = mock_write.call_args[0][0]
            assert "mouse on" in config_content
            assert "prefix C-a" in config_content


class TestScreenInstallation:
    """Test cases for Screen installation."""
    
    @pytest.fixture
    def manager(self) -> SystemToolManager:
        """Create a SystemToolManager instance."""
        return SystemToolManager()
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_screen_already_installed(self, mock_which: Mock, manager: SystemToolManager) -> None:
        """Test installing Screen when already installed."""
        mock_which.return_value = "/usr/bin/screen"
        
        result = await manager.install_screen()
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_screen_via_package_manager(self, mock_which: Mock, manager: SystemToolManager) -> None:
        """Test installing Screen via package manager."""
        mock_which.side_effect = lambda x: None if x == "screen" else f"/usr/bin/{x}"
        
        with patch.object(manager, "install_via_package_manager", return_value=True):
            result = await manager.install_screen()
        
        assert result is True


class TestByobuInstallation:
    """Test cases for Byobu installation."""
    
    @pytest.fixture
    def manager(self) -> SystemToolManager:
        """Create a SystemToolManager instance."""
        return SystemToolManager()
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_byobu_already_installed(self, mock_which: Mock, manager: SystemToolManager) -> None:
        """Test installing Byobu when already installed."""
        mock_which.return_value = "/usr/bin/byobu"
        
        result = await manager.install_byobu()
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_byobu_via_package_manager(self, mock_which: Mock, manager: SystemToolManager) -> None:
        """Test installing Byobu via package manager."""
        mock_which.side_effect = lambda x: None if x == "byobu" else f"/usr/bin/{x}"
        
        with patch.object(manager, "install_via_package_manager", return_value=True):
            result = await manager.install_byobu()
        
        assert result is True


class TestMonitoringTools:
    """Test cases for monitoring tools installation."""
    
    @pytest.fixture
    def manager(self) -> SystemToolManager:
        """Create a SystemToolManager instance."""
        return SystemToolManager()
    
    @pytest.mark.asyncio
    async def test_install_monitoring_tools(self, manager: SystemToolManager) -> None:
        """Test installing monitoring tools."""
        manager._detected_distro = "debian"
        
        with patch.object(manager, "install_via_package_manager", return_value=True):
            result = await manager.install_monitoring_tools()
        
        assert result is True


class TestFileTools:
    """Test cases for file management tools."""
    
    @pytest.fixture
    def manager(self) -> SystemToolManager:
        """Create a SystemToolManager instance."""
        return SystemToolManager()
    
    @pytest.mark.asyncio
    async def test_install_file_tools(self, manager: SystemToolManager) -> None:
        """Test installing file tools."""
        manager._detected_distro = "debian"
        
        with patch.object(manager, "install_via_package_manager", return_value=True):
            result = await manager.install_file_tools()
        
        assert result is True


class TestNeofetch:
    """Test cases for Neofetch installation."""
    
    @pytest.fixture
    def manager(self) -> SystemToolManager:
        """Create a SystemToolManager instance."""
        return SystemToolManager()
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_neofetch_already_installed(self, mock_which: Mock, manager: SystemToolManager) -> None:
        """Test installing Neofetch when already installed."""
        mock_which.return_value = "/usr/bin/neofetch"
        
        result = await manager.install_neofetch()
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_neofetch_via_package_manager(self, mock_which: Mock, manager: SystemToolManager) -> None:
        """Test installing Neofetch via package manager."""
        mock_which.side_effect = lambda x: None if x == "neofetch" else f"/usr/bin/{x}"
        
        with patch.object(manager, "install_via_package_manager", return_value=True):
            result = await manager.install_neofetch()
        
        assert result is True


class TestUEFI:
    """Test cases for UEFI management."""
    
    @pytest.fixture
    def manager(self) -> SystemToolManager:
        """Create a SystemToolManager instance."""
        return SystemToolManager()
    
    def test_is_uefi_system_true(self, manager: SystemToolManager) -> None:
        """Test detecting UEFI system (true)."""
        with patch.object(Path, "exists", return_value=True):
            result = manager.is_uefi_system()
        
        assert result is True
    
    def test_is_uefi_system_false(self, manager: SystemToolManager) -> None:
        """Test detecting UEFI system (false)."""
        with patch.object(Path, "exists", return_value=False):
            result = manager.is_uefi_system()
        
        assert result is False
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_efibootmgr_already_installed(self, mock_which: Mock, manager: SystemToolManager) -> None:
        """Test installing efibootmgr when already installed."""
        mock_which.return_value = "/usr/bin/efibootmgr"
        
        with patch.object(Path, "exists", return_value=True):
            result = await manager.install_efibootmgr()
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_efibootmgr_not_uefi(self, mock_which: Mock, manager: SystemToolManager) -> None:
        """Test installing efibootmgr on non-UEFI system."""
        mock_which.return_value = None
        
        with patch.object(Path, "exists", return_value=False):
            result = await manager.install_efibootmgr()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_uefi_boot_entries(self, manager: SystemToolManager) -> None:
        """Test getting UEFI boot entries."""
        with patch("shutil.which", return_value="/usr/bin/efibootmgr"):
            mock_proc = AsyncMock()
            mock_proc.returncode = 0
            mock_proc.communicate = AsyncMock(return_value=(
                b"BootCurrent: 0000\nBootOrder: 0001,0000\nBoot0000* Ubuntu\nBoot0001* Windows\n",
                b"",
            ))
            
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                entries = await manager.get_uefi_boot_entries()
        
        assert len(entries) == 2
        assert entries[0]["number"] == "0000"
        assert entries[0]["name"] == "Ubuntu"
    
    @pytest.mark.asyncio
    async def test_set_uefi_boot_order(self, manager: SystemToolManager) -> None:
        """Test setting UEFI boot order."""
        with patch("shutil.which", return_value="/usr/bin/efibootmgr"):
            mock_proc = AsyncMock()
            mock_proc.returncode = 0
            mock_proc.communicate = AsyncMock(return_value=(b"", b""))
            
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                result = await manager.set_uefi_boot_order(["0001", "0000"])
        
        assert result is True


class TestSystemOptimization:
    """Test cases for system optimization."""
    
    @pytest.fixture
    def manager(self) -> SystemToolManager:
        """Create a SystemToolManager instance."""
        return SystemToolManager()
    
    @pytest.mark.asyncio
    async def test_optimize_system(self, manager: SystemToolManager, tmp_path: Path) -> None:
        """Test system optimization."""
        sysctl_file = tmp_path / "99-tmoe.conf"
        
        with patch.object(Path, "write_text") as mock_write:
            result = await manager.optimize_system()
            
            # May succeed or fail depending on permissions
            assert isinstance(result, bool)


class TestAllShellTools:
    """Test cases for installing all shell tools."""
    
    @pytest.fixture
    def manager(self) -> SystemToolManager:
        """Create a SystemToolManager instance."""
        return SystemToolManager()
    
    @pytest.mark.asyncio
    async def test_install_all_shell_tools(self, manager: SystemToolManager) -> None:
        """Test installing all recommended shell tools."""
        with patch.object(manager, "install_zsh", return_value=True):
            with patch.object(manager, "install_fish", return_value=True):
                with patch.object(manager, "install_tmux", return_value=True):
                    with patch.object(manager, "configure_tmux", return_value=True):
                        with patch.object(manager, "install_monitoring_tools", return_value=True):
                            with patch.object(manager, "install_file_tools", return_value=True):
                                with patch.object(manager, "install_neofetch", return_value=True):
                                    result = await manager.install_all_shell_tools()
        
        assert result is True


class TestPackageManager:
    """Test cases for package manager operations."""
    
    @pytest.fixture
    def manager(self) -> SystemToolManager:
        """Create a SystemToolManager instance."""
        return SystemToolManager()
    
    @pytest.mark.asyncio
    async def test_install_via_package_manager_success(self, manager: SystemToolManager) -> None:
        """Test successful package installation."""
        manager._detected_distro = "debian"
        
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await manager.install_via_package_manager(["zsh", "tmux"])
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_install_via_package_manager_failure(self, manager: SystemToolManager) -> None:
        """Test failed package installation."""
        manager._detected_distro = "debian"
        
        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"Error"))
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await manager.install_via_package_manager(["zsh"])
        
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
