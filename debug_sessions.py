#!/usr/bin/env python3
"""Debug script to check session detection."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codemux.tmux_controller import TmuxController


def main():
    """Debug session detection."""
    print("🔍 Debugging Claude Code session detection...")
    print("=" * 50)
    
    controller = TmuxController()
    
    # List all tmux sessions
    print("📋 All tmux sessions:")
    for session in controller.server.sessions:
        print(f"  Session: {session.name}")
        for window in session.windows:
            print(f"    Window: {window.name}")
            for pane in window.panes:
                try:
                    # Get current command
                    result = pane.cmd("display", "-p", "#{pane_current_command}")
                    command = str(result.stdout[0]) if result and result.stdout else "unknown"
                    
                    # Get pane content snippet
                    content_result = pane.cmd("capture-pane", "-p")
                    content = ""
                    if content_result and content_result.stdout:
                        content_lines = content_result.stdout[:3]  # First 3 lines
                        content = " | ".join(content_lines)
                    
                    print(f"      Pane {pane.id}: command='{command}' content='{content[:100]}...'")
                    
                    # Check if this would be detected as Claude
                    is_claude = "claude" in command.lower()
                    print(f"        → Would detect as Claude: {is_claude}")
                    
                except Exception as e:
                    print(f"      Pane {pane.id}: Error getting info - {e}")
    
    print("\n🔍 Running discover_claude_sessions()...")
    sessions = controller.discover_claude_sessions()
    print(f"Found {len(sessions)} Claude Code sessions:")
    
    for session in sessions:
        print(f"  📍 {session['name']}")
        print(f"     Path: {session['current_path']}")
        print(f"     Tmux: {session['tmux_session_name']}")
        print(f"     Pane: {session['pane_id']}")
    
    if not sessions:
        print("❌ No Claude Code sessions detected!")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure you have a tmux session running")
        print("   2. Start Claude Code with: claude")
        print("   3. Check that the command appears in tmux pane")
        print("   4. Restart codemux-client after starting Claude")


if __name__ == "__main__":
    main()