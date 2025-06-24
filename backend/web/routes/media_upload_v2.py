"""SIMPLIFIED media upload processing - rebuilt from scratch for reliability."""

import json
import shutil
import tempfile
import uuid
import asyncio
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import UploadFile, HTTPException

from utils.media_index import media_index
from utils.logger import get_logger
from ..core.events import broadcaster

logger = get_logger("web.media_v2")

# Global upload deduplication
_active_uploads: Dict[str, str] = {}  # content_hash -> job_id
_upload_lock = asyncio.Lock()

async def process_media_upload_v2(
    files: List[UploadFile],
    media_raw_dir: Path,
    media_processed_dir: Path,
    display_player=None
) -> Dict[str, Any]:
    """Simplified, bulletproof media upload processing."""
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Remove duplicate logging - main router already logs this
    # logger.info(f"🎬 Processing {len(files)} files")
    
    # Notify display of upload start
    if display_player:
        try:
            display_player.notify_upload_start(len(files))
        except Exception:
            pass
    
    # Process each file independently - no coordination needed
    results = []
    for file in files:
        try:
            # Notify processing of current file
            if display_player:
                try:
                    display_player.notify_processing(file.filename)
                except Exception:
                    pass
            
            result = await process_single_file_v2(file, media_raw_dir, media_processed_dir)
            if result:
                results.append(result)
        except Exception as e:
            logger.error(f"Failed to process {file.filename}: {e}")
            # Show error on display
            if display_player:
                try:
                    display_player.notify_error(f"Upload failed: {file.filename}")
                except Exception:
                    pass
            continue
    
    # Refresh display if we got anything
    if results and display_player:
        try:
            display_player.refresh_media_list()
            # Set last uploaded as active
            if results:
                display_player.set_active_media(results[-1]['slug'])
        except Exception as e:
            logger.warning(f"Display refresh failed: {e}")
    
    return {
        "success": len(results) > 0,
        "processed": len(results),
        "last_slug": results[-1]['slug'] if results else None
    }


async def process_single_file_v2(file: UploadFile, media_raw_dir: Path, media_processed_dir: Path) -> Optional[Dict[str, Any]]:
    """Process a single file with deduplication and simple logic."""
    
    # Read file content once
    try:
        content = await file.read()
        file_size = len(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read {file.filename}: {e}")
    
    # File size validation
    if file_size > 100 * 1024 * 1024:  # 100MB limit
        raise HTTPException(status_code=413, detail=f"{file.filename} too large (max 100MB)")
    
    # Calculate content hash for deduplication
    content_hash = hashlib.sha256(content).hexdigest()[:16]
    
    async with _upload_lock:
        # Check for duplicate upload
        if content_hash in _active_uploads:
            existing_job = _active_uploads[content_hash]
            logger.info(f"🔄 Duplicate upload detected: {file.filename} (hash: {content_hash})")
            return {"slug": existing_job, "status": "duplicate"}
        
        # Reserve this upload
        _active_uploads[content_hash] = content_hash  # Will be updated with actual slug
    
    try:
        # Generate slug
        sanitized = Path(file.filename).stem.replace(" ", "_").lower()
        slug = f"{sanitized}_{content_hash}"
        
        # Update reservation with actual slug
        async with _upload_lock:
            _active_uploads[content_hash] = slug
        
        # Determine file type and processing strategy
        is_zip = file.filename.lower().endswith(".zip")
        
        if is_zip:
            return await process_zip_v2(file, content, slug, media_processed_dir)
        else:
            return await process_media_v2(file, content, slug, media_raw_dir)
    
    finally:
        # Always clean up reservation
        async with _upload_lock:
            _active_uploads.pop(content_hash, None)


async def process_media_v2(file: UploadFile, content: bytes, slug: str, media_raw_dir: Path) -> Dict[str, Any]:
    """Process regular media file (image/video) - no jobs, just direct processing."""
    
    # Reduce logging verbosity - main router already logs the request
    logger.debug(f"📁 Processing media: {file.filename} -> {slug}")
    
    # Save file
    raw_path = media_raw_dir / f"{slug}_{file.filename}"
    with open(raw_path, "wb") as f:
        f.write(content)
    
    # Create metadata
    metadata = {
        "slug": slug,
        "filename": file.filename,
        "type": file.content_type or _detect_content_type(file.filename),
        "size": len(content),
        "uploadedAt": datetime.utcnow().isoformat() + "Z",
        "url": f"/media/raw/{slug}_{file.filename}",
        "processing_status": "uploaded",  # Just uploaded, no processing needed
        "frame_count": 1,  # Default for images
        "width": 320,
        "height": 240
    }
    
    # Add to media index
    media_index.add_media(metadata, make_active=True)
    
    # Broadcast to dashboard
    await broadcaster.media_uploaded(metadata)
    
    # Only log completion, not processing start
    logger.info(f"✅ Media uploaded: {file.filename}")
    
    return {"slug": slug, "status": "uploaded"}


async def process_zip_v2(file: UploadFile, content: bytes, slug: str, media_processed_dir: Path) -> Dict[str, Any]:
    """Process ZIP file with frames - complete self-contained processing."""
    
    # Reduce logging verbosity
    logger.debug(f"📦 Processing ZIP: {file.filename} -> {slug}")
    
    try:
        # Extract ZIP and get metadata
        metadata = await extract_zip_frames_v2(content, slug, media_processed_dir)
        
        # Add to media index
        media_index.add_media(metadata, make_active=True)
        
        # Broadcast completion
        await broadcaster.media_uploaded(metadata)
        
        # Only log completion
        logger.info(f"✅ ZIP processed: {file.filename}")
        
        return {"slug": slug, "status": "completed"}
        
    except Exception as e:
        logger.error(f"ZIP processing failed: {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"ZIP processing failed: {e}")


async def extract_zip_frames_v2(content: bytes, slug: str, media_processed_dir: Path) -> Dict[str, Any]:
    """Extract ZIP frames and return complete metadata."""
    
    import zipfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_zip = Path(tmpdir) / "upload.zip"
        
        # Write ZIP content
        with open(tmp_zip, "wb") as f:
            f.write(content)
        
        # Extract ZIP
        with zipfile.ZipFile(tmp_zip, "r") as zf:
            members = zf.namelist()
            
            if "metadata.json" not in members:
                raise ValueError("metadata.json missing in ZIP")
            
            # Read metadata
            zip_metadata = json.loads(zf.read("metadata.json").decode())
            
            # Create output directory
            output_dir = media_processed_dir / slug
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract all files
            zf.extractall(output_dir)
            
            # Organize frames if needed
            frames_dir = output_dir / "frames"
            if not frames_dir.exists():
                # Look for loose frame files
                frame_files = (
                    list(output_dir.glob("*.rgb")) + 
                    list(output_dir.glob("*.png")) + 
                    list(output_dir.glob("*.jpg"))
                )
                if frame_files:
                    frames_dir.mkdir(exist_ok=True)
                    for frame_file in frame_files:
                        frame_file.rename(frames_dir / frame_file.name)
    
    # Build complete metadata
    return {
        "slug": slug,
        "filename": zip_metadata.get("original_filename", f"{slug}.zip"),
        "type": zip_metadata.get("type", "video/mp4"),
        "size": len(content),
        "uploadedAt": datetime.utcnow().isoformat() + "Z",
        "url": f"/media/raw/{slug}_original",  # Will be updated when original arrives
        "processing_status": "completed",
        "frame_count": zip_metadata.get("frame_count", 1),
        "width": zip_metadata.get("width", 320),
        "height": zip_metadata.get("height", 240)
    }


def _detect_content_type(filename: str) -> str:
    """Simple content type detection."""
    ext = Path(filename).suffix.lower()
    if ext in ['.mp4', '.mov', '.m4v']:
        return 'video/mp4'
    elif ext in ['.jpg', '.jpeg']:
        return 'image/jpeg'
    elif ext in ['.png']:
        return 'image/png'
    elif ext in ['.gif']:
        return 'image/gif'
    else:
        return 'application/octet-stream' 