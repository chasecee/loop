"""Media management routes for LOOP web server."""

import json
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from typing import List
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi import Depends

from ..core.models import APIResponse, AddToLoopPayload, ProcessingJobResponse
from ..core.storage import invalidate_storage_cache
from ..core.events import broadcaster
from display.player import DisplayPlayer
from utils.media_index import media_index
from utils.logger import get_logger
from .media_upload import process_media_upload
from .dashboard import invalidate_dashboard_cache

logger = get_logger("web.media")

def create_media_router(
    display_player: DisplayPlayer = None,
    media_raw_dir: Path = None,
    media_processed_dir: Path = None
) -> APIRouter:
    """Create media management router with dependencies."""
    
    router = APIRouter(prefix="/api/media", tags=["media"])
    
    @router.get("", response_model=APIResponse)
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
    
    @router.post("", response_model=APIResponse)
    async def upload_media(files: List[UploadFile] = File(...)):
        """Upload already-converted media files from the browser."""
        logger.info(f"Upload started: {len(files)} files received")
        
        upload_result = await process_media_upload(
            files, media_raw_dir, media_processed_dir, display_player
        )
        
        invalidate_storage_cache()
        invalidate_dashboard_cache()
        
        return APIResponse(
            success=True, 
            message="Upload complete", 
            data=upload_result
        )
    
    @router.post("/{slug}/activate", response_model=APIResponse)
    async def activate_media(slug: str):
        """Set a media item as active."""
        if not display_player:
            raise HTTPException(status_code=503, detail="Display player not available")
        
        try:
            media_index.add_to_loop(slug)  # Ensure in loop
            media_index.set_active(slug)
            display_player.set_active_media(slug)
            invalidate_dashboard_cache()
            return APIResponse(success=True, message=f"Activated media: {slug}")
        except KeyError:
            raise HTTPException(status_code=404, detail="Media not found")
    
    @router.delete("/{slug}", response_model=APIResponse)
    async def delete_media(slug: str):
        """Delete a media item."""
        try:
            # Handle display player deletion first (before removing files)
            if display_player:
                display_player.handle_media_deletion(slug)
            
            # Update media index
            media_index.remove_media(slug)
            
            # Remove from filesystem AFTER stopping playback
            media_dir = media_processed_dir / slug
            raw_files = list(media_raw_dir.glob(f"*{slug}*"))
            
            if media_dir.exists():
                shutil.rmtree(media_dir)
                logger.info(f"Removed processed directory: {media_dir}")
            
            for raw_file in raw_files:
                raw_file.unlink()
                logger.info(f"Removed raw file: {raw_file}")
            
            invalidate_storage_cache()
            invalidate_dashboard_cache()
            
            return APIResponse(success=True, message=f"Deleted media: {slug}")
            
        except Exception as e:
            logger.error(f"Failed to delete media {slug}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/cleanup", response_model=APIResponse)
    async def cleanup_orphaned_media():
        """Clean up orphaned media files."""
        try:
            cleanup_count = media_index.cleanup_orphaned_files(media_raw_dir, media_processed_dir)
            
            if display_player:
                display_player.refresh_media_list()
            
            if cleanup_count:
                invalidate_storage_cache()
                invalidate_dashboard_cache()
            
            return APIResponse(
                success=True,
                message=f"Cleaned up {cleanup_count} orphaned files"
            )
        except Exception as e:
            logger.error(f"Failed to cleanup media: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Processing Progress API
    
    @router.get("/progress/{job_id}", response_model=APIResponse)
    async def get_processing_progress(job_id: str):
        """Get processing progress for a specific job."""
        job_data = media_index.get_processing_job(job_id)
        if not job_data:
            raise HTTPException(status_code=404, detail="Processing job not found")
        
        return APIResponse(
            success=True,
            data=job_data
        )
    
    @router.get("/progress", response_model=APIResponse)
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
    
    @router.delete("/progress/{job_id}", response_model=APIResponse)
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
    
    return router 