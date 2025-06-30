"""
Simple polling endpoints for LOOP - replaces WebSocket complexity.
Frontend polls these endpoints every 5-10 seconds for updates.
"""

import time
from typing import Dict, Any, Optional
from fastapi import APIRouter

from display.hardened_player import HardenedDisplayPlayer as DisplayPlayer
from boot.wifi import WiFiManager
from deployment.updater import SystemUpdater
from utils.media_index import media_index
from ..core.models import APIResponse
from utils.logger import get_logger

logger = get_logger("polling")

def create_polling_router(
    display_player: DisplayPlayer = None,
    wifi_manager: WiFiManager = None,
    updater: SystemUpdater = None
) -> APIRouter:
    """Create polling router for frontend state updates."""
    
    router = APIRouter(prefix="/api/poll", tags=["polling"])
    
    @router.get("/status", response_model=APIResponse)
    async def poll_system_status():
        """
        Get complete system status for frontend polling.
        Frontend calls this every 5-10 seconds instead of WebSocket.
        """
        try:
            # Collect all system state in one call
            status_data = {
                "timestamp": time.time(),
                "player": {},
                "wifi": {},
                "updates": {},
                "media": {},
                "processing": {}
            }
            
            # Player status
            if display_player:
                try:
                    player_status = display_player.get_status()
                    status_data["player"] = player_status
                except Exception as e:
                    logger.warning(f"Failed to get player status: {e}")
                    status_data["player"] = {"error": "Player unavailable"}
            
            # WiFi status
            if wifi_manager:
                try:
                    status_data["wifi"] = wifi_manager.get_status()
                except Exception as e:
                    logger.warning(f"Failed to get WiFi status: {e}")
                    status_data["wifi"] = {"error": "WiFi unavailable"}
            
            # Update status
            if updater:
                try:
                    status_data["updates"] = updater.get_update_status()
                except Exception as e:
                    logger.warning(f"Failed to get update status: {e}")
                    status_data["updates"] = {"error": "Updates unavailable"}
            
            # Media status
            try:
                media_list = media_index.list_media()
                loop_order = media_index.list_loop()
                active_media = media_index.get_active()
                
                status_data["media"] = {
                    "total_count": len(media_list),
                    "loop_count": len(loop_order),
                    "active": active_media,
                    "has_media": len(media_list) > 0
                }
            except Exception as e:
                logger.warning(f"Failed to get media status: {e}")
                status_data["media"] = {"error": "Media unavailable"}
            
            # Processing jobs
            try:
                processing_jobs = media_index.list_processing_jobs()
                active_jobs = {
                    job_id: job_data for job_id, job_data in processing_jobs.items()
                    if job_data.get("status") == "processing"
                }
                
                status_data["processing"] = {
                    "active_jobs": len(active_jobs),
                    "jobs": active_jobs if active_jobs else {}
                }
            except Exception as e:
                logger.warning(f"Failed to get processing status: {e}")
                status_data["processing"] = {"error": "Processing unavailable"}
            
            return APIResponse(
                success=True,
                data=status_data
            )
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return APIResponse(
                success=False,
                message=f"Status polling failed: {e}",
                data={"timestamp": time.time()}
            )
    
    @router.get("/progress", response_model=APIResponse)
    async def poll_upload_progress():
        """
        Get upload/processing progress for active jobs.
        Called frequently during uploads/processing.
        """
        try:
            processing_jobs = media_index.list_processing_jobs()
            
            # Only return active processing jobs with full details
            active_progress = {}
            for job_id, job_data in processing_jobs.items():
                if job_data.get("status") == "processing":
                    active_progress[job_id] = {
                        "filename": job_data.get("filename", "Unknown"),
                        "progress": job_data.get("progress", 0),
                        "stage": job_data.get("stage", "processing"),
                        "message": job_data.get("message", "Processing..."),
                        "timestamp": job_data.get("timestamp", time.time())
                    }
            
            return APIResponse(
                success=True,
                data={
                    "active_jobs": active_progress,
                    "timestamp": time.time()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to get progress: {e}")
            return APIResponse(
                success=False,
                message=f"Progress polling failed: {e}",
                data={"timestamp": time.time()}
            )
    
    @router.get("/health", response_model=APIResponse)
    async def poll_system_health():
        """
        Simple health check endpoint.
        Returns basic system health indicators.
        """
        try:
            import psutil
            
            # Basic system metrics
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_data = {
                "timestamp": time.time(),
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available // (1024 * 1024),
                "disk_free_percent": (disk.free / disk.total) * 100,
                "disk_free_gb": disk.free // (1024 * 1024 * 1024),
                "components": {
                    "display": display_player is not None and display_player.running,
                    "wifi": wifi_manager is not None,
                    "updater": updater is not None
                }
            }
            
            # Simple health assessment
            is_healthy = (
                memory.percent < 80 and
                (disk.free / disk.total) * 100 > 10 and
                health_data["components"]["display"]
            )
            
            return APIResponse(
                success=True,
                data={
                    "healthy": is_healthy,
                    "metrics": health_data
                }
            )
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return APIResponse(
                success=False,
                message=f"Health check failed: {e}",
                data={
                    "healthy": False,
                    "timestamp": time.time()
                }
            )
    
    return router 