"""Tests for Codemux server."""

import json
from unittest.mock import AsyncMock, Mock

import pytest
from codemux.protocol import MessageType, SessionInfo
from codemux.protocol import ProtocolHelper as BaseProtocolHelper
from codemux.server import ClientConnection, CodemuxServer


@pytest.fixture
def server():
    """Create a test server."""
    return CodemuxServer(host="localhost", port=0)


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket."""
    ws = AsyncMock()
    ws.closed = False
    ws.remote_address = ("127.0.0.1", 12345)
    return ws


@pytest.fixture
def sample_sessions():
    """Sample session data."""
    return [
        {
            "name": "host1_project1",
            "tmux_session_name": "main",
            "current_path": "/home/user/project1",
            "dirname": "project1",
            "window_name": "editor",
            "pane_id": "pane1",
        },
        {
            "name": "host1_project2",
            "tmux_session_name": "dev",
            "current_path": "/home/user/project2",
            "dirname": "project2",
            "window_name": "terminal",
            "pane_id": "pane2",
        },
    ]


def test_server_initialization():
    """Test server initialization."""
    server = CodemuxServer(host="0.0.0.0", port=8080)

    assert server.host == "0.0.0.0"
    assert server.port == 8080
    assert server.heartbeat_interval == 30
    assert server.heartbeat_timeout == 90
    assert len(server.clients) == 0
    assert len(server.auth_tokens) == 0


def test_server_with_auth_tokens():
    """Test server with authentication tokens."""
    tokens = {"token1", "token2"}
    server = CodemuxServer(auth_tokens=tokens)

    assert server.auth_tokens == tokens


def test_client_connection():
    """Test ClientConnection class."""
    ws = Mock()
    client = ClientConnection(ws, "client1")

    assert client.websocket == ws
    assert client.client_id == "client1"
    assert client.hostname == ""
    assert client.platform == ""
    assert len(client.sessions) == 0
    assert not client.authenticated


@pytest.mark.asyncio
async def test_handle_auth_success(server, mock_websocket):
    """Test successful authentication."""
    server.auth_tokens = {"valid_token"}

    auth_msg = ProtocolHelper.create_auth(client_id="client1", auth_token="valid_token")

    success = await server._handle_auth(mock_websocket, auth_msg)

    assert success
    mock_websocket.send.assert_called_once()

    # Check the response
    sent_data = mock_websocket.send.call_args[0][0]
    response_msg = json.loads(sent_data)
    assert response_msg["type"] == "auth_result"
    assert response_msg["data"]["success"] is True


@pytest.mark.asyncio
async def test_handle_auth_failure(server, mock_websocket):
    """Test failed authentication."""
    server.auth_tokens = {"valid_token"}

    auth_msg = ProtocolHelper.create_auth(
        client_id="client1", auth_token="invalid_token"
    )

    success = await server._handle_auth(mock_websocket, auth_msg)

    assert not success
    mock_websocket.send.assert_called_once()

    # Check the response
    sent_data = mock_websocket.send.call_args[0][0]
    response_msg = json.loads(sent_data)
    assert response_msg["type"] == "auth_result"
    assert response_msg["data"]["success"] is False


def test_update_sessions(server, sample_sessions):
    """Test session list update."""
    # Create mock clients with sessions
    client1 = ClientConnection(Mock(), "client1")
    client1.hostname = "host1"
    client1.sessions = {
        "host1_project1": SessionInfo.from_dict(sample_sessions[0]),
        "host1_project2": SessionInfo.from_dict(sample_sessions[1]),
    }

    server.clients["client1"] = client1

    # Update sessions
    server._update_sessions()

    # Check session list
    assert len(server.all_sessions) == 2
    assert server.all_sessions[0]["name"] == "host1_project1"
    assert server.all_sessions[0]["client_id"] == "client1"
    assert server.all_sessions[1]["name"] == "host1_project2"
    assert server.all_sessions[1]["client_id"] == "client1"


@pytest.mark.asyncio
async def test_execute_command_session_not_found(server):
    """Test execute command with non-existent session."""
    result = await server.execute_command("nonexistent", "ls")

    assert not result["success"]
    assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_execute_command_success(server, mock_websocket):
    """Test successful command execution."""
    # Create a client with a session
    client = ClientConnection(mock_websocket, "client1")
    client.sessions["host1_project1"] = SessionInfo(
        name="host1_project1",
        tmux_session_name="main",
        current_path="/home/user/project1",
        dirname="project1",
    )

    server.clients["client1"] = client

    # Execute command
    result = await server.execute_command("host1_project1", "ls", timeout=10.0)

    assert result["success"]
    assert "request_id" in result
    assert result["status"] == "sent"

    # Check that command was sent
    mock_websocket.send.assert_called_once()
    sent_data = mock_websocket.send.call_args[0][0]
    sent_msg = json.loads(sent_data)
    assert sent_msg["type"] == "execute_command"
    assert sent_msg["data"]["session_name"] == "host1_project1"
    assert sent_msg["data"]["command"] == "ls"
    assert sent_msg["data"]["timeout"] == 10.0


def test_get_all_sessions(server, sample_sessions):
    """Test getting all sessions."""
    # Create mock clients with sessions
    client1 = ClientConnection(Mock(), "client1")
    client1.hostname = "host1"
    client1.platform = "linux"
    client1.sessions = {"host1_project1": SessionInfo.from_dict(sample_sessions[0])}

    client2 = ClientConnection(Mock(), "client2")
    client2.hostname = "host2"
    client2.platform = "darwin"
    client2.sessions = {"host1_project2": SessionInfo.from_dict(sample_sessions[1])}

    server.clients["client1"] = client1
    server.clients["client2"] = client2

    # Get all sessions
    sessions = server.get_all_sessions()

    assert len(sessions) == 2

    # Check first session
    session1 = next(s for s in sessions if s["name"] == "host1_project1")
    assert session1["client_id"] == "client1"
    assert session1["client_hostname"] == "host1"
    assert session1["client_platform"] == "linux"

    # Check second session
    session2 = next(s for s in sessions if s["name"] == "host1_project2")
    assert session2["client_id"] == "client2"
    assert session2["client_hostname"] == "host2"
    assert session2["client_platform"] == "darwin"


@pytest.mark.asyncio
async def test_handle_session_update_added(server):
    """Test handling session add update."""
    client = ClientConnection(Mock(), "client1")
    server.clients["client1"] = client

    # Mock session update
    server._update_sessions = Mock()

    session_data = {
        "name": "host1_newproject",
        "tmux_session_name": "new",
        "current_path": "/home/user/newproject",
        "dirname": "newproject",
    }

    msg = ProtocolHelper.create_session_update(action="added", session=session_data)

    await server._handle_session_update(client, msg)

    # Check session was added
    assert "host1_newproject" in client.sessions
    assert client.sessions["host1_newproject"].name == "host1_newproject"

    # Check sessions were updated
    server._update_sessions.assert_called_once()


@pytest.mark.asyncio
async def test_handle_session_update_removed(server):
    """Test handling session remove update."""
    client = ClientConnection(Mock(), "client1")

    # Add initial session
    session_info = SessionInfo(
        name="host1_oldproject",
        tmux_session_name="old",
        current_path="/home/user/oldproject",
        dirname="oldproject",
    )
    client.sessions["host1_oldproject"] = session_info

    server.clients["client1"] = client

    # Mock session update
    server._update_sessions = Mock()

    msg = ProtocolHelper.create_session_update(
        action="removed", session=session_info.to_dict()
    )

    await server._handle_session_update(client, msg)

    # Check session was removed
    assert "host1_oldproject" not in client.sessions

    # Check sessions were updated
    server._update_sessions.assert_called_once()


# Helper for protocol tests
def create_auth_message(client_id, auth_token):
    """Create AUTH message."""
    return {
        "type": MessageType.AUTH.value,
        "timestamp": 1234567890,
        "data": {"client_id": client_id, "auth_token": auth_token},
    }


class ProtocolHelper(BaseProtocolHelper):
    """Extended protocol helper for tests."""

    @staticmethod
    def create_auth(client_id, auth_token):
        """Create AUTH message."""
        from codemux.protocol import Message, MessageType

        return Message.create(
            MessageType.AUTH, {"client_id": client_id, "auth_token": auth_token}
        )

    @staticmethod
    def create_session_update(action, session):
        """Create SESSION_UPDATE message."""
        from codemux.protocol import Message, MessageType

        return Message.create(
            MessageType.SESSION_UPDATE, {"action": action, "session": session}
        )
