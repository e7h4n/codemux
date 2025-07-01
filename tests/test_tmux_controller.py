"""Tests for TmuxController."""

from unittest.mock import Mock, patch

from codemux.tmux_controller import TmuxController


class TestTmuxController:
    """Test cases for TmuxController."""

    @patch("codemux.tmux_controller.libtmux.Server")
    @patch("codemux.tmux_controller.socket.gethostname")
    def test_init(self, mock_gethostname, mock_server_class):
        """Test TmuxController initialization."""
        mock_gethostname.return_value = "test-host"
        mock_server = Mock()
        mock_server_class.return_value = mock_server

        controller = TmuxController()

        assert controller.hostname == "test-host"
        assert controller.server == mock_server
        mock_server_class.assert_called_once()

    def test_is_running_claude_true(self, mock_pane_with_claude):
        """Test _is_running_claude returns True for Claude Code."""
        controller = TmuxController()

        result = controller._is_running_claude(mock_pane_with_claude)

        assert result is True
        mock_pane_with_claude.cmd.assert_called_once_with(
            "display", "-p", "#{pane_current_command}"
        )

    def test_is_running_claude_false(self, mock_pane_without_claude):
        """Test _is_running_claude returns False for non-Claude processes."""
        controller = TmuxController()

        result = controller._is_running_claude(mock_pane_without_claude)

        assert result is False

    def test_is_running_claude_exception(self):
        """Test _is_running_claude handles exceptions gracefully."""
        controller = TmuxController()
        pane = Mock()
        pane.cmd.side_effect = Exception("Command failed")

        result = controller._is_running_claude(pane)

        assert result is False

    @patch("codemux.tmux_controller.socket.gethostname")
    def test_create_session_info(self, mock_gethostname, mock_pane_with_claude):
        """Test _create_session_info creates correct session information."""
        mock_gethostname.return_value = "test-host"
        controller = TmuxController()

        session = Mock()
        session.name = "test-session"

        result = controller._create_session_info(session, mock_pane_with_claude)

        assert result == {
            "name": "test-host_frontend",
            "tmux_session_name": "test-session",
            "window_name": "window1",
            "pane_id": "pane1",
            "current_path": "/home/user/projects/frontend",
            "dirname": "frontend",
            "hostname": "test-host",
        }

    @patch("codemux.tmux_controller.socket.gethostname")
    def test_create_session_info_edge_cases(self, mock_gethostname):
        """Test _create_session_info handles edge cases."""
        mock_gethostname.return_value = "test-host"
        controller = TmuxController()

        session = Mock()
        session.name = "test-session"

        # Test with root directory
        pane = Mock()
        pane.current_path = "/"
        pane.window = Mock(name="window1")
        pane.id = "pane1"

        result = controller._create_session_info(session, pane)
        assert result["dirname"] == "root"
        assert result["name"] == "test-host_root"

        # Test with no path
        pane.current_path = None
        result = controller._create_session_info(session, pane)
        assert result["dirname"] == "unknown"
        assert result["name"] == "test-host_unknown"

    @patch("codemux.tmux_controller.libtmux.Server")
    @patch("codemux.tmux_controller.socket.gethostname")
    def test_discover_claude_sessions(
        self,
        mock_gethostname,
        mock_server_class,
        mock_pane_with_claude,
        mock_pane_without_claude,
    ):
        """Test discover_claude_sessions finds Claude Code sessions."""
        mock_gethostname.return_value = "test-host"

        # Set up mock server with sessions
        mock_server = Mock()
        mock_server_class.return_value = mock_server

        # Create mock session with windows and panes
        session = Mock()
        session.name = "test-session"

        window = Mock()
        window.panes = [mock_pane_with_claude, mock_pane_without_claude]

        session.windows = [window]
        mock_server.sessions = [session]

        controller = TmuxController()
        result = controller.discover_claude_sessions()

        # Should only find the pane running Claude
        assert len(result) == 1
        assert result[0]["name"] == "test-host_frontend"
        assert result[0]["tmux_session_name"] == "test-session"

    @patch("codemux.tmux_controller.libtmux.Server")
    def test_discover_claude_sessions_empty(self, mock_server_class):
        """Test discover_claude_sessions returns empty list when no Claude sessions."""
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        mock_server.sessions = []

        controller = TmuxController()
        result = controller.discover_claude_sessions()

        assert result == []
