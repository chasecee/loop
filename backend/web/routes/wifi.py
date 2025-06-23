"""WiFi management routes for LOOP web server."""

from fastapi import APIRouter, HTTPException

from ..core.models import APIResponse, WiFiCredentials
from boot.wifi import WiFiManager
from config.schema import Config
from utils.logger import get_logger

logger = get_logger("web.wifi")

def create_wifi_router(
    wifi_manager: WiFiManager = None,
    config: Config = None
) -> APIRouter:
    """Create WiFi management router with dependencies."""
    
    router = APIRouter(prefix="/api/wifi", tags=["wifi"])
    
    @router.get("/scan", response_model=APIResponse)
    async def scan_wifi():
        """Scan for available WiFi networks."""
        if not wifi_manager:
            raise HTTPException(status_code=503, detail="WiFi manager not available")
        
        networks = wifi_manager.scan_networks()
        return APIResponse(
            success=True,
            message="Networks scanned",
            data={"networks": networks}
        )
    
    @router.post("/connect", response_model=APIResponse)
    async def connect_wifi(credentials: WiFiCredentials):
        """Connect to WiFi network."""
        if not wifi_manager:
            raise HTTPException(status_code=503, detail="WiFi manager not available")
        
        success = wifi_manager.connect_to_network(credentials.ssid, credentials.password)
        
        if success:
            # Update config
            if config:
                config.wifi.ssid = credentials.ssid
                config.wifi.password = credentials.password
                config.save()
            
            return APIResponse(
                success=True,
                message=f"Connected to {credentials.ssid}"
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to connect to WiFi")
    
    @router.post("/hotspot", response_model=APIResponse)
    async def toggle_hotspot():
        """Toggle WiFi hotspot."""
        if not wifi_manager:
            raise HTTPException(status_code=503, detail="WiFi manager not available")
        
        if wifi_manager.hotspot_active:
            success = wifi_manager.stop_hotspot()
            return APIResponse(
                success=success,
                message="Hotspot stopped" if success else "Failed to stop hotspot",
                data={"hotspot_active": False}
            )
        else:
            if config and not config.wifi.hotspot_enabled:
                raise HTTPException(status_code=403, detail="Hotspot functionality is disabled in the configuration.")
            
            success = wifi_manager.start_hotspot()
            return APIResponse(
                success=success,
                message="Hotspot started" if success else "Failed to start hotspot",
                data={"hotspot_active": success}
            )
    
    return router 