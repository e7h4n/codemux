# First Commit Plan: Session Discovery

## 🎯 Goal
Implement the minimal viable functionality: discover tmux sessions running Claude Code and display their information.

## 📦 Features to Implement

### 1. TmuxController Core
- Connect to tmux server
- List all sessions
- Identify Claude Code sessions
- Generate session names (hostname_dirname format)
- Get basic session info (path, status)

### 2. CLI Tool for Testing
- Simple script to test discovery
- Display found sessions in readable format
- Verify core functionality works

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/test_tmux_controller.py
- test_connect_to_server
- test_discover_sessions
- test_identify_claude_sessions
- test_generate_session_names
- test_session_not_found
```

### Integration Tests
```python
# tests/test_integration.py
- test_with_real_tmux_server
- test_multiple_sessions
- test_no_claude_sessions
```

### Manual Testing
1. Start tmux with several Claude Code sessions
2. Run discovery script
3. Verify correct session identification and naming

## 🛠️ Technical Stack

### Dependencies
- `libtmux` - Python tmux library (successor to tmuxp)
- `pytest` - Testing framework
- `pytest-mock` - Mocking for unit tests
- `rich` - Pretty terminal output for CLI

### Project Structure
```
codemux/
├── pyproject.toml          # uv project config
├── src/
│   └── codemux/
│       ├── __init__.py
│       ├── tmux_controller.py
│       └── cli.py          # Simple CLI for testing
├── tests/
│   ├── __init__.py
│   ├── test_tmux_controller.py
│   └── test_integration.py
└── scripts/
    └── test_discovery.py   # Quick manual test script
```

## 📝 Implementation Details

### Session Identification Logic
```python
def is_running_claude(self, pane):
    """Check if pane is running Claude Code"""
    # Check current command
    cmd = pane.cmd('display', '-p', '#{pane_current_command}').stdout
    if 'claude' in cmd.lower():
        return True

    # Check process tree for more accuracy
    # This handles cases where claude is run through shell
    return False
```

### Session Naming
```python
def generate_session_name(self, pane):
    """Generate unique session name"""
    hostname = socket.gethostname()
    current_path = pane.current_path
    dirname = os.path.basename(current_path)

    # Handle edge cases
    if not dirname or dirname == '/':
        dirname = 'root'

    return f"{hostname}_{dirname}"
```

## ✅ Success Criteria

1. **Functionality**
   - Can discover all tmux sessions
   - Correctly identifies Claude Code sessions
   - Generates proper session names
   - Handles edge cases (no sessions, invalid paths)

2. **Code Quality**
   - All tests pass
   - Type hints throughout
   - Clear documentation
   - Error handling for tmux connection issues

3. **Developer Experience**
   - Easy to run: `uv run scripts/test_discovery.py`
   - Clear output showing discovered sessions
   - Helpful error messages

## 🚀 Development Steps

1. **Setup Project**
   ```bash
   uv init
   uv add libtmux pytest pytest-mock rich
   ```

2. **Implement Core**
   - TmuxController class with discovery method
   - Basic error handling
   - Logging for debugging

3. **Write Tests**
   - Unit tests with mocked tmux
   - Integration test if tmux available

4. **Create CLI Tool**
   - Simple script to visualize results
   - Help validate implementation

5. **Documentation**
   - Inline code documentation
   - README with quick start

## 📊 Example Output

```
$ uv run scripts/test_discovery.py

🔍 Discovering Claude Code Sessions...

Found 3 sessions:
┌─────────────────────────┬────────────────────┬─────────┐
│ Session Name            │ Directory          │ Status  │
├─────────────────────────┼────────────────────┼─────────┤
│ macbook_frontend        │ ~/projects/frontend│ Active  │
│ macbook_backend         │ ~/projects/backend │ Active  │
│ macbook_codemux         │ ~/workspace/codemux│ Active  │
└─────────────────────────┴────────────────────┴─────────┘
```
