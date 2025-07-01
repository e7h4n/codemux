"""Server-side CLI for Codemux."""

import asyncio
import logging

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from codemux.server import CodemuxServer

logger = logging.getLogger(__name__)
console = Console()


class ServerCLI:
    """Interactive CLI for Codemux server management."""

    def __init__(self, server: CodemuxServer):
        """Initialize server CLI."""
        self.server = server
        self.running = True

    async def start(self):
        """Start the interactive CLI."""
        console.print("[bold green]Codemux Server CLI[/bold green]")
        console.print("Type 'help' for available commands\n")

        while self.running:
            try:
                # Get command from user
                command = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: Prompt.ask("[bold]server[/bold]")
                )

                if not command:
                    continue

                await self.handle_command(command.strip())

            except KeyboardInterrupt:
                console.print("\nUse 'quit' to exit")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    async def handle_command(self, command: str):
        """Handle a CLI command."""
        parts = command.split(maxsplit=1)
        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "help":
            self.show_help()
        elif cmd == "status":
            self.show_status()
        elif cmd == "clients":
            self.show_clients()
        elif cmd == "sessions":
            self.show_sessions()
        elif cmd == "exec":
            await self.execute_command(args)
        elif cmd == "quit" or cmd == "exit":
            self.running = False
            console.print("[yellow]Shutting down...[/yellow]")
        else:
            console.print(f"[red]Unknown command: {cmd}[/red]")

    def show_help(self):
        """Show help information."""
        table = Table(title="Available Commands")
        table.add_column("Command", style="cyan")
        table.add_column("Description")

        table.add_row("help", "Show this help message")
        table.add_row("status", "Show server status")
        table.add_row("clients", "List connected clients")
        table.add_row("sessions", "List all available sessions")
        table.add_row("exec <session> <command>", "Execute command on session")
        table.add_row("quit/exit", "Shutdown server")

        console.print(table)

    def show_status(self):
        """Show server status."""
        client_count = len(self.server.clients)
        session_count = sum(len(c.sessions) for c in self.server.clients.values())

        status_panel = Panel(
            f"[green]Server Status[/green]\n\n"
            f"Address: ws://{self.server.host}:{self.server.port}/ws\n"
            f"Connected Clients: {client_count}\n"
            f"Total Sessions: {session_count}\n"
            f"Heartbeat Interval: {self.server.heartbeat_interval}s\n"
            f"Heartbeat Timeout: {self.server.heartbeat_timeout}s",
            title="Status",
            border_style="green",
        )
        console.print(status_panel)

    def show_clients(self):
        """Show connected clients."""
        if not self.server.clients:
            console.print("[yellow]No clients connected[/yellow]")
            return

        table = Table(title="Connected Clients")
        table.add_column("Client ID", style="cyan")
        table.add_column("Hostname")
        table.add_column("Platform")
        table.add_column("Sessions")
        table.add_column("Last Heartbeat")

        for client in self.server.clients.values():
            last_hb = client.last_heartbeat.strftime("%H:%M:%S")
            table.add_row(
                client.client_id,
                client.hostname,
                client.platform,
                str(len(client.sessions)),
                last_hb,
            )

        console.print(table)

    def show_sessions(self):
        """Show all available sessions."""
        sessions = self.server.get_all_sessions()

        if not sessions:
            console.print("[yellow]No sessions available[/yellow]")
            return

        table = Table(title="Available Sessions")
        table.add_column("Session", style="cyan")
        table.add_column("Client")
        table.add_column("Path")
        table.add_column("Tmux Session")

        for session in sessions:
            table.add_row(
                session["name"],
                session["client_id"],
                session["current_path"],
                session["tmux_session_name"],
            )

        console.print(table)

    async def execute_command(self, args: str):
        """Execute command on a session."""
        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            console.print("[red]Usage: exec <session> <command>[/red]")
            return

        session_name = parts[0]
        command = parts[1]

        console.print(f"Executing on {session_name}: {command}")

        result = await self.server.execute_command(session_name, command)

        if result["success"]:
            console.print(
                f"[green]Command sent (request_id: {result.get('request_id')})[/green]"
            )
        else:
            console.print(f"[red]Failed: {result.get('error')}[/red]")


async def run_server_with_cli(host: str = "0.0.0.0", port: int = 8000):
    """Run server with CLI interface."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create server
    server = CodemuxServer(host=host, port=port)

    # Create CLI
    cli = ServerCLI(server)

    # Start server and CLI concurrently
    server_task = asyncio.create_task(server.start())
    cli_task = asyncio.create_task(cli.start())

    try:
        # Wait for either to complete (usually CLI exit)
        done, pending = await asyncio.wait(
            [server_task, cli_task], return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel remaining tasks
        for task in pending:
            task.cancel()

    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")


def main():
    """Main entry point for server CLI."""
    import sys

    # Parse arguments
    host = "0.0.0.0"
    port = 8000

    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])

    # Run server with CLI
    asyncio.run(run_server_with_cli(host, port))


if __name__ == "__main__":
    main()
