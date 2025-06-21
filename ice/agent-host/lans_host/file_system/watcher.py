"""
File System Watcher for LANS ICE

Monitors file system changes and broadcasts events to connected clients.
Provides real-time updates for the Live Workspace view.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from ..websocket.manager import WebSocketManager
from ..websocket.events import EventType

logger = logging.getLogger(__name__)


class LANSFileSystemEventHandler(FileSystemEventHandler):
    """Custom file system event handler for LANS ICE"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.loop = None  # Will be set when the watcher starts
        self.ignored_patterns = {
            ".git", "__pycache__", ".pytest_cache", "node_modules",
            ".vscode", ".idea", "*.pyc", "*.pyo", "*.pyd", ".DS_Store"
        }
        super().__init__()
    
    def should_ignore(self, path: str) -> bool:
        """Check if a file should be ignored"""
        path_obj = Path(path)
        
        # Check if any part of the path matches ignored patterns
        for part in path_obj.parts:
            for pattern in self.ignored_patterns:
                if pattern.startswith("*"):
                    # Handle wildcard patterns
                    if part.endswith(pattern[1:]):
                        return True
                elif part == pattern:
                    return True
        
        return False
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events"""
        if event.is_directory or self.should_ignore(event.src_path):
            return
        
        self._schedule_broadcast("modified", event.src_path)
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation events"""
        if self.should_ignore(event.src_path):
            return
        
        self._schedule_broadcast("created", event.src_path)
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion events"""
        if self.should_ignore(event.src_path):
            return
        
        self._schedule_broadcast("deleted", event.src_path)
    
    def on_moved(self, event: FileSystemEvent):
        """Handle file move/rename events"""
        if (self.should_ignore(event.src_path) or 
            (hasattr(event, 'dest_path') and self.should_ignore(event.dest_path))):
            return
        
        dest_path = event.dest_path if hasattr(event, 'dest_path') else None
        self._schedule_broadcast("moved", event.src_path, dest_path)
    
    def _schedule_broadcast(self, change_type: str, src_path: str, dest_path: Optional[str] = None):
        """Schedule a broadcast event safely from file watcher thread"""
        if not self.loop:
            return
            
        try:
            # Use run_coroutine_threadsafe to safely schedule from thread
            asyncio.run_coroutine_threadsafe(
                self._broadcast_file_event(change_type, src_path, dest_path),
                self.loop
            )
        except Exception as e:
            logger.error(f"Error scheduling file change broadcast: {e}")
    
    def on_moved(self, event: FileSystemEvent):
        """Handle file move/rename events"""
        if (self.should_ignore(event.src_path) or 
            (hasattr(event, 'dest_path') and self.should_ignore(event.dest_path))):
            return
        
        asyncio.create_task(self._broadcast_file_move_event(event))
    
    async def _broadcast_file_event(self, change_type: str, src_path: str, dest_path: Optional[str] = None):
        """Broadcast a file system event"""
        try:
            event_data = {
                "type": "file_changed",
                "path": src_path,
                "change_type": change_type,
                "timestamp": self._get_timestamp()
            }
            
            if dest_path:
                event_data["dest_path"] = dest_path
            
            # Get file size for modifications
            if change_type == "modified" and os.path.exists(src_path):
                try:
                    stat = os.stat(src_path)
                    event_data["size"] = stat.st_size
                except (OSError, PermissionError):
                    pass
            
            await self.websocket_manager.broadcast(event_data)
            
        except Exception as e:
            logger.error(f"Error broadcasting file event: {e}")
    
    async def _broadcast_file_move_event(self, event: FileSystemEvent):
        """Broadcast a file move event"""
        try:
            await self.websocket_manager.broadcast({
                "type": EventType.FILE_MOVED,
                "path": event.dest_path if hasattr(event, 'dest_path') else event.src_path,
                "old_path": event.src_path,
                "change_type": "moved",
                "timestamp": self._get_timestamp()
            })
        except Exception as e:
            logger.error(f"Error broadcasting file move event: {e}")
    
    async def _get_file_diff(self, path: str) -> Optional[str]:
        """Get a simple diff representation for a modified file"""
        try:
            # For now, just return file size and last modified time
            stat = os.stat(path)
            return f"Size: {stat.st_size} bytes, Modified: {stat.st_mtime}"
        except (OSError, FileNotFoundError):
            return None
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"


class FileSystemWatcher:
    """File system watcher for monitoring project files"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.observer: Optional[Observer] = None
        self.watched_paths: Set[str] = set()
        self.event_handler = LANSFileSystemEventHandler(websocket_manager)
    
    async def start(self):
        """Start watching the file system"""
        try:
            # Set the event loop for the handler
            self.event_handler.loop = asyncio.get_running_loop()
            
            self.observer = Observer()
            
            # Watch current working directory by default
            current_dir = os.getcwd()
            await self.watch_path(current_dir)
            
            self.observer.start()
            logger.info(f"File system watcher started, watching: {self.watched_paths}")
            
        except Exception as e:
            logger.error(f"Error starting file system watcher: {e}")
    
    async def stop(self):
        """Stop watching the file system"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("File system watcher stopped")
    
    async def watch_path(self, path: str, recursive: bool = True):
        """Add a path to watch"""
        if not os.path.exists(path):
            logger.warning(f"Path does not exist: {path}")
            return
        
        if path in self.watched_paths:
            return
        
        if self.observer:
            self.observer.schedule(
                self.event_handler,
                path,
                recursive=recursive
            )
            self.watched_paths.add(path)
            logger.info(f"Now watching path: {path}")
    
    async def unwatch_path(self, path: str):
        """Remove a path from watching"""
        if path in self.watched_paths:
            # Note: watchdog doesn't provide a direct way to unschedule a specific path
            # For now, we'll just remove it from our tracked paths
            self.watched_paths.discard(path)
            logger.info(f"Stopped watching path: {path}")
    
    def get_watched_paths(self) -> Set[str]:
        """Get currently watched paths"""
        return self.watched_paths.copy()
    
    def is_running(self) -> bool:
        """Check if the watcher is running"""
        return self.observer is not None and self.observer.is_alive()
