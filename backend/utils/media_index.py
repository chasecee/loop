"""
Utility helpers for reading/writing the media index (media/index.json).

HARDENED VERSION: Protects SD card from excessive writes with intelligent batching.
"""
from __future__ import annotations

import json
import time
import fcntl
import tempfile
import os
import shutil
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import threading
from contextlib import contextmanager

from utils.logger import get_logger

LOGGER = get_logger("media_index")
MEDIA_INDEX_PATH = Path("media/index.json")
MEDIA_DB_PATH = Path("media/media.db")

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
    """Complete media index structure."""
    media: Dict[str, Dict[str, Any]]
    loop: List[str]
    active: Optional[str]
    last_updated: Optional[int]
    processing: Dict[str, Dict[str, Any]]
    
    @classmethod
    def empty(cls) -> 'MediaIndex':
        """Create empty media index."""
        return cls(
            media={},
            loop=[],
            active=None,
            last_updated=int(time.time()),
            processing={}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "media": self.media,
            "loop": self.loop, 
            "active": self.active,
            "last_updated": self.last_updated,
            "processing": self.processing
        }

class HardenedMediaIndexManager:
    """SD-card-friendly media index manager with intelligent batching."""
    
    def __init__(self, index_path: Path = MEDIA_INDEX_PATH):
        self.index_path = index_path
        self.db_path = MEDIA_DB_PATH
        self._ensure_media_dir()
        
        # In-memory state
        self._cache: Optional[MediaIndex] = None
        self._cache_lock = threading.RLock()
        
        # Write protection - batch operations to protect SD card
        self._pending_operations = []
        self._last_write_time = 0
        self._min_write_interval = 300  # 5 minutes minimum between writes
        self._max_pending_ops = 20      # Force write after 20 operations
        self._shutdown_flag = False
        
        # Initialize DB and load initial state
        self._init_db()
        self._load_initial_state()
        
        # Start background writer (single thread for all persistence)
        self._writer_thread = threading.Thread(target=self._background_writer, daemon=True)
        self._writer_thread.start()
        
        LOGGER.info("Hardened media index manager initialized with write batching")
    
    def _ensure_media_dir(self) -> None:
        """Ensure media directory exists."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _init_db(self) -> None:
        """Initialize SQLite database for crash-safe operations."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS operations_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL,
                        operation TEXT,
                        data TEXT
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON operations_log(timestamp)
                """)
                conn.commit()
        except Exception as e:
            LOGGER.warning(f"Failed to initialize operations log DB: {e}")
    
    def _load_initial_state(self) -> None:
        """Load initial state from disk, handling corruption gracefully."""
        with self._cache_lock:
            try:
                if self.index_path.exists():
                    self._cache = self._read_from_disk()
                else:
                    self._cache = MediaIndex.empty()
                LOGGER.info(f"Loaded initial state: {len(self._cache.media)} media items")
            except Exception as e:
                LOGGER.error(f"Failed to load initial state, creating empty: {e}")
                self._cache = MediaIndex.empty()
    
    def _background_writer(self) -> None:
        """Background thread that handles all disk writes with intelligent batching."""
        LOGGER.info("Background writer started")
        
        while not self._shutdown_flag:
            try:
                time.sleep(30)  # Check every 30 seconds
                
                with self._cache_lock:
                    should_write = (
                        len(self._pending_operations) >= self._max_pending_ops or
                        (len(self._pending_operations) > 0 and 
                         time.time() - self._last_write_time >= self._min_write_interval)
                    )
                    
                    if should_write and self._cache:
                        try:
                            self._write_to_disk_internal(self._cache)
                            self._pending_operations.clear()
                            self._last_write_time = time.time()
                            LOGGER.info(f"Background write completed ({len(self._pending_operations)} ops batched)")
                        except Exception as e:
                            LOGGER.error(f"Background write failed: {e}")
                            # Don't clear pending operations on failure - retry later
                            
            except Exception as e:
                LOGGER.error(f"Background writer error: {e}")
                time.sleep(60)  # Back off on errors
        
        LOGGER.info("Background writer stopped")
    
    def _read_from_disk(self) -> MediaIndex:
        """Read media index from disk with corruption handling."""
        if not self.index_path.exists():
            return MediaIndex.empty()
        
        try:
            with open(self.index_path, "r") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock for reading
                try:
                    data = json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            
            # Validate and sanitize data
            if not isinstance(data, dict):
                LOGGER.error("Corrupted index file, resetting")
                return MediaIndex.empty()
            
            raw_media = data.get("media", {})
            if isinstance(raw_media, list):
                # Convert legacy format
                converted = {m.get("slug", f"legacy_{i}"): m for i, m in enumerate(raw_media) if isinstance(m, dict)}
                raw_media = converted
            
            index = MediaIndex(
                media=raw_media if isinstance(raw_media, dict) else {},
                loop=data.get("loop", []),
                active=data.get("active"),
                last_updated=data.get("last_updated"),
                processing=data.get("processing", {})
            )
            
            # Clean up stale data
            self._cleanup_stale_data(index)
            return index
            
        except json.JSONDecodeError as e:
            LOGGER.error(f"JSON corruption in index file: {e}")
            return MediaIndex.empty()
        except Exception as e:
            LOGGER.error(f"Failed to read index file: {e}")
            return MediaIndex.empty()
    
    def _cleanup_stale_data(self, index: MediaIndex) -> None:
        """Clean up stale data without triggering writes."""
        current_time = time.time()
        
        # Clean up old processing jobs (1 hour max)
        stale_jobs = []
        for job_id, job_data in index.processing.items():
            job_timestamp = job_data.get("timestamp", 0)
            if current_time - job_timestamp > 3600:  # 1 hour
                stale_jobs.append(job_id)
        
        for job_id in stale_jobs:
            del index.processing[job_id]
        
        # Validate loop consistency
        valid_slugs = set(index.media.keys())
        index.loop = [slug for slug in index.loop if slug in valid_slugs]
        
        if index.active and index.active not in valid_slugs:
            index.active = index.loop[0] if index.loop else None
    
    def _write_to_disk_internal(self, index: MediaIndex) -> None:
        """Internal disk write with atomic operations."""
        try:
            # Update timestamp
            index.last_updated = int(time.time())
            
            # Atomic write using temporary file
            temp_file = self.index_path.with_suffix('.json.tmp')
            
            with open(temp_file, "w") as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(index.to_dict(), f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())  # Ensure data reaches disk
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            
            # Atomic rename
            shutil.move(str(temp_file), str(self.index_path))
            
        except Exception as e:
            # Clean up temp file on failure
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except:
                    pass
            raise
    
    def _queue_operation(self, operation_name: str, data: Any = None) -> None:
        """Queue an operation for batched writing."""
        with self._cache_lock:
            self._pending_operations.append({
                "timestamp": time.time(),
                "operation": operation_name,
                "data": data
            })
    
    def _force_immediate_write(self) -> None:
        """Force immediate write for critical operations."""
        with self._cache_lock:
            if self._cache:
                try:
                    self._write_to_disk_internal(self._cache)
                    self._pending_operations.clear()
                    self._last_write_time = time.time()
                    LOGGER.info("Forced immediate write completed")
                except Exception as e:
                    LOGGER.error(f"Forced write failed: {e}")
                    raise
    
    # Public API
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get all data for dashboard."""
        with self._cache_lock:
            if not self._cache:
                return {"media": [], "loop": [], "active": None, "processing": {}}
            
            return {
                "media": list(self._cache.media.values()),
                "loop": self._cache.loop.copy(),
                "active": self._cache.active,
                "last_updated": self._cache.last_updated,
                "processing": self._cache.processing.copy()
            }
    
    def list_media(self) -> List[Dict[str, Any]]:
        """Return all media objects."""
        with self._cache_lock:
            return list(self._cache.media.values()) if self._cache else []
    
    def get_media_dict(self) -> Dict[str, Dict[str, Any]]:
        """Return media dictionary."""
        with self._cache_lock:
            return self._cache.media.copy() if self._cache else {}
    
    def list_loop(self) -> List[str]:
        """Return loop list."""
        with self._cache_lock:
            return self._cache.loop.copy() if self._cache else []
    
    def get_active(self) -> Optional[str]:
        """Return active media slug."""
        with self._cache_lock:
            if not self._cache:
                return None
            
            # Validate active slug
            if self._cache.active and self._cache.active not in self._cache.media:
                self._cache.active = None
                self._queue_operation("clear_invalid_active")
            
            return self._cache.active
    
    def add_media(self, metadata: Dict[str, Any], set_active: bool = False) -> None:
        """Add media with batched write."""
        with self._cache_lock:
            if not self._cache:
                self._cache = MediaIndex.empty()
            
            slug = metadata["slug"]
            self._cache.media[slug] = metadata
            
            # Add to loop if not present
            if slug not in self._cache.loop:
                self._cache.loop.append(slug)
            
            # Set as active if requested or no active media
            if set_active or not self._cache.active:
                self._cache.active = slug
            
            self._queue_operation("add_media", slug)
            LOGGER.info(f"Added media: {slug} (batched write)")
    
    def remove_media(self, slug: str) -> None:
        """Remove media with immediate write for safety."""
        with self._cache_lock:
            if not self._cache:
                return
            
            # Remove from media dict
            if slug in self._cache.media:
                del self._cache.media[slug]
            
            # Remove from loop
            self._cache.loop = [s for s in self._cache.loop if s != slug]
            
            # Clear active if it was the removed media
            if self._cache.active == slug:
                self._cache.active = self._cache.loop[0] if self._cache.loop else None
            
            # Force immediate write for deletions
            self._force_immediate_write()
            LOGGER.info(f"Removed media: {slug} (immediate write)")
    
    def set_active(self, slug: Optional[str]) -> None:
        """Set active media."""
        with self._cache_lock:
            if not self._cache:
                self._cache = MediaIndex.empty()
            
            if slug and slug in self._cache.media:
                self._cache.active = slug
            else:
                self._cache.active = None
            
            self._queue_operation("set_active", slug)
    
    def set_loop_order(self, loop_order: List[str]) -> None:
        """Set loop order with validation."""
        with self._cache_lock:
            if not self._cache:
                return
            
            # Validate all slugs exist
            valid_slugs = [slug for slug in loop_order if slug in self._cache.media]
            self._cache.loop = valid_slugs
            
            self._queue_operation("reorder_loop")
    
    def add_processing_job(self, job_id: str, filename: str) -> None:
        """Add processing job with immediate write."""
        with self._cache_lock:
            if not self._cache:
                self._cache = MediaIndex.empty()
            
            self._cache.processing[job_id] = {
                "job_id": job_id,
                "filename": filename,
                "status": "processing",
                "progress": 0,
                "stage": "starting",
                "message": "Initializing...",
                "timestamp": time.time()
            }
            
            self._force_immediate_write()  # Critical operation
    
    def update_processing_job(self, job_id: str, progress: float, stage: str, message: str) -> None:
        """Update processing job progress."""
        with self._cache_lock:
            if not self._cache or job_id not in self._cache.processing:
                return
            
            self._cache.processing[job_id].update({
                "progress": min(100, max(0, progress)),
                "stage": stage,
                "message": message,
                "timestamp": time.time()
            })
            
            # Don't force immediate write for progress updates
            self._queue_operation("update_processing", job_id)
    
    def complete_processing_job(self, job_id: str, success: bool, error: str = "") -> None:
        """Complete processing job with immediate write."""
        with self._cache_lock:
            if not self._cache or job_id not in self._cache.processing:
                return
            
            self._cache.processing[job_id].update({
                "progress": 100,
                "stage": "completed" if success else "error", 
                "message": "Completed" if success else f"Error: {error}",
                "status": "completed" if success else "error",
                "timestamp": time.time()
            })
            
            self._force_immediate_write()  # Critical operation
    
    def list_processing_jobs(self) -> Dict[str, Dict[str, Any]]:
        """List all processing jobs."""
        with self._cache_lock:
            return self._cache.processing.copy() if self._cache else {}
    
    def cleanup_orphaned_files(self, media_raw_dir: Path, media_processed_dir: Path) -> int:
        """Clean up orphaned files."""
        with self._cache_lock:
            if not self._cache:
                return 0
            
            valid_slugs = set(self._cache.media.keys())
            cleanup_count = 0
            
            # Clean processed directories
            if media_processed_dir.exists():
                for item in media_processed_dir.iterdir():
                    if item.is_dir() and item.name not in valid_slugs:
                        try:
                            shutil.rmtree(item)
                            cleanup_count += 1
                        except Exception as e:
                            LOGGER.error(f"Failed to clean up {item}: {e}")
            
            # Clean raw files
            if media_raw_dir.exists():
                for item in media_raw_dir.iterdir():
                    if item.is_file():
                        file_slug = None
                        for slug in valid_slugs:
                            if slug in item.name:
                                file_slug = slug
                                break
                        
                        if not file_slug:
                            try:
                                item.unlink()
                                cleanup_count += 1
                            except Exception as e:
                                LOGGER.error(f"Failed to clean up {item}: {e}")
            
            if cleanup_count > 0:
                self._queue_operation("cleanup_orphaned")
            
            return cleanup_count
    
    def shutdown(self) -> None:
        """Graceful shutdown with final write."""
        LOGGER.info("Shutting down media index manager...")
        self._shutdown_flag = True
        
        # Force final write if needed
        with self._cache_lock:
            if self._pending_operations and self._cache:
                try:
                    self._write_to_disk_internal(self._cache)
                    LOGGER.info("Final write completed during shutdown")
                except Exception as e:
                    LOGGER.error(f"Final write failed: {e}")
        
        # Wait for background thread
        if self._writer_thread.is_alive():
            self._writer_thread.join(timeout=10)

# Global instance
media_index = HardenedMediaIndexManager()

@contextmanager
def batch_operations(media_index_manager: 'HardenedMediaIndexManager'):
    """Context manager for batching operations (no-op in hardened version)."""
    yield  # Operations are already batched automatically 