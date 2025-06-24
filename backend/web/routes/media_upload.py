"""Clean media upload processing for LOOP web server."""

import json
import shutil
import tempfile
import uuid
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import UploadFile, HTTPException

from utils.media_index import media_index
from utils.logger import get_logger
from ..core.events import broadcaster

logger = get_logger("web.media")

async def _safe_progress_update(job_id: str, progress: float, stage: str, message: str, filename: str) -> None:
    """Update job progress with error handling."""
    # Always update job record first (critical)
    try:
        media_index.update_processing_job(job_id, progress, stage, message)
        logger.info(f"✅ Job record updated: {job_id[:8]} -> {progress}% ({stage})")
    except Exception as e:
        logger.error(f"CRITICAL: Failed to update job record {job_id}: {e}")
        raise  # Don't continue if job record fails
    
    # Then attempt WebSocket broadcast (secondary, but important)
    try:
        await broadcaster.processing_progress(job_id, {
            "progress": progress,
            "stage": stage,
            "message": message,
            "filename": filename
        })
        logger.info(f"📡 WebSocket broadcast sent: {job_id[:8]} -> {progress}% ({stage})")
    except Exception as e:
        logger.error(f"WebSocket broadcast failed for {job_id}: {e}")
        # Don't raise - job record is already updated


async def process_media_upload(
    files: List[UploadFile],
    media_raw_dir: Path,
    media_processed_dir: Path,
    display_player=None
) -> Dict[str, Any]:
    """Process uploaded media files with simplified logic."""
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Pre-validate all files
    total_size = 0
    for file in files:
        try:
            content = await file.read()
            file_size = len(content)
            await file.seek(0)
            total_size += file_size
            
            if file_size > 250 * 1024 * 1024:  # 250MB limit per file
                raise HTTPException(status_code=413, detail=f"{file.filename} is too large (max 250 MB)")
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing {file.filename}")

    if total_size > 500 * 1024 * 1024:  # 500MB total limit
        raise HTTPException(status_code=413, detail="Total upload size exceeds 500MB limit")

    processed_media = []
    job_ids = []

    for file in files:
        try:
            result = await process_single_file(file, media_raw_dir, media_processed_dir, display_player)
            if result:
                processed_media.append(result)
                if result.get('job_id'):
                    job_ids.append(result['job_id'])
        except Exception as e:
            logger.error(f"Failed to process {file.filename}: {e}")
            continue

    # Start progress display for active jobs
    if display_player and job_ids:
        display_player.start_processing_display(job_ids)

    # Refresh player display
    if display_player and processed_media:
        def refresh_player_async():
            try:
                display_player.refresh_media_list()
                if processed_media:
                    last_slug = processed_media[-1].get('slug')
                    if last_slug:
                        display_player.set_active_media(last_slug)
            except Exception as exc:
                logger.warning(f"Failed to refresh player after upload: {exc}")
        
        import threading
        refresh_thread = threading.Thread(target=refresh_player_async, daemon=True)
        refresh_thread.start()

    return {
        "slug": processed_media[-1]['slug'] if processed_media else None, 
        "job_ids": job_ids
    }


async def process_single_file(file: UploadFile, media_raw_dir: Path, media_processed_dir: Path, display_player=None) -> Optional[Dict[str, Any]]:
    """Process a single uploaded file with simplified logic."""
    
    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")

    # Generate slug
    sanitized = Path(file.filename).stem.replace(" ", "_").lower()
    slug = f"{sanitized}_{uuid.uuid4().hex[:8]}"
    
    # Detect file type
    is_zip = file.filename.lower().endswith(".zip")
    
    if is_zip:
        return await process_zip_file(file, content, slug, media_raw_dir, media_processed_dir)
    else:
        return await process_media_file(file, content, slug, media_raw_dir, media_processed_dir)


async def process_media_file(file: UploadFile, content: bytes, slug: str, media_raw_dir: Path, media_processed_dir: Path) -> Dict[str, Any]:
    """Process image/video file - ONE job for the entire lifecycle."""
    
    # Create ONE job for this media
    job_id = str(uuid.uuid4())
    media_index.add_processing_job(job_id, file.filename)
    logger.info(f"🎬 Processing {file.filename} with job {job_id[:8]}")
    
    try:
        # Step 1: Upload (0-30%)
        await _safe_progress_update(job_id, 10, "uploading", "Uploading media...", file.filename)
        
        # Save to raw directory
        raw_path = media_raw_dir / f"{slug}_{file.filename}"
        with open(raw_path, "wb") as f:
            f.write(content)
        
        await _safe_progress_update(job_id, 30, "uploaded", "Media uploaded, waiting for frames...", file.filename)
        
        # Create metadata
        metadata = {
            "slug": slug,
            "filename": file.filename,
            "type": file.content_type or ("video/mp4" if file.filename.lower().endswith(('.mov', '.mp4')) else "image/jpeg"),
            "size": len(content),
            "uploadedAt": datetime.utcnow().isoformat() + "Z",
            "url": f"/media/raw/{slug}_{file.filename}",
            "processing_status": "processing",
        }
        
        # Add to media index
        media_index.add_media(metadata, make_active=True)
        
        # Broadcast upload
        await broadcaster.media_uploaded(metadata)
        logger.info(f"✅ Media uploaded: {file.filename}")
        
        return {"slug": slug, "job_id": job_id}
        
    except Exception as e:
        error_msg = f"Error processing {file.filename}: {str(e)}"
        logger.error(error_msg)
        media_index.complete_processing_job(job_id, False, error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


async def process_zip_file(file: UploadFile, content: bytes, slug: str, media_raw_dir: Path, media_processed_dir: Path) -> Dict[str, Any]:
    """Process ZIP file - find original job and complete it."""
    
    try:
        # Extract ZIP metadata first
        zip_metadata = await extract_zip_frames(content, slug, media_processed_dir)
        original_filename = zip_metadata.get("original_filename", file.filename.replace(".zip", ""))
        
        # Find the original media job
        original_job_id = None
        original_slug = None
        
        # Look for existing media with matching filename
        all_media = media_index.list_media()
        for media_item in all_media:
            if (media_item.get("filename") == original_filename and 
                media_item.get("processing_status") == "processing"):
                original_slug = media_item.get("slug")
                break
        
        # Find the job for this media
        if original_slug:
            all_jobs = media_index.list_processing_jobs()
            for jid, job_data in all_jobs.items():
                if job_data.get('filename') == original_filename:
                    original_job_id = jid
                    break
        
        if not original_job_id:
            logger.warning(f"No original job found for ZIP {file.filename}")
            return None
        
        logger.info(f"🎯 ZIP completing original job {original_job_id[:8]} for {original_filename}")
        
        # Update progress - frames processing
        await _safe_progress_update(original_job_id, 70, "processing", "Processing frames...", original_filename)
        
        # Move frames to correct directory if needed
        if slug != original_slug:
            current_dir = media_processed_dir / slug
            target_dir = media_processed_dir / original_slug
            
            if current_dir.exists():
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                current_dir.rename(target_dir)
        
        # Update metadata
        existing_media = None
        for media_item in all_media:
            if media_item.get("slug") == original_slug:
                existing_media = media_item
                break
        
        if existing_media:
            updated_metadata = existing_media.copy()
            updated_metadata.update({
                "frame_count": zip_metadata.get("frame_count", 1),
                "width": zip_metadata.get("width", 320),
                "height": zip_metadata.get("height", 240),
                "processing_status": "completed",
            })
            
            media_index.add_media(updated_metadata, make_active=False)
        
        # Complete the job
        await _safe_progress_update(original_job_id, 100, "complete", "Processing complete!", original_filename)
        media_index.complete_processing_job(original_job_id, True, "")
        
        # Broadcast completion
        await broadcaster.media_uploaded(updated_metadata)
        logger.info(f"✅ ZIP processing complete for {original_filename}")
        
        return {"slug": original_slug, "job_id": original_job_id}
        
    except Exception as e:
        error_msg = f"Error processing ZIP {file.filename}: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


async def extract_zip_frames(content: bytes, slug: str, media_processed_dir: Path) -> Dict[str, Any]:
    """Extract ZIP frames to processed directory."""
    
    import zipfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_zip = Path(tmpdir) / "upload.zip"
        
        with open(tmp_zip, "wb") as f:
            f.write(content)

        with zipfile.ZipFile(tmp_zip, "r") as zf:
            members = zf.namelist()
            
            if "metadata.json" not in members:
                raise HTTPException(status_code=400, detail="metadata.json missing in ZIP")
            
            meta_data = json.loads(zf.read("metadata.json").decode())
            output_dir = media_processed_dir / slug
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract all files
            for member in members:
                zf.extract(member, output_dir)
            
            # Ensure frames are in frames/ directory
            frames_dir = output_dir / "frames"
            if not frames_dir.exists():
                frame_files = list(output_dir.glob("*.rgb")) + list(output_dir.glob("*.png")) + list(output_dir.glob("*.jpg"))
                if frame_files:
                    frames_dir.mkdir(exist_ok=True)
                    for frame_file in frame_files:
                        frame_file.rename(frames_dir / frame_file.name)
            
            return meta_data 