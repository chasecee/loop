"""Storage calculation utilities for LOOP web server."""

import os
import time
import json
from pathlib import Path

from utils.logger import get_logger

logger = get_logger("web")

# Aggressive caching with persistence for Pi Zero 2 performance
_STORAGE_CACHE: dict[Path, int] = {}
_CACHE_FILE = Path("media/.storage_cache.json")
_LAST_SCAN_TIME = 0
_SCAN_INTERVAL = 300  # Only rescan every 5 minutes max


def _calc_dir_size_fast(path: Path) -> int:
    """Fast directory size calculation with early bailout for large directories."""
    total = 0
    if not path.exists():
        return 0
    
    try:
        # Use os.walk for better performance than recursive scandir
        for root, dirs, files in os.walk(path):
            # More aggressive limit to prevent runaway calculations on Pi Zero 2
            if total > 5 * 1024**3:  # 5GB limit (reduced from 10GB)
                logger.warning(f"Directory size calculation truncated at 5GB for {path}")
                break
                
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    total += os.path.getsize(file_path)
                except (OSError, IOError):
                    # Skip files we can't read
                    continue
    except (OSError, IOError) as e:
        logger.warning(f"Error calculating directory size for {path}: {e}")
        return 0
    
    return total


def _load_cache_from_disk():
    """Load cached storage data from disk."""
    global _STORAGE_CACHE, _LAST_SCAN_TIME
    
    try:
        if _CACHE_FILE.exists():
            with open(_CACHE_FILE, 'r') as f:
                data = json.load(f)
                _STORAGE_CACHE = {Path(k): v for k, v in data.get('cache', {}).items()}
                _LAST_SCAN_TIME = data.get('last_scan', 0)
                logger.info(f"Loaded storage cache from disk ({len(_STORAGE_CACHE)} entries)")
    except Exception as e:
        logger.warning(f"Failed to load storage cache: {e}")


def _save_cache_to_disk():
    """Save cached storage data to disk."""
    try:
        _CACHE_FILE.parent.mkdir(exist_ok=True)
        data = {
            'cache': {str(k): v for k, v in _STORAGE_CACHE.items()},
            'last_scan': _LAST_SCAN_TIME
        }
        with open(_CACHE_FILE, 'w') as f:
            json.dump(data, f)
        logger.debug("Saved storage cache to disk")
    except Exception as e:
        logger.warning(f"Failed to save storage cache: {e}")


def get_dir_size(path: Path) -> int:
    """Return cached dir size - scanned once on startup or from persistent cache."""
    return _STORAGE_CACHE.get(path, 0)


def scan_storage_on_startup():
    """Scan storage with aggressive caching and persistence."""
    global _LAST_SCAN_TIME
    
    # Load existing cache first
    _load_cache_from_disk()
    
    current_time = time.time()
    
    # Skip scan if we have recent cached data (unless forced)
    if _LAST_SCAN_TIME > 0 and (current_time - _LAST_SCAN_TIME) < _SCAN_INTERVAL:
        logger.info(f"Using cached storage data (last scan {int(current_time - _LAST_SCAN_TIME)}s ago)")
        return
    
    logger.info("Scanning storage sizes (this may take a while on Pi Zero 2)...")
    start_time = time.time()
    
    backend_root = Path(__file__).resolve().parent.parent.parent  # core/ -> web/ -> backend/
    media_path = backend_root / "media"
    
    # Scan both directories
    media_size = _calc_dir_size_fast(media_path)
    backend_size = _calc_dir_size_fast(backend_root)
    
    _STORAGE_CACHE[media_path] = media_size
    _STORAGE_CACHE[backend_root] = backend_size
    _LAST_SCAN_TIME = current_time
    
    # Save to disk for next startup
    _save_cache_to_disk()
    
    scan_time = time.time() - start_time
    logger.info(f"Storage scan complete: media={media_size/1024/1024:.1f}MB, backend={backend_size/1024/1024:.1f}MB (took {scan_time:.2f}s)")


def invalidate_storage_cache():
    """Force rescan storage after media changes, but rate-limited."""
    global _LAST_SCAN_TIME
    
    current_time = time.time()
    
    # Rate limit storage rescans to prevent hammering SD card
    if (current_time - _LAST_SCAN_TIME) < 60:  # No more than once per minute
        logger.debug("Storage cache invalidation rate-limited")
        return
    
    logger.info("Media changed, rescanning storage...")
    scan_storage_on_startup() 