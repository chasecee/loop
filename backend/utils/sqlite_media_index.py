"""
SQLite-based media index manager.

Clean, efficient SQLite operations for media management.
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import functools

from utils.logger import get_logger

LOGGER = get_logger("sqlite_media_index")

def retry_on_database_error(max_retries: int = 3, delay: float = 0.1):
    """Decorator to retry database operations on transient failures."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    # Retry on database locked errors
                    if "database is locked" in str(e).lower() and attempt < max_retries:
                        LOGGER.warning(f"Database locked, retrying in {delay}s (attempt {attempt + 1}/{max_retries + 1})")
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                        last_exception = e
                        continue
                    raise
                except sqlite3.DatabaseError as e:
                    # Retry on certain database errors
                    if attempt < max_retries and ("busy" in str(e).lower() or "locked" in str(e).lower()):
                        LOGGER.warning(f"Database error, retrying in {delay}s (attempt {attempt + 1}/{max_retries + 1}): {e}")
                        time.sleep(delay * (2 ** attempt))
                        last_exception = e
                        continue
                    raise
            # If we get here, all retries failed
            if last_exception:
                raise last_exception
        return wrapper
    return decorator

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
    processing_status: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class ProcessingJob:
    """Type-safe processing job structure."""
    job_id: str
    filename: str
    status: str
    progress: float
    stage: str
    message: str
    timestamp: float

class SQLiteMediaIndexManager:
    """SQLite-based media index manager with Pi optimizations."""
    
    def __init__(self, db_path: str = "media/media.db"):
        """Initialize SQLite media index manager."""
        self.db_path = Path(db_path)
        
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        LOGGER.info(f"SQLiteMediaIndexManager initialized: {self.db_path}")
    
    def _init_database(self) -> None:
        """Initialize SQLite database with Pi-optimized settings."""
        with self._get_connection() as conn:
            # Pi optimization pragmas
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=2000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA auto_vacuum=INCREMENTAL")
            conn.execute("PRAGMA mmap_size=268435456")
            
            # Create tables
            conn.execute("""
                CREATE TABLE IF NOT EXISTS media (
                    slug TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    type TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    url TEXT,
                    duration REAL,
                    width INTEGER,
                    height INTEGER,
                    frame_count INTEGER,
                    processing_status TEXT DEFAULT 'completed',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS loop_order (
                    position INTEGER PRIMARY KEY,
                    slug TEXT NOT NULL,
                    FOREIGN KEY (slug) REFERENCES media(slug) ON DELETE CASCADE
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processing_jobs (
                    job_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'processing',
                    progress REAL NOT NULL DEFAULT 0,
                    stage TEXT NOT NULL DEFAULT 'starting',
                    message TEXT NOT NULL DEFAULT 'Initializing...',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_media_status ON media(processing_status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_media_uploaded ON media(uploaded_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_loop_position ON loop_order(position)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON processing_jobs(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_updated ON processing_jobs(updated_at)")
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with SQLite-specific error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.IntegrityError as e:
            if conn:
                conn.rollback()
            LOGGER.error(f"Database constraint violation: {e}")
            raise
        except sqlite3.OperationalError as e:
            if conn:
                conn.rollback()
            LOGGER.error(f"Database operational error (likely locked): {e}")
            raise
        except sqlite3.DatabaseError as e:
            if conn:
                conn.rollback()
            LOGGER.error(f"Database error: {e}")
            raise
        except Exception as e:
            if conn:
                conn.rollback()
            LOGGER.error(f"Unexpected error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    

    
    # Public API - identical signatures to HardenedMediaIndexManager
    
    @retry_on_database_error()
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get all data for dashboard."""
        with self._get_connection() as conn:
            # Get all media with proper field name mapping
            media_rows = conn.execute("""
                SELECT slug, filename, type, size, uploaded_at as uploadedAt, url, duration,
                       width, height, frame_count, processing_status
                FROM media ORDER BY uploaded_at DESC
            """).fetchall()
            
            media_list = [dict(row) for row in media_rows]
            
            # Get loop order
            loop_rows = conn.execute("""
                SELECT slug FROM loop_order ORDER BY position
            """).fetchall()
            
            loop_list = [row['slug'] for row in loop_rows]
            
            # Get active media
            active_row = conn.execute("""
                SELECT value FROM settings WHERE key = 'active'
            """).fetchone()
            
            active = active_row['value'] if active_row else None
            
            # Get last updated
            updated_row = conn.execute("""
                SELECT value FROM settings WHERE key = 'last_updated'
            """).fetchone()
            
            last_updated = int(updated_row['value']) if updated_row else int(time.time())
            
            # Get recent processing jobs (active and recently completed) with optimized timestamp conversion
            recent_cutoff = int(time.time() - 300)  # 5 minutes
            processing_rows = conn.execute("""
                SELECT job_id, filename, status, progress, stage, message,
                       strftime('%s', updated_at) as timestamp
                FROM processing_jobs
                WHERE status = 'processing' OR strftime('%s', updated_at) > ?
                ORDER BY updated_at DESC
                LIMIT 20
            """, (str(recent_cutoff),)).fetchall()
            
            processing = {
                row['job_id']: {
                    'job_id': row['job_id'],
                    'filename': row['filename'],
                    'status': row['status'],
                    'progress': row['progress'],
                    'stage': row['stage'],
                    'message': row['message'],
                    'timestamp': float(row['timestamp'])
                }
                for row in processing_rows
            }
            
            return {
                "media": media_list,
                "loop": loop_list,
                "active": active,
                "last_updated": last_updated,
                "processing": processing
            }
    
    def list_media(self) -> List[str]:
        """List all media slugs."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT slug FROM media ORDER BY uploaded_at DESC").fetchall()
            return [row['slug'] for row in rows]
    
    def get_media_dict(self) -> Dict[str, Dict[str, Any]]:
        """Get media dictionary."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT slug, filename, type, size, uploaded_at as uploadedAt, url, duration,
                       width, height, frame_count, processing_status
                FROM media ORDER BY uploaded_at DESC
            """).fetchall()
            
            return {
                row['slug']: {
                    k: v for k, v in dict(row).items() 
                    if v is not None
                }
                for row in rows
            }
    
    def list_loop(self) -> List[str]:
        """Get loop order."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT slug FROM loop_order ORDER BY position
            """).fetchall()
            return [row['slug'] for row in rows]
    
    def get_active(self) -> Optional[str]:
        """Get active media slug."""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT value FROM settings WHERE key = 'active'
            """).fetchone()
            return row['value'] if row else None
    
    def set_active(self, slug: Optional[str]) -> None:
        """Set active media."""
        with self._get_connection() as conn:
            if slug:
                # Verify slug exists
                exists = conn.execute("""
                    SELECT 1 FROM media WHERE slug = ?
                """, (slug,)).fetchone()
                
                if not exists:
                    LOGGER.warning(f"Cannot set active media to non-existent slug: {slug}")
                    return
            
            conn.execute("""
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES ('active', ?, datetime('now'))
            """, (slug,))
            
            conn.commit()
    
    def add_media(self, slug: str, media_data: Dict[str, Any]) -> None:
        """Add media."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO media 
                (slug, filename, type, size, uploaded_at, url, duration,
                 width, height, frame_count, processing_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                slug,
                media_data.get('filename', ''),
                media_data.get('type', ''),
                media_data.get('size', 0),
                media_data.get('uploadedAt', ''),
                media_data.get('url'),
                media_data.get('duration'),
                media_data.get('width'),
                media_data.get('height'),
                media_data.get('frame_count'),
                media_data.get('processing_status', 'completed')
            ))
            
            # Update last_updated
            conn.execute("""
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES ('last_updated', ?, datetime('now'))
            """, (str(int(time.time())),))
            
            conn.commit()
    
    def remove_media(self, slug: str) -> None:
        """Remove media (cascade removes from loop_order)."""
        with self._get_connection() as conn:
            # Remove media (cascades to loop_order due to FK)
            conn.execute("DELETE FROM media WHERE slug = ?", (slug,))
            
            # Clear active if it was the removed media
            active = conn.execute("""
                SELECT value FROM settings WHERE key = 'active'
            """).fetchone()
            
            if active and active['value'] == slug:
                conn.execute("""
                    DELETE FROM settings WHERE key = 'active'
                """)
            
            # Update last_updated
            conn.execute("""
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES ('last_updated', ?, datetime('now'))
            """, (str(int(time.time())),))
            
            conn.commit()
    
    @retry_on_database_error()
    def reorder_loop(self, loop_order: List[str]) -> None:
        """Reorder loop with validation and explicit transaction."""
        with self._get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")  # Explicit transaction start
            try:
                # Validate all slugs exist
                valid_slugs = []
                for slug in loop_order:
                    exists = conn.execute("""
                        SELECT 1 FROM media WHERE slug = ?
                    """, (slug,)).fetchone()
                    if exists:
                        valid_slugs.append(slug)
                
                # Atomic replacement of loop order
                conn.execute("DELETE FROM loop_order")
                
                for position, slug in enumerate(valid_slugs):
                    conn.execute("""
                        INSERT INTO loop_order (position, slug) VALUES (?, ?)
                    """, (position, slug))
                
                conn.commit()
            except Exception:
                conn.rollback()
                raise
    
    def add_to_loop(self, slug: str) -> None:
        """Add media to loop if not already present."""
        with self._get_connection() as conn:
            # Check if media exists
            media_exists = conn.execute("""
                SELECT 1 FROM media WHERE slug = ?
            """, (slug,)).fetchone()
            
            if not media_exists:
                return
            
            # Check if already in loop
            in_loop = conn.execute("""
                SELECT 1 FROM loop_order WHERE slug = ?
            """, (slug,)).fetchone()
            
            if in_loop:
                return
            
            # Get next position
            max_pos = conn.execute("""
                SELECT COALESCE(MAX(position), -1) FROM loop_order
            """).fetchone()[0]
            
            conn.execute("""
                INSERT INTO loop_order (position, slug) VALUES (?, ?)
            """, (max_pos + 1, slug))
            
            conn.commit()
            LOGGER.info(f"Added to loop: {slug}")
    
    @retry_on_database_error()
    def remove_from_loop(self, slug: str) -> None:
        """Remove media from loop with explicit transaction."""
        with self._get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")  # Explicit transaction start
            try:
                # Remove from loop
                conn.execute("DELETE FROM loop_order WHERE slug = ?", (slug,))
                
                # Recompact positions
                rows = conn.execute("""
                    SELECT slug FROM loop_order ORDER BY position
                """).fetchall()
                
                conn.execute("DELETE FROM loop_order")
                
                for position, row in enumerate(rows):
                    conn.execute("""
                        INSERT INTO loop_order (position, slug) VALUES (?, ?)
                    """, (position, row['slug']))
                
                # Clear active if it was the removed media
                active = conn.execute("""
                    SELECT value FROM settings WHERE key = 'active'
                """).fetchone()
                
                if active and active['value'] == slug:
                    # Set new active to first in loop
                    first_in_loop = conn.execute("""
                        SELECT slug FROM loop_order ORDER BY position LIMIT 1
                    """).fetchone()
                    
                    new_active = first_in_loop['slug'] if first_in_loop else None
                    
                    if new_active:
                        conn.execute("""
                            INSERT OR REPLACE INTO settings (key, value, updated_at)
                            VALUES ('active', ?, datetime('now'))
                        """, (new_active,))
                    else:
                        conn.execute("DELETE FROM settings WHERE key = 'active'")
                
                conn.commit()
                LOGGER.info(f"Removed from loop: {slug}")
            except Exception:
                conn.rollback()
                raise
    
    def add_processing_job(self, job_id: str, filename: str) -> None:
        """Add processing job."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO processing_jobs
                (job_id, filename, status, progress, stage, message, updated_at)
                VALUES (?, ?, 'processing', 0, 'starting', 'Initializing...', datetime('now'))
            """, (job_id, filename))
            
            conn.commit()
    
    def update_processing_job(self, job_id: str, progress: float, stage: str, message: str) -> None:
        """Update processing job progress."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE processing_jobs 
                SET progress = ?, stage = ?, message = ?, updated_at = datetime('now')
                WHERE job_id = ?
            """, (min(100, max(0, progress)), stage, message, job_id))
            
            conn.commit()
    
    def complete_processing_job(self, job_id: str, success: bool, error: str = "") -> None:
        """Complete processing job."""
        status = "completed" if success else "error"
        message = "Completed" if success else f"Error: {error}"
        
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE processing_jobs
                SET progress = 100, stage = ?, message = ?, status = ?, updated_at = datetime('now')
                WHERE job_id = ?
            """, (status, message, status, job_id))
            
            conn.commit()
    
    def list_processing_jobs(self) -> Dict[str, Dict[str, Any]]:
        """List all processing jobs (let caller filter by recency)."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT job_id, filename, status, progress, stage, message,
                       strftime('%s', updated_at) as timestamp
                FROM processing_jobs
                ORDER BY updated_at DESC
                LIMIT 50
            """).fetchall()
            
            return {
                row['job_id']: {
                    'job_id': row['job_id'],
                    'filename': row['filename'],
                    'status': row['status'],
                    'progress': row['progress'],
                    'stage': row['stage'],
                    'message': row['message'],
                    'timestamp': float(row['timestamp'])
                }
                for row in rows
            }
    
    def cleanup_orphaned_files(self, media_raw_dir: Path, media_processed_dir: Path) -> int:
        """Clean up orphaned files."""
        import shutil
        
        with self._get_connection() as conn:
            # Get valid slugs
            rows = conn.execute("SELECT slug FROM media").fetchall()
            valid_slugs = {row['slug'] for row in rows}
            
            cleanup_count = 0
            
            # Clean processed directories
            if media_processed_dir.exists():
                for item in media_processed_dir.iterdir():
                    if item.is_dir() and item.name not in valid_slugs:
                        try:
                            shutil.rmtree(item)
                            cleanup_count += 1
                        except OSError as e:
                            LOGGER.error(f"Failed to clean up directory {item}: {e}")
                        except Exception as e:
                            LOGGER.error(f"Unexpected error cleaning up {item}: {e}")
            
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
                            except OSError as e:
                                LOGGER.error(f"Failed to clean up file {item}: {e}")
                            except Exception as e:
                                LOGGER.error(f"Unexpected error cleaning up {item}: {e}")
            
            return cleanup_count
    
    def shutdown(self) -> None:
        """Graceful shutdown (no-op for SQLite)."""
        LOGGER.info("SQLite media index manager shutdown complete") 