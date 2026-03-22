"""Constants for TMOE.

This module contains all the constant values used throughout the application,
including supported architectures, distributions, and default configurations.
"""

from __future__ import annotations

from enum import Enum
from typing import Final


class ContainerType(str, Enum):
    """Supported container backend types."""
    PROOT = "proot"
    CHROOT = "chroot"
    NSPAWN = "nspawn"
    DOCKER = "docker"


class DesktopEnvironment(str, Enum):
    """Supported desktop environments."""
    XFCE = "xfce"
    LXDE = "lxde"
    LXQT = "lxqt"
    MATE = "mate"
    KDE = "kde"
    GNOME = "gnome"
    CINNAMON = "cinnamon"
    BUDGIE = "budgie"
    DEEPIN = "deepin"
    UKUI = "ukui"


class VncServer(str, Enum):
    """Supported VNC servers."""
    TIGER = "tiger"
    TIGHT = "tight"


# Supported architectures
SUPPORTED_ARCHITECTURES: Final[list[str]] = [
    "arm64",    # ARM 64-bit (aarch64)
    "amd64",    # x86 64-bit (x86_64)
    "armhf",    # ARM 32-bit hard float (armv7)
    "armel",    # ARM 32-bit soft float
    "i386",     # x86 32-bit
    "mips64el", # MIPS 64-bit little endian
    "mipsel",   # MIPS 32-bit little endian
    "ppc64el",  # PowerPC 64-bit little endian
    "s390x",    # IBM Z
    "riscv64",  # RISC-V 64-bit
]

# Architecture mappings (various names -> normalized)
ARCH_MAPPINGS: Final[dict[str, str]] = {
    # ARM 64-bit
    "aarch64": "arm64",
    "arm64": "arm64",
    "armv8": "arm64",
    # x86 64-bit
    "x86_64": "amd64",
    "x86-64": "amd64",
    "amd64": "amd64",
    # ARM 32-bit
    "armv7l": "armhf",
    "armv7": "armhf",
    "armhf": "armhf",
    "arm": "armhf",
    "armel": "armel",
    # x86 32-bit
    "i686": "i386",
    "i586": "i386",
    "i486": "i386",
    "i386": "i386",
    "x86": "i386",
    # MIPS
    "mips64": "mips64el",
    "mips64el": "mips64el",
    "mips": "mipsel",
    "mipsel": "mipsel",
    # PowerPC
    "ppc64le": "ppc64el",
    "powerpc64le": "ppc64el",
    # RISC-V
    "riscv": "riscv64",
    "riscv64": "riscv64",
    "rv64": "riscv64",
    # IBM Z
    "s390": "s390x",
    "s390x": "s390x",
}

# QEMU architecture mappings
QEMU_ARCH_MAPPINGS: Final[dict[str, str]] = {
    "arm64": "aarch64",
    "amd64": "x86_64",
    "armhf": "arm",
    "armel": "armeb",
    "i386": "i386",
    "mips64el": "mips64el",
    "mipsel": "mipsel",
    "ppc64el": "ppc64le",
    "s390x": "s390x",
    "riscv64": "riscv64",
}

# Supported distributions
SUPPORTED_DISTROS: Final[dict[str, list[str]]] = {
    "debian": ["sid", "testing", "stable", "oldstable", "bookworm", "bullseye"],
    "ubuntu": ["noble", "jammy", "focal", "bionic"],
    "kali": ["rolling"],
    "arch": ["latest"],
    "manjaro": ["latest"],
    "alpine": ["edge", "latest", "3.19", "3.18"],
    "fedora": ["rawhide", "40", "39", "38"],
    "centos": ["stream9", "stream8"],
    "opensuse": ["tumbleweed", "leap"],
    "gentoo": ["latest"],
    "void": ["latest"],
    "openeuler": ["latest"],
    "oracle": ["9", "8"],
    "amazon": ["2023", "2"],
}

# Default locales
DEFAULT_LOCALES: Final[dict[str, str]] = {
    "zh_CN": "zh_CN.UTF-8",
    "zh_TW": "zh_TW.UTF-8",
    "zh_HK": "zh_HK.UTF-8",
    "en_US": "en_US.UTF-8",
    "en_GB": "en_GB.UTF-8",
    "ja_JP": "ja_JP.UTF-8",
    "ko_KR": "ko_KR.UTF-8",
    "de_DE": "de_DE.UTF-8",
    "fr_FR": "fr_FR.UTF-8",
    "ru_RU": "ru_RU.UTF-8",
}

# Mirror sites for China
CHINA_MIRRORS: Final[dict[str, str]] = {
    "tsinghua": "mirrors.tuna.tsinghua.edu.cn",
    "ustc": "mirrors.ustc.edu.cn",
    "bfsu": "mirrors.bfsu.edu.cn",
    "sjtu": "mirror.sjtu.edu.cn",
    "aliyun": "mirrors.aliyun.com",
    "tencent": "mirrors.cloud.tencent.com",
    "huawei": "mirrors.huaweicloud.com",
    "163": "mirrors.163.com",
}

# Default ports
DEFAULT_PORTS: Final[dict[str, int]] = {
    "vnc_base": 5900,
    "vnc_display": 2,
    "novnc": 36080,
    "pulseaudio": 4713,
}

# File paths
CONTAINER_ENV_FILE: Final[str] = "container.env"
CONTAINER_LOGIN_FILE: Final[str] = "login"
CONTAINER_ENTRYPOINT_FILE: Final[str] = "entrypoint"

# TMOE specific paths
TMOE_ENV_DIR: Final[str] = "environment"
TMOE_BIN_DIR: Final[str] = "bin"
