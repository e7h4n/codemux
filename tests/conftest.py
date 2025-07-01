"""Pytest configuration and fixtures."""

from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_tmux_server():
    """Create a mock tmux server."""
    server = Mock()
    return server


@pytest.fixture
def mock_pane_with_claude():
    """Create a mock pane running Claude Code."""
    pane = Mock()
    pane.current_path = "/home/user/projects/frontend"
    pane.id = "pane1"

    # Mock the cmd result
    cmd_result = Mock()
    cmd_result.stdout = ["claude"]
    pane.cmd.return_value = cmd_result

    # Add window mock
    pane.window = Mock()
    pane.window.name = "window1"

    return pane


@pytest.fixture
def mock_pane_without_claude():
    """Create a mock pane not running Claude Code."""
    pane = Mock()
    pane.current_path = "/home/user/projects/backend"
    pane.id = "pane2"

    # Mock the cmd result
    cmd_result = Mock()
    cmd_result.stdout = ["bash"]
    pane.cmd.return_value = cmd_result

    # Add window mock
    pane.window = Mock()
    pane.window.name = "window2"

    return pane
