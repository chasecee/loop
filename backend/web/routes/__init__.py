"""Route registration for LOOP web server."""

from pathlib import Path

from .dashboard import create_dashboard_router
from .loop import create_loop_router
from .media import create_media_router
from .playback import create_playback_router, create_display_router
from .updates import create_updates_router
from .wifi import create_wifi_router

def register_routers(app, display_player=None, wifi_manager=None, updater=None, config=None):
    """Register all routers with the FastAPI app."""
    
    # Media directories
    media_raw_dir = Path("media/raw")
    media_processed_dir = Path("media/processed")
    media_raw_dir.mkdir(parents=True, exist_ok=True)
    media_processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Create and register all routers
    app.include_router(create_dashboard_router(display_player, wifi_manager, updater))
    app.include_router(create_media_router(display_player, media_raw_dir, media_processed_dir))
    app.include_router(create_loop_router(display_player))
    app.include_router(create_playback_router(display_player, config))
    app.include_router(create_display_router(display_player, config))
    app.include_router(create_wifi_router(wifi_manager, config))
    app.include_router(create_updates_router(updater)) 