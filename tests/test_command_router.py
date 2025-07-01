"""Tests for CommandRouter."""

from unittest.mock import Mock

import pytest
from codemux.command_router import CommandRouter


class TestCommandRouter:
    """Test cases for CommandRouter."""

    @pytest.fixture
    def mock_tmux_controller(self):
        """Create a mock tmux controller."""
        return Mock()

    @pytest.fixture
    def router(self, mock_tmux_controller):
        """Create a CommandRouter instance."""
        return CommandRouter(mock_tmux_controller)

    @pytest.fixture
    def router_with_sessions(self, router):
        """Create a router with sample sessions."""
        sessions = [
            {
                "name": "macbook_frontend",
                "current_path": "/Users/dev/projects/frontend",
                "dirname": "frontend",
                "tmux_session_name": "session1",
            },
            {
                "name": "macbook_backend",
                "current_path": "/Users/dev/projects/backend",
                "dirname": "backend",
                "tmux_session_name": "session2",
            },
            {
                "name": "server_ml-model",
                "current_path": "/home/dev/ml-model",
                "dirname": "ml-model",
                "tmux_session_name": "session3",
            },
        ]
        router.update_sessions(sessions)
        return router

    def test_init(self, mock_tmux_controller):
        """Test CommandRouter initialization."""
        router = CommandRouter(mock_tmux_controller)

        assert router.tmux == mock_tmux_controller
        assert router.current_session is None
        assert router.sessions == {}

    def test_parse_input_status_query_english(self, router):
        """Test parsing status query in English."""
        result = router.parse_input("status")
        assert result == ("status_query", None, "status")

        result = router.parse_input("all sessions")
        assert result == ("status_query", None, "all sessions")

    def test_parse_input_status_query_chinese(self, router):
        """Test parsing status query in Chinese."""
        result = router.parse_input("状态")
        assert result == ("status_query", None, "状态")

        result = router.parse_input("所有会话")
        assert result == ("status_query", None, "所有会话")

    def test_parse_input_session_switch_english(self, router):
        """Test parsing session switch commands in English."""
        result = router.parse_input("switch to frontend")
        assert result == ("session_command", "frontend", "")

        result = router.parse_input("go to backend")
        assert result == ("session_command", "backend", "")

    def test_parse_input_session_switch_chinese(self, router):
        """Test parsing session switch commands in Chinese."""
        result = router.parse_input("切换到frontend")
        assert result == ("session_command", "frontend", "")

        result = router.parse_input("切换到 backend 目录")
        assert result == ("session_command", "backend", "")

    def test_parse_input_hash_syntax(self, router):
        """Test parsing #sessionId syntax."""
        result = router.parse_input("#frontend")
        assert result == ("session_command", "frontend", "")

        result = router.parse_input("#backend npm test")
        assert result == ("session_command", "backend", "npm test")

    def test_parse_input_current_session(self, router):
        """Test parsing commands for current session."""
        result = router.parse_input("npm start")
        assert result == ("current_session", None, "npm start")

        router.current_session = "frontend"
        result = router.parse_input("npm test")
        assert result == ("current_session", "frontend", "npm test")

    def test_find_session_exact_match(self, router_with_sessions):
        """Test exact session name matching."""
        result = router_with_sessions.find_session("macbook_frontend")
        assert result == "macbook_frontend"

    def test_find_session_directory_match(self, router_with_sessions):
        """Test directory name matching."""
        result = router_with_sessions.find_session("frontend")
        assert result == "macbook_frontend"

        result = router_with_sessions.find_session("backend")
        assert result == "macbook_backend"

    def test_find_session_partial_match(self, router_with_sessions):
        """Test partial matching."""
        result = router_with_sessions.find_session("ml")
        assert result == "server_ml-model"

        result = router_with_sessions.find_session("server")
        assert result == "server_ml-model"

    def test_find_session_not_found(self, router_with_sessions):
        """Test session not found."""
        result = router_with_sessions.find_session("nonexistent")
        assert result is None

    def test_update_sessions(self, router):
        """Test updating sessions dictionary."""
        sessions = [
            {
                "name": "test_session",
                "current_path": "/test/path",
                "dirname": "test",
                "tmux_session_name": "tmux_test",
            }
        ]

        router.update_sessions(sessions)

        assert len(router.sessions) == 1
        assert "test_session" in router.sessions
        assert router.sessions["test_session"]["status"] == "active"

    def test_handle_status_query_empty(self, router):
        """Test status query with no sessions."""
        result = router.handle_status_query()
        assert result == "No Claude Code sessions discovered"

    def test_handle_status_query_with_sessions(self, router_with_sessions):
        """Test status query with sessions."""
        result = router_with_sessions.handle_status_query()

        assert "Active sessions (3):" in result
        assert "macbook_frontend: active" in result
        assert "macbook_backend: active" in result
        assert "server_ml-model: active" in result

    def test_handle_status_query_with_current_session(self, router_with_sessions):
        """Test status query shows current session indicator."""
        router_with_sessions.current_session = "macbook_frontend"
        result = router_with_sessions.handle_status_query()

        lines = result.split("\n")
        # Find the frontend line and check it has the indicator
        frontend_line = next(line for line in lines if "macbook_frontend" in line)
        assert frontend_line.startswith("* ")

    def test_handle_session_command_no_session(self, router):
        """Test session command with no session specified."""
        import asyncio

        result = asyncio.run(router.handle_session_command(None, "test"))
        assert result == "No session specified"

    def test_handle_session_command_not_found(self, router_with_sessions):
        """Test session command with non-existent session."""
        import asyncio

        result = asyncio.run(
            router_with_sessions.handle_session_command("nonexistent", "test")
        )
        assert "not found" in result
        assert "Available sessions:" in result

    def test_handle_session_command_switch_only(self, router_with_sessions):
        """Test session switching without command."""
        import asyncio

        result = asyncio.run(
            router_with_sessions.handle_session_command("frontend", "")
        )

        assert result == "Switched to session 'macbook_frontend'"
        assert router_with_sessions.current_session == "macbook_frontend"

    def test_handle_session_command_with_command(self, router_with_sessions):
        """Test session command with actual command."""
        # For this test, we'll mock the output processor to avoid real tmux calls
        from unittest.mock import AsyncMock

        router_with_sessions.output_processor.send_command_with_response = AsyncMock(
            return_value={
                "success": True,
                "output": "test output",
                "response_time": 1.0,
            }
        )

        import asyncio

        result = asyncio.run(
            router_with_sessions.handle_session_command("backend", "npm test")
        )

        assert "test output" in result
        assert router_with_sessions.current_session == "macbook_backend"

    def test_route_command_status(self, router_with_sessions):
        """Test routing status query command."""
        result = router_with_sessions.route_command_sync("status")
        assert "Active sessions" in result

    def test_route_command_session_switch(self, router_with_sessions):
        """Test routing session switch command."""
        result = router_with_sessions.route_command_sync("switch to frontend")
        assert "Switched to session 'macbook_frontend'" in result

    def test_route_command_hash_syntax(self, router_with_sessions):
        """Test routing #sessionId command."""
        # Mock the output processor for this test too
        from unittest.mock import AsyncMock

        router_with_sessions.output_processor.send_command_with_response = AsyncMock(
            return_value={
                "success": True,
                "output": "npm start output",
                "response_time": 0.5,
            }
        )

        result = router_with_sessions.route_command_sync("#backend npm start")
        assert "npm start output" in result

    def test_route_command_current_session_no_active(self, router_with_sessions):
        """Test routing to current session when none is active."""
        result = router_with_sessions.route_command_sync("npm test")
        assert "Please specify a session first" in result

    def test_route_command_current_session_with_active(self, router_with_sessions):
        """Test routing to current session when one is active."""
        # Mock the output processor
        from unittest.mock import AsyncMock

        router_with_sessions.output_processor.send_command_with_response = AsyncMock(
            return_value={
                "success": True,
                "output": "npm test output",
                "response_time": 0.8,
            }
        )

        router_with_sessions.current_session = "macbook_frontend"
        result = router_with_sessions.route_command_sync("npm test")
        assert "npm test output" in result
