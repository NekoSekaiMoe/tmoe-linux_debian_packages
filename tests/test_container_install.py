"""Tests for container installation module.

This module tests the ContainerInstaller class and related functionality
for downloading and installing container rootfs.
"""

from __future__ import annotations

import asyncio
import lzma
import tarfile
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from tmoe.container.install import (
    ContainerInstaller,
    InstallOptions,
    InstallResult,
    RootfsSource,
)
from tmoe.core.config import ContainerConfig
from tmoe.core.constants import ContainerType


class TestInstallOptions:
    """Test cases for InstallOptions dataclass."""
    
    def test_default_options(self) -> None:
        """Test default installation options."""
        options = InstallOptions()
        
        assert options.source == RootfsSource.LXC
        assert options.custom_url is None
        assert options.dns_servers == [
            "8.8.8.8", "8.8.4.4",
            "2001:4860:4860::8888", "2001:4860:4860::8844",
        ]
        assert options.setup_user is True
        assert options.install_base_packages is False
        assert options.configure_mirror is False
        assert options.mirror_region == "global"
        assert options.run_init_scripts is False
        assert options.init_scripts == []
    
    def test_custom_options(self) -> None:
        """Test custom installation options."""
        options = InstallOptions(
            source=RootfsSource.CUSTOM,
            custom_url="https://example.com/rootfs.tar.xz",
            dns_servers=["1.1.1.1", "1.0.0.1"],
            setup_user=False,
            configure_mirror=True,
            mirror_region="china",
        )
        
        assert options.source == RootfsSource.CUSTOM
        assert options.custom_url == "https://example.com/rootfs.tar.xz"
        assert options.dns_servers == ["1.1.1.1", "1.0.0.1"]
        assert options.setup_user is False
        assert options.configure_mirror is True
        assert options.mirror_region == "china"


class TestInstallResult:
    """Test cases for InstallResult dataclass."""
    
    def test_success_result(self) -> None:
        """Test successful installation result."""
        result = InstallResult(
            success=True,
            message="Container installed successfully",
            rootfs_path=Path("/tmp/test"),
            download_time=10.5,
            extract_time=5.2,
            setup_time=2.1,
        )
        
        assert result.success is True
        assert result.message == "Container installed successfully"
        assert result.rootfs_path == Path("/tmp/test")
        assert result.download_time == 10.5
        assert result.extract_time == 5.2
        assert result.setup_time == 2.1
    
    def test_failure_result(self) -> None:
        """Test failed installation result."""
        result = InstallResult(
            success=False,
            message="Installation failed: Network error",
        )
        
        assert result.success is False
        assert "Network error" in result.message
        assert result.rootfs_path is None


class TestContainerInstallerInitialization:
    """Test cases for ContainerInstaller initialization."""
    
    def test_default_initialization(self) -> None:
        """Test default initialization."""
        installer = ContainerInstaller()
        
        assert installer.platform is not None
        assert installer.downloader is not None
        assert installer._progress_callback is None
    
    def test_set_progress_callback(self) -> None:
        """Test setting progress callback."""
        installer = ContainerInstaller()
        callback = Mock()
        
        installer.set_progress_callback(callback)
        
        assert installer._progress_callback == callback
    
    def test_report_progress(self) -> None:
        """Test progress reporting."""
        installer = ContainerInstaller()
        callback = Mock()
        installer.set_progress_callback(callback)
        
        installer._report_progress("Downloading...", 50, 100)
        
        callback.assert_called_once_with("Downloading...", 50, 100)


class TestConfigValidation:
    """Test cases for configuration validation."""
    
    @pytest.fixture
    def installer(self) -> ContainerInstaller:
        """Create a ContainerInstaller instance."""
        return ContainerInstaller()
    
    def test_valid_config(self, installer: ContainerInstaller) -> None:
        """Test valid configuration."""
        config = ContainerConfig(
            name="test-container",
            distro="debian",
            arch="arm64",
            container_type=ContainerType.PROOT,
        )
        
        assert installer._validate_config(config) is True
    
    def test_invalid_config_no_name(self, installer: ContainerInstaller) -> None:
        """Test invalid configuration (no name)."""
        config = ContainerConfig(
            name="",
            distro="debian",
            arch="arm64",
            container_type=ContainerType.PROOT,
        )
        
        assert installer._validate_config(config) is False
    
    def test_invalid_config_no_distro(self, installer: ContainerInstaller) -> None:
        """Test invalid configuration (no distro)."""
        config = ContainerConfig(
            name="test",
            distro="",
            arch="arm64",
            container_type=ContainerType.PROOT,
        )
        
        assert installer._validate_config(config) is False
    
    def test_invalid_config_no_arch(self, installer: ContainerInstaller) -> None:
        """Test invalid configuration (no arch)."""
        # ContainerConfig validates arch in __post_init__, so we can't create with empty arch
        # Instead test that the installer rejects it
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="arm64",  # Use valid arch
            container_type=ContainerType.PROOT,
        )
        # Manually clear arch to test validation
        object.__setattr__(config, "arch", "")
        
        assert installer._validate_config(config) is False
    
    def test_invalid_config_unknown_arch(self, installer: ContainerInstaller) -> None:
        """Test invalid configuration (unknown arch)."""
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="arm64",  # Use valid arch first
            container_type=ContainerType.PROOT,
        )
        # Manually set unknown arch to test validation
        object.__setattr__(config, "arch", "unknown-arch")
        
        assert installer._validate_config(config) is False


class TestURLBuilding:
    """Test cases for URL building."""
    
    @pytest.fixture
    def installer(self) -> ContainerInstaller:
        """Create a ContainerInstaller instance."""
        return ContainerInstaller()
    
    def test_build_lxc_url(self, installer: ContainerInstaller) -> None:
        """Test building LXC URL."""
        url = installer._build_lxc_url("debian", "bookworm", "arm64")
        
        assert "images.linuxcontainers.org" in url
        assert "debian/bookworm/arm64" in url
        assert "rootfs.tar.xz" in url
    
    def test_build_lxc_url_arch_mapping(self, installer: ContainerInstaller) -> None:
        """Test LXC URL with architecture mapping."""
        url = installer._build_lxc_url("ubuntu", "jammy", "amd64")
        
        assert "amd64" in url
    
    def test_build_tmoe_url(self, installer: ContainerInstaller) -> None:
        """Test building TMOE URL."""
        url = installer._build_tmoe_url("debian", "bookworm", "arm64")
        
        assert "cdn.tmoe.me" in url
        assert "debian/bookworm/arm64" in url
        assert "rootfs.tar.xz" in url


class TestContainerInstallation:
    """Test cases for container installation."""
    
    @pytest.fixture
    def installer(self) -> ContainerInstaller:
        """Create a ContainerInstaller instance."""
        return ContainerInstaller()
    
    @pytest.fixture
    def sample_config(self, tmp_path: Path) -> ContainerConfig:
        """Create a sample container configuration."""
        return ContainerConfig(
            name="test-container",
            distro="debian",
            arch="arm64",
            container_type=ContainerType.PROOT,
            rootfs_path=tmp_path / "test-container",
        )
    
    @pytest.mark.asyncio
    async def test_install_invalid_config(self, installer: ContainerInstaller) -> None:
        """Test installation with invalid config."""
        config = ContainerConfig(
            name="",
            distro="debian",
            arch="arm64",
            container_type=ContainerType.PROOT,
        )
        
        result = await installer.install(config)
        
        assert result.success is False
        assert "Invalid" in result.message
    
    @pytest.mark.asyncio
    async def test_install_no_rootfs_path(self, installer: ContainerInstaller) -> None:
        """Test installation without rootfs path."""
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="arm64",
            container_type=ContainerType.PROOT,
            rootfs_path=None,
        )
        
        result = await installer.install(config)
        
        assert result.success is False
        assert "rootfs path not set" in result.message
    
    @pytest.mark.asyncio
    async def test_install_existing_container(
        self,
        installer: ContainerInstaller,
        sample_config: ContainerConfig,
    ) -> None:
        """Test installation when container already exists."""
        # Create existing container directory with content
        sample_config.rootfs_path.mkdir(parents=True, exist_ok=True)
        (sample_config.rootfs_path / "existing_file").write_text("content")
        
        result = await installer.install(sample_config)
        
        assert result.success is False
        assert "already exists" in result.message
    
    @pytest.mark.asyncio
    async def test_install_proot_success(
        self,
        installer: ContainerInstaller,
        sample_config: ContainerConfig,
        tmp_path: Path,
    ) -> None:
        """Test successful proot installation."""
        options = InstallOptions(source=RootfsSource.LXC)
        
        # Mock download and extract
        async def mock_download_and_extract(url: str, dest: Path) -> None:
            # Create a minimal rootfs structure
            (dest / "etc").mkdir(parents=True)
            (dest / "etc" / "passwd").write_text("root:x:0:0:root:/root:/bin/bash\n")
            (dest / "etc" / "group").write_text("root:x:0:\n")
            (dest / "bin").mkdir()
            (dest / "bin" / "sh").write_text("#!/bin/sh\n")
        
        installer._download_and_extract = mock_download_and_extract
        
        result = await installer.install_proot(sample_config, options)
        
        assert result.success is True
        assert result.rootfs_path == sample_config.rootfs_path
    
    @pytest.mark.asyncio
    async def test_install_chroot_requires_root(
        self,
        installer: ContainerInstaller,
        sample_config: ContainerConfig,
    ) -> None:
        """Test chroot installation requires root."""
        sample_config.container_type = ContainerType.CHROOT
        
        with patch("os.geteuid", return_value=1000):
            result = await installer.install_chroot(sample_config)
        
        assert result.success is False
        assert "requires root" in result.message


class TestDNSSetup:
    """Test cases for DNS setup."""
    
    @pytest.fixture
    def installer(self) -> ContainerInstaller:
        """Create a ContainerInstaller instance."""
        return ContainerInstaller()
    
    @pytest.mark.asyncio
    async def test_setup_dns(self, installer: ContainerInstaller, tmp_path: Path) -> None:
        """Test DNS configuration setup."""
        rootfs_path = tmp_path / "rootfs"
        options = InstallOptions(
            dns_servers=["1.1.1.1", "8.8.8.8"],
        )
        
        await installer._setup_dns(rootfs_path, options)
        
        resolv_conf = rootfs_path / "etc" / "resolv.conf"
        assert resolv_conf.exists()
        content = resolv_conf.read_text()
        assert "nameserver 1.1.1.1" in content
        assert "nameserver 8.8.8.8" in content


class TestUserSetup:
    """Test cases for user setup."""
    
    @pytest.fixture
    def installer(self) -> ContainerInstaller:
        """Create a ContainerInstaller instance."""
        return ContainerInstaller()
    
    @pytest.mark.asyncio
    async def test_setup_users_root_only(self, installer: ContainerInstaller, tmp_path: Path) -> None:
        """Test user setup with root only."""
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="arm64",
            container_type=ContainerType.PROOT,
            user="root",
        )
        rootfs_path = tmp_path / "rootfs"
        
        # Should not create any users
        await installer._setup_users(config, rootfs_path)
        
        # No assertions needed - just shouldn't raise
    
    @pytest.mark.asyncio
    async def test_setup_users_non_root(self, installer: ContainerInstaller, tmp_path: Path) -> None:
        """Test user setup with non-root user."""
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="arm64",
            container_type=ContainerType.PROOT,
            user="testuser",
            uid=1000,
            gid=1000,
            home="/home/testuser",
        )
        rootfs_path = tmp_path / "rootfs"
        (rootfs_path / "etc").mkdir(parents=True)
        (rootfs_path / "etc" / "passwd").write_text("root:x:0:0:root:/root:/bin/bash\n")
        (rootfs_path / "etc" / "group").write_text("root:x:0:\n")
        
        await installer._setup_users(config, rootfs_path)
        
        # Check passwd file
        passwd_content = (rootfs_path / "etc" / "passwd").read_text()
        assert "testuser:x:1000:1000" in passwd_content
        
        # Check group file
        group_content = (rootfs_path / "etc" / "group").read_text()
        assert "testuser:x:1000:" in group_content
        
        # Check home directory
        assert (rootfs_path / "home" / "testuser").exists()


class TestTmoeEnvironment:
    """Test cases for TMOE environment setup."""
    
    @pytest.fixture
    def installer(self) -> ContainerInstaller:
        """Create a ContainerInstaller instance."""
        return ContainerInstaller()
    
    @pytest.mark.asyncio
    async def test_setup_tmoe_env_proot(self, installer: ContainerInstaller, tmp_path: Path) -> None:
        """Test TMOE environment setup for proot."""
        config = ContainerConfig(
            name="test-container",
            distro="debian",
            arch="arm64",
            container_type=ContainerType.PROOT,
            codename="bookworm",
            user="testuser",
            home="/home/testuser",
            uid=1000,
            gid=1000,
        )
        rootfs_path = tmp_path / "rootfs"
        
        await installer._setup_tmoe_env(config, rootfs_path)
        
        # Check environment file
        env_file = rootfs_path / "usr" / "local" / "etc" / "tmoe-linux" / "environment" / "container.env"
        assert env_file.exists()
        content = env_file.read_text()
        assert 'TMOE_CONTAINER_NAME="test-container"' in content
        assert 'TMOE_PROOT="true"' in content
        assert 'TMOE_CHROOT="false"' in content
        
        # Check profile.d entry
        profile_file = rootfs_path / "etc" / "profile.d" / "000_tmoe_env.sh"
        assert profile_file.exists()
        
        # Check configure file
        configure_file = rootfs_path / "usr" / "local" / "etc" / "tmoe-linux" / ".tmoe-rootfs-configure"
        assert configure_file.exists()


class TestRootfsExtraction:
    """Test cases for rootfs extraction."""
    
    @pytest.fixture
    def installer(self) -> ContainerInstaller:
        """Create a ContainerInstaller instance."""
        return ContainerInstaller()
    
    def create_test_tarball(self) -> BytesIO:
        """Create a test tarball."""
        buffer = BytesIO()
        
        # Create tar.xz file
        with lzma.open(buffer, "w") as xz_file:
            with tarfile.open(fileobj=xz_file, mode="w") as tar:
                # Add some test files
                data = b"root:x:0:0:root:/root:/bin/bash\n"
                info = tarfile.TarInfo(name="etc/passwd")
                info.size = len(data)
                tar.addfile(info, BytesIO(data))
        
        buffer.seek(0)
        return buffer
    
    def test_extract_sync(self, installer: ContainerInstaller, tmp_path: Path) -> None:
        """Test synchronous extraction."""
        tar_path = tmp_path / "rootfs.tar.xz"
        dest_path = tmp_path / "rootfs"
        
        # Create test tarball
        buffer = self.create_test_tarball()
        tar_path.write_bytes(buffer.read())
        
        installer._extract_sync(tar_path, dest_path)
        
        assert (dest_path / "etc" / "passwd").exists()


class TestInstallationVerification:
    """Test cases for installation verification."""
    
    @pytest.fixture
    def installer(self) -> ContainerInstaller:
        """Create a ContainerInstaller instance."""
        return ContainerInstaller()
    
    @pytest.mark.asyncio
    async def test_verify_installation_valid(self, installer: ContainerInstaller, tmp_path: Path) -> None:
        """Test verification of valid installation."""
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="arm64",
            container_type=ContainerType.PROOT,
            rootfs_path=tmp_path / "rootfs",
        )
        
        # Create valid rootfs structure
        (config.rootfs_path / "etc").mkdir(parents=True)
        (config.rootfs_path / "etc" / "passwd").write_text("root:x:0:0:root:/root:/bin/bash\n")
        (config.rootfs_path / "etc" / "group").write_text("root:x:0:\n")
        (config.rootfs_path / "bin").mkdir()
        (config.rootfs_path / "bin" / "sh").write_text("#!/bin/sh\n")
        
        env_dir = config.rootfs_path / "usr" / "local" / "etc" / "tmoe-linux" / "environment"
        env_dir.mkdir(parents=True)
        (env_dir / "container.env").write_text("TMOE_CONTAINER_NAME=test\n")
        
        result = await installer.verify_installation(config)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_installation_invalid(self, installer: ContainerInstaller, tmp_path: Path) -> None:
        """Test verification of invalid installation."""
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="arm64",
            container_type=ContainerType.PROOT,
            rootfs_path=tmp_path / "rootfs",
        )
        
        # Create incomplete rootfs structure
        config.rootfs_path.mkdir(parents=True)
        
        result = await installer.verify_installation(config)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_installation_no_rootfs(self, installer: ContainerInstaller) -> None:
        """Test verification with no rootfs path."""
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="arm64",
            container_type=ContainerType.PROOT,
            rootfs_path=None,
        )
        
        result = await installer.verify_installation(config)
        
        assert result is False


class TestSizeFormatting:
    """Test cases for size formatting."""
    
    @pytest.fixture
    def installer(self) -> ContainerInstaller:
        """Create a ContainerInstaller instance."""
        return ContainerInstaller()
    
    def test_format_size_bytes(self, installer: ContainerInstaller) -> None:
        """Test formatting bytes."""
        result = installer.format_size(500)
        assert "B" in result
    
    def test_format_size_kilobytes(self, installer: ContainerInstaller) -> None:
        """Test formatting kilobytes."""
        result = installer.format_size(1024 * 500)
        assert "KB" in result
    
    def test_format_size_megabytes(self, installer: ContainerInstaller) -> None:
        """Test formatting megabytes."""
        result = installer.format_size(1024 * 1024 * 500)
        assert "MB" in result
    
    def test_format_size_gigabytes(self, installer: ContainerInstaller) -> None:
        """Test formatting gigabytes."""
        result = installer.format_size(1024 * 1024 * 1024 * 2)
        assert "GB" in result
    
    def test_get_install_size(self, installer: ContainerInstaller, tmp_path: Path) -> None:
        """Test getting installation size."""
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="arm64",
            container_type=ContainerType.PROOT,
            rootfs_path=tmp_path / "rootfs",
        )
        
        # Create some files
        config.rootfs_path.mkdir(parents=True)
        (config.rootfs_path / "file1").write_text("Hello World!")
        (config.rootfs_path / "file2").write_text("More content here")
        
        size = installer.get_install_size(config)
        
        assert size > 0
        assert size == len("Hello World!") + len("More content here")
    
    def test_get_install_size_no_rootfs(self, installer: ContainerInstaller) -> None:
        """Test getting size with no rootfs."""
        config = ContainerConfig(
            name="test",
            distro="debian",
            arch="arm64",
            container_type=ContainerType.PROOT,
            rootfs_path=None,
        )
        
        size = installer.get_install_size(config)
        
        assert size == 0


class TestContainerInstallerIntegration:
    """Integration tests for ContainerInstaller."""
    
    @pytest.mark.asyncio
    async def test_full_installation_flow(self, tmp_path: Path) -> None:
        """Test full installation flow."""
        installer = ContainerInstaller()
        
        config = ContainerConfig(
            name="integration-test",
            distro="debian",
            arch="arm64",
            container_type=ContainerType.PROOT,
            rootfs_path=tmp_path / "integration-test",
        )
        
        options = InstallOptions(
            source=RootfsSource.LXC,
            setup_user=True,
        )
        
        # Mock the download and extract
        async def mock_download_and_extract(url: str, dest: Path) -> None:
            # Create minimal rootfs
            (dest / "etc").mkdir(parents=True)
            (dest / "etc" / "passwd").write_text("root:x:0:0:root:/root:/bin/bash\n")
            (dest / "etc" / "group").write_text("root:x:0:\n")
            (dest / "bin").mkdir()
            (dest / "bin" / "sh").write_text("#!/bin/sh\n")
        
        installer._download_and_extract = mock_download_and_extract
        
        result = await installer.install(config, options)
        
        assert result.success is True
        assert result.rootfs_path == config.rootfs_path
        
        # Verify installation
        verify_result = await installer.verify_installation(config)
        assert verify_result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
