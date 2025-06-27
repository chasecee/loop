"""Refactored FastAPI web server for LOOP."""

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
    
    # Scan storage once on startup for lightning-fast dashboard responses
    scan_storage_on_startup()
    
    app = FastAPI(
        title="LOOP",
        description="Little Optical Output Pal - Your pocket-sized animation companion!",
        version="1.0.0",
        docs_url="/docs" if config and config.web.debug else None,
        redoc_url="/redoc" if config and config.web.debug else None
    )
    
    # Configure request limits for large file uploads
    app.router.default_response_class.media_type = "application/json"
    
    # Add middleware in correct order (innermost to outermost)
    app.add_middleware(CacheControlMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    # New: stream upload progress to clients
    from .core.middleware import UploadProgressMiddleware
    app.add_middleware(UploadProgressMiddleware)
    app.add_middleware(ConcurrencyLimitMiddleware, max_concurrent=config.web.max_concurrent_requests if config else 16)
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Gzip compression for JSON/text responses (5-10x smaller transfers!)
    # Exclude file uploads - only compress outgoing responses
    from .core.middleware import ConditionalGZipMiddleware
    app.add_middleware(ConditionalGZipMiddleware, minimum_size=1000)
    
    # CORS middleware (outermost)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify exact origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )
    
    # Determine paths
    backend_root = Path(__file__).resolve().parent.parent
    media_raw_dir = backend_root / "media" / "raw"
    media_processed_dir = backend_root / "media" / "processed"
    
    # SPA assets directory (deployed via deploy-frontend.sh)
    spa_dir = Path(__file__).parent / "spa"
    
    # Mount static file routes with optimized caching
    if (spa_dir / "_next").exists():
        app.mount("/_next", StaticFiles(directory=spa_dir / "_next"), name="next-static")
    if spa_dir.exists():
        app.mount("/assets", StaticFiles(directory=spa_dir), name="spa-assets")
    
    # Media directories
    media_raw_dir.mkdir(parents=True, exist_ok=True)
    media_processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Serve raw media files for frontend previews
    app.mount("/media/raw", StaticFiles(directory=media_raw_dir), name="raw-media")
    
    # Serve processed media files for frontend display
    app.mount("/media/processed", StaticFiles(directory=media_processed_dir), name="processed-media")
    
    # Root SPA route
    @app.get("/", response_class=HTMLResponse)
    async def root_spa():
        """Serve the SPA index page."""
        spa_index = spa_dir / "index.html"
        if spa_index.exists():
            return FileResponse(spa_index)
        else:
            # Fallback if frontend not deployed yet
            return """
            <html>
                <head><title>LOOP - Deploy Required</title></head>
                <body>
                    <h1>LOOP Backend Running</h1>
                    <p>Frontend not deployed yet. Run deployment script:</p>
                    <code>./deploy-frontend.sh</code>
                    <p><a href="/docs">View API Documentation</a></p>
                </body>
            </html>
            """
    
    # Favicon route to prevent 404 spam
    @app.get("/favicon.ico")
    async def favicon():
        """Serve favicon if available, otherwise return 204."""
        favicon_path = spa_dir / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(favicon_path)
        # Return empty response if no favicon found
        from fastapi import Response
        return Response(status_code=204)
    
    # Register all API routes
    register_routers(app, display_player, wifi_manager, updater, config)
    
    logger.info("FastAPI application created successfully")
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