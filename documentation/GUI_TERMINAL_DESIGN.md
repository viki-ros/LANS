# 🖥️ LANS GUI with Terminal Access - Design Specification

## 🏗️ **Enhanced Architecture Overview**

```
┌─────────────────────────────────────────────────────────────────┐
│                         LANS Web GUI                           │
├─────────────────────────────────────────────────────────────────┤
│  Frontend: React/Vue + xterm.js Terminal Emulator              │
│  Real-time: WebSocket for terminal I/O + system updates        │
│  Security: Client-side command validation + server-side        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Enhanced LANS Backend                        │
├─────────────────────────────────────────────────────────────────┤
│  • WebSocket Terminal Server (new)                             │
│  • GUI API Extensions (new)                                    │
│  • Existing FastAPI server                                     │
│  • Real-time event broadcasting                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Existing LANS Security Layer                  │
├─────────────────────────────────────────────────────────────────┤
│  • SandboxManager (path validation, command filtering)         │
│  • CommandHandler (secure execution, timeout handling)         │
│  • AgentOS Kernel (tool registry, AIL integration)             │
└─────────────────────────────────────────────────────────────────┘
```

## 🎨 **GUI Module Structure (Enhanced)**

```
gui/
├── static/
│   ├── css/
│   │   ├── main.css              # Main styling
│   │   ├── dashboard.css         # Dashboard-specific styles
│   │   ├── terminal.css          # Terminal emulator styles
│   │   └── components.css        # Reusable components
│   ├── js/
│   │   ├── main.js               # Core JavaScript
│   │   ├── dashboard.js          # Dashboard functionality
│   │   ├── agents.js             # Agent management
│   │   ├── memory.js             # Memory explorer
│   │   ├── cognition.js          # Cognition studio
│   │   ├── terminal.js           # Terminal emulator (xterm.js)
│   │   ├── websocket.js          # Real-time updates
│   │   └── security.js           # Client-side security validation
│   ├── lib/
│   │   ├── xterm.js              # Terminal emulator library
│   │   ├── xterm.css             # Terminal styling
│   │   └── fit-addon.js          # Terminal resize addon
│   └── assets/
│       ├── icons/                # UI icons
│       └── fonts/                # Custom fonts
├── templates/
│   ├── base.html                 # Base template
│   ├── dashboard.html            # Main dashboard
│   ├── agents.html               # Agent management
│   ├── memory.html               # Memory explorer
│   ├── cognition.html            # Cognition studio with terminal
│   ├── terminal.html             # Dedicated terminal interface
│   └── settings.html             # System settings
├── components/
│   ├── agent_card.html           # Reusable agent card
│   ├── metric_card.html          # Metric display card
│   ├── memory_browser.html       # Memory browsing component
│   ├── code_editor.html          # AIL code editor
│   ├── terminal_widget.html      # Embeddable terminal
│   └── command_history.html      # Command history component
├── backend/
│   ├── __init__.py               # GUI backend initialization
│   ├── routes.py                 # Web routes for GUI
│   ├── websocket_handlers.py     # WebSocket terminal handlers
│   ├── terminal_server.py        # Terminal session management
│   ├── security_middleware.py    # GUI security layer
│   └── real_time.py              # Real-time data broadcasting
└── tests/
    ├── test_terminal_gui.py      # Terminal GUI tests
    ├── test_security.py          # Security validation tests
    └── test_websocket.py         # WebSocket functionality tests
```

## 🚀 **Key GUI Features with Terminal Integration**

### **1. Multi-Mode Terminal Access**

#### **A. Embedded Terminal Widgets**
```html
<!-- Terminal widget in agent cards -->
<div class="agent-card">
    <h3>🤖 Coding Agent</h3>
    <div class="agent-terminal-widget">
        <div class="terminal-header">
            <span>Agent Terminal</span>
            <button class="expand-terminal">⛶</button>
        </div>
        <div class="mini-terminal" id="agent-coding-terminal"></div>
    </div>
</div>
```

#### **B. Full-Screen Terminal Interface**
```html
<!-- Dedicated terminal page -->
<div class="terminal-interface">
    <div class="terminal-tabs">
        <div class="tab active" data-session="main">Main Terminal</div>
        <div class="tab" data-session="agent-1">Agent 1</div>
        <div class="tab" data-session="debug">Debug Session</div>
        <button class="new-tab-btn">+ New</button>
    </div>
    <div class="terminal-container">
        <div id="main-terminal" class="terminal-session active"></div>
    </div>
</div>
```

#### **C. Cognition Studio with Integrated Terminal**
```html
<!-- AIL editor with terminal output -->
<div class="cognition-studio">
    <div class="editor-section">
        <textarea id="ail-editor" placeholder="Enter AIL code...">
(EXECUTE [tool_shell] ["ls -la"])
        </textarea>
        <button id="execute-cognition">Execute</button>
    </div>
    <div class="output-section">
        <div class="tabs">
            <button class="tab-btn active" data-target="results">Results</button>
            <button class="tab-btn" data-target="terminal">Terminal</button>
            <button class="tab-btn" data-target="memory">Memory</button>
        </div>
        <div id="results" class="output-panel active">
            <!-- Cognition results -->
        </div>
        <div id="terminal" class="output-panel">
            <div id="cognition-terminal"></div>
        </div>
    </div>
</div>
```

### **2. Security-First Design**

#### **Command Validation Interface**
```javascript
// Client-side command validation
class SecureTerminal {
    constructor(sessionId, agentId) {
        this.sessionId = sessionId;
        this.agentId = agentId;
        this.allowedCommands = [];
        this.commandHistory = [];
        this.initializeSecurity();
    }
    
    async validateCommand(command) {
        // Client-side pre-validation
        const dangerous = ['rm -rf', 'sudo rm', 'dd if=', '>/dev/'];
        for (const pattern of dangerous) {
            if (command.includes(pattern)) {
                return { valid: false, reason: 'Dangerous command detected' };
            }
        }
        
        // Server-side validation via API
        const response = await fetch('/api/v1/terminal/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                command, 
                sessionId: this.sessionId,
                agentId: this.agentId 
            })
        });
        
        return await response.json();
    }
    
    async executeCommand(command) {
        const validation = await this.validateCommand(command);
        if (!validation.valid) {
            this.displayError(`Command blocked: ${validation.reason}`);
            return;
        }
        
        // Send to terminal via WebSocket
        this.websocket.send(JSON.stringify({
            type: 'execute',
            command: command,
            sessionId: this.sessionId
        }));
    }
}
```

### **3. Agent-Integrated Terminal Sessions**

#### **Agent-Specific Terminal Management**
```python
# Backend: Agent terminal session management
class AgentTerminalManager:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.sandbox = SandboxManager(f"/tmp/lans_agent_{agent_id}")
        self.command_handler = CommandHandler(self.sandbox)
        self.session_history = []
        
    async def create_session(self, user_id: str) -> str:
        """Create a new terminal session for the agent."""
        session_id = f"agent_{self.agent_id}_{uuid.uuid4().hex[:8]}"
        
        # Initialize sandbox for this session
        await self.sandbox.initialize()
        
        # Set up agent-specific environment
        env_vars = {
            'LANS_AGENT_ID': self.agent_id,
            'LANS_SESSION_ID': session_id,
            'LANS_USER_ID': user_id
        }
        
        return session_id
    
    async def execute_command_for_gui(
        self, 
        session_id: str, 
        command: str, 
        websocket: WebSocket
    ):
        """Execute command and stream output to GUI via WebSocket."""
        try:
            # Validate command through existing security layer
            if not self.sandbox.is_command_allowed(command):
                await websocket.send_json({
                    'type': 'error',
                    'message': f'Command not allowed: {command}'
                })
                return
            
            # Stream command execution
            await websocket.send_json({
                'type': 'command_start',
                'command': command
            })
            
            # Execute with real-time output streaming
            result = await self.command_handler.run_command(
                command, 
                timeout=300  # 5 minute timeout for GUI commands
            )
            
            # Send results back to GUI
            await websocket.send_json({
                'type': 'command_complete',
                'result': result
            })
            
        except Exception as e:
            await websocket.send_json({
                'type': 'error',
                'message': str(e)
            })
```

### **4. Real-Time Terminal Features**

#### **WebSocket Terminal Protocol**
```javascript
// Frontend: Real-time terminal communication
class LANSTerminal {
    constructor(containerId, sessionType = 'main') {
        this.container = document.getElementById(containerId);
        this.sessionType = sessionType;
        this.term = new Terminal({
            theme: {
                background: '#1a1a1a',
                foreground: '#ffffff',
                cursor: '#00ff00'
            }
        });
        
        this.setupWebSocket();
        this.initializeTerminal();
    }
    
    setupWebSocket() {
        this.ws = new WebSocket(`ws://localhost:8001/ws/terminal/${this.sessionType}`);
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
                case 'stdout':
                    this.term.write(data.content);
                    break;
                case 'stderr':
                    this.term.write(`\x1b[31m${data.content}\x1b[0m`); // Red text
                    break;
                case 'command_complete':
                    this.term.write(`\n\x1b[32m[Exit: ${data.result.exit_code}]\x1b[0m\n$ `);
                    break;
                case 'error':
                    this.term.write(`\x1b[31mError: ${data.message}\x1b[0m\n$ `);
                    break;
            }
        };
    }
    
    initializeTerminal() {
        this.term.open(this.container);
        this.term.write('Welcome to LANS Terminal\n$ ');
        
        // Handle user input
        this.term.onData((data) => {
            if (data === '\r') { // Enter key
                const command = this.currentCommand;
                this.currentCommand = '';
                this.term.write('\n');
                
                // Send command to backend
                this.ws.send(JSON.stringify({
                    type: 'execute',
                    command: command
                }));
            } else if (data === '\u007f') { // Backspace
                if (this.currentCommand.length > 0) {
                    this.currentCommand = this.currentCommand.slice(0, -1);
                    this.term.write('\b \b');
                }
            } else {
                this.currentCommand += data;
                this.term.write(data);
            }
        });
    }
}
```

## 🔐 **Enhanced Security Model**

### **Multi-Layer Security Architecture**
```python
# Backend: Enhanced security for GUI terminal access
class GUISecurityMiddleware:
    def __init__(self):
        self.session_permissions = {}
        self.command_audit_log = []
        
    async def validate_gui_session(self, session_id: str, user_id: str) -> bool:
        """Validate GUI session has terminal access."""
        # Check session permissions
        permissions = self.session_permissions.get(session_id, {})
        return permissions.get('terminal_access', False)
    
    async def audit_command(self, session_id: str, command: str, result: dict):
        """Audit all commands executed through GUI."""
        audit_entry = {
            'timestamp': datetime.utcnow(),
            'session_id': session_id,
            'command': command,
            'success': result.get('success', False),
            'exit_code': result.get('exit_code', -1)
        }
        self.command_audit_log.append(audit_entry)
        
        # Store in database for permanent audit trail
        await self.store_audit_entry(audit_entry)
    
    def get_restricted_commands_for_gui(self) -> List[str]:
        """Get additional restrictions for GUI-initiated commands."""
        return [
            # File system operations that could affect LANS
            'rm /home/viki/LANS/*',
            'chmod 777',
            'chown root',
            
            # Network operations
            'netcat',
            'nc',
            'wget',
            'curl http',
            
            # System modification
            'systemctl',
            'service',
            'mount',
            'umount'
        ]
```

## 📊 **Terminal Integration Points**

### **1. Dashboard Integration**
- **Mini terminals** in agent status cards
- **System terminal** for quick commands
- **Real-time command output** streaming

### **2. Agent Management Integration**
- **Per-agent terminal sessions**
- **Agent command history**
- **Agent-specific environment variables**

### **3. Cognition Studio Integration**
- **AIL execution with terminal output**
- **Interactive debugging**
- **Command result visualization**

### **4. Memory System Integration**
- **Command history stored in memory**
- **Terminal session replay**
- **Knowledge extraction from command patterns**

## 🎯 **Implementation Priority**

### **Phase 1: Foundation** (Week 1-2)
1. **Basic WebSocket terminal server**
2. **Simple terminal widget integration**
3. **Security validation layer**

### **Phase 2: Core Features** (Week 3-4)
4. **Multi-session terminal management**
5. **Agent-specific terminal sessions**
6. **Command history and audit logging**

### **Phase 3: Advanced Features** (Week 5-6)
7. **Real-time output streaming**
8. **Terminal session recording/replay**
9. **Advanced security policies**

### **Phase 4: Polish** (Week 7-8)
10. **Performance optimization**
11. **UI/UX improvements**
12. **Comprehensive testing**

## 🚨 **Critical Security Considerations**

### **Command Execution Safety**
- ✅ **Leverage existing SandboxManager**
- ✅ **Multiple validation layers** (client + server)
- ✅ **Command audit trail**
- ✅ **Session isolation**
- ✅ **Timeout protection**

### **Access Control**
- ✅ **User authentication required**
- ✅ **Role-based terminal permissions**
- ✅ **Agent-specific command restrictions**
- ✅ **Session-based security tokens**

### **Monitoring & Alerting**
- ✅ **Real-time command monitoring**
- ✅ **Suspicious activity detection**
- ✅ **Failed command attempt logging**
- ✅ **Security event notifications**

This design leverages LANS's existing robust security infrastructure while providing a powerful, user-friendly terminal interface that enables LANS to function as a true agent system with real-world capabilities.
