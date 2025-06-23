"""System update routes for LOOP web server."""

from fastapi import APIRouter, HTTPException

from ..core.models import APIResponse
from deployment.updater import SystemUpdater
from utils.logger import get_logger

logger = get_logger("web.updates")

def create_updates_router(updater: SystemUpdater = None) -> APIRouter:
    """Create system update router with dependencies."""
    
    router = APIRouter(prefix="/api/updates", tags=["updates"])
    
    @router.get("/check", response_model=APIResponse)
    async def check_updates():
        """Check for available updates."""
        if not updater:
            raise HTTPException(status_code=503, detail="Updater not available")
        
        update_sources = updater.check_all_sources()
        return APIResponse(
            success=True,
            message="Updates checked",
            data={"updates_available": update_sources}
        )
    
    @router.post("/install", response_model=APIResponse)
    async def install_updates():
        """Install available updates."""
        if not updater:
            raise HTTPException(status_code=503, detail="Updater not available")
        
        success, message = updater.auto_update()
        return APIResponse(success=success, message=message)
    
    return router 