"""Type definitions for external libraries."""

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    # These imports are only for type checking
    from websockets.asyncio.client import ClientConnection as WSClientConnection
    from websockets.asyncio.server import ServerConnection

    WebSocketServerProtocol = ServerConnection
    WebSocketClientProtocol = WSClientConnection
else:
    # At runtime, create a class that accepts any arguments
    class WebSocketServerProtocol:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class WebSocketClientProtocol:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass


@runtime_checkable
class WebSocketProtocol(Protocol):
    """Protocol for WebSocket connections."""

    async def send(self, message: str | bytes) -> None:
        """Send a message."""
        ...

    async def recv(self) -> str | bytes:
        """Receive a message."""
        ...

    async def close(self) -> None:
        """Close the connection."""
        ...

    @property
    def closed(self) -> bool:
        """Check if connection is closed."""
        ...
