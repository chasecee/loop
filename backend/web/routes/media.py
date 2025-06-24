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
from .media_upload_v2 import process_media_upload_v2
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
        """Upload media files with v2 simplified processing."""
        # Log only once to prevent duplicates
        logger.info(f"🎬 Upload request: {len(files)} files")
        
        try:
            # Use new v2 processor - no jobs, no coordination, just works
            upload_result = await process_media_upload_v2(
                files, media_raw_dir, media_processed_dir, display_player
            )
            
            # Invalidate caches
            invalidate_storage_cache()
            invalidate_dashboard_cache()
            
            return APIResponse(
                success=upload_result["success"], 
                message=f"Processed {upload_result['processed']} files", 
                data={
                    "slug": upload_result["last_slug"],
                    "job_ids": []  # No jobs in v2 system
                }
            )
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
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
    
    # Legacy processing progress endpoints - now simplified since no jobs in v2
    
    @router.get("/progress/{job_id}", response_model=APIResponse)
    async def get_processing_progress(job_id: str):
        """Get processing progress - simplified for v2 (no jobs)."""
        # V2 system has no jobs, so always return completed
        return APIResponse(
            success=True,
            data={
                "job_id": job_id,
                "status": "completed", 
                "progress": 100,
                "stage": "completed",
                "message": "Upload completed (v2 system)"
            }
        )
    
    @router.get("/progress", response_model=APIResponse)
    async def get_all_processing_progress():
        """Get all processing jobs - simplified for v2."""
        # V2 system processes everything immediately, no jobs to track
        return APIResponse(
            success=True,
            data={"jobs": {}}
        )
    
    @router.delete("/progress/{job_id}", response_model=APIResponse)
    async def clear_processing_job(job_id: str):
        """Clear processing job - no-op in v2."""
        return APIResponse(
            success=True,
            message="No jobs to clear in v2 system"
        )
    
    return router 