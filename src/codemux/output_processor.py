"""Output processing and response capture."""

import asyncio
import time
from typing import Any

from codemux.tmux_controller import TmuxController


class OutputProcessor:
    """Processor for capturing and analyzing tmux output."""

    def __init__(self, tmux_controller: TmuxController) -> None:
        """Initialize output processor.

        Args:
            tmux_controller: The tmux controller instance.
        """
        self.tmux = tmux_controller

    async def send_command_with_response(
        self, session_name: str, command: str, timeout: float = 30.0
    ) -> dict[str, Any]:
        """Send command and wait for response with timing.

        Args:
            session_name: The target session name.
            command: The command to send.
            timeout: Maximum time to wait for response in seconds.

        Returns:
            Dictionary containing response data.
        """
        start_time = time.time()

        # Capture screen content before sending command
        old_content = self.tmux.capture_screen(session_name)
        if not old_content:
            return {
                "success": False,
                "error": f"Failed to capture screen from session {session_name}",
                "response_time": 0.0,
            }

        # Send the command
        success = self.tmux.send_command(session_name, command)
        if not success:
            return {
                "success": False,
                "error": f"Failed to send command to session {session_name}",
                "response_time": time.time() - start_time,
            }

        # Wait for response
        response_data = await self._wait_for_response(
            session_name, old_content, start_time, timeout
        )

        return response_data

    async def _wait_for_response(
        self, session_name: str, old_content: str, start_time: float, timeout: float
    ) -> dict[str, Any]:
        """Wait for response from Claude Code.

        Args:
            session_name: The session name to monitor.
            old_content: The screen content before command was sent.
            start_time: The time when command was sent.
            timeout: Maximum time to wait.

        Returns:
            Dictionary containing response data.
        """
        check_interval = 0.5  # Check every 500ms
        last_content = old_content

        while time.time() - start_time < timeout:
            await asyncio.sleep(check_interval)

            # Capture current screen content
            current_content = self.tmux.capture_screen(session_name)
            if not current_content:
                continue

            # Check if content has changed
            if current_content != last_content:
                # Content changed - check if Claude is still working
                if self._is_claude_working(current_content):
                    # Claude is still processing, update last_content and continue waiting
                    last_content = current_content
                    continue
                else:
                    # Claude appears to be done, extract the response
                    response_time = time.time() - start_time
                    new_output = self._extract_new_content(old_content, current_content)

                    return {
                        "success": True,
                        "output": new_output,
                        "full_screen": current_content,
                        "response_time": response_time,
                        "session_name": session_name,
                    }

        # Timeout reached
        return {
            "success": False,
            "error": f"Response timeout after {timeout}s",
            "response_time": timeout,
            "session_name": session_name,
        }

    def _is_claude_working(self, screen_content: str) -> bool:
        """Check if Claude Code is still processing.

        Args:
            screen_content: Current screen content.

        Returns:
            True if Claude appears to be working, False if idle.
        """
        # Look for indicators that Claude is still working
        working_indicators = [
            "thinking...",
            "processing...",
            "working on",
            "generating",
            "analyzing",
            "creating",
            "writing",
            "reading",
            "searching",
            "executing",
            "running",
        ]

        content_lower = screen_content.lower()
        for indicator in working_indicators:
            if indicator in content_lower:
                return True

        # Check for cursor at the end (Claude waiting for more input)
        lines = screen_content.strip().split("\n")
        if lines:
            last_line = lines[-1].strip()
            # If last line ends with a prompt-like pattern, Claude might be waiting
            if (
                last_line.endswith(">")
                or last_line.endswith("$")
                or last_line.endswith(":")
            ):
                return False

        # Default to not working if no clear indicators
        return False

    def _extract_new_content(self, old_content: str, new_content: str) -> str:
        """Extract new content from screen comparison.

        Args:
            old_content: Screen content before command.
            new_content: Screen content after response.

        Returns:
            The new content that was added.
        """
        old_lines = old_content.split("\n")
        new_lines = new_content.split("\n")

        # Simple approach: if new content has more lines, return the additional lines
        if len(new_lines) > len(old_lines):
            additional_lines = new_lines[len(old_lines) :]
            return "\n".join(additional_lines).strip()

        # If same number of lines, check if content at the end has changed
        if len(new_lines) >= 10:
            # Return last 10 lines as they likely contain the response
            return "\n".join(new_lines[-10:]).strip()

        # Fallback: return the entire new content
        return new_content.strip()

    def process_output(self, output: str, max_length: int = 500) -> str:
        """Process output for display.

        Args:
            output: The raw output to process.
            max_length: Maximum length before summarization is needed.

        Returns:
            Processed output string.
        """
        if not output.strip():
            return "No output received"

        # Return short content directly
        if len(output) <= max_length:
            return output.strip()

        # For now, truncate long output with indication
        # TODO: Implement Claude API summarization
        truncated = output[:max_length].strip()
        return f"{truncated}...\n\n[Output truncated - {len(output)} total characters]"
