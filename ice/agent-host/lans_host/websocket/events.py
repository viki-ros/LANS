"""
WebSocket Event Types and Base Classes for LANS ICE
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel


class EventType(str, Enum):
    """WebSocket event types"""
    # Connection events
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_LOST = "connection_lost"
    
    # Agent events
    AGENT_THOUGHT = "agent_thought"
    AGENT_STATUS = "agent_status"
    AGENT_ERROR = "agent_error"
    
    # Command events
    COMMAND_START = "command_start"
    COMMAND_OUTPUT = "command_output"
    COMMAND_COMPLETE = "command_complete"
    COMMAND_ERROR = "command_error"
    
    # File system events
    FILE_CHANGED = "file_changed"
    FILE_CREATED = "file_created"
    FILE_DELETED = "file_deleted"
    FILE_MOVED = "file_moved"
    
    # Project events
    PROJECT_SELECTED = "project_selected"
    PROJECT_STATUS = "project_status"
    
    # Context events
    CONTEXT_UPDATED = "context_updated"
    CONTEXT_REMOVED = "context_removed"
    
    # Memory events
    MEMORY_UPDATED = "memory_updated"
    
    # System events
    SYSTEM_STATUS = "system_status"
    ERROR = "error"


class BaseEvent(BaseModel):
    """Base class for all WebSocket events"""
    type: EventType
    timestamp: str
    
    @staticmethod
    def get_timestamp() -> str:
        """Get current timestamp in ISO format"""
        return datetime.utcnow().isoformat() + "Z"


class AgentThoughtEvent(BaseEvent):
    """Agent thought/reasoning event"""
    type: EventType = EventType.AGENT_THOUGHT
    content: str
    context: Optional[list] = None
    confidence: Optional[float] = None


class CommandEvent(BaseEvent):
    """Command execution event"""
    command: str
    output: Optional[str] = None
    exit_code: Optional[int] = None
    error: Optional[str] = None


class FileSystemEvent(BaseEvent):
    """File system change event"""
    path: str
    change_type: str  # created, modified, deleted, moved
    diff: Optional[str] = None
    old_path: Optional[str] = None  # For move events


class MemoryEvent(BaseEvent):
    """Agent memory update event"""
    type: EventType = EventType.MEMORY_UPDATED
    memory_type: str  # working, context, knowledge
    size: str
    contents: Optional[Dict[str, Any]] = None


class SystemStatusEvent(BaseEvent):
    """System status event"""
    type: EventType = EventType.SYSTEM_STATUS
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_processes: int


class ErrorEvent(BaseEvent):
    """Error event"""
    type: EventType = EventType.ERROR
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
