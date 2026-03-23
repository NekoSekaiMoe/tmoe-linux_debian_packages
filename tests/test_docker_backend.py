"""Tests for Docker container backend.

These tests verify the Docker backend functionality including
container lifecycle management, image mapping, and label handling.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from tmoe.container.docker import DockerBackend
from tmoe.container.base import ContainerStatus
from tmoe.core.config import ContainerConfig


@pytest.fixture
def mock_platform():
    """Create a mock platform for testing."""
    platform = Mock()
    platform.config_dir = Path("/tmp/tmoe_test/config")
    platform.normalized_arch = "amd64"
    platform.is_android = False
    platform.is_termux = False
    return platform


@pytest.fixture
def docker_backend(mock_platform, tmp_path):
    """Create a Docker backend with mocked dependencies."""
    mock_platform.config_dir = tmp_path / "config"
    mock_platform.config_dir.mkdir(parents=True, exist_ok=True)
    
    backend = DockerBackend(mock_platform)
    return backend


class TestDockerBackendBasic:
    """Test basic Docker backend properties."""
    
    def test_backend_type(self, docker_backend):
        """Test backend type is 'docker'."""
        assert docker_backend.backend_type == "docker"
    
    def test_requires_root(self, docker_backend):
        """Test Docker backend does not require root."""
        assert docker_backend.requires_root is False
    
    def test_docker_available_when_docker_exists(self, docker_backend):
        """Test is_available returns True when docker exists."""
        with patch('shutil.which', return_value='/usr/bin/docker'):
            # Reset the cached value
            docker_backend._docker_available = None
            assert docker_backend.is_available is True
    
    def test_docker_not_available_when_docker_missing(self, docker_backend):
        """Test is_available returns False when docker is not installed."""
        with patch('shutil.which', return_value=None):
            # Reset the cached value
            docker_backend._docker_available = None
            assert docker_backend.is_available is False
    
    def test_distro_images_mapping(self, docker_backend):
        """Test Docker image mapping for distributions."""
        expected_images = {
            "debian": "debian",
            "ubuntu": "ubuntu",
            "alpine": "alpine",
            "arch": "archlinux",
            "fedora": "fedora",
            "centos": "centos",
            "opensuse": "opensuse/leap",
            "kali": "kalilinux/kali-rolling",
        }
        
        for distro, expected_image in expected_images.items():
            assert docker_backend.DISTRO_IMAGES.get(distro) == expected_image, \
                f"Image mapping for {distro} should be {expected_image}"


class TestDockerContainerLifecycle:
    """Test Docker container lifecycle operations."""
    
    @pytest.mark.asyncio
    async def test_create_container_success(self, docker_backend):
        """Test successful container creation."""
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, 'exists', return_value=False):
                with patch.object(docker_backend, 'save_container_config') as mock_save:
                    config = await docker_backend.create(
                        name="test-debian",
                        distro="debian",
                        arch="amd64",
                        codename="bookworm"
                    )
                    
                    assert config.name == "test-debian"
                    assert config.distro == "debian"
                    assert config.arch == "amd64"
                    assert config.codename == "bookworm"
                    assert config.container_type == "docker"
                    assert config.user == "root"
                    mock_save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_container_already_exists(self, docker_backend):
        """Test creating container that already exists raises error."""
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, 'exists', return_value=True):
                with pytest.raises(ValueError, match="already exists"):
                    await docker_backend.create("existing-container", "debian")
    
    @pytest.mark.asyncio
    async def test_create_container_docker_not_available(self, docker_backend):
        """Test creating container when Docker is not available."""
        with patch.object(docker_backend, 'is_available', False):
            with pytest.raises(RuntimeError, match="not available"):
                await docker_backend.create("test-container", "debian")
    
    @pytest.mark.asyncio
    async def test_create_container_default_arch(self, docker_backend):
        """Test container creation uses default arch when not specified."""
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, 'exists', return_value=False):
                with patch.object(docker_backend, 'save_container_config'):
                    config = await docker_backend.create(
                        name="test-default",
                        distro="ubuntu"
                    )
                    
                    assert config.arch == "amd64"  # From mock_platform
    
    @pytest.mark.asyncio
    async def test_create_container_default_codename(self, docker_backend):
        """Test container creation uses 'latest' when codename not specified."""
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, 'exists', return_value=False):
                with patch.object(docker_backend, 'save_container_config'):
                    config = await docker_backend.create(
                        name="test-latest",
                        distro="alpine"
                    )
                    
                    assert config.codename == "latest"


class TestDockerContainerOperations:
    """Test Docker container operations."""
    
    @pytest.mark.asyncio
    async def test_exists_when_container_exists(self, docker_backend):
        """Test exists returns True when container exists."""
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, '_run_docker', return_value=(0, "", "")):
                result = await docker_backend.exists("existing-container")
                assert result is True
    
    @pytest.mark.asyncio
    async def test_exists_when_container_not_exists(self, docker_backend):
        """Test exists returns False when container doesn't exist."""
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, '_run_docker', return_value=(1, "", "Error")):
                result = await docker_backend.exists("nonexistent-container")
                assert result is False
    
    @pytest.mark.asyncio
    async def test_exists_docker_not_available(self, docker_backend):
        """Test exists returns False when Docker is not available."""
        with patch.object(docker_backend, 'is_available', False):
            result = await docker_backend.exists("any-container")
            assert result is False
    
    @pytest.mark.asyncio
    async def test_start_container_success(self, docker_backend):
        """Test starting a container successfully."""
        config = ContainerConfig(
            name="test-start",
            distro="debian",
            arch="amd64",
            container_type="docker"
        )
        
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, 'load_container_config', return_value=config):
                with patch.object(docker_backend, 'exists', return_value=True):
                    with patch.object(docker_backend, '_run_docker', return_value=(0, "", "")):
                        await docker_backend.start("test-start")
    
    @pytest.mark.asyncio
    async def test_start_container_not_found(self, docker_backend):
        """Test starting a container that doesn't exist in config."""
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, 'load_container_config', return_value=None):
                with pytest.raises(ValueError, match="not found"):
                    await docker_backend.start("missing-config")
    
    @pytest.mark.asyncio
    async def test_start_creates_new_container(self, docker_backend):
        """Test start creates container if it doesn't exist in Docker."""
        config = ContainerConfig(
            name="test-create-new",
            distro="ubuntu",
            arch="amd64",
            codename="jammy",
            container_type="docker"
        )
        
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, 'load_container_config', return_value=config):
                with patch.object(docker_backend, 'exists', return_value=False):
                    with patch.object(docker_backend, '_create_container') as mock_create:
                        await docker_backend.start("test-create-new")
                        mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_container_success(self, docker_backend):
        """Test stopping a container successfully."""
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, '_run_docker', return_value=(0, "", "")) as mock_run:
                await docker_backend.stop("test-stop")
                mock_run.assert_called_once_with(["stop", "test-stop"])
    
    @pytest.mark.asyncio
    async def test_stop_container_docker_not_available(self, docker_backend):
        """Test stop returns early when Docker is not available."""
        with patch.object(docker_backend, 'is_available', False):
            with patch.object(docker_backend, '_run_docker') as mock_run:
                await docker_backend.stop("test-stop")
                mock_run.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_remove_container_normal(self, docker_backend):
        """Test removing a container normally."""
        config_path = docker_backend.platform.config_dir / "test-remove.json"
        config_path.touch()
        
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, '_run_docker', return_value=(0, "", "")) as mock_run:
                with patch.object(docker_backend, 'get_container_config_path', return_value=config_path):
                    await docker_backend.remove("test-remove", force=False)
                    mock_run.assert_called_once_with(["rm", "test-remove"])
                    assert not config_path.exists()
    
    @pytest.mark.asyncio
    async def test_remove_container_force(self, docker_backend):
        """Test force removing a container."""
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, '_run_docker', return_value=(0, "", "")) as mock_run:
                with patch.object(docker_backend, 'get_container_config_path', return_value=Path("/nonexistent")):
                    await docker_backend.remove("test-force", force=True)
                    mock_run.assert_called_once_with(["rm", "-f", "test-force"])


class TestDockerExec:
    """Test Docker exec operations."""
    
    @pytest.mark.asyncio
    async def test_exec_command_success(self, docker_backend):
        """Test executing a command in container."""
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, '_run_docker', return_value=(0, "output", "")) as mock_run:
                exit_code, stdout, stderr = await docker_backend.exec(
                    "test-container",
                    ["ls", "-la"]
                )
                
                assert exit_code == 0
                assert stdout == "output"
                mock_run.assert_called_once_with(["exec", "test-container", "ls", "-la"])
    
    @pytest.mark.asyncio
    async def test_exec_command_failure(self, docker_backend):
        """Test exec when command fails."""
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, '_run_docker', return_value=(1, "", "error message")):
                exit_code, stdout, stderr = await docker_backend.exec(
                    "test-container",
                    ["false"]
                )
                
                assert exit_code == 1
                assert stderr == "error message"
    
    @pytest.mark.asyncio
    async def test_exec_docker_not_available(self, docker_backend):
        """Test exec raises error when Docker is not available."""
        with patch.object(docker_backend, 'is_available', False):
            with pytest.raises(RuntimeError, match="not available"):
                await docker_backend.exec("test-container", ["ls"])


class TestDockerGetInfo:
    """Test Docker container info retrieval."""
    
    @pytest.mark.asyncio
    async def test_get_info_running_container(self, docker_backend):
        """Test getting info for a running container."""
        inspect_data = {
            "Config": {
                "Labels": {
                    "tmoe": "true",
                    "tmoe.distro": "debian",
                    "tmoe.arch": "arm64"
                }
            },
            "State": {
                "Running": True,
                "Pid": 1234
            }
        }
        
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, '_run_docker', return_value=(0, json.dumps(inspect_data), "")):
                info = await docker_backend.get_info("running-container")
                
                assert info is not None
                assert info.name == "running-container"
                assert info.config.distro == "debian"
                assert info.config.arch == "arm64"
                assert info.status == ContainerStatus.RUNNING
                assert info.pid == 1234
    
    @pytest.mark.asyncio
    async def test_get_info_stopped_container(self, docker_backend):
        """Test getting info for a stopped container."""
        inspect_data = {
            "Config": {
                "Labels": {}
            },
            "State": {
                "Running": False,
                "Paused": False
            }
        }
        
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, '_run_docker', return_value=(0, json.dumps(inspect_data), "")):
                info = await docker_backend.get_info("stopped-container")
                
                assert info is not None
                assert info.status == ContainerStatus.STOPPED
                assert info.pid is None
    
    @pytest.mark.asyncio
    async def test_get_info_paused_container(self, docker_backend):
        """Test getting info for a paused container."""
        inspect_data = {
            "Config": {
                "Labels": {}
            },
            "State": {
                "Running": False,
                "Paused": True
            }
        }
        
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, '_run_docker', return_value=(0, json.dumps(inspect_data), "")):
                info = await docker_backend.get_info("paused-container")
                
                assert info is not None
                assert info.status == ContainerStatus.PAUSED
    
    @pytest.mark.asyncio
    async def test_get_info_container_not_exists(self, docker_backend):
        """Test getting info for non-existent container."""
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, '_run_docker', return_value=(1, "", "No such container")):
                info = await docker_backend.get_info("nonexistent")
                assert info is None
    
    @pytest.mark.asyncio
    async def test_get_info_docker_not_available(self, docker_backend):
        """Test getting info when Docker is not available."""
        with patch.object(docker_backend, 'is_available', False):
            info = await docker_backend.get_info("any-container")
            assert info is None
    
    @pytest.mark.asyncio
    async def test_get_info_invalid_json(self, docker_backend):
        """Test handling invalid JSON from docker inspect."""
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, '_run_docker', return_value=(0, "invalid json", "")):
                info = await docker_backend.get_info("bad-container")
                assert info is None


class TestDockerListContainers:
    """Test listing Docker containers."""
    
    @pytest.mark.asyncio
    async def test_list_containers_success(self, docker_backend):
        """Test listing containers successfully."""
        container_data = [
            {"Names": "container1"},
            {"Names": "container2"}
        ]
        
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, '_run_docker', return_value=(0, "\n".join([json.dumps(d) for d in container_data]), "")):
                with patch.object(docker_backend, 'get_info') as mock_get_info:
                    mock_get_info.side_effect = [
                        Mock(name="container1"),
                        Mock(name="container2")
                    ]
                    
                    containers = await docker_backend.list_containers()
                    
                    assert len(containers) == 2
                    assert mock_get_info.call_count == 2
    
    @pytest.mark.asyncio
    async def test_list_containers_empty(self, docker_backend):
        """Test listing when no containers exist."""
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, '_run_docker', return_value=(0, "", "")):
                containers = await docker_backend.list_containers()
                assert containers == []
    
    @pytest.mark.asyncio
    async def test_list_containers_docker_not_available(self, docker_backend):
        """Test listing returns empty list when Docker is not available."""
        with patch.object(docker_backend, 'is_available', False):
            containers = await docker_backend.list_containers()
            assert containers == []
    
    @pytest.mark.asyncio
    async def test_list_containers_filter_error(self, docker_backend):
        """Test listing when docker command fails."""
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, '_run_docker', return_value=(1, "", "error")):
                containers = await docker_backend.list_containers()
                assert containers == []
    
    @pytest.mark.asyncio
    async def test_list_containers_skips_invalid_json(self, docker_backend):
        """Test that containers with invalid JSON are skipped."""
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, '_run_docker', return_value=(0, "invalid\n{\"Names\": \"valid\"}", "")):
                with patch.object(docker_backend, 'get_info', return_value=Mock(name="valid")):
                    containers = await docker_backend.list_containers()
                    
                    assert len(containers) == 1


class TestDockerCreateContainer:
    """Test Docker container creation (_create_container method)."""
    
    @pytest.mark.asyncio
    async def test_create_container_with_command(self, docker_backend):
        """Test creating container with custom command."""
        config = ContainerConfig(
            name="test-cmd",
            distro="debian",
            arch="amd64",
            codename="bookworm",
            container_type="docker"
        )
        
        with patch.object(docker_backend, '_run_docker', return_value=(0, "container_id", "")) as mock_run:
            await docker_backend._create_container(
                "test-cmd",
                config,
                ["/bin/bash"]
            )
            
            call_args = mock_run.call_args[0][0]
            assert "run" in call_args
            assert "-d" in call_args
            assert "--name" in call_args
            assert "test-cmd" in call_args
            assert "debian:bookworm" in call_args
            assert "/bin/bash" in call_args
    
    @pytest.mark.asyncio
    async def test_create_container_default_command(self, docker_backend):
        """Test creating container with default sleep command."""
        config = ContainerConfig(
            name="test-default-cmd",
            distro="alpine",
            arch="amd64",
            container_type="docker"
        )
        
        with patch.object(docker_backend, '_run_docker', return_value=(0, "container_id", "")) as mock_run:
            await docker_backend._create_container(
                "test-default-cmd",
                config,
                None
            )
            
            call_args = mock_run.call_args[0][0]
            assert "/bin/bash" in call_args
            assert "while true; do sleep 3600; done" in " ".join(call_args)
    
    @pytest.mark.asyncio
    async def test_create_container_labels(self, docker_backend):
        """Test container is created with proper labels."""
        config = ContainerConfig(
            name="test-labels",
            distro="ubuntu",
            arch="arm64",
            container_type="docker"
        )
        
        with patch.object(docker_backend, '_run_docker', return_value=(0, "container_id", "")) as mock_run:
            await docker_backend._create_container("test-labels", config, None)
            
            call_args = mock_run.call_args[0][0]
            assert "--label" in call_args
            assert "tmoe=true" in call_args
            assert "tmoe.distro=ubuntu" in call_args
            assert "tmoe.arch=arm64" in call_args
    
    @pytest.mark.asyncio
    async def test_create_container_environment_variables(self, docker_backend):
        """Test container is created with TMOE environment variables."""
        config = ContainerConfig(
            name="test-env",
            distro="fedora",
            container_type="docker"
        )
        
        with patch.object(docker_backend, '_run_docker', return_value=(0, "container_id", "")) as mock_run:
            await docker_backend._create_container("test-env", config, None)
            
            call_args = mock_run.call_args[0][0]
            assert "-e" in call_args
            assert "TMOE_DOCKER=true" in call_args
            assert "TMOE_CHROOT=true" in call_args
            assert "TMOE_CONTAINER_NAME=test-env" in call_args
    
    @pytest.mark.asyncio
    async def test_create_container_failure(self, docker_backend):
        """Test container creation failure handling."""
        config = ContainerConfig(
            name="test-fail",
            distro="debian",
            container_type="docker"
        )
        
        with patch.object(docker_backend, '_run_docker', return_value=(1, "", "image not found")):
            with pytest.raises(RuntimeError, match="Failed to create"):
                await docker_backend._create_container("test-fail", config, None)


class TestDockerAllDistros:
    """Test Docker backend with all supported distributions."""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("distro,expected_image", [
        ("debian", "debian"),
        ("ubuntu", "ubuntu"),
        ("alpine", "alpine"),
        ("arch", "archlinux"),
        ("fedora", "fedora"),
        ("centos", "centos"),
        ("opensuse", "opensuse/leap"),
        ("kali", "kalilinux/kali-rolling"),
    ])
    async def test_all_distro_images(self, docker_backend, distro, expected_image):
        """Test that all distributions map to correct Docker images."""
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, 'exists', return_value=False):
                with patch.object(docker_backend, 'save_container_config'):
                    with patch.object(docker_backend, '_run_docker', return_value=(0, "", "")):
                        config = await docker_backend.create(
                            name=f"test-{distro}",
                            distro=distro
                        )
                        
                        assert config.distro == distro
                        assert docker_backend.DISTRO_IMAGES.get(distro) == expected_image


class TestDockerEdgeCases:
    """Test Docker backend edge cases."""
    
    @pytest.mark.asyncio
    async def test_start_docker_not_available(self, docker_backend):
        """Test start raises error when Docker is not available."""
        with patch.object(docker_backend, 'is_available', False):
            with pytest.raises(RuntimeError, match="not available"):
                await docker_backend.start("test-container")
    
    @pytest.mark.asyncio
    async def test_unknown_distro_uses_direct_name(self, docker_backend):
        """Test unknown distro uses name directly as image."""
        with patch.object(docker_backend, 'is_available', True):
            with patch.object(docker_backend, 'exists', return_value=False):
                with patch.object(docker_backend, 'save_container_config'):
                    config = await docker_backend.create(
                        name="test-unknown",
                        distro="customlinux"
                    )
                    
                    # Unknown distro should fallback to using the name directly
                    assert config.distro == "customlinux"
    
    def test_cached_docker_availability(self, docker_backend):
        """Test that Docker availability is cached."""
        with patch('shutil.which') as mock_which:
            mock_which.return_value = '/usr/bin/docker'
            
            # First call should check
            docker_backend._docker_available = None
            _ = docker_backend.is_available
            
            # Second call should use cached value
            _ = docker_backend.is_available
            
            # shutil.which should only be called once
            mock_which.assert_called_once()
