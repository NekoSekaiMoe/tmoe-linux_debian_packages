"""Backup and restore functionality for TMOE containers.

This module provides backup and restore functionality for containers,
matching the original TMOE shell implementation.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from tmoe.core.config import get_config
from tmoe.core.platform import PlatformInfo

if TYPE_CHECKING:
    from tmoe.container.base import ContainerBackend


@dataclass
class BackupInfo:
    """Information about a backup."""
    name: str
    container_name: str
    container_type: str
    distro: str
    arch: str
    size: int
    created_at: datetime
    compression: str  # "zst" or "xz"
    path: Path


class BackupManager:
    """Manager for container backup and restore.
    
    Provides functionality to:
    - Create compressed backups of containers
    - Restore containers from backups
    - List available backups
    - Clean up before backup (remove cache, logs, etc.)
    
    Example:
        >>> manager = BackupManager()
        >>> backup_path = await manager.backup_container("my-debian")
        >>> await manager.restore_container(backup_path)
    """
    
    def __init__(self, platform: PlatformInfo | None = None) -> None:
        self.platform = platform or PlatformInfo()
        self.config = get_config()
        self._backup_dir = self.platform.data_dir / "backups"
        self._backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_backup_path(
        self,
        container_name: str,
        compression: str = "zst",
    ) -> Path:
        """Generate backup file path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{container_name}_{timestamp}_rootfs_bak.tar.{compression}"
        return self._backup_dir / filename
    
    async def _clean_container_before_backup(self, rootfs_path: Path) -> None:
        """Clean up container before backup (原版清理逻辑)."""
        if not rootfs_path.exists():
            return
        
        cleanup_commands = [
            # Clean APT cache
            ["rm", "-rf", str(rootfs_path / "var" / "cache" / "apt" / "archives" / "*")],
            ["rm", "-rf", str(rootfs_path / "var" / "lib" / "apt" / "lists" / "*")],
            # Clean temporary files
            ["rm", "-rf", str(rootfs_path / "tmp" / "*")],
            ["rm", "-rf", str(rootfs_path / "var" / "tmp" / "*")],
            # Clean command history
            ["rm", "-f", str(rootfs_path / "root" / ".bash_history")],
            ["rm", "-f", str(rootfs_path / "root" / ".zsh_history")],
        ]
        
        for cmd in cleanup_commands:
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await proc.wait()
            except Exception:
                pass
    
    async def backup_container(
        self,
        container_name: str,
        backend: ContainerBackend,
        compression: str = "zst",
        clean_first: bool = True,
    ) -> BackupInfo:
        """Create a backup of a container (原版备份逻辑)."""
        info = await backend.get_info(container_name)
        if not info:
            raise ValueError(f"Container '{container_name}' not found")
        
        config = info.config
        rootfs_path = config.rootfs_path
        
        if not rootfs_path or not rootfs_path.exists():
            raise ValueError(f"Container '{container_name}' rootfs not found")
        
        if clean_first:
            await self._clean_container_before_backup(rootfs_path)
        
        backup_path = self._get_backup_path(container_name, compression)
        
        # Create backup
        if compression == "zst":
            cmd = [
                "tar", "--use-compress-program", "zstd",
                "-Ppcvf", str(backup_path),
                "--exclude", str(rootfs_path / "media" / "sd"),
                "--exclude", str(rootfs_path / "media" / "tf"),
                str(rootfs_path),
            ]
        else:
            cmd = [
                "tar", "-PJpcvf", str(backup_path),
                "--exclude", str(rootfs_path / "media" / "sd"),
                "--exclude", str(rootfs_path / "media" / "tf"),
                str(rootfs_path),
            ]
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise RuntimeError(f"Backup failed: {stderr.decode()}")
        
        size = backup_path.stat().st_size
        
        backup_info = BackupInfo(
            name=backup_path.stem,
            container_name=container_name,
            container_type=config.container_type,
            distro=config.distro,
            arch=config.arch,
            size=size,
            created_at=datetime.now(),
            compression=compression,
            path=backup_path,
        )
        
        await self._save_backup_metadata(backup_info)
        
        return backup_info
    
    async def _save_backup_metadata(self, backup_info: BackupInfo) -> None:
        """Save backup metadata to JSON file."""
        metadata_path = backup_info.path.with_suffix(".json")
        metadata = {
            "name": backup_info.name,
            "container_name": backup_info.container_name,
            "container_type": backup_info.container_type,
            "distro": backup_info.distro,
            "arch": backup_info.arch,
            "size": backup_info.size,
            "created_at": backup_info.created_at.isoformat(),
            "compression": backup_info.compression,
        }
        metadata_path.write_text(json.dumps(metadata, indent=2))
    
    async def restore_container(
        self,
        backup_path: Path,
        backend: ContainerBackend,
        new_name: str | None = None,
    ) -> str:
        """Restore a container from backup (原版恢复逻辑)."""
        if not backup_path.exists():
            raise ValueError(f"Backup file not found: {backup_path}")
        
        metadata_path = backup_path.with_suffix(".json")
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text())
            container_name = new_name or metadata["container_name"]
            container_type = metadata["container_type"]
            distro = metadata["distro"]
            arch = metadata["arch"]
        else:
            container_name = new_name or backup_path.stem.split("_")[0]
            container_type = "proot"
            distro = "debian"
            arch = self.platform.normalized_arch
        
        if await backend.exists(container_name):
            raise ValueError(f"Container '{container_name}' already exists")
        
        container_path = backend.get_container_path(container_name)
        container_path.mkdir(parents=True, exist_ok=True)
        
        compression = backup_path.suffix.replace(".", "")
        
        if compression == "zst":
            cmd = [
                "tar", "--use-compress-program", "zstd",
                "-Ppxvf", str(backup_path),
                "-C", str(container_path.parent),
            ]
        elif compression in ("xz", "gz"):
            cmd = [
                "tar", f"-Pp{compression[0]}vf", str(backup_path),
                "-C", str(container_path.parent),
            ]
        else:
            raise ValueError(f"Unsupported compression: {compression}")
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise RuntimeError(f"Restore failed: {stderr.decode()}")
        
        from tmoe.core.config import ContainerConfig
        
        config = ContainerConfig(
            name=container_name,
            distro=distro,
            arch=arch,
            rootfs_path=container_path,
            container_type=container_type,
        )
        
        backend.save_container_config(config)
        
        return container_name
    
    def list_backups(self) -> list[BackupInfo]:
        """List available backups."""
        backups: list[BackupInfo] = []
        
        for backup_file in self._backup_dir.glob("*.tar.*"):
            metadata_path = backup_file.with_suffix(".json")
            
            if metadata_path.exists():
                try:
                    metadata = json.loads(metadata_path.read_text())
                    backups.append(BackupInfo(
                        name=metadata["name"],
                        container_name=metadata["container_name"],
                        container_type=metadata["container_type"],
                        distro=metadata["distro"],
                        arch=metadata["arch"],
                        size=metadata["size"],
                        created_at=datetime.fromisoformat(metadata["created_at"]),
                        compression=metadata["compression"],
                        path=backup_file,
                    ))
                except Exception:
                    pass
        
        backups.sort(key=lambda x: x.created_at, reverse=True)
        return backups
    
    async def delete_backup(self, backup_path: Path) -> bool:
        """Delete a backup."""
        try:
            backup_path.unlink(missing_ok=True)
            metadata_path = backup_path.with_suffix(".json")
            metadata_path.unlink(missing_ok=True)
            return True
        except Exception:
            return False
    
    def format_size(self, size: int) -> str:
        """Format size in human readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"