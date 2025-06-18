"""Utility helpers for reading/writing the media index (media/index.json).

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
from datetime import datetime

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
        """Read the raw media index, handling backwards compatibility migration."""
        if not self.index_path.exists():
            return MediaIndex.empty()
        
        try:
            with open(self.index_path, "r") as f:
                # Get an exclusive lock for reading
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    data = json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            # Validate structure
            if not isinstance(data, dict):
                LOGGER.warning("Invalid media index format, resetting to default")
                return MediaIndex.empty()

            # Backwards compatibility: convert old list format to dict format
            needs_migration = False
            
            # Handle old media list format
            if isinstance(data.get("media"), list):
                LOGGER.info("Migrating media from list to dict format")
                media_dict = {}
                for item in data["media"]:
                    if isinstance(item, dict) and "slug" in item:
                        media_dict[item["slug"]] = item
                data["media"] = media_dict
                needs_migration = True

            # Handle old loop format (if it contains objects instead of slugs)
            loop_raw = data.get("loop", [])
            if loop_raw and isinstance(loop_raw[0], dict):
                LOGGER.info("Migrating loop from object list to slug list")
                data["loop"] = [item.get("slug") for item in loop_raw if isinstance(item, dict) and item.get("slug")]
                needs_migration = True

            # Create MediaIndex with validated data
            index = MediaIndex(
                media=data.get("media", {}),
                loop=data.get("loop", []),
                active=data.get("active"),
                last_updated=data.get("last_updated")
            )

            # Clean up orphaned slugs in loop that don't exist in media
            valid_slugs = set(index.media.keys())
            original_loop = index.loop[:]
            index.loop = [slug for slug in index.loop if slug in valid_slugs]
            
            if len(index.loop) != len(original_loop):
                LOGGER.info(f"Cleaned up {len(original_loop) - len(index.loop)} orphaned slugs from loop")
                needs_migration = True

            # Validate active slug
            if index.active and index.active not in valid_slugs:
                LOGGER.info(f"Clearing invalid active slug: {index.active}")
                index.active = index.loop[0] if index.loop else None
                needs_migration = True

            # Write back if we migrated anything
            if needs_migration:
                LOGGER.info("Persisting migrated media index")
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

# Global instance for backward compatibility
_manager = MediaIndexManager()

# Legacy API functions for backward compatibility
def list_media() -> List[Dict[str, Any]]:
    """Return all media objects as a list."""
    return _manager.list_media()

def get_media_dict() -> Dict[str, Dict[str, Any]]:
    """Return the media dictionary directly."""
    return _manager.get_media_dict()

def list_loop() -> List[str]:
    """Return the current loop slug list."""
    return _manager.list_loop()

def get_active() -> Optional[str]:
    """Return the currently active media slug."""
    return _manager.get_active()

def add_media(meta: Dict[str, Any], make_active: bool = True) -> None:
    """Add a media item to the index."""
    return _manager.add_media(meta, make_active)

def remove_media(slug: str) -> None:
    """Remove a media item completely from the index."""
    return _manager.remove_media(slug)

def add_to_loop(slug: str) -> None:
    """Add a media item to the loop queue."""
    return _manager.add_to_loop(slug)

def remove_from_loop(slug: str) -> None:
    """Remove a media item from the loop queue."""
    return _manager.remove_from_loop(slug)

def reorder_loop(new_order: List[str]) -> None:
    """Reorder the loop queue with the given slug list."""
    return _manager.reorder_loop(new_order)

def set_active(slug: Optional[str]) -> None:
    """Set the currently active media slug."""
    return _manager.set_active(slug)

def get_dashboard_data() -> Dict[str, Any]:
    """Get all data needed for the dashboard in a single operation."""
    return _manager.get_dashboard_data()

def cleanup_orphaned_files(media_raw_dir: Path, media_processed_dir: Path) -> int:
    """Clean up files that don't have corresponding entries in the media index."""
    return _manager.cleanup_orphaned_files(media_raw_dir, media_processed_dir) 