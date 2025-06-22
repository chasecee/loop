"""FastAPI web server for LOOP."""

import json
import os
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, status # type: ignore
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from config.schema import Config
from display.player import DisplayPlayer
from boot.wifi import WiFiManager
from deployment.updater import SystemUpdater

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

class ProcessingJobResponse(BaseModel):
    """Processing job status response - matches frontend ProcessingJob interface."""
    job_id: str
    filename: str
    status: Literal["processing", "completed", "error"]  # Match TypeScript union type
    progress: float  # 0-100
    stage: str
    message: str
    timestamp: float  # Unix timestamp

class PlayerStatus(BaseModel):
    """Player status - matches frontend PlayerStatus interface."""
    is_playing: bool
    current_media: Optional[str] = None
    loop_index: int
    total_media: int
    frame_rate: float
    loop_mode: Literal["all", "one"]
    showing_progress: bool = False  # Extra field returned by DisplayPlayer

class WiFiStatus(BaseModel):
    """WiFi status - matches frontend WiFiStatus interface."""
    connected: bool
    hotspot_active: bool
    current_ssid: Optional[str] = None
    ip_address: Optional[str] = None
    configured_ssid: Optional[str] = None
    hotspot_ssid: Optional[str] = None
    signal_strength: Optional[str] = None  # Can be string from wireless stats
    network_info: Optional[Dict[str, Any]] = None

class UpdateStatus(BaseModel):
    """Update status - matches frontend UpdateStatus interface."""
    current_version: Optional[str] = None
    git_available: Optional[bool] = None
    last_check: Optional[str] = None
    update_sources: Optional[Dict[str, Any]] = None

class DeviceStatus(BaseModel):
    """Device status matching frontend expectations."""
    system: str = "LOOP v1.0.0" 
    status: str = "running"
    timestamp: int = Field(default_factory=lambda: int(time.time()))
    player: Optional[PlayerStatus] = None
    wifi: Optional[WiFiStatus] = None
    updates: Optional[UpdateStatus] = None

class StorageInfo(BaseModel):
    """Storage info - matches frontend StorageData interface."""
    total: int
    used: int
    free: int
    system: int
    app: int
    media: int
    units: str = "bytes"

class DashboardData(BaseModel):
    """Combined dashboard data - matches frontend DashboardData interface."""
    status: DeviceStatus
    media: List[MediaItem]  # List of MediaItem objects
    active: Optional[str]
    loop: List[str]
    last_updated: Optional[int]
    processing: Optional[Dict[str, ProcessingJobResponse]] = None  # Processing jobs dict
    storage: StorageInfo

class APIResponse(BaseModel):
    """Standard API response format - matches frontend APIResponse interface."""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    errors: Optional[List[Dict[str, str]]] = None

class CacheControlMiddleware(BaseHTTPMiddleware):
    """Add cache control headers for static media files."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add cache headers for media files
        if request.url.path.startswith("/media/raw/"):
            # Cache media files for 1 hour
            response.headers["Cache-Control"] = "public, max-age=3600"
            response.headers["ETag"] = f'"{hash(request.url.path)}"'
        
        return response

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log each HTTP request with method, path, status code, and processing time."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"{request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f} ms)")
        return response

class ConcurrencyLimitMiddleware(BaseHTTPMiddleware):
    """Handle concurrency limits gracefully and provide helpful error responses."""
    
    def __init__(self, app, max_concurrent: int = 3):
        super().__init__(app)
        self.max_concurrent = max_concurrent
        self.active_requests = 0
    
    async def dispatch(self, request: Request, call_next):
        # Skip concurrency check for static files and health checks
        if (request.url.path.startswith("/_next") or 
            request.url.path.startswith("/assets") or
            request.url.path.startswith("/media/raw") or
            request.url.path == "/"):
            return await call_next(request)
        
        if self.active_requests >= self.max_concurrent:
            logger.warning(f"Concurrency limit exceeded: {self.active_requests}/{self.max_concurrent} active requests")
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "message": f"Server busy. Too many concurrent requests ({self.active_requests}/{self.max_concurrent}). Please retry in a moment.",
                    "code": "CONCURRENCY_LIMIT_EXCEEDED",
                    "retry_after": 2  # Suggest retry after 2 seconds
                }
            )
        
        self.active_requests += 1
        try:
            response = await call_next(request)
            return response
        finally:
            self.active_requests -= 1

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Standardize error responses across the API."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.error(f"Unhandled error in {request.method} {request.url.path}: {exc}", exc_info=True)
            
            # Map common exceptions to appropriate HTTP status codes
            if isinstance(exc, ValueError):
                status_code = 400
                message = str(exc)
            elif isinstance(exc, KeyError):
                status_code = 404
                message = f"Resource not found: {exc}"
            elif isinstance(exc, PermissionError):
                status_code = 403
                message = "Permission denied"
            elif isinstance(exc, FileNotFoundError):
                status_code = 404
                message = "File not found"
            else:
                status_code = 500
                message = "Internal server error"
            
            return JSONResponse(
                status_code=status_code,
                content={
                    "success": False,
                    "message": message,
                    "code": exc.__class__.__name__,
                    "timestamp": int(time.time())
                }
            )

class DisplaySettingsPayload(BaseModel):
    brightness: Optional[int] = None
    gamma: Optional[float] = None

class WifiNetwork(BaseModel):
    """WiFi network info - matches frontend WifiNetwork interface."""
    ssid: str
    signal: int
    secured: bool

# ------------------------------------------------------------------
# Directory-size helper with aggressive caching to prevent 44+ second delays.
# SD card operations are extremely slow, so we cache aggressively and only
# update after actual media changes.
# ------------------------------------------------------------------

_DIR_SIZE_CACHE: dict[Path, tuple[float, int]] = {}
_DIR_SIZE_TTL = 300  # 5 minutes - much longer cache since it's expensive
_STORAGE_CALCULATION_IN_PROGRESS = False


def _calc_dir_size_fast(path: Path) -> int:
    """Fast directory size calculation with early bailout for large directories."""
    total = 0
    if not path.exists():
        return 0
    
    try:
        # Use os.walk for better performance than recursive scandir
        for root, dirs, files in os.walk(path):
            # Limit to prevent runaway calculations
            if total > 10 * 1024**3:  # 10GB limit
                logger.warning(f"Directory size calculation truncated at 10GB for {path}")
                break
                
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    total += os.path.getsize(file_path)
                except (OSError, IOError):
                    # Skip files we can't read
                    continue
    except (OSError, IOError) as e:
        logger.warning(f"Error calculating directory size for {path}: {e}")
        return 0
    
    return total


def get_dir_size(path: Path) -> int:
    """Return cached dir size with aggressive caching to prevent slow SD card operations."""
    global _STORAGE_CALCULATION_IN_PROGRESS
    
    now = time.time()
    cached = _DIR_SIZE_CACHE.get(path)
    if cached and (now - cached[0] < _DIR_SIZE_TTL):
        return cached[1]

    # If a calculation is already in progress, return last known value or estimate
    if _STORAGE_CALCULATION_IN_PROGRESS:
        if cached:
            logger.debug(f"Storage calculation in progress, returning cached value for {path}")
            return cached[1]
        else:
            logger.debug(f"Storage calculation in progress, returning estimate for {path}")
            return 1024 * 1024 * 100  # 100MB estimate

    _STORAGE_CALCULATION_IN_PROGRESS = True
    try:
        logger.debug(f"Calculating directory size for {path}")
        start_time = time.time()
        size = _calc_dir_size_fast(path)
        calc_time = time.time() - start_time
        
        if calc_time > 1.0:  # Log slow calculations
            logger.warning(f"Slow storage calculation for {path}: {calc_time:.2f}s")
        
        _DIR_SIZE_CACHE[path] = (now, size)
        return size
    finally:
        _STORAGE_CALCULATION_IN_PROGRESS = False


def _invalidate_dir_size(path: Path | None = None):
    """Remove cache entry (or all) after media changes."""
    if path is None:
        _DIR_SIZE_CACHE.clear()
        logger.debug("Cleared all directory size cache")
    else:
        _DIR_SIZE_CACHE.pop(path, None)
        logger.debug(f"Invalidated directory size cache for {path}")

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
    
    # Configure request limits for large file uploads
    app.router.default_response_class.media_type = "application/json"
    

    
    # Add middleware in correct order (innermost to outermost)
    app.add_middleware(CacheControlMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ConcurrencyLimitMiddleware, max_concurrent=config.web.max_concurrent_requests if config else 12)  # Increased temporarily
    app.add_middleware(ErrorHandlingMiddleware)
    
    # CORS middleware (outermost)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify exact origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        max_age=3600,  # Cache preflight requests for 1 hour
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
    
    # Routes
    
    @app.get("/", response_class=HTMLResponse)
    async def root_spa():
        """Serve the SPA index page."""
        spa_index = spa_dir / "index.html"
        if spa_index.exists():
            return FileResponse(spa_index)
        raise HTTPException(status_code=404, detail="SPA not built/deployed")
    
    # System Status API
    
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
        """Upload *already-converted* media files from the browser (no server-side ffmpeg)."""
        logger.info(f"Upload started: {len(files)} files received")

        if not files:
            logger.warning("Upload failed: No files provided")
            raise HTTPException(status_code=400, detail="No files provided")

        # Pre-validate all files before processing any
        total_size = 0
        for file in files:
            # Check file size without reading full content first
            try:
                # Try to get size from content-length header if available
                file_size = getattr(file, 'size', None)
                if file_size is None:
                    # Fallback: read file to check size (unavoidable)
                    content = await file.read()
                    file_size = len(content)
                    # Reset file pointer
                    await file.seek(0)
                
                total_size += file_size
                logger.info(f"File {file.filename}: {file_size} bytes")
                
                if file_size > 100 * 1024 * 1024:  # 100MB limit per file
                    logger.warning(f"File {file.filename} too large: {file_size} bytes")
                    raise HTTPException(status_code=413, detail=f"{file.filename} is too large (max 100 MB)")
                    
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error checking file size for {file.filename}: {e}")
                raise HTTPException(status_code=500, detail=f"Error processing {file.filename}")

        # Check total upload size
        if total_size > 500 * 1024 * 1024:  # 500MB total limit
            logger.warning(f"Total upload size too large: {total_size} bytes")
            raise HTTPException(status_code=413, detail="Total upload size exceeds 500MB limit")

        logger.info(f"Pre-validation complete: {len(files)} files, {total_size} bytes total")

        slugs: list[str] = []
        job_ids: list[str] = []  # Track job IDs for display progress

        for i, file in enumerate(files):
            logger.info(f"Processing file {i+1}/{len(files)}: {file.filename} ({file.content_type})")
            
            # Read file content (may have been read during validation)
            try:
                content = await file.read()
                file_size = len(content)
                logger.info(f"File {file.filename} read successfully: {file_size} bytes")
            except Exception as e:
                logger.error(f"Failed to read file {file.filename}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")

            # Create a slug based on filename + uuid to avoid clashes
            sanitized = Path(file.filename).stem.replace(" ", "_").lower()
            slug = f"{sanitized}_{uuid.uuid4().hex[:8]}"
            logger.info(f"Generated slug for {file.filename}: {slug}")

            # --- Register lightweight upload job for progress UI ---
            job_id = str(uuid.uuid4())
            job_ids.append(job_id)
            logger.info(f"Created processing job {job_id} for {file.filename}")
            media_index.add_processing_job(job_id, file.filename)

            # Start progress overlay once
            if display_player and not display_player.showing_progress:
                try:
                    logger.info(f"Starting processing display for jobs: {job_ids}")
                    display_player.start_processing_display(job_ids)
                except Exception as e:
                    logger.warning(f"Failed to start processing display: {e}")

            try:
                if file.filename.lower().endswith(".zip"):
                    logger.info(f"Processing ZIP file: {file.filename}")
                    import zipfile, json

                    # Extract zip directly into processed directory
                    with tempfile.TemporaryDirectory() as tmpdir:
                        tmp_zip = Path(tmpdir) / "upload.zip"
                        logger.debug(f"Writing ZIP to temp file: {tmp_zip}")
                        
                        # Write file in chunks to avoid memory issues with large files
                        with open(tmp_zip, "wb") as f:
                            chunk_size = 1024 * 1024  # 1MB chunks
                            bytes_written = 0
                            while bytes_written < len(content):
                                chunk = content[bytes_written:bytes_written + chunk_size]
                                f.write(chunk)
                                bytes_written += len(chunk)
                                if bytes_written % (10 * 1024 * 1024) == 0:  # Log every 10MB
                                    logger.debug(f"Written {bytes_written}/{len(content)} bytes to temp file")

                        try:
                            with zipfile.ZipFile(tmp_zip, "r") as zf:
                                members = zf.namelist()
                                logger.debug(f"ZIP contents: {len(members)} files - {members[:10]}{'...' if len(members) > 10 else ''}")
                                
                                if "metadata.json" not in members:
                                    logger.error(f"ZIP file {file.filename} missing metadata.json")
                                    raise HTTPException(status_code=400, detail="metadata.json missing in upload")
                                
                                logger.debug("Reading metadata.json from ZIP")
                                meta_data = json.loads(zf.read("metadata.json").decode())
                                logger.debug(f"Metadata loaded: {list(meta_data.keys())}")

                                slug = meta_data.get("slug") or slug  # prefer slug from metadata
                                meta_data["slug"] = slug
                                output_dir = Path("media/processed") / slug
                                logger.info(f"Extracting ZIP to: {output_dir}")
                                output_dir.mkdir(parents=True, exist_ok=True)
                                
                                # Extract with progress logging for large files
                                total_members = len(members)
                                for idx, member in enumerate(members):
                                    zf.extract(member, output_dir)
                                    if idx % 100 == 0 or idx == total_members - 1:
                                        logger.debug(f"Extracted {idx+1}/{total_members} files")

                                # Minimal sanitisation: ensure frames live in frames/
                                # (skip deeper validation for brevity)

                                # Preserve original filename from metadata, not ZIP filename
                                original_filename = meta_data.get("original_filename") or meta_data.get("filename") or file.filename
                                logger.info(f"Original filename: {original_filename}")
                                
                                meta_data.setdefault("uploadedAt", datetime.utcnow().isoformat() + "Z")
                                meta_data["filename"] = original_filename  # Use original filename
                                meta_data.setdefault("size", len(content))

                                # Verify frames directory exists
                                frames_dir = output_dir / "frames"
                                if not frames_dir.exists():
                                    logger.warning(f"Frames directory not found after extraction: {frames_dir}")
                                    # Try to find frames in root of extracted content
                                    frame_files = list(output_dir.glob("*.rgb")) + list(output_dir.glob("*.png")) + list(output_dir.glob("*.jpg"))
                                    if frame_files:
                                        logger.info(f"Found {len(frame_files)} frame files in root, creating frames/ directory")
                                        frames_dir.mkdir(exist_ok=True)
                                        for frame_file in frame_files:
                                            frame_file.rename(frames_dir / frame_file.name)
                                            logger.debug(f"Moved {frame_file.name} to frames/")
                                    else:
                                        logger.error(f"No frame files found in extraction, this may cause playback issues")
                                else:
                                    logger.info(f"Frames directory exists with {len(list(frames_dir.glob('*')))} files")

                                logger.info(f"Adding media to index: {slug}")
                                media_index.add_media(meta_data, make_active=True)

                                slugs.append(slug)
                                logger.info(f"Completing processing job {job_id} for {file.filename}")
                                media_index.complete_processing_job(job_id, True)

                        except zipfile.BadZipFile as e:
                            error_msg = f"Invalid ZIP file {file.filename}: {str(e)}"
                            logger.error(error_msg)
                            media_index.complete_processing_job(job_id, False, error_msg)
                            raise HTTPException(status_code=400, detail=error_msg)
                        except json.JSONDecodeError as e:
                            error_msg = f"Invalid metadata.json in {file.filename}: {str(e)}"
                            logger.error(error_msg)
                            media_index.complete_processing_job(job_id, False, error_msg)
                            raise HTTPException(status_code=400, detail=error_msg)
                        except Exception as e:
                            error_msg = f"ZIP processing error for {file.filename}: {str(e)}"
                            logger.error(error_msg, exc_info=True)
                            media_index.complete_processing_job(job_id, False, error_msg)
                            raise HTTPException(status_code=500, detail=error_msg)

                else:
                    logger.info(f"Processing as pre-rendered video: {file.filename}")
                    # Fallback: treat as pre-rendered video
                    # Prepare directories
                    output_dir = Path("media/processed") / slug
                    output_dir.mkdir(parents=True, exist_ok=True)

                    # Save as video.mp4 inside its folder for consistency
                    out_path = output_dir / "video.mp4"
                    logger.debug(f"Writing video file to: {out_path}")
                    
                    # Write in chunks for large files
                    with open(out_path, "wb") as out_f:
                        chunk_size = 1024 * 1024  # 1MB chunks
                        bytes_written = 0
                        while bytes_written < len(content):
                            chunk = content[bytes_written:bytes_written + chunk_size]
                            out_f.write(chunk)
                            bytes_written += len(chunk)

                    metadata = {
                        "slug": slug,
                        "filename": file.filename,
                        "type": file.content_type or "video/mp4",
                        "size": len(content),
                        "uploadedAt": datetime.utcnow().isoformat() + "Z",
                    }

                    logger.info(f"Adding video media to index: {slug}")
                    media_index.add_media(metadata, make_active=True)

                    slugs.append(slug)
                    logger.info(f"Completing processing job {job_id} for {file.filename}")
                    media_index.complete_processing_job(job_id, True)

            except HTTPException:
                # Re-raise HTTP exceptions as-is
                raise
            except Exception as e:
                error_msg = f"Unexpected error processing {file.filename}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                media_index.complete_processing_job(job_id, False, error_msg)
                raise HTTPException(status_code=500, detail=error_msg)

        # Stop progress overlay
        if display_player:
            try:
                logger.info("Stopping processing display")
                display_player.stop_processing_display()
            except Exception as e:
                logger.warning(f"Failed to stop processing display: {e}")

        # Refresh player display in background to avoid blocking HTTP response
        if display_player:
            def refresh_player_async():
                try:
                    logger.info("Refreshing player media list")
                    display_player.refresh_media_list()
                    if slugs:
                        logger.info(f"Setting active media to: {slugs[-1]}")
                        display_player.set_active_media(slugs[-1])
                except Exception as exc:
                    logger.warning(f"Failed to refresh player after upload: {exc}")
            
            # Run in background thread to avoid blocking HTTP response
            import threading
            refresh_thread = threading.Thread(target=refresh_player_async, daemon=True)
            refresh_thread.start()
            logger.info("Started background player refresh")

        _invalidate_dir_size()
        logger.info(f"Upload complete: {len(slugs)} files processed, job_ids: {job_ids}")

        return APIResponse(success=True, message="Upload complete", data={"slug": slugs[-1] if slugs else None, "job_ids": job_ids})
    
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
            
            _invalidate_dir_size()
            
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
            
            if cleanup_count:
                _invalidate_dir_size()
            
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
    
    @app.post("/api/playback/loop-mode", response_model=APIResponse)
    async def toggle_loop_mode():
        """Toggle loop mode between 'all' and 'one'."""
        if not display_player:
            raise HTTPException(status_code=503, detail="Display player not available")
        
        new_mode = display_player.toggle_loop_mode()
        return APIResponse(
            success=True, 
            message=f"Loop mode set to: {new_mode}",
            data={"loop_mode": new_mode}
        )
    
    @app.post("/api/display/brightness", response_model=APIResponse)
    async def set_display_settings(payload: DisplaySettingsPayload):
        """Set LCD backlight brightness (0-100)."""
        if not display_player:
            raise HTTPException(status_code=503, detail="Display driver not available")
        response_data = {}
        try:
            if payload.brightness is not None:
                level = max(0, min(100, payload.brightness))
                display_player.display_driver.set_backlight(level)
                response_data["brightness"] = level
                if config:
                    config.display.brightness = level
            if payload.gamma is not None:
                display_player.display_driver.set_gamma(payload.gamma)
                response_data["gamma"] = payload.gamma
                if config:
                    config.display.gamma = payload.gamma
            if config and response_data:
                config.save()
            return APIResponse(success=True, message="Display settings updated", data=response_data)
        except Exception as e:
            logger.error(f"Failed to set brightness: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/display/brightness", response_model=APIResponse)
    async def get_display_settings():
        """Get current LCD backlight brightness and gamma."""
        try:
            level = config.display.brightness if config and config.display else 100
            gamma = config.display.gamma if config and config.display else 2.4
            return APIResponse(success=True, data={"brightness": level, "gamma": gamma})
        except Exception as e:
            logger.error(f"Failed to get brightness: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
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
            if config and not config.wifi.hotspot_enabled:
                raise HTTPException(status_code=403, detail="Hotspot functionality is disabled in the configuration.")
            
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
    
    # @app.get("/api/storage", response_model=APIResponse)  # DEPRECATED – storage now in /api/dashboard
    
    # Dashboard API - Optimized single endpoint
    
    @app.get("/api/dashboard", response_model=DashboardData)
    async def get_dashboard():
        """Get consolidated dashboard data in a single request."""
        # System status
        device_status = await get_status()

        # Media / loop / processing data
        dashboard_data = media_index.get_dashboard_data()

        # Storage data (reuse logic from /api/storage)
        total, used, free = shutil.disk_usage("/")

        project_root = Path(__file__).resolve().parents[2]
        media_path = project_root / "media"
        media_size = get_dir_size(media_path)

        total_project_size = get_dir_size(project_root)
        app_size = total_project_size - media_size
        system_size = max(0, used - total_project_size)

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
    
    # Processing Progress API
    
    @app.get("/api/media/progress/{job_id}", response_model=APIResponse)
    async def get_processing_progress(job_id: str):
        """Get processing progress for a specific job."""
        job_data = media_index.get_processing_job(job_id)
        if not job_data:
            raise HTTPException(status_code=404, detail="Processing job not found")
        
        return APIResponse(
            success=True,
            data=job_data
        )
    
    @app.get("/api/media/progress", response_model=APIResponse)
    async def get_all_processing_progress():
        """Get all current processing jobs."""
        try:
            jobs = media_index.list_processing_jobs()
            return APIResponse(
                success=True,
                data={"jobs": jobs}
            )
        except Exception as e:
            logger.error(f"Failed to get processing progress: {e}")
            # Return empty jobs instead of error to prevent frontend polling issues
            return APIResponse(
                success=True,
                data={"jobs": {}},
                message="Progress data temporarily unavailable"
            )
    
    @app.delete("/api/media/progress/{job_id}", response_model=APIResponse)
    async def clear_processing_job(job_id: str):
        """Clear a completed processing job."""
        job_data = media_index.get_processing_job(job_id)
        if not job_data:
            raise HTTPException(status_code=404, detail="Processing job not found")
        
        media_index.remove_processing_job(job_id)
        return APIResponse(
            success=True,
            message="Processing job cleared"
        )
    
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
        log_level="info",
        limit_max_requests=None,
    ) 