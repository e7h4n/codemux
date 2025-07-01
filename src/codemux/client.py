"""Codemux client implementation."""

import asyncio
import logging
import platform
import socket
from typing import TYPE_CHECKING, Any

import websockets

if TYPE_CHECKING:
    from websockets.asyncio.client import ClientConnection as WebSocketClientProtocol
else:
    from codemux.types import WebSocketClientProtocol

from codemux.output_processor import OutputProcessor
from codemux.protocol import (
    ErrorType,
    Message,
    MessageType,
    ProtocolHelper,
    SessionAction,
)
from codemux.tmux_controller import TmuxController

logger = logging.getLogger(__name__)


class CodemuxClient:
    """Client that connects to Codemux server and manages local tmux sessions."""

    def __init__(
        self,
        server_url: str,
        client_id: str | None = None,
        auth_token: str | None = None,
    ):
        """Initialize Codemux client.

        Args:
            server_url: WebSocket server URL (e.g., "ws://localhost:8000/ws")
            client_id: Optional client identifier, defaults to hostname
            auth_token: Optional authentication token
        """
        self.server_url = server_url
        self.client_id = client_id or socket.gethostname()
        self.auth_token = auth_token

        self.tmux = TmuxController()
        self.processor = OutputProcessor(self.tmux)

        self.websocket: WebSocketClientProtocol | None = None
        self.running = False
        self.heartbeat_interval = 30
        self.sessions_cache: dict[str, dict[str, Any]] = {}

    async def connect(self):
        """Connect to server and start client operations."""
        self.running = True

        while self.running:
            try:
                logger.info(f"Connecting to {self.server_url}...")
                async with websockets.connect(self.server_url) as websocket:
                    self.websocket = websocket
                    logger.info("Connected to server")

                    # Authenticate if token provided
                    if self.auth_token:
                        await self._authenticate()

                    # Register client
                    await self._register()

                    # Start background tasks
                    tasks = [
                        asyncio.create_task(self._handle_messages()),
                        asyncio.create_task(self._monitor_sessions()),
                        asyncio.create_task(self._heartbeat_loop()),
                    ]

                    # Wait for any task to complete (usually due to error)
                    done, pending = await asyncio.wait(
                        tasks, return_when=asyncio.FIRST_COMPLETED
                    )

                    # Cancel remaining tasks
                    for task in pending:
                        task.cancel()

                    # Wait for first completed task to propagate any exceptions
                    if done:
                        await list(done)[0]

            except websockets.exceptions.ConnectionClosed:  # type: ignore[attr-defined]
                logger.warning("Connection closed by server")
            except Exception as e:
                logger.error(f"Connection error: {e}")

            if self.running:
                logger.info("Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

    async def disconnect(self):
        """Disconnect from server."""
        self.running = False
        if self.websocket:
            await self.websocket.close()

    async def _authenticate(self):
        """Authenticate with server."""
        auth_msg = Message.create(
            MessageType.AUTH,
            {"client_id": self.client_id, "auth_token": self.auth_token},
        )
        await self._send_message(auth_msg)

        # Wait for auth result
        if self.websocket is None:
            raise Exception("Not connected")
        response = await self.websocket.recv()
        msg = Message.from_json(str(response))

        if msg.type != MessageType.AUTH_RESULT or not msg.data.get("success"):
            raise Exception("Authentication failed")

        logger.info("Authentication successful")

    async def _register(self):
        """Register client with server."""
        sessions = self.tmux.discover_claude_sessions()
        self.sessions_cache = {s["name"]: s for s in sessions}

        register_msg = ProtocolHelper.create_register(
            client_id=self.client_id,
            hostname=socket.gethostname(),
            platform=platform.system().lower(),
            sessions=sessions,
        )

        await self._send_message(register_msg)
        logger.info(f"Registered with {len(sessions)} sessions")

    async def _handle_messages(self):
        """Handle incoming messages from server."""
        try:
            async for message in self.websocket:  # type: ignore[misc]
                await self._process_message(str(message))
        except websockets.exceptions.ConnectionClosed:  # type: ignore[attr-defined]
            logger.info("Message handler: connection closed")
            raise

    async def _process_message(self, message: str):
        """Process a single message from server."""
        try:
            msg = Message.from_json(message)
            logger.debug(f"Received: {msg.type.value}")

            if msg.type == MessageType.REGISTER_ACK:
                self.heartbeat_interval = msg.data.get("heartbeat_interval", 30)

            elif msg.type == MessageType.EXECUTE_COMMAND:
                await self._handle_execute_command(msg)

            elif msg.type == MessageType.QUERY_STATUS:
                await self._handle_query_status(msg)

            elif msg.type == MessageType.CONTROL:
                await self._handle_control(msg)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_msg = ProtocolHelper.create_error(ErrorType.INTERNAL_ERROR, str(e))
            await self._send_message(error_msg)

    async def _handle_execute_command(self, msg: Message):
        """Handle execute command request."""
        data = msg.data
        request_id = data["request_id"]
        session_name = data["session_name"]
        command = data["command"]
        timeout = data.get("timeout", 30.0)

        try:
            # Execute command
            result = await self.processor.send_command_with_response(
                session_name, command, timeout
            )

            # Send response
            response = ProtocolHelper.create_command_response(
                request_id=request_id,
                session_name=session_name,
                success=result["success"],
                output=result.get("output", ""),
                response_time=result.get("response_time", 0.0),
                error=result.get("error"),
            )

        except Exception as e:
            # Send error response
            response = ProtocolHelper.create_command_response(
                request_id=request_id,
                session_name=session_name,
                success=False,
                error=str(e),
            )

        await self._send_message(response)

    async def _handle_query_status(self, msg: Message):
        """Handle status query request."""
        # TODO: Implement status queries
        pass

    async def _handle_control(self, msg: Message):
        """Handle control command."""
        action = msg.data.get("action")

        if action == "refresh_sessions":
            # Force refresh sessions
            await self._check_sessions()

    async def _monitor_sessions(self):
        """Monitor local sessions for changes."""
        while self.running:
            await self._check_sessions()
            await asyncio.sleep(10)  # Check every 10 seconds

    async def _check_sessions(self):
        """Check for session changes and notify server."""
        try:
            current_sessions = self.tmux.discover_claude_sessions()
            current_dict = {s["name"]: s for s in current_sessions}

            # Check for added sessions
            for name, session in current_dict.items():
                if name not in self.sessions_cache:
                    await self._notify_session_change(SessionAction.ADDED, session)

            # Check for removed sessions
            for name in list(self.sessions_cache.keys()):
                if name not in current_dict:
                    await self._notify_session_change(
                        SessionAction.REMOVED, self.sessions_cache[name]
                    )

            # Update cache
            self.sessions_cache = current_dict

        except Exception as e:
            logger.error(f"Error monitoring sessions: {e}")

    async def _notify_session_change(
        self, action: SessionAction, session: dict[str, Any]
    ):
        """Notify server of session change."""
        msg = Message.create(
            MessageType.SESSION_UPDATE, {"action": action.value, "session": session}
        )
        await self._send_message(msg)
        logger.info(f"Session {action.value}: {session['name']}")

    async def _heartbeat_loop(self):
        """Send periodic heartbeats to server."""
        while self.running:
            await asyncio.sleep(self.heartbeat_interval)

            if self.websocket is not None and not self.websocket.closed:
                heartbeat = ProtocolHelper.create_heartbeat(
                    self.client_id, len(self.sessions_cache)
                )
                await self._send_message(heartbeat)

    async def _send_message(self, message: Message):
        """Send message to server."""
        if self.websocket is not None and not self.websocket.closed:
            await self.websocket.send(message.to_json())
        else:
            logger.warning("Cannot send message: not connected")


async def main():
    """Main entry point for client."""
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Get server URL from command line or use default
    server_url = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8000/ws"

    client = CodemuxClient(server_url)

    try:
        await client.connect()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
