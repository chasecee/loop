"""Dashboard route with intelligent caching and performance optimization."""

import shutil
import time
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import APIRouter, Request, HTTPException

from ..core.models import DashboardData, DeviceStatus, PlayerStatus, WiFiStatus, UpdateStatus, StorageInfo, APIResponse, ProcessingJobResponse, MediaItem
from ..core.storage import get_dir_size, get_storage_stats
from display.player import DisplayPlayer
from boot.wifi import WiFiManager
from deployment.updater import SystemUpdater
from utils.media_index import media_index
from utils.logger import get_logger

logger = get_logger("web.dashboard")

# Smart caching for expensive operations
_dashboard_cache: Dict[str, Any] = {}
_cache_timestamps: Dict[str, float] = {}
_cache_locks: Dict[str, bool] = {}

async def collect_device_status(
    display_player: DisplayPlayer = None,
    wifi_manager: WiFiManager = None,
    updater: SystemUpdater = None
) -> DeviceStatus:
    """Shared device status collection logic for dashboard and WebSocket routes."""
    device_status = DeviceStatus()

    if display_player:
        try:
            player_data = display_player.get_status()
            device_status.player = PlayerStatus(**player_data)
        except Exception:
            pass

    if wifi_manager:
        try:
            wifi_data = wifi_manager.get_status()
            device_status.wifi = WiFiStatus(**wifi_data)
        except Exception:
            pass

    if updater:
        try:
            update_data = updater.get_update_status()
            device_status.updates = UpdateStatus(**update_data)
        except Exception:
            pass

    return device_status

def create_dashboard_router(
    display_player: DisplayPlayer = None,
    wifi_manager: WiFiManager = None,
    updater: SystemUpdater = None
) -> APIRouter:
    """Create dashboard router with dependencies."""
    
    router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
    
    def get_storage_info():
        """Get storage information - completely separate from dashboard."""
        total, used, free = shutil.disk_usage("/")

        backend_root = Path(__file__).resolve().parent.parent.parent
        media_path = backend_root / "media"
        media_size = get_dir_size(media_path)
        backend_size = get_dir_size(backend_root)
        app_size = max(0, backend_size - media_size)
        system_size = max(0, used - backend_size)

        return StorageInfo(
            total=total,
            used=used,
            free=free,
            system=system_size,
            app=app_size,
            media=media_size,
        )
    
    def _get_cached_or_compute(key: str, compute_fn, ttl: int = 60, force_refresh: bool = False) -> Any:
        """Get cached value or compute if stale/missing."""
        current_time = time.time()
        
        # Check if we have fresh cached data
        if not force_refresh and key in _dashboard_cache:
            cache_age = current_time - _cache_timestamps.get(key, 0)
            if cache_age < ttl:
                return _dashboard_cache[key]
        
        # Check if computation is already in progress
        if _cache_locks.get(key, False):
            # Return stale data if available while computation is in progress
            if key in _dashboard_cache:
                logger.debug(f"Returning stale {key} data while computation in progress")
                return _dashboard_cache[key]
            else:
                # Wait briefly for in-progress computation
                time.sleep(0.1)
                if key in _dashboard_cache:
                    return _dashboard_cache[key]
        
        # Compute new value
        _cache_locks[key] = True
        try:
            logger.debug(f"Computing fresh {key} data")
            result = compute_fn()
            _dashboard_cache[key] = result
            _cache_timestamps[key] = current_time
            return result
        except Exception as e:
            logger.error(f"Failed to compute {key}: {e}")
            # Return stale data if available
            if key in _dashboard_cache:
                logger.warning(f"Using stale {key} data due to computation error")
                return _dashboard_cache[key]
            raise
        finally:
            _cache_locks[key] = False

    @router.get("", response_model=DashboardData)
    async def get_dashboard(request: Request) -> DashboardData:
        """Get dashboard data with intelligent caching."""
        try:
            start_time = time.time()
            
            # Get core data (cached separately to avoid recomputing everything)
            media_data = _get_cached_or_compute(
                "media_list", 
                lambda: _get_media_data(),
                ttl=30  # 30 second cache for media list
            )
            
            loop_data = _get_cached_or_compute(
                "loop_status",
                lambda: _get_loop_status(), 
                ttl=10  # 10 second cache for loop status
            )
            
            player_status = _get_cached_or_compute(
                "player_status",
                lambda: _get_player_status(),
                ttl=5  # 5 second cache for player status
            )
            
            system_status = _get_cached_or_compute(
                "system_status", 
                lambda: _get_system_status(),
                ttl=60  # 1 minute cache for system status
            )
            
            wifi_status = _get_cached_or_compute(
                "wifi_status",
                lambda: _get_wifi_status(),
                ttl=30  # 30 second cache for WiFi status
            )
            
            processing_jobs = _get_cached_or_compute(
                "processing_jobs",
                lambda: _get_processing_jobs(),
                ttl=5  # 5 second cache for processing jobs
            )
            
            # Get active media
            active_media = _get_cached_or_compute(
                "active_media",
                lambda: _get_active_media(),
                ttl=5  # 5 second cache for active media
            )
            
            # Build device status
            device_status = DeviceStatus(
                player=player_status,
                wifi=wifi_status,
                updates=system_status
            )
            
            response_time = time.time() - start_time
            logger.info(f"Dashboard response generated in {response_time:.3f}s")
            
            return DashboardData(
                status=device_status,
                media=media_data,
                loop=loop_data,
                active=active_media,
                last_updated=int(time.time()),
                processing=processing_jobs
            )
            
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")

    @router.get("/storage", response_model=StorageInfo)
    async def get_storage():
        """Get storage information separately - for settings modal only."""
        return get_storage_info()
    
    @router.get("/memory", response_model=APIResponse)
    async def get_memory_stats():
        """Get memory pool statistics for performance monitoring."""
        try:
            from display.memory_pool import get_memory_stats
            stats = get_memory_stats()
            return APIResponse(
                success=True,
                data=stats
            )
        except Exception as e:
            logger.warning(f"Failed to get memory stats: {e}")
            return APIResponse(
                success=False,
                message="Memory stats unavailable",
                data={}
            )
    
    return router

def invalidate_dashboard_cache():
    """Invalidate the dashboard cache to force refresh on next request."""
    global _dashboard_cache, _cache_timestamps
    _dashboard_cache = {}
    _cache_timestamps = {}
    logger.debug("Dashboard cache invalidated")

def _get_media_data():
    """Get media data efficiently."""
    from utils.media_index import media_index
    
    # Get only essential fields to reduce memory usage
    media_dict = media_index.get_media_dict()
    media_list = []
    
    for slug, data in media_dict.items():
        # Only return essential fields for dashboard
        essential_media = {
            "slug": slug,
            "filename": data.get("filename", "Unknown"),
            "type": data.get("type", "unknown"),
            "size": data.get("size", 0),
            "uploadedAt": data.get("uploadedAt", ""),
            "processing_status": data.get("processing_status", "unknown"),
        }
        
        # Add optional fields only if they exist
        if "duration" in data:
            essential_media["duration"] = data["duration"]
        if "frame_count" in data:
            essential_media["frame_count"] = data["frame_count"]
            
        media_list.append(essential_media)
    
    return media_list

def _get_loop_status():
    """Get loop status efficiently."""
    from utils.media_index import media_index
    return media_index.list_loop()

def _get_storage_info():
    """Get storage info with caching."""
    from ..core.storage import get_storage_stats
    return get_storage_stats()

def _get_player_status():
    """Get player status efficiently."""
    from display.player import display_player
    if display_player:
        return display_player.get_status()
    return {"running": False, "active_media": None}

def _get_system_status():
    """Get system status efficiently.""" 
    from deployment.updater import system_updater
    if system_updater:
        return system_updater.get_status()
    return {"update_available": False}

def _get_wifi_status():
    """Get WiFi status efficiently."""
    from boot.wifi import wifi_manager
    if wifi_manager:
        return wifi_manager.get_status()
    return {"connected": False, "hotspot_active": False}

def _get_processing_jobs():
    """Get processing jobs efficiently."""
    from utils.media_index import media_index
    
    try:
        # Get processing jobs (SQLite method already filters for recent ones)
        jobs_dict = media_index.list_processing_jobs()
        
        # Convert to ProcessingJobResponse objects for API
        active_jobs = {}
        
        for job_id, job_data in jobs_dict.items():
            active_jobs[job_id] = ProcessingJobResponse(
                job_id=job_data.get("job_id", job_id),
                filename=job_data.get("filename", "Unknown"),
                status=job_data.get("status", "processing"),
                progress=job_data.get("progress", 0.0),
                stage=job_data.get("stage", "Processing"),
                message=job_data.get("message", ""),
                timestamp=job_data.get("timestamp", time.time())
            )
        
        return active_jobs
    except Exception as e:
        logger.warning(f"Failed to get processing jobs: {e}")
        return {}

def _get_active_media():
    """Get active media efficiently."""
    from utils.media_index import media_index
    return media_index.get_active() 