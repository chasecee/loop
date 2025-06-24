"""WebSocket routes for LOOP web server."""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..core.websocket import manager
from ..core.models import APIResponse
from utils.logger import get_logger
from utils.media_index import media_index

logger = get_logger("web.websocket")

def create_websocket_router() -> APIRouter:
    """Create WebSocket router."""
    
    router = APIRouter(tags=["websocket"])
    
    @router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """Main WebSocket endpoint for real-time updates."""
        conn_id = None
        
        try:
            # Accept connection
            conn_id = await manager.connect(websocket)
            
            # Send initial dashboard data
            try:
                dashboard_data = media_index.get_dashboard_data()
                await manager._send_to_connection(conn_id, {
                    "type": "initial_dashboard",
                    "data": dashboard_data
                })
            except Exception as e:
                logger.warning(f"Failed to send initial dashboard data: {e}")
            
            # Message handling loop
            while True:
                try:
                    # Receive message from client
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Handle the message
                    await manager.handle_message(conn_id, message)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON from {conn_id}: {e}")
                    await manager._send_to_connection(conn_id, {
                        "type": "error",
                        "message": "Invalid JSON format"
                    })
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket client disconnected: {conn_id}")
            
        except Exception as e:
            logger.error(f"WebSocket error for {conn_id}: {e}")
            
        finally:
            if conn_id:
                manager.disconnect(conn_id)
    
    @router.get("/api/websocket/status", response_model=APIResponse)
    async def websocket_status():
        """Get WebSocket connection status and diagnostics."""
        stats = manager.get_stats()
        return APIResponse(
            success=True,
            data={
                "connections": stats,
                "detailed_rooms": {
                    room: list(connections) for room, connections in manager.rooms.items()
                }
            }
        )
    
    return router 