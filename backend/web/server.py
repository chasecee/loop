"""FastAPI web server for LOOP."""

import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config.schema import Config
from display.player import DisplayPlayer
from boot.wifi import WiFiManager
from deployment.updater import SystemUpdater
from utils.convert import MediaConverter
from utils.media_index import media_index
from utils.logger import get_logger

logger = get_logger("web")

# Pydantic models for request/response validation
class WiFiCredentials(BaseModel):
    ssid: str
    password: Optional[str] = ""

class AddToLoopPayload(BaseModel):
    slug: str

class LoopOrderPayload(BaseModel):
    loop: List[str]

class MediaItem(BaseModel):
    slug: str
    filename: str
    type: str
    size: int
    uploadedAt: str
    url: Optional[str] = None
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    frame_count: Optional[int] = None

class DeviceStatus(BaseModel):
    """Device status matching frontend expectations."""
    system: str = "LOOP v1.0.0"
    status: str = "running"
    timestamp: int = Field(default_factory=lambda: int(time.time()))
    player: Optional[Dict[str, Any]] = None
    wifi: Optional[Dict[str, Any]] = None
    updates: Optional[Dict[str, Any]] = None

class DashboardData(BaseModel):
    """Combined dashboard data."""
    status: DeviceStatus
    media: List[Dict[str, Any]]
    active: Optional[str]
    loop: List[str]
    last_updated: Optional[int]

class APIResponse(BaseModel):
    """Standard API response format."""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    errors: Optional[List[Dict[str, str]]] = None

def get_dir_size(path: Path) -> int:
    """Recursively get the size of a directory."""
    total = 0
    if path.exists():
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(Path(entry.path))
    return total

def create_app(
    display_player: DisplayPlayer = None,
    wifi_manager: WiFiManager = None, 
    updater: SystemUpdater = None,
    config: Config = None
) -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="LOOP",
        description="Little Optical Output Pal - Your pocket-sized animation companion!",
        version="1.0.0",
        docs_url="/docs" if config and config.web.debug else None,
        redoc_url="/redoc" if config and config.web.debug else None
    )
    
    # SPA assets directory (Next.js export)
    spa_dir = Path(__file__).parent / "spa"
    if (spa_dir / "_next").exists():
        app.mount("/_next", StaticFiles(directory=spa_dir / "_next"), name="next-static")
    if spa_dir.exists():
        app.mount("/assets", StaticFiles(directory=spa_dir), name="spa-assets")
    
    # Media directories
    media_raw_dir = Path("media/raw")
    media_processed_dir = Path("media/processed")
    media_raw_dir.mkdir(parents=True, exist_ok=True)
    media_processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Serve raw media files for frontend previews
    app.mount("/media/raw", StaticFiles(directory=media_raw_dir), name="raw-media")
    
    # Media converter
    converter = MediaConverter(
        config.display.width if config else 240,
        config.display.height if config else 320
    )
    
    # Exception handlers
    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"success": False, "message": str(exc)}
        )
    
    @app.exception_handler(KeyError)
    async def key_error_handler(request, exc):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"success": False, "message": f"Resource not found: {exc}"}
        )
    
    # Routes
    
    @app.get("/", response_class=HTMLResponse)
    async def root_spa():
        """Serve the SPA index page."""
        spa_index = spa_dir / "index.html"
        if spa_index.exists():
            return FileResponse(spa_index)
        raise HTTPException(status_code=404, detail="SPA not built/deployed")
    
    # System Status API
    
    @app.get("/api/status", response_model=DeviceStatus)
    async def get_status():
        """Get comprehensive system status."""
        device_status = DeviceStatus()
        
        if display_player:
            player_status = display_player.get_status()
            device_status.player = player_status
        
        if wifi_manager:
            wifi_status = wifi_manager.get_status()
            device_status.wifi = wifi_status
        
        if updater:
            update_status = updater.get_update_status()
            device_status.updates = update_status
        
        return device_status
    
    # Media Management API
    
    @app.get("/api/media", response_model=APIResponse)
    async def get_media():
        """Get all media items."""
        try:
            media_list = media_index.list_media()
            return APIResponse(
                success=True,
                data={
                    "media": media_list,
                    "active": media_index.get_active(),
                    "last_updated": int(time.time())
                }
            )
        except Exception as e:
            logger.error(f"Failed to get media: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/media", response_model=APIResponse)
    async def upload_media(files: List[UploadFile] = File(...)):
        """Upload and process media files."""
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        processed_files = []
        errors = []
        
        # Pause playback during processing
        playback_was_running = False
        if display_player and not display_player.is_paused():
            playback_was_running = True
            try:
                display_player.toggle_pause()
                display_player.show_message("Processing media…", duration=0)
            except Exception as exc:
                logger.warning(f"Failed to display processing splash: {exc}")
        
        try:
            for file in files:
                try:
                    metadata = await process_media_file(file, converter, config)
                    processed_files.append(metadata)
                except Exception as e:
                    logger.error(f"Upload failed for {file.filename}: {e}")
                    error_detail = e.detail if isinstance(e, HTTPException) else str(e)
                    errors.append({"filename": file.filename, "error": error_detail})
        finally:
            # Always refresh player and resume if needed
            if display_player:
                try:
                    display_player.refresh_media_list()
                    
                    # If we successfully processed files, activate the last one uploaded
                    if processed_files:
                        last_uploaded_slug = processed_files[-1].get('slug')
                        if last_uploaded_slug:
                            display_player.set_active_media(last_uploaded_slug)
                            logger.info(f"Activated newly uploaded media: {last_uploaded_slug}")
                    
                    if playback_was_running:
                        display_player.show_message("Processing complete!", duration=2.0)
                        display_player.toggle_pause()  # Resume
                except Exception as exc:
                    logger.error(f"Failed to refresh/activate player: {exc}")
        
        if not processed_files and errors:
            raise HTTPException(status_code=500, detail={"errors": errors})
        
        return APIResponse(
            success=True,
            message=f"Processed {len(processed_files)} files",
            data={"processed_files": processed_files},
            errors=errors if errors else None
        )
    
    @app.post("/api/media/{slug}/activate", response_model=APIResponse)
    async def activate_media(slug: str):
        """Set a media item as active."""
        if not display_player:
            raise HTTPException(status_code=503, detail="Display player not available")
        
        try:
            media_index.add_to_loop(slug)  # Ensure in loop
            media_index.set_active(slug)
            display_player.set_active_media(slug)
            return APIResponse(success=True, message=f"Activated media: {slug}")
        except KeyError:
            raise HTTPException(status_code=404, detail="Media not found")
    
    @app.delete("/api/media/{slug}", response_model=APIResponse)
    async def delete_media(slug: str):
        """Delete a media item."""
        try:
            # Update media index first
            media_index.remove_media(slug)
            
            # Remove from filesystem
            media_dir = media_processed_dir / slug
            raw_files = list(media_raw_dir.glob(f"*{slug}*"))
            
            if media_dir.exists():
                shutil.rmtree(media_dir)
                logger.info(f"Removed processed directory: {media_dir}")
            
            for raw_file in raw_files:
                raw_file.unlink()
                logger.info(f"Removed raw file: {raw_file}")
            
            # Refresh player
            if display_player:
                display_player.refresh_media_list()
            
            return APIResponse(success=True, message=f"Deleted media: {slug}")
            
        except Exception as e:
            logger.error(f"Failed to delete media {slug}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/media/cleanup", response_model=APIResponse)
    async def cleanup_orphaned_media():
        """Clean up orphaned media files."""
        try:
            cleanup_count = media_index.cleanup_orphaned_files(media_raw_dir, media_processed_dir)
            
            if display_player:
                display_player.refresh_media_list()
            
            return APIResponse(
                success=True,
                message=f"Cleaned up {cleanup_count} orphaned files"
            )
        except Exception as e:
            logger.error(f"Failed to cleanup media: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Loop Management API
    
    @app.get("/api/loop", response_model=APIResponse)
    async def get_loop_queue():
        """Get the current loop queue."""
        return APIResponse(
            success=True,
            data={"loop": media_index.list_loop()}
        )
    
    @app.post("/api/loop", response_model=APIResponse)
    async def add_to_loop(payload: AddToLoopPayload):
        """Add a media item to the loop queue."""
        try:
            media_index.add_to_loop(payload.slug)
            if display_player:
                display_player.refresh_media_list()
            return APIResponse(
                success=True,
                message="Added to loop",
                data={"loop": media_index.list_loop()}
            )
        except KeyError:
            raise HTTPException(status_code=404, detail="Media not found")
    
    @app.put("/api/loop", response_model=APIResponse)
    async def reorder_loop(payload: LoopOrderPayload):
        """Reorder the loop queue."""
        media_index.reorder_loop(payload.loop)
        if display_player:
            display_player.refresh_media_list()
        return APIResponse(
            success=True,
            message="Loop reordered",
            data={"loop": media_index.list_loop()}
        )
    
    @app.delete("/api/loop/{slug}", response_model=APIResponse)
    async def remove_from_loop(slug: str):
        """Remove a media item from the loop queue."""
        media_index.remove_from_loop(slug)
        if display_player:
            display_player.refresh_media_list()
        return APIResponse(
            success=True,
            message="Removed from loop",
            data={"loop": media_index.list_loop()}
        )
    
    # Playback Control API
    
    @app.post("/api/playback/toggle", response_model=APIResponse)
    async def toggle_playback():
        """Toggle playback pause/resume."""
        if not display_player:
            raise HTTPException(status_code=503, detail="Display player not available")
        
        display_player.toggle_pause()
        is_paused = display_player.is_paused()
        
        return APIResponse(
            success=True,
            message="Paused" if is_paused else "Resumed",
            data={"paused": is_paused}
        )
    
    @app.post("/api/playback/next", response_model=APIResponse)
    async def next_media():
        """Switch to next media."""
        if not display_player:
            raise HTTPException(status_code=503, detail="Display player not available")
        
        display_player.next_media()
        return APIResponse(success=True, message="Switched to next media")
    
    @app.post("/api/playback/previous", response_model=APIResponse)
    async def previous_media():
        """Switch to previous media."""
        if not display_player:
            raise HTTPException(status_code=503, detail="Display player not available")
        
        display_player.previous_media()
        return APIResponse(success=True, message="Switched to previous media")
    
    # WiFi Management API
    
    @app.get("/api/wifi/scan", response_model=APIResponse)
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
    
    @app.post("/api/wifi/connect", response_model=APIResponse)
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
    
    @app.post("/api/wifi/hotspot", response_model=APIResponse)
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
            success = wifi_manager.start_hotspot()
            return APIResponse(
                success=success,
                message="Hotspot started" if success else "Failed to start hotspot",
                data={"hotspot_active": success}
            )
    
    # System Update API
    
    @app.get("/api/updates/check", response_model=APIResponse)
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
    
    @app.post("/api/updates/install", response_model=APIResponse)
    async def install_updates():
        """Install available updates."""
        if not updater:
            raise HTTPException(status_code=503, detail="Updater not available")
        
        success, message = updater.auto_update()
        return APIResponse(success=success, message=message)
    
    # Storage Information API
    
    @app.get("/api/storage", response_model=APIResponse)
    async def get_storage_info():
        """Get detailed storage usage information."""
        total, used, free = shutil.disk_usage("/")
        
        project_root = Path(__file__).resolve().parents[2]
        media_path = project_root / "media"
        media_size = get_dir_size(media_path)
        
        total_project_size = get_dir_size(project_root)
        app_size = total_project_size - media_size
        system_size = max(0, used - total_project_size)
        
        return APIResponse(
            success=True,
            data={
                "total": total,
                "used": used,
                "free": free,
                "system": system_size,
                "app": app_size,
                "media": media_size,
                "units": "bytes"
            }
        )
    
    # Dashboard API - Optimized single endpoint
    
    @app.get("/api/dashboard", response_model=DashboardData)
    async def get_dashboard():
        """Get consolidated dashboard data in a single request."""
        # Get status
        device_status = await get_status()
        
        # Get media data
        dashboard_data = media_index.get_dashboard_data()
        
        return DashboardData(
            status=device_status,
            media=dashboard_data["media"],
            active=dashboard_data["active"],
            loop=dashboard_data["loop"],
            last_updated=dashboard_data["last_updated"]
        )
    
    logger.info("FastAPI application created successfully")
    return app

async def process_media_file(file: UploadFile, converter: MediaConverter, config: Config) -> Dict[str, Any]:
    """Process a single uploaded media file."""
    # Validate file type and size
    allowed_extensions = {".gif", ".mp4", ".avi", ".mov", ".png", ".jpg", ".jpeg"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.filename}",
        )

    max_size = (config.media.max_file_size_mb if config else 10) * 1024 * 1024
    
    # Save to temporary file
    media_raw_dir = Path("media/raw")
    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file.filename, dir=media_raw_dir
        ) as tmp:
            content = await file.read()
            if len(content) > max_size:
                raise HTTPException(
                    status_code=413, detail=f"File too large: {file.filename}"
                )
            tmp.write(content)
            tmp_path = Path(tmp.name)

        # Generate slug and output directory
        slug = converter._generate_slug(tmp_path.name)
        output_dir = Path("media/processed") / slug

        # Convert media
        metadata = converter.convert_media_file(tmp_path, output_dir)
        if not metadata:
            raise HTTPException(
                status_code=500, detail=f"Failed to process {file.filename}"
            )
        
        # Augment metadata for frontend
        file_size = len(content)
        uploaded_at_iso = datetime.utcnow().isoformat() + "Z"

        metadata.update({
            "filename": file.filename,
            "type": file.content_type or metadata.get("type", "unknown"),
            "size": file_size,
            "uploadedAt": uploaded_at_iso,
            "url": f"/media/raw/{slug}{Path(file.filename).suffix}",
        })

        # Add to media index
        media_index.add_media(metadata, make_active=True)

        # Save original for preview
        dest_raw_path = media_raw_dir / f"{slug}{Path(file.filename).suffix}"
        shutil.copy(tmp_path, dest_raw_path)

        return metadata

    finally:
        # Clean up temp file
        if "tmp_path" in locals() and tmp_path.exists():
            tmp_path.unlink()

# For development/testing
if __name__ == "__main__":
    import uvicorn
    from config.schema import get_config
    
    config = get_config()
    app = create_app(config=config)
    
    # Add a dummy template for SPA testing if it doesn't exist
    spa_dir = Path(__file__).parent / "spa"
    spa_dir.mkdir(exist_ok=True)
    if not (spa_dir / "index.html").exists():
        with open(spa_dir / "index.html", "w") as f:
            f.write("<h1>SPA Placeholder</h1><p>Build the frontend and place it here.</p>")

    uvicorn.run(
        app, 
        host=config.web.host, 
        port=config.web.port,
        log_level="info"
    ) 