"""Container management for TMOE.

Provides backends for different container types:
- Proot: User-mode containers (no root required)
- Chroot: Traditional chroot containers (requires root)
- Nspawn: Systemd-nspawn containers
- Docker: Docker containers
"""

from tmoe.container.base import ContainerBackend, ContainerStatus
from tmoe.container.proot import ProotBackend

__all__ = [
    "ContainerBackend",
    "ContainerStatus",
    "ProotBackend",
]
