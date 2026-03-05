import json
import logging
from typing import Dict, List, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSockets"])

class ConnectionManager:
    def __init__(self):
        # We store connections for the global IPO channel
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        failed_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to a websocket: {e}")
                failed_connections.append(connection)
                
        # Clean up dead connections
        for dead_conn in failed_connections:
            self.disconnect(dead_conn)

manager = ConnectionManager()


@router.websocket("/ipos")
async def websocket_ipo_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for frontend clients to subscribe to real-time IPO updates.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive, we primarily just push data FROM server
            data = await websocket.receive_text()
            # We could handle specific client subscriptions here if needed
            # e.g., if data == "ping", await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.post("/internal-broadcast")
async def internal_broadcast(request: Request):
    """
    Internal endpoint called by the `real_time_updater.py` background process
    to trigger a WebSocket payload to all connected frontends.
    """
    try:
        payload = await request.json()
        await manager.broadcast(json.dumps(payload))
        return {"success": True, "broadcasted": True}
    except Exception as e:
        logger.error(f"Broadcast webhook failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
