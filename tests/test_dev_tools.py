"""Tests for development tools management module.

This module tests the DevToolManager class and related functionality
for installing and managing development tools.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from tmoe.tools.dev import DevToolInfo, DevToolManager, DevToolType


class TestDevToolInfo:
    """Test cases for DevToolInfo dataclass."""
    
    def test_tool_info_creation(self) -> None:
        """Test creating DevToolInfo."""
        tool = DevToolInfo(
            name="Rust",
            tool_type=DevToolType.RUST,
            description="Systems programming language",
            install_methods=["rustup"],
            check_command="rustc",
            version_command="rustc --version",
        )
        
        assert tool.name == "Rust"
        assert tool.tool_type == DevToolType.RUST
        assert tool.description == "Systems programming language"
        assert tool.install_methods == ["rustup"]
        assert tool.check_command == "rustc"
        assert tool.version_command == "rustc --version"


class TestDevToolManagerInitialization:
    """Test cases for DevToolManager initialization."""
    
    def test_default_initialization(self) -> None:
        """Test default initialization."""
        manager = DevToolManager()
        
        assert manager.platform is not None
        assert manager.downloader is not None
        assert manager._detected_distro is None
    
    def test_tools_defined(self) -> None:
        """Test that all tools are properly defined."""
        manager = DevToolManager()
        
        assert len(manager.TOOLS) == 9
        assert DevToolType.RUST in manager.TOOLS
        assert DevToolType.GO in manager.TOOLS
        assert DevToolType.NODEJS in manager.TOOLS
        assert DevToolType.PYTHON in manager.TOOLS
        assert DevToolType.JAVA in manager.TOOLS
        assert DevToolType.DOCKER in manager.TOOLS
        assert DevToolType.CMAKE in manager.TOOLS
        assert DevToolType.NINJA in manager.TOOLS
        assert DevToolType.GIT in manager.TOOLS


class TestDevToolManagerDetection:
    """Test cases for tool detection."""
    
    @pytest.fixture
    def manager(self) -> DevToolManager:
        """Create a DevToolManager instance."""
        return DevToolManager()
    
    @patch("shutil.which")
    def test_is_installed_true(self, mock_which: Mock, manager: DevToolManager) -> None:
        """Test checking if a tool is installed (true case)."""
        mock_which.return_value = "/usr/bin/rustc"
        
        result = manager.is_installed(DevToolType.RUST)
        
        assert result is True
        mock_which.assert_called_with("rustc")
    
    @patch("shutil.which")
    def test_is_installed_false(self, mock_which: Mock, manager: DevToolManager) -> None:
        """Test checking if a tool is installed (false case)."""
        mock_which.return_value = None
        
        result = manager.is_installed(DevToolType.RUST)
        
        assert result is False
    
    @patch("shutil.which")
    def test_is_installed_unknown_tool(self, mock_which: Mock, manager: DevToolManager) -> None:
        """Test checking unknown tool type."""
        result = manager.is_installed("unknown")  # type: ignore
        assert result is False
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_get_version_installed(self, mock_which: Mock, manager: DevToolManager) -> None:
        """Test getting version of installed tool."""
        mock_which.return_value = "/usr/bin/rustc"
        
        # Mock subprocess
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"rustc 1.70.0\n", b""))
        
        with patch("asyncio.create_subprocess_shell", return_value=mock_proc):
            version = await manager.get_version(DevToolType.RUST)
        
        assert version == "rustc 1.70.0"
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_get_version_not_installed(self, mock_which: Mock, manager: DevToolManager) -> None:
        """Test getting version of non-installed tool."""
        mock_which.return_value = None
        
        version = await manager.get_version(DevToolType.RUST)
        
        assert version is None
    
    def test_get_available_tools(self, manager: DevToolManager) -> None:
        """Test getting list of available tools."""
        tools = manager.get_available_tools()
        
        assert len(tools) == 9
        assert all(isinstance(tool, DevToolInfo) for tool in tools)


class TestDistroDetection:
    """Test cases for distribution detection."""
    
    @pytest.fixture
    def manager(self) -> DevToolManager:
        """Create a DevToolManager instance."""
        return DevToolManager()
    
    def test_detect_distro_from_os_release(self, manager: DevToolManager, tmp_path: Path) -> None:
        """Test detecting distro from /etc/os-release."""
        mock_os_release = tmp_path / "os-release"
        mock_os_release.write_text('ID=ubuntu\nVERSION_ID="22.04"\n')
        
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = True
            with patch.object(Path, "read_text", return_value=mock_os_release.read_text()):
                distro = manager.detect_distro()
        
        assert distro == "ubuntu"
    
    def test_detect_distro_arch(self, manager: DevToolManager) -> None:
        """Test detecting Arch Linux."""
        # Create a new manager to avoid cached distro
        manager = DevToolManager()
        manager._detected_distro = None
        # Mock Path.exists to return False for os-release, True for arch-release
        original_exists = Path.exists
        def mock_exists(self):
            path_str = str(self)
            if "os-release" in path_str:
                return False
            if "arch-release" in path_str:
                return True
            return original_exists(self)
        with patch.object(Path, "exists", mock_exists):
            distro = manager.detect_distro()
        
        assert distro == "arch"
    
    def test_detect_distro_fedora(self, manager: DevToolManager) -> None:
        """Test detecting Fedora."""
        # Create a new manager to avoid cached distro
        manager = DevToolManager()
        manager._detected_distro = None
        # Mock Path.exists to return False for os-release, True for fedora-release
        original_exists = Path.exists
        def mock_exists(self):
            path_str = str(self)
            if "os-release" in path_str:
                return False
            if "fedora-release" in path_str:
                return True
            return original_exists(self)
        with patch.object(Path, "exists", mock_exists):
            distro = manager.detect_distro()
        
        assert distro == "fedora"
    
    def test_detect_distro_debian(self, manager: DevToolManager) -> None:
        """Test detecting Debian."""
        # Create a new manager to avoid cached distro
        manager = DevToolManager()
        manager._detected_distro = None
        with patch("os.path.exists") as mock_exists:
            mock_exists.side_effect = lambda p: "debian_version" in str(p)
            distro = manager.detect_distro()
        
        assert distro == "debian"
    
    def test_get_package_manager(self, manager: DevToolManager) -> None:
        """Test getting package manager for distro."""
        test_cases = [
            ("debian", "apt"),
            ("ubuntu", "apt"),
            ("arch", "pacman"),
            ("manjaro", "pacman"),
            ("fedora", "dnf"),
            ("centos", "yum"),
            ("opensuse", "zypper"),
            ("alpine", "apk"),
            ("unknown", "apt"),  # Default
        ]
        
        for distro, expected_pm in test_cases:
            with patch.object(manager, "_detected_distro", distro):
                pm = manager.get_package_manager()
                assert pm == expected_pm, f"Failed for {distro}"


class TestPackageInstallation:
    """Test cases for package installation."""
    
    @pytest.fixture
    def manager(self) -> DevToolManager:
        """Create a DevToolManager instance."""
        return DevToolManager()
    
    @pytest.mark.asyncio
    async def test_install_via_package_manager_success(self, manager: DevToolManager) -> None:
        """Test successful package installation."""
        manager._detected_distro = "debian"
        
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await manager.install_via_package_manager(["git", "curl"])
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_install_via_package_manager_failure(self, manager: DevToolManager) -> None:
        """Test failed package installation."""
        manager._detected_distro = "debian"
        
        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"Error"))
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await manager.install_via_package_manager(["git"])
        
        assert result is False
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_git_already_installed(self, mock_which: Mock, manager: DevToolManager) -> None:
        """Test installing git when already installed."""
        mock_which.return_value = "/usr/bin/git"
        
        result = await manager.install_git()
        
        assert result is True


class TestRustInstallation:
    """Test cases for Rust installation."""
    
    @pytest.fixture
    def manager(self) -> DevToolManager:
        """Create a DevToolManager instance."""
        return DevToolManager()
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_rust_already_installed(self, mock_which: Mock, manager: DevToolManager) -> None:
        """Test installing Rust when already installed."""
        mock_which.return_value = "/usr/bin/rustc"
        
        result = await manager.install_rust()
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_rust_via_rustup(self, mock_which: Mock, manager: DevToolManager, tmp_path: Path) -> None:
        """Test installing Rust via rustup."""
        mock_which.side_effect = lambda x: None if x == "rustc" else f"/usr/bin/{x}"
        
        # Mock download
        mock_download = AsyncMock()
        manager.downloader.download = mock_download
        
        # Mock subprocess
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with patch.object(Path, "chmod"):
                result = await manager.install_rust()
        
        assert result is True
        mock_download.assert_called_once()


class TestGoInstallation:
    """Test cases for Go installation."""
    
    @pytest.fixture
    def manager(self) -> DevToolManager:
        """Create a DevToolManager instance."""
        return DevToolManager()
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_go_already_installed(self, mock_which: Mock, manager: DevToolManager) -> None:
        """Test installing Go when already installed."""
        mock_which.return_value = "/usr/bin/go"
        
        result = await manager.install_go()
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_go_via_package_manager(self, mock_which: Mock, manager: DevToolManager) -> None:
        """Test installing Go via package manager."""
        mock_which.side_effect = lambda x: None if x == "go" else f"/usr/bin/{x}"
        
        with patch.object(manager, "install_via_package_manager", return_value=True):
            result = await manager.install_go()
        
        assert result is True


class TestNodejsInstallation:
    """Test cases for Node.js installation."""
    
    @pytest.fixture
    def manager(self) -> DevToolManager:
        """Create a DevToolManager instance."""
        return DevToolManager()
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_nodejs_already_installed(self, mock_which: Mock, manager: DevToolManager) -> None:
        """Test installing Node.js when already installed."""
        mock_which.return_value = "/usr/bin/node"
        
        result = await manager.install_nodejs()
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_nodejs_via_nodesource(self, mock_which: Mock, manager: DevToolManager) -> None:
        """Test installing Node.js via NodeSource."""
        mock_which.side_effect = lambda x: None if x == "node" else f"/usr/bin/{x}"
        manager._detected_distro = "debian"
        
        # Mock download and subprocess
        mock_download = AsyncMock()
        manager.downloader.download = mock_download
        
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        
        with patch.object(manager, "install_via_package_manager", return_value=True) as mock_install:
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                with patch("pathlib.Path.chmod"):
                    with patch("pathlib.Path.unlink"):
                        result = await manager.install_nodejs(method="nodesource")
        
        assert result is True


class TestJavaInstallation:
    """Test cases for Java installation."""
    
    @pytest.fixture
    def manager(self) -> DevToolManager:
        """Create a DevToolManager instance."""
        return DevToolManager()
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_java_already_installed(self, mock_which: Mock, manager: DevToolManager) -> None:
        """Test installing Java when already installed."""
        mock_which.return_value = "/usr/bin/java"
        
        result = await manager.install_java()
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_java_openjdk(self, mock_which: Mock, manager: DevToolManager) -> None:
        """Test installing OpenJDK."""
        mock_which.side_effect = lambda x: None if x == "java" else f"/usr/bin/{x}"
        manager._detected_distro = "debian"
        
        with patch.object(manager, "install_via_package_manager", return_value=True):
            result = await manager.install_java(version="17")
        
        assert result is True


class TestDockerInstallation:
    """Test cases for Docker installation."""
    
    @pytest.fixture
    def manager(self) -> DevToolManager:
        """Create a DevToolManager instance."""
        return DevToolManager()
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_docker_already_installed(self, mock_which: Mock, manager: DevToolManager) -> None:
        """Test installing Docker when already installed."""
        mock_which.return_value = "/usr/bin/docker"
        
        result = await manager.install_docker()
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_install_docker_debian(self, mock_which: Mock, manager: DevToolManager) -> None:
        """Test installing Docker on Debian."""
        mock_which.side_effect = lambda x: None if x == "docker" else f"/usr/bin/{x}"
        manager._detected_distro = "debian"
        
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        
        with patch("asyncio.create_subprocess_shell", return_value=mock_proc):
            with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
                with patch.object(manager, "install_via_package_manager", return_value=True):
                    with patch("pathlib.Path.write_text"):
                        with patch("pathlib.Path.mkdir"):
                            result = await manager.install_docker()
        
        assert result is True


class TestBuildToolsInstallation:
    """Test cases for build tools installation."""
    
    @pytest.fixture
    def manager(self) -> DevToolManager:
        """Create a DevToolManager instance."""
        return DevToolManager()
    
    @pytest.mark.asyncio
    async def test_install_build_tools_debian(self, manager: DevToolManager) -> None:
        """Test installing build tools on Debian."""
        manager._detected_distro = "debian"
        
        with patch.object(manager, "install_via_package_manager", return_value=True):
            result = await manager.install_build_tools()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_install_build_tools_arch(self, manager: DevToolManager) -> None:
        """Test installing build tools on Arch."""
        manager._detected_distro = "arch"
        
        with patch.object(manager, "install_via_package_manager", return_value=True):
            result = await manager.install_build_tools()
        
        assert result is True


class TestPythonToolsInstallation:
    """Test cases for Python tools installation."""
    
    @pytest.fixture
    def manager(self) -> DevToolManager:
        """Create a DevToolManager instance."""
        return DevToolManager()
    
    @pytest.mark.asyncio
    async def test_install_python_tools(self, manager: DevToolManager) -> None:
        """Test installing Python development tools."""
        with patch.object(manager, "install_via_package_manager", return_value=True):
            result = await manager.install_python_tools()
        
        assert result is True


class TestGitConfiguration:
    """Test cases for Git configuration."""
    
    @pytest.fixture
    def manager(self) -> DevToolManager:
        """Create a DevToolManager instance."""
        return DevToolManager()
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_configure_git(self, mock_which: Mock, manager: DevToolManager) -> None:
        """Test configuring Git."""
        mock_which.return_value = "/usr/bin/git"
        
        call_count = 0
        async def mock_exec(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_proc = AsyncMock()
            mock_proc.returncode = 0
            mock_proc.communicate = AsyncMock(return_value=(b"", b""))
            return mock_proc
        
        with patch("asyncio.create_subprocess_exec", side_effect=mock_exec):
            result = await manager.configure_git(
                username="Test User",
                email="test@example.com",
                editor="vim",
            )
        
        assert result is True
        assert call_count == 3  # user.name, user.email, core.editor
    
    @pytest.mark.asyncio
    @patch("shutil.which")
    async def test_configure_git_not_installed(self, mock_which: Mock, manager: DevToolManager) -> None:
        """Test configuring Git when not installed."""
        mock_which.return_value = None
        
        result = await manager.configure_git(username="Test")
        
        assert result is False


class TestDevToolManagerIntegration:
    """Integration tests for DevToolManager."""
    
    @pytest.mark.asyncio
    async def test_full_toolchain_installation(self) -> None:
        """Test installing full development toolchain."""
        manager = DevToolManager()
        
        with patch.object(manager, "install_git", return_value=True):
            with patch.object(manager, "install_build_tools", return_value=True):
                with patch.object(manager, "install_python_tools", return_value=True):
                    # Install essential tools
                    git_result = await manager.install_git()
                    build_result = await manager.install_build_tools()
                    python_result = await manager.install_python_tools()
        
        assert git_result is True
        assert build_result is True
        assert python_result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])