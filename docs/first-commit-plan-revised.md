# First Commit Plan (Revised): Project Infrastructure

## 🎯 Goal
Establish robust engineering foundation with modern Python tooling, CI/CD, and basic session discovery functionality.

## 📦 Components

### 1. Project Setup with uv
- Modern Python packaging with `pyproject.toml`
- Dependency management
- Python 3.11+ requirement

### 2. Code Quality Tools
- **ruff**: Fast Python linter and formatter
  - Replace black, isort, flake8
  - Configure in `pyproject.toml`
- **basedpyright**: Fast static type checking (Pyright fork)
- **pytest**: Testing framework
- **coverage**: Code coverage reporting

### 3. Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/DetachHead/basedpyright
    rev: v1.10.0
    hooks:
      - id: basedpyright

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

### 4. GitHub Actions CI/CD
```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4

    - name: Install uv
      uses: astral-sh/setup-uv@v2

    - name: Set up Python ${{ matrix.python-version }}
      run: uv python pin ${{ matrix.python-version }}

    - name: Install dependencies
      run: uv sync --dev

    - name: Run pre-commit
      run: uv run pre-commit run --all-files

    - name: Run tests
      run: uv run pytest -v --cov=codemux --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### 5. Basic TmuxController Implementation
```python
# src/codemux/tmux_controller.py
"""Tmux session discovery and control."""
import socket
from typing import List, Dict, Any

import libtmux
from libtmux.server import Server
from libtmux.session import Session
from libtmux.pane import Pane


class TmuxController:
    """Controller for discovering and managing tmux sessions."""

    def __init__(self) -> None:
        """Initialize tmux controller."""
        self.server: Server = libtmux.Server()
        self.hostname: str = socket.gethostname()

    def discover_claude_sessions(self) -> List[Dict[str, Any]]:
        """Discover all tmux sessions running Claude Code.

        Returns:
            List of session information dictionaries.
        """
        sessions = []

        for session in self.server.sessions:
            for window in session.windows:
                for pane in window.panes:
                    if self._is_running_claude(pane):
                        session_info = self._create_session_info(session, pane)
                        sessions.append(session_info)

        return sessions

    def _is_running_claude(self, pane: Pane) -> bool:
        """Check if pane is running Claude Code."""
        try:
            # Get current command
            cmd = pane.cmd('display', '-p', '#{pane_current_command}').stdout
            return 'claude' in str(cmd).lower()
        except Exception:
            return False

    def _create_session_info(self, session: Session, pane: Pane) -> Dict[str, Any]:
        """Create session information dictionary."""
        current_path = pane.current_path
        dirname = current_path.split('/')[-1] if current_path else 'unknown'

        return {
            'name': f"{self.hostname}_{dirname}",
            'tmux_session_name': session.name,
            'current_path': current_path,
            'dirname': dirname,
        }
```

## 📁 Complete Project Structure

```
codemux/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI/CD
├── .pre-commit-config.yaml     # Pre-commit hooks
├── .gitignore                  # Python gitignore
├── pyproject.toml              # Project config & dependencies
├── README.md                   # Project README
├── LICENSE                     # MIT License
├── src/
│   └── codemux/
│       ├── __init__.py
│       ├── __version__.py      # Version info
│       └── tmux_controller.py  # Core functionality
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # pytest fixtures
│   └── test_tmux_controller.py
├── scripts/
│   └── test_discovery.py      # Manual testing script
└── docs/
    ├── plan.md
    ├── user-cases.md
    ├── first-commit-plan.md
    └── first-commit-plan-revised.md
```

## 🛠️ pyproject.toml Configuration

```toml
[project]
name = "codemux"
version = "0.1.0"
description = "Voice-controlled tmux management for Claude Code sessions"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [{name = "Your Name", email = "your.email@example.com"}]

dependencies = [
    "libtmux>=0.33.0",
    "rich>=13.7.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "basedpyright>=1.10.0",
    "ruff>=0.1.9",
    "pre-commit>=3.6.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "ARG", # flake8-unused-arguments
    "SIM", # flake8-simplify
]
ignore = [
    "E501",  # line too long (handled by formatter)
]

[tool.basedpyright]
typeCheckingMode = "strict"
pythonVersion = "3.11"
include = ["src", "tests"]
exclude = ["**/node_modules", "**/__pycache__", ".venv"]
reportMissingImports = true
reportMissingTypeStubs = false

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --strict-markers --cov=codemux"

[tool.coverage.run]
source = ["src/codemux"]
omit = ["*/tests/*", "*/__init__.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

## ✅ First Commit Checklist

1. **Project Structure**
   - [ ] Initialize with `uv init`
   - [ ] Create directory structure
   - [ ] Add LICENSE file

2. **Dependencies**
   - [ ] Configure pyproject.toml
   - [ ] Install with `uv sync --dev`

3. **Code Quality**
   - [ ] Configure ruff
   - [ ] Configure basedpyright
   - [ ] Set up pre-commit hooks
   - [ ] Run initial formatting

4. **CI/CD**
   - [ ] Create GitHub Actions workflow
   - [ ] Test on multiple Python versions
   - [ ] Set up coverage reporting

5. **Basic Implementation**
   - [ ] TmuxController with discovery
   - [ ] Basic tests
   - [ ] Manual test script

6. **Documentation**
   - [ ] README with badges
   - [ ] Development setup instructions
   - [ ] Contributing guidelines

## 🚀 Development Commands

```bash
# Initial setup
uv sync --dev
uv run pre-commit install

# Development workflow
uv run pytest                    # Run tests
uv run pytest --cov             # Run tests with coverage
uv run basedpyright             # Type checking
uv run ruff check src tests     # Lint code
uv run ruff format src tests    # Format code
uv run pre-commit run --all-files  # Run all checks

# Manual testing
uv run python scripts/test_discovery.py
```

## 📝 Commit Message

```
feat: Initialize project with modern Python infrastructure

- Set up project structure with uv package manager
- Configure ruff for linting and formatting
- Add pre-commit hooks for code quality
- Set up GitHub Actions CI/CD pipeline
- Implement basic TmuxController for session discovery
- Add comprehensive test setup with pytest
- Configure basedpyright for fast static type checking
- Add documentation structure

This establishes a solid foundation for the codemux project with
modern Python tooling and automated quality checks.
```
