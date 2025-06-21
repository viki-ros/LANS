"""
Agent Command Bridge for LANS ICE

Bridges the existing LANS CommandHandler with the ICE WebSocket interface
for optimal agent-driven command execution.
"""

import asyncio
import logging
import uuid
import json
import pickle
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, AsyncGenerator

from ..websocket.manager import WebSocketManager

logger = logging.getLogger(__name__)

# Session storage directory
SESSION_STORAGE_DIR = Path.home() / ".lans_ice" / "sessions"
SESSION_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class AgentCommandSession:
    """Represents an agent-driven command execution session"""
    
    def __init__(self, session_id: str, websocket_manager: WebSocketManager, command_handler):
        self.session_id = session_id
        self.websocket_manager = websocket_manager
        self.command_handler = command_handler
        self.is_active = True
        self.working_directory = None
        self.environment = {}
        self.command_history = []
        self.max_history = 100
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.persistent = False  # Whether this session should be saved
    
    async def execute_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute command using LANS CommandHandler with real-time streaming"""
        try:
            # Broadcast command start
            await self._broadcast_event("command_start", {
                "command": command,
                "working_directory": self.working_directory
            })
            
            # Execute through existing LANS infrastructure
            result = await self.command_handler.run_command(
                command=command,
                cwd=self.working_directory,
                timeout=timeout
            )
            
            # Stream output in chunks for real-time feel
            if result.get("stdout"):
                await self._stream_output(result["stdout"], "stdout")
            
            if result.get("stderr"):
                await self._stream_output(result["stderr"], "stderr")
            
            # Add to history
            self._add_to_history(command, result)
            
            # Save session state if persistent
            if self.persistent:
                self.save_to_disk()
            
            # Broadcast completion
            await self._broadcast_event("command_complete", {
                "command": command,
                "exit_code": result.get("exit_code", 0),
                "success": result.get("success", False)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            await self._broadcast_event("command_error", {
                "command": command,
                "error": str(e)
            })
            raise
    
    async def _stream_output(self, output: str, stream_type: str):
        """Stream output in chunks to simulate real-time"""
        # Split into lines for more natural streaming
        lines = output.split('\n')
        
        for i, line in enumerate(lines):
            if line or i < len(lines) - 1:  # Include empty lines except final one
                await self._broadcast_event("terminal_output", {
                    "data": line + ('\n' if i < len(lines) - 1 else ''),
                    "stream": stream_type
                })
                
                # Small delay for real-time feel
                await asyncio.sleep(0.01)
    
    async def _broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcast event to connected clients"""
        await self.websocket_manager.broadcast({
            "type": event_type,
            "session_id": self.session_id,
            **data,
            "timestamp": self._get_timestamp()
        })
    
    def _add_to_history(self, command: str, result: Dict[str, Any]):
        """Add command execution to history"""
        self.command_history.append({
            "command": command,
            "result": result,
            "timestamp": self._get_timestamp()
        })
        
        # Limit history size
        if len(self.command_history) > self.max_history:
            self.command_history = self.command_history[-self.max_history:]
    
    def set_working_directory(self, directory: str):
        """Set working directory for future commands"""
        self.working_directory = directory
    
    def set_environment(self, env_vars: Dict[str, str]):
        """Set environment variables"""
        self.environment.update(env_vars)
    
    def get_status(self) -> Dict[str, Any]:
        """Get session status"""
        return {
            "session_id": self.session_id,
            "is_active": self.is_active,
            "working_directory": self.working_directory,
            "command_count": len(self.command_history),
            "environment_vars": len(self.environment)
        }
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
    
    def enable_persistence(self):
        """Enable persistence for this session"""
        self.persistent = True
        self.last_activity = datetime.utcnow()

    def save_to_disk(self):
        """Save session state to disk"""
        if not self.persistent:
            return
        
        self.last_activity = datetime.utcnow()
        
        session_data = {
            "session_id": self.session_id,
            "working_directory": self.working_directory,
            "environment": self.environment,
            "command_history": self.command_history,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "persistent": self.persistent
        }
        
        file_path = SESSION_STORAGE_DIR / f"{self.session_id}.json"
        try:
            with open(file_path, "w") as f:
                json.dump(session_data, f, indent=2)
            logger.info(f"Session {self.session_id} saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save session {self.session_id}: {e}")

    @classmethod
    def restore_from_disk(cls, session_id: str, websocket_manager: WebSocketManager, command_handler) -> Optional["AgentCommandSession"]:
        """Restore session from disk"""
        file_path = SESSION_STORAGE_DIR / f"{session_id}.json"
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r") as f:
                session_data = json.load(f)
            
            # Create new session with restored data
            session = cls(session_id, websocket_manager, command_handler)
            session.working_directory = session_data.get("working_directory")
            session.environment = session_data.get("environment", {})
            session.command_history = session_data.get("command_history", [])
            session.created_at = datetime.fromisoformat(session_data.get("created_at"))
            session.last_activity = datetime.fromisoformat(session_data.get("last_activity"))
            session.persistent = session_data.get("persistent", False)
            
            logger.info(f"Session {session_id} restored from {file_path}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to restore session {session_id}: {e}")
            return None

    @staticmethod
    def cleanup_old_sessions(max_age_hours: int = 24):
        """Clean up old session files"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        for session_file in SESSION_STORAGE_DIR.glob("*.json"):
            try:
                with open(session_file, "r") as f:
                    session_data = json.load(f)
                
                last_activity = datetime.fromisoformat(session_data.get("last_activity"))
                if last_activity < cutoff_time:
                    session_file.unlink()
                    logger.info(f"Cleaned up old session file: {session_file}")
                    
            except Exception as e:
                logger.error(f"Error cleaning up session file {session_file}: {e}")

    # ...existing methods...


class AgentCommandBridge:
    """Bridges LANS CommandHandler with ICE WebSocket interface"""
    
    def __init__(self, websocket_manager: WebSocketManager, command_handler):
        self.websocket_manager = websocket_manager
        self.command_handler = command_handler
        self.sessions: Dict[str, AgentCommandSession] = {}
        self.is_running = False
    
    async def start(self):
        """Start the command bridge"""
        self.is_running = True
        logger.info("Agent Command Bridge started")
    
    async def stop(self):
        """Stop the command bridge"""
        self.is_running = False
        
        # Stop all sessions
        for session in list(self.sessions.values()):
            session.is_active = False
        
        self.sessions.clear()
        logger.info("Agent Command Bridge stopped")
    
    async def create_session(self, working_directory: Optional[str] = None) -> str:
        """Create a new agent command session"""
        session_id = str(uuid.uuid4())
        
        session = AgentCommandSession(
            session_id=session_id,
            websocket_manager=self.websocket_manager,
            command_handler=self.command_handler
        )
        
        if working_directory:
            session.set_working_directory(working_directory)
        
        self.sessions[session_id] = session
        
        logger.info(f"Created agent command session: {session_id}")
        return session_id
    
    async def execute_command(self, session_id: str, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute command in specified session"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.sessions[session_id]
        return await session.execute_command(command, timeout)
    
    async def destroy_session(self, session_id: str):
        """Destroy a command session"""
        if session_id in self.sessions:
            self.sessions[session_id].is_active = False
            del self.sessions[session_id]
            logger.info(f"Destroyed agent command session: {session_id}")
    
    def get_session(self, session_id: str) -> Optional[AgentCommandSession]:
        """Get a command session"""
        return self.sessions.get(session_id)
    
    def get_all_sessions(self) -> Dict[str, AgentCommandSession]:
        """Get all command sessions"""
        return self.sessions.copy()
    
    def get_status(self) -> Dict[str, Any]:
        """Get bridge status"""
        return {
            "is_running": self.is_running,
            "active_sessions": len(self.sessions),
            "sessions": [session.get_status() for session in self.sessions.values()]
        }

    async def create_persistent_session(self, working_directory: Optional[str] = None) -> str:
        """Create a new persistent agent command session"""
        session_id = await self.create_session(working_directory)
        session = self.sessions[session_id]
        session.enable_persistence()
        session.save_to_disk()
        logger.info(f"Created persistent agent command session: {session_id}")
        return session_id

    async def restore_session(self, session_id: str) -> bool:
        """Restore a session from disk"""
        if session_id in self.sessions:
            logger.warning(f"Session {session_id} already exists in memory")
            return True
        
        restored_session = AgentCommandSession.restore_from_disk(
            session_id, self.websocket_manager, self.command_handler
        )
        
        if restored_session:
            self.sessions[session_id] = restored_session
            logger.info(f"Restored session {session_id}")
            return True
        
        return False

    def save_all_sessions(self):
        """Save all persistent sessions to disk"""
        for session in self.sessions.values():
            if session.persistent:
                session.save_to_disk()

    def list_saved_sessions(self) -> List[Dict[str, Any]]:
        """List all saved sessions"""
        saved_sessions = []
        
        for file_path in SESSION_STORAGE_DIR.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    session_data = json.load(f)
                
                saved_sessions.append({
                    "session_id": session_data.get("session_id"),
                    "working_directory": session_data.get("working_directory"),
                    "command_count": len(session_data.get("command_history", [])),
                    "created_at": session_data.get("created_at"),
                    "last_activity": session_data.get("last_activity"),
                    "is_active": session_data.get("session_id") in self.sessions
                })
                
            except Exception as e:
                logger.error(f"Error reading session file {file_path}: {e}")
        
        return saved_sessions

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old session files"""
        AgentCommandSession.cleanup_old_sessions(max_age_hours)
