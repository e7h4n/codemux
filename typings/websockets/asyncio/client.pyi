"""Type stubs for websockets.asyncio.client."""

from typing import Any

class ClientConnection:
    async def send(self, message: str | bytes) -> None: ...
    async def recv(self) -> str | bytes: ...
    async def close(self) -> None: ...
    @property
    def closed(self) -> bool: ...
    def __aiter__(self) -> Any: ...
    async def __anext__(self) -> str | bytes: ...
