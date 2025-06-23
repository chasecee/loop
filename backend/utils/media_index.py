"""
Utility helpers for reading/writing the media index (media/index.json).

This consolidates all access in one place so multiple endpoints and the
DisplayPlayer can share a single canonical schema:

{
    "media": {
        "<slug>": { ...metadata... },
        ...
    },
    "loop": ["slug1", "slug2", ...],
    "active": "slug1",            # optional currently-playing slug
    "last_updated": 1700000000,
    "processing": {              # track processing jobs
        "<job_id>": {
            "filename": "...",
            "status": "processing|completed|error",
            "progress": 0-100,
            "stage": "...",
            "message": "...",
            "timestamp": 1700000000
        }
    }
}
"""
from __future__ import annotations

import json
import time
import fcntl
import tempfile
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import threading
from contextlib import contextmanager

from utils.logger import get_logger

LOGGER = get_logger("media_index")
MEDIA_INDEX_PATH = Path("media/index.json")

@dataclass
class MediaMetadata:
    """Type-safe media metadata structure."""
    slug: str
    filename: str
    type: str
    size: int
    uploadedAt: str
    url: Optional[str] = None
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    frame_count: Optional[int] = None
    processing_status: Optional[str] = None  # "pending", "processing", "completed", "error"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class ProcessingJob:
    """Type-safe processing job structure."""
    job_id: str
    filename: str
    status: str  # "processing", "completed", "error"
    progress: float
    stage: str
    message: str
    timestamp: float

@dataclass
class MediaIndex:
    """Type-safe media index structure."""
    media: Dict[str, Dict[str, Any]]
    loop: List[str]
    active: Optional[str]
    last_updated: Optional[int]
    processing: Dict[str, Dict[str, Any]]  # job_id -> processing info
    
    @classmethod
    def empty(cls) -> 'MediaIndex':
        """Create empty media index."""
        return cls(
            media={},
            loop=[],
            active=None,
            last_updated=None,
            processing={}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "media": self.media,
            "loop": self.loop,
            "active": self.active,
            "last_updated": self.last_updated or int(time.time()),
            "processing": self.processing
        }

class MediaIndexManager:
    """Thread-safe manager for media index operations with in-memory caching."""
    
    def __init__(self, index_path: Path = MEDIA_INDEX_PATH):
        self.index_path = index_path
        self._ensure_media_dir()
        
        # In-memory cache for performance
        self._cache: Optional[MediaIndex] = None
        self._cache_dirty = False
        self._last_file_read = 0
        self._cache_lock = threading.Lock()
        
        # Batching support
        self._batching = False
        self._batch_dirty = False
        
        # Periodic persistence timer
        self._persistence_timer: Optional[threading.Timer] = None
        self._persistence_interval = 30  # seconds
        self._start_persistence_timer()
    
    def _ensure_media_dir(self) -> None:
        """Ensure media directory exists."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _start_persistence_timer(self) -> None:
        """Start periodic persistence timer."""
        def persist_if_dirty():
            with self._cache_lock:
                if self._cache_dirty and self._cache:
                    try:
                        self._write_to_disk(self._cache)
                        self._cache_dirty = False
                        LOGGER.debug("Periodic persistence completed")
                    except Exception as e:
                        LOGGER.error(f"Periodic persistence failed: {e}")
            
            # Schedule next persistence
            self._persistence_timer = threading.Timer(self._persistence_interval, persist_if_dirty)
            self._persistence_timer.daemon = True
            self._persistence_timer.start()
        
        # Start the timer
        self._persistence_timer = threading.Timer(self._persistence_interval, persist_if_dirty)
        self._persistence_timer.daemon = True
        self._persistence_timer.start()
    
    def _read_raw(self) -> MediaIndex:
        """Read the media index with in-memory caching."""
        with self._cache_lock:
            # Check if we can use cache
            if self._cache and not self._cache_dirty:
                # Check if file was modified since last read
                try:
                    file_mtime = self.index_path.stat().st_mtime
                    if file_mtime <= self._last_file_read:
                        return self._cache
                except (OSError, FileNotFoundError):
                    pass
            
            # Read from disk
            index = self._read_from_disk()
            self._cache = index
            self._cache_dirty = False
            self._last_file_read = time.time()
            return index
    
    def _read_from_disk(self) -> MediaIndex:
        """Read the media index from disk."""
        if not self.index_path.exists():
            return MediaIndex.empty()
        
        try:
            with open(self.index_path, "r") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    data = json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            # Validate structure
            if not isinstance(data, dict):
                LOGGER.error("Invalid media index format, resetting to default")
                return MediaIndex.empty()

            raw_media = data.get("media", {})
            if isinstance(raw_media, list):
                # Legacy format: list of media; convert to dict keyed by slug
                converted = {m.get("slug", f"legacy_{i}"): m for i, m in enumerate(raw_media) if isinstance(m, dict)}
                LOGGER.warning("Converted legacy list-based media index to dict format")
                raw_media = converted

            index = MediaIndex(
                media=raw_media if isinstance(raw_media, dict) else {},
                loop=data.get("loop", []),
                active=data.get("active"),
                last_updated=data.get("last_updated"),
                processing=data.get("processing", {})
            )

            # Validate data integrity
            valid_slugs = set(index.media.keys())
            
            # Clean up orphaned slugs in loop
            original_loop_length = len(index.loop)
            index.loop = [slug for slug in index.loop if slug in valid_slugs]
            
            if len(index.loop) != original_loop_length:
                LOGGER.info(f"Cleaned up {original_loop_length - len(index.loop)} orphaned slugs from loop")
                self._write_to_disk(index)

            # Validate active slug
            if index.active and index.active not in valid_slugs:
                LOGGER.info(f"Clearing invalid active slug: {index.active}")
                index.active = index.loop[0] if index.loop else None
                self._write_to_disk(index)

            # Clean up old processing jobs (more aggressive cleanup: 5 minutes for completed, limit total jobs)
            current_time = time.time()
            old_jobs = []
            completed_jobs = []
            
            for job_id, job_data in index.processing.items():
                job_timestamp = job_data.get("timestamp", 0)
                job_status = job_data.get("status", "processing")
                job_age = current_time - job_timestamp
                
                # Remove completed/error jobs after 5 minutes
                if job_status in ["completed", "error"] and job_age > 300:
                    old_jobs.append(job_id)
                # Remove very old processing jobs (30 minutes)
                elif job_age > 1800:
                    old_jobs.append(job_id)
                # Track completed jobs for size limiting
                elif job_status in ["completed", "error"]:
                    completed_jobs.append((job_id, job_timestamp))
            
            # Limit total completed jobs to prevent memory buildup (keep max 20 most recent)
            if len(completed_jobs) > 20:
                completed_jobs.sort(key=lambda x: x[1])  # Sort by timestamp
                old_jobs.extend([job_id for job_id, _ in completed_jobs[:-20]])
            
            # Remove old jobs
            for job_id in old_jobs:
                if job_id in index.processing:
                    del index.processing[job_id]
            
            if old_jobs:
                LOGGER.info(f"Cleaned up {len(old_jobs)} old processing jobs")
                self._write_to_disk(index)

            return index

        except Exception as exc:
            LOGGER.error(f"Failed to read media index: {exc}")
            return MediaIndex.empty()

    def _write_raw(self, index: MediaIndex) -> None:
        """Write the media index with caching and batching support."""
        with self._cache_lock:
            self._cache = index
            self._cache_dirty = True
            
            # Check if we're in batching mode
            if self._batching:
                self._batch_dirty = True
                return
            
            # For critical operations, write immediately
            # For less critical ones, rely on periodic persistence
            if hasattr(self, '_immediate_write_needed'):
                self._write_to_disk(index)
                self._cache_dirty = False
                delattr(self, '_immediate_write_needed')

    def _write_to_disk(self, index: MediaIndex) -> None:
        """Write the media index atomically with proper locking."""
        try:
            # Update timestamp
            index.last_updated = int(time.time())
            
            # Validate data structure before writing
            if not isinstance(index.media, dict):
                LOGGER.error("Invalid media format for writing")
                return
            
            if not isinstance(index.loop, list):
                LOGGER.error("Invalid loop format for writing")
                return

            if not isinstance(index.processing, dict):
                LOGGER.error("Invalid processing format for writing")
                return

            # Write to temporary file first for atomic operation
            temp_file = self.index_path.with_suffix('.json.tmp')
            
            with open(temp_file, "w") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(index.to_dict(), f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())  # Ensure data is written to disk
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            # Atomic rename
            shutil.move(str(temp_file), str(self.index_path))
            LOGGER.debug(f"Media index written successfully ({len(index.media)} items, {len(index.loop)} in loop, {len(index.processing)} processing)")

        except Exception as exc:
            LOGGER.error(f"Failed to write media index: {exc}")
            # Clean up temp file if it exists
            if 'temp_file' in locals() and temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass

    def _force_immediate_write(self) -> None:
        """Mark next write as immediate (for critical operations)."""
        self._immediate_write_needed = True

    # Public API methods
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get all data needed for the dashboard in a single operation."""
        index = self._read_raw()
        return {
            "media": list(index.media.values()),
            "loop": index.loop,
            "active": index.active,
            "last_updated": index.last_updated,
            "processing": index.processing
        }
    
    def list_media(self) -> List[Dict[str, Any]]:
        """Return all media objects as a list."""
        return list(self._read_raw().media.values())

    def get_media_dict(self) -> Dict[str, Dict[str, Any]]:
        """Return the media dictionary directly."""
        return self._read_raw().media.copy()

    def list_loop(self) -> List[str]:
        """Return the current loop slug list."""
        return self._read_raw().loop.copy()

    def get_active(self) -> Optional[str]:
        """Return the currently active media slug."""
        index = self._read_raw()
        
        # Validate that active slug exists in media
        if index.active and index.active not in index.media:
            LOGGER.warning(f"Active slug {index.active} not found in media, clearing")
            self.set_active(None)
            return None
        
        return index.active

    # Processing job management
    
    def add_processing_job(self, job_id: str, filename: str) -> None:
        """Add a processing job to track conversion progress."""
        LOGGER.info(f"Adding processing job: {job_id} for {filename}")
        index = self._read_raw()
        index.processing[job_id] = {
            "job_id": job_id,
            "filename": filename,
            "status": "processing",
            "progress": 0,
            "stage": "starting",
            "message": "Initializing conversion...",
            "timestamp": time.time()
        }
        self._write_raw(index)
        LOGGER.info(f"Processing job added successfully: {job_id}")

    def update_processing_job(self, job_id: str, progress: float, stage: str, message: str) -> None:
        """Update processing job progress."""
        LOGGER.debug(f"Updating processing job {job_id}: {progress}% - {stage} - {message}")
        index = self._read_raw()
        if job_id in index.processing:
            old_progress = index.processing[job_id].get("progress", 0)
            index.processing[job_id].update({
                "progress": min(100, max(0, progress)),
                "stage": stage,
                "message": message,
                "timestamp": time.time()
            })
            self._write_raw(index)
            if progress != old_progress:
                LOGGER.debug(f"Processing job {job_id} progress: {old_progress}% -> {progress}%")
        else:
            LOGGER.warning(f"Attempted to update non-existent processing job: {job_id}")

    def complete_processing_job(self, job_id: str, success: bool, error: str = "") -> None:
        """Mark a processing job as completed."""
        LOGGER.info(f"Completing processing job {job_id}: success={success}, error='{error}'")
        index = self._read_raw()
        if job_id in index.processing:
            old_status = index.processing[job_id].get("status", "unknown")
            index.processing[job_id].update({
                "progress": 100,
                "stage": "completed" if success else "error",
                "message": "Conversion completed" if success else f"Error: {error}",
                "status": "completed" if success else "error",
                "timestamp": time.time()
            })
            self._write_raw(index)
            LOGGER.info(f"Processing job {job_id} status: {old_status} -> {'completed' if success else 'error'}")
        else:
            LOGGER.warning(f"Attempted to complete non-existent processing job: {job_id}")

    def get_processing_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get processing job status."""
        LOGGER.debug(f"Getting processing job status: {job_id}")
        index = self._read_raw()
        job = index.processing.get(job_id)
        if job:
            LOGGER.debug(f"Processing job {job_id} found: {job.get('progress', 0)}% - {job.get('stage', 'unknown')}")
        else:
            LOGGER.debug(f"Processing job {job_id} not found")
        return job

    def remove_processing_job(self, job_id: str) -> None:
        """Remove a processing job from tracking."""
        LOGGER.info(f"Removing processing job: {job_id}")
        index = self._read_raw()
        if job_id in index.processing:
            del index.processing[job_id]
            self._write_raw(index)
            LOGGER.info(f"Processing job removed successfully: {job_id}")
        else:
            LOGGER.warning(f"Attempted to remove non-existent processing job: {job_id}")

    def list_processing_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Return all processing jobs."""
        index = self._read_raw()
        job_count = len(index.processing)
        LOGGER.debug(f"Listed {job_count} processing jobs")
        return index.processing.copy()

    def add_media(self, metadata: Union[Dict[str, Any], MediaMetadata], make_active: bool = True) -> None:
        """Add a media item to the index."""
        if isinstance(metadata, MediaMetadata):
            meta_dict = metadata.to_dict()
            slug = metadata.slug
        else:
            meta_dict = metadata
            slug = meta_dict.get("slug")
            
        if not slug:
            raise ValueError("Metadata missing slug")

        index = self._read_raw()
        
        # Add to media dict
        index.media[slug] = meta_dict

        # Add to loop if requested
        if make_active and slug not in index.loop:
            index.loop.append(slug)

        # Set as active if it's the first item or explicitly requested
        if make_active and (not index.active or index.active not in index.media):
            index.active = slug

        self._force_immediate_write()  # Critical operation
        self._write_raw(index)
        LOGGER.info(f"Added media: {slug}")

    def remove_media(self, slug: str) -> None:
        """Remove a media item completely from the index."""
        index = self._read_raw()
        
        # Remove from media dict
        if slug in index.media:
            del index.media[slug]
            LOGGER.info(f"Removed media from library: {slug}")
        
        # Remove from loop
        if slug in index.loop:
            index.loop.remove(slug)
            LOGGER.info(f"Removed media from loop: {slug}")
        
        # Update active if it was the deleted item
        if index.active == slug:
            index.active = index.loop[0] if index.loop else None
            LOGGER.info(f"Updated active media to: {index.active}")
        
        self._force_immediate_write()  # Critical operation
        self._write_raw(index)
        LOGGER.info(f"Successfully removed media: {slug}")

    def add_to_loop(self, slug: str) -> None:
        """Add a media item to the loop queue."""
        index = self._read_raw()
        
        if slug not in index.media:
            raise KeyError(f"Media slug not found: {slug}")
        
        if slug not in index.loop:
            index.loop.append(slug)
            self._write_raw(index)
            LOGGER.info(f"Added to loop: {slug}")

    def remove_from_loop(self, slug: str) -> None:
        """Remove a media item from the loop queue."""
        index = self._read_raw()
        
        if slug in index.loop:
            index.loop.remove(slug)
            
            # If this was the active item, update active
            if index.active == slug:
                index.active = index.loop[0] if index.loop else None
                LOGGER.info(f"Updated active media to: {index.active}")
            
            self._write_raw(index)
            LOGGER.info(f"Removed from loop: {slug}")

    def reorder_loop(self, new_order: List[str]) -> None:
        """Reorder the loop queue with the given slug list."""
        index = self._read_raw()
        valid_slugs = set(index.media.keys())
        
        # Only keep slugs that exist in media
        validated_order = [slug for slug in new_order if slug in valid_slugs]
        
        index.loop = validated_order
        
        # Ensure active is still valid
        if index.active and index.active not in validated_order:
            index.active = validated_order[0] if validated_order else None
        
        self._write_raw(index)
        LOGGER.info(f"Reordered loop with {len(validated_order)} items")

    def set_active(self, slug: Optional[str]) -> None:
        """Set the currently active media slug."""
        index = self._read_raw()
        
        if slug is not None:
            if slug not in index.media:
                raise KeyError(f"Media slug not found: {slug}")
            
            # Ensure the slug is in the loop
            if slug not in index.loop:
                index.loop.append(slug)
        
        index.active = slug
        self._force_immediate_write()  # Critical operation
        self._write_raw(index)
        LOGGER.info(f"Set active media to: {slug}")

    def cleanup_orphaned_files(self, media_raw_dir: Path, media_processed_dir: Path) -> int:
        """Clean up files that don't have corresponding entries in the media index."""
        index = self._read_raw()
        valid_slugs = set(index.media.keys())
        cleanup_count = 0
        
        # Clean up processed directories
        if media_processed_dir.exists():
            for item in media_processed_dir.iterdir():
                if item.is_dir() and item.name not in valid_slugs:
                    try:
                        shutil.rmtree(item)
                        cleanup_count += 1
                        LOGGER.info(f"Cleaned up orphaned processed directory: {item.name}")
                    except Exception as e:
                        LOGGER.error(f"Failed to clean up {item}: {e}")
        
        # Clean up raw files
        if media_raw_dir.exists():
            for item in media_raw_dir.iterdir():
                if item.is_file():
                    # Extract slug from filename (remove extension)
                    file_slug = None
                    for slug in valid_slugs:
                        if slug in item.name:
                            file_slug = slug
                            break
                    
                    if not file_slug:
                        try:
                            item.unlink()
                            cleanup_count += 1
                            LOGGER.info(f"Cleaned up orphaned raw file: {item.name}")
                        except Exception as e:
                            LOGGER.error(f"Failed to clean up {item}: {e}")
        
        return cleanup_count

# Global instance - the clean way to access media index
media_index = MediaIndexManager()

@contextmanager
def batch_operations(media_index_manager: 'MediaIndexManager'):
    """Context manager to batch multiple media operations before persistence."""
    media_index_manager._batching = True
    try:
        yield
    finally:
        media_index_manager._batching = False
        # Force immediate write after batch
        if hasattr(media_index_manager, '_batch_dirty') and media_index_manager._batch_dirty:
            media_index_manager._force_immediate_write()
            if media_index_manager._cache:
                media_index_manager._write_raw(media_index_manager._cache)
            media_index_manager._batch_dirty = False 