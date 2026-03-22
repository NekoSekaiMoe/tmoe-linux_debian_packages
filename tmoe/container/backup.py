"""Container backup and restore for TMOE.

Provides backup and restore functionality for containers using tar archives.
"""

from __future__ import annotations

import asyncio
import gzip
import lzma
import shutil
import tarfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from tmoe.container.base import ContainerInfo, ContainerBackend


@dataclass
class BackupInfo:
    """Backup information."""
    path: Path
    name: str
    container_name: str
    created_at: datetime
    size_bytes: int
    compression: str
    
    @property
    def size_human(self) -> str:
        """Human-readable size."""
        size = self.size_bytes
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"


class ContainerBackupManager:
    """Manager for container backup and restore.
    
    Creates compressed tar archives of container rootfs.
    Supports multiple compression formats.
    
    Example:
        >>> manager = ContainerBackupManager(backend)
        >>> backup = await manager.backup_container("my-container")
        >>> await manager.restore_container(backup.path, "restored-container")
    """
    
    def __init__(
        self,
        backend: ContainerBackend,
        backup_dir: Path | None = None,
    ) -> None:
        self.backend = backend
        
        if backup_dir is None:
            from tmoe.core.platform import PlatformInfo
            platform = PlatformInfo()
            self.backup_dir = platform.data_dir / "backups"
        else:
            self.backup_dir = backup_dir
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._progress_callback: Callable[[str, int, int], None] | None = None
    
    def set_progress_callback(
        self,
        callback: Callable[[str, int, int], None],
    ) -> None:
        """Set callback for progress updates."""
        self._progress_callback = callback
    
    def _report_progress(self, message: str, current: int, total: int) -> None:
        """Report progress."""
        if self._progress_callback:
            self._progress_callback(message, current, total)
    
    def _generate_backup_name(self, container_name: str) -> str:
        """Generate backup file name."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{container_name}_{timestamp}"
    
    async def backup_container(
        self,
        container_name: str,
        compression: str = "xz",
    ) -> BackupInfo:
        """Create a backup of a container.
        
        Args:
            container_name: Name of container to backup
            compression: Compression type ('xz', 'gz', 'bz2', 'none')
            
        Returns:
            Backup info
        """
        # Get container info
        info = await self.backend.get_info(container_name)
        if not info:
            raise ValueError(f"Container '{container_name}' not found")
        
        if not info.config.rootfs_path:
            raise ValueError(f"Container '{container_name}' has no rootfs")
        
        rootfs_path = info.config.rootfs_path
        
        # Check if container is running
        if info.status.name == "RUNNING":
            raise RuntimeError(
                f"Container '{container_name}' is running. "
                "Please stop it before backup."
            )
        
        # Generate backup filename
        backup_name = self._generate_backup_name(container_name)
        
        # Determine file extension
        ext_map = {
            "xz": ".tar.xz",
            "gz": ".tar.gz",
            "bz2": ".tar.bz2",
            "none": ".tar",
        }
        ext = ext_map.get(compression, ".tar.xz")
        backup_path = self.backup_dir / f"{backup_name}{ext}"
        
        self._report_progress(f"Creating backup of {container_name}...", 0, 0)
        
        # Create tar archive
        await self._create_tar_archive(
            rootfs_path,
            backup_path,
            compression,
        )
        
        # Get backup size
        size = backup_path.stat().st_size
        
        self._report_progress(f"Backup created: {backup_path.name}", size, size)
        
        return BackupInfo(
            path=backup_path,
            name=backup_path.name,
            container_name=container_name,
            created_at=datetime.now(),
            size_bytes=size,
            compression=compression,
        )
    
    async def _create_tar_archive(
        self,
        source_path: Path,
        dest_path: Path,
        compression: str,
    ) -> None:
        """Create compressed tar archive.
        
        Args:
            source_path: Path to archive
            dest_path: Destination tar file
            compression: Compression type
        """
        # Map compression types to tarfile modes
        mode_map = {
            "xz": "w:xz",
            "gz": "w:gz",
            "bz2": "w:bz2",
            "none": "w",
        }
        mode = mode_map.get(compression, "w:xz")
        
        # Get total file count for progress
        total_files = sum(1 for _ in source_path.rglob("*") if _.is_file())
        processed = 0
        
        def progress_filter(member: tarfile.TarInfo) -> tarfile.TarInfo:
            nonlocal processed
            processed += 1
            if processed % 100 == 0:
                self._report_progress(
                    f"Archiving files...",
                    processed,
                    total_files,
                )
            return member
        
        # Create tar archive
        with tarfile.open(dest_path, mode) as tar:
            tar.add(source_path, arcname="rootfs", filter=progress_filter)
    
    async def restore_container(
        self,
        backup_path: Path,
        new_name: str | None = None,
    ) -> Path:
        """Restore a container from backup.
        
        Args:
            backup_path: Path to backup file
            new_name: New container name (default: original name)
            
        Returns:
            Path to restored container rootfs
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")
        
        # Determine container name from backup filename
        if new_name is None:
            # Extract name from backup_20240101_120000.tar.xz
            new_name = backup_path.stem.split("_")[0]
        
        # Check if container already exists
        if await self.backend.exists(new_name):
            raise ValueError(f"Container '{new_name}' already exists")
        
        # Get container path
        rootfs_path = self.backend.get_container_path(new_name)
        
        if rootfs_path.exists():
            raise ValueError(f"Path already exists: {rootfs_path}")
        
        self._report_progress(f"Restoring {new_name}...", 0, 0)
        
        # Extract tar archive
        await self._extract_tar_archive(backup_path, rootfs_path)
        
        self._report_progress(f"Restored {new_name}", 100, 100)
        
        return rootfs_path
    
    async def _extract_tar_archive(
        self,
        tar_path: Path,
        dest_path: Path,
    ) -> None:
        """Extract tar archive.
        
        Args:
            tar_path: Path to tar file
            dest_path: Destination directory
        """
        dest_path.mkdir(parents=True, exist_ok=True)
        
        # Detect compression from extension
        if tar_path.suffix == ".xz" or tar_path.name.endswith(".tar.xz"):
            mode = "r:xz"
        elif tar_path.suffix == ".gz" or tar_path.name.endswith(".tar.gz"):
            mode = "r:gz"
        elif tar_path.suffix == ".bz2" or tar_path.name.endswith(".tar.bz2"):
            mode = "r:bz2"
        else:
            mode = "r"
        
        with tarfile.open(tar_path, mode) as tar:
            # Filter for security (Python 3.12+)
            if hasattr(tarfile, 'data_filter'):
                tar.extraction_filter = getattr(tarfile, 'data_filter', None)
            tar.extractall(path=dest_path.parent)
            
            # If extracted as 'rootfs' directory, rename to container name
            rootfs_dir = dest_path.parent / "rootfs"
            if rootfs_dir.exists() and not dest_path.exists():
                rootfs_dir.rename(dest_path)
    
    def list_backups(self, container_name: str | None = None) -> list[BackupInfo]:
        """List available backups.
        
        Args:
            container_name: Filter by container name (optional)
            
        Returns:
            List of backup info
        """
        backups = []
        
        for backup_file in self.backup_dir.iterdir():
            if not backup_file.is_file():
                continue
            
            # Parse filename
            name = backup_file.stem
            if container_name and not name.startswith(container_name):
                continue
            
            # Try to parse timestamp
            try:
                # Format: container_20240101_120000
                parts = name.split("_")
                if len(parts) >= 3:
                    container = parts[0]
                    timestamp = datetime.strptime(
                        f"{parts[1]}_{parts[2]}",
                        "%Y%m%d_%H%M%S"
                    )
                else:
                    container = name
                    timestamp = datetime.fromtimestamp(
                        backup_file.stat().st_mtime
                    )
            except ValueError:
                container = name
                timestamp = datetime.fromtimestamp(
                    backup_file.stat().st_mtime
                )
            
            # Determine compression
            if backup_file.name.endswith(".tar.xz"):
                compression = "xz"
            elif backup_file.name.endswith(".tar.gz"):
                compression = "gz"
            elif backup_file.name.endswith(".tar.bz2"):
                compression = "bz2"
            else:
                compression = "none"
            
            backups.append(BackupInfo(
                path=backup_file,
                name=backup_file.name,
                container_name=container,
                created_at=timestamp,
                size_bytes=backup_file.stat().st_size,
                compression=compression,
            ))
        
        # Sort by creation time (newest first)
        return sorted(backups, key=lambda x: x.created_at, reverse=True)
    
    async def delete_backup(self, backup_path: Path) -> None:
        """Delete a backup.
        
        Args:
            backup_path: Path to backup file
        """
        if backup_path.exists():
            backup_path.unlink()
