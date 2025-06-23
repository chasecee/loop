"""Dashboard route for LOOP web server."""

import shutil
from pathlib import Path

from fastapi import APIRouter

from ..core.models import DashboardData, DeviceStatus, PlayerStatus, WiFiStatus, UpdateStatus, StorageInfo
from ..core.storage import get_dir_size
from display.player import DisplayPlayer
from boot.wifi import WiFiManager
from deployment.updater import SystemUpdater
from utils.media_index import media_index
from utils.logger import get_logger

logger = get_logger("web.dashboard")

def create_dashboard_router(
    display_player: DisplayPlayer = None,
    wifi_manager: WiFiManager = None,
    updater: SystemUpdater = None
) -> APIRouter:
    """Create dashboard router with dependencies."""
    
    router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
    
    async def get_status():
        """Collect comprehensive system status (internal helper)."""
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

        return device_status
    
    @router.get("", response_model=DashboardData)
    async def get_dashboard():
        """Get consolidated dashboard data in a single request."""
        # System status
        device_status = await get_status()

        # Media / loop / processing data
        dashboard_data = media_index.get_dashboard_data()

        # Storage data - ONLY scan what we need, not entire project!
        total, used, free = shutil.disk_usage("/")

        # Only scan backend directory (not entire project with git/node_modules/etc)
        backend_root = Path(__file__).resolve().parent.parent.parent  # dashboard.py -> routes/ -> web/ -> backend/
        media_path = backend_root / "media"
        media_size = get_dir_size(media_path)

        # Only scan backend app files (exclude media)
        backend_size = get_dir_size(backend_root)
        app_size = max(0, backend_size - media_size)
        system_size = max(0, used - backend_size)

        storage_payload = StorageInfo(
            total=total,
            used=used,
            free=free,
            system=system_size,
            app=app_size,
            media=media_size,
        )

        return DashboardData(
            status=device_status,
            media=dashboard_data["media"],
            active=dashboard_data["active"],
            loop=dashboard_data["loop"],
            last_updated=dashboard_data["last_updated"],
            processing=dashboard_data["processing"],
            storage=storage_payload,
        )
    
    return router 