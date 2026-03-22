"""Base classes for container management.

This module defines the abstract base class for all container backends
and common data structures used across backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any

from tmoe.core.config import ContainerConfig, get_config
from tmoe.core.platform import PlatformInfo


class ContainerStatus(Enum):
    """Container runtime status."""
    STOPPED = auto()
    RUNNING = auto()
    PAUSED = auto()
    UNKNOWN = auto()


@dataclass
class ContainerInfo:
    """Information about a container."""
    name: str
    config: ContainerConfig
    status: ContainerStatus = ContainerStatus.STOPPED
    pid: int | None = None
    created_at: str | None = None
    size_bytes: int | None = None
    
    @property
    def size_human(self) -> str:
        """Return human-readable size."""
        if self.size_bytes is None:
            return "Unknown"
        
        size = self.size_bytes
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"


class ContainerBackend(ABC):
    """Abstract base class for container backends.
    
    All container backends (proot, chroot, nspawn, docker) must implement
    this interface to provide a consistent API.
    
    Example:
        >>> from tmoe.container.proot import ProotBackend
        >>> backend = ProotBackend()
        >>> containers = await backend.list_containers()
        >>> print(containers[0].name)
        'debian-arm64'
    """
    
    def __init__(self, platform: PlatformInfo | None = None) -> None:
        self.platform = platform or PlatformInfo()
        self.config = get_config()
    
    @property
    @abstractmethod
    def backend_type(self) -> str:
        """Return the backend type identifier."""
        pass
    
    @property
    @abstractmethod
    def requires_root(self) -> bool:
        """Whether this backend requires root privileges."""
        pass
    
    @abstractmethod
    async def list_containers(self) -> list[ContainerInfo]:
        """List all containers managed by this backend.
        
        Returns:
            List of ContainerInfo objects.
        """
        pass
    
    @abstractmethod
    async def exists(self, name: str) -> bool:
        """Check if a container exists.
        
        Args:
            name: Container name.
            
        Returns:
            True if container exists.
        """
        pass
    
    @abstractmethod
    async def get_info(self, name: str) -> ContainerInfo | None:
        """Get information about a container.
        
        Args:
            name: Container name.
            
        Returns:
            ContainerInfo if container exists, None otherwise.
        """
        pass
    
    @abstractmethod
    async def create(
        self,
        name: str,
        distro: str,
        arch: str | None = None,
        codename: str | None = None,
    ) -> ContainerConfig:
        """Create a new container.
        
        Args:
            name: Container name.
            distro: Linux distribution.
            arch: Architecture (defaults to host arch).
            codename: Distribution codename.
            
        Returns:
            ContainerConfig for the new container.
        """
        pass
    
    @abstractmethod
    async def start(
        self,
        name: str,
        command: list[str] | None = None,
    ) -> None:
        """Start a container.
        
        Args:
            name: Container name.
            command: Command to run (default: shell).
        """
        pass
    
    @abstractmethod
    async def stop(self, name: str) -> None:
        """Stop a running container.
        
        Args:
            name: Container name.
        """
        pass
    
    @abstractmethod
    async def remove(self, name: str, force: bool = False) -> None:
        """Remove a container.
        
        Args:
            name: Container name.
            force: Force removal even if running.
        """
        pass
    
    @abstractmethod
    async def exec(
        self,
        name: str,
        command: list[str],
    ) -> tuple[int, str, str]:
        """Execute a command in a container.
        
        Args:
            name: Container name.
            command: Command to execute.
            
        Returns:
            Tuple of (exit_code, stdout, stderr).
        """
        pass
    
    def get_container_path(self, name: str) -> Path:
        """Get the path to a container's rootfs.
        
        Args:
            name: Container name.
            
        Returns:
            Path to container rootfs.
        """
        return self.platform.get_container_dir(self.backend_type) / name
    
    def get_container_config_path(self, name: str) -> Path:
        """Get the path to a container's config file.
        
        Args:
            name: Container name.
            
        Returns:
            Path to config file.
        """
        return self.platform.config_dir / "containers" / f"{name}.json"
    
    def load_container_config(self, name: str) -> ContainerConfig | None:
        """Load container configuration from file.
        
        Args:
            name: Container name.
            
        Returns:
            ContainerConfig if exists, None otherwise.
        """
        config_path = self.get_container_config_path(name)
        if not config_path.exists():
            return None
        
        import json
        data = json.loads(config_path.read_text())
        return ContainerConfig(**data)
    
    def save_container_config(self, config: ContainerConfig) -> None:
        """Save container configuration to file.
        
        Args:
            config: Container configuration.
        """
        config_path = self.get_container_config_path(config.name)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(config.model_dump_json(indent=2))
    
    def check_root(self) -> None:
        """Check if root is required and available.
        
        Raises:
            PermissionError: If root is required but not available.
        """
        if self.requires_root and not self.platform.is_root:
            raise PermissionError(
                f"{self.backend_type} backend requires root privileges"
            )
