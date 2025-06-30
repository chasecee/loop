"""Loop management routes for LOOP web server."""

from fastapi import APIRouter, HTTPException

from ..core.models import APIResponse, AddToLoopPayload, LoopOrderPayload
from display.hardened_player import HardenedDisplayPlayer as DisplayPlayer
from utils.media_index import media_index
from utils.logger import get_logger
from .dashboard import invalidate_dashboard_cache

logger = get_logger("web.loop")

def create_loop_router(display_player: DisplayPlayer = None) -> APIRouter:
    """Create loop management router with dependencies."""
    
    router = APIRouter(prefix="/api/loop", tags=["loop"])
    
    @router.get("", response_model=APIResponse)
    async def get_loop_queue():
        """Get the current loop queue."""
        return APIResponse(
            success=True,
            data={"loop": media_index.list_loop()}
        )
    
    @router.post("", response_model=APIResponse)
    async def add_to_loop(payload: AddToLoopPayload):
        """Add a media item to the loop queue."""
        try:
            media_index.add_to_loop(payload.slug)
            if display_player:
                display_player.refresh_media_list()
            invalidate_dashboard_cache()
            
            return APIResponse(
                success=True,
                message="Added to loop",
                data={"loop": media_index.list_loop()}
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="Media not found")
    
    @router.put("", response_model=APIResponse)
    async def reorder_loop(payload: LoopOrderPayload):
        """Reorder the loop queue."""
        media_index.reorder_loop(payload.loop)
        if display_player:
            display_player.refresh_media_list()
        invalidate_dashboard_cache()
        
        return APIResponse(
            success=True,
            message="Loop reordered",
            data={"loop": media_index.list_loop()}
        )
    
    @router.delete("/{slug}", response_model=APIResponse)
    async def remove_from_loop(slug: str):
        """Remove a media item from the loop queue."""
        media_index.remove_from_loop(slug)
        if display_player:
            display_player.refresh_media_list()
        invalidate_dashboard_cache()
        return APIResponse(
            success=True,
            message="Removed from loop",
            data={"loop": media_index.list_loop()}
        )
    
    return router 