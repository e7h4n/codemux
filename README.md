# Codemux

Voice-controlled tmux management for Claude Code sessions.

## Overview

Codemux is a unified control platform that manages multiple Claude Code tmux sessions, providing voice and text interaction capabilities. It uses a client-server architecture where clients discover local Claude Code sessions and connect to a central server for unified control.

## Features

- 🔍 **Session Discovery**: Automatically finds tmux sessions running Claude Code
- 🎯 **Smart Routing**: Route commands to specific sessions using `#sessionId` syntax
- 🌏 **Multi-language**: Support for English and Chinese commands
- 🔄 **Session Switching**: Easy switching between sessions with fuzzy matching
- 📊 **Status Monitoring**: View all active sessions and current status
- 🌐 **Client-Server Architecture**: WebSocket-based communication for distributed control
- 💓 **Heartbeat Monitoring**: Automatic detection of disconnected clients
- 🔐 **Optional Authentication**: Token-based authentication support

## Installation

Requires Python 3.11+ and tmux.

```bash
# Install with uv
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install
```

## Usage

### Server Mode

```bash
# Start the server
uv run codemux-server

# Or specify host and port
uv run codemux-server 0.0.0.0 8000
```

### Client Mode

```bash
# Start a client (connects to local server by default)
uv run codemux-client

# Or connect to remote server
uv run codemux-client ws://server-host:8000/ws
```

### Standalone Mode (Legacy)

```bash
# Start the interactive CLI (local mode)
uv run codemux

# Or run directly
uv run python -m codemux.cli
```

### Commands

```bash
# Session management
status                  # Show all sessions
refresh                 # Refresh session list
switch to frontend      # Switch to frontend session
切换到 backend          # Switch to backend (Chinese)

# Command routing
#frontend npm test      # Run command in specific session
#backend git status     # Check git status in backend

# Direct commands (sent to current session)
npm start              # Run in current session
git pull               # Run in current session
```

### Example Session

```
codemux> status
Active sessions (2):
  macbook_frontend: active
  macbook_backend: active

codemux> switch to frontend
Switched to session 'macbook_frontend'

codemux(macbook_frontend)> #backend npm test
[macbook_backend] Would execute: npm test

codemux(macbook_frontend)> git status
[macbook_frontend] Would execute: git status
```

## Development

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Run linting
uv run ruff check src tests

# Manual testing
uv run python scripts/test_discovery.py
uv run python scripts/test_cli.py
```

## License

MIT
