"""Tests for VNC server management.

These tests verify VNC server configuration, startup, and management
for both TigerVNC and TightVNC backends.
"""

import pytest
import socket
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call

from tmoe.gui.vnc import VncManager, VncConfig


@pytest.fixture
def mock_config():
    """Create a mock global config."""
    config = Mock()
    config.vnc_server = "tiger"
    config.vnc_resolution = "1440x720"
    config.vnc_display = 2
    config.vnc_depth = 24
    config.vnc_localhost = False
    return config


@pytest.fixture
def vnc_manager(mock_config):
    """Create a VNC manager with mocked config."""
    with patch('tmoe.gui.vnc.get_config', return_value=mock_config):
        with patch('tmoe.gui.vnc.PlatformInfo'):
            manager = VncManager()
            return manager


class TestVncConfig:
    """Test VNC configuration dataclass."""
    
    def test_default_config(self):
        """Test default VNC configuration."""
        config = VncConfig()
        
        assert config.server == "tiger"
        assert config.resolution == "1440x720"
        assert config.display == 2
        assert config.depth == 24
        assert config.localhost is False
        assert config.password is None
    
    def test_custom_config(self):
        """Test custom VNC configuration."""
        config = VncConfig(
            server="tight",
            resolution="1920x1080",
            display=1,
            depth=16,
            localhost=True,
            password="secret"
        )
        
        assert config.server == "tight"
        assert config.resolution == "1920x1080"
        assert config.display == 1
        assert config.depth == 16
        assert config.localhost is True
        assert config.password == "secret"


class TestVncManagerInitialization:
    """Test VNC manager initialization."""
    
    def test_init_loads_config(self, mock_config):
        """Test that VncManager loads config on init."""
        with patch('tmoe.gui.vnc.get_config', return_value=mock_config):
            with patch('tmoe.gui.vnc.PlatformInfo'):
                manager = VncManager()
                
                assert manager.vnc_config.server == "tiger"
                assert manager.vnc_config.resolution == "1440x720"
                assert manager.vnc_config.display == 2
    
    def test_vnc_config_property(self, vnc_manager):
        """Test vnc_config property returns current config."""
        config = vnc_manager.vnc_config
        
        assert isinstance(config, VncConfig)
        assert config.server == "tiger"


class TestVncBinaryDetection:
    """Test VNC binary detection."""
    
    def test_get_vnc_bin_tiger_found(self, vnc_manager):
        """Test detecting TigerVNC binary."""
        vnc_manager._vnc_config.server = "tiger"
        
        with patch('shutil.which', side_effect=["/usr/bin/tigervncserver", None]):
            result = vnc_manager.get_vnc_bin()
            assert result == "/usr/bin/tigervncserver"
    
    def test_get_vnc_bin_tiger_fallback(self, vnc_manager):
        """Test TigerVNC fallback to Xtigervnc."""
        vnc_manager._vnc_config.server = "tiger"
        
        with patch('shutil.which', side_effect=[None, "/usr/bin/Xtigervnc"]):
            result = vnc_manager.get_vnc_bin()
            assert result == "/usr/bin/Xtigervnc"
    
    def test_get_vnc_bin_tight_found(self, vnc_manager):
        """Test detecting TightVNC binary."""
        vnc_manager._vnc_config.server = "tight"
        
        with patch('shutil.which', side_effect=["/usr/bin/tightvncserver", None]):
            result = vnc_manager.get_vnc_bin()
            assert result == "/usr/bin/tightvncserver"
    
    def test_get_vnc_bin_tight_fallback(self, vnc_manager):
        """Test TightVNC fallback to Xvnc."""
        vnc_manager._vnc_config.server = "tight"
        
        with patch('shutil.which', side_effect=[None, "/usr/bin/Xvnc"]):
            result = vnc_manager.get_vnc_bin()
            assert result == "/usr/bin/Xvnc"
    
    def test_get_vnc_bin_not_found(self, vnc_manager):
        """Test when VNC binary is not found."""
        vnc_manager._vnc_config.server = "tiger"
        
        with patch('shutil.which', return_value=None):
            result = vnc_manager.get_vnc_bin()
            assert result is None
    
    def test_get_vnc_bin_unknown_server(self, vnc_manager):
        """Test unknown VNC server type."""
        vnc_manager._vnc_config.server = "unknown"
        
        result = vnc_manager.get_vnc_bin()
        assert result is None


class TestVncPortCalculation:
    """Test VNC port calculation."""
    
    @pytest.mark.parametrize("display,expected_port", [
        (0, 5900),
        (1, 5901),
        (2, 5902),
        (10, 5910),
        (99, 5999),
    ])
    def test_get_display_port(self, vnc_manager, display, expected_port):
        """Test display to port calculation."""
        vnc_manager._vnc_config.display = display
        
        port = vnc_manager.get_display_port()
        assert port == expected_port


class TestVncCommandBuilding:
    """Test VNC command building."""
    
    def test_build_tiger_cmd_basic(self, vnc_manager):
        """Test basic TigerVNC command building."""
        vnc_manager._vnc_config.server = "tiger"
        vnc_manager._vnc_config.display = 2
        vnc_manager._vnc_config.resolution = "1440x720"
        vnc_manager._vnc_config.depth = 24
        vnc_manager._vnc_config.localhost = False
        
        cmd = vnc_manager._build_tiger_cmd(desktop=None, command=None)
        
        assert "Xtigervnc" in cmd
        assert ":2" in cmd
        assert "-geometry" in cmd
        assert "1440x720" in cmd
        assert "-depth" in cmd
        assert "24" in cmd
        assert "-pn" in cmd
        assert "-localhost" in cmd
        assert "no" in cmd  # localhost=no
    
    def test_build_tiger_cmd_localhost(self, vnc_manager):
        """Test TigerVNC with localhost only."""
        vnc_manager._vnc_config.localhost = True
        
        cmd = vnc_manager._build_tiger_cmd(desktop=None, command=None)
        
        localhost_idx = cmd.index("-localhost")
        assert cmd[localhost_idx + 1] == "yes"
    
    def test_build_tiger_cmd_with_desktop(self, vnc_manager):
        """Test TigerVNC command with desktop session."""
        cmd = vnc_manager._build_tiger_cmd(desktop="xfce", command=None)
        
        assert "-Session" in cmd
        assert "xfce" in cmd
    
    def test_build_tight_cmd_basic(self, vnc_manager):
        """Test basic TightVNC command building."""
        vnc_manager._vnc_config.server = "tight"
        vnc_manager._vnc_config.display = 1
        vnc_manager._vnc_config.resolution = "1920x1080"
        vnc_manager._vnc_config.depth = 16
        vnc_manager._vnc_config.localhost = False
        
        cmd = vnc_manager._build_tight_cmd(desktop=None, command=None)
        
        assert "Xvnc" in cmd
        assert ":1" in cmd
        assert "-geometry" in cmd
        assert "1920x1080" in cmd
        assert "-depth" in cmd
        assert "16" in cmd
    
    def test_build_tight_cmd_localhost(self, vnc_manager):
        """Test TightVNC with localhost only."""
        vnc_manager._vnc_config.server = "tight"
        vnc_manager._vnc_config.localhost = True
        
        cmd = vnc_manager._build_tight_cmd(desktop=None, command=None)
        
        assert "-localhost" in cmd


class TestVncLifecycle:
    """Test VNC server lifecycle operations."""
    
    @pytest.mark.asyncio
    async def test_start_vnc_success(self, vnc_manager):
        """Test successful VNC server start."""
        vnc_manager._vnc_config.server = "tiger"
        vnc_manager._vnc_config.display = 2
        
        with patch.object(vnc_manager, 'get_vnc_bin', return_value="/usr/bin/Xtigervnc"):
            with patch('asyncio.create_subprocess_exec', return_value=AsyncMock()) as mock_exec:
                with patch.object(vnc_manager, 'is_running', return_value=True):
                    port, display = await vnc_manager.start_vnc()
                    
                    assert port == 5902
                    assert display == ":2"
                    mock_exec.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_vnc_server_not_found(self, vnc_manager):
        """Test start when VNC server binary not found."""
        with patch.object(vnc_manager, 'get_vnc_bin', return_value=None):
            with pytest.raises(RuntimeError, match="not found"):
                await vnc_manager.start_vnc()
    
    @pytest.mark.asyncio
    async def test_start_vnc_fails_to_start(self, vnc_manager):
        """Test when VNC server fails to start."""
        vnc_manager._vnc_config.server = "tiger"
        
        with patch.object(vnc_manager, 'get_vnc_bin', return_value="/usr/bin/Xtigervnc"):
            with patch('asyncio.create_subprocess_exec', return_value=AsyncMock()):
                with patch.object(vnc_manager, 'is_running', return_value=False):
                    with pytest.raises(RuntimeError, match="Failed to start"):
                        await vnc_manager.start_vnc()
    
    @pytest.mark.asyncio
    async def test_start_vnc_with_desktop(self, vnc_manager):
        """Test starting VNC with desktop environment."""
        vnc_manager._vnc_config.server = "tiger"
        
        with patch.object(vnc_manager, 'get_vnc_bin', return_value="/usr/bin/Xtigervnc"):
            with patch('asyncio.create_subprocess_exec') as mock_exec:
                with patch.object(vnc_manager, 'is_running', return_value=True):
                    await vnc_manager.start_vnc(desktop="xfce")
                    
                    # Verify command includes desktop
                    call_args = mock_exec.call_args[0]
                    assert "Xtigervnc" in call_args
    
    @pytest.mark.asyncio
    async def test_stop_vnc_tiger(self, vnc_manager):
        """Test stopping TigerVNC server."""
        vnc_manager._vnc_config.server = "tiger"
        vnc_manager._vnc_config.display = 2
        
        mock_proc = AsyncMock()
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc) as mock_exec:
            await vnc_manager.stop_vnc()
            
            mock_exec.assert_called_once()
            call_args = mock_exec.call_args[0]
            assert "tigervncserver" in call_args
            assert "-kill" in call_args
            assert ":2" in call_args
    
    @pytest.mark.asyncio
    async def test_stop_vnc_tight(self, vnc_manager):
        """Test stopping TightVNC server."""
        vnc_manager._vnc_config.server = "tight"
        vnc_manager._vnc_config.display = 1
        
        mock_proc = AsyncMock()
        with patch('asyncio.create_subprocess_exec', return_value=mock_proc) as mock_exec:
            await vnc_manager.stop_vnc()
            
            call_args = mock_exec.call_args[0]
            assert "tightvncserver" in call_args
            assert "-kill" in call_args
            assert ":1" in call_args


class TestVncRunningCheck:
    """Test VNC server running status check."""
    
    @pytest.mark.asyncio
    async def test_is_running_true(self, vnc_manager):
        """Test detecting running VNC server."""
        vnc_manager._vnc_config.display = 2  # Port 5902
        
        with patch('socket.socket') as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket.connect_ex.return_value = 0  # Success
            mock_socket_class.return_value = mock_socket
            
            result = await vnc_manager.is_running()
            
            assert result is True
            mock_socket.connect_ex.assert_called_once_with(("127.0.0.1", 5902))
    
    @pytest.mark.asyncio
    async def test_is_running_false(self, vnc_manager):
        """Test detecting stopped VNC server."""
        vnc_manager._vnc_config.display = 2
        
        with patch('socket.socket') as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket.connect_ex.return_value = 1  # Connection refused
            mock_socket_class.return_value = mock_socket
            
            result = await vnc_manager.is_running()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_is_running_exception(self, vnc_manager):
        """Test is_running handles exceptions gracefully."""
        with patch('socket.socket', side_effect=socket.error("Socket error")):
            result = await vnc_manager.is_running()
            
            assert result is False


class TestVncConfiguration:
    """Test VNC configuration methods."""
    
    def test_configure_all_settings(self, vnc_manager, mock_config):
        """Test configuring all VNC settings."""
        vnc_manager.configure(
            server="tight",
            resolution="1920x1080",
            display=5,
            depth=16,
            localhost=True
        )
        
        assert vnc_manager.vnc_config.server == "tight"
        assert vnc_manager.vnc_config.resolution == "1920x1080"
        assert vnc_manager.vnc_config.display == 5
        assert vnc_manager.vnc_config.depth == 16
        assert vnc_manager.vnc_config.localhost is True
        
        # Verify config was saved
        assert mock_config.vnc_server == "tight"
        assert mock_config.vnc_resolution == "1920x1080"
        assert mock_config.vnc_display == 5
        assert mock_config.vnc_depth == 16
        assert mock_config.vnc_localhost is True
        mock_config.save.assert_called_once()
    
    def test_configure_partial_settings(self, vnc_manager, mock_config):
        """Test configuring only some settings."""
        original_server = vnc_manager.vnc_config.server
        original_display = vnc_manager.vnc_config.display
        
        vnc_manager.configure(resolution="800x600")
        
        assert vnc_manager.vnc_config.resolution == "800x600"
        assert vnc_manager.vnc_config.server == original_server  # Unchanged
        assert vnc_manager.vnc_config.display == original_display  # Unchanged
    
    def test_configure_no_settings(self, vnc_manager, mock_config):
        """Test configure with no settings still saves."""
        vnc_manager.configure()
        
        mock_config.save.assert_called_once()


class TestVncResolutions:
    """Test various VNC resolutions."""
    
    @pytest.mark.parametrize("resolution", [
        "640x480",
        "800x600",
        "1024x768",
        "1280x720",
        "1440x720",
        "1920x1080",
        "2560x1440",
        "3840x2160",
    ])
    def test_supported_resolutions(self, vnc_manager, resolution):
        """Test that various resolutions can be configured."""
        vnc_manager.configure(resolution=resolution)
        assert vnc_manager.vnc_config.resolution == resolution


class TestVncDepths:
    """Test VNC color depths."""
    
    @pytest.mark.parametrize("depth", [16, 24, 32])
    def test_supported_depths(self, vnc_manager, depth):
        """Test that various color depths can be configured."""
        vnc_manager.configure(depth=depth)
        assert vnc_manager.vnc_config.depth == depth


class TestVncEdgeCases:
    """Test VNC edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_start_vnc_with_custom_command(self, vnc_manager):
        """Test starting VNC with custom command."""
        vnc_manager._vnc_config.server = "tiger"
        
        with patch.object(vnc_manager, 'get_vnc_bin', return_value="/usr/bin/Xtigervnc"):
            with patch('asyncio.create_subprocess_exec') as mock_exec:
                with patch.object(vnc_manager, 'is_running', return_value=True):
                    await vnc_manager.start_vnc(command=["/bin/bash"])
                    
                    mock_exec.assert_called_once()
    
    def test_server_type_switching(self, vnc_manager, mock_config):
        """Test switching between Tiger and Tight VNC."""
        # Start with tiger
        assert vnc_manager.vnc_config.server == "tiger"
        
        # Switch to tight
        vnc_manager.configure(server="tight")
        assert vnc_manager.vnc_config.server == "tight"
        
        # Switch back to tiger
        vnc_manager.configure(server="tiger")
        assert vnc_manager.vnc_config.server == "tiger"
    
    @pytest.mark.asyncio
    async def test_is_running_different_displays(self, vnc_manager):
        """Test is_running checks correct port for different displays."""
        test_cases = [
            (0, 5900),
            (1, 5901),
            (5, 5905),
            (10, 5910),
        ]
        
        for display, expected_port in test_cases:
            vnc_manager._vnc_config.display = display
            
            with patch('socket.socket') as mock_socket_class:
                mock_socket = MagicMock()
                mock_socket.connect_ex.return_value = 0
                mock_socket_class.return_value = mock_socket
                
                await vnc_manager.is_running()
                
                mock_socket.connect_ex.assert_called_with(("127.0.0.1", expected_port))
