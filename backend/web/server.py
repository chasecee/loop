"""Hardened FastAPI web server for LOOP - No WebSockets, simple polling."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from config.schema import Config
from display.player import DisplayPlayer
from boot.wifi import WiFiManager
from deployment.updater import SystemUpdater

from .core.middleware import (
    CacheControlMiddleware,
    RequestLoggingMiddleware, 
    ConcurrencyLimitMiddleware,
    ErrorHandlingMiddleware
)
from .core.storage import scan_storage_on_startup
from .routes import register_routers
from utils.logger import get_logger

logger = get_logger("web")

def create_app(
    display_player: DisplayPlayer = None,
    wifi_manager: WiFiManager = None, 
    updater: SystemUpdater = None,
    config: Config = None
) -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Scan storage once on startup for fast dashboard responses
    scan_storage_on_startup()
    
    app = FastAPI(
        title="LOOP",
        description="Little Optical Output Pal - Rock solid Pi deployment",
        version="1.0.0",
        docs_url="/docs" if config and config.web.debug else None,
        redoc_url="/redoc" if config and config.web.debug else None
    )
    
    # Simple middleware stack - no WebSocket complexity
    app.add_middleware(CacheControlMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ConcurrencyLimitMiddleware, max_concurrent=config.web.max_concurrent_requests if config else 8)
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Lightweight compression for JSON responses only
    from .core.middleware import ConditionalGZipMiddleware
    app.add_middleware(ConditionalGZipMiddleware, minimum_size=1000)
    
    # CORS middleware (outermost)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Simplify for Pi deployment
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],  # Explicit methods only
        allow_headers=["*"],
        max_age=3600,
    )
    
    # Determine paths
    backend_root = Path(__file__).resolve().parent.parent
    media_raw_dir = backend_root / "media" / "raw"
    media_processed_dir = backend_root / "media" / "processed"
    
    # SPA assets directory
    spa_dir = Path(__file__).parent / "spa"
    
    # Mount static file routes with aggressive caching
    if (spa_dir / "_next").exists():
        app.mount("/_next", StaticFiles(directory=spa_dir / "_next"), name="next-static")
    if spa_dir.exists():
        app.mount("/assets", StaticFiles(directory=spa_dir), name="spa-assets")
    
    # Media directories
    media_raw_dir.mkdir(parents=True, exist_ok=True)
    media_processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Serve media files
    app.mount("/media/raw", StaticFiles(directory=media_raw_dir), name="raw-media")
    app.mount("/media/processed", StaticFiles(directory=media_processed_dir), name="processed-media")
    
    # Root SPA route
    @app.get("/", response_class=HTMLResponse)
    async def root_spa():
        """Serve the SPA index page."""
        spa_index = spa_dir / "index.html"
        if spa_index.exists():
            return FileResponse(spa_index)
        else:
            return """
            <html>
                <head><title>LOOP - Backend Ready</title></head>
                <body>
                    <h1>LOOP Backend Running</h1>
                    <p>Rock solid Pi deployment ready.</p>
                    <p><a href="/docs">View API Documentation</a></p>
                </body>
            </html>
            """
    
    # Favicon to prevent 404 spam
    @app.get("/favicon.ico")
    async def favicon():
        """Return empty response for favicon."""
        from fastapi import Response
        return Response(status_code=204)
    
    # Register all API routes (no WebSocket routes)
    register_routers(app, display_player, wifi_manager, updater, config)
    
    logger.info("Hardened FastAPI application created (WebSocket-free)")
    return app


# For development/testing
if __name__ == "__main__":
    import uvicorn
    from config.schema import get_config
    
    config = get_config()
    app = create_app(config=config)

    uvicorn.run(
        app,
        host=config.web.host,
        port=config.web.port,
        log_level="info",
        limit_max_requests=None,
    ) 