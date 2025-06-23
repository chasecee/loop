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
    """Safely update both WebSocket and job record with comprehensive error handling."""
    # Always update job record first (source of truth)
    try:
        media_index.update_processing_job(job_id, progress, stage, message)
    except Exception as e:
        logger.error(f"CRITICAL: Failed to update job record {job_id}: {e}")
        # Don't raise - continue with broadcast attempt
    
    # Then attempt WebSocket broadcast (secondary)
    try:
        await broadcaster.processing_progress(job_id, {
            "progress": progress,
            "stage": stage,
            "message": message,
            "filename": filename
        })
    except Exception as e:
        logger.warning(f"Failed to broadcast progress for {job_id}: {e}")
        # Don't raise - job record is already updated


async def process_media_upload(
    files: List[UploadFile],
    media_raw_dir: Path,
    media_processed_dir: Path,
    display_player=None
) -> Dict[str, Any]:
    """Process uploaded media files with clean, simple logic."""
    
    if not files:
        logger.warning("Upload failed: No files provided")
        raise HTTPException(status_code=400, detail="No files provided")

    # Pre-validate all files
    total_size = 0
    for file in files:
        try:
            file_size = getattr(file, 'size', None)
            if file_size is None:
                content = await file.read()
                file_size = len(content)
                await file.seek(0)
            
            total_size += file_size
            
            if file_size > 250 * 1024 * 1024:  # 250MB limit per file
                raise HTTPException(status_code=413, detail=f"{file.filename} is too large (max 250 MB)")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error checking file size for {file.filename}: {e}")
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

    # Start progress overlay on display if we have jobs
    if display_player and job_ids and not display_player.showing_progress:
        try:
            display_player.start_processing_display(job_ids)
        except Exception as e:
            logger.warning(f"Failed to start processing display: {e}")

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
    """Process a single uploaded file with clean logic."""
    
    # Read file content
    try:
        content = await file.read()
        file_size = len(content)
    except Exception as e:
        logger.error(f"Failed to read file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")

    # Generate slug
    sanitized = Path(file.filename).stem.replace(" ", "_").lower()
    slug = f"{sanitized}_{uuid.uuid4().hex[:8]}"
    
    # Detect file type
    is_image = (file.content_type and file.content_type.startswith("image/")) or \
              file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'))
    is_zip = file.filename.lower().endswith(".zip")
    is_video = not is_image and not is_zip
    
    if is_image:
        return await process_image_file(file, content, slug, media_raw_dir, media_processed_dir)
    elif is_zip:
        return await process_zip_file(file, content, slug, media_raw_dir, media_processed_dir)
    elif is_video:
        return await process_video_file(file, content, slug, media_raw_dir, media_processed_dir)
    else:
        logger.warning(f"Unknown file type: {file.filename}")
        return None


async def process_image_file(file: UploadFile, content: bytes, slug: str, media_raw_dir: Path, media_processed_dir: Path) -> Dict[str, Any]:
    """Process image file - save for frontend preview, wait for ZIP frames."""
    
    # Create job for progress tracking
    job_id = str(uuid.uuid4())
    media_index.add_processing_job(job_id, file.filename)
    
    try:
        # 🚀 Safe progress update: uploading
        await _safe_progress_update(job_id, 0, "uploading", "Uploading image...", file.filename)
        
        # Save to raw directory for frontend preview
        raw_path = media_raw_dir / f"{slug}_{file.filename}"
        with open(raw_path, "wb") as f:
            f.write(content)
        
        # 🚀 Safe progress update: uploaded
        await _safe_progress_update(job_id, 30, "uploaded", "Image uploaded, waiting for frame data...", file.filename)
        
        # Create metadata (incomplete until frames arrive)
        metadata = {
            "slug": slug,
            "filename": file.filename,
            "type": file.content_type or "image/jpeg",
            "size": len(content),
            "uploadedAt": datetime.utcnow().isoformat() + "Z",
            "url": f"/media/raw/{slug}_{file.filename}",
            "processing_status": "processing",
        }
        
        # Add to media index
        media_index.add_media(metadata, make_active=True)
        
        # 🚀 CRITICAL: Broadcast upload (partial) via WebSocket
        try:
            await broadcaster.media_uploaded(metadata)
            logger.info(f"✅ Broadcasted image upload: {file.filename}")
        except Exception as e:
            logger.warning(f"Failed to broadcast image upload: {e}")
        
        return {"slug": slug, "job_id": job_id}
        
    except Exception as e:
        error_msg = f"Error processing image {file.filename}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # GUARANTEE job reaches terminal state
        try:
            media_index.complete_processing_job(job_id, False, error_msg)
            await broadcaster.processing_progress(job_id, {
                "progress": 0,
                "stage": "error",
                "message": error_msg,
                "filename": file.filename
            })
        except Exception as cleanup_error:
            logger.error(f"Failed to mark job {job_id} as error: {cleanup_error}")
            
        raise HTTPException(status_code=500, detail=error_msg)


async def process_video_file(file: UploadFile, content: bytes, slug: str, media_raw_dir: Path, media_processed_dir: Path) -> Dict[str, Any]:
    """Process video file - save for frontend preview, wait for ZIP frames."""
    
    # Create job for progress tracking
    job_id = str(uuid.uuid4())
    logger.info(f"🎬 STARTING process_video_file for {file.filename}, job_id: {job_id}")
    media_index.add_processing_job(job_id, file.filename)
    logger.info(f"🎬 Job {job_id} added to media index")
    
    try:
        logger.info(f"🎬 About to call _safe_progress_update for uploading - job {job_id}")
        # 🚀 Safe progress update: uploading
        await _safe_progress_update(job_id, 0, "uploading", "Uploading video...", file.filename)
        logger.info(f"🎬 Completed _safe_progress_update for uploading - job {job_id}")
        
        # Save to raw directory for frontend preview
        logger.info(f"🎬 About to save file to {media_raw_dir} - job {job_id}")
        raw_path = media_raw_dir / f"{slug}_{file.filename}"
        with open(raw_path, "wb") as f:
            f.write(content)
        logger.info(f"🎬 File saved to {raw_path} - job {job_id}")
        
        logger.info(f"🎬 About to call _safe_progress_update for uploaded - job {job_id}")
        # 🚀 Safe progress update: uploaded
        await _safe_progress_update(job_id, 30, "uploaded", "Video uploaded, waiting for frame data...", file.filename)
        logger.info(f"🎬 Completed _safe_progress_update for uploaded - job {job_id}")
        
        # Create metadata (incomplete until frames arrive)
        logger.info(f"🎬 Creating metadata - job {job_id}")
        metadata = {
            "slug": slug,
            "filename": file.filename,
            "type": file.content_type or "video/mp4",
            "size": len(content),
            "uploadedAt": datetime.utcnow().isoformat() + "Z",
            "url": f"/media/raw/{slug}_{file.filename}",
            "processing_status": "processing",
        }
        
        # Add to media index
        logger.info(f"🎬 Adding metadata to media index - job {job_id}")
        media_index.add_media(metadata, make_active=True)
        logger.info(f"🎬 Metadata added to media index - job {job_id}")
        
        # 🚀 CRITICAL: Broadcast upload (partial) via WebSocket
        try:
            logger.info(f"🎬 Broadcasting media upload - job {job_id}")
            await broadcaster.media_uploaded(metadata)
            logger.info(f"✅ Broadcasted video upload: {file.filename}")
        except Exception as e:
            logger.warning(f"Failed to broadcast video upload: {e}")
        
        logger.info(f"🎬 COMPLETING process_video_file successfully - job {job_id}")
        return {"slug": slug, "job_id": job_id}
        
    except Exception as e:
        error_msg = f"Error processing video {file.filename}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        logger.error(f"🎬 EXCEPTION in process_video_file - job {job_id}: {e}")
        
        # GUARANTEE job reaches terminal state
        try:
            media_index.complete_processing_job(job_id, False, error_msg)
            await broadcaster.processing_progress(job_id, {
                "progress": 0,
                "stage": "error",
                "message": error_msg,
                "filename": file.filename
            })
        except Exception as cleanup_error:
            logger.error(f"Failed to mark job {job_id} as error: {cleanup_error}")
            
        raise HTTPException(status_code=500, detail=error_msg)


async def process_zip_file(file: UploadFile, content: bytes, slug: str, media_raw_dir: Path, media_processed_dir: Path) -> Dict[str, Any]:
    """Process ZIP file - extract frames and either create new media or update existing video."""
    
    # Create job for progress tracking (will coordinate with existing jobs later)
    job_id = str(uuid.uuid4())
    media_index.add_processing_job(job_id, file.filename)
    logger.info(f"📦 ZIP processing started with job: {job_id[:8]}")
    
    try:
        # 🚀 Safe progress update: extracting
        await _safe_progress_update(job_id, 0, "extracting", "Starting frame extraction...", file.filename)
        
        # Extract ZIP to get metadata
        zip_metadata = await extract_zip_frames(content, slug, media_processed_dir, job_id)
        original_filename = zip_metadata.get("original_filename", file.filename)
        
        # Check if we have an existing video for these frames
        # Use the original filename from ZIP metadata, not the ZIP filename
        zip_original_filename = zip_metadata.get("original_filename", original_filename)
        logger.info(f"🔍 Looking for existing media with filename: {zip_original_filename}")
        
        existing_media = None
        all_media = media_index.list_media()
        for media_item in all_media:
            if (media_item.get("filename") == zip_original_filename and 
                media_item.get("processing_status") == "processing"):
                existing_media = media_item
                logger.info(f"🎯 Found existing media: {media_item.get('slug')} for {zip_original_filename}")
                break
        
        if existing_media:
            # Update existing video/image entry with frame data
            existing_slug = existing_media["slug"]
            
            # 🔗 CRITICAL: Find the original video job and complete IT, not the ZIP job
            original_video_job_id = None
            all_jobs = media_index.list_processing_jobs()
            for jid, job_data in all_jobs.items():
                if (job_data.get('filename') == zip_original_filename and 
                    job_data.get('status') == 'processing'):
                    original_video_job_id = jid
                    logger.info(f"🎯 Found original video job to complete: {jid[:8]} for {zip_original_filename}")
                    break
            
            # Use the original video job ID for progress updates
            progress_job_id = original_video_job_id or job_id
            
            # 🚀 Safe progress update: finalizing
            await _safe_progress_update(progress_job_id, 90, "finalizing", f"Updating {zip_metadata.get('type', 'media')} with frame data...", zip_original_filename)
            
            # Move frames to existing directory if different
            if slug != existing_slug:
                current_dir = media_processed_dir / slug
                target_dir = media_processed_dir / existing_slug
                
                if current_dir.exists():
                    if target_dir.exists():
                        shutil.rmtree(target_dir)
                    current_dir.rename(target_dir)
            
            # Update metadata
            updated_metadata = existing_media.copy()
            updated_metadata.update({
                "frame_count": zip_metadata.get("frame_count", 1),
                "width": zip_metadata.get("width", 320),
                "height": zip_metadata.get("height", 240),
                "processing_status": "completed",
            })
            
            media_index.add_media(updated_metadata, make_active=False)
            
            # Complete the ORIGINAL video job, not the ZIP job
            if original_video_job_id:
                media_index.complete_processing_job(original_video_job_id, True, "")
                logger.info(f"✅ Completed original video job: {original_video_job_id[:8]}")
                
                # Clean up ZIP job if it's different
                if job_id != original_video_job_id:
                    media_index.complete_processing_job(job_id, True, "")
                    logger.info(f"🧹 Cleaned up ZIP job: {job_id[:8]}")
            else:
                media_index.complete_processing_job(job_id, True, "")
                logger.warning(f"⚠️ No original video job found, completed ZIP job: {job_id[:8]}")
            
            # 🚀 Final broadcast: completion
            try:
                await broadcaster.processing_progress(progress_job_id, {
                    "progress": 100,
                    "stage": "complete",
                    "message": f"{zip_metadata.get('type', 'Media').title()} processing complete!",
                    "filename": zip_original_filename
                })
            except Exception as e:
                logger.warning(f"Failed to broadcast completion: {e}")
            
            # 🚀 CRITICAL: Broadcast update via WebSocket
            try:
                await broadcaster.media_uploaded(updated_metadata)
                logger.info(f"✅ Broadcasted {zip_metadata.get('type', 'media')} update: {zip_original_filename}")
            except Exception as e:
                logger.warning(f"Failed to broadcast media update: {e}")
            
            # Return the original video job ID so display progress tracking works
            return {"slug": existing_slug, "job_id": original_video_job_id or job_id}
            
        else:
            # Create new ZIP-only media entry (image or video)
            # 🚀 Safe progress update: finalizing
            await _safe_progress_update(job_id, 90, "finalizing", f"Creating new {zip_metadata.get('type', 'media')} entry...", original_filename)
            
            metadata = {
                "slug": slug,
                "filename": original_filename,
                "type": zip_metadata.get("type", "video"),  # Use type from metadata
                "size": len(content),
                "uploadedAt": datetime.utcnow().isoformat() + "Z",
                "url": None,  # No preview for ZIP-only uploads
                "frame_count": zip_metadata.get("frame_count", 1),
                "width": zip_metadata.get("width", 320),
                "height": zip_metadata.get("height", 240),
                "processing_status": "completed",
            }
            
            media_index.add_media(metadata, make_active=True)
            media_index.complete_processing_job(job_id, True, "")
            
            # 🚀 Final broadcast: completion
            try:
                await broadcaster.processing_progress(job_id, {
                    "progress": 100,
                    "stage": "complete",
                    "message": f"ZIP processing complete!",
                    "filename": original_filename
                })
            except Exception as e:
                logger.warning(f"Failed to broadcast completion: {e}")
            
            # 🚀 CRITICAL: Broadcast upload via WebSocket
            try:
                await broadcaster.media_uploaded(metadata)
                logger.info(f"✅ Broadcasted ZIP upload: {original_filename}")
            except Exception as e:
                logger.warning(f"Failed to broadcast ZIP upload: {e}")
            
            return {"slug": slug, "job_id": job_id}
        
    except Exception as e:
        error_msg = f"Error processing ZIP {file.filename}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # GUARANTEE job reaches terminal state
        try:
            media_index.complete_processing_job(job_id, False, error_msg)
            await broadcaster.processing_progress(job_id, {
                "progress": 0,
                "stage": "error",
                "message": error_msg,
                "filename": file.filename
            })
        except Exception as cleanup_error:
            logger.error(f"Failed to mark job {job_id} as error: {cleanup_error}")
            
        raise HTTPException(status_code=500, detail=error_msg)


async def extract_zip_frames(content: bytes, slug: str, media_processed_dir: Path, job_id: str) -> Dict[str, Any]:
    """Extract ZIP frames to processed directory."""
    
    import zipfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_zip = Path(tmpdir) / "upload.zip"
        
        with open(tmp_zip, "wb") as f:
            f.write(content)

        with zipfile.ZipFile(tmp_zip, "r") as zf:
            members = zf.namelist()
            
            if "metadata.json" not in members:
                raise HTTPException(status_code=400, detail="metadata.json missing in upload")
            
            meta_data = json.loads(zf.read("metadata.json").decode())
            output_dir = media_processed_dir / slug
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract all files with robust progress tracking
            total_members = len(members)
            logger.info(f"Extracting {total_members} files from ZIP...")
            
            for idx, member in enumerate(members):
                zf.extract(member, output_dir)
                
                # Broadcast progress every 25 files or at completion
                if idx % 25 == 0 or idx == total_members - 1:
                    progress = 10 + (idx / total_members) * 70  # 10-80% during extraction
                    
                    # 🚀 Safe progress update during extraction
                    await _safe_progress_update(
                        job_id, 
                        progress, 
                        "extracting", 
                        f"Extracted {idx+1}/{total_members} frames...", 
                        meta_data.get("original_filename", "unknown")
                    )

            # Ensure frames are in frames/ directory
            frames_dir = output_dir / "frames"
            if not frames_dir.exists():
                frame_files = list(output_dir.glob("*.rgb")) + list(output_dir.glob("*.png")) + list(output_dir.glob("*.jpg"))
                if frame_files:
                    frames_dir.mkdir(exist_ok=True)
                    for frame_file in frame_files:
                        frame_file.rename(frames_dir / frame_file.name)
            
            # 🚀 Safe progress update: organizing
            await _safe_progress_update(
                job_id, 
                80, 
                "organizing", 
                "Organizing frame files...", 
                meta_data.get("original_filename", "unknown")
            )
            
            return meta_data 