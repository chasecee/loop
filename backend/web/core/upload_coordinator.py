"""
HARDENED Upload Coordinator - Simple, bulletproof file processing.
No transactions, no complex locks, just reliable uploads.
"""

import json
import shutil
import asyncio
import hashlib
import tempfile
import io
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from urllib.parse import quote

from fastapi import UploadFile, HTTPException
from utils.media_index import media_index
from utils.logger import get_logger
from utils.safe_extract import safe_extract_zip

logger = get_logger("upload")

@dataclass
class UploadResult:
    """Simple upload result."""
    success: bool
    slug: Optional[str] = None
    error: Optional[str] = None

class HardenedUploadCoordinator:
    """Simple, bulletproof upload coordinator - no complex transactions."""
    
    def __init__(self):
        self.logger = logger
        # Simple deduplication
        self._active_uploads = set()
        self._upload_lock = asyncio.Lock()
    
    async def process_upload(
        self,
        files: List[UploadFile],
        media_raw_dir: Path,
        media_processed_dir: Path,
        display_player=None
    ) -> Dict[str, Any]:
        """Process upload with simple, reliable handling."""
        
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        start_time = asyncio.get_event_loop().time()
        
        # Simple file processing
        results = []
        last_slug = None
        
        async with self._upload_lock:
            for file in files:
                try:
                    result = await self._process_single_file(file, media_raw_dir, media_processed_dir)
                    results.append(result)
                    if result.success and result.slug:
                        last_slug = result.slug
                except Exception as e:
                    logger.error(f"Failed to process {file.filename}: {e}")
                    results.append(UploadResult(success=False, error=str(e)))
        
        # Simple success counting
        successful = [r for r in results if r.success]
        
        total_time = asyncio.get_event_loop().time() - start_time
        logger.info(f"Upload completed: {len(successful)}/{len(files)} files in {total_time:.1f}s")
        
        return {
            "success": len(successful) > 0,
            "processed": len(successful),
            "last_slug": last_slug
        }
    
    async def _process_single_file(
        self,
        file: UploadFile,
        media_raw_dir: Path,
        media_processed_dir: Path,
        chunk_size: int = 1024 * 1024,
    ) -> UploadResult:
        """Stream a single file to disk while hashing to avoid RAM spikes."""

        try:
            # ------------------------------------------------------------------
            # 1. Stream upload to a temporary file while computing SHA-256 hash
            # ------------------------------------------------------------------
            tmp_dir = media_raw_dir
            tmp_file_path = Path(tempfile.mktemp(dir=tmp_dir))

            def write_and_hash() -> tuple[str, int]:
                sha256 = hashlib.sha256()
                total = 0

                # Ensure we start at beginning
                file.file.seek(0)

                with open(tmp_file_path, "wb") as dst:
                    while True:
                        chunk = file.file.read(chunk_size)
                        if not chunk:
                            break
                        sha256.update(chunk)
                        dst.write(chunk)
                        total += len(chunk)
                return sha256.hexdigest(), total

            file_hash, total_size = await asyncio.to_thread(write_and_hash)

            # ------------------------------------------------------------------
            # 2. Derive slug & handle duplicates
            # ------------------------------------------------------------------
            filename_clean = Path(file.filename).stem.replace(" ", "_").lower()
            slug = f"{filename_clean}_{file_hash[:12]}"

            if slug in self._active_uploads:
                # Duplicate upload in progress
                tmp_file_path.unlink(missing_ok=True)
                return UploadResult(success=False, error="Upload already in progress")

            self._active_uploads.add(slug)

            try:
                # ------------------------------------------------------------------
                # 3. Dispatch based on file type
                # ------------------------------------------------------------------
                if file.filename.lower().endswith("_frames.zip"):
                    result = await self._process_frames_zip_path(
                        slug, file.filename, tmp_file_path, media_processed_dir
                    )
                    # Frames zip not stored in raw dir – delete temp file
                    tmp_file_path.unlink(missing_ok=True)
                    return result
                else:
                    final_path = media_raw_dir / f"{slug}_{file.filename}"
                    await asyncio.to_thread(shutil.move, tmp_file_path, final_path)
                    return await self._register_original_media(
                        slug, file.filename, total_size, final_path
                    )
            finally:
                self._active_uploads.discard(slug)

        except Exception as e:
            logger.error(f"File processing error: {e}")
            # Cleanup temp file in case of error
            if 'tmp_file_path' in locals() and tmp_file_path.exists():
                tmp_file_path.unlink(missing_ok=True)
            return UploadResult(success=False, error=str(e))

    # ------------------------------------------------------------------
    # New helpers (stream-friendly)
    # ------------------------------------------------------------------

    async def _register_original_media(
        self,
        slug: str,
        filename: str,
        size_bytes: int,
        stored_path: Path,
    ) -> UploadResult:
        """Register an already-saved raw file in the media index."""

        try:
            metadata = {
                "slug": slug,
                "filename": filename,
                "type": self._detect_content_type(filename),
                "size": size_bytes,
                "uploadedAt": datetime.utcnow().isoformat() + "Z",
                "url": f"/media/raw/{quote(stored_path.name)}",
                "processing_status": "uploaded",
                "frame_count": 1,
                "width": 320,
                "height": 240,
            }

            media_index.add_media(slug, metadata)
            logger.info(f"Original file uploaded: {filename} -> {slug}")
            
            # NOTE: Don't add to loop yet - wait for frames.zip processing
            # This prevents race condition where display player tries to load
            # media before frames are available
            
            return UploadResult(success=True, slug=slug)

        except Exception as e:
            logger.error(f"Failed to register media {filename}: {e}")
            stored_path.unlink(missing_ok=True)
            return UploadResult(success=False, error=str(e))

    async def _process_frames_zip_path(
        self,
        slug: str,
        filename: str,
        zip_path: Path,
        media_processed_dir: Path,
    ) -> UploadResult:
        """Process frames ZIP from path (secure extraction)."""

        try:
            # Validate ZIP file size first
            zip_size = zip_path.stat().st_size
            if zip_size < 1000:  # Less than 1KB is likely empty/invalid
                logger.warning(f"Frames ZIP {filename} appears to be empty ({zip_size} bytes)")
                return UploadResult(success=False, error="Frames ZIP appears to be empty or invalid")

            # Read metadata within archive
            with zipfile.ZipFile(zip_path, "r") as zf:
                if "metadata.json" not in zf.namelist():
                    return UploadResult(success=False, error="Invalid ZIP: missing metadata.json")
                
                metadata_raw = json.loads(zf.read("metadata.json").decode())
                
                # Validate frame count
                frame_count = metadata_raw.get("frame_count", 0)
                if frame_count <= 0:
                    logger.warning(f"Frames ZIP {filename} has invalid frame count: {frame_count}")
                    return UploadResult(success=False, error=f"Invalid frame count: {frame_count}")

                # Check for frame data (either frames.bin or individual .rgb files)
                file_list = zf.namelist()
                has_frames_bin = "frames.bin" in file_list
                has_rgb_files = any(f.endswith(".rgb") for f in file_list)
                
                if not has_frames_bin and not has_rgb_files:
                    logger.warning(f"Frames ZIP {filename} contains no frame data")
                    return UploadResult(success=False, error="No frame data found in ZIP")

            # Determine target directory slug logic reused from original code
            original_filename = metadata_raw.get("original_filename", filename.replace("_frames.zip", ""))

            existing_slug = None
            for s, m in media_index.get_media_dict().items():
                if m.get("filename") == original_filename:
                    existing_slug = s
                    break

            target_slug = existing_slug or slug
            target_dir = media_processed_dir / target_slug

            if target_dir.exists():
                await asyncio.to_thread(shutil.rmtree, target_dir)

            # Securely extract
            await asyncio.to_thread(
                self._secure_extract_zip_to_dir, zip_path, target_dir
            )

            # Handle both new binary format and legacy individual frame files
            frames_dir = target_dir / "frames"
            
            # Check for new binary format first
            frames_bin = target_dir / "frames.bin"
            if frames_bin.exists():
                # Validate binary frames file
                bin_size = frames_bin.stat().st_size
                expected_min_size = 8 + (frame_count * 320 * 240 * 2)  # Header + frame data
                if bin_size < expected_min_size:
                    logger.warning(f"Binary frames file too small: {bin_size} < {expected_min_size}")
                    return UploadResult(success=False, error="Binary frames file appears corrupted")
                
                # New binary format - move to frames directory
                if not frames_dir.exists():
                    await asyncio.to_thread(frames_dir.mkdir, parents=True)
                await asyncio.to_thread(frames_bin.rename, frames_dir / "frames.bin")
                logger.info(f"Moved binary frames file to {frames_dir}")
            else:
                # Legacy format - move individual .rgb files
                frame_files = list(target_dir.glob("*.rgb"))
                if frame_files:
                    # Validate frame files
                    expected_frame_size = 320 * 240 * 2  # RGB565
                    valid_frames = 0
                    for frame_file in frame_files:
                        if frame_file.stat().st_size == expected_frame_size:
                            valid_frames += 1
                    
                    if valid_frames == 0:
                        logger.warning(f"No valid frame files found (expected size: {expected_frame_size})")
                        return UploadResult(success=False, error="No valid frame files found")
                    
                    if not frames_dir.exists():
                        await asyncio.to_thread(frames_dir.mkdir, parents=True)
                    for frame_file in frame_files:
                        await asyncio.to_thread(frame_file.rename, frames_dir / frame_file.name)
                    logger.info(f"Moved {len(frame_files)} individual frame files to {frames_dir} ({valid_frames} valid)")
                else:
                    logger.warning(f"No frames found in ZIP for {target_slug}")
                    return UploadResult(success=False, error="No frame files found in ZIP")

            # Update / create metadata same as original
            if existing_slug:
                existing_meta = media_index.get_media_dict().get(existing_slug, {})
                updated_meta = {
                    **existing_meta,  # Preserve all existing fields including URL
                    "processing_status": "completed",
                    "frame_count": metadata_raw.get("frame_count", 1),
                    "width": metadata_raw.get("width", 320),
                    "height": metadata_raw.get("height", 240),
                }
                logger.info(f"Updating existing media {existing_slug}: URL={existing_meta.get('url')}")
                media_index.add_media(existing_slug, updated_meta)
                final_slug = existing_slug
            else:
                new_meta = {
                    "slug": target_slug,
                    "filename": original_filename,
                    "type": metadata_raw.get("type", "video/mp4"),
                    "size": zip_path.stat().st_size,
                    "uploadedAt": datetime.utcnow().isoformat() + "Z",
                    "processing_status": "completed",
                    "frame_count": metadata_raw.get("frame_count", 1),
                    "width": metadata_raw.get("width", 320),
                    "height": metadata_raw.get("height", 240),
                }
                media_index.add_media(target_slug, new_meta)
                final_slug = target_slug

            # SENIOR FIX: Complete media activation pipeline
            try:
                # 1. Add to loop (makes it available for playback)
                media_index.add_to_loop(final_slug)
                logger.info(f"Added to loop: {final_slug}")
                
                # 2. Auto-activate if no active media (first upload)
                current_active = media_index.get_active()
                if not current_active:
                    media_index.set_active(final_slug)
                    logger.info(f"Auto-activated first media: {final_slug}")
                
                # 3. Invalidate dashboard cache to ensure immediate frontend pickup
                from ..routes.dashboard import invalidate_dashboard_cache
                invalidate_dashboard_cache()
                logger.info(f"Invalidated dashboard cache for immediate pickup")
                
                # 4. Force display player to check for new media immediately
                try:
                    from main import display_player
                    if display_player:
                        display_player.force_media_check()
                        logger.info(f"Forced display player media check")
                except ImportError:
                    logger.debug("Display player not available for force refresh")
                except Exception as e:
                    logger.debug(f"Could not force display player refresh: {e}")
                
            except Exception as e:
                logger.warning(f"Media activation failed for {final_slug}: {e}")
                # Don't fail the entire upload, just log the issue

            logger.info(f"Frames ZIP processed: {filename} -> {target_slug}")
            return UploadResult(success=True, slug=target_slug)

        except Exception as e:
            logger.error(f"Frames ZIP error for {filename}: {e}")
            if 'target_dir' in locals() and target_dir.exists():
                await asyncio.to_thread(shutil.rmtree, target_dir)
            return UploadResult(success=False, error=str(e))

    # Helper runs in thread
    def _secure_extract_zip_to_dir(self, zip_path: Path, dest_dir: Path):
        from utils.safe_extract import safe_extract_zip
        with zipfile.ZipFile(zip_path, "r") as zf:
            safe_extract_zip(zf, dest_dir)

    def _detect_content_type(self, filename: str) -> str:
        """Detect content type from filename."""
        ext = Path(filename).suffix.lower()
        
        type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg', 
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.mp4': 'video/mp4',
            '.mov': 'video/quicktime',
            '.avi': 'video/x-msvideo',
            '.webm': 'video/webm',
        }
        
        return type_map.get(ext, 'application/octet-stream')


# Global instance
upload_coordinator = HardenedUploadCoordinator() 