"""Web server for Codemux with FastAPI."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from codemux.server import CodemuxServer

logger = logging.getLogger(__name__)


class WebUI:
    """Web UI for Codemux server."""

    def __init__(self, codemux_server: CodemuxServer):
        """Initialize Web UI."""
        self.codemux_server = codemux_server
        self.app = FastAPI(title="Codemux Web UI", version="0.1.0")

        # Get the web directory path
        web_dir = Path(__file__).parent / "web"

        # Mount static files
        self.app.mount(
            "/static", StaticFiles(directory=str(web_dir / "static")), name="static"
        )

        # Setup templates
        self.templates = Jinja2Templates(directory=str(web_dir / "templates"))

        # Track WebSocket connections for real-time updates
        self.websocket_connections: set[WebSocket] = set()

        self._setup_routes()

    def _setup_routes(self):
        """Setup FastAPI routes."""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            """Main dashboard page."""
            # Get initial data for template
            client_count = len(self.codemux_server.clients)
            session_count = sum(
                len(c.sessions) for c in self.codemux_server.clients.values()
            )

            return self.templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "stats": {"clients": client_count, "sessions": session_count},
                    "serverInfo": {
                        "heartbeat_interval": self.codemux_server.heartbeat_interval,
                        "heartbeat_timeout": self.codemux_server.heartbeat_timeout,
                    },
                },
            )

        @self.app.get("/api/status")
        async def api_status():
            """Get server status."""
            client_count = len(self.codemux_server.clients)
            session_count = sum(
                len(c.sessions) for c in self.codemux_server.clients.values()
            )

            return {
                "status": "running",
                "clients": client_count,
                "sessions": session_count,
                "server_info": {
                    "host": self.codemux_server.host,
                    "port": self.codemux_server.port,
                    "heartbeat_interval": self.codemux_server.heartbeat_interval,
                    "heartbeat_timeout": self.codemux_server.heartbeat_timeout,
                },
            }

        @self.app.get("/api/clients")
        async def api_clients():
            """Get all connected clients."""
            clients = []
            for client in self.codemux_server.clients.values():
                clients.append(
                    {
                        "id": client.client_id,
                        "hostname": client.hostname,
                        "platform": client.platform,
                        "sessions_count": len(client.sessions),
                        "last_heartbeat": client.last_heartbeat.isoformat(),
                        "authenticated": client.authenticated,
                    }
                )
            return {"clients": clients}

        @self.app.get("/api/sessions")
        async def api_sessions():
            """Get all available sessions."""
            sessions = self.codemux_server.get_all_sessions()
            return {"sessions": sessions}

        @self.app.post("/api/execute")
        async def api_execute(request: Request):
            """Execute command on a session."""
            data = await request.json()
            session_name = data.get("session_name")
            command = data.get("command")
            timeout = data.get("timeout", 30.0)

            if not session_name or not command:
                return {"success": False, "error": "Missing session_name or command"}

            result = await self.codemux_server.execute_command(
                session_name, command, timeout
            )

            # Broadcast the command execution to WebSocket clients
            await self._broadcast_update(
                {
                    "type": "command_executed",
                    "session_name": session_name,
                    "command": command,
                    "result": result,
                }
            )

            return result

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.websocket_connections.add(websocket)

            try:
                # Send initial data
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "initial_data",
                            "clients": [
                                {
                                    "id": client.client_id,
                                    "hostname": client.hostname,
                                    "platform": client.platform,
                                    "sessions_count": len(client.sessions),
                                    "last_heartbeat": client.last_heartbeat.isoformat(),
                                }
                                for client in self.codemux_server.clients.values()
                            ],
                            "sessions": self.codemux_server.get_all_sessions(),
                        }
                    )
                )

                # Keep connection alive and handle incoming messages
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))

            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.websocket_connections.discard(websocket)

    async def _broadcast_update(self, data: dict[str, Any]):
        """Broadcast update to all WebSocket connections."""
        if not self.websocket_connections:
            return

        message = json.dumps(data)
        disconnected = set()

        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(message)
            except Exception:
                disconnected.add(websocket)

        # Remove disconnected WebSockets
        self.websocket_connections -= disconnected

    async def broadcast_client_update(self):
        """Broadcast client list update."""
        await self._broadcast_update(
            {
                "type": "clients_updated",
                "clients": [
                    {
                        "id": client.client_id,
                        "hostname": client.hostname,
                        "platform": client.platform,
                        "sessions_count": len(client.sessions),
                        "last_heartbeat": client.last_heartbeat.isoformat(),
                    }
                    for client in self.codemux_server.clients.values()
                ],
            }
        )

    async def broadcast_sessions_update(self):
        """Broadcast sessions list update."""
        await self._broadcast_update(
            {
                "type": "sessions_updated",
                "sessions": self.codemux_server.get_all_sessions(),
            }
        )


class CodemuxWebServer(CodemuxServer):
    """Extended Codemux server with Web UI."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        web_port: int = 8001,
        auth_tokens: set[str] | None = None,
    ):
        """Initialize Codemux server with Web UI."""
        super().__init__(host, port, auth_tokens)
        self.web_port = web_port
        self.web_ui = WebUI(self)

    async def start_with_web(self):
        """Start both WebSocket server and Web UI."""
        # Start the original WebSocket server
        websocket_task = asyncio.create_task(self.start())

        # Start the web server
        import uvicorn

        config = uvicorn.Config(
            app=self.web_ui.app, host=self.host, port=self.web_port, log_level="info"
        )
        web_server = uvicorn.Server(config)
        web_task = asyncio.create_task(web_server.serve())

        logger.info(f"Web UI available at http://{self.host}:{self.web_port}")

        # Wait for either to complete
        done, pending = await asyncio.wait(
            [websocket_task, web_task], return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel remaining tasks
        for task in pending:
            task.cancel()

    def _update_sessions(self):
        """Override to broadcast updates to Web UI."""
        super()._update_sessions()
        # Schedule broadcast (don't await here as this might be called from sync context)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.web_ui.broadcast_sessions_update())
        except RuntimeError:
            # No event loop running, skip broadcast
            pass

    async def _handle_client_registered(self, client_id: str):  # noqa: ARG002
        """Handle client registration for Web UI updates."""
        await self.web_ui.broadcast_client_update()

    async def _handle_client_disconnected(self, client_id: str):  # noqa: ARG002
        """Handle client disconnection for Web UI updates."""
        await self.web_ui.broadcast_client_update()


async def main():
    """Main entry point for web server."""
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Parse arguments
    host = "0.0.0.0"
    port = 8000
    web_port = 8001

    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    if len(sys.argv) > 3:
        web_port = int(sys.argv[3])

    # Create and start server with Web UI
    server = CodemuxWebServer(host=host, port=port, web_port=web_port)

    try:
        await server.start_with_web()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")


def main_sync():
    """Synchronous entry point for web server script."""
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
