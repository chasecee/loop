"""Playback control routes for LOOP web server."""

from fastapi import APIRouter, HTTPException

from ..core.models import APIResponse, DisplaySettingsPayload
from ..core.events import broadcaster
from display.player import DisplayPlayer
from config.schema import Config
from utils.logger import get_logger
from .dashboard import invalidate_dashboard_cache

logger = get_logger("web.playback")

def create_playback_router(
    display_player: DisplayPlayer = None,
    config: Config = None
) -> APIRouter:
    """Create playback control router with dependencies."""
    
    router = APIRouter(prefix="/api/playback", tags=["playback"])
    
    @router.post("/toggle", response_model=APIResponse)
    async def toggle_playback():
        """Toggle playback pause/resume."""
        if not display_player:
            raise HTTPException(status_code=503, detail="Display player not available")
        
        display_player.toggle_pause()
        is_paused = display_player.is_paused()
        
        # Broadcast playback state change via WebSocket
        try:
            import asyncio
            player_status = display_player.get_status()
            asyncio.create_task(broadcaster.playback_changed(player_status))
        except Exception as e:
            logger.debug(f"WebSocket broadcast failed: {e}")
        
        return APIResponse(
            success=True,
            message="Paused" if is_paused else "Resumed",
            data={"paused": is_paused}
        )
    
    @router.post("/next", response_model=APIResponse)
    async def next_media():
        """Switch to next media."""
        if not display_player:
            raise HTTPException(status_code=503, detail="Display player not available")
        
        display_player.next_media()
        invalidate_dashboard_cache()
        
        # Broadcast playback state change via WebSocket
        try:
            import asyncio
            player_status = display_player.get_status()
            asyncio.create_task(broadcaster.playback_changed(player_status))
        except Exception as e:
            logger.debug(f"WebSocket broadcast failed: {e}")
        
        return APIResponse(success=True, message="Switched to next media")
    
    @router.post("/previous", response_model=APIResponse)
    async def previous_media():
        """Switch to previous media."""
        if not display_player:
            raise HTTPException(status_code=503, detail="Display player not available")
        
        display_player.previous_media()
        invalidate_dashboard_cache()
        
        # Broadcast playback state change via WebSocket
        try:
            import asyncio
            player_status = display_player.get_status()
            asyncio.create_task(broadcaster.playback_changed(player_status))
        except Exception as e:
            logger.debug(f"WebSocket broadcast failed: {e}")
        
        return APIResponse(success=True, message="Switched to previous media")
    
    @router.post("/loop-mode", response_model=APIResponse)
    async def toggle_loop_mode():
        """Toggle loop mode between 'all' and 'one'."""
        if not display_player:
            raise HTTPException(status_code=503, detail="Display player not available")
        
        new_mode = display_player.toggle_loop_mode()
        return APIResponse(
            success=True, 
            message=f"Loop mode set to: {new_mode}",
            data={"loop_mode": new_mode}
        )
    
    return router

def create_display_router(
    display_player: DisplayPlayer = None,
    config: Config = None
) -> APIRouter:
    """Create display settings router with dependencies."""
    
    router = APIRouter(prefix="/api/display", tags=["display"])
    
    @router.post("/brightness", response_model=APIResponse)
    async def set_display_settings(payload: DisplaySettingsPayload):
        """Set LCD backlight brightness (0-100)."""
        if not display_player:
            raise HTTPException(status_code=503, detail="Display driver not available")
        response_data = {}
        try:
            if payload.brightness is not None:
                level = max(0, min(100, payload.brightness))
                display_player.display_driver.set_backlight(level)
                response_data["brightness"] = level
                if config:
                    config.display.brightness = level
            if config and response_data:
                config.save()
            return APIResponse(success=True, message="Display settings updated", data=response_data)
        except Exception as e:
            logger.error(f"Failed to set brightness: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/brightness", response_model=APIResponse)
    async def get_display_settings():
        """Get current LCD backlight brightness."""
        try:
            level = config.display.brightness if config and config.display else 100
            return APIResponse(success=True, data={"brightness": level})
        except Exception as e:
            logger.error(f"Failed to get brightness: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return router 