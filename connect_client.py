#!/usr/bin/env python3
"""Simple client connection script that bypasses proxy issues."""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codemux.client import CodemuxClient


async def main():
    """Connect Codemux client to server."""
    # Clear ALL proxy environment variables
    proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']
    for var in proxy_vars:
        if var in os.environ:
            print(f"Clearing proxy variable: {var}")
            del os.environ[var]
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get server URL from command line or use default
    server_url = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8000"
    
    print(f"🔌 Connecting to Codemux server at {server_url}")
    print("Press Ctrl+C to disconnect")
    print("=" * 50)
    
    client = CodemuxClient(server_url)
    
    try:
        await client.connect()
    except KeyboardInterrupt:
        print("\n🔌 Client disconnected")
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())