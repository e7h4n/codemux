#!/usr/bin/env python3
"""Simple startup script for Codemux that bypasses WebSocket proxy issues."""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codemux.web_server import CodemuxWebServer


async def main():
    """Start Codemux server with web UI."""
    # Clear proxy environment variables to avoid WebSocket issues
    proxy_vars = [
        "http_proxy",
        "https_proxy",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "all_proxy",
        "ALL_PROXY",
    ]
    for var in proxy_vars:
        if var in os.environ:
            del os.environ[var]

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("🚀 Starting Codemux with Web UI...")
    print("📡 WebSocket Server: ws://localhost:8000")
    print("🌐 Web Dashboard: http://localhost:8001")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    # Start server with web UI
    server = CodemuxWebServer(host="localhost", port=8000, web_port=8001)

    try:
        await server.start_with_web()
    except KeyboardInterrupt:
        print("\n🛑 Codemux stopped")


if __name__ == "__main__":
    asyncio.run(main())
