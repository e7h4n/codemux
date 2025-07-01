#!/usr/bin/env python3
"""Demo script for Codemux Web UI."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codemux.web_server import CodemuxWebServer


async def main():
    """Run a demo of the Codemux Web UI."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)

    print("🚀 Starting Codemux Web UI Demo")
    print("=" * 50)
    print()
    print("📡 WebSocket Server: ws://localhost:8000")
    print("🌐 Web Dashboard: http://localhost:8001")
    print()
    print("💡 To test the Web UI:")
    print("   1. Open http://localhost:8001 in your browser")
    print("   2. Start a Codemux client in another terminal:")
    print("      codemux-client")
    print("   3. Navigate between Dashboard tabs:")
    print("      • Clients: View connected clients")
    print("      • Sessions: Browse Claude Code sessions")
    print("      • Terminal: Execute commands remotely")
    print()
    print("🔄 The dashboard updates in real-time as clients connect")
    print("⌨️  Try executing commands in the Terminal tab")
    print("📊 Monitor client heartbeats and session changes")
    print()
    print("Press Ctrl+C to stop the servers...")
    print("=" * 50)

    # Create server with default ports
    server = CodemuxWebServer(
        host="0.0.0.0",
        port=8000,  # WebSocket server
        web_port=8001,  # Web UI server
    )

    try:
        await server.start_with_web()
    except KeyboardInterrupt:
        logger.info("🛑 Demo stopped by user")
        print("\n✅ Thanks for trying the Codemux Web UI!")


if __name__ == "__main__":
    asyncio.run(main())
