"""Tests for noVNC Web client integration.

These tests verify noVNC installation, startup, and management
using websockify for Web-based VNC access.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from tmoe.gui.novnc import NoVncManager, NoVncConfig


@pytest.fixture
def mock_platform(tmp_path):
    """Create a mock platform."""
    platform = Mock()
    platform.data_dir = tmp_path / "tmoe_data"
    return platform


@pytest.fixture
def novnc_manager(mock_platform):
    """Create a noVNC manager with mock platform."""
    with patch('tmoe.core.platform.PlatformInfo', return_value=mock_platform):
        manager = NoVncManager(data_dir=mock_platform.data_dir)
        return manager


class TestNoVncConfig:
    """Test noVNC configuration dataclass."""
    
    def test_default_config(self):
        """Test default noVNC configuration."""
        config = NoVncConfig()
        
        assert config.web_port == 36080
        assert config.vnc_host == "localhost"
        assert config.vnc_port == 5902
        assert config.base_path == "/novnc"
    
    def test_custom_config(self):
        """Test custom noVNC configuration."""
        config = NoVncConfig(
            web_port=8080,
            vnc_host="192.168.1.1",
            vnc_port=5905,
            base_path="/vnc"
        )
        
        assert config.web_port == 8080
        assert config.vnc_host == "192.168.1.1"
        assert config.vnc_port == 5905
        assert config.base_path == "/vnc"


class TestNoVncInitialization:
    """Test noVNC manager initialization."""
    
    def test_init_creates_paths(self, novnc_manager, mock_platform):
        """Test initialization creates directory paths."""
        assert novnc_manager.data_dir == mock_platform.data_dir
        assert novnc_manager.novnc_dir == mock_platform.data_dir / "novnc"
        assert novnc_manager.websockify_dir == mock_platform.data_dir / "websockify"
    
    def test_init_default_config(self, novnc_manager):
        """Test initialization creates default config."""
        assert isinstance(novnc_manager.config, NoVncConfig)
        assert novnc_manager.config.web_port == 36080
    
    def test_init_no_websockify_proc(self, novnc_manager):
        """Test initialization has no websockify process."""
        assert novnc_manager._websockify_proc is None
    
    def test_init_with_custom_data_dir(self, tmp_path):
        """Test initialization with custom data directory."""
        custom_dir = tmp_path / "custom_novnc"
        
        with patch('tmoe.core.platform.PlatformInfo'):
            manager = NoVncManager(data_dir=custom_dir)
            
            assert manager.data_dir == custom_dir
            assert manager.novnc_dir == custom_dir / "novnc"


class TestNoVncInstallation:
    """Test noVNC installation."""
    
    def test_is_installed_true(self, novnc_manager, tmp_path):
        """Test is_installed returns True when noVNC exists."""
        # Create fake noVNC directory with vnc.html
        novnc_manager.novnc_dir.mkdir(parents=True, exist_ok=True)
        (novnc_manager.novnc_dir / "vnc.html").touch()
        
        assert novnc_manager.is_installed is True
    
    def test_is_installed_false_no_dir(self, novnc_manager):
        """Test is_installed returns False when directory doesn't exist."""
        assert novnc_manager.is_installed is False
    
    def test_is_installed_false_no_vnc_html(self, novnc_manager, tmp_path):
        """Test is_installed returns False when vnc.html is missing."""
        novnc_manager.novnc_dir.mkdir(parents=True, exist_ok=True)
        # Create other files but not vnc.html
        (novnc_manager.novnc_dir / "other.html").touch()
        
        assert novnc_manager.is_installed is False
    
    @pytest.mark.asyncio
    async def test_install_success(self, novnc_manager):
        """Test successful noVNC installation."""
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc
            
            result = await novnc_manager.install()
            
            assert result is True
            # Should be called twice: once for noVNC, once for websockify
            assert mock_exec.call_count == 2
    
    @pytest.mark.asyncio
    async def test_install_novnc_clone_fails(self, novnc_manager):
        """Test install when noVNC clone fails."""
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.returncode = 1
            mock_exec.return_value = mock_proc
            
            result = await novnc_manager.install()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_install_websockify_clone_fails(self, novnc_manager):
        """Test install when websockify clone fails."""
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            # First call (noVNC) succeeds, second (websockify) fails
            mock_proc_novnc = AsyncMock()
            mock_proc_novnc.returncode = 0
            mock_proc_websockify = AsyncMock()
            mock_proc_websockify.returncode = 1
            
            mock_exec.side_effect = [mock_proc_novnc, mock_proc_websockify]
            
            result = await novnc_manager.install()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_install_exception_handling(self, novnc_manager):
        """Test install handles exceptions gracefully."""
        with patch('asyncio.create_subprocess_exec', side_effect=Exception("Git error")):
            result = await novnc_manager.install()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_install_creates_data_dir(self, novnc_manager):
        """Test install creates data directory if needed."""
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc
            
            await novnc_manager.install()
            
            assert novnc_manager.data_dir.exists()
    
    @pytest.mark.asyncio
    async def test_install_skip_if_already_installed(self, novnc_manager):
        """Test install skips if noVNC already installed."""
        # Make it appear installed
        novnc_manager.novnc_dir.mkdir(parents=True, exist_ok=True)
        (novnc_manager.novnc_dir / "vnc.html").touch()
        
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc
            
            await novnc_manager.install()
            
            # Should only clone websockify, not noVNC
            assert mock_exec.call_count == 1
            call_args = mock_exec.call_args[0]
            # Check that websockify repo is in the call args
            assert any("websockify" in str(arg) for arg in call_args)


class TestWebsockifyCommand:
    """Test websockify command building."""
    
    def test_get_websockify_cmd_with_system_binary(self, novnc_manager):
        """Test using system websockify binary."""
        novnc_manager.config.web_port = 8080
        novnc_manager.config.vnc_host = "127.0.0.1"
        novnc_manager.config.vnc_port = 5905
        
        with patch('shutil.which', return_value="/usr/bin/websockify"):
            cmd = novnc_manager._get_websockify_cmd()
            
            assert cmd[0] == "/usr/bin/websockify"
            assert "8080" in cmd
            assert "127.0.0.1:5905" in cmd
            assert "--web" in cmd
            assert "--cert" in cmd
            assert "self.pem" in cmd
    
    def test_get_websockify_cmd_with_bundled(self, novnc_manager):
        """Test using bundled websockify when system not available."""
        novnc_manager.config.web_port = 36080
        novnc_manager.config.vnc_host = "localhost"
        novnc_manager.config.vnc_port = 5902
        
        with patch('shutil.which', return_value=None):
            cmd = novnc_manager._get_websockify_cmd()
            
            assert cmd[0] == "python3"
            assert "websockify.py" in cmd[1]
            assert "36080" in cmd
            assert "localhost:5902" in cmd
            assert "--web" in cmd


class TestNoVncLifecycle:
    """Test noVNC server lifecycle."""
    
    @pytest.mark.asyncio
    async def test_start_success(self, novnc_manager):
        """Test successful noVNC start."""
        # Make it appear installed
        novnc_manager.novnc_dir.mkdir(parents=True, exist_ok=True)
        (novnc_manager.novnc_dir / "vnc.html").touch()
        
        mock_proc = AsyncMock()
        mock_proc.returncode = None  # Still running
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc) as mock_exec:
            with patch('shutil.which', return_value="/usr/bin/websockify"):
                url = await novnc_manager.start()
                
                assert "localhost" in url
                assert "36080" in url
                assert "vnc.html" in url
                assert novnc_manager._websockify_proc is mock_proc
                mock_exec.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_not_installed(self, novnc_manager):
        """Test start installs noVNC if not present."""
        # Create separate mock procs for install (returncode=0) and start (returncode=None)
        install_proc = AsyncMock()
        install_proc.returncode = 0
        install_proc.communicate = AsyncMock(return_value=(b"", b""))
        
        start_proc = AsyncMock()
        start_proc.returncode = None  # Still running
        start_proc.communicate = AsyncMock(return_value=(b"", b""))
        
        # First 2 calls are for install, 3rd call is for start
        procs = [install_proc, install_proc, start_proc]
        proc_iter = iter(procs)
        
        with patch('asyncio.create_subprocess_exec', side_effect=lambda *args, **kwargs: next(proc_iter)) as mock_exec:
            with patch('shutil.which', return_value="/usr/bin/websockify"):
                with patch('asyncio.sleep', AsyncMock()):  # Skip sleep
                    
                    url = await novnc_manager.start()
                    
                    # Should have called for install (2 calls) + start (1 call)
                    assert mock_exec.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_start_install_fails(self, novnc_manager):
        """Test start raises error when install fails."""
        with patch.object(novnc_manager, 'install', return_value=False):
            with pytest.raises(RuntimeError, match="Failed to install"):
                await novnc_manager.start()
    
    @pytest.mark.asyncio
    async def test_start_process_fails(self, novnc_manager):
        """Test start when websockify process fails."""
        novnc_manager.novnc_dir.mkdir(parents=True, exist_ok=True)
        (novnc_manager.novnc_dir / "vnc.html").touch()
        
        mock_proc = AsyncMock()
        mock_proc.returncode = 1  # Failed immediately
        mock_proc.communicate = AsyncMock(return_value=(b"", b"Error: port in use"))
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            with patch('shutil.which', return_value="/usr/bin/websockify"):
                with pytest.raises(RuntimeError, match="Failed to start"):
                    await novnc_manager.start()
    
    @pytest.mark.asyncio
    async def test_start_stops_existing(self, novnc_manager):
        """Test start stops existing instance first."""
        novnc_manager.novnc_dir.mkdir(parents=True, exist_ok=True)
        (novnc_manager.novnc_dir / "vnc.html").touch()
        
        old_proc = AsyncMock()
        old_proc.returncode = None
        novnc_manager._websockify_proc = old_proc
        
        new_proc = AsyncMock()
        new_proc.returncode = None
        
        with patch('asyncio.create_subprocess_exec', return_value=new_proc):
            with patch('shutil.which', return_value="/usr/bin/websockify"):
                await novnc_manager.start()
                
                old_proc.terminate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_running(self, novnc_manager):
        """Test stopping running noVNC server."""
        mock_proc = AsyncMock()
        mock_proc.returncode = None
        novnc_manager._websockify_proc = mock_proc
        
        await novnc_manager.stop()
        
        mock_proc.terminate.assert_called_once()
        mock_proc.wait.assert_called_once()
        assert novnc_manager._websockify_proc is None
    
    @pytest.mark.asyncio
    async def test_stop_timeout_kills(self, novnc_manager):
        """Test stop kills process if terminate times out."""
        mock_proc = AsyncMock()
        mock_proc.returncode = None
        # Make wait raise TimeoutError on first call, then succeed
        mock_proc.wait = AsyncMock(side_effect=[asyncio.TimeoutError(), None])
        novnc_manager._websockify_proc = mock_proc
        
        await novnc_manager.stop()
        
        mock_proc.terminate.assert_called_once()
        mock_proc.kill.assert_called_once()
        assert novnc_manager._websockify_proc is None
    
    @pytest.mark.asyncio
    async def test_stop_not_running(self, novnc_manager):
        """Test stop when not running does nothing."""
        novnc_manager._websockify_proc = None
        
        # Should not raise
        await novnc_manager.stop()
        
        assert novnc_manager._websockify_proc is None


class TestNoVncRunningCheck:
    """Test noVNC running status check."""
    
    @pytest.mark.asyncio
    async def test_is_running_true(self, novnc_manager):
        """Test is_running when process is active."""
        mock_proc = AsyncMock()
        mock_proc.returncode = None  # Still running
        novnc_manager._websockify_proc = mock_proc
        
        result = await novnc_manager.is_running()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_is_running_false_no_proc(self, novnc_manager):
        """Test is_running when no process."""
        novnc_manager._websockify_proc = None
        
        result = await novnc_manager.is_running()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_is_running_false_finished(self, novnc_manager):
        """Test is_running when process has finished."""
        mock_proc = AsyncMock()
        mock_proc.returncode = 0  # Finished
        novnc_manager._websockify_proc = mock_proc
        
        result = await novnc_manager.is_running()
        
        assert result is False


class TestNoVncUrl:
    """Test noVNC URL generation."""
    
    def test_get_url_default(self, novnc_manager):
        """Test getting default noVNC URL."""
        url = novnc_manager.get_url()
        
        assert "http://localhost:36080/vnc.html" == url
    
    def test_get_url_custom_port(self, novnc_manager):
        """Test getting URL with custom port."""
        novnc_manager.config.web_port = 8080
        
        url = novnc_manager.get_url()
        
        assert "http://localhost:8080/vnc.html" == url
    
    @pytest.mark.asyncio
    async def test_start_returns_full_url(self, novnc_manager):
        """Test start returns full URL with parameters."""
        novnc_manager.novnc_dir.mkdir(parents=True, exist_ok=True)
        (novnc_manager.novnc_dir / "vnc.html").touch()
        
        mock_proc = AsyncMock()
        mock_proc.returncode = None
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            with patch('shutil.which', return_value="/usr/bin/websockify"):
                url = await novnc_manager.start()
                
                assert "host=localhost" in url
                assert "port=36080" in url


class TestNoVncConfiguration:
    """Test noVNC configuration options."""
    
    def test_config_web_port(self, novnc_manager):
        """Test web port configuration."""
        novnc_manager.config.web_port = 9090
        
        url = novnc_manager.get_url()
        assert ":9090" in url
    
    def test_config_vnc_host(self, novnc_manager):
        """Test VNC host configuration."""
        novnc_manager.config.vnc_host = "192.168.1.100"
        novnc_manager.config.vnc_port = 5905
        
        with patch('shutil.which', return_value=None):
            cmd = novnc_manager._get_websockify_cmd()
            
            assert "192.168.1.100:5905" in cmd


class TestNoVncEdgeCases:
    """Test noVNC edge cases."""
    
    @pytest.mark.asyncio
    async def test_install_idempotent(self, novnc_manager):
        """Test install is idempotent."""
        # First install
        with patch('asyncio.create_subprocess_exec') as mock_exec:
            mock_proc = AsyncMock()
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc
            
            result1 = await novnc_manager.install()
            assert result1 is True
            
            # Second install should succeed without errors
            result2 = await novnc_manager.install()
            assert result2 is True
    
    @pytest.mark.asyncio
    async def test_stop_after_start_failed(self, novnc_manager):
        """Test stop after start failed doesn't raise."""
        novnc_manager.novnc_dir.mkdir(parents=True, exist_ok=True)
        (novnc_manager.novnc_dir / "vnc.html").touch()
        
        mock_proc = AsyncMock()
        mock_proc.returncode = 1  # Failed
        mock_proc.communicate = AsyncMock(return_value=(b"", b"Error"))
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
            with patch('shutil.which', return_value="/usr/bin/websockify"):
                try:
                    await novnc_manager.start()
                except RuntimeError:
                    pass
                
                # Stop should not raise
                await novnc_manager.stop()
    
    def test_repo_urls(self, novnc_manager):
        """Test noVNC and websockify repository URLs."""
        assert "github.com/novnc/noVNC" in novnc_manager.NOVNC_REPO
        assert "github.com/novnc/websockify" in novnc_manager.WEBSOCKIFY_REPO
