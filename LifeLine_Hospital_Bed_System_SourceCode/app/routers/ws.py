import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket_manager import ws_manager

logger = logging.getLogger("lifeline.ws")
router = APIRouter(tags=["Real-Time WebSockets"])

@router.websocket("/ws/beds")
async def websocket_bed_updates(websocket: WebSocket):
    """
    Real-time bi-directional WebSocket connection for instant bed updates.
    Broadcasts every hospital bed change across all patient and staff clients.
    """
    await ws_manager.connect(websocket)
    try:
        # Send initial connection handshake
        await ws_manager.send_personal_message(
            {
                "event": "CONNECTED",
                "message": "Connected to LifeLine Real-Time Hospital Bed WebSocket",
                "status": "LIVE_SYNC"
            },
            websocket
        )
        
        while True:
            # Keep connection open, handle client heartbeats/pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"event":"pong"}')
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket client error: {e}")
        ws_manager.disconnect(websocket)
