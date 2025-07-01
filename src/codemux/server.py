"""Codemux server implementation."""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

import websockets
from websockets import serve

if TYPE_CHECKING:
    from websockets.asyncio.server import ServerConnection as WebSocketServerProtocol
else:
    from codemux.types import WebSocketServerProtocol

# CommandRouter removed - server tracks sessions directly
from codemux.protocol import (
    ErrorType,
    Message,
    MessageType,
    ProtocolHelper,
    SessionAction,
    SessionInfo,
)

logger = logging.getLogger(__name__)


class ClientConnection:
    """Represents a connected client."""

    def __init__(self, websocket: WebSocketServerProtocol, client_id: str):
        """Initialize client connection."""
        self.websocket = websocket
        self.client_id = client_id
        self.hostname = ""
        self.platform = ""
        self.sessions: dict[str, SessionInfo] = {}
        self.last_heartbeat = datetime.now()
        self.authenticated = False


class CodemuxServer:
    """WebSocket server for Codemux C/S architecture."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        auth_tokens: set[str] | None = None,
    ):
        """Initialize Codemux server.

        Args:
            host: Host to bind to
            port: Port to bind to
            auth_tokens: Optional set of valid authentication tokens
        """
        self.host = host
        self.port = port
        self.auth_tokens = auth_tokens or set()

        self.clients: dict[str, ClientConnection] = {}
        self.websocket_to_client: dict[WebSocketServerProtocol, str] = {}
        self.all_sessions: list[dict[str, Any]] = []  # Track all sessions

        # Server configuration
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout = 90  # seconds

    async def start(self):
        """Start the WebSocket server."""
        logger.info(f"Starting Codemux server on {self.host}:{self.port}")

        # Start background tasks
        asyncio.create_task(self._monitor_heartbeats())

        # Start WebSocket server
        async with serve(self._handle_client, self.host, self.port):
            logger.info(f"Server listening on ws://{self.host}:{self.port}/ws")
            await asyncio.Future()  # run forever

    async def _handle_client(self, websocket: WebSocketServerProtocol) -> None:
        """Handle a new client connection."""
        client_id = None
        try:
            logger.info(f"New connection from {websocket.remote_address}")

            # Wait for registration or auth
            first_message = await asyncio.wait_for(websocket.recv(), timeout=10.0)

            msg = Message.from_json(str(first_message))

            # Handle authentication if required
            if self.auth_tokens and msg.type == MessageType.AUTH:
                auth_success = await self._handle_auth(websocket, msg)
                if not auth_success:
                    return
                # Wait for registration after auth
                registration_message = await asyncio.wait_for(
                    websocket.recv(), timeout=10.0
                )
                msg = Message.from_json(str(registration_message))

            # Handle registration
            if msg.type != MessageType.REGISTER:
                error_msg = ProtocolHelper.create_error(
                    ErrorType.INTERNAL_ERROR, "Expected REGISTER message"
                )
                await websocket.send(error_msg.to_json())
                return

            client_id = msg.data["client_id"]

            # Create client connection
            client = ClientConnection(websocket, client_id)
            client.hostname = msg.data["hostname"]
            client.platform = msg.data["platform"]
            client.authenticated = not self.auth_tokens or client.authenticated

            # Register sessions
            for session_data in msg.data["sessions"]:
                session_info = SessionInfo.from_dict(session_data)
                client.sessions[session_info.name] = session_info

            # Store client
            self.clients[client_id] = client
            self.websocket_to_client[websocket] = client_id

            # Send acknowledgment
            ack_msg = Message.create(
                MessageType.REGISTER_ACK,
                {
                    "success": True,
                    "heartbeat_interval": self.heartbeat_interval,
                    "server_version": "0.1.0",
                },
            )
            await websocket.send(ack_msg.to_json())

            logger.info(
                f"Client {client_id} registered with {len(client.sessions)} sessions"
            )

            # Update session list
            self._update_sessions()
            
            logger.info(f"Starting message loop for client {client_id}")

            # Handle messages from client
            try:
                async for message in websocket:
                    logger.debug(f"Received message from client {client_id}: {str(message)[:100]}")
                    await self._process_client_message(client, str(message))
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"Client {client_id} connection closed normally")
                raise

        except websockets.exceptions.ConnectionClosed:  # type: ignore[attr-defined]
            logger.info(f"Client {client_id or 'unknown'} disconnected")
        except TimeoutError:
            logger.warning(f"Client {client_id or 'unknown'} registration timeout")
        except Exception as e:
            logger.error(f"Error handling client {client_id or 'unknown'}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        finally:
            # Clean up client
            if client_id and client_id in self.clients:
                del self.clients[client_id]
            if websocket in self.websocket_to_client:
                del self.websocket_to_client[websocket]
            self._update_sessions()

    async def _handle_auth(
        self, websocket: WebSocketServerProtocol, msg: Message
    ) -> bool:
        """Handle authentication message."""
        auth_token = msg.data.get("auth_token")
        success = auth_token in self.auth_tokens

        result_msg = Message.create(MessageType.AUTH_RESULT, {"success": success})
        await websocket.send(result_msg.to_json())

        if not success:
            logger.warning(f"Authentication failed from {websocket.remote_address}")

        return success

    async def _process_client_message(self, client: ClientConnection, message: str):
        """Process a message from a client."""
        try:
            msg = Message.from_json(message)
            logger.debug(f"Received {msg.type.value} from {client.client_id}")

            if msg.type == MessageType.HEARTBEAT:
                client.last_heartbeat = datetime.now()

            elif msg.type == MessageType.SESSION_UPDATE:
                await self._handle_session_update(client, msg)

            elif msg.type == MessageType.COMMAND_RESPONSE:
                await self._handle_command_response(client, msg)

            elif msg.type == MessageType.ERROR:
                logger.error(
                    f"Client error from {client.client_id}: "
                    f"{msg.data.get('message')}"
                )

        except Exception as e:
            logger.error(f"Error processing message from {client.client_id}: {e}")

    async def _handle_session_update(self, client: ClientConnection, msg: Message):
        """Handle session update from client."""
        action = SessionAction(msg.data["action"])
        session_data = msg.data["session"]
        session_info = SessionInfo.from_dict(session_data)

        if action == SessionAction.ADDED:
            client.sessions[session_info.name] = session_info
            logger.info(f"Session added: {session_info.name} from {client.client_id}")

        elif action == SessionAction.REMOVED:
            if session_info.name in client.sessions:
                del client.sessions[session_info.name]
                logger.info(
                    f"Session removed: {session_info.name} from {client.client_id}"
                )

        elif action == SessionAction.CHANGED:
            client.sessions[session_info.name] = session_info
            logger.info(f"Session updated: {session_info.name} from {client.client_id}")

        # Update session list
        self._update_sessions()

    async def _handle_command_response(self, client: ClientConnection, msg: Message):
        """Handle command response from client."""
        # In a full implementation, this would handle responses to commands
        # sent to clients and potentially forward them to other components
        logger.info(
            f"Command response from {client.client_id}: "
            f"request_id={msg.data.get('request_id')}, "
            f"success={msg.data.get('success')}"
        )

    def _update_sessions(self):
        """Update the list of all available sessions."""
        all_sessions: list[dict[str, Any]] = []
        for client in self.clients.values():
            for session_info in client.sessions.values():
                # Convert SessionInfo to dict format
                session_dict: dict[str, Any] = {
                    "name": session_info.name,
                    "tmux_session_name": session_info.tmux_session_name,
                    "current_path": session_info.current_path,
                    "dirname": session_info.dirname,
                    "client_id": client.client_id,
                    "hostname": client.hostname,
                }
                all_sessions.append(session_dict)

        # Update session list
        self.all_sessions = all_sessions

    async def _monitor_heartbeats(self):
        """Monitor client heartbeats and remove dead connections."""
        while True:
            await asyncio.sleep(self.heartbeat_interval)

            now = datetime.now()
            timeout_threshold = timedelta(seconds=self.heartbeat_timeout)

            # Check all clients
            dead_clients: list[str] = []
            for client_id, client in self.clients.items():
                if now - client.last_heartbeat > timeout_threshold:
                    logger.warning(f"Client {client_id} heartbeat timeout")
                    dead_clients.append(client_id)

            # Remove dead clients
            for dead_client_id in dead_clients:
                client = self.clients.get(dead_client_id)
                if client:
                    await client.websocket.close()

    async def execute_command(
        self, session_name: str, command: str, timeout: float = 30.0
    ) -> dict[str, Any]:
        """Execute command on a specific session.

        Args:
            session_name: Target session name
            command: Command to execute
            timeout: Command timeout in seconds

        Returns:
            Command execution result
        """
        # Find which client owns this session
        target_client = None
        for client in self.clients.values():
            if session_name in client.sessions:
                target_client = client
                break

        if not target_client:
            return {"success": False, "error": f"Session '{session_name}' not found"}

        # Generate request ID
        request_id = str(uuid.uuid4())

        # Send execute command message
        exec_msg = ProtocolHelper.create_execute_command(
            request_id=request_id,
            session_name=session_name,
            command=command,
            timeout=timeout,
        )

        try:
            await target_client.websocket.send(exec_msg.to_json())

            # In a full implementation, we would wait for the response
            # with the matching request_id
            # For now, return a placeholder
            return {"success": True, "request_id": request_id, "status": "sent"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_all_sessions(self) -> list[dict[str, Any]]:
        """Get all available sessions across all clients."""
        sessions: list[dict[str, Any]] = []
        for client in self.clients.values():
            for session_info in client.sessions.values():
                session_dict = session_info.to_dict()
                session_dict["client_id"] = client.client_id
                session_dict["client_hostname"] = client.hostname
                session_dict["client_platform"] = client.platform
                sessions.append(session_dict)
        return sessions


async def main():
    """Main entry point for server."""
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Parse arguments
    host = "0.0.0.0"
    port = 8000

    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])

    # Create and start server
    server = CodemuxServer(host=host, port=port)

    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Server shutting down...")


if __name__ == "__main__":
    asyncio.run(main())
