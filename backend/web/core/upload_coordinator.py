"""
Backend Upload Coordinator - Transaction-based upload processing

Features:
- Atomic upload transactions
- Proper error rollback
- State consistency
- Duplicate detection
- Resource cleanup
"""

import json
import shutil
import asyncio
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

from fastapi import UploadFile, HTTPException
from utils.media_index import media_index
from utils.logger import get_logger
from ..core.events import broadcaster

logger = get_logger("upload_coordinator")

@dataclass
class UploadTransaction:
    """Upload transaction state"""
    id: str
    files: List[Dict[str, Any]]  # File metadata
    state: str  # 'processing', 'completed', 'error', 'rolled_back'
    created_at: datetime
    updated_at: datetime
    original_slug: Optional[str] = None
    zip_slug: Optional[str] = None
    merged_slug: Optional[str] = None
    error_message: Optional[str] = None
    temp_files: List[str] = None

    def __post_init__(self):
        if self.temp_files is None:
            self.temp_files = []

class UploadCoordinator:
    """Manages upload transactions with atomic operations"""
    
    def __init__(self):
        self.transactions: Dict[str, UploadTransaction] = {}
        self.lock = asyncio.Lock()
        
        # Start cleanup task
        asyncio.create_task(self.cleanup_old_transactions())

    async def process_upload(
        self,
        files: List[UploadFile],
        media_raw_dir: Path,
        media_processed_dir: Path,
        display_player=None
    ) -> Dict[str, Any]:
        """Process upload with full transaction safety"""
        
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")

        # Create transaction ID from file content hashes
        content_hashes = []
        file_data = []
        
        for file in files:
            content = await file.read()
            file_hash = hashlib.sha256(content).hexdigest()[:16]
            content_hashes.append(file_hash)
            file_data.append({
                'filename': file.filename,
                'content': content,
                'hash': file_hash,
                'size': len(content),
                'content_type': file.content_type
            })

        # Generate deterministic transaction ID
        combined_hash = hashlib.sha256(''.join(sorted(content_hashes)).encode()).hexdigest()[:16]
        transaction_id = f"tx_{combined_hash}"

        async with self.lock:
            # Check for duplicate transaction
            if transaction_id in self.transactions:
                existing = self.transactions[transaction_id]
                if existing.state == 'completed':
                    logger.info(f"Returning existing completed transaction: {transaction_id}")
                    return {
                        "success": True,
                        "processed": len(existing.files),
                        "last_slug": existing.merged_slug or existing.original_slug
                    }
                elif existing.state == 'processing':
                    raise HTTPException(status_code=409, detail="Upload already in progress")

            # Create new transaction
            transaction = UploadTransaction(
                id=transaction_id,
                files=[{'filename': f['filename'], 'hash': f['hash'], 'size': f['size']} for f in file_data],
                state='processing',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.transactions[transaction_id] = transaction

        logger.info(f"🎬 Starting upload transaction [{transaction_id}]: {len(files)} files")

        try:
            # Process files within transaction
            await self._process_transaction(transaction, file_data, media_raw_dir, media_processed_dir, display_player)
            
            # Mark transaction as completed
            async with self.lock:
                transaction.state = 'completed'
                transaction.updated_at = datetime.utcnow()

            logger.info(f"✅ Upload transaction completed [{transaction_id}]")
            
            return {
                "success": True,
                "processed": len(file_data),
                "last_slug": transaction.merged_slug or transaction.original_slug
            }

        except Exception as e:
            logger.error(f"❌ Upload transaction failed [{transaction_id}]: {e}")
            await self._rollback_transaction(transaction, media_raw_dir, media_processed_dir)
            raise

    async def _process_transaction(
        self,
        transaction: UploadTransaction,
        file_data: List[Dict],
        media_raw_dir: Path,
        media_processed_dir: Path,
        display_player=None
    ) -> None:
        """Process all files in the transaction"""
        
        # Pause playback during upload
        playback_paused = False
        if display_player and not display_player.is_paused():
            display_player.pause()
            playback_paused = True

        try:
            original_file = None
            zip_file = None
            
            # Categorize files
            for file_info in file_data:
                if file_info['filename'].lower().endswith('_frames.zip'):
                    zip_file = file_info
                else:
                    original_file = file_info

            if not original_file and not zip_file:
                raise ValueError("No valid files found")

            # Process original file first (if present)
            if original_file:
                await broadcaster.upload_progress_simple(original_file['filename'], 10, "finalizing")
                transaction.original_slug = await self._process_original_file(
                    transaction, original_file, media_raw_dir
                )
                await broadcaster.upload_progress_simple(original_file['filename'], 50, "finalizing")

            # Process ZIP file (if present)
            if zip_file:
                await broadcaster.upload_progress_simple(zip_file['filename'], 60, "finalizing")
                transaction.zip_slug = await self._process_zip_file(
                    transaction, zip_file, media_processed_dir, transaction.original_slug
                )
                await broadcaster.upload_progress_simple(zip_file['filename'], 90, "finalizing")

            # Determine final slug and broadcast completion
            final_slug = transaction.zip_slug or transaction.original_slug
            transaction.merged_slug = final_slug
            
            if final_slug:
                final_metadata = media_index.get_media_dict().get(final_slug)
                if final_metadata:
                    await broadcaster.media_uploaded(final_metadata)
                    await broadcaster.loop_updated(media_index.list_loop())

            # Notify completion for all processed files
            for file_info in file_data:
                await broadcaster.upload_progress_simple(file_info['filename'], 100, "complete")

        finally:
            # Resume playback
            if display_player and playback_paused:
                display_player.resume()

    async def _process_original_file(
        self, 
        transaction: UploadTransaction, 
        file_info: Dict, 
        media_raw_dir: Path
    ) -> str:
        """Process original media file"""
        
        # Generate slug
        sanitized = Path(file_info['filename']).stem.replace(" ", "_").lower()
        slug = f"{sanitized}_{file_info['hash']}"
        
        # Save file to temp location first
        temp_path = media_raw_dir / f"{slug}_{file_info['filename']}.tmp"
        transaction.temp_files.append(str(temp_path))
        
        with open(temp_path, "wb") as f:
            f.write(file_info['content'])
        
        # Create metadata
        metadata = {
            "slug": slug,
            "filename": file_info['filename'],
            "type": file_info['content_type'] or self._detect_content_type(file_info['filename']),
            "size": file_info['size'],
            "uploadedAt": datetime.utcnow().isoformat() + "Z",
            "url": f"/media/raw/{slug}_{file_info['filename']}",
            "processing_status": "uploaded",
            "frame_count": 1,
            "width": 320,
            "height": 240
        }
        
        # Atomically move to final location and add to index
        final_path = media_raw_dir / f"{slug}_{file_info['filename']}"
        temp_path.rename(final_path)
        transaction.temp_files.remove(str(temp_path))
        
        # Only auto-activate simple images, not videos
        is_video = metadata["type"].startswith("video/") or metadata["type"] in {
            "image/gif", "image/webp", "image/apng", "image/heic", "image/heif"
        }
        
        media_index.add_media(metadata, make_active=not is_video)
        
        logger.info(f"✅ Original file processed: {file_info['filename']} -> {slug}")
        return slug

    async def _process_zip_file(
        self,
        transaction: UploadTransaction,
        file_info: Dict,
        media_processed_dir: Path,
        original_slug: Optional[str] = None
    ) -> str:
        """Process ZIP file with frames"""
        
        import zipfile
        
        # Extract metadata from ZIP
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_zip = Path(tmpdir) / "upload.zip"
            with open(tmp_zip, "wb") as f:
                f.write(file_info['content'])
            
            with zipfile.ZipFile(tmp_zip, "r") as zf:
                if "metadata.json" not in zf.namelist():
                    raise ValueError("metadata.json missing in ZIP")
                
                zip_metadata = json.loads(zf.read("metadata.json").decode())

        original_filename = zip_metadata.get("original_filename", file_info['filename'].replace("_frames.zip", ""))
        
        # Determine target slug (prefer existing original)
        target_slug = original_slug
        if not target_slug:
            # Look for existing upload by filename
            media_dict = media_index.get_media_dict()
            for s, m in media_dict.items():
                if m.get("filename") == original_filename:
                    target_slug = s
                    break
        
        if not target_slug:
            # Create new slug
            sanitized = Path(original_filename).stem.replace(" ", "_").lower()
            target_slug = f"{sanitized}_{file_info['hash']}"

        # Extract ZIP to temp directory first
        temp_dir = media_processed_dir / f"{target_slug}.tmp"
        transaction.temp_files.append(str(temp_dir))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_zip = Path(tmpdir) / "upload.zip"
            with open(tmp_zip, "wb") as f:
                f.write(file_info['content'])
            
            with zipfile.ZipFile(tmp_zip, "r") as zf:
                zf.extractall(temp_dir)

        # Organize frames
        frames_dir = temp_dir / "frames"
        if not frames_dir.exists():
            frames_dir.mkdir()
            # Move frame files to frames directory
            for frame_file in temp_dir.glob("*.rgb"):
                frame_file.rename(frames_dir / frame_file.name)

        # Create or update metadata
        if original_slug:
            # Merge with existing metadata
            existing_meta = media_index.get_media_dict().get(original_slug, {})
            metadata = {
                **existing_meta,
                "processing_status": "completed",
                "frame_count": zip_metadata.get("frame_count", existing_meta.get("frame_count", 1)),
                "width": zip_metadata.get("width", existing_meta.get("width", 320)),
                "height": zip_metadata.get("height", existing_meta.get("height", 240)),
                "slug": original_slug,
            }
        else:
            # Create new metadata
            metadata = {
                "slug": target_slug,
                "filename": original_filename,
                "type": zip_metadata.get("type", "video/mp4"),
                "size": file_info['size'],
                "uploadedAt": datetime.utcnow().isoformat() + "Z",
                "url": f"/media/raw/{target_slug}_original",
                "processing_status": "completed",
                "frame_count": zip_metadata.get("frame_count", 1),
                "width": zip_metadata.get("width", 320),
                "height": zip_metadata.get("height", 240)
            }

        # Atomically move to final location and update index
        final_dir = media_processed_dir / target_slug
        if final_dir.exists():
            shutil.rmtree(final_dir)
        temp_dir.rename(final_dir)
        transaction.temp_files.remove(str(temp_dir))
        
        media_index.add_media(metadata, make_active=True)
        
        logger.info(f"✅ ZIP file processed: {file_info['filename']} -> {target_slug}")
        return target_slug

    async def _rollback_transaction(
        self,
        transaction: UploadTransaction,
        media_raw_dir: Path,
        media_processed_dir: Path
    ) -> None:
        """Rollback transaction changes"""
        
        logger.warning(f"🔄 Rolling back transaction [{transaction.id}]")
        
        async with self.lock:
            transaction.state = 'rolled_back'
            transaction.updated_at = datetime.utcnow()

        try:
            # Remove from media index
            if transaction.original_slug:
                try:
                    media_index.remove_media(transaction.original_slug)
                except Exception as e:
                    logger.warning(f"Failed to remove original from index: {e}")
            
            if transaction.zip_slug and transaction.zip_slug != transaction.original_slug:
                try:
                    media_index.remove_media(transaction.zip_slug)
                except Exception as e:
                    logger.warning(f"Failed to remove ZIP from index: {e}")

            # Clean up temp files
            for temp_file_path in transaction.temp_files:
                temp_path = Path(temp_file_path)
                try:
                    if temp_path.is_file():
                        temp_path.unlink()
                    elif temp_path.is_dir():
                        shutil.rmtree(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file {temp_path}: {e}")

            # Clean up final files if they were created
            for slug in [transaction.original_slug, transaction.zip_slug]:
                if slug:
                    try:
                        # Remove processed directory
                        processed_dir = media_processed_dir / slug
                        if processed_dir.exists():
                            shutil.rmtree(processed_dir)
                        
                        # Remove raw files
                        for raw_file in media_raw_dir.glob(f"{slug}_*"):
                            raw_file.unlink()
                            
                    except Exception as e:
                        logger.warning(f"Failed to cleanup files for {slug}: {e}")

        except Exception as e:
            logger.error(f"Error during rollback: {e}")

        logger.info(f"✅ Transaction rollback completed [{transaction.id}]")

    async def cleanup_old_transactions(self) -> None:
        """Cleanup old completed transactions"""
        while True:
            try:
                cutoff = datetime.utcnow() - timedelta(hours=24)
                
                async with self.lock:
                    to_remove = [
                        tx_id for tx_id, tx in self.transactions.items()
                        if tx.updated_at < cutoff and tx.state in ['completed', 'rolled_back']
                    ]
                    
                    for tx_id in to_remove:
                        del self.transactions[tx_id]
                
                if to_remove:
                    logger.info(f"🧹 Cleaned up {len(to_remove)} old transactions")
                    
            except Exception as e:
                logger.error(f"Error during transaction cleanup: {e}")
            
            # Run cleanup every hour
            await asyncio.sleep(3600)

    def _detect_content_type(self, filename: str) -> str:
        """Detect content type from filename"""
        ext = Path(filename).suffix.lower()
        type_map = {
            '.mp4': 'video/mp4',
            '.mov': 'video/quicktime',
            '.avi': 'video/x-msvideo',
            '.gif': 'image/gif',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
        }
        return type_map.get(ext, 'application/octet-stream')

# Global coordinator instance
upload_coordinator = UploadCoordinator() 