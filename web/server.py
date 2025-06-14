"""FastAPI web server for LOOP."""

import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config.schema import Config
from display.player import DisplayPlayer
from boot.wifi import WiFiManager
from deployment.updater import SystemUpdater
from utils.convert import MediaConverter
from utils.logger import get_logger


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
        return {
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
    
    @app.post("/api/upload")
    async def upload_media(
        file: UploadFile = File(None),
        original_file: UploadFile = File(None),
        frames: List[UploadFile] = File(None),
        durations: List[float] = Form(None)
    ):
        """Upload and process media file."""
        
        # Handle pre-processed frames from browser
        if original_file and frames and durations:
            try:
                # Generate slug from original filename
                slug = converter._generate_slug(original_file.filename)
                output_dir = media_processed_dir / slug
                frames_dir = output_dir / "frames"
                output_dir.mkdir(parents=True, exist_ok=True)
                frames_dir.mkdir(exist_ok=True)
                
                # Save frames
                frame_files = []
                for i, frame in enumerate(frames):
                    frame_path = frames_dir / f"frame_{i:06d}.jpg"
                    content = await frame.read()
                    with open(frame_path, 'wb') as f:
                        f.write(content)
                    frame_files.append(frame_path.name)
                
                # Generate metadata
                metadata = {
                    "type": "gif",
                    "slug": slug,
                    "original_filename": original_file.filename,
                    "width": config.display.width if config else 240,
                    "height": config.display.height if config else 320,
                    "frame_count": len(frames),
                    "frames": frame_files,
                    "durations": durations,
                    "format": "jpeg",
                    "loop_count": 0  # Infinite loop by default
                }
                
                # Save metadata
                with open(output_dir / "metadata.json", 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                # Update media index
                media_index_file = Path("media/index.json")
                media_data = {"media": [], "active": None, "last_updated": None}
                
                if media_index_file.exists():
                    with open(media_index_file, 'r') as f:
                        media_data = json.load(f)
                
                media_data["media"].append(metadata)
                media_data["last_updated"] = time.time()
                
                if len(media_data["media"]) == 1:
                    media_data["active"] = slug
                
                with open(media_index_file, 'w') as f:
                    json.dump(media_data, f, indent=2)
                
                # Refresh player media list
                if display_player:
                    display_player.refresh_media_list()
                
                logger.info(f"Successfully processed pre-processed frames for: {metadata['original_filename']}")
                
                return {
                    "success": True,
                    "message": f"Successfully uploaded and processed {original_file.filename}",
                    "metadata": metadata
                }
                
            except Exception as e:
                logger.error(f"Failed to process pre-processed frames: {e}")
                if 'output_dir' in locals() and output_dir.exists():
                    shutil.rmtree(output_dir)
                raise HTTPException(status_code=500, detail=str(e))
        
        # Handle regular file upload (fallback for videos or when browser processing fails)
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Validate file type
        allowed_extensions = {'.gif', '.mp4', '.avi', '.mov', '.png', '.jpg', '.jpeg'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_ext}"
            )
        
        # Check file size (10MB limit by default)
        max_size = (config.media.max_file_size_mb if config else 10) * 1024 * 1024
        
        try:
            # Save uploaded file
            raw_file_path = media_raw_dir / file.filename
            with open(raw_file_path, 'wb') as f:
                content = await file.read()
                if len(content) > max_size:
                    raise HTTPException(
                        status_code=413, 
                        detail=f"File too large. Maximum size: {max_size // (1024*1024)}MB"
                    )
                f.write(content)
            
            logger.info(f"Uploaded file: {file.filename} ({len(content)} bytes)")
            
            # Convert media
            slug = converter._generate_slug(file.filename)
            output_dir = media_processed_dir / slug
            
            metadata = converter.convert_media_file(raw_file_path, output_dir)
            
            if not metadata:
                # Clean up on failure
                if raw_file_path.exists():
                    raw_file_path.unlink()
                if output_dir.exists():
                    shutil.rmtree(output_dir)
                raise HTTPException(status_code=500, detail="Failed to process media file")
            
            # Update media index
            media_index_file = Path("media/index.json")
            media_data = {"media": [], "active": None, "last_updated": None}
            
            if media_index_file.exists():
                with open(media_index_file, 'r') as f:
                    media_data = json.load(f)
            
            # Add new media to list
            media_data["media"].append(metadata)
            media_data["last_updated"] = time.time()
            
            # Set as active if it's the first media
            if len(media_data["media"]) == 1:
                media_data["active"] = slug
            
            with open(media_index_file, 'w') as f:
                json.dump(media_data, f, indent=2)
            
            # Refresh player media list
            if display_player:
                display_player.refresh_media_list()
            
            logger.info(f"Successfully processed media: {metadata['original_filename']}")
            
            return {
                "success": True,
                "message": f"Successfully uploaded and processed {file.filename}",
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            # Clean up on any error
            if 'raw_file_path' in locals() and raw_file_path.exists():
                raw_file_path.unlink()
            if 'output_dir' in locals() and output_dir.exists():
                shutil.rmtree(output_dir)
            
            if isinstance(e, HTTPException):
                raise e
            else:
                raise HTTPException(status_code=500, detail=str(e))
    
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
    async def connect_wifi(ssid: str = Form(...), password: str = Form("")):
        """Connect to WiFi network."""
        if not wifi_manager:
            raise HTTPException(status_code=503, detail="WiFi manager not available")
        
        success = wifi_manager.connect_to_network(ssid, password)
        
        if success:
            # Update config
            if config:
                config.wifi.ssid = ssid
                config.wifi.password = password
                config.save()
            
            return {"success": True, "message": f"Connected to {ssid}"}
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
        log_level="info"
    ) 