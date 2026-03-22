"""Docker container backend for TMOE.

Manages Docker containers alongside proot/chroot containers.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import TYPE_CHECKING

from tmoe.container.base import ContainerBackend, ContainerInfo, ContainerStatus
from tmoe.core.config import ContainerConfig
from tmoe.core.platform import PlatformInfo

if TYPE_CHECKING:
    from collections.abc import Sequence


class DockerBackend(ContainerBackend):
    """Docker container backend implementation.
    
    Manages Docker containers using the Docker CLI.
    Provides similar interface to proot/chroot backends.
    
    Example:
        >>> backend = DockerBackend()
        >>> config = await backend.create("my-debian", "debian")
        >>> await backend.start("my-debian")
    """
    
    # Docker Hub images for distributions
    DISTRO_IMAGES: dict[str, str] = {
        "debian": "debian",
        "ubuntu": "ubuntu",
        "alpine": "alpine",
        "arch": "archlinux",
        "fedora": "fedora",
        "centos": "centos",
        "opensuse": "opensuse/leap",
        "kali": "kalilinux/kali-rolling",
    }
    
    def __init__(self, platform: PlatformInfo | None = None) -> None:
        super().__init__(platform)
        self._docker_available: bool | None = None
    
    @property
    def backend_type(self) -> str:
        return "docker"
    
    @property
    def requires_root(self) -> bool:
        return False  # Docker can run as non-root with proper group
    
    @property
    def is_available(self) -> bool:
        """Check if Docker is available."""
        if self._docker_available is None:
            import shutil
            self._docker_available = shutil.which("docker") is not None
        return self._docker_available
    
    async def _run_docker(
        self,
        args: list[str],
    ) -> tuple[int, str, str]:
        """Run docker command.
        
        Args:
            args: Docker arguments
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        cmd = ["docker"] + args
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await proc.communicate()
        return (
            proc.returncode or 0,
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
        )
    
    async def list_containers(self) -> list[ContainerInfo]:
        """List Docker containers managed by TMOE."""
        if not self.is_available:
            return []
        
        # List containers with tmoe label
        exit_code, stdout, stderr = await self._run_docker([
            "ps", "-a",
            "--filter", "label=tmoe=true",
            "--format", "{{json .}}",
        ])
        
        if exit_code != 0:
            return []
        
        containers = []
        for line in stdout.strip().split("\n"):
            if not line:
                continue
            
            try:
                data = json.loads(line)
                name = data.get("Names", "")
                
                # Get full info
                info = await self.get_info(name)
                if info:
                    containers.append(info)
            except json.JSONDecodeError:
                continue
        
        return containers
    
    async def exists(self, name: str) -> bool:
        """Check if a Docker container exists."""
        if not self.is_available:
            return False
        
        exit_code, _, _ = await self._run_docker(["inspect", name])
        return exit_code == 0
    
    async def get_info(self, name: str) -> ContainerInfo | None:
        """Get information about a Docker container."""
        if not self.is_available:
            return None
        
        exit_code, stdout, _ = await self._run_docker([
            "inspect", "--format", "{{json .}}", name
        ])
        
        if exit_code != 0:
            return None
        
        try:
            data = json.loads(stdout)
            config = data.get("Config", {})
            state = data.get("State", {})
            
            # Determine status
            if state.get("Running", False):
                status = ContainerStatus.RUNNING
            elif state.get("Paused", False):
                status = ContainerStatus.PAUSED
            else:
                status = ContainerStatus.STOPPED
            
            # Get labels
            labels = config.get("Labels", {}) or {}
            
            # Create container config
            container_config = ContainerConfig(
                name=name,
                distro=labels.get("tmoe.distro", "unknown"),
                arch=labels.get("tmoe.arch", self.platform.normalized_arch),
                container_type="docker",
                user="root",
                uid=0,
                gid=0,
                home="/root",
            )
            
            return ContainerInfo(
                name=name,
                config=container_config,
                status=status,
                pid=state.get("Pid") if state.get("Running") else None,
            )
        except json.JSONDecodeError:
            return None
    
    async def create(
        self,
        name: str,
        distro: str,
        arch: str | None = None,
        codename: str | None = None,
    ) -> ContainerConfig:
        """Create a new Docker container configuration.
        
        Note: For Docker, 'create' just prepares the config.
        The actual container is created on first start.
        """
        if not self.is_available:
            raise RuntimeError("Docker is not available")
        
        if await self.exists(name):
            raise ValueError(f"Container '{name}' already exists")
        
        arch = arch or self.platform.normalized_arch
        
        # Get Docker image
        image = self.DISTRO_IMAGES.get(distro, distro)
        tag = codename or "latest"
        
        config = ContainerConfig(
            name=name,
            distro=distro,
            arch=arch,
            codename=codename or "latest",
            container_type="docker",
            user="root",
            uid=0,
            gid=0,
            home="/root",
        )
        
        # Save config
        self.save_container_config(config)
        
        return config
    
    async def start(
        self,
        name: str,
        command: list[str] | None = None,
    ) -> None:
        """Start a Docker container."""
        if not self.is_available:
            raise RuntimeError("Docker is not available")
        
        config = self.load_container_config(name)
        if not config:
            raise ValueError(f"Container '{name}' not found")
        
        # Check if container exists in Docker
        if not await self.exists(name):
            # Create container first
            await self._create_container(name, config, command)
        else:
            # Start existing container
            exit_code, stdout, stderr = await self._run_docker(["start", name])
            if exit_code != 0:
                raise RuntimeError(f"Failed to start container: {stderr}")
    
    async def _create_container(
        self,
        name: str,
        config: ContainerConfig,
        command: list[str] | None,
    ) -> None:
        """Create Docker container."""
        # Get image
        image = self.DISTRO_IMAGES.get(config.distro, config.distro)
        tag = config.codename or "latest"
        
        # Build docker run command
        docker_args = [
            "run", "-d",
            "--name", name,
            "--label", "tmoe=true",
            "--label", f"tmoe.distro={config.distro}",
            "--label", f"tmoe.arch={config.arch}",
            "-e", "TMOE_DOCKER=true",
            "-e", "TMOE_CHROOT=true",
            "-e", f"TMOE_CONTAINER_NAME={name}",
        ]
        
        # Add volume mounts
        docker_args.extend([
            "-v", f"{name}_data:/data",
        ])
        
        # Add image
        docker_args.append(f"{image}:{tag}")
        
        # Add command if specified
        if command:
            docker_args.extend(command)
        else:
            docker_args.extend(["/bin/bash", "-c", "while true; do sleep 3600; done"])
        
        exit_code, stdout, stderr = await self._run_docker(docker_args)
        if exit_code != 0:
            raise RuntimeError(f"Failed to create container: {stderr}")
    
    async def stop(self, name: str) -> None:
        """Stop a Docker container."""
        if not self.is_available:
            return
        
        await self._run_docker(["stop", name])
    
    async def remove(self, name: str, force: bool = False) -> None:
        """Remove a Docker container."""
        if not self.is_available:
            return
        
        if force:
            await self._run_docker(["rm", "-f", name])
        else:
            await self._run_docker(["rm", name])
        
        # Remove config
        config_path = self.get_container_config_path(name)
        if config_path.exists():
            config_path.unlink()
    
    async def exec(
        self,
        name: str,
        command: list[str],
    ) -> tuple[int, str, str]:
        """Execute a command in a Docker container."""
        if not self.is_available:
            raise RuntimeError("Docker is not available")
        
        docker_args = ["exec", name] + command
        return await self._run_docker(docker_args)
