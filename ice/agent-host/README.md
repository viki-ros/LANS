# LANS ICE Agent Host
## Local service providing system access for LANS ICE desktop application

This service provides the backend capabilities for LANS ICE, including:

- WebSocket communication with the desktop app
- File system monitoring and operations
- Terminal session management
- Agent process management and memory introspection
- Context management for files, URLs, and text

## Installation

```bash
cd LANS/ice/agent-host
pip install -e .
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python -m lans_host.main

# Run with auto-reload for development
uvicorn lans_host.main:app --reload --host 0.0.0.0 --port 8765
```

## API Endpoints

### WebSocket
- `ws://localhost:8765/ws` - Main WebSocket connection for real-time communication

### REST API
- `GET /health` - Service health check
- `GET /projects` - List available projects
- `POST /projects/{id}/select` - Select active project
- `GET /files` - Get file tree for current project
- `POST /context/attach` - Attach file/URL/text to context

## WebSocket Events

### From Desktop App to Agent Host
```json
{
  "type": "command_request",
  "command": "implement OAuth2 authentication",
  "context": ["auth.py", "https://oauth.net/2/"],
  "mode": "expert"
}
```

### From Agent Host to Desktop App
```json
{
  "type": "agent_thought",
  "content": "Analyzing OAuth2 implementation options...",
  "timestamp": "2024-01-15T14:35:23Z"
}

{
  "type": "file_changed",
  "path": "/project/src/auth.py",
  "change_type": "modified",
  "diff": "+import oauth2\n+import jwt"
}

{
  "type": "command_output",
  "command": "npm test",
  "output": "✓ 2 tests passed",
  "exit_code": 0
}
```

## Security

The agent host runs with the same security model as existing LANS components:
- Sandboxed command execution
- File system access controls
- Rate limiting and validation
- Secure WebSocket connections
