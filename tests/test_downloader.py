"""Tests for download management module.

This module tests the DownloadManager class and related functionality
for downloading files using various backends.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from tmoe.tools.downloader import (
    Aria2Config,
    DownloadBackend,
    DownloadManager,
    DownloadTask,
)


class TestDownloadTask:
    """Test cases for DownloadTask dataclass."""
    
    def test_default_creation(self) -> None:
        """Test creating a download task with defaults."""
        task = DownloadTask(
            url="https://example.com/file.zip",
            dest=Path("/tmp/file.zip"),
        )
        
        assert task.url == "https://example.com/file.zip"
        assert task.dest == Path("/tmp/file.zip")
        assert task.backend == DownloadBackend.ARIA2
        assert task.headers == {}
        assert task.cookies == {}
        assert task.concurrent == 4
        assert task.max_speed is None
        assert task.resume is True
    
    def test_custom_creation(self) -> None:
        """Test creating a download task with custom values."""
        task = DownloadTask(
            url="https://example.com/file.zip",
            dest=Path("/tmp/file.zip"),
            backend=DownloadBackend.CURL,
            headers={"Authorization": "Bearer token"},
            concurrent=8,
            max_speed="1M",
            resume=False,
        )
        
        assert task.backend == DownloadBackend.CURL
        assert task.headers == {"Authorization": "Bearer token"}
        assert task.concurrent == 8
        assert task.max_speed == "1M"
        assert task.resume is False


class TestAria2Config:
    """Test cases for Aria2Config dataclass."""
    
    def test_default_config(self) -> None:
        """Test default aria2 configuration."""
        config = Aria2Config()
        
        assert config.enabled is False
        assert config.rpc_port == 6800
        assert config.rpc_secret == "tmoe"
        assert config.max_connections == 16
        assert config.split == 16
        assert config.min_split_size == "1M"
        assert config.dir == Path.home() / "Downloads"
        assert config.config_file == Path("/usr/local/etc/tmoe-linux/aria2/aria2.conf")
    
    def test_custom_config(self) -> None:
        """Test custom aria2 configuration."""
        config = Aria2Config(
            enabled=True,
            rpc_port=8080,
            rpc_secret="secret123",
            max_connections=32,
        )
        
        assert config.enabled is True
        assert config.rpc_port == 8080
        assert config.rpc_secret == "secret123"
        assert config.max_connections == 32


class TestDownloadManager:
    """Test cases for DownloadManager class."""
    
    @pytest.fixture
    def manager(self) -> DownloadManager:
        """Create a DownloadManager instance for testing."""
        return DownloadManager()
    
    def test_initialization(self, manager: DownloadManager) -> None:
        """Test DownloadManager initialization."""
        assert manager._progress_callback is None
        assert manager._aria2_config is None
        assert manager.platform is not None
    
    def test_set_progress_callback(self, manager: DownloadManager) -> None:
        """Test setting progress callback."""
        callback = Mock()
        manager.set_progress_callback(callback)
        
        assert manager._progress_callback == callback
    
    def test_report_progress(self, manager: DownloadManager) -> None:
        """Test progress reporting."""
        callback = Mock()
        manager.set_progress_callback(callback)
        
        manager._report_progress("Downloading...", 50, 100)
        
        callback.assert_called_once_with("Downloading...", 50, 100)
    
    def test_report_progress_no_callback(self, manager: DownloadManager) -> None:
        """Test progress reporting without callback."""
        # Should not raise any errors
        manager._report_progress("Downloading...", 50, 100)
    
    @patch("shutil.which")
    def test_detect_backends_all_available(self, mock_which: Mock) -> None:
        """Test detecting backends when all are available."""
        mock_which.side_effect = lambda x: f"/usr/bin/{x}"
        
        manager = DownloadManager()
        backends = manager.detect_backends()
        
        assert DownloadBackend.ARIA2 in backends
        assert DownloadBackend.CURL in backends
        assert DownloadBackend.WGET in backends
        assert DownloadBackend.HTTpx in backends
    
    @patch("shutil.which")
    def test_detect_backends_none_available(self, mock_which: Mock) -> None:
        """Test detecting backends when none are available."""
        mock_which.return_value = None
        
        manager = DownloadManager()
        backends = manager.detect_backends()
        
        assert DownloadBackend.ARIA2 not in backends
        assert DownloadBackend.CURL not in backends
        assert DownloadBackend.WGET not in backends
        assert DownloadBackend.HTTpx in backends  # httpx is always available
    
    @patch("shutil.which")
    def test_get_best_backend(self, mock_which: Mock) -> None:
        """Test getting best available backend."""
        mock_which.side_effect = lambda x: f"/usr/bin/{x}" if x == "aria2c" else None
        
        manager = DownloadManager()
        best = manager.get_best_backend()
        
        assert best == DownloadBackend.ARIA2
    
    @patch("shutil.which")
    def test_get_best_backend_fallback(self, mock_which: Mock) -> None:
        """Test getting best backend falls back to httpx."""
        mock_which.return_value = None
        
        manager = DownloadManager()
        best = manager.get_best_backend()
        
        assert best == DownloadBackend.HTTpx


class TestDownloadManagerAsync:
    """Async test cases for DownloadManager."""
    
    @pytest.fixture
    def manager(self) -> DownloadManager:
        """Create a DownloadManager instance."""
        return DownloadManager()
    
    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Path:
        """Create a temporary directory."""
        return tmp_path
    
    @pytest.mark.asyncio
    async def test_download_with_httpx(self, manager: DownloadManager, temp_dir: Path) -> None:
        """Test downloading with httpx backend."""
        # Create a simple test server response mock
        task = DownloadTask(
            url="https://example.com/test.txt",
            dest=temp_dir / "test.txt",
            backend=DownloadBackend.HTTpx,
        )
        
        # Create a proper async iterator for chunks
        async def async_chunks(chunk_size=8192):
            yield b"Hello World!"
        
        # Mock httpx client - properly set up async context manager
        mock_response = MagicMock()
        mock_response.headers = {"content-length": "12"}
        mock_response.aiter_bytes = async_chunks
        mock_response.raise_for_status = Mock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_client = MagicMock()
        mock_client.stream = MagicMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await manager.download(task, backend=DownloadBackend.HTTpx)
        
        assert result == task.dest
        assert result.exists()
        assert result.read_text() == "Hello World!"
    
    @pytest.mark.asyncio
    async def test_download_with_curl(self, manager: DownloadManager, temp_dir: Path) -> None:
        """Test downloading with curl backend."""
        task = DownloadTask(
            url="https://example.com/test.txt",
            dest=temp_dir / "test.txt",
            backend=DownloadBackend.CURL,
        )
        
        # Mock subprocess
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await manager._download_curl(task)
        
        assert result == task.dest
    
    @pytest.mark.asyncio
    async def test_download_with_wget(self, manager: DownloadManager, temp_dir: Path) -> None:
        """Test downloading with wget backend."""
        task = DownloadTask(
            url="https://example.com/test.txt",
            dest=temp_dir / "test.txt",
            backend=DownloadBackend.WGET,
        )
        
        # Mock subprocess
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await manager._download_wget(task)
        
        assert result == task.dest
    
    @pytest.mark.asyncio
    async def test_download_with_aria2(self, manager: DownloadManager, temp_dir: Path) -> None:
        """Test downloading with aria2 backend."""
        task = DownloadTask(
            url="https://example.com/test.txt",
            dest=temp_dir / "test.txt",
            backend=DownloadBackend.ARIA2,
            concurrent=8,
            max_speed="2M",
        )
        
        # Mock subprocess
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(return_value=(b"", b""))
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await manager._download_aria2(task)
        
        assert result == task.dest
    
    @pytest.mark.asyncio
    async def test_download_failure(self, manager: DownloadManager, temp_dir: Path) -> None:
        """Test download failure handling."""
        task = DownloadTask(
            url="https://example.com/test.txt",
            dest=temp_dir / "test.txt",
            backend=DownloadBackend.CURL,
        )
        
        # Mock subprocess failure
        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"Error: Download failed"))
        
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            with pytest.raises(RuntimeError, match="curl failed"):
                await manager._download_curl(task)
    
    @pytest.mark.asyncio
    async def test_download_batch(self, manager: DownloadManager, temp_dir: Path) -> None:
        """Test batch download."""
        tasks = [
            DownloadTask(
                url=f"https://example.com/file{i}.txt",
                dest=temp_dir / f"file{i}.txt",
                backend=DownloadBackend.HTTpx,
            )
            for i in range(3)
        ]
        
        # Mock download method
        async def mock_download(task: DownloadTask, backend=None) -> Path:
            task.dest.write_text("content")
            return task.dest
        
        manager.download = mock_download
        
        results = await manager.download_batch(tasks, max_concurrent=2)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result == temp_dir / f"file{i}.txt"


class TestAria2ConfigManagement:
    """Test cases for aria2 configuration management."""
    
    @pytest.fixture
    def manager(self) -> DownloadManager:
        """Create a DownloadManager instance."""
        return DownloadManager()
    
    def test_get_aria2_config_default(self, manager: DownloadManager) -> None:
        """Test getting default aria2 config when file doesn't exist."""
        with patch.object(Path, "exists", return_value=False):
            config = manager.get_aria2_config()
        
        assert isinstance(config, Aria2Config)
        assert config.enabled is False
    
    def test_save_aria2_config(self, manager: DownloadManager, tmp_path: Path) -> None:
        """Test saving aria2 configuration."""
        config = Aria2Config(
            enabled=True,
            rpc_port=8080,
            config_file=tmp_path / "aria2.conf",
        )
        
        manager.save_aria2_config(config)
        
        assert config.config_file.exists()
        content = config.config_file.read_text()
        assert "rpc-listen-port=8080" in content
        assert "enable-rpc=true" in content
    
    def test_load_aria2_config(self, manager: DownloadManager, tmp_path: Path) -> None:
        """Test loading aria2 configuration from file."""
        config_file = tmp_path / "aria2.conf"
        config_content = """# Aria2 Config
rpc-listen-port=9090
rpc-secret=mysecret
max-connection-per-server=32
split=8
min-split-size=2M
dir=/downloads
"""
        config_file.write_text(config_content)
        
        manager._aria2_config = None
        with patch.object(manager, "_aria2_config", None):
            config = manager._load_aria2_config(config_file)
        
        assert config.rpc_port == 9090
        assert config.rpc_secret == "mysecret"
        assert config.max_connections == 32
        assert config.split == 8
        assert config.min_split_size == "2M"
        assert str(config.dir) == "/downloads"


class TestBTTrackerUpdate:
    """Test cases for BitTorrent tracker updates."""
    
    @pytest.fixture
    def manager(self) -> DownloadManager:
        """Create a DownloadManager instance."""
        return DownloadManager()
    
    def test_update_bt_trackers_success(self, manager: DownloadManager, tmp_path: Path) -> None:
        """Test successful BT tracker update."""
        config = Aria2Config(config_file=tmp_path / "aria2.conf")
        config.config_file.parent.mkdir(parents=True, exist_ok=True)
        config.config_file.write_text("# Aria2 config\n")
        manager._aria2_config = config
        
        # Mock curl response
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "udp://tracker1.com:1337\nudp://tracker2.com:1337\n"
        
        with patch("subprocess.run", return_value=mock_result):
            result = manager.update_bt_trackers()
        
        assert result is True
        content = config.config_file.read_text()
        assert "bt-tracker=" in content
        assert "udp://tracker1.com:1337" in content
    
    def test_update_bt_trackers_failure(self, manager: DownloadManager) -> None:
        """Test BT tracker update failure."""
        mock_result = Mock()
        mock_result.returncode = 1
        
        with patch("subprocess.run", return_value=mock_result):
            result = manager.update_bt_trackers()
        
        assert result is False


class TestDownloadManagerIntegration:
    """Integration tests for DownloadManager."""
    
    @pytest.mark.asyncio
    async def test_download_with_resume(self, tmp_path: Path) -> None:
        """Test downloading with resume support."""
        manager = DownloadManager()
        
        # Create a partially downloaded file
        dest = tmp_path / "partial.txt"
        dest.write_text("Hello ")  # Partial content
        
        task = DownloadTask(
            url="https://example.com/file.txt",
            dest=dest,
            resume=True,
            backend=DownloadBackend.HTTpx,
        )
        
        # Create a proper async iterator for chunks
        async def async_chunks(chunk_size=8192):
            yield b"World!"
        
        # Mock response with range support
        mock_response = MagicMock()
        mock_response.headers = {"content-length": "6"}
        mock_response.aiter_bytes = async_chunks
        mock_response.raise_for_status = Mock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_client = MagicMock()
        mock_client.stream = MagicMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await manager._download_httpx(task)
        
        assert result.exists()
        # File should contain appended content
        assert "World!" in result.read_text()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
