# Codemux

Voice-controlled tmux management for Claude Code sessions.

## Overview

Codemux is a unified control platform that manages multiple Claude Code tmux sessions, providing voice and text interaction capabilities.

## Installation

Requires Python 3.11+ and tmux.

```bash
# Install with uv
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install
```

## Development

```bash
# Run tests
uv run pytest

# Run linting
uv run ruff check src tests

# Manual testing
uv run python scripts/test_discovery.py
```

## License

MIT
