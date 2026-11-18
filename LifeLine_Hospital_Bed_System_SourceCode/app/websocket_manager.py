import json
import logging
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger("lifeline.ws")

class ConnectionManager:
    """Central manager handling WebSocket connections for live real-time bed updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcasts real-time events to all connected patient and staff browsers."""
        payload = json.dumps(message)
        dead_connections = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.warning(f"Error broadcasting to client, marking for removal: {e}")
                dead_connections.append(connection)

        # Cleanup disconnected clients
        for dead in dead_connections:
            self.disconnect(dead)

# Global singleton instance
ws_manager = ConnectionManager()
