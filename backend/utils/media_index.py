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
    "last_updated": 1700000000
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class MediaIndex:
    """Type-safe media index structure."""
    media: Dict[str, Dict[str, Any]]
    loop: List[str]
    active: Optional[str]
    last_updated: Optional[int]
    
    @classmethod
    def empty(cls) -> 'MediaIndex':
        """Create empty media index."""
        return cls(
            media={},
            loop=[],
            active=None,
            last_updated=None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "media": self.media,
            "loop": self.loop,
            "active": self.active,
            "last_updated": self.last_updated or int(time.time())
        }

class MediaIndexManager:
    """Thread-safe manager for media index operations."""
    
    def __init__(self, index_path: Path = MEDIA_INDEX_PATH):
        self.index_path = index_path
        self._ensure_media_dir()
    
    def _ensure_media_dir(self) -> None:
        """Ensure media directory exists."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _read_raw(self) -> MediaIndex:
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

            # Create MediaIndex with validated data
            index = MediaIndex(
                media=data.get("media", {}),
                loop=data.get("loop", []),
                active=data.get("active"),
                last_updated=data.get("last_updated")
            )

            # Validate data integrity
            valid_slugs = set(index.media.keys())
            
            # Clean up orphaned slugs in loop
            original_loop_length = len(index.loop)
            index.loop = [slug for slug in index.loop if slug in valid_slugs]
            
            if len(index.loop) != original_loop_length:
                LOGGER.info(f"Cleaned up {original_loop_length - len(index.loop)} orphaned slugs from loop")
                self._write_raw(index)

            # Validate active slug
            if index.active and index.active not in valid_slugs:
                LOGGER.info(f"Clearing invalid active slug: {index.active}")
                index.active = index.loop[0] if index.loop else None
                self._write_raw(index)

            return index

        except Exception as exc:
            LOGGER.error(f"Failed to read media index: {exc}")
            return MediaIndex.empty()

    def _write_raw(self, index: MediaIndex) -> None:
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
            LOGGER.debug(f"Media index written successfully ({len(index.media)} items, {len(index.loop)} in loop)")

        except Exception as exc:
            LOGGER.error(f"Failed to write media index: {exc}")
            # Clean up temp file if it exists
            if 'temp_file' in locals() and temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass

    # Public API methods
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get all data needed for the dashboard in a single operation."""
        index = self._read_raw()
        return {
            "media": list(index.media.values()),
            "loop": index.loop,
            "active": index.active,
            "last_updated": index.last_updated
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