"""Media upload processing utilities for LOOP web server."""

import json
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from typing import List
from datetime import datetime

from fastapi import UploadFile, HTTPException

from utils.media_index import media_index
from utils.logger import get_logger

logger = get_logger("web.media")

async def process_media_upload(
    files: List[UploadFile],
    media_raw_dir: Path,
    media_processed_dir: Path,
    display_player=None
):
    """Process uploaded media files (ZIP + video)."""
    
    if not files:
        logger.warning("Upload failed: No files provided")
        raise HTTPException(status_code=400, detail="No files provided")

    # Pre-validate all files before processing any
    total_size = 0
    for file in files:
        # Check file size without reading full content first
        try:
            file_size = getattr(file, 'size', None)
            if file_size is None:
                content = await file.read()
                file_size = len(content)
                await file.seek(0)
            
            total_size += file_size
            logger.info(f"File {file.filename}: {file_size} bytes")
            
            if file_size > 250 * 1024 * 1024:  # 250MB limit per file
                logger.warning(f"File {file.filename} too large: {file_size} bytes")
                raise HTTPException(status_code=413, detail=f"{file.filename} is too large (max 250 MB)")
                
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

    def process_zip_content_sync(zip_path, filename, slug, job_id):
        """Extract ZIP content synchronously (for background processing)."""
        import zipfile
        
        with zipfile.ZipFile(zip_path, "r") as zf:
            members = zf.namelist()
            
            if "metadata.json" not in members:
                logger.error(f"ZIP file {filename} missing metadata.json")
                raise ValueError("metadata.json missing in upload")
            
            meta_data = json.loads(zf.read("metadata.json").decode())
            output_dir = media_processed_dir / slug
            logger.info(f"Extracting ZIP to: {output_dir}")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract all files with progress updates
            total_members = len(members)
            logger.info(f"Extracting {total_members} files from ZIP...")
            for idx, member in enumerate(members):
                zf.extract(member, output_dir)
                
                # Update progress every 50 files or at completion
                if idx % 50 == 0 or idx == total_members - 1:
                    progress = 10 + (idx / total_members) * 80  # 10-90% during extraction
                    logger.info(f"Extracted {idx+1}/{total_members} files")
                    
                    # Update progress
                    try:
                        media_index.update_processing_job(job_id, progress, "extracting", f"Extracted {idx+1}/{total_members} frames...")
                    except Exception:
                        pass  # Don't fail extraction on progress update errors

            # Ensure frames are in frames/ directory
            frames_dir = output_dir / "frames"
            if not frames_dir.exists():
                logger.warning(f"Frames directory not found, creating it")
                frame_files = list(output_dir.glob("*.rgb")) + list(output_dir.glob("*.png")) + list(output_dir.glob("*.jpg"))
                if frame_files:
                    frames_dir.mkdir(exist_ok=True)
                    for frame_file in frame_files:
                        frame_file.rename(frames_dir / frame_file.name)
                    logger.info(f"Moved {len(frame_files)} frame files to frames/ directory")
                else:
                    logger.warning(f"No frame files found in {output_dir}")
            else:
                frame_count = len(list(frames_dir.glob('*')))
                logger.info(f"Frames directory exists with {frame_count} files")
            
            return meta_data

    async def process_zip_content(content, filename, slug, job_id):
        """Extract ZIP content and store frames."""
        import zipfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_zip = Path(tmpdir) / "upload.zip"
            
            with open(tmp_zip, "wb") as f:
                f.write(content)

            with zipfile.ZipFile(tmp_zip, "r") as zf:
                members = zf.namelist()
                
                if "metadata.json" not in members:
                    logger.error(f"ZIP file {filename} missing metadata.json")
                    raise HTTPException(status_code=400, detail="metadata.json missing in upload")
                
                meta_data = json.loads(zf.read("metadata.json").decode())
                output_dir = media_processed_dir / slug
                logger.info(f"Extracting ZIP to: {output_dir}")
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Extract all files with progress updates
                total_members = len(members)
                logger.info(f"Extracting {total_members} files from ZIP...")
                for idx, member in enumerate(members):
                    zf.extract(member, output_dir)
                    
                    # Update progress every 50 files or at completion
                    if idx % 50 == 0 or idx == total_members - 1:
                        progress = 50 + (idx / total_members) * 35  # 50-85% during extraction
                        logger.info(f"Extracted {idx+1}/{total_members} files")
                        
                        # Update progress if we have a job_id
                        if job_id:
                            try:
                                media_index.update_processing_job(job_id, progress, "extracting", f"Extracted {idx+1}/{total_members} frames...")
                            except Exception:
                                pass  # Don't fail extraction on progress update errors

                # Ensure frames are in frames/ directory
                frames_dir = output_dir / "frames"
                if not frames_dir.exists():
                    logger.warning(f"Frames directory not found, creating it")
                    frame_files = list(output_dir.glob("*.rgb")) + list(output_dir.glob("*.png")) + list(output_dir.glob("*.jpg"))
                    if frame_files:
                        frames_dir.mkdir(exist_ok=True)
                        for frame_file in frame_files:
                            frame_file.rename(frames_dir / frame_file.name)
                        logger.info(f"Moved {len(frame_files)} frame files to frames/ directory")
                    else:
                        logger.warning(f"No frame files found in {output_dir}")
                else:
                    frame_count = len(list(frames_dir.glob('*')))
                    logger.info(f"Frames directory exists with {frame_count} files")
                
                return meta_data

    async def process_single_file(file, job_ids, slugs):
        """Process a single file."""
        logger.info(f"Processing single file: {file.filename} ({file.content_type})")
        
        # Read file content
        logger.info(f"Reading uploaded file {file.filename}...")
        read_start = time.time()
        try:
            content = await file.read()
            file_size = len(content)
            read_time = time.time() - read_start
            speed_mbps = (file_size / (1024 * 1024)) / read_time if read_time > 0 else 0
            logger.info(f"File {file.filename} read successfully: {file_size} bytes ({speed_mbps:.1f} MB/s in {read_time:.2f}s)")
        except Exception as e:
            read_time = time.time() - read_start
            logger.error(f"Failed to read file {file.filename} after {read_time:.2f}s: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")

        # Create a slug based on filename + uuid to avoid clashes
        sanitized = Path(file.filename).stem.replace(" ", "_").lower()
        slug = f"{sanitized}_{uuid.uuid4().hex[:8]}"
        logger.info(f"Generated slug for {file.filename}: {slug}")

        # Register lightweight upload job for progress UI
        job_id = str(uuid.uuid4())
        job_ids.append(job_id)
        logger.info(f"Created processing job {job_id} for {file.filename}")
        media_index.add_processing_job(job_id, file.filename)

        try:
            if file.filename.lower().endswith(".zip"):
                # Process ZIP file asynchronously (frames for hardware display)
                import threading
                
                # Save ZIP content to temp file first
                temp_zip_path = media_processed_dir / f"temp_{slug}.zip"
                with open(temp_zip_path, "wb") as f:
                    f.write(content)
                
                # Start async processing
                def process_zip_async():
                    try:
                        # Update progress to show ZIP processing started
                        media_index.update_processing_job(job_id, 10, "extracting", "Starting ZIP extraction...")
                        
                        # Process the ZIP
                        zip_metadata = process_zip_content_sync(temp_zip_path, file.filename, slug, job_id)
                        original_filename = zip_metadata.get("original_filename", file.filename)
                
                        # Check if we already have a media entry for this video
                        existing_media = None
                        all_media = media_index.list_media()
                        for media_item in all_media:
                            if media_item.get("filename") == original_filename:
                                existing_media = media_item
                                break
                        
                        if existing_media:
                            # Update existing entry with frame data (phase 2 of upload)
                            logger.info(f"Updating existing media entry for {original_filename} (phase 2 of upload)")
                            existing_slug = existing_media["slug"]
                            
                            # Move frames to existing directory
                            existing_output_dir = media_processed_dir / existing_slug
                            current_output_dir = media_processed_dir / slug
                            
                            if current_output_dir.exists() and current_output_dir != existing_output_dir:
                                existing_frames_dir = existing_output_dir / "frames"
                                current_frames_dir = current_output_dir / "frames"
                                
                                if current_frames_dir.exists():
                                    if existing_frames_dir.exists():
                                        shutil.rmtree(existing_frames_dir)
                                    existing_frames_dir.mkdir(parents=True, exist_ok=True)
                                    
                                    # Move all frame files
                                    frame_files = list(current_frames_dir.glob("*"))
                                    for frame_file in frame_files:
                                        target_file = existing_frames_dir / frame_file.name
                                        frame_file.rename(target_file)
                                    
                                    logger.info(f"Moved {len(frame_files)} frame files to existing directory")
                                
                                # Clean up temporary directory
                                shutil.rmtree(current_output_dir)
                            
                            # Update media entry with frame info
                            updated_meta = existing_media.copy()
                            updated_meta.update({
                                "frame_count": zip_metadata.get("frame_count", 510),
                                "width": zip_metadata.get("width", 320),
                                "height": zip_metadata.get("height", 240),
                                "processing_status": "completed",
                            })
                            
                            media_index.add_media(updated_meta, make_active=False)
                            
                            # Complete processing job
                            media_index.update_processing_job(job_id, 100, "complete", "Upload and processing finished!")
                            media_index.complete_processing_job(job_id, True, "")
                        
                        else:
                            # Create new entry (ZIP-only upload)
                            meta_data = {
                                "slug": slug,
                                "filename": original_filename,
                                "type": "video",
                                "size": temp_zip_path.stat().st_size,
                                "uploadedAt": datetime.utcnow().isoformat() + "Z",
                                "url": None,
                                "frame_count": zip_metadata.get("frame_count", 510),
                                "width": zip_metadata.get("width", 320),
                                "height": zip_metadata.get("height", 240),
                                "processing_status": "completed",
                            }
                            
                            media_index.add_media(meta_data, make_active=True)
                            
                            media_index.update_processing_job(job_id, 100, "complete", "ZIP processing complete!")
                            media_index.complete_processing_job(job_id, True)
                        
                        # Clean up temp file
                        if temp_zip_path.exists():
                            temp_zip_path.unlink()
                            
                    except Exception as e:
                        error_msg = f"Error processing ZIP {file.filename}: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        media_index.complete_processing_job(job_id, False, error_msg)
                        # Clean up temp file on error
                        if temp_zip_path.exists():
                            temp_zip_path.unlink()
                
                # Start async processing thread
                processing_thread = threading.Thread(target=process_zip_async, daemon=True)
                processing_thread.start()
                
                # Return immediately - don't wait for ZIP processing
                slugs.append(slug)
                
                # Create placeholder media entry that will be updated when processing completes
                temp_metadata = {
                    "slug": slug,
                    "filename": file.filename,
                    "type": "video",
                    "size": file_size,
                    "uploadedAt": datetime.utcnow().isoformat() + "Z",
                    "url": None,
                    "processing_status": "processing",
                }
                
                # Check if this is updating an existing video
                existing_media = None
                all_media = media_index.list_media()
                original_filename = file.filename.replace('.zip', '').replace('-1', '')  # Basic cleanup
                for media_item in all_media:
                    if original_filename in media_item.get("filename", ""):
                        existing_media = media_item
                        break
                
                if existing_media:
                    # Don't create new entry, just update existing one
                    logger.info(f"ZIP will update existing media: {existing_media['slug']}")
                else:
                    # Create temporary entry
                    media_index.add_media(temp_metadata, make_active=True)
                
            else:
                # Process as original video file (for frontend previews)
                raw_video_path = media_raw_dir / f"{slug}_{file.filename}"
                with open(raw_video_path, "wb") as f:
                    chunk_size = 1024 * 1024  # 1MB chunks
                    bytes_written = 0
                    while bytes_written < len(content):
                        chunk = content[bytes_written:bytes_written + chunk_size]
                        f.write(chunk)
                        bytes_written += len(chunk)
                
                logger.info(f"Saved original video: {raw_video_path}")

                metadata = {
                    "slug": slug,
                    "filename": file.filename,
                    "type": file.content_type or "video/mp4",
                    "size": len(content),
                    "uploadedAt": datetime.utcnow().isoformat() + "Z",
                    "url": f"/media/raw/{slug}_{file.filename}",
                    "processing_status": "processing",  # Wait for frame data
                }

                media_index.add_media(metadata, make_active=True)
                slugs.append(slug)
                
                # Update progress to show video upload completed
                media_index.update_processing_job(job_id, 30, "uploaded", f"Video uploaded, waiting for frame data...")
                logger.info(f"Video upload completed for {file.filename}, waiting for frame data")
                
        except Exception as e:
            error_msg = f"Error processing {file.filename}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            media_index.complete_processing_job(job_id, False, error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

    slugs = []
    job_ids = []

    # Process all files individually
    for file in files:
        await process_single_file(file, job_ids, slugs)

    # Start progress overlay
    if display_player and not display_player.showing_progress and job_ids:
        try:
            logger.info(f"Starting processing display for jobs: {job_ids}")
            display_player.start_processing_display(job_ids)
        except Exception as e:
            logger.warning(f"Failed to start processing display: {e}")

    # Refresh player display in background
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
        
        import threading
        refresh_thread = threading.Thread(target=refresh_player_async, daemon=True)
        refresh_thread.start()
        logger.info("Started background player refresh")

    logger.info(f"Upload complete: {len(slugs)} files processed, job_ids: {job_ids}")
    return {"slug": slugs[-1] if slugs else None, "job_ids": job_ids} 