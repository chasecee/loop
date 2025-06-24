"""Event broadcasting system for real-time LOOP updates."""

import asyncio
import time
from typing import Dict, Any, Optional
from .websocket import manager
from utils.logger import get_logger

logger = get_logger("events")

class EventBroadcaster:
    """Handles event broadcasting to WebSocket clients."""
    
    def __init__(self):
        self.last_dashboard_update = 0
        self.dashboard_throttle = 0.1  # Throttle dashboard updates to 100ms
    
    async def dashboard_updated(self, data: dict):
        """Broadcast dashboard data update."""
        current_time = time.time()
        
        # Throttle dashboard updates to prevent spam
        if current_time - self.last_dashboard_update < self.dashboard_throttle:
            return
            
        self.last_dashboard_update = current_time
        
        await manager.broadcast_to_room("dashboard", {
            "type": "dashboard_update",
            "data": data
        })
        
        logger.debug("Dashboard update broadcasted")
    
    async def media_uploaded(self, media_data: dict):
        """Broadcast new media upload."""
        await manager.broadcast_to_room("dashboard", {
            "type": "media_uploaded",
            "data": media_data
        })
        
        logger.info(f"Media upload broadcasted: {media_data.get('filename', 'unknown')}")
    
    async def media_deleted(self, slug: str):
        """Broadcast media deletion."""
        await manager.broadcast_to_room("dashboard", {
            "type": "media_deleted", 
            "data": {"slug": slug}
        })
        
        logger.info(f"Media deletion broadcasted: {slug}")
    
    async def loop_updated(self, loop_data: list):
        """Broadcast loop queue update."""
        await manager.broadcast_to_room("dashboard", {
            "type": "loop_updated",
            "data": {"loop": loop_data}
        })
        
        logger.debug("Loop update broadcasted")
    
    async def playback_changed(self, player_status: dict):
        """Broadcast playback state change."""
        await manager.broadcast_to_room("dashboard", {
            "type": "playback_changed",
            "data": {"player": player_status}
        })
        
        logger.debug("Playback change broadcasted")
    
    async def processing_progress(self, job_id: str, progress_data: dict):
        """Broadcast processing progress update."""
        try:
            message = {
                "type": "processing_progress",
                "data": {
                    "job_id": job_id,
                    **progress_data
                }
            }
            
            await manager.broadcast_to_room("progress", message)
            logger.info(f"📡 Progress broadcast sent: {job_id[:8]} -> {progress_data.get('progress', 0)}% to progress room")
            
        except Exception as e:
            logger.error(f"Failed to broadcast progress for {job_id}: {e}")
            raise
    
    async def wifi_status_changed(self, wifi_data: dict):
        """Broadcast WiFi status change."""
        await manager.broadcast_to_room("wifi", {
            "type": "wifi_status_changed",
            "data": wifi_data
        })
        
        logger.debug("WiFi status change broadcasted")
    
    async def system_status_changed(self, system_data: dict):
        """Broadcast system status change."""
        await manager.broadcast_to_room("system", {
            "type": "system_status_changed",
            "data": system_data
        })
        
        logger.debug("System status change broadcasted")
    
    async def error_occurred(self, error_data: dict):
        """Broadcast error to all clients."""
        await manager.broadcast_to_all({
            "type": "error",
            "data": error_data
        })
        
        logger.warning(f"Error broadcasted: {error_data.get('message', 'Unknown error')}")

# Global event broadcaster instance
broadcaster = EventBroadcaster() 