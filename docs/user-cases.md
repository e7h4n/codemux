# Codemux User Cases

## Primary User Profile

A developer who:
- Works on 4-5 projects simultaneously across different repositories
- Uses Claude Code for development but faces slow response times
- Opens multiple sessions to improve efficiency through parallel processing
- Needs to monitor progress across sessions while working on other tasks

## Core Use Cases

### UC1: Session Discovery and Management
**Scenario**: Developer has manually opened 4-5 Claude Code sessions in tmux
**Flow**:
1. User starts tmux sessions with Claude Code in different project directories
2. User starts Codemux server
3. Codemux automatically discovers all tmux sessions running Claude Code
4. Sessions are named as `{hostname}_{dirname}` (e.g., `macbook_frontend`)
5. User can query all sessions status via web/voice interface

**Key Requirements**:
- No batch startup needed - user manually controls session creation
- Automatic discovery of Claude Code sessions
- Clear naming convention based on directory

### UC2: Status Monitoring
**Scenario**: User wants to check progress across all sessions
**Voice Command**: "status" or "状态"
**Expected Output**:
```
Active sessions (4):
- macbook_frontend: idle, main branch, no pending MR
- macbook_backend: working on API endpoint, feature/auth branch, MR #123 open
- macbook_docs: last output: "Generated 3 documentation files"
- server_ml-model: processing data analysis, 2 min elapsed
```

**Information Needed**:
- Idle/working status
- Git repository status (branch, uncommitted changes)
- MR/PR status if applicable
- Summary of last interaction
- Elapsed time for current operation

### UC3: Session Switching
**Scenario**: User wants to switch between sessions
**Interaction Patterns**:
- Voice: "切换到 frontend 目录" (Switch to frontend directory)
- Text: "switch to frontend"
- Fuzzy matching: "frontend" matches "macbook_frontend"

**Behavior**:
- Updates current active session
- Future commands without session specifier go to this session
- Returns confirmation: "Switched to session 'macbook_frontend'"

### UC4: Command Routing
**Scenario**: User sends commands to specific or current session

**Patterns**:
1. **Current session**: "run npm test"
   - Sends to currently active session
   
2. **Specific session**: "#backend npm build"
   - Routes to backend session regardless of current active session
   
3. **Voice with numbers**: When Claude Code shows options (1/2/3)
   - User says "1" or "one"
   - Codemux sends "1" to the session

### UC5: Output Handling
**Scenario**: Claude Code generates output that needs to be displayed

**Two Modes**:
1. **At Computer (Web Interface)**:
   - Show full output in chat interface
   - Display response time
   - Keep latest output visible
   
2. **Away from Computer (Voice)**:
   - Summarize long outputs using Claude API
   - Focus on key results and actions taken
   - Example: "Claude Code generated a React component with user authentication. No errors found."

### UC6: Multi-Session Output
**Scenario**: Multiple sessions produce output simultaneously
**Behavior**:
- Merge outputs in chronological order
- Prefix each output with session name
- Example:
  ```
  [frontend] Compiled successfully (⏱️ 2.3s)
  [backend] Running tests... 15 passed (⏱️ 5.1s)
  [docs] Generated API documentation (⏱️ 1.2s)
  ```

### UC7: Voice Interaction Flow
**Scenario**: User interacts via voice while away from computer
**Typical Flow**:
1. User: "状态" (Status)
2. Codemux: Lists all sessions with current state
3. User: "切换到 backend"
4. Codemux: "Switched to session 'macbook_backend'"
5. User: "run all tests"
6. Codemux: Sends command, waits for output
7. Codemux: "All 45 tests passed successfully in backend project"

## Non-Functional Requirements

### Simplicity
- Single chat interface for web
- No conversation history needed
- Minimal UI - just input box and output display

### Performance
- Session discovery within 2 seconds
- Command routing immediate
- Output capture with 500ms polling

### Language Support
- Multilingual voice support via Whisper
- Commands can be in English or Chinese
- Natural language processing for session names

## Future Considerations (Not in MVP)

- Automatic approval of safe Claude Code operations
- Batch session startup with configuration
- Session templates for common project types
- Integration with CI/CD status
- Proactive notifications for long-running operations