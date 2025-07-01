# Voice Control Claude Code System - Final Design Plan

## 🎯 System Overview

A tmux control platform that manages multiple Claude Code tmux sessions through tmuxp, providing a unified voice/text interaction interface. Users interact with multiple Claude Code instances through voice or text, while the system handles command routing and response aggregation.

### Core Value

- **Unified Control**: One interface to manage multiple Claude Code sessions
- **Voice Interaction**: Hands-free, voice programming
- **Smart Routing**: #sessionId to switch sessions, continuous conversation maintains context
- **Response Aggregation**: Unified display of outputs and status from each session
- **Simple and Efficient**: Focus on control and routing, no over-engineering

## 🏗️ System Architecture

```
User Input (Voice/Text)
        ↓ 
   Dispatch Service (FastAPI)
        ↓ Command Routing
   tmuxp Controller
        ↓ send_keys
   Multiple tmux Sessions
        ↓ Running
   Multiple Claude Code Instances
        ↓ Output Capture
   Response Aggregation ← Claude API Summary
        ↓
   Return to User Interface
```

## 📋 Core Feature List

### ✅ P0 - Core Control Features

- **Session Discovery**: Scan tmux on startup, identify sessions running Claude Code
- **Command Routing**:
  - Direct input → Send to current active session
  - #sessionId command → Send to specified session
- **Response Capture**: Detect tmux screen changes, capture Claude Code output
- **Output Processing**: Use Claude API to summarize long outputs, keep conversations concise
- **Session Switching**: Support voice/text methods to switch current active session
- **Status Query**: Status commands show current state of all sessions

### 🔶 P1 - Enhanced Interaction

- **Voice Input**: Whisper recognition, support #sessionId syntax
- **Voice Output**: TTS reads Claude Code replies
- **Selection Support**: Recognize Claude Code option prompts, support voice replies
- **Mode Switching**: Support Claude Code shortcuts like Shift+Tab
- **Error Handling**: Voice recognition error correction, session disconnection recovery

### 🔷 P2 - Monitoring and Display

- **Response Time**: Show time from command sent to output received
- **Token Statistics**: Estimate token usage through Claude API calls
- **Session Info**: Display current directory, git status, and other basic info
- **Usage Statistics**: Simple session activity and interaction count statistics

## 🔧 Technical Architecture Details

### 1. Core Components

#### TmuxController - tmux Control Core

```python
import tmuxp
import asyncio
import time

class TmuxController:
    def __init__(self):
        self.server = tmuxp.Server()
        
    def discover_claude_sessions(self):
        """Discover sessions running Claude Code"""
        claude_sessions = []
        
        for session in self.server.sessions:
            for window in session.windows:
                for pane in window.panes:
                    if self.is_running_claude(pane):
                        claude_sessions.append({
                            'session': session,
                            'pane': pane,
                            'name': session.name,
                            'current_path': pane.current_path
                        })
        return claude_sessions
    
    def is_running_claude(self, pane):
        """Check if running Claude Code"""
        try:
            cmd = pane.cmd('display-message', '-p', '#{pane_current_command}')
            return 'claude' in cmd.stdout[0].lower()
        except:
            return False
    
    def capture_screen(self, session_name):
        """Capture session screen content"""
        session = self.server.find_where({"session_name": session_name})
        if session:
            pane = session.active_window.active_pane
            content = pane.cmd('capture-pane', '-p')
            return '\n'.join(content.stdout)
        return ""
    
    def send_input(self, session_name, text):
        """Send input to specified session"""
        session = self.server.find_where({"session_name": session_name})
        if session:
            pane = session.active_window.active_pane
            pane.send_keys(text)
            return True
        return False
    
    def send_special_key(self, session_name, key_combination):
        """Send special key combinations"""
        session = self.server.find_where({"session_name": session_name})
        if session:
            pane = session.active_window.active_pane
            if key_combination == "shift+tab":
                pane.cmd('send-keys', 'S-Tab')
            return True
        return False
```

#### CommandRouter - Command Router

```python
class CommandRouter:
    def __init__(self, tmux_controller, output_processor):
        self.tmux = tmux_controller
        self.processor = output_processor
        self.current_session = None
        self.sessions = {}
        
    def parse_input(self, user_input):
        """Parse user input"""
        user_input = user_input.strip()
        
        # Status query
        if user_input.lower() in ['status', 'all sessions']:
            return 'status_query', None, user_input
            
        # Specified session: #sessionId command
        if user_input.startswith('#'):
            parts = user_input[1:].split(' ', 1)
            session_id = parts[0]
            command = parts[1] if len(parts) > 1 else ""
            return 'session_command', session_id, command
        else:
            # Send to current active session
            return 'current_session', self.current_session, user_input
            
    async def route_command(self, user_input):
        """Route command to appropriate handler"""
        command_type, session_id, command = self.parse_input(user_input)
        
        if command_type == 'status_query':
            return await self.handle_status_query()
        elif command_type == 'session_command':
            return await self.handle_session_command(session_id, command)
        elif command_type == 'current_session':
            if session_id:
                return await self.handle_session_command(session_id, command)
            else:
                return "Please specify a session first (use #sessionName) or check status"
                
    async def handle_session_command(self, session_id, command):
        """Handle session command"""
        # Fuzzy match session name
        matched_session = self.find_session(session_id)
        if not matched_session:
            available = list(self.sessions.keys())
            return f"Session '{session_id}' not found. Available sessions: {', '.join(available)}"
            
        # Update current active session
        self.current_session = matched_session
        
        if not command:
            # Just switching session
            return f"Switched to session '{matched_session}'"
            
        # Send command and wait for response
        return await self.send_command_with_timing(matched_session, command)
        
    async def send_command_with_timing(self, session_name, command):
        """Send command with timing"""
        start_time = time.time()
        
        # Record screen content before sending
        old_content = self.tmux.capture_screen(session_name)
        
        # Send command
        success = self.tmux.send_input(session_name, command)
        if not success:
            return f"Failed to send command: session {session_name} unavailable"
            
        # Wait for response
        response = await self.wait_for_response(session_name, old_content, start_time)
        
        return response
        
    async def wait_for_response(self, session_name, old_content, start_time):
        """Wait for Claude Code response"""
        timeout = 30  # 30 second timeout
        check_interval = 0.5  # Check every 500ms
        
        while time.time() - start_time < timeout:
            await asyncio.sleep(check_interval)
            
            current_content = self.tmux.capture_screen(session_name)
            if current_content != old_content:
                # Detected output change
                response_time = time.time() - start_time
                
                # Extract new content
                new_output = self.extract_new_content(old_content, current_content)
                
                # Process output
                processed = await self.processor.process_output(new_output)
                
                return f"[{session_name}] {processed} (⏱️ {response_time:.1f}s)"
                
        return f"[{session_name}] Response timeout (>{timeout}s)"
        
    def extract_new_content(self, old_content, new_content):
        """Extract new content"""
        # Simple implementation: compare differences in last few lines
        old_lines = old_content.split('\n')
        new_lines = new_content.split('\n')
        
        if len(new_lines) > len(old_lines):
            # New lines added
            return '\n'.join(new_lines[len(old_lines):])
        else:
            # Content may have changed, return last 10 lines
            return '\n'.join(new_lines[-10:])
```

#### OutputProcessor - Output Processor

```python
class OutputProcessor:
    def __init__(self, claude_client):
        self.claude = claude_client
        
    async def process_output(self, content):
        """Process Claude Code output"""
        if not content.strip():
            return "No output"
            
        # Return short content directly
        if len(content) < 200:
            return content
            
        # Long content needs summarization
        return await self.summarize_output(content)
        
    async def summarize_output(self, content):
        """Summarize long output"""
        prompt = f"""Please concisely summarize this Claude Code output:

{content}

Requirements:
1. 1-2 sentences summarizing main content
2. Highlight key results and operations
3. If code generation, describe main functionality
4. If errors, identify the problem
5. Natural tone, like daily conversation

Summary:"""

        try:
            response = await self.claude.complete(prompt)
            return response.strip()
        except Exception as e:
            return f"Output summary failed: {str(e)}"
            
    async def analyze_claude_status(self, screen_content):
        """Analyze Claude Code current status"""
        prompt = f"""Analyze this Claude Code terminal status:

{screen_content}

Determine Claude Code current status:
- idle: Waiting for user input
- working: Processing task
- choice: Showing selection options waiting for user choice
- editing: In edit mode
- error: Error occurred

Return a brief status description."""

        try:
            response = await self.claude.complete(prompt)
            return response.strip()
        except:
            return "Status unknown"
```

#### SessionManager - Session Manager

```python
class SessionManager:
    def __init__(self, tmux_controller, output_processor):
        self.tmux = tmux_controller
        self.processor = output_processor
        self.sessions = {}
        
    async def update_all_sessions(self):
        """Update all session statuses"""
        discovered = self.tmux.discover_claude_sessions()
        
        # Update existing sessions
        current_names = set()
        for session_info in discovered:
            name = session_info['name']
            current_names.add(name)
            
            if name not in self.sessions:
                # New session
                await self.register_session(session_info)
            else:
                # Update existing session
                await self.update_session(session_info)
                
        # Remove offline sessions
        offline_sessions = set(self.sessions.keys()) - current_names
        for name in offline_sessions:
            self.sessions.pop(name, None)
            
    async def register_session(self, session_info):
        """Register new session"""
        name = session_info['name']
        
        # Get current status
        screen_content = self.tmux.capture_screen(name)
        status = await self.processor.analyze_claude_status(screen_content)
        
        self.sessions[name] = {
            'name': name,
            'current_path': session_info['current_path'],
            'status': status,
            'last_update': time.time(),
            'online': True
        }
        
        print(f"Session registered: {name}")
        
    async def update_session(self, session_info):
        """Update session info"""
        name = session_info['name']
        session_data = self.sessions[name]
        
        session_data['current_path'] = session_info['current_path']
        session_data['last_update'] = time.time()
        session_data['online'] = True
        
        # Periodic status update (not every time to avoid frequent calls)
        if time.time() - session_data.get('last_status_update', 0) > 60:  # Update every minute
            screen_content = self.tmux.capture_screen(name)
            session_data['status'] = await self.processor.analyze_claude_status(screen_content)
            session_data['last_status_update'] = time.time()
            
    async def get_all_sessions_status(self):
        """Get all sessions status overview"""
        if not self.sessions:
            return "No Claude Code sessions discovered"
            
        status_list = []
        for name, data in self.sessions.items():
            status_list.append(f"{name}: {data['status']}")
            
        return f"Active sessions ({len(self.sessions)}):\n" + "\n".join(status_list)
```

### 2. Main Service

#### VoiceClaudeController - Main Controller

```python
from fastapi import FastAPI, WebSocket
import asyncio

class VoiceClaudeController:
    def __init__(self):
        self.app = FastAPI()
        self.tmux = TmuxController()
        self.processor = OutputProcessor(claude_client)
        self.router = CommandRouter(self.tmux, self.processor)
        self.session_manager = SessionManager(self.tmux, self.processor)
        
        # Start periodic session updates
        asyncio.create_task(self.periodic_session_update())
        
    async def periodic_session_update(self):
        """Periodically update session status"""
        while True:
            try:
                await self.session_manager.update_all_sessions()
                self.router.sessions = self.session_manager.sessions
            except Exception as e:
                print(f"Session update error: {e}")
            await asyncio.sleep(30)  # Update every 30 seconds
            
    async def process_user_input(self, user_input):
        """Main entry point for processing user input"""
        try:
            return await self.router.route_command(user_input)
        except Exception as e:
            return f"Error processing command: {str(e)}"
            
    @app.websocket("/ws")
    async def websocket_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                # Receive user input
                data = await websocket.receive_text()
                
                # Process command
                response = await self.process_user_input(data)
                
                # Return result
                await websocket.send_text(response)
        except Exception as e:
            print(f"WebSocket error: {e}")
```

## 🎯 MVP Implementation Roadmap

### Phase 1: Basic Control (1 week)

- ✓ tmuxp session discovery and control
- ✓ Basic command routing (#sessionId)
- ✓ Output capture and simple processing
- ✓ Web interface single dialog

### Phase 2: Smart Processing (1 week)

- ✓ Claude API output summarization
- ✓ Status query and session management
- ✓ Response time display
- ✓ Error handling improvements

### Phase 3: Voice Integration (1 week)

- ✓ Whisper voice recognition
- ✓ TTS voice output
- ✓ Selection support and special keys
- ✓ Voice error correction

## 📝 Core Design Principles

### Focus on Control, Don't Reinvent the Wheel

- **Leverage Claude Code**: Don't replace Claude Code features, only control and aggregate
- **Simple Routing**: Core is command distribution and response collection
- **Minimal Intrusion**: Control through tmux, don't modify Claude Code itself
- **User Friendly**: Natural voice interaction, concise status display

### Technology Selection Principles

- **tmuxp**: Elegant Python tmux control
- **Claude API**: For output summarization and status analysis
- **FastAPI**: Lightweight web service
- **WebSocket**: Real-time bidirectional communication
- **Whisper + TTS**: Optional voice features

This solution returns to the original core: a unified platform controlling multiple Claude Code instances through tmux, focusing on control, routing, and aggregation, rather than duplicating Claude Code's functionality.