#!/usr/bin/env python3
"""Test script for real command execution with Claude Code sessions."""

import asyncio
import sys

from codemux.command_router import CommandRouter
from codemux.output_processor import OutputProcessor
from codemux.tmux_controller import TmuxController


async def test_real_command_execution():
    """Test real command execution with timing."""
    print("🧪 Testing Real Command Execution with Claude Code Sessions...\n")

    # Initialize components
    tmux = TmuxController()
    processor = OutputProcessor(tmux)
    router = CommandRouter(tmux, processor)

    # Discover sessions
    sessions = tmux.discover_claude_sessions()
    router.update_sessions(sessions)

    if not sessions:
        print(
            "❌ No Claude Code sessions found. Please start Claude Code in a tmux session first."
        )
        return False

    print(f"✅ Found {len(sessions)} Claude Code session(s):")
    for session in sessions:
        print(f"   - {session['name']} (tmux: {session['tmux_session_name']})")
    print()

    # Get the first session for testing
    test_session = sessions[0]["name"]
    print(f"🎯 Testing with session: {test_session}")
    print()

    # Test 1: Simple command
    print("Test 1: Simple echo command")
    try:
        result = await router.handle_session_command(
            test_session.split("_")[-1], "echo 'Hello from Codemux!'"
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    print()

    # Test 2: Status query
    print("Test 2: Status query")
    try:
        result = await router.handle_session_command(test_session.split("_")[-1], "pwd")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    print()

    # Test 3: List files
    print("Test 3: List files")
    try:
        result = await router.handle_session_command(
            test_session.split("_")[-1], "ls -la"
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    print()

    print("✅ Real command execution test completed!")
    return True


def main():
    """Main test runner."""
    try:
        success = asyncio.run(test_real_command_execution())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
