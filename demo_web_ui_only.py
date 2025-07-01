#!/usr/bin/env python3
"""Demo script that shows the Web UI without client connection issues."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codemux.web_server import CodemuxWebServer


async def main():
    """Start Codemux Web UI server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🎉 Codemux Web UI Demo")
    print("=" * 40)
    print()
    print("🌐 Web Dashboard: http://localhost:8001")
    print("📡 WebSocket Server: ws://localhost:8000")
    print()
    print("✨ Features you can see in the Web UI:")
    print("   • Modern glassmorphism design")
    print("   • Real-time dashboard with stats")
    print("   • Three interactive tabs:")
    print("     - Clients: Connected client monitoring")  
    print("     - Sessions: Claude Code session management")
    print("     - Terminal: Remote command execution")
    print("   • Responsive Vue.js interface")
    print("   • Live WebSocket updates")
    print()
    print("💡 What to try:")
    print("   1. Open http://localhost:8001 in your browser")
    print("   2. Explore the three tabs (Clients, Sessions, Terminal)")
    print("   3. Check the API endpoints:")
    print("      - http://localhost:8001/api/status")
    print("      - http://localhost:8001/api/clients") 
    print("      - http://localhost:8001/api/sessions")
    print()
    print("ℹ️  Note: Client connections may have proxy issues on this system.")
    print("   The Web UI demonstrates the complete interface design.")
    print()
    print("Press Ctrl+C to stop the demo")
    print("=" * 40)
    
    # Start server with web UI
    server = CodemuxWebServer(host="localhost", port=8000, web_port=8001)
    
    try:
        await server.start_with_web()
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped. Thanks for checking out Codemux!")


if __name__ == "__main__":
    asyncio.run(main())