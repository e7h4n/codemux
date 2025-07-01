"""Type stubs for websockets."""

from collections.abc import Awaitable, Callable
from typing import Any

from websockets.asyncio.client import ClientConnection
from websockets.asyncio.server import ServerConnection

class connect:
    def __init__(self, uri: str, **kwargs: Any) -> None: ...
    async def __aenter__(self) -> ClientConnection: ...
    async def __aexit__(self, *args: Any) -> None: ...

class serve:
    def __init__(
        self,
        handler: Callable[[ServerConnection], Awaitable[None]],
        host: str,
        port: int,
        **kwargs: Any,
    ) -> None: ...
    async def __aenter__(self) -> Any: ...
    async def __aexit__(self, *args: Any) -> None: ...

class ConnectionClosed(Exception): ...

class exceptions:
    ConnectionClosed = ConnectionClosed
