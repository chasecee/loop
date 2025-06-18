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
from typing import Dict, List, Optional, Any

from utils.logger import get_logger

LOGGER = get_logger("media_index")

MEDIA_INDEX_PATH = Path("media/index.json")
_MEDIA_DEFAULT = {"media": {}, "loop": [], "active": None, "last_updated": None}


def _read_raw() -> Dict[str, Any]:
    """Read the raw media index, handling backwards compatibility migration."""
    if not MEDIA_INDEX_PATH.exists():
        return _MEDIA_DEFAULT.copy()
    
    try:
        with open(MEDIA_INDEX_PATH, "r") as f:
            # Get an exclusive lock for reading
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                data = json.load(f)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        # Ensure we have the expected structure
        if not isinstance(data, dict):
            LOGGER.warning("Invalid media index format, resetting to default")
            return _MEDIA_DEFAULT.copy()

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

        # Ensure all required fields exist
        data.setdefault("media", {})
        data.setdefault("loop", [])
        data.setdefault("active", None)
        data.setdefault("last_updated", None)

        # Clean up orphaned slugs in loop that don't exist in media
        valid_slugs = set(data["media"].keys())
        original_loop = data["loop"][:]
        data["loop"] = [slug for slug in data["loop"] if slug in valid_slugs]
        
        if len(data["loop"]) != len(original_loop):
            LOGGER.info(f"Cleaned up {len(original_loop) - len(data['loop'])} orphaned slugs from loop")
            needs_migration = True

        # Validate active slug
        if data["active"] and data["active"] not in valid_slugs:
            LOGGER.info(f"Clearing invalid active slug: {data['active']}")
            data["active"] = data["loop"][0] if data["loop"] else None
            needs_migration = True

        # Write back if we migrated anything
        if needs_migration:
            LOGGER.info("Persisting migrated media index")
            _write_raw(data)

        return data

    except Exception as exc:
        LOGGER.error(f"Failed to read media index: {exc}")
        return _MEDIA_DEFAULT.copy()


def _write_raw(data: Dict[str, Any]) -> None:
    """Write the media index atomically with proper locking."""
    try:
        MEDIA_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a copy to avoid modifying the original
        data_to_write = data.copy()
        data_to_write["last_updated"] = int(time.time())

        # Validate data structure before writing
        if not isinstance(data_to_write.get("media"), dict):
            LOGGER.error("Invalid media format for writing")
            return
        
        if not isinstance(data_to_write.get("loop"), list):
            LOGGER.error("Invalid loop format for writing")
            return

        # Write to temporary file first for atomic operation
        temp_file = MEDIA_INDEX_PATH.with_suffix('.json.tmp')
        
        with open(temp_file, "w") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(data_to_write, f, indent=2)
                f.flush()
                os.fsync(f.fileno())  # Ensure data is written to disk
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        # Atomic rename
        shutil.move(str(temp_file), str(MEDIA_INDEX_PATH))
        LOGGER.debug("Media index written successfully")

    except Exception as exc:
        LOGGER.error(f"Failed to write media index: {exc}")
        # Clean up temp file if it exists
        if 'temp_file' in locals() and temp_file.exists():
            try:
                temp_file.unlink()
            except Exception:
                pass


# Public API -----------------------------------------------------------


def list_media() -> List[Dict[str, Any]]:
    """Return all media objects as a list."""
    media_dict = _read_raw().get("media", {})
    return list(media_dict.values())


def get_media_dict() -> Dict[str, Dict[str, Any]]:
    """Return the media dictionary directly."""
    return _read_raw().get("media", {})


def list_loop() -> List[str]:
    """Return the current loop slug list."""
    return _read_raw().get("loop", [])


def get_active() -> Optional[str]:
    """Return the currently active media slug."""
    active = _read_raw().get("active")
    
    # Validate that active slug exists in media
    if active and active not in _read_raw().get("media", {}):
        LOGGER.warning(f"Active slug {active} not found in media, clearing")
        set_active(None)
        return None
    
    return active


# Mutations ----------------------------------------------------------------


def add_media(meta: Dict[str, Any], make_active: bool = True) -> None:
    """Add a media item to the index."""
    slug = meta.get("slug")
    if not slug:
        raise ValueError("Metadata missing slug")

    data = _read_raw()
    
    # Add to media dict
    data["media"][slug] = meta

    # Add to loop if requested
    if make_active and slug not in data["loop"]:
        data["loop"].append(slug)

    # Set as active if it's the first item or explicitly requested
    if make_active and (not data["active"] or data["active"] not in data["media"]):
        data["active"] = slug

    _write_raw(data)
    LOGGER.info(f"Added media: {slug}")


def remove_media(slug: str) -> None:
    """Remove a media item completely from the index."""
    data = _read_raw()
    
    # Remove from media dict
    if slug in data["media"]:
        del data["media"][slug]
        LOGGER.info(f"Removed media from library: {slug}")
    
    # Remove from loop
    if slug in data["loop"]:
        data["loop"].remove(slug)
        LOGGER.info(f"Removed media from loop: {slug}")
    
    # Update active if it was the deleted item
    if data["active"] == slug:
        data["active"] = data["loop"][0] if data["loop"] else None
        LOGGER.info(f"Updated active media to: {data['active']}")
    
    _write_raw(data)
    LOGGER.info(f"Successfully removed media: {slug}")


def add_to_loop(slug: str) -> None:
    """Add a media item to the loop queue."""
    data = _read_raw()
    
    if slug not in data["media"]:
        raise KeyError(f"Media slug not found: {slug}")
    
    if slug not in data["loop"]:
        data["loop"].append(slug)
        _write_raw(data)
        LOGGER.info(f"Added to loop: {slug}")


def remove_from_loop(slug: str) -> None:
    """Remove a media item from the loop queue."""
    data = _read_raw()
    
    if slug in data["loop"]:
        data["loop"].remove(slug)
        
        # If this was the active item, update active
        if data["active"] == slug:
            data["active"] = data["loop"][0] if data["loop"] else None
            LOGGER.info(f"Updated active media to: {data['active']}")
        
        _write_raw(data)
        LOGGER.info(f"Removed from loop: {slug}")


def reorder_loop(new_order: List[str]) -> None:
    """Reorder the loop queue with the given slug list."""
    data = _read_raw()
    valid_slugs = set(data["media"].keys())
    
    # Only keep slugs that exist in media
    validated_order = [slug for slug in new_order if slug in valid_slugs]
    
    data["loop"] = validated_order
    
    # Ensure active is still valid
    if data["active"] and data["active"] not in validated_order:
        data["active"] = validated_order[0] if validated_order else None
    
    _write_raw(data)
    LOGGER.info(f"Reordered loop with {len(validated_order)} items")


def set_active(slug: Optional[str]) -> None:
    """Set the currently active media slug."""
    data = _read_raw()
    
    if slug is not None:
        if slug not in data["media"]:
            raise KeyError(f"Media slug not found: {slug}")
        
        # Ensure the slug is in the loop
        if slug not in data["loop"]:
            data["loop"].append(slug)
    
    data["active"] = slug
    _write_raw(data)
    LOGGER.info(f"Set active media to: {slug}")


def get_dashboard_data() -> Dict[str, Any]:
    """Get all data needed for the dashboard in a single operation."""
    data = _read_raw()
    
    return {
        "media": list(data["media"].values()),
        "loop": data["loop"],
        "active": data["active"],
        "last_updated": data["last_updated"]
    }


def cleanup_orphaned_files(media_raw_dir: Path, media_processed_dir: Path) -> int:
    """Clean up files that don't have corresponding entries in the media index."""
    data = _read_raw()
    valid_slugs = set(data["media"].keys())
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
    
    # Clean up raw files (this is trickier since we need to match by slug pattern)
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