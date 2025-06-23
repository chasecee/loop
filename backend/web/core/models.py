"""Pydantic models for LOOP web API request/response validation."""

import time
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field

# Request Models

class WiFiCredentials(BaseModel):
    ssid: str
    password: Optional[str] = ""

class AddToLoopPayload(BaseModel):
    slug: str

class LoopOrderPayload(BaseModel):
    loop: List[str]

class DisplaySettingsPayload(BaseModel):
    brightness: Optional[int] = None
    gamma: Optional[float] = None

# Response Models

class MediaItem(BaseModel):
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

class ProcessingJobResponse(BaseModel):
    """Processing job status response - matches frontend ProcessingJob interface."""
    job_id: str
    filename: str
    status: Literal["processing", "completed", "error"]  # Match TypeScript union type
    progress: float  # 0-100
    stage: str
    message: str
    timestamp: float  # Unix timestamp

class PlayerStatus(BaseModel):
    """Player status - matches frontend PlayerStatus interface."""
    is_playing: bool
    current_media: Optional[str] = None
    loop_index: int
    total_media: int
    frame_rate: float
    loop_mode: Literal["all", "one"]
    showing_progress: bool = False  # Extra field returned by DisplayPlayer

class WiFiStatus(BaseModel):
    """WiFi status - matches frontend WiFiStatus interface."""
    connected: bool
    hotspot_active: bool
    current_ssid: Optional[str] = None
    ip_address: Optional[str] = None
    configured_ssid: Optional[str] = None
    hotspot_ssid: Optional[str] = None
    signal_strength: Optional[str] = None  # Can be string from wireless stats
    network_info: Optional[Dict[str, Any]] = None

class UpdateStatus(BaseModel):
    """Update status - matches frontend UpdateStatus interface."""
    current_version: Optional[str] = None
    git_available: Optional[bool] = None
    last_check: Optional[str] = None
    update_sources: Optional[Dict[str, Any]] = None

class DeviceStatus(BaseModel):
    """Device status matching frontend expectations."""
    system: str = "LOOP v1.0.0" 
    status: str = "running"
    timestamp: int = Field(default_factory=lambda: int(time.time()))
    player: Optional[PlayerStatus] = None
    wifi: Optional[WiFiStatus] = None
    updates: Optional[UpdateStatus] = None

class StorageInfo(BaseModel):
    """Storage info - matches frontend StorageData interface."""
    total: int
    used: int
    free: int
    system: int
    app: int
    media: int
    units: str = "bytes"

class DashboardData(BaseModel):
    """Combined dashboard data - matches frontend DashboardData interface."""
    status: DeviceStatus
    media: List[MediaItem]  # List of MediaItem objects
    active: Optional[str]
    loop: List[str]
    last_updated: Optional[int]
    processing: Optional[Dict[str, ProcessingJobResponse]] = None  # Processing jobs dict
    storage: StorageInfo

class APIResponse(BaseModel):
    """Standard API response format - matches frontend APIResponse interface."""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    errors: Optional[List[Dict[str, str]]] = None

class WifiNetwork(BaseModel):
    """WiFi network info - matches frontend WifiNetwork interface."""
    ssid: str
    signal: int
    secured: bool 