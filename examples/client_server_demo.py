#!/usr/bin/env python
"""Demo script showing client-server architecture."""

import asyncio
import subprocess
import sys


async def demo():
    """Run a demo of the client-server architecture."""
    print("Codemux Client-Server Demo")
    print("=" * 50)

    # Start server
    print("\n1. Starting Codemux server...")
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "codemux.server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    await asyncio.sleep(2)

    print("   Server started on ws://localhost:8000/ws")

    # Start client
    print("\n2. Starting Codemux client...")
    client_proc = subprocess.Popen(
        [sys.executable, "-m", "codemux.client"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for client to connect
    await asyncio.sleep(2)

    print("   Client connected to server")

    # Demo info
    print("\n3. Architecture Overview:")
    print("   - Server listens on WebSocket port 8000")
    print("   - Clients discover local Claude Code sessions")
    print("   - Clients report sessions to server")
    print("   - Server provides unified control interface")
    print("   - Commands are routed through server to appropriate client")

    print("\n4. WebSocket Protocol:")
    print("   Client -> Server:")
    print("     - REGISTER: Register client and sessions")
    print("     - HEARTBEAT: Keep connection alive")
    print("     - SESSION_UPDATE: Notify session changes")
    print("     - COMMAND_RESPONSE: Return command results")
    print("   Server -> Client:")
    print("     - EXECUTE_COMMAND: Execute command on session")
    print("     - QUERY_STATUS: Request session status")
    print("     - CONTROL: Server control commands")

    print("\nPress Ctrl+C to stop the demo...")

    try:
        # Keep running
        await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        # Cleanup
        server_proc.terminate()
        client_proc.terminate()
        await asyncio.sleep(1)
        server_proc.kill()
        client_proc.kill()


if __name__ == "__main__":
    try:
        asyncio.run(demo())
    except KeyboardInterrupt:
        print("\nDemo stopped")
