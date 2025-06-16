"""FastAPI web server for LOOP."""

import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config.schema import Config
from display.player import DisplayPlayer
from boot.wifi import WiFiManager
from deployment.updater import SystemUpdater
from utils.convert import MediaConverter
from utils.logger import get_logger

# Define a Pydantic model for the WiFi connection request
from pydantic import BaseModel

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

class WiFiCredentials(BaseModel):
    ssid: str
    password: Optional[str] = ""

class AddToLoopPayload(BaseModel):
    slug: str

def create_app(display_player: DisplayPlayer = None,
               wifi_manager: WiFiManager = None, 
               updater: SystemUpdater = None,
               config: Config = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="LOOP",
        description="Little Optical Output Pal - Your pocket-sized animation companion!",
        version="1.0.0"
    )
    
    logger = get_logger("web")
    
    # Static files and templates
    static_dir = Path(__file__).parent / "static"
    template_dir = Path(__file__).parent / "templates"
    
    # Create directories if they don't exist
    static_dir.mkdir(exist_ok=True)
    template_dir.mkdir(exist_ok=True)
    
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    templates = Jinja2Templates(directory=template_dir)
    
    # --- New SPA static file serving ---
    # The Next.js build output will be moved to this directory
    spa_dir = Path(__file__).parent / "spa"
    
    # Mount the static assets from the Next.js build
    if (spa_dir / "_next").exists():
        app.mount("/_next", StaticFiles(directory=spa_dir / "_next"), name="next-static")
    
    # Mount other public assets only if SPA folder exists to avoid runtime error
    if spa_dir.exists():
        app.mount("/assets", StaticFiles(directory=spa_dir), name="spa-assets")
    else:
        logger.warning("SPA directory %s not found, skipping static mount", spa_dir)
    
    # --- End new SPA serving ---

    # Media directories
    media_raw_dir = Path("media/raw")
    media_processed_dir = Path("media/processed")
    media_raw_dir.mkdir(parents=True, exist_ok=True)
    media_processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Media converter
    if config:
        converter = MediaConverter(config.display.width, config.display.height)
    else:
        converter = MediaConverter(240, 320)  # Default size
    
    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request):
        """Home page with media list and controls."""
        
        # Get current status
        player_status = display_player.get_status() if display_player else {}
        wifi_status = wifi_manager.get_status() if wifi_manager else {}
        
        # Load media list
        media_index_file = Path("media/index.json")
        media_list = []
        if media_index_file.exists():
            with open(media_index_file, 'r') as f:
                data = json.load(f)
                media_list = data.get('media', [])
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "media_list": media_list,
            "player_status": player_status,
            "wifi_status": wifi_status,
            "current_media": player_status.get('current_media', {}),
        })
    
    @app.get("/api/status")
    async def get_status():
        """Get system status."""
        status = {
            "system": "LOOP v1.0.0",
            "status": "running",
            "timestamp": int(time.time())
        }
        
        if display_player:
            status["player"] = display_player.get_status()
        
        if wifi_manager:
            status["wifi"] = wifi_manager.get_status()
        
        if updater:
            status["updates"] = updater.get_update_status()
        
        return status
    
    async def process_and_index_file(
        file: UploadFile, converter: MediaConverter, config: Config
    ):
        """Helper to process a single uploaded file."""
        # Validate file type and size
        allowed_extensions = {
            ".gif", ".mp4", ".avi", ".mov", ".png", ".jpg", ".jpeg"
        }
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.filename}",
            )

        max_size = (
            config.media.max_file_size_mb if config else 10
        ) * 1024 * 1024
        
        # Save to a temporary file to check size and pass to converter
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
            slug = converter._generate_slug(file.filename)
            output_dir = media_processed_dir / slug

            # Convert media
            metadata = converter.convert_media_file(tmp_path, output_dir)
            if not metadata:
                raise HTTPException(
                    status_code=500, detail=f"Failed to process {file.filename}"
                )
            
            # Update media index
            media_index_file = Path("media/index.json")
            media_data = {"media": [], "active": None, "loop": [], "last_updated": None}
            if media_index_file.exists():
                with open(media_index_file, "r") as f:
                    media_data = json.load(f)

            # Add new media and set as active if it's the first one
            media_data["media"].append(metadata)
            if len(media_data["media"]) == 1:
                media_data["active"] = slug

            media_data["last_updated"] = time.time()
            with open(media_index_file, "w") as f:
                json.dump(media_data, f, indent=2)

            return metadata

        finally:
            # Clean up the temporary file
            if "tmp_path" in locals() and tmp_path.exists():
                tmp_path.unlink()
    
    @app.post("/api/media")
    async def upload_media_files(files: List[UploadFile] = File(...)):
        """Handles multiple file uploads and processing."""
        processed_files = []
        errors = []

        for file in files:
            try:
                metadata = await process_and_index_file(file, converter, config)
                processed_files.append(metadata)
            except Exception as e:
                logger.error(f"Upload failed for {file.filename}: {e}")
                error_detail = e.detail if isinstance(e, HTTPException) else str(e)
                errors.append({"filename": file.filename, "error": error_detail})

        # Refresh player only once after all files are processed
        if display_player:
            display_player.refresh_media_list()

        if not processed_files and errors:
             raise HTTPException(status_code=500, detail={"errors": errors})

        return {
            "success": True,
            "processed_files": processed_files,
            "errors": errors
        }
    
    @app.post("/api/media/{slug}/activate")
    async def activate_media(slug: str):
        """Set a media item as active."""
        
        if not display_player:
            raise HTTPException(status_code=503, detail="Display player not available")
        
        success = display_player.set_active_media(slug)
        
        if success:
            return {"success": True, "message": f"Activated media: {slug}"}
        else:
            raise HTTPException(status_code=404, detail="Media not found")
    
    @app.delete("/api/media/{slug}")
    async def delete_media(slug: str):
        """Delete a media item."""
        
        try:
            # Remove from filesystem
            media_dir = media_processed_dir / slug
            raw_files = list(media_raw_dir.glob(f"*{slug}*"))
            
            if media_dir.exists():
                shutil.rmtree(media_dir)
            
            for raw_file in raw_files:
                raw_file.unlink()
            
            # Update media index
            media_index_file = Path("media/index.json")
            if media_index_file.exists():
                with open(media_index_file, 'r') as f:
                    media_data = json.load(f)
                
                # Remove from media list
                media_data["media"] = [m for m in media_data["media"] if m.get("slug") != slug]
                
                # Reset active if this was the active media
                if media_data.get("active") == slug:
                    media_data["active"] = media_data["media"][0]["slug"] if media_data["media"] else None
                
                media_data["last_updated"] = time.time()
                
                with open(media_index_file, 'w') as f:
                    json.dump(media_data, f, indent=2)
            
            # Refresh player media list
            if display_player:
                display_player.refresh_media_list()
            
            logger.info(f"Deleted media: {slug}")
            
            return {"success": True, "message": f"Deleted media: {slug}"}
            
        except Exception as e:
            logger.error(f"Failed to delete media {slug}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/player/pause")
    async def toggle_pause():
        """Toggle playback pause."""
        if not display_player:
            raise HTTPException(status_code=503, detail="Display player not available")
        
        display_player.toggle_pause()
        is_paused = display_player.is_paused()
        
        return {"success": True, "paused": is_paused}
    
    @app.post("/api/player/next")
    async def next_media():
        """Switch to next media."""
        if not display_player:
            raise HTTPException(status_code=503, detail="Display player not available")
        
        display_player.next_media()
        return {"success": True, "message": "Switched to next media"}
    
    @app.post("/api/player/previous")
    async def previous_media():
        """Switch to previous media."""
        if not display_player:
            raise HTTPException(status_code=503, detail="Display player not available")
        
        display_player.previous_media()
        return {"success": True, "message": "Switched to previous media"}
    
    @app.get("/api/wifi/scan")
    async def scan_wifi():
        """Scan for available WiFi networks."""
        if not wifi_manager:
            raise HTTPException(status_code=503, detail="WiFi manager not available")
        
        networks = wifi_manager.scan_networks()
        return {"networks": networks}
    
    @app.post("/api/wifi/connect")
    async def connect_wifi(credentials: WiFiCredentials):
        """Connect to WiFi network using JSON payload."""
        if not wifi_manager:
            raise HTTPException(status_code=503, detail="WiFi manager not available")
        
        success = wifi_manager.connect_to_network(credentials.ssid, credentials.password)
        
        if success:
            # Update config
            if config:
                config.wifi.ssid = credentials.ssid
                config.wifi.password = credentials.password
                config.save()
            
            return {"success": True, "message": f"Connected to {credentials.ssid}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to connect to WiFi")
    
    @app.post("/api/wifi/hotspot")
    async def toggle_hotspot():
        """Toggle WiFi hotspot."""
        if not wifi_manager:
            raise HTTPException(status_code=503, detail="WiFi manager not available")
        
        if wifi_manager.hotspot_active:
            success = wifi_manager.stop_hotspot()
            return {"success": success, "hotspot_active": False}
        else:
            success = wifi_manager.start_hotspot()
            return {"success": success, "hotspot_active": success}
    
    @app.get("/api/updates/check")
    async def check_updates():
        """Check for available updates."""
        if not updater:
            raise HTTPException(status_code=503, detail="Updater not available")
        
        update_sources = updater.check_all_sources()
        return {"updates_available": update_sources}
    
    @app.post("/api/updates/install")
    async def install_updates():
        """Install available updates."""
        if not updater:
            raise HTTPException(status_code=503, detail="Updater not available")
        
        success, message = updater.auto_update()
        return {"success": success, "message": message}
    
    # Settings page
    @app.get("/settings", response_class=HTMLResponse)
    async def settings_page(request: Request):
        """Settings and configuration page."""
        
        wifi_status = wifi_manager.get_status() if wifi_manager else {}
        update_status = updater.get_update_status() if updater else {}
        
        return templates.TemplateResponse("settings.html", {
            "request": request,
            "wifi_status": wifi_status,
            "update_status": update_status,
            "config": config.__dict__ if config else {}
        })
    
    @app.get("/api/media")
    async def get_media():
        """Return the media library and active item."""
        media_index_file = Path("media/index.json")
        if media_index_file.exists():
            with open(media_index_file, "r") as f:
                data = json.load(f)
            return {
                "media": data.get("media", []),
                "active": data.get("active"),
                "last_updated": data.get("last_updated"),
            }
        else:
            return {"media": [], "active": None, "last_updated": None}
    
    # Aliases for playback controls to match frontend expectations
    @app.post("/api/playback/toggle")
    async def playback_toggle():
        return await toggle_pause()

    @app.post("/api/playback/next")
    async def playback_next():
        return await next_media()

    @app.post("/api/playback/previous")
    async def playback_previous():
        return await previous_media()
    
    # --- New Endpoints for SPA ---
    
    @app.get("/api/loop")
    async def get_loop_queue():
        """Get the current media loop/playlist."""
        # This is a placeholder. You'd typically return a list of media slugs.
        if display_player:
            return {"loop": [media.get("slug") for media in display_player.media_list]}
        return {"loop": []}

    @app.post("/api/loop")
    async def add_to_loop(payload: AddToLoopPayload):
        """Add a media item to the loop."""
        # Placeholder logic
        return {"success": True, "message": f"Added {payload.slug} to loop."}

    @app.delete("/api/loop/{slug}")
    async def remove_from_loop(slug: str):
        """Remove a media item from the loop."""
        # Placeholder logic
        return {"success": True, "message": f"Removed {slug} from loop."}

    @app.get("/api/storage")
    async def get_storage_info():
        """Get detailed storage usage information."""
        total, used, free = shutil.disk_usage("/")
        
        project_root = Path(__file__).resolve().parents[2]
        
        media_path = project_root / "media"
        media_size = get_dir_size(media_path)
        
        # App size is the total project size minus media
        total_project_size = get_dir_size(project_root)
        app_size = total_project_size - media_size
        
        # System size is what's left over
        system_size = used - total_project_size
        
        return {
            "total": total,
            "used": used,
            "free": free,
            "system": system_size if system_size > 0 else 0,
            "app": app_size,
            "media": media_size,
            "units": "bytes"
        }

    # --- End New Endpoints ---

    # --- New SPA Catch-all Route ---
    @app.get("/{full_path:path}", response_class=HTMLResponse)
    async def serve_spa(request: Request, full_path: str):
        """Serve the single-page application (compiled Next.js export)."""
        spa_index = Path(__file__).parent / "spa" / "index.html"

        if spa_index.exists():
            # Return the raw exported HTML file – no template rendering needed
            return FileResponse(spa_index)

        logger.error("SPA index.html not found at %s", spa_index)
        raise HTTPException(status_code=404, detail="SPA not built/deployed")

    logger.info("FastAPI application created successfully")
    return app


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