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
                if "claude" in command.lower():
                    return True

                # Check if it's a node process that might be Claude Code
                if "node" in command.lower():
                    # Check pane content for Claude Code indicators
                    try:
                        content_result = pane.cmd("capture-pane", "-p")
                        if content_result and content_result.stdout:
                            content = "\n".join(content_result.stdout)
                            # Look for Claude Code specific text
                            claude_indicators = [
                                "claude code",
                                "do you trust the files",
                                "claude.ai",
                                "anthropic",
                                "tips for getting started",
                                "run /init to create",
                                "use claude to help",
                                "claude.md file",
                            ]
                            for indicator in claude_indicators:
                                if indicator in content.lower():
                                    return True
                    except Exception:
                        pass
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
        # Get current path using tmux command
        current_path = ""
        try:
            # Try to get path from pane
            result = pane.cmd("display", "-p", "#{pane_current_path}")
            if result and result.stdout:
                current_path = str(result.stdout[0]) if result.stdout else ""
        except Exception:
            # Fallback to getting path from pane attribute if available
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
        }

    def send_command(self, session_name: str, command: str) -> bool:
        """Send command to specified session.

        Args:
            session_name: The session name to send command to.
            command: The command text to send.

        Returns:
            True if command was sent successfully, False otherwise.
        """
        try:
            # Find the session by tmux session name
            session_info = self._find_session_by_name(session_name)
            if not session_info:
                return False

            # Get the session and pane
            session = self.server.sessions.get(
                session_name=session_info["tmux_session_name"]
            )
            if not session:
                return False

            # Find the pane running Claude Code
            target_pane = None
            for window in session.windows:
                for pane in window.panes:
                    if pane.id == session_info["pane_id"]:
                        target_pane = pane
                        break
                if target_pane:
                    break

            if not target_pane:
                return False

            # Send the command
            target_pane.send_keys(command)
            return True

        except Exception:
            return False

    def capture_screen(self, session_name: str) -> str:
        """Capture screen content from specified session.

        Args:
            session_name: The session name to capture from.

        Returns:
            Screen content as string, empty if failed.
        """
        try:
            # Find the session by name
            session_info = self._find_session_by_name(session_name)
            if not session_info:
                return ""

            # Get the session and pane
            session = self.server.sessions.get(
                session_name=session_info["tmux_session_name"]
            )
            if not session:
                return ""

            # Find the pane running Claude Code
            target_pane = None
            for window in session.windows:
                for pane in window.panes:
                    if pane.id == session_info["pane_id"]:
                        target_pane = pane
                        break
                if target_pane:
                    break

            if not target_pane:
                return ""

            # Capture pane content
            result = target_pane.cmd("capture-pane", "-p")
            if result and result.stdout:
                return "\n".join(result.stdout)

        except Exception:
            pass

        return ""

    def _find_session_by_name(self, session_name: str) -> dict[str, Any] | None:
        """Find session info by session name.

        Args:
            session_name: The session name to find.

        Returns:
            Session info dictionary or None if not found.
        """
        sessions = self.discover_claude_sessions()
        for session_info in sessions:
            if session_info["name"] == session_name:
                return session_info
        return None
