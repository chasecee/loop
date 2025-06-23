"""Storage calculation utilities for LOOP web server."""

import os
import time
from pathlib import Path

from utils.logger import get_logger

logger = get_logger("web")

# Startup-only storage calculation with permanent cache.
# Scans once on startup, then only invalidates on actual media changes.

_STORAGE_CACHE: dict[Path, int] = {}


def _calc_dir_size_fast(path: Path) -> int:
    """Fast directory size calculation with early bailout for large directories."""
    total = 0
    if not path.exists():
        return 0
    
    try:
        # Use os.walk for better performance than recursive scandir
        for root, dirs, files in os.walk(path):
            # Limit to prevent runaway calculations
            if total > 10 * 1024**3:  # 10GB limit
                logger.warning(f"Directory size calculation truncated at 10GB for {path}")
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


def get_dir_size(path: Path) -> int:
    """Return cached dir size - scanned once on startup."""
    return _STORAGE_CACHE.get(path, 0)


def scan_storage_on_startup():
    """Scan all storage once during startup."""
    logger.info("Scanning storage sizes on startup...")
    start_time = time.time()
    
    backend_root = Path(__file__).resolve().parent.parent.parent  # core/ -> web/ -> backend/
    media_path = backend_root / "media"
    
    # Scan both directories
    media_size = _calc_dir_size_fast(media_path)
    backend_size = _calc_dir_size_fast(backend_root)
    
    _STORAGE_CACHE[media_path] = media_size
    _STORAGE_CACHE[backend_root] = backend_size
    
    scan_time = time.time() - start_time
    logger.info(f"Storage scan complete: media={media_size/1024/1024:.1f}MB, backend={backend_size/1024/1024:.1f}MB (took {scan_time:.2f}s)")


def invalidate_storage_cache():
    """Rescan storage after media changes."""
    logger.info("Media changed, rescanning storage...")
    scan_storage_on_startup() 