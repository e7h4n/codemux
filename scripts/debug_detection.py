#!/usr/bin/env python3
"""Debug script for session detection."""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codemux.tmux_controller import TmuxController


def debug_detection():
    """Debug session detection logic."""
    print("🔍 Debugging Claude Code Detection...\n")

    controller = TmuxController()

    # List all tmux sessions
    print("All tmux sessions:")
    for session in controller.server.sessions:
        print(f"  Session: {session.name}")
        for window in session.windows:
            print(f"    Window: {window.name}")
            for pane in window.panes:
                # Get command
                try:
                    result = pane.cmd("display", "-p", "#{pane_current_command}")
                    command = (
                        str(result.stdout[0]) if result and result.stdout else "unknown"
                    )
                except Exception as e:
                    command = f"error: {e}"

                # Get content
                try:
                    content_result = pane.cmd("capture-pane", "-p")
                    content = (
                        "\n".join(content_result.stdout)
                        if content_result and content_result.stdout
                        else ""
                    )
                    content_preview = (
                        content[:200].replace("\n", "\\n") if content else ""
                    )
                except Exception as e:
                    content_preview = f"error: {e}"

                print(f"      Pane {pane.id}: command='{command}'")
                print(f"        Content preview: '{content_preview}'")

                # Test detection
                is_claude = controller._is_running_claude(pane)
                print(f"        Is Claude? {is_claude}")
                print()


if __name__ == "__main__":
    debug_detection()
