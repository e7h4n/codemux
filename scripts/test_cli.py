#!/usr/bin/env python3
"""Manual test script for CLI functionality."""

import sys
from pathlib import Path

from rich.console import Console

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codemux.command_router import CommandRouter
from codemux.tmux_controller import TmuxController


def test_basic_functionality():
    """Test basic CLI functionality without starting interactive mode."""
    console = Console()
    console.print("\n[bold cyan]Testing Codemux CLI Components...[/bold cyan]\n")

    # Test TmuxController
    console.print("[yellow]1. Testing TmuxController...[/yellow]")
    try:
        controller = TmuxController()
        sessions = controller.discover_claude_sessions()
        console.print(f"   Found {len(sessions)} Claude Code sessions")
    except Exception as e:
        console.print(f"   [red]Error: {e}[/red]")

    # Test CommandRouter
    console.print("\n[yellow]2. Testing CommandRouter...[/yellow]")
    router = CommandRouter(controller)
    router.update_sessions(sessions)

    # Test various commands
    test_commands = [
        "status",
        "switch to frontend" if sessions else "switch to nonexistent",
        "#backend npm test" if sessions else "#nonexistent test",
        "help",
    ]

    for cmd in test_commands:
        response = router.route_command(cmd)
        console.print(f"   [dim]>{cmd}[/dim] → {response}")

    console.print("\n[green]✓ Basic functionality test completed[/green]")
    console.print(
        "\nTo test interactive CLI, run: [bold]uv run python -m codemux.cli[/bold]"
    )


if __name__ == "__main__":
    test_basic_functionality()
