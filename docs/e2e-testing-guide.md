# Codemux End-to-End Testing Guide

## Objectives

Verify that Codemux can:
1. Correctly discover and identify Claude Code sessions
2. Route commands intelligently to specified sessions
3. Support multilingual commands and fuzzy matching
4. Provide a friendly interactive experience

## Testing Steps

### Phase 1: Environment Setup (5 minutes)

#### 1.1 Create test project directories
```bash
# Create mock project directories
mkdir -p ~/tmp/codemux-test/{frontend,backend,docs}
cd ~/tmp/codemux-test/frontend && echo "# Frontend Project" > README.md
cd ~/tmp/codemux-test/backend && echo "# Backend Project" > README.md
cd ~/tmp/codemux-test/docs && echo "# Documentation" > README.md
```

#### 1.2 Create batch startup script
```bash
# Create ~/tmp/start-test-sessions.sh
cat > ~/tmp/start-test-sessions.sh << 'EOF'
#!/bin/bash
echo "Starting Claude Code test sessions..."

# Kill existing test sessions if they exist
tmux kill-session -t test-frontend 2>/dev/null || true
tmux kill-session -t test-backend 2>/dev/null || true
tmux kill-session -t test-docs 2>/dev/null || true

# Create test sessions
tmux new-session -d -s test-frontend -c ~/tmp/codemux-test/frontend
tmux new-session -d -s test-backend -c ~/tmp/codemux-test/backend
tmux new-session -d -s test-docs -c ~/tmp/codemux-test/docs

# Start mock Claude Code processes in each session
# Note: we create scripts named 'claude' to simulate Claude Code
tmux send-keys -t test-frontend 'exec -a claude bash -c "while true; do echo [claude-frontend]; sleep 30; done"' Enter
tmux send-keys -t test-backend 'exec -a claude bash -c "while true; do echo [claude-backend]; sleep 30; done"' Enter
tmux send-keys -t test-docs 'exec -a claude bash -c "while true; do echo [claude-docs]; sleep 30; done"' Enter

echo "Created 3 test sessions:"
tmux list-sessions | grep test-
echo ""
echo "Sessions should be named like: hostname_frontend, hostname_backend, hostname_docs"
EOF

chmod +x ~/tmp/start-test-sessions.sh
```

### Phase 2: Basic Functionality Verification (10 minutes)

#### 2.1 Start test sessions
```bash
# Start test sessions
~/tmp/start-test-sessions.sh

# Verify sessions are created
tmux list-sessions
```

**Expected Result:** See 3 test-* sessions running

#### 2.2 Test session discovery functionality
```bash
cd ~/workspace/codemux

# Test basic session discovery
uv run python scripts/test_discovery.py
```

**Expected Result:**
- Discover 3 sessions
- Session names formatted as `hostname_frontend`, `hostname_backend`, `hostname_docs`
- Display correct directory paths

#### 2.3 Test basic CLI functionality
```bash
# Test CLI components
uv run python scripts/test_cli.py
```

**Expected Result:**
- Discover 3 Claude Code sessions
- Command routing tests pass
- No error messages

### Phase 3: Interactive CLI Verification (15 minutes)

#### 3.1 Start interactive CLI
```bash
uv run codemux
```

#### 3.2 Verify core commands

Test each command in the following order:

```bash
# 1. View help
help

# 2. View session status
status

# 3. Test Chinese status query
状态

# 4. Test session switching (English)
switch to frontend

# 5. Verify current session indicator
status

# 6. Test Chinese session switching
切换到 backend

# 7. Test fuzzy matching
switch to docs

# 8. Test # syntax switching
#frontend

# 9. Test # syntax with command
#backend echo "test command"

# 10. Test current session command
echo "current session command"

# 11. Test non-existent session
switch to nonexistent

# 12. Refresh session list
refresh

# 13. Exit
quit
```

#### 3.3 Verification Checklist

Expected results for each command:

- [ ] `help` - Display complete help information
- [ ] `status` - Show 3 sessions with correct format
- [ ] `状态` - Same as status, supports Chinese
- [ ] `switch to frontend` - Successfully switch, return confirmation
- [ ] `status` - frontend session has `*` marker
- [ ] `切换到 backend` - Chinese switching successful
- [ ] `switch to docs` - Fuzzy matching works (docs matches hostname_docs)
- [ ] `#frontend` - Direct switching successful
- [ ] `#backend echo "test"` - Show "Would execute: echo test"
- [ ] `echo "current"` - Send to current session
- [ ] `switch to nonexistent` - Show error message and available session list
- [ ] `refresh` - Rediscover sessions
- [ ] `quit` - Exit normally

### Phase 4: Edge Case Verification (10 minutes)

#### 4.1 Test empty session scenario
```bash
# Stop all test sessions
tmux kill-session -t test-frontend
tmux kill-session -t test-backend
tmux kill-session -t test-docs

# Run discovery again
uv run python scripts/test_discovery.py
```

**Expected Result:** Display "No Claude Code sessions found"

#### 4.2 Test partial session scenario
```bash
# Start only one session
tmux new-session -d -s test-single -c ~/tmp/codemux-test/frontend
tmux send-keys -t test-single 'exec -a claude bash -c "while true; do echo [claude-single]; sleep 30; done"' Enter

# Test CLI
uv run codemux
# Input: status
# Input: switch to single
# Input: quit
```

#### 4.3 Test session name edge cases
```bash
# Create specially named session
tmux new-session -d -s test-special-name -c ~/tmp/codemux-test/backend
tmux send-keys -t test-special-name 'exec -a claude bash -c "while true; do echo [claude-special]; sleep 30; done"' Enter

uv run codemux
# Test various matching methods
# Input: status
# Input: switch to special
# Input: switch to backend
# Input: #special-name
```

### Phase 5: Performance and Stability Verification (5 minutes)

#### 5.1 Concurrent session test
```bash
# Create more sessions to test performance
for i in {1..5}; do
    tmux new-session -d -s "test-perf-$i" -c ~/tmp/codemux-test/frontend
    tmux send-keys -t "test-perf-$i" 'exec -a claude bash -c "while true; do echo [claude-perf-'$i']; sleep 30; done"' Enter
done

# Test discovery performance
time uv run python scripts/test_discovery.py
```

**Expected Result:**
- Discovery time < 2 seconds
- Correctly identify all sessions
- No errors or crashes

#### 5.2 Command response test
```bash
uv run codemux
# Quickly input multiple commands to test responsiveness
# status -> switch to perf-1 -> status -> #perf-2 -> status -> quit
```

### Phase 6: Cleanup and Summary (2 minutes)

#### 6.1 Clean up test environment
```bash
# Kill all test sessions
tmux list-sessions | grep test- | cut -d: -f1 | xargs -I {} tmux kill-session -t {}

# Delete test directory
rm -rf ~/tmp/codemux-test
rm ~/tmp/start-test-sessions.sh

# Verify cleanup is complete
tmux list-sessions 2>/dev/null | grep test- || echo "All test sessions cleaned up"
```

#### 6.2 Verification summary

If all steps pass, Codemux core functionality is working properly:

✅ **Session Discovery** - Correctly identifies mock Claude Code processes
✅ **Command Routing** - Supports multiple syntax and matching methods
✅ **Multilingual** - Both English and Chinese commands work
✅ **Interactive Experience** - CLI interface is friendly and responsive
✅ **Error Handling** - Correctly handles edge cases and invalid input
✅ **Performance** - Good performance in multi-session environments

## Troubleshooting

### Issue 1: Sessions not discovered
**Symptom:** `test_discovery.py` shows "No Claude Code sessions found"
**Diagnosis:**
```bash
# Check if tmux sessions exist
tmux list-sessions

# Check if processes contain "claude"
tmux list-sessions -F "#{session_name}" | xargs -I {} tmux display-message -t {} -p "#{pane_current_command}"
```

### Issue 2: CLI unresponsive
**Symptom:** No output after entering commands
**Diagnosis:**
```bash
# Check for Python errors
uv run python -c "from codemux.cli import main; main()" 2>&1
```

### Issue 3: Incorrect session names
**Symptom:** Session name format doesn't match expectations
**Diagnosis:**
```bash
# Check hostname and directory retrieval
python3 -c "import socket, os; print(f'{socket.gethostname()}_{os.path.basename(os.getcwd())}')"
```

## Performance Benchmarks

Normal performance indicators:

- **Session discovery time:** < 2 seconds (5 sessions)
- **Command response time:** < 500ms
- **Memory usage:** < 50MB
- **Startup time:** < 3 seconds

If performance is significantly below these indicators, code optimization may be needed.
