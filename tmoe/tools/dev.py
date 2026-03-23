"""Development tools management for TMOE.

Provides installation and management for:
- Programming languages (Rust, Go, Node.js, Python, Java)
- Development environments (Docker, LXD)
- Build tools (CMake, Make, Ninja)
- Version control systems
"""

from __future__ import annotations

import asyncio
import os
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from tmoe.core.platform import PlatformInfo
from tmoe.tools.downloader import DownloadManager, DownloadTask

if TYPE_CHECKING:
    from collections.abc import Callable


class DevToolType(str, Enum):
    """Types of development tools."""
    RUST = "rust"
    GO = "go"
    NODEJS = "nodejs"
    PYTHON = "python"
    JAVA = "java"
    DOCKER = "docker"
    CMAKE = "cmake"
    NINJA = "ninja"
    GIT = "git"


@dataclass
class DevToolInfo:
    """Information about a development tool.
    
    Attributes:
        name: Tool name.
        tool_type: Type of development tool.
        description: Tool description.
        install_methods: Available installation methods.
        check_command: Command to check if tool is installed.
        version_command: Command to get version.
    """
    name: str
    tool_type: DevToolType
    description: str
    install_methods: list[str]
    check_command: str
    version_command: str


class DevToolManager:
    """Manager for development tools.
    
    Provides installation and management for various development
    tools and programming languages.
    
    Example:
        >>> manager = DevToolManager()
        >>> await manager.install_rust()
        >>> await manager.install_nodejs(version="20")
    """
    
    # Tool definitions
    TOOLS: dict[DevToolType, DevToolInfo] = {
        DevToolType.RUST: DevToolInfo(
            name="Rust",
            tool_type=DevToolType.RUST,
            description="Systems programming language",
            install_methods=["rustup"],
            check_command="rustc",
            version_command="rustc --version",
        ),
        DevToolType.GO: DevToolInfo(
            name="Go",
            tool_type=DevToolType.GO,
            description="Google's programming language",
            install_methods=["official", "package_manager"],
            check_command="go",
            version_command="go version",
        ),
        DevToolType.NODEJS: DevToolInfo(
            name="Node.js",
            tool_type=DevToolType.NODEJS,
            description="JavaScript runtime",
            install_methods=["nvm", "nodesource", "package_manager"],
            check_command="node",
            version_command="node --version",
        ),
        DevToolType.PYTHON: DevToolInfo(
            name="Python",
            tool_type=DevToolType.PYTHON,
            description="Programming language",
            install_methods=["pyenv", "package_manager"],
            check_command="python3",
            version_command="python3 --version",
        ),
        DevToolType.JAVA: DevToolInfo(
            name="Java",
            tool_type=DevToolType.JAVA,
            description="Oracle/Sun programming language",
            install_methods=["openjdk", "oracle", "package_manager"],
            check_command="java",
            version_command="java -version",
        ),
        DevToolType.DOCKER: DevToolInfo(
            name="Docker",
            tool_type=DevToolType.DOCKER,
            description="Container platform",
            install_methods=["official", "package_manager"],
            check_command="docker",
            version_command="docker --version",
        ),
        DevToolType.CMAKE: DevToolInfo(
            name="CMake",
            tool_type=DevToolType.CMAKE,
            description="Build system generator",
            install_methods=["official", "package_manager"],
            check_command="cmake",
            version_command="cmake --version",
        ),
        DevToolType.NINJA: DevToolInfo(
            name="Ninja",
            tool_type=DevToolType.NINJA,
            description="Fast build system",
            install_methods=["package_manager", "source"],
            check_command="ninja",
            version_command="ninja --version",
        ),
        DevToolType.GIT: DevToolInfo(
            name="Git",
            tool_type=DevToolType.GIT,
            description="Version control system",
            install_methods=["package_manager", "source"],
            check_command="git",
            version_command="git --version",
        ),
    }
    
    def __init__(self, platform: PlatformInfo | None = None) -> None:
        self.platform = platform or PlatformInfo()
        self.downloader = DownloadManager(platform)
        self._detected_distro: str | None = None
    
    def get_available_tools(self) -> list[DevToolInfo]:
        """Get list of available development tools.
        
        Returns:
            List of available tool information.
        """
        return list(self.TOOLS.values())
    
    def is_installed(self, tool_type: DevToolType) -> bool:
        """Check if a tool is installed.
        
        Args:
            tool_type: Type of tool to check.
        
        Returns:
            True if tool is installed.
        """
        tool = self.TOOLS.get(tool_type)
        if not tool:
            return False
        return shutil.which(tool.check_command) is not None
    
    async def get_version(self, tool_type: DevToolType) -> str | None:
        """Get installed version of a tool.
        
        Args:
            tool_type: Type of tool.
        
        Returns:
            Version string if installed, None otherwise.
        """
        tool = self.TOOLS.get(tool_type)
        if not tool or not self.is_installed(tool_type):
            return None
        
        try:
            proc = await asyncio.create_subprocess_shell(
                tool.version_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            
            # Some tools output version to stderr
            output = stdout.decode().strip() or stderr.decode().strip()
            return output.split("\n")[0] if output else None
        except Exception:
            return None
    
    def detect_distro(self) -> str:
        """Detect Linux distribution.
        
        Returns:
            Distribution name (debian, ubuntu, arch, fedora, etc.)
        """
        if self._detected_distro:
            return self._detected_distro
        
        # Try /etc/os-release
        os_release = Path("/etc/os-release")
        if os_release.exists():
            content = os_release.read_text()
            for line in content.split("\n"):
                if line.startswith("ID="):
                    distro = line.split("=", 1)[1].strip('"')
                    self._detected_distro = distro
                    return distro
        
        # Fallback to checking for specific files
        if Path("/etc/arch-release").exists():
            return "arch"
        elif Path("/etc/fedora-release").exists():
            return "fedora"
        elif Path("/etc/debian_version").exists():
            return "debian"
        
        return "unknown"
    
    def get_package_manager(self) -> str:
        """Get the package manager for current distro.
        
        Returns:
            Package manager command (apt, pacman, dnf, etc.)
        """
        distro = self.detect_distro()
        
        package_managers = {
            "debian": "apt",
            "ubuntu": "apt",
            "arch": "pacman",
            "manjaro": "pacman",
            "fedora": "dnf",
            "centos": "yum",
            "opensuse": "zypper",
            "alpine": "apk",
        }
        
        return package_managers.get(distro, "apt")
    
    async def install_via_package_manager(
        self,
        packages: list[str],
        update_first: bool = True,
    ) -> bool:
        """Install packages using system package manager.
        
        Args:
            packages: List of package names to install.
            update_first: Whether to update package list first.
        
        Returns:
            True if installation succeeded.
        """
        pm = self.get_package_manager()
        
        if update_first:
            update_cmds = {
                "apt": ["apt", "update", "-qq"],
                "pacman": ["pacman", "-Sy", "--noconfirm"],
                "dnf": ["dnf", "check-update"],
                "yum": ["yum", "check-update"],
                "zypper": ["zypper", "refresh"],
                "apk": ["apk", "update"],
            }
            
            if pm in update_cmds:
                proc = await asyncio.create_subprocess_exec(
                    *update_cmds[pm],
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await proc.wait()
        
        # Install packages
        install_cmds = {
            "apt": ["apt", "install", "-y", "-qq"],
            "pacman": ["pacman", "-S", "--noconfirm"],
            "dnf": ["dnf", "install", "-y"],
            "yum": ["yum", "install", "-y"],
            "zypper": ["zypper", "install", "-y"],
            "apk": ["apk", "add"],
        }
        
        if pm not in install_cmds:
            return False
        
        cmd = install_cmds[pm] + packages
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await proc.communicate()
        return proc.returncode == 0
    
    async def install_rust(self, method: str = "rustup") -> bool:
        """Install Rust programming language.
        
        Args:
            method: Installation method (rustup).
        
        Returns:
            True if installation succeeded.
        """
        if self.is_installed(DevToolType.RUST):
            return True
        
        if method == "rustup":
            # Download and run rustup-init
            rustup_url = "https://sh.rustup.rs"
            script_path = Path("/tmp/rustup-init.sh")
            
            task = DownloadTask(
                url=rustup_url,
                dest=script_path,
                backend="httpx",
            )
            await self.downloader.download(task)
            
            # Make executable and run
            script_path.chmod(0o755)
            
            env = os.environ.copy()
            env["RUSTUP_HOME"] = str(Path.home() / ".rustup")
            env["CARGO_HOME"] = str(Path.home() / ".cargo")
            
            proc = await asyncio.create_subprocess_exec(
                "sh", str(script_path), "-y", "--default-toolchain", "stable",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            
            stdout, stderr = await proc.communicate()
            
            # Cleanup
            script_path.unlink(missing_ok=True)
            
            return proc.returncode == 0
        
        return False
    
    async def install_go(self, version: str | None = None) -> bool:
        """Install Go programming language.
        
        Args:
            version: Go version to install (e.g., "1.21.5").
                    If None, installs latest.
        
        Returns:
            True if installation succeeded.
        """
        if self.is_installed(DevToolType.GO):
            return True
        
        # Try package manager first
        if await self.install_via_package_manager(["golang-go"]):
            return True
        
        # Fallback to official binary
        arch = self.platform.normalized_arch
        go_arch = {"arm64": "arm64", "amd64": "amd64", "armhf": "armv6l"}.get(arch, "amd64")
        
        if version is None:
            version = "1.21.5"  # Default version
        
        url = f"https://go.dev/dl/go{version}.linux-{go_arch}.tar.gz"
        archive_path = Path(f"/tmp/go{version}.linux-{go_arch}.tar.gz")
        
        task = DownloadTask(url=url, dest=archive_path)
        await self.downloader.download(task)
        
        # Extract to /usr/local
        proc = await asyncio.create_subprocess_exec(
            "tar", "-C", "/usr/local", "-xzf", str(archive_path),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await proc.communicate()
        archive_path.unlink(missing_ok=True)
        
        if proc.returncode != 0:
            return False
        
        # Create symlink
        go_bin = Path("/usr/local/go/bin/go")
        if go_bin.exists():
            link_path = Path("/usr/local/bin/go")
            if not link_path.exists():
                link_path.symlink_to(go_bin)
        
        return True
    
    async def install_nodejs(
        self,
        version: str | None = None,
        method: str = "nvm",
    ) -> bool:
        """Install Node.js JavaScript runtime.
        
        Args:
            version: Node.js version to install (e.g., "20").
                    If None, installs LTS.
            method: Installation method (nvm, nodesource).
        
        Returns:
            True if installation succeeded.
        """
        if self.is_installed(DevToolType.NODEJS):
            return True
        
        if method == "nodesource":
            # Use NodeSource repository
            distro = self.detect_distro()
            node_major = version or "20"
            
            # Install dependencies
            deps = ["curl", "ca-certificates", "gnupg"]
            await self.install_via_package_manager(deps)
            
            # Add NodeSource repo
            setup_url = f"https://deb.nodesource.com/setup_{node_major}.x"
            script_path = Path("/tmp/nodesource_setup.sh")
            
            task = DownloadTask(
                url=setup_url,
                dest=script_path,
                backend="httpx",
            )
            await self.downloader.download(task)
            
            script_path.chmod(0o755)
            proc = await asyncio.create_subprocess_exec(
                "bash", str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            script_path.unlink(missing_ok=True)
            
            # Install Node.js
            return await self.install_via_package_manager(["nodejs"])
        
        elif method == "nvm":
            # Install via NVM
            nvm_url = "https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh"
            script_path = Path("/tmp/nvm-install.sh")
            
            task = DownloadTask(
                url=nvm_url,
                dest=script_path,
                backend="httpx",
            )
            await self.downloader.download(task)
            
            script_path.chmod(0o755)
            proc = await asyncio.create_subprocess_exec(
                "bash", str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            script_path.unlink(missing_ok=True)
            
            # Install Node.js via NVM
            node_version = version or "lts/*"
            nvm_dir = Path.home() / ".nvm"
            
            env = os.environ.copy()
            env["NVM_DIR"] = str(nvm_dir)
            
            proc = await asyncio.create_subprocess_shell(
                f"source {nvm_dir}/nvm.sh && nvm install {node_version}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                executable="/bin/bash",
            )
            stdout, stderr = await proc.communicate()
            return proc.returncode == 0
        
        # Fallback to package manager
        return await self.install_via_package_manager(["nodejs", "npm"])
    
    async def install_python_tools(self) -> bool:
        """Install Python development tools.
        
        Returns:
            True if installation succeeded.
        """
        packages = ["python3", "python3-pip", "python3-venv", "python3-dev"]
        return await self.install_via_package_manager(packages)
    
    async def install_java(self, version: str = "17") -> bool:
        """Install Java Development Kit.
        
        Args:
            version: Java version to install (e.g., "17", "21").
        
        Returns:
            True if installation succeeded.
        """
        if self.is_installed(DevToolType.JAVA):
            return True
        
        distro = self.detect_distro()
        
        if distro in ["debian", "ubuntu"]:
            packages = [f"openjdk-{version}-jdk", f"openjdk-{version}-jre"]
        elif distro in ["arch", "manjaro"]:
            packages = [f"jdk{version}-openjdk"]
        elif distro in ["fedora", "centos"]:
            packages = [f"java-{version}-openjdk-devel"]
        else:
            packages = ["default-jdk"]
        
        return await self.install_via_package_manager(packages)
    
    async def install_docker(self) -> bool:
        """Install Docker container platform.
        
        Returns:
            True if installation succeeded.
        """
        if self.is_installed(DevToolType.DOCKER):
            return True
        
        distro = self.detect_distro()
        
        # Install dependencies
        deps = ["ca-certificates", "curl", "gnupg"]
        await self.install_via_package_manager(deps)
        
        if distro in ["debian", "ubuntu"]:
            # Add Docker GPG key
            proc = await asyncio.create_subprocess_shell(
                "install -m 0755 -d /etc/apt/keyrings && "
                "curl -fsSL https://download.docker.com/linux/" + distro + "/gpg | "
                "gpg --dearmor -o /etc/apt/keyrings/docker.gpg && "
                "chmod a+r /etc/apt/keyrings/docker.gpg",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            
            # Add Docker repository
            arch = self.platform.normalized_arch
            codename = "bookworm" if distro == "debian" else "jammy"
            repo_line = (
                f"deb [arch={arch} signed-by=/etc/apt/keyrings/docker.gpg] "
                f"https://download.docker.com/linux/{distro} {codename} stable"
            )
            
            sources_file = Path("/etc/apt/sources.list.d/docker.list")
            sources_file.write_text(repo_line + "\n")
            
            # Install Docker
            await self.install_via_package_manager([])  # Update first
            packages = ["docker-ce", "docker-ce-cli", "containerd.io", "docker-buildx-plugin"]
            return await self.install_via_package_manager(packages)
        
        elif distro in ["arch", "manjaro"]:
            return await self.install_via_package_manager(["docker"])
        
        elif distro in ["fedora"]:
            proc = await asyncio.create_subprocess_exec(
                "dnf", "-y", "install", "dnf-plugins-core",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
            
            proc = await asyncio.create_subprocess_shell(
                "dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            
            return await self.install_via_package_manager(["docker-ce", "docker-ce-cli"])
        
        return False
    
    async def install_build_tools(self) -> bool:
        """Install essential build tools.
        
        Returns:
            True if installation succeeded.
        """
        distro = self.detect_distro()
        
        if distro in ["debian", "ubuntu"]:
            packages = ["build-essential", "cmake", "ninja-build", "make", "gcc", "g++"]
        elif distro in ["arch", "manjaro"]:
            packages = ["base-devel", "cmake", "ninja"]
        elif distro in ["fedora", "centos"]:
            packages = ["gcc", "gcc-c++", "make", "cmake", "ninja-build"]
        else:
            packages = ["gcc", "make", "cmake"]
        
        return await self.install_via_package_manager(packages)
    
    async def install_git(self) -> bool:
        """Install Git version control.
        
        Returns:
            True if installation succeeded.
        """
        if self.is_installed(DevToolType.GIT):
            return True
        
        return await self.install_via_package_manager(["git"])
    
    async def configure_git(
        self,
        username: str | None = None,
        email: str | None = None,
        editor: str = "vim",
    ) -> bool:
        """Configure Git settings.
        
        Args:
            username: Git user name.
            email: Git user email.
            editor: Default text editor.
        
        Returns:
            True if configuration succeeded.
        """
        if not self.is_installed(DevToolType.GIT):
            return False
        
        configs = []
        if username:
            configs.append(("user.name", username))
        if email:
            configs.append(("user.email", email))
        if editor:
            configs.append(("core.editor", editor))
        
        for key, value in configs:
            proc = await asyncio.create_subprocess_exec(
                "git", "config", "--global", key, value,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
        
        return True
