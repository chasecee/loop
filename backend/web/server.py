"""FastAPI web server for LOOP."""

import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from config.schema import Config
from display.player import DisplayPlayer
from boot.wifi import WiFiManager
from deployment.updater import SystemUpdater
from utils.convert import MediaConverter
import utils.media_index as mindex
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
    
    # (Removed legacy /static mount; SPA bundle should contain all assets)
    
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
    
    # Serve raw media files so the frontend can display previews
    app.mount("/media/raw", StaticFiles(directory=media_raw_dir), name="raw-media")
    
    # Media converter
    if config:
        converter = MediaConverter(config.display.width, config.display.height)
    else:
        converter = MediaConverter(240, 320)  # Default size
    
    @app.get("/", response_class=HTMLResponse)
    async def root_spa():
        spa_index = Path(__file__).parent / "spa" / "index.html"
        if spa_index.exists():
            return FileResponse(spa_index)
        raise HTTPException(status_code=404, detail="SPA not built/deployed")
    
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
            slug = converter._generate_slug(tmp_path.name)
            output_dir = media_processed_dir / slug

            # Convert media
            metadata = converter.convert_media_file(tmp_path, output_dir)
            if not metadata:
                raise HTTPException(
                    status_code=500, detail=f"Failed to process {file.filename}"
                )
            
            # --- Augment metadata with extra fields expected by the frontend UI ---
            file_size = len(content)  # Size in bytes from uploaded content
            uploaded_at_iso = datetime.utcnow().isoformat() + "Z"

            metadata.update(
                {
                    "filename": file.filename,
                    "type": file.content_type or metadata.get("type", "unknown"),
                    "size": file_size,
                    "uploadedAt": uploaded_at_iso,
                    "url": f"/media/raw/{slug}{Path(file.filename).suffix}",
                }
            )

            # Persist via media_index – automatically marks active & adds to loop
            mindex.add_media(metadata, make_active=True)

            # Persist original upload for preview image (copy instead of move to retain tmp for cleanup)
            dest_raw_path = media_raw_dir / f"{slug}{Path(file.filename).suffix}"
            shutil.copy(tmp_path, dest_raw_path)

            return metadata

        finally:
            # Clean up the temporary file
            if "tmp_path" in locals() and tmp_path.exists():
                tmp_path.unlink()
    
    @app.post("/api/media")
    async def upload_media_files(files: List[UploadFile] = File(...)):
        """Handle multiple file uploads and processing.

        While conversion is underway, pause the on-device playback and show a
        *Processing…* message so the user isn't left wondering what's
        happening. Playback automatically resumes (with a *Done!* toast) once
        everything is finished – even if one of the uploads fails. This avoids
        race-conditions by pausing *before* any heavy work begins so the
        `DisplayPlayer` thread is idle during `display_driver.display_frame`
        calls made from `show_message()`.
        """

        processed_files: List[Dict] = []
        errors: List[Dict] = []

        # ------------------------------------------------------------------
        # Pause playback & show "Processing" splash
        # ------------------------------------------------------------------
        playback_was_running = False
        if display_player and not display_player.is_paused():
            playback_was_running = True
            try:
                display_player.toggle_pause()
                display_player.show_message("Processing media…", duration=0)
            except Exception as exc:
                logger.warning(f"Failed to display processing splash: {exc}")

        try:
            # --------------------------------------------------------------
            # Process every uploaded file serially for now (keeps memory low)
            # --------------------------------------------------------------
            for file in files:
                try:
                    metadata = await process_and_index_file(file, converter, config)
                    processed_files.append(metadata)
                except Exception as e:
                    logger.error(f"Upload failed for {file.filename}: {e}")
                    error_detail = e.detail if isinstance(e, HTTPException) else str(e)
                    errors.append({"filename": file.filename, "error": error_detail})
        finally:
            # ------------------------------------------------------------------
            # Always refresh the player/media-list, then resume playback
            # ------------------------------------------------------------------
            if display_player:
                try:
                    display_player.refresh_media_list()
                except Exception as exc:
                    logger.error(f"Failed to refresh media list: {exc}")

                if playback_was_running:
                    # Show quick "done" banner, then resume playback
                    try:
                        display_player.show_message("Processing complete!", duration=2.0)
                    except Exception:
                        pass
                    display_player.toggle_pause()  # Resume

        # If *all* uploads failed, bubble an error back to the client
        if not processed_files and errors:
            raise HTTPException(status_code=500, detail={"errors": errors})

        return {
            "success": True,
            "processed_files": processed_files,
            "errors": errors,
        }
    
    @app.post("/api/media/{slug}/activate")
    async def activate_media(slug: str):
        """Set a media item as active."""
        
        if not display_player:
            raise HTTPException(status_code=503, detail="Display player not available")
        
        try:
            mindex.add_to_loop(slug)  # ensure in loop
            mindex.set_active(slug)
            if display_player:
                display_player.set_active_media(slug)
            return {"success": True, "message": f"Activated media: {slug}"}
        except KeyError:
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
            mindex.remove_media(slug)
            
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
    
    @app.get("/api/media")
    async def get_media():
        """Return the media library and active item."""
        return {
            "media": mindex.list_media(),
            "active": mindex.get_active(),
            "last_updated": int(time.time()),
        }
    
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
    
    # ------------------------------------------------------------------
    # Loop queue management
    # ------------------------------------------------------------------

    MEDIA_INDEX_PATH = Path("media/index.json")

    def _read_media_index() -> Dict:
        """Read the media index JSON, returning default structure if missing."""
        if MEDIA_INDEX_PATH.exists():
            try:
                with open(MEDIA_INDEX_PATH, "r") as f:
                    return json.load(f)
            except Exception as exc:
                logger.error(f"Failed to read media index: {exc}")
        # Default structure
        return {"media": [], "active": None, "loop": [], "last_updated": None}

    def _write_media_index(data: Dict) -> None:
        """Persist the media index atomically."""
        try:
            MEDIA_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(MEDIA_INDEX_PATH, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as exc:
            logger.error(f"Failed to write media index: {exc}")

    @app.get("/api/loop")
    async def get_loop_queue():
        """Return the current loop queue as a list of slugs."""
        return {"loop": mindex.list_loop()}

    @app.post("/api/loop")
    async def add_to_loop(payload: AddToLoopPayload):
        """Append a slug to the loop queue (if not already present)."""
        try:
            mindex.add_to_loop(payload.slug)
            if display_player:
                display_player.refresh_media_list()
            return {"success": True, "loop": mindex.list_loop()}
        except KeyError:
            raise HTTPException(status_code=404, detail="Media not found")

    @app.delete("/api/loop/{slug}")
    async def remove_from_loop(slug: str):
        """Remove slug from loop queue."""
        mindex.remove_from_loop(slug)
        if display_player:
            display_player.refresh_media_list()
        return {"success": True, "loop": mindex.list_loop()}

    # ------------------------------------------------------------
    # Re-order loop list – replaces the entire array atomically
    # ------------------------------------------------------------

    class LoopOrderPayload(BaseModel):
        loop: List[str]

    @app.put("/api/loop")
    async def reorder_loop(payload: LoopOrderPayload):
        """Persist a new loop order supplied as a list of slugs."""
        mindex.reorder_loop(payload.loop)
        if display_player:
            display_player.refresh_media_list()
        return {"success": True, "loop": mindex.list_loop()}

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

    # --------------------------------------------------------------
    # Dashboard endpoint – aggregate common polling data
    # --------------------------------------------------------------

    @app.get("/api/dashboard")
    async def get_dashboard():
        """Return status, media library and loop queue in one request."""
        # Re-use existing helper handlers to avoid duplicating logic.
        status_data = await get_status()
        media_data = await get_media()
        loop_data = await get_loop_queue()

        # Ensure active media info is included at the top level
        return {
            "status": status_data,
            "media": media_data["media"],  # Just the media list
            "active": media_data["active"],  # Active media at top level
            "loop": loop_data["loop"],  # Just the loop list
            "last_updated": media_data["last_updated"]
        }

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