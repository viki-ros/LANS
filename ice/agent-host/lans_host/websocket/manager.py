"""
WebSocket Connection Manager for LANS ICE

Manages WebSocket connections and message broadcasting
for real-time communication with the desktop application.
"""

import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_metadata: Dict[WebSocket, dict] = {}
        self.terminal_output_listeners = []  # For real-time terminal analysis
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_metadata[websocket] = {
            "connected_at": self._get_timestamp(),
            "client_info": self._get_client_info(websocket)
        }
        logger.info(f"WebSocket connected: {len(self.active_connections)} active connections")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        self.active_connections.discard(websocket)
        self.connection_metadata.pop(websocket, None)
        logger.info(f"WebSocket disconnected: {len(self.active_connections)} active connections")
    
    async def send_to_websocket(self, websocket: WebSocket, data: dict):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_json(data)
        except WebSocketDisconnect:
            logger.warning("Attempted to send to disconnected WebSocket")
            self.disconnect(websocket)
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
    
    async def broadcast(self, data: dict):
        """Broadcast a message to all connected WebSocket clients"""
        if not self.active_connections:
            return
        
        # Notify terminal output listeners for real-time analysis
        if data.get("type") == "terminal_output":
            for listener in self.terminal_output_listeners:
                try:
                    await listener(data)
                except Exception as e:
                    logger.error(f"Error in terminal output listener: {e}")
        
        # Broadcast to all connections
        disconnected_connections = []
        
        for websocket in self.active_connections:
            try:
                await websocket.send_json(data)
            except WebSocketDisconnect:
                disconnected_connections.append(websocket)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected_connections.append(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected_connections:
            self.disconnect(websocket)

    def add_terminal_output_listener(self, listener_func):
        """Add a listener for terminal output events"""
        self.terminal_output_listeners.append(listener_func)
        logger.info("Terminal output listener added for real-time analysis")

    def remove_terminal_output_listener(self, listener_func):
        """Remove a terminal output listener"""
        if listener_func in self.terminal_output_listeners:
            self.terminal_output_listeners.remove(listener_func)
            logger.info("Terminal output listener removed")

    async def broadcast_event(self, event_type: str, **kwargs):
        """Broadcast an event with the standard event structure"""
        event_data = {
            "type": event_type,
            "timestamp": self._get_timestamp(),
            **kwargs
        }
        await self.broadcast(event_data)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[dict]:
        """Get information about all active connections"""
        return [
            {
                "client_info": metadata.get("client_info", {}),
                "connected_at": metadata.get("connected_at"),
                "connection_id": id(websocket)
            }
            for websocket, metadata in self.connection_metadata.items()
        ]
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
    
    @staticmethod
    def _get_client_info(websocket: WebSocket) -> dict:
        """Extract client information from WebSocket"""
        return {
            "client": websocket.client.host if websocket.client else "unknown",
            "user_agent": websocket.headers.get("user-agent", "unknown")
        }
