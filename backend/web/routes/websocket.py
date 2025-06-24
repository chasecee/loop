"""WebSocket routes for LOOP web server."""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..core.websocket import manager
from ..core.models import APIResponse, DashboardData, DeviceStatus, PlayerStatus, WiFiStatus, UpdateStatus
from utils.logger import get_logger
from utils.media_index import media_index
from display.player import DisplayPlayer
from boot.wifi import WiFiManager
from deployment.updater import SystemUpdater

logger = get_logger("web.websocket")

def create_websocket_router(
    display_player: DisplayPlayer = None,
    wifi_manager: WiFiManager = None,
    updater: SystemUpdater = None
) -> APIRouter:
    """Create WebSocket router with dependencies."""
    
    router = APIRouter(tags=["websocket"])
    
    async def get_complete_dashboard_data():
        """Get complete dashboard data including device status (same as dashboard route)."""
        # System status
        device_status = DeviceStatus()

        if display_player:
            try:
                player_data = display_player.get_status()
                device_status.player = PlayerStatus(**player_data)
            except Exception:
                pass

        if wifi_manager:
            try:
                wifi_data = wifi_manager.get_status()
                device_status.wifi = WiFiStatus(**wifi_data)
            except Exception:
                pass

        if updater:
            try:
                update_data = updater.get_update_status()
                device_status.updates = UpdateStatus(**update_data)
            except Exception:
                pass

        # Media / loop / processing data
        media_data = media_index.get_dashboard_data()

        # Build complete dashboard data (same structure as dashboard route)
        return {
            "status": device_status.dict(),
            "media": media_data["media"],
            "active": media_data["active"],
            "loop": media_data["loop"],
            "last_updated": media_data["last_updated"],
            "processing": media_data["processing"],
        }
    
    @router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """Main WebSocket endpoint for real-time updates."""
        conn_id = None
        
        try:
            # Accept connection (manager logs this)
            conn_id = await manager.connect(websocket)
            
            # Send complete initial dashboard data (including status)
            try:
                dashboard_data = await get_complete_dashboard_data()
                logger.debug(f"📡 Sending initial dashboard data: {len(dashboard_data['media'])} media items")
                await manager._send_to_connection(conn_id, {
                    "type": "initial_dashboard",
                    "data": dashboard_data
                })
                logger.debug(f"✅ Initial dashboard data sent successfully to {conn_id}")
            except Exception as e:
                logger.error(f"❌ Failed to send initial dashboard data to {conn_id}: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
            
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
            # Manager logs disconnection
            pass
            
        except Exception as e:
            # Suppress noisy disconnect errors (1000/1001 are normal closes)
            if isinstance(e, WebSocketDisconnect):
                pass
            else:
                logger.error(f"🔌 WebSocket error for {conn_id}: {e}")
            
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