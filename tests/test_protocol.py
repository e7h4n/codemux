"""Tests for WebSocket protocol."""

import json
import time

from codemux.protocol import (
    ErrorType,
    Message,
    MessageType,
    ProtocolHelper,
    SessionAction,
    SessionInfo,
)


def test_message_creation():
    """Test message creation."""
    msg = Message.create(
        MessageType.REGISTER, {"client_id": "test-client", "sessions": []}
    )

    assert msg.type == MessageType.REGISTER
    assert msg.data["client_id"] == "test-client"
    assert isinstance(msg.timestamp, float)
    assert msg.timestamp > 0


def test_message_json_serialization():
    """Test message JSON serialization."""
    msg = Message.create(MessageType.HEARTBEAT, {"client_id": "test-client"})

    json_str = msg.to_json()
    data = json.loads(json_str)

    assert data["type"] == "heartbeat"
    assert data["data"]["client_id"] == "test-client"
    assert "timestamp" in data


def test_message_json_deserialization():
    """Test message JSON deserialization."""
    json_str = json.dumps(
        {"type": "register", "timestamp": time.time(), "data": {"client_id": "test"}}
    )

    msg = Message.from_json(json_str)

    assert msg.type == MessageType.REGISTER
    assert msg.data["client_id"] == "test"


def test_session_info():
    """Test SessionInfo dataclass."""
    session = SessionInfo(
        name="hostname_project",
        tmux_session_name="main",
        current_path="/home/user/project",
        dirname="project",
        pane_id="pane123",
        window_name="window1",
    )

    # Test to_dict
    d = session.to_dict()
    assert d["name"] == "hostname_project"
    assert d["tmux_session_name"] == "main"
    assert d["current_path"] == "/home/user/project"
    assert d["dirname"] == "project"
    assert d["pane_id"] == "pane123"
    assert d["window_name"] == "window1"

    # Test from_dict
    session2 = SessionInfo.from_dict(d)
    assert session2.name == session.name
    assert session2.tmux_session_name == session.tmux_session_name
    assert session2.current_path == session.current_path


def test_protocol_helper_register():
    """Test ProtocolHelper.create_register."""
    sessions = [
        {
            "name": "host_proj1",
            "tmux_session_name": "main",
            "current_path": "/path/to/proj1",
            "dirname": "proj1",
        }
    ]

    msg = ProtocolHelper.create_register(
        client_id="client1", hostname="myhost", platform="linux", sessions=sessions
    )

    assert msg.type == MessageType.REGISTER
    assert msg.data["client_id"] == "client1"
    assert msg.data["hostname"] == "myhost"
    assert msg.data["platform"] == "linux"
    assert len(msg.data["sessions"]) == 1
    assert msg.data["sessions"][0]["name"] == "host_proj1"


def test_protocol_helper_heartbeat():
    """Test ProtocolHelper.create_heartbeat."""
    msg = ProtocolHelper.create_heartbeat("client1", 3)

    assert msg.type == MessageType.HEARTBEAT
    assert msg.data["client_id"] == "client1"
    assert msg.data["sessions_count"] == 3


def test_protocol_helper_command_response():
    """Test ProtocolHelper.create_command_response."""
    msg = ProtocolHelper.create_command_response(
        request_id="req123",
        session_name="host_proj",
        success=True,
        output="Command output",
        response_time=1.5,
    )

    assert msg.type == MessageType.COMMAND_RESPONSE
    assert msg.data["request_id"] == "req123"
    assert msg.data["session_name"] == "host_proj"
    assert msg.data["success"] is True
    assert msg.data["output"] == "Command output"
    assert msg.data["response_time"] == 1.5
    assert msg.data["error"] is None


def test_protocol_helper_execute_command():
    """Test ProtocolHelper.create_execute_command."""
    msg = ProtocolHelper.create_execute_command(
        request_id="req456", session_name="host_proj", command="ls -la", timeout=10.0
    )

    assert msg.type == MessageType.EXECUTE_COMMAND
    assert msg.data["request_id"] == "req456"
    assert msg.data["session_name"] == "host_proj"
    assert msg.data["command"] == "ls -la"
    assert msg.data["timeout"] == 10.0


def test_protocol_helper_error():
    """Test ProtocolHelper.create_error."""
    msg = ProtocolHelper.create_error(
        ErrorType.SESSION_NOT_FOUND,
        "Session 'test' not found",
        {"session_name": "test"},
    )

    assert msg.type == MessageType.ERROR
    assert msg.data["error_type"] == "session_not_found"
    assert msg.data["message"] == "Session 'test' not found"
    assert msg.data["details"]["session_name"] == "test"


def test_message_type_enum():
    """Test MessageType enum values."""
    assert MessageType.REGISTER.value == "register"
    assert MessageType.HEARTBEAT.value == "heartbeat"
    assert MessageType.SESSION_UPDATE.value == "session_update"
    assert MessageType.COMMAND_RESPONSE.value == "command_response"
    assert MessageType.ERROR.value == "error"
    assert MessageType.AUTH.value == "auth"
    assert MessageType.REGISTER_ACK.value == "register_ack"
    assert MessageType.EXECUTE_COMMAND.value == "execute_command"
    assert MessageType.QUERY_STATUS.value == "query_status"
    assert MessageType.CONTROL.value == "control"
    assert MessageType.AUTH_RESULT.value == "auth_result"


def test_session_action_enum():
    """Test SessionAction enum values."""
    assert SessionAction.ADDED.value == "added"
    assert SessionAction.REMOVED.value == "removed"
    assert SessionAction.CHANGED.value == "changed"


def test_error_type_enum():
    """Test ErrorType enum values."""
    assert ErrorType.SESSION_NOT_FOUND.value == "session_not_found"
    assert ErrorType.COMMAND_FAILED.value == "command_failed"
    assert ErrorType.INTERNAL_ERROR.value == "internal_error"
    assert ErrorType.AUTH_FAILED.value == "auth_failed"
