"""Command line interface for codemux."""

import sys
from typing import NoReturn

from rich.console import Console
from rich.prompt import Prompt

from codemux.command_router import CommandRouter
from codemux.tmux_controller import TmuxController


class CodemuxCLI:
    """Interactive command line interface for codemux."""

    def __init__(self) -> None:
        """Initialize the CLI."""
        self.console = Console()
        self.tmux_controller = TmuxController()
        self.router = CommandRouter(self.tmux_controller)

    def start(self) -> NoReturn:
        """Start the interactive CLI session."""
        self.console.print("\n[bold cyan]Codemux - Voice-controlled tmux management[/bold cyan]")
        self.console.print("[dim]Type 'help' for commands, 'quit' to exit[/dim]\n")

        # Discover sessions on startup
        self.refresh_sessions()

        try:
            while True:
                try:
                    user_input = Prompt.ask(
                        f"[bold green]codemux[/bold green]"
                        f"{self._get_session_indicator()}"
                    ).strip()

                    if not user_input:
                        continue

                    if user_input.lower() in ["quit", "exit", "q"]:
                        self.console.print("[yellow]Goodbye![/yellow]")
                        sys.exit(0)

                    if user_input.lower() == "help":
                        self._show_help()
                        continue

                    if user_input.lower() in ["refresh", "reload"]:
                        self.refresh_sessions()
                        continue

                    # Process the command
                    response = self.router.route_command(user_input)
                    self.console.print(f"[blue]{response}[/blue]")

                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Use 'quit' to exit[/yellow]")
                except EOFError:
                    self.console.print("\n[yellow]Goodbye![/yellow]")
                    sys.exit(0)

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)

    def refresh_sessions(self) -> None:
        """Refresh the list of Claude Code sessions."""
        try:
            sessions = self.tmux_controller.discover_claude_sessions()
            self.router.update_sessions(sessions)

            if sessions:
                self.console.print(
                    f"[green]Discovered {len(sessions)} Claude Code session(s)[/green]"
                )
            else:
                self.console.print(
                    "[yellow]No Claude Code sessions found. "
                    "Make sure tmux is running with Claude Code sessions.[/yellow]"
                )

        except Exception as e:
            self.console.print(f"[red]Error discovering sessions: {e}[/red]")

    def _get_session_indicator(self) -> str:
        """Get the current session indicator for the prompt."""
        if self.router.current_session:
            return f"[dim]({self.router.current_session})[/dim]> "
        else:
            return "> "

    def _show_help(self) -> None:
        """Show help information."""
        help_text = """[bold]Codemux Commands:[/bold]

[yellow]Session Management:[/yellow]
  status                  - Show all sessions
  refresh                 - Refresh session list
  switch to <session>     - Switch to session
  #<session>             - Switch to session
  #<session> <command>   - Send command to session

[yellow]Examples:[/yellow]
  status                  - List all sessions
  switch to frontend      - Switch to frontend session
  #backend npm test      - Run npm test in backend session
  切换到 frontend         - Switch to frontend (Chinese)

[yellow]Control:[/yellow]
  help                   - Show this help
  quit, exit, q          - Exit codemux

[dim]Note: Session names are typically hostname_directory (e.g., macbook_frontend)[/dim]
"""
        self.console.print(help_text)


def main() -> NoReturn:
    """Main entry point for the CLI."""
    cli = CodemuxCLI()
    cli.start()


if __name__ == "__main__":
    main()