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
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

from fastapi import UploadFile, HTTPException
from utils.media_index import media_index
from utils.logger import get_logger

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
        media_processed_dir: Path
    ) -> UploadResult:
        """Process a single file simply and safely."""
        
        try:
            # Read file content
            content = await file.read()
            if not content:
                return UploadResult(success=False, error="Empty file")
            
            # Generate simple hash-based slug
            file_hash = hashlib.sha256(content).hexdigest()[:12]
            filename_clean = Path(file.filename).stem.replace(" ", "_").lower()
            slug = f"{filename_clean}_{file_hash}"
            
            # Check for duplicate uploads
            if slug in self._active_uploads:
                return UploadResult(success=False, error="Upload already in progress")
            
            self._active_uploads.add(slug)
            
            try:
                # Determine file type
                if file.filename.lower().endswith('_frames.zip'):
                    return await self._process_frames_zip(slug, file.filename, content, media_processed_dir)
                else:
                    return await self._process_original_file(slug, file.filename, content, media_raw_dir)
            finally:
                self._active_uploads.discard(slug)
                
        except Exception as e:
            logger.error(f"File processing error: {e}")
            return UploadResult(success=False, error=str(e))
    
    async def _process_original_file(
        self,
        slug: str,
        filename: str,
        content: bytes,
        media_raw_dir: Path
    ) -> UploadResult:
        """Process original media file."""
        
        try:
            # Save file directly
            file_path = media_raw_dir / f"{slug}_{filename}"
            
            def write_file():
                with open(file_path, "wb") as f:
                    f.write(content)
            
            await asyncio.to_thread(write_file)
            
            # Create simple metadata
            metadata = {
                "slug": slug,
                "filename": filename,
                "type": self._detect_content_type(filename),
                "size": len(content),
                "uploadedAt": datetime.utcnow().isoformat() + "Z",
                "url": f"/media/raw/{slug}_{filename}",
                "processing_status": "uploaded",
                "frame_count": 1,
                "width": 320,
                "height": 240
            }
            
            # Add to media index
            media_index.add_media(metadata, True)  # Set as active
            
            logger.info(f"Original file uploaded: {filename} -> {slug}")
            return UploadResult(success=True, slug=slug)
            
        except Exception as e:
            # Cleanup on failure
            if file_path.exists():
                try:
                    file_path.unlink()
                except:
                    pass
            raise
    
    async def _process_frames_zip(
        self,
        slug: str,
        filename: str,
        content: bytes,
        media_processed_dir: Path
    ) -> UploadResult:
        """Process frames ZIP file."""
        
        import zipfile
        
        try:
            # Extract metadata from ZIP
            with zipfile.ZipFile(io.BytesIO(content), "r") as zf:
                if "metadata.json" not in zf.namelist():
                    return UploadResult(success=False, error="Invalid ZIP: missing metadata.json")
                
                metadata_raw = json.loads(zf.read("metadata.json").decode())
            
            # Determine target directory
            original_filename = metadata_raw.get("original_filename", filename.replace("_frames.zip", ""))
            
            # Look for existing media with same filename
            existing_slug = None
            for s, m in media_index.get_media_dict().items():
                if m.get("filename") == original_filename:
                    existing_slug = s
                    break
            
            target_slug = existing_slug or slug
            target_dir = media_processed_dir / target_slug
            
            # Clean up existing directory
            if target_dir.exists():
                await asyncio.to_thread(shutil.rmtree, target_dir)
            
            # Extract ZIP
            def extract_zip():
                with zipfile.ZipFile(io.BytesIO(content), "r") as zf:
                    zf.extractall(target_dir)
            
            await asyncio.to_thread(extract_zip)
            
            # Organize frames if needed
            frames_dir = target_dir / "frames"
            frame_files = list(target_dir.glob("*.rgb"))
            
            if frame_files and not frames_dir.exists():
                await asyncio.to_thread(frames_dir.mkdir, parents=True)
                for frame_file in frame_files:
                    await asyncio.to_thread(frame_file.rename, frames_dir / frame_file.name)
            
            # Create/update metadata
            if existing_slug:
                # Update existing media
                existing_meta = media_index.get_media_dict().get(existing_slug, {})
                updated_meta = {
                    **existing_meta,
                    "processing_status": "completed",
                    "frame_count": metadata_raw.get("frame_count", 1),
                    "width": metadata_raw.get("width", 320),
                    "height": metadata_raw.get("height", 240),
                }
                media_index.add_media(updated_meta, True)
            else:
                # Create new metadata
                new_meta = {
                    "slug": target_slug,
                    "filename": original_filename,
                    "type": metadata_raw.get("type", "video/mp4"),
                    "size": len(content),
                    "uploadedAt": datetime.utcnow().isoformat() + "Z",
                    "processing_status": "completed",
                    "frame_count": metadata_raw.get("frame_count", 1),
                    "width": metadata_raw.get("width", 320),
                    "height": metadata_raw.get("height", 240)
                }
                media_index.add_media(new_meta, True)
            
            logger.info(f"Frames ZIP processed: {filename} -> {target_slug}")
            return UploadResult(success=True, slug=target_slug)
            
        except Exception as e:
            # Cleanup on failure
            if 'target_dir' in locals() and target_dir.exists():
                try:
                    await asyncio.to_thread(shutil.rmtree, target_dir)
                except:
                    pass
            raise
    
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