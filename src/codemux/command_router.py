"""Command routing and session management."""

import asyncio
import re
from typing import Any

from codemux.output_processor import OutputProcessor
from codemux.tmux_controller import TmuxController


class CommandRouter:
    """Router for parsing and routing commands to tmux sessions."""

    def __init__(
        self,
        tmux_controller: TmuxController,
        output_processor: OutputProcessor | None = None,
    ) -> None:
        """Initialize command router.

        Args:
            tmux_controller: The tmux controller instance.
            output_processor: Optional output processor. If None, creates one.
        """
        self.tmux = tmux_controller
        self.output_processor = output_processor or OutputProcessor(tmux_controller)
        self.current_session: str | None = None
        self.sessions: dict[str, dict[str, Any]] = {}

    def parse_input(self, user_input: str) -> tuple[str, str | None, str]:
        """Parse user input and determine command type.

        Args:
            user_input: The user's input string.

        Returns:
            Tuple of (command_type, session_id, command).
        """
        user_input = user_input.strip()

        # Status query (support multiple languages)
        if user_input.lower() in ["status", "all sessions", "状态", "所有会话"]:
            return "status_query", None, user_input

        # Session switching patterns
        switch_patterns = [
            r"switch to (\w+)",
            r"切换到(\w+)",
            r"go to (\w+)",
            r"切换到\s*(\w+)\s*目录",
        ]
        for pattern in switch_patterns:
            match = re.match(pattern, user_input.lower())
            if match:
                session_id = match.group(1)
                return "session_command", session_id, ""

        # Specified session: #sessionId command
        if user_input.startswith("#"):
            parts = user_input[1:].split(" ", 1)
            session_id = parts[0]
            command = parts[1] if len(parts) > 1 else ""
            return "session_command", session_id, command
        else:
            # Send to current active session
            return "current_session", self.current_session, user_input

    def find_session(self, session_id: str) -> str | None:
        """Fuzzy match session name.

        Args:
            session_id: The session identifier to match.

        Returns:
            The matched session name or None if not found.
        """
        # Exact match first
        for name in self.sessions:
            if name == session_id:
                return name

        # Match by directory name (hostname_dirname -> dirname)
        for name in self.sessions:
            if name.endswith(f"_{session_id}"):
                return name

        # Partial match (case-insensitive)
        for name in self.sessions:
            if session_id.lower() in name.lower():
                return name

        return None

    async def route_command(self, user_input: str) -> str:
        """Route command to appropriate handler.

        Args:
            user_input: The user's input string.

        Returns:
            Response message.
        """
        command_type, session_id, command = self.parse_input(user_input)

        if command_type == "status_query":
            return self.handle_status_query()
        elif command_type == "session_command":
            return await self.handle_session_command(session_id, command)
        elif command_type == "current_session":
            if session_id:
                return await self.handle_session_command(session_id, command)
            else:
                return (
                    "Please specify a session first (use #sessionName) or check status"
                )

        return "Unknown command"

    def route_command_sync(self, user_input: str) -> str:
        """Synchronous wrapper for route_command.

        Args:
            user_input: The user's input string.

        Returns:
            Response message.
        """
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.route_command(user_input))
        except RuntimeError:
            # No event loop running, create a new one
            return asyncio.run(self.route_command(user_input))

    def handle_status_query(self) -> str:
        """Handle status query command.

        Returns:
            Status information for all sessions.
        """
        if not self.sessions:
            return "No Claude Code sessions discovered"

        status_list = []
        for name, data in self.sessions.items():
            current_indicator = "* " if name == self.current_session else "  "
            status_list.append(
                f"{current_indicator}{name}: {data.get('status', 'unknown')}"
            )

        return f"Active sessions ({len(self.sessions)}):\n" + "\n".join(status_list)

    async def handle_session_command(self, session_id: str | None, command: str) -> str:
        """Handle session command.

        Args:
            session_id: The target session ID.
            command: The command to execute.

        Returns:
            Response message.
        """
        if not session_id:
            return "No session specified"

        # Fuzzy match session name
        matched_session = self.find_session(session_id)
        if not matched_session:
            available = list(self.sessions.keys())
            return f"Session '{session_id}' not found. Available sessions: {', '.join(available)}"

        # Update current active session
        self.current_session = matched_session

        if not command:
            # Just switching session
            return f"Switched to session '{matched_session}'"

        # Send command to tmux and wait for response
        try:
            response_data = await self.output_processor.send_command_with_response(
                matched_session, command
            )

            if response_data["success"]:
                output = response_data["output"]
                response_time = response_data["response_time"]
                processed_output = self.output_processor.process_output(output)

                return (
                    f"[{matched_session}] (⏱️ {response_time:.1f}s)\n{processed_output}"
                )
            else:
                error = response_data.get("error", "Unknown error")
                return f"[{matched_session}] Error: {error}"

        except Exception as e:
            return f"[{matched_session}] Exception: {str(e)}"

    def update_sessions(self, sessions: list[dict[str, Any]]) -> None:
        """Update the sessions dictionary.

        Args:
            sessions: List of session information from TmuxController.
        """
        self.sessions = {}
        for session_info in sessions:
            name = session_info["name"]
            self.sessions[name] = {
                "name": name,
                "status": "active",  # For now, always active
                "current_path": session_info["current_path"],
                "dirname": session_info["dirname"],
                "tmux_session_name": session_info["tmux_session_name"],
            }
