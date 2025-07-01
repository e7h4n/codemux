// Dashboard Vue.js application
const { createApp } = Vue;

createApp({
    data() {
        return {
            // UI state
            activeTab: 'clients',
            serverStatus: 'connected',

            // Data
            stats: {
                clients: 0,
                sessions: 0
            },
            serverInfo: {
                host: '',
                port: 0,
                heartbeat_interval: 0,
                heartbeat_timeout: 0
            },
            clients: [],
            sessions: [],

            // Terminal
            selectedSession: '',
            currentCommand: '',
            terminalHistory: [],
            commandHistory: [],
            historyIndex: -1,

            // WebSocket
            ws: null,
            reconnectAttempts: 0,
            maxReconnectAttempts: 5
        };
    },

    computed: {
        serverStatusText() {
            return this.serverStatus === 'connected' ? 'Connected' : 'Disconnected';
        }
    },

    mounted() {
        this.initializeWebSocket();
        this.loadInitialData();

        // Focus command input when terminal tab is active
        this.$watch('activeTab', (newTab) => {
            if (newTab === 'terminal') {
                this.$nextTick(() => {
                    if (this.$refs.commandInput) {
                        this.$refs.commandInput.focus();
                    }
                });
            }
        });
    },

    beforeUnmount() {
        if (this.ws) {
            this.ws.close();
        }
    },

    methods: {
        async loadInitialData() {
            try {
                // Load server status
                const statusResponse = await fetch('/api/status');
                const statusData = await statusResponse.json();

                this.stats.clients = statusData.clients;
                this.stats.sessions = statusData.sessions;
                this.serverInfo = statusData.server_info;

                // Load clients
                await this.loadClients();

                // Load sessions
                await this.loadSessions();

            } catch (error) {
                console.error('Failed to load initial data:', error);
                this.showNotification('Failed to load data', 'error');
            }
        },

        async loadClients() {
            try {
                const response = await fetch('/api/clients');
                const data = await response.json();
                this.clients = data.clients;
                this.stats.clients = this.clients.length;
            } catch (error) {
                console.error('Failed to load clients:', error);
            }
        },

        async loadSessions() {
            try {
                const response = await fetch('/api/sessions');
                const data = await response.json();
                this.sessions = data.sessions;
                this.stats.sessions = this.sessions.length;
            } catch (error) {
                console.error('Failed to load sessions:', error);
            }
        },

        async refreshData() {
            await Promise.all([
                this.loadClients(),
                this.loadSessions()
            ]);
            this.showNotification('Data refreshed', 'success');
        },

        initializeWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.serverStatus = 'connected';
                this.reconnectAttempts = 0;
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.serverStatus = 'disconnected';
                this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.serverStatus = 'disconnected';
            };

            // Send ping every 30 seconds to keep connection alive
            setInterval(() => {
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({ type: 'ping' }));
                }
            }, 30000);
        },

        attemptReconnect() {
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

                setTimeout(() => {
                    this.initializeWebSocket();
                }, 2000 * this.reconnectAttempts); // Exponential backoff
            } else {
                console.error('Max reconnection attempts reached');
                this.showNotification('Connection lost. Please refresh the page.', 'error');
            }
        },

        handleWebSocketMessage(data) {
            switch (data.type) {
                case 'initial_data':
                    this.clients = data.clients || [];
                    this.sessions = data.sessions || [];
                    this.stats.clients = this.clients.length;
                    this.stats.sessions = this.sessions.length;
                    break;

                case 'clients_updated':
                    this.clients = data.clients || [];
                    this.stats.clients = this.clients.length;
                    break;

                case 'sessions_updated':
                    this.sessions = data.sessions || [];
                    this.stats.sessions = this.sessions.length;
                    break;

                case 'command_executed':
                    this.handleCommandResult(data);
                    break;

                case 'pong':
                    // Keep-alive response
                    break;

                default:
                    console.log('Unknown WebSocket message type:', data.type);
            }
        },

        handleCommandResult(data) {
            const entry = {
                id: Date.now(),
                session: data.session_name,
                command: data.command,
                timestamp: new Date().toISOString(),
                success: data.result.success,
                output: '',
                error: ''
            };

            if (data.result.success) {
                entry.output = data.result.output || 'Command executed successfully';
            } else {
                entry.error = data.result.error || 'Command execution failed';
            }

            this.terminalHistory.push(entry);

            // Auto-scroll to bottom
            this.$nextTick(() => {
                if (this.$refs.terminalOutput) {
                    this.$refs.terminalOutput.scrollTop = this.$refs.terminalOutput.scrollHeight;
                }
            });
        },

        selectSession(session) {
            this.selectedSession = session.name;
            this.activeTab = 'terminal';

            this.$nextTick(() => {
                if (this.$refs.commandInput) {
                    this.$refs.commandInput.focus();
                }
            });
        },

        async executeCommand() {
            if (!this.selectedSession || !this.currentCommand.trim()) {
                return;
            }

            const command = this.currentCommand.trim();

            // Add to command history
            if (this.commandHistory[this.commandHistory.length - 1] !== command) {
                this.commandHistory.push(command);
            }
            this.historyIndex = -1;

            // Add entry to terminal with pending status
            const entry = {
                id: Date.now(),
                session: this.selectedSession,
                command: command,
                timestamp: new Date().toISOString(),
                success: null,
                output: 'Executing...',
                error: ''
            };

            this.terminalHistory.push(entry);
            this.currentCommand = '';

            // Auto-scroll to bottom
            this.$nextTick(() => {
                if (this.$refs.terminalOutput) {
                    this.$refs.terminalOutput.scrollTop = this.$refs.terminalOutput.scrollHeight;
                }
            });

            try {
                const response = await fetch('/api/execute', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        session_name: this.selectedSession,
                        command: command,
                        timeout: 30.0
                    })
                });

                const result = await response.json();

                // Update the entry with the result
                entry.success = result.success;
                if (result.success) {
                    entry.output = result.output || 'Command executed successfully';
                } else {
                    entry.error = result.error || 'Command execution failed';
                    entry.output = '';
                }

            } catch (error) {
                console.error('Failed to execute command:', error);
                entry.success = false;
                entry.error = 'Network error: Failed to execute command';
                entry.output = '';
            }

            // Auto-scroll to bottom again
            this.$nextTick(() => {
                if (this.$refs.terminalOutput) {
                    this.$refs.terminalOutput.scrollTop = this.$refs.terminalOutput.scrollHeight;
                }
            });
        },

        historyUp() {
            if (this.commandHistory.length === 0) return;

            if (this.historyIndex === -1) {
                this.historyIndex = this.commandHistory.length - 1;
            } else if (this.historyIndex > 0) {
                this.historyIndex--;
            }

            this.currentCommand = this.commandHistory[this.historyIndex] || '';
        },

        historyDown() {
            if (this.commandHistory.length === 0 || this.historyIndex === -1) return;

            if (this.historyIndex < this.commandHistory.length - 1) {
                this.historyIndex++;
                this.currentCommand = this.commandHistory[this.historyIndex] || '';
            } else {
                this.historyIndex = -1;
                this.currentCommand = '';
            }
        },

        getClientStatus(client) {
            const lastHeartbeat = new Date(client.last_heartbeat);
            const now = new Date();
            const diffSeconds = (now - lastHeartbeat) / 1000;

            // Consider client offline if no heartbeat for more than 2 minutes
            return diffSeconds > 120 ? 'offline' : 'online';
        },

        getClientStatusText(client) {
            return this.getClientStatus(client) === 'online' ? 'Online' : 'Offline';
        },

        formatTime(isoString) {
            try {
                const date = new Date(isoString);
                return date.toLocaleTimeString();
            } catch (error) {
                return 'Invalid time';
            }
        },

        showNotification(message, type = 'info') {
            // Simple notification system - can be enhanced with a proper toast library
            console.log(`[${type.toUpperCase()}] ${message}`);

            // Create a simple toast notification
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.textContent = message;
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 1rem 1.5rem;
                border-radius: 8px;
                color: white;
                font-weight: 500;
                z-index: 1000;
                animation: slideIn 0.3s ease;
                ${type === 'success' ? 'background: #10b981;' : ''}
                ${type === 'error' ? 'background: #ef4444;' : ''}
                ${type === 'info' ? 'background: #3b82f6;' : ''}
            `;

            document.body.appendChild(toast);

            setTimeout(() => {
                toast.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => {
                    document.body.removeChild(toast);
                }, 300);
            }, 3000);
        }
    }
}).mount('#app');

// Add CSS animations for toasts
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
