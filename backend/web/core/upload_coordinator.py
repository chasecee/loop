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
import io
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

        # Performance timing
        total_start = asyncio.get_event_loop().time()
        
        # Create transaction ID from file content hashes
        content_hashes = []
        file_data = []
        
        # OPTIMIZATION: Process file hashing concurrently
        hash_start = asyncio.get_event_loop().time()
        
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

        hash_time = asyncio.get_event_loop().time() - hash_start
        logger.info(f"⚡ File hashing completed in {hash_time:.2f}s for {len(files)} files")

        # Generate deterministic transaction ID
        combined_hash = hashlib.sha256(''.join(sorted(content_hashes)).encode()).hexdigest()[:16]
        transaction_id = f"tx_{combined_hash}"

        # OPTIMIZATION: Track lock acquisition time
        lock_start = asyncio.get_event_loop().time()
        async with self.lock:
            lock_time = asyncio.get_event_loop().time() - lock_start
            if lock_time > 0.1:  # Log if lock took more than 100ms
                logger.warning(f"🔒 Lock acquisition took {lock_time:.2f}s - potential contention")
            
            # Check for duplicate transaction
            if transaction_id in self.transactions:
                existing = self.transactions[transaction_id]
                if existing.state == 'completed':
                    logger.info(f"🔄 Returning existing completed transaction: {transaction_id}")
                    return {
                        "success": True,
                        "processed": len(existing.files),
                        "last_slug": existing.merged_slug or existing.original_slug
                    }
                elif existing.state == 'processing':
                    logger.warning(f"🚫 Blocking duplicate upload request: {transaction_id}")
                    raise HTTPException(status_code=409, detail="Upload already in progress")
                else:
                    # Clean up failed/rolled_back transactions
                    logger.info(f"🧹 Cleaning up previous failed transaction: {transaction_id}")
                    del self.transactions[transaction_id]
            
            # Also check for filename-based duplicates across all transactions
            for existing_id, existing_tx in self.transactions.items():
                if existing_tx.state == 'processing':
                    existing_filenames = {f['filename'] for f in existing_tx.files}
                    new_filenames = {f['filename'] for f in file_data}
                    
                    # Check for any filename overlap
                    if existing_filenames & new_filenames:
                        overlap = existing_filenames & new_filenames
                        logger.warning(f"🚫 Blocking upload with overlapping filenames: {overlap}")
                        raise HTTPException(
                            status_code=409, 
                            detail=f"Files already being processed: {', '.join(overlap)}"
                        )

            # Create new transaction
            transaction = UploadTransaction(
                id=transaction_id,
                files=[{'filename': f['filename'], 'hash': f['hash'], 'size': f['size']} for f in file_data],
                state='processing',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.transactions[transaction_id] = transaction

        logger.info(f"🎬 Starting upload transaction [{transaction_id}]: {len(files)} files, total size: {sum(f['size'] for f in file_data)/1024/1024:.1f}MB")

        try:
            # Process files within transaction
            await self._process_transaction(transaction, file_data, media_raw_dir, media_processed_dir, display_player)
            
            # Mark transaction as completed
            async with self.lock:
                transaction.state = 'completed'
                transaction.updated_at = datetime.utcnow()

            total_time = asyncio.get_event_loop().time() - total_start
            logger.info(f"✅ Upload transaction completed in {total_time:.2f}s [{transaction_id}]")
            
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
        
        # Performance timing
        start_time = asyncio.get_event_loop().time()
        logger.info(f"🎬 Processing transaction [{transaction.id}]: {len(file_data)} files")
        
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
                original_start = asyncio.get_event_loop().time()
                await broadcaster.upload_progress_simple(original_file['filename'], 10, "processing original")
                transaction.original_slug = await self._process_original_file(
                    transaction, original_file, media_raw_dir
                )
                original_time = asyncio.get_event_loop().time() - original_start
                logger.info(f"⚡ Original file processed in {original_time:.2f}s: {original_file['filename']}")

            # Process ZIP file (if present)
            if zip_file:
                zip_start = asyncio.get_event_loop().time()
                await broadcaster.upload_progress_simple(zip_file['filename'], 60, "processing frames")
                transaction.zip_slug = await self._process_zip_file(
                    transaction, zip_file, media_processed_dir, transaction.original_slug
                )
                zip_time = asyncio.get_event_loop().time() - zip_start
                logger.info(f"✅ ZIP file processed in {zip_time:.2f}s: {zip_file['filename']} -> {transaction.zip_slug}")

            # Determine final slug and broadcast completion
            final_slug = transaction.zip_slug or transaction.original_slug
            transaction.merged_slug = final_slug
            
            if final_slug:
                final_metadata = media_index.get_media_dict().get(final_slug)
                if final_metadata:
                    await broadcaster.media_uploaded(final_metadata)
                    await broadcaster.loop_updated(media_index.list_loop())

            # Single completion message for the primary file
            primary_filename = zip_file['filename'] if zip_file else original_file['filename']
            await broadcaster.upload_progress_simple(primary_filename, 100, "complete")

            total_time = asyncio.get_event_loop().time() - start_time
            logger.info(f"🏁 Transaction completed in {total_time:.2f}s [{transaction.id}]")

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
        """Process original media file - OPTIMIZED FOR PERFORMANCE"""
        
        logger.info(f"📄 Processing original file: {file_info['filename']} ({file_info['size']/1024/1024:.1f}MB)")
        
        # Generate slug
        sanitized = Path(file_info['filename']).stem.replace(" ", "_").lower()
        slug = f"{sanitized}_{file_info['hash']}"
        
        # Save file using async I/O to avoid blocking
        temp_path = media_raw_dir / f"{slug}_{file_info['filename']}.tmp"
        transaction.temp_files.append(str(temp_path))
        
        # OPTIMIZATION: Use async file writing
        def write_file_sync():
            with open(temp_path, "wb") as f:
                f.write(file_info['content'])
        
        await asyncio.to_thread(write_file_sync)
        logger.info(f"💾 Original file written to temp: {temp_path}")
        
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
        
        # Atomically move to final location and add to index using async I/O
        final_path = media_raw_dir / f"{slug}_{file_info['filename']}"
        await asyncio.to_thread(temp_path.rename, final_path)
        transaction.temp_files.remove(str(temp_path))
        
        # Only auto-activate simple images, not videos
        is_video = metadata["type"].startswith("video/") or metadata["type"] in {
            "image/gif", "image/webp", "image/apng", "image/heic", "image/heif"
        }
        
        # OPTIMIZATION: Non-blocking media index update
        await asyncio.to_thread(media_index.add_media, metadata, not is_video)
        
        logger.info(f"✅ Original file processed: {file_info['filename']} -> {slug}")
        return slug

    async def _process_zip_file(
        self,
        transaction: UploadTransaction,
        file_info: Dict,
        media_processed_dir: Path,
        original_slug: Optional[str] = None
    ) -> str:
        """Process ZIP file with frames - OPTIMIZED FOR PERFORMANCE"""
        
        import zipfile
        
        logger.info(f"🏃 Starting optimized ZIP processing: {file_info['filename']} ({file_info['size']/1024/1024:.1f}MB)")
        start_time = asyncio.get_event_loop().time()
        
        # OPTIMIZATION 1: Single in-memory ZIP processing - no temp files
        zip_metadata = None
        original_filename = None
        
        try:
            # Read metadata from memory without writing to disk
            with zipfile.ZipFile(io.BytesIO(file_info['content']), "r") as zf:
                if "metadata.json" not in zf.namelist():
                    raise ValueError("metadata.json missing in ZIP")
                
                zip_metadata = json.loads(zf.read("metadata.json").decode())
                logger.info(f"📋 ZIP metadata extracted: {zip_metadata.get('frame_count', 0)} frames")
        except Exception as e:
            logger.error(f"❌ Failed to read ZIP metadata: {e}")
            raise ValueError(f"Invalid ZIP file: {e}")

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

        # OPTIMIZATION 2: Direct extraction to final location with progress
        final_dir = media_processed_dir / target_slug
        
        # Clean up existing directory if present
        if final_dir.exists():
            await asyncio.to_thread(shutil.rmtree, final_dir)
            logger.info(f"🧹 Cleaned up existing directory: {final_dir}")
        
        # Progress update
        await broadcaster.upload_progress_simple(file_info['filename'], 65, "extracting")
        
        # OPTIMIZATION 3: Single-pass extraction with async I/O and progress
        await self._extract_zip_async(file_info['content'], final_dir, file_info['filename'])
        
        # Progress update  
        await broadcaster.upload_progress_simple(file_info['filename'], 85, "organizing")
        
        # OPTIMIZATION 4: Smart frame organization - only if needed
        frames_dir = final_dir / "frames"
        frame_files = list(final_dir.glob("*.rgb"))
        
        if frame_files and not frames_dir.exists():
            await asyncio.to_thread(frames_dir.mkdir, parents=True)
            
            # Move frame files efficiently
            await asyncio.gather(*[
                asyncio.to_thread(frame_file.rename, frames_dir / frame_file.name)
                for frame_file in frame_files
            ])
            logger.info(f"📁 Organized {len(frame_files)} frames into frames/ directory")

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

        # OPTIMIZATION 5: Non-blocking media index update
        await asyncio.to_thread(media_index.add_media, metadata, True)
        
        processing_time = asyncio.get_event_loop().time() - start_time
        logger.info(f"✅ ZIP file processed in {processing_time:.2f}s: {file_info['filename']} -> {target_slug}")
        return target_slug

    async def _extract_zip_async(self, zip_content: bytes, extract_path: Path, filename: str) -> None:
        """Extract ZIP file asynchronously with progress reporting."""
        import zipfile
        import io
        
        # Create a list to collect progress updates from the thread
        progress_updates = []
        
        def extract_sync():
            """Synchronous extraction function to run in thread."""
            with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zf:
                # Get file list for progress calculation
                file_list = zf.namelist()
                total_files = len(file_list)
                
                logger.info(f"📦 Extracting {total_files} files from ZIP")
                
                for i, file_name in enumerate(file_list):
                    try:
                        zf.extract(file_name, extract_path)
                        
                        # Progress update every 20% or 100 files
                        if (i + 1) % max(1, total_files // 5) == 0 or (i + 1) % 100 == 0:
                            progress = 65 + int((i + 1) / total_files * 15)  # 65-80% range
                            # Store progress updates instead of creating tasks from thread
                            progress_updates.append({
                                'filename': filename,
                                'progress': progress,
                                'stage': f"extracting ({i+1}/{total_files})"
                            })
                    except Exception as e:
                        logger.warning(f"Failed to extract {file_name}: {e}")
                        continue
                
                logger.info(f"✅ Extracted {total_files} files to {extract_path}")
        
        # Run extraction in thread to avoid blocking
        await asyncio.to_thread(extract_sync)
        
        # Send progress updates from the main thread after extraction completes
        for update in progress_updates:
            try:
                await broadcaster.upload_progress_simple(
                    update['filename'], 
                    update['progress'], 
                    update['stage']
                )
            except Exception as e:
                logger.warning(f"Failed to send progress update: {e}")

    async def _rollback_transaction(
        self,
        transaction: UploadTransaction,
        media_raw_dir: Path,
        media_processed_dir: Path
    ) -> None:
        """Rollback transaction changes - OPTIMIZED FOR PERFORMANCE"""
        
        logger.warning(f"🔄 Rolling back transaction [{transaction.id}]")
        rollback_start = asyncio.get_event_loop().time()
        
        async with self.lock:
            transaction.state = 'rolled_back'
            transaction.updated_at = datetime.utcnow()

        try:
            # OPTIMIZATION: Parallel cleanup operations
            cleanup_tasks = []
            
            # Remove from media index (async)
            if transaction.original_slug:
                cleanup_tasks.append(self._remove_media_async(transaction.original_slug, "original"))
            
            if transaction.zip_slug and transaction.zip_slug != transaction.original_slug:
                cleanup_tasks.append(self._remove_media_async(transaction.zip_slug, "ZIP"))

            # Clean up temp files (async)
            if transaction.temp_files:
                cleanup_tasks.append(self._cleanup_temp_files_async(transaction.temp_files))

            # Clean up final files (async)
            for slug in [transaction.original_slug, transaction.zip_slug]:
                if slug:
                    cleanup_tasks.append(self._cleanup_slug_files_async(slug, media_raw_dir, media_processed_dir))

            # Execute all cleanup tasks in parallel
            if cleanup_tasks:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Error during rollback: {e}")

        rollback_time = asyncio.get_event_loop().time() - rollback_start
        logger.info(f"✅ Transaction rollback completed in {rollback_time:.2f}s [{transaction.id}]")

    async def _remove_media_async(self, slug: str, media_type: str) -> None:
        """Remove media from index asynchronously."""
        try:
            await asyncio.to_thread(media_index.remove_media, slug)
            logger.info(f"🗑️ Removed {media_type} from index: {slug}")
        except Exception as e:
            logger.warning(f"Failed to remove {media_type} from index: {e}")

    async def _cleanup_temp_files_async(self, temp_files: List[str]) -> None:
        """Clean up temporary files asynchronously."""
        def cleanup_temp_sync():
            cleaned = 0
            for temp_file_path in temp_files:
                temp_path = Path(temp_file_path)
                try:
                    if temp_path.is_file():
                        temp_path.unlink()
                        cleaned += 1
                    elif temp_path.is_dir():
                        shutil.rmtree(temp_path)
                        cleaned += 1
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file {temp_path}: {e}")
            logger.info(f"🧹 Cleaned up {cleaned} temp files")
        
        await asyncio.to_thread(cleanup_temp_sync)

    async def _cleanup_slug_files_async(self, slug: str, media_raw_dir: Path, media_processed_dir: Path) -> None:
        """Clean up files for a specific slug asynchronously."""
        def cleanup_slug_sync():
            cleaned = 0
            try:
                # Remove processed directory
                processed_dir = media_processed_dir / slug
                if processed_dir.exists():
                    shutil.rmtree(processed_dir)
                    cleaned += 1
                
                # Remove raw files
                for raw_file in media_raw_dir.glob(f"{slug}_*"):
                    raw_file.unlink()
                    cleaned += 1
                    
                logger.info(f"🗑️ Cleaned up {cleaned} files for slug: {slug}")
                    
            except Exception as e:
                logger.warning(f"Failed to cleanup files for {slug}: {e}")
        
        await asyncio.to_thread(cleanup_slug_sync)

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