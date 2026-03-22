"""Command line interface for TMOE.

Provides both TUI (Textual) and CLI modes for managing Linux containers.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Sequence

from tmoe.core.config import get_config
from tmoe.core.platform import get_platform_info


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="tmoe",
        description="TMOE - More Optional Environments for Linux containers and GUI desktops",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tmoe                      Launch TUI manager
  tmoe p debian             Start proot Debian container
  tmoe c ubuntu             Start chroot Ubuntu container
  tmoe ls                   List installed containers
  tmoe --version            Show version
        """
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 2.0.0",
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # TUI manager
    subparsers.add_parser(
        "m",
        aliases=["manager", "menu"],
        help="Launch TUI manager (default)",
    )
    
    # Proot container
    proot_parser = subparsers.add_parser(
        "p",
        aliases=["proot"],
        help="Proot container operations",
    )
    proot_parser.add_argument(
        "distro",
        nargs="?",
        help="Distribution name (e.g., debian, ubuntu, arch)",
    )
    proot_parser.add_argument(
        "codename",
        nargs="?",
        help="Distribution codename (e.g., stable, jammy)",
    )
    proot_parser.add_argument(
        "arch",
        nargs="?",
        help="Architecture (e.g., arm64, amd64)",
    )
    
    # Chroot container
    chroot_parser = subparsers.add_parser(
        "c",
        aliases=["chroot"],
        help="Chroot container operations (requires root)",
    )
    chroot_parser.add_argument(
        "distro",
        nargs="?",
        help="Distribution name",
    )
    chroot_parser.add_argument(
        "codename",
        nargs="?",
        help="Distribution codename",
    )
    chroot_parser.add_argument(
        "arch",
        nargs="?",
        help="Architecture",
    )
    
    # Systemd-nspawn
    nspawn_parser = subparsers.add_parser(
        "systemd",
        aliases=["sd", "nspawn"],
        help="Systemd-nspawn container operations",
    )
    nspawn_parser.add_argument(
        "distro",
        nargs="?",
        help="Distribution name",
    )
    
    # List containers
    subparsers.add_parser(
        "ls",
        aliases=["list"],
        help="List installed containers",
    )
    
    # Tools
    subparsers.add_parser(
        "t",
        aliases=["tool", "tools"],
        help="Launch tools menu",
    )
    
    # Zsh management
    subparsers.add_parser(
        "zsh",
        help="Zsh management",
    )
    
    # Theme management
    subparsers.add_parser(
        "theme",
        help="Zsh theme management",
    )
    
    # Aria2 management
    subparsers.add_parser(
        "aria2",
        help="Aria2 download manager",
    )
    
    return parser


async def launch_tui() -> int:
    """Launch the Textual TUI."""
    try:
        from tmoe.tui.app import TmoeApp
        app = TmoeApp()
        await app.run_async()
        return 0
    except ImportError as e:
        print(f"Error: Could not load TUI. {e}", file=sys.stderr)
        return 1


async def handle_proot(args: argparse.Namespace) -> int:
    """Handle proot container command."""
    from tmoe.container.proot import ProotBackend
    
    backend = ProotBackend()
    
    if args.distro:
        # Start or install specific container
        config = get_config()
        distro = args.distro
        codename = args.codename or config.default_codename
        arch = args.arch or config.default_arch
        
        print(f"Starting proot {distro} ({codename}, {arch})...")
        # TODO: Implement container start
        return 0
    else:
        # Show proot menu
        print("Proot container menu (TUI not implemented yet)")
        return 0


async def handle_chroot(args: argparse.Namespace) -> int:
    """Handle chroot container command."""
    from tmoe.container.chroot import ChrootBackend
    
    platform = get_platform_info()
    if not platform.is_root:
        print("Error: Chroot requires root privileges", file=sys.stderr)
        return 1
    
    backend = ChrootBackend()
    
    if args.distro:
        print(f"Starting chroot {args.distro}...")
        # TODO: Implement container start
        return 0
    else:
        print("Chroot container menu (TUI not implemented yet)")
        return 0


async def handle_list(args: argparse.Namespace) -> int:
    """Handle list containers command."""
    platform = get_platform_info()
    config = get_config()
    
    print("Installed containers:")
    print("-" * 50)
    
    # List proot containers
    proot_dir = platform.proot_dir
    if proot_dir.exists():
        for path in sorted(proot_dir.iterdir()):
            if path.is_dir():
                print(f"  [proot] {path.name}")
    
    # List chroot containers
    chroot_dir = platform.chroot_dir
    if chroot_dir.exists():
        for path in sorted(chroot_dir.iterdir()):
            if path.is_dir():
                print(f"  [chroot] {path.name}")
    
    return 0


async def async_main(argv: Sequence[str] | None = None) -> int:
    """Async main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Update config with command line flags
    config = get_config()
    if args.verbose:
        config.verbose = True
    if args.debug:
        config.debug = True
    
    # Route to appropriate handler
    command = args.command or "m"  # Default to manager TUI
    
    match command:
        case "m" | "manager" | "menu" | None:
            return await launch_tui()
        case "p" | "proot":
            return await handle_proot(args)
        case "c" | "chroot":
            return await handle_chroot(args)
        case "systemd" | "sd" | "nspawn":
            print("Systemd-nspawn not yet implemented")
            return 0
        case "ls" | "list":
            return await handle_list(args)
        case "t" | "tool" | "tools":
            print("Tools menu not yet implemented")
            return 0
        case "zsh":
            print("Zsh management not yet implemented")
            return 0
        case "theme":
            print("Theme management not yet implemented")
            return 0
        case "aria2":
            print("Aria2 management not yet implemented")
            return 0
        case _:
            parser.print_help()
            return 1


def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point."""
    try:
        return asyncio.run(async_main(argv))
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        if get_config().debug:
            raise
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
