"""Tmux session discovery and control."""

import os
import socket
from typing import Any

import libtmux
from libtmux.pane import Pane
from libtmux.server import Server
from libtmux.session import Session


class TmuxController:
    """Controller for discovering and managing tmux sessions."""

    def __init__(self) -> None:
        """Initialize tmux controller."""
        self.server: Server = libtmux.Server()
        self.hostname: str = socket.gethostname()

    def discover_claude_sessions(self) -> list[dict[str, Any]]:
        """Discover all tmux sessions running Claude Code.

        Returns:
            List of session information dictionaries.
        """
        sessions: list[dict[str, Any]] = []

        for session in self.server.sessions:
            for window in session.windows:
                for pane in window.panes:
                    if self._is_running_claude(pane):
                        session_info = self._create_session_info(session, pane)
                        sessions.append(session_info)

        return sessions

    def _is_running_claude(self, pane: Pane) -> bool:
        """Check if pane is running Claude Code.

        Args:
            pane: The tmux pane to check.

        Returns:
            True if the pane is running Claude Code, False otherwise.
        """
        try:
            # Get current command in the pane
            result = pane.cmd("display", "-p", "#{pane_current_command}")
            if result and result.stdout:
                # stdout is always a list
                command = str(result.stdout[0]) if result.stdout else ""
                return "claude" in command.lower()
        except Exception:
            # If we can't get the command, assume it's not Claude
            pass

        return False

    def _create_session_info(self, session: Session, pane: Pane) -> dict[str, Any]:
        """Create session information dictionary.

        Args:
            session: The tmux session.
            pane: The pane running Claude Code.

        Returns:
            Dictionary containing session information.
        """
        # Get current path - libtmux might not have this attribute in all versions
        current_path = ""
        try:
            path_attr = getattr(pane, "current_path", "")
            if path_attr is not None:
                current_path = str(path_attr)
        except Exception:
            pass
        dirname = os.path.basename(current_path) if current_path else "unknown"

        # Handle edge cases for directory name
        if not dirname or dirname == "/":
            dirname = "root"

        return {
            "name": f"{self.hostname}_{dirname}",
            "tmux_session_name": session.name,
            "window_name": pane.window.name,
            "pane_id": pane.id,
            "current_path": current_path,
            "dirname": dirname,
            "hostname": self.hostname,
        }
