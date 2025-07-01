"""WebSocket protocol definitions for Codemux C/S communication."""

import json
import time
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class MessageType(Enum):
    """Message types for WebSocket communication."""

    # Client -> Server
    REGISTER = "register"
    HEARTBEAT = "heartbeat"
    SESSION_UPDATE = "session_update"
    COMMAND_RESPONSE = "command_response"
    ERROR = "error"
    AUTH = "auth"

    # Server -> Client
    REGISTER_ACK = "register_ack"
    EXECUTE_COMMAND = "execute_command"
    QUERY_STATUS = "query_status"
    CONTROL = "control"
    AUTH_RESULT = "auth_result"


class SessionAction(Enum):
    """Session update actions."""

    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"


class ErrorType(Enum):
    """Error types."""

    SESSION_NOT_FOUND = "session_not_found"
    COMMAND_FAILED = "command_failed"
    INTERNAL_ERROR = "internal_error"
    AUTH_FAILED = "auth_failed"


@dataclass
class Message:
    """Base message structure."""

    type: MessageType
    timestamp: float
    data: dict[str, Any]

    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(
            {"type": self.type.value, "timestamp": self.timestamp, "data": self.data}
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Message":
        """Create message from JSON string."""
        data = json.loads(json_str)
        return cls(
            type=MessageType(data["type"]),
            timestamp=data["timestamp"],
            data=data["data"],
        )

    @classmethod
    def create(cls, msg_type: MessageType, data: dict[str, Any]) -> "Message":
        """Create a new message with current timestamp."""
        return cls(type=msg_type, timestamp=time.time(), data=data)


@dataclass
class SessionInfo:
    """Session information structure."""

    name: str
    tmux_session_name: str
    current_path: str
    dirname: str
    pane_id: str | None = None
    window_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionInfo":
        """Create from dictionary."""
        return cls(**data)


class ProtocolHelper:
    """Helper class for creating protocol messages."""

    @staticmethod
    def create_register(
        client_id: str, hostname: str, platform: str, sessions: list[dict[str, Any]]
    ) -> Message:
        """Create register message."""
        return Message.create(
            MessageType.REGISTER,
            {
                "client_id": client_id,
                "hostname": hostname,
                "platform": platform,
                "sessions": sessions,
            },
        )

    @staticmethod
    def create_heartbeat(client_id: str, sessions_count: int) -> Message:
        """Create heartbeat message."""
        return Message.create(
            MessageType.HEARTBEAT,
            {"client_id": client_id, "sessions_count": sessions_count},
        )

    @staticmethod
    def create_command_response(
        request_id: str,
        session_name: str,
        success: bool,
        output: str = "",
        response_time: float = 0.0,
        error: str | None = None,
    ) -> Message:
        """Create command response message."""
        return Message.create(
            MessageType.COMMAND_RESPONSE,
            {
                "request_id": request_id,
                "session_name": session_name,
                "success": success,
                "output": output,
                "response_time": response_time,
                "error": error,
            },
        )

    @staticmethod
    def create_execute_command(
        request_id: str, session_name: str, command: str, timeout: float = 30.0
    ) -> Message:
        """Create execute command message."""
        return Message.create(
            MessageType.EXECUTE_COMMAND,
            {
                "request_id": request_id,
                "session_name": session_name,
                "command": command,
                "timeout": timeout,
            },
        )

    @staticmethod
    def create_error(
        error_type: ErrorType, message: str, details: dict[str, Any] | None = None
    ) -> Message:
        """Create error message."""
        return Message.create(
            MessageType.ERROR,
            {
                "error_type": error_type.value,
                "message": message,
                "details": details or {},
            },
        )
