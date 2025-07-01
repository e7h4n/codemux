#!/usr/bin/env python3
"""Manual test script for tmux session discovery."""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.table import Table

from codemux.tmux_controller import TmuxController


def main():
    """Run session discovery and display results."""
    console = Console()
    
    console.print("\n🔍 [bold cyan]Discovering Claude Code Sessions...[/bold cyan]\n")
    
    try:
        controller = TmuxController()
        sessions = controller.discover_claude_sessions()
        
        if not sessions:
            console.print("[yellow]No Claude Code sessions found.[/yellow]")
            console.print("\nMake sure you have tmux sessions running Claude Code.")
            return
        
        # Create a table for display
        table = Table(title=f"Found {len(sessions)} session(s)")
        table.add_column("Session Name", style="cyan")
        table.add_column("Directory", style="green")
        table.add_column("Path", style="blue")
        table.add_column("Tmux Session", style="magenta")
        
        for session in sessions:
            table.add_row(
                session["name"],
                session["dirname"],
                session["current_path"],
                session["tmux_session_name"],
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("\nMake sure tmux is installed and running.")


if __name__ == "__main__":
    main()