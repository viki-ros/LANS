"""
LANS ICE Agent Host - Main Application

FastAPI application providing WebSocket and REST API endpoints
for real-time communication with the LANS ICE desktop application.
"""

import asyncio
import logging
import os
import socket
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .websocket.manager import WebSocketManager
from .websocket.events import EventType, BaseEvent
from .file_system.watcher import FileSystemWatcher
from .agent.manager import AgentManager
from .context.manager import ContextManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_port_available(host: str, port: int) -> bool:
    """Check if a port is available for binding"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            return True
    except OSError:
        return False

def find_available_port(host: str, preferred_port: int, max_attempts: int = 10) -> int:
    """Find an available port, starting from the preferred port"""
    for port_offset in range(max_attempts):
        test_port = preferred_port + port_offset
        if is_port_available(host, test_port):
            return test_port
    
    raise RuntimeError(f"Could not find an available port in range {preferred_port}-{preferred_port + max_attempts - 1}")

def kill_process_on_port(port: int) -> bool:
    """Kill any process using the specified port"""
    try:
        import subprocess
        import signal
        
        # Find process using the port
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    pid_int = int(pid.strip())
                    logger.warning(f"Killing process {pid_int} using port {port}")
                    os.kill(pid_int, signal.SIGTERM)
                    # Give process time to terminate gracefully
                    import time
                    time.sleep(1)
                    # Force kill if still running
                    try:
                        os.kill(pid_int, signal.SIGKILL)
                    except ProcessLookupError:
                        pass  # Process already terminated
                except (ValueError, ProcessLookupError):
                    continue
            return True
    except (FileNotFoundError, subprocess.SubprocessError) as e:
        logger.debug(f"Could not kill process on port {port}: {e}")
    
    return False

# Global managers
websocket_manager = WebSocketManager()
file_watcher: Optional[FileSystemWatcher] = None
agent_manager: Optional[AgentManager] = None
context_manager = ContextManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global file_watcher, agent_manager
    
    # Startup
    logger.info("Starting LANS ICE Agent Host...")
    
    # Initialize file system watcher
    file_watcher = FileSystemWatcher(websocket_manager)
    
    # Initialize agent manager
    agent_manager = AgentManager(websocket_manager)
    
    # Start background tasks
    asyncio.create_task(file_watcher.start())
    asyncio.create_task(agent_manager.start())
    
    # Clean up old sessions (older than 24 hours)
    if hasattr(agent_manager, 'command_bridge') and agent_manager.command_bridge:
        agent_manager.command_bridge.cleanup_old_sessions(24)
    
    logger.info("LANS ICE Agent Host started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down LANS ICE Agent Host...")
    if file_watcher:
        await file_watcher.stop()
    if agent_manager:
        await agent_manager.stop()
    logger.info("LANS ICE Agent Host stopped")

# Create FastAPI application
app = FastAPI(
    title="LANS ICE Agent Host",
    description="Backend service for LANS Integrated Cognitive Environment",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict

class ProjectInfo(BaseModel):
    id: str
    name: str
    path: str
    active: bool

class FileInfo(BaseModel):
    path: str
    name: str
    type: str  # "file" or "directory"
    size: Optional[int] = None
    modified: Optional[str] = None

class ContextAttachment(BaseModel):
    type: str  # "file", "url", or "text"
    content: str
    metadata: Optional[dict] = None

# REST API endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        services={
            "websocket": "running",
            "file_watcher": "running" if file_watcher else "stopped",
            "agent_manager": "running" if agent_manager else "stopped"
        }
    )

@app.get("/projects", response_model=List[ProjectInfo])
async def list_projects():
    """List available projects"""
    # For now, return current directory as a project
    current_dir = Path.cwd()
    return [
        ProjectInfo(
            id="current",
            name=current_dir.name,
            path=str(current_dir),
            active=True
        )
    ]

@app.post("/projects/{project_id}/select")
async def select_project(project_id: str):
    """Select active project"""
    if project_id != "current":
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Notify all connected clients about project selection
    await websocket_manager.broadcast({
        "type": EventType.PROJECT_SELECTED,
        "project_id": project_id,
        "timestamp": BaseEvent.get_timestamp()
    })
    
    return {"status": "success", "project_id": project_id}

@app.get("/files", response_model=List[FileInfo])
async def list_files(path: str = "."):
    """Get file tree for current project"""
    try:
        target_path = Path(path).resolve()
        files = []
        
        for item in target_path.iterdir():
            file_info = FileInfo(
                path=str(item),
                name=item.name,
                type="directory" if item.is_dir() else "file"
            )
            
            if item.is_file():
                try:
                    stat = item.stat()
                    file_info.size = stat.st_size
                    file_info.modified = str(stat.st_mtime)
                except (OSError, PermissionError):
                    pass
            
            files.append(file_info)
        
        return sorted(files, key=lambda x: (x.type == "file", x.name.lower()))
    
    except (OSError, PermissionError) as e:
        raise HTTPException(status_code=403, detail=f"Access denied: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@app.post("/context/attach")
async def attach_context(attachment: ContextAttachment):
    """Attach file/URL/text to context"""
    try:
        context_id = await context_manager.attach(
            attachment.type,
            attachment.content,
            attachment.metadata or {}
        )
        
        # Notify all connected clients about context update
        await websocket_manager.broadcast({
            "type": EventType.CONTEXT_UPDATED,
            "context_id": context_id,
            "attachment": attachment.dict(),
            "timestamp": BaseEvent.get_timestamp()
        })
        
        return {"status": "success", "context_id": context_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error attaching context: {str(e)}")

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time communication"""
    await websocket_manager.connect(websocket)
    
    try:
        # Send initial status
        await websocket_manager.send_to_websocket(websocket, {
            "type": EventType.CONNECTION_ESTABLISHED,
            "status": "connected",
            "timestamp": BaseEvent.get_timestamp()
        })
        
        # Listen for messages
        while True:
            data = await websocket.receive_json()
            await handle_websocket_message(websocket, data)
            
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        websocket_manager.disconnect(websocket)

async def handle_websocket_message(websocket: WebSocket, data: dict):
    """Handle incoming WebSocket messages"""
    message_type = data.get("type")
    
    if message_type == "command_request":
        # Handle command execution request
        if agent_manager:
            await agent_manager.execute_command(
                data.get("command", ""),
                data.get("context", []),
                data.get("mode", "assistant")
            )
    
    elif message_type == "create_terminal":
        # Create a new agent command session
        if hasattr(agent_manager, 'command_bridge') and agent_manager.command_bridge:
            try:
                working_dir = data.get("working_directory", os.getcwd())
                persistent = data.get("persistent", False)
                
                if persistent:
                    session_id = await agent_manager.command_bridge.create_persistent_session(working_dir)
                else:
                    session_id = await agent_manager.command_bridge.create_session(working_dir)
                    
                await websocket_manager.send_to_websocket(websocket, {
                    "type": "terminal_created",
                    "session_id": session_id,
                    "working_directory": working_dir,
                    "persistent": persistent,
                    "timestamp": BaseEvent.get_timestamp()
                })
            except Exception as e:
                await websocket_manager.send_to_websocket(websocket, {
                    "type": "error",
                    "error": str(e),
                    "timestamp": BaseEvent.get_timestamp()
                })

    elif message_type == "restore_session":
        # Restore a persistent session
        if hasattr(agent_manager, 'command_bridge') and agent_manager.command_bridge:
            try:
                session_id = data.get("session_id")
                if not session_id:
                    raise ValueError("No session_id provided")
                
                success = await agent_manager.command_bridge.restore_session(session_id)
                if success:
                    session = agent_manager.command_bridge.get_session(session_id)
                    await websocket_manager.send_to_websocket(websocket, {
                        "type": "session_restored",
                        "session_id": session_id,
                        "working_directory": session.working_directory,
                        "command_history": session.command_history[-5:],  # Last 5 commands
                        "timestamp": BaseEvent.get_timestamp()
                    })
                else:
                    await websocket_manager.send_to_websocket(websocket, {
                        "type": "error",
                        "error": f"Could not restore session {session_id}",
                        "timestamp": BaseEvent.get_timestamp()
                    })
            except Exception as e:
                await websocket_manager.send_to_websocket(websocket, {
                    "type": "error",
                    "error": str(e),
                    "timestamp": BaseEvent.get_timestamp()
                })

    elif message_type == "list_saved_sessions":
        # List all saved persistent sessions
        if hasattr(agent_manager, 'command_bridge') and agent_manager.command_bridge:
            try:
                saved_sessions = agent_manager.command_bridge.list_saved_sessions()
                await websocket_manager.send_to_websocket(websocket, {
                    "type": "saved_sessions",
                    "sessions": saved_sessions,
                    "timestamp": BaseEvent.get_timestamp()
                })
            except Exception as e:
                await websocket_manager.send_to_websocket(websocket, {
                    "type": "error",
                    "error": str(e),
                    "timestamp": BaseEvent.get_timestamp()
                })
    
    elif message_type == "terminal_input":
        # Execute command through agent command bridge
        if hasattr(agent_manager, 'command_bridge') and agent_manager.command_bridge:
            try:
                session_id = data.get("session_id")
                input_data = data.get("data", "")
                
                # Execute command if it ends with newline (complete command)
                if input_data.endswith('\n') or input_data.endswith('\r'):
                    command = input_data.strip()
                    if command:
                        await agent_manager.command_bridge.execute_command(session_id, command)
                        
            except Exception as e:
                await websocket_manager.send_to_websocket(websocket, {
                    "type": "error",
                    "error": str(e),
                    "timestamp": BaseEvent.get_timestamp()
                })
    
    elif message_type == "ping":
        # Respond to ping with pong
        await websocket_manager.send_to_websocket(websocket, {
            "type": "pong",
            "timestamp": BaseEvent.get_timestamp()
        })
    
    elif message_type == "list_files":
        # List files in a directory
        try:
            path = data.get("path", ".")
            target_path = Path(path).resolve()
            files = []
            
            for item in target_path.iterdir():
                files.append(str(item))
            
            await websocket_manager.send_to_websocket(websocket, {
                "type": "file_list",
                "files": sorted(files),
                "path": str(target_path),
                "timestamp": BaseEvent.get_timestamp()
            })
        except Exception as e:
            await websocket_manager.send_to_websocket(websocket, {
                "type": "error",
                "message": f"Failed to list files: {str(e)}",
                "timestamp": BaseEvent.get_timestamp()
            })
    
    elif message_type == "read_file":
        # Read file content
        try:
            file_path = data.get("path")
            if not file_path:
                raise ValueError("No file path provided")
            
            path = Path(file_path).resolve()
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if path.is_dir():
                raise IsADirectoryError(f"Path is a directory: {file_path}")
            
            # Read file content (limit size for safety)
            if path.stat().st_size > 10 * 1024 * 1024:  # 10MB limit
                raise ValueError("File too large to read")
            
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            await websocket_manager.send_to_websocket(websocket, {
                "type": "file_content",
                "path": str(path),
                "content": content,
                "timestamp": BaseEvent.get_timestamp()
            })
        except Exception as e:
            await websocket_manager.send_to_websocket(websocket, {
                "type": "error",
                "message": f"Failed to read file: {str(e)}",
                "timestamp": BaseEvent.get_timestamp()
            })
    
    elif message_type == "write_file":
        # Write file content
        try:
            file_path = data.get("path")
            content = data.get("content", "")
            
            if not file_path:
                raise ValueError("No file path provided")
            
            path = Path(file_path).resolve()
            
            # Create directory if it doesn't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            await websocket_manager.send_to_websocket(websocket, {
                "type": "file_saved",
                "path": str(path),
                "timestamp": BaseEvent.get_timestamp()
            })
            
            # Broadcast file change to other clients
            await websocket_manager.broadcast({
                "type": "file_changed",
                "path": str(path),
                "change_type": "modified",
                "timestamp": BaseEvent.get_timestamp()
            })
            
        except Exception as e:
            await websocket_manager.send_to_websocket(websocket, {
                "type": "error",
                "message": f"Failed to write file: {str(e)}",
                "timestamp": BaseEvent.get_timestamp()
            })
    
    elif message_type == "terminal_resize":
        # Handle terminal resize
        if hasattr(agent_manager, 'terminal_manager'):
            try:
                session_id = data.get("session_id")
                cols = data.get("cols", 80)
                rows = data.get("rows", 24)
                await agent_manager.terminal_manager.resize_terminal(session_id, cols, rows)
            except Exception as e:
                await websocket_manager.send_to_websocket(websocket, {
                    "type": "error",
                    "error": str(e),
                    "timestamp": BaseEvent.get_timestamp()
                })
    
    else:
        logger.warning(f"Unknown message type: {message_type}")

def main():
    """Main entry point for running the agent host"""
    port = int(os.getenv("LANS_ICE_PORT", "8765"))
    host = os.getenv("LANS_ICE_HOST", "127.0.0.1")
    
    logger.info(f"Starting LANS ICE Agent Host on {host}:{port}")
    
    # Check if port is available
    if not is_port_available(host, port):
        logger.warning(f"Port {port} is already in use!")
        
        # Try to kill existing process
        if kill_process_on_port(port):
            logger.info(f"Killed existing process on port {port}")
            # Wait a moment for the port to be released
            import time
            time.sleep(2)
            
            # Check if port is now available
            if is_port_available(host, port):
                logger.info(f"Port {port} is now available")
            else:
                logger.error(f"Port {port} is still not available after killing process")
                # Try to find alternative port
                try:
                    alternative_port = find_available_port(host, port + 1)
                    logger.warning(f"Using alternative port {alternative_port}")
                    port = alternative_port
                except RuntimeError as e:
                    logger.error(f"Could not find available port: {e}")
                    sys.exit(1)
        else:
            # Try to find alternative port
            try:
                alternative_port = find_available_port(host, port + 1)
                logger.warning(f"Could not kill process on port {port}, using alternative port {alternative_port}")
                port = alternative_port
            except RuntimeError as e:
                logger.error(f"Could not find available port: {e}")
                sys.exit(1)
    
    logger.info(f"✅ Port {port} is available, starting server...")
    
    try:
        # Run uvicorn directly with the app instance to avoid import issues
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=False,  # Disable reload to prevent import issues
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
