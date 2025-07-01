# Codemux Web UI

A modern web-based dashboard for monitoring and managing Codemux clients and Claude Code sessions.

## Features

### 📊 Dashboard Overview
- **Real-time Statistics**: Connected clients, active sessions, and server metrics
- **Server Status**: Live connection status with automatic reconnection
- **Modern Design**: Glassmorphism UI with responsive layout

### 👥 Client Management
- **Connected Clients**: View all connected Codemux clients
- **Client Details**: Hostname, platform, session count, and last heartbeat
- **Status Monitoring**: Online/offline status with visual indicators

### 💻 Session Management
- **Active Sessions**: List all Claude Code sessions across clients
- **Session Details**: Session name, client hostname, current path, tmux session
- **Quick Actions**: Direct access to terminal for each session

### 🖥️ Interactive Terminal
- **Remote Execution**: Execute commands on any active session
- **Command History**: Navigate previous commands with up/down arrows
- **Real-time Output**: View command results and errors immediately
- **Session Selection**: Easy dropdown to switch between sessions

## Getting Started

### Installation

1. Install the required dependencies:
```bash
pip install fastapi uvicorn jinja2
```

2. Install Codemux in development mode:
```bash
pip install -e .
```

### Running the Web UI

Start the Codemux server with Web UI:

```bash
# Start both WebSocket server (port 8000) and Web UI (port 8001)
python -m codemux.web_server

# Or specify custom ports
python -m codemux.web_server 0.0.0.0 8000 8001
```

### Accessing the Dashboard

Open your browser and navigate to:
- **Web UI**: http://localhost:8001
- **WebSocket Server**: ws://localhost:8000

## Architecture

### Components

1. **FastAPI Web Server**: Serves the dashboard and REST API endpoints
2. **WebSocket Integration**: Real-time updates and command execution
3. **Vue.js Frontend**: Reactive dashboard with modern UI components
4. **Static Assets**: CSS and JavaScript files for styling and functionality

### API Endpoints

- `GET /` - Dashboard HTML page
- `GET /api/status` - Server status and statistics
- `GET /api/clients` - List of connected clients
- `GET /api/sessions` - List of active sessions
- `POST /api/execute` - Execute command on a session
- `WebSocket /ws` - Real-time updates and communication

### Real-time Updates

The Web UI uses WebSocket connections to provide:
- Live client connection/disconnection notifications
- Session updates when new sessions are created or removed
- Command execution results broadcast to all connected browsers
- Automatic reconnection with exponential backoff

## Usage

### Monitoring Clients

1. **Clients Tab**: View all connected Codemux clients
   - Client ID and hostname
   - Platform information (macOS, Linux, etc.)
   - Number of active sessions
   - Last heartbeat timestamp
   - Online/offline status

### Managing Sessions

1. **Sessions Tab**: Browse all Claude Code sessions
   - Session name and client hostname
   - Current working directory
   - Associated tmux session name
   - Quick "Execute" button to open terminal

### Using the Terminal

1. **Terminal Tab**: Interactive command execution
   - Select target session from dropdown
   - Type commands and press Enter to execute
   - View output and error messages in real-time
   - Use arrow keys to navigate command history
   - Auto-scroll to latest output

### Keyboard Shortcuts

- **Enter**: Execute current command
- **↑**: Previous command in history
- **↓**: Next command in history
- **Tab Switch**: Click on tab headers to switch views

## Advanced Features

### Real-time Notifications

The dashboard shows toast notifications for:
- Data refresh confirmations
- Connection status changes
- Command execution results
- Error messages

### Responsive Design

The Web UI adapts to different screen sizes:
- **Desktop**: Full grid layout with all features
- **Tablet**: Stacked layout with preserved functionality
- **Mobile**: Single-column layout optimized for touch

### Browser Compatibility

Tested and supported browsers:
- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Troubleshooting

### Common Issues

1. **Cannot connect to WebSocket server**
   - Ensure the Codemux server is running on port 8000
   - Check firewall settings
   - Verify no other services are using the ports

2. **Web UI shows "No clients connected"**
   - Start a Codemux client: `codemux-client`
   - Check client authentication
   - Verify network connectivity

3. **Commands not executing**
   - Ensure session is selected in terminal
   - Check that the target session still exists
   - Verify client is still connected

### Debug Mode

Enable debug logging:
```bash
PYTHONPATH=src python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from codemux.web_server import main
import asyncio
asyncio.run(main())
"
```

## Development

### File Structure

```
src/codemux/web/
├── templates/
│   └── dashboard.html     # Main dashboard template
├── static/
│   ├── css/
│   │   └── dashboard.css  # Styling and animations
│   └── js/
│       └── dashboard.js   # Vue.js application logic
└── web_server.py          # FastAPI server and WebUI class
```

### Customization

1. **Styling**: Modify `dashboard.css` for custom themes
2. **Functionality**: Extend `dashboard.js` for new features
3. **Layout**: Update `dashboard.html` template structure
4. **API**: Add new endpoints in `web_server.py`

### Contributing

When adding new features:
1. Follow the existing Vue.js component structure
2. Maintain responsive design principles
3. Add proper error handling
4. Update this documentation

## Security Considerations

- Web UI runs on localhost by default
- No authentication implemented (suitable for local development)
- WebSocket connections are not encrypted (use behind reverse proxy for production)
- Command execution is limited to authenticated Codemux clients

For production deployments, consider:
- Adding HTTPS/WSS support
- Implementing user authentication
- Setting up proper access controls
- Using a reverse proxy (nginx, traefik)
