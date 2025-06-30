"""Pydantic models for LOOP web API request/response validation."""

import time
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
import re

# Request Models

class WiFiCredentials(BaseModel):
    ssid: str = Field(..., min_length=1, max_length=32, description="WiFi network SSID")
    password: Optional[str] = Field(default="", max_length=63, description="WiFi network password")
    
    @field_validator('ssid')
    @classmethod
    def validate_ssid(cls, v):
        """Validate SSID with comprehensive security checks."""
        if not v or not v.strip():
            raise ValueError('SSID cannot be empty or whitespace only')
        
        # Trim whitespace but preserve internal spaces
        v = v.strip()
        
        # Check length constraints
        if len(v) > 32:
            raise ValueError('SSID cannot exceed 32 characters')
        
        # Security: Check for control characters and null bytes
        if any(ord(c) < 32 for c in v if c != ' '):
            raise ValueError('SSID contains invalid control characters')
        
        # Security: Check for potentially dangerous characters
        dangerous_chars = ['\\', '"', "'", '`', '$', ';', '&', '|', '<', '>']
        if any(char in v for char in dangerous_chars):
            raise ValueError('SSID contains potentially unsafe characters')
        
        # Check for valid UTF-8 encoding
        try:
            v.encode('utf-8')
        except UnicodeEncodeError:
            raise ValueError('SSID contains invalid characters')
        
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate WiFi password with security requirements."""
        if v is None:
            return ""
        
        # Allow empty password for open networks
        if not v:
            return ""
        
        # WPA/WPA2 minimum length requirement
        if len(v) < 8:
            raise ValueError('WiFi password must be at least 8 characters for secured networks')
        
        # WPA key length limit
        if len(v) > 63:
            raise ValueError('WiFi password cannot exceed 63 characters')
        
        # Security: Check for null bytes
        if '\x00' in v:
            raise ValueError('WiFi password contains null bytes')
        
        # Check for valid UTF-8 encoding
        try:
            v.encode('utf-8')
        except UnicodeEncodeError:
            raise ValueError('WiFi password contains invalid characters')
        
        return v
    
    @model_validator(mode='before')
    @classmethod
    def validate_credentials_combination(cls, data):
        """Validate the combination of SSID and password."""
        if isinstance(data, dict):
            ssid = data.get('ssid', '')
            password = data.get('password', '')
            
            # Security check: Don't allow SSID and password to be identical
            if ssid and password and ssid == password:
                raise ValueError('SSID and password cannot be identical')
        
        return data
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "ssid": "MyHomeNetwork",
                "password": "securepassword123"
            }
        }
    }

class AddToLoopPayload(BaseModel):
    slug: str

class LoopOrderPayload(BaseModel):
    loop: List[str]

class DisplaySettingsPayload(BaseModel):
    brightness: Optional[int] = None

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
    processing_status: Optional[str] = None  # "pending", "processing", "completed", "error"

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
    network_info: Optional[Dict[str, str | int | bool]] = None
    # Extra fields returned by WiFiManager but not in frontend interface
    interface: Optional[str] = None
    state: Optional[str] = None

class UpdateStatus(BaseModel):
    """Update status - matches frontend UpdateStatus interface."""
    current_version: Optional[str] = None
    git_available: Optional[bool] = None
    last_check: Optional[str] = None
    update_sources: Optional[Dict[str, str | int | bool]] = None

class DeviceStatus(BaseModel):
    """Device status matching frontend expectations."""
    system: str = "LOOP v1.0.0" 
    status: str = "running"
    timestamp: int = Field(default_factory=lambda: int(time.time()))
    player: Optional[PlayerStatus] = None
    wifi: Optional[WiFiStatus] = None
    updates: Optional[UpdateStatus] = None

class StorageData(BaseModel):
    """Storage data - matches frontend StorageData interface exactly."""
    total: int
    used: int
    free: int
    system: int
    app: int
    media: int
    units: str = "bytes"

class DashboardData(BaseModel):
    """Combined dashboard data - storage now separate for performance."""
    status: DeviceStatus
    media: List[MediaItem]  # List of MediaItem objects
    active: Optional[str]
    loop: List[str]
    last_updated: Optional[int]
    processing: Optional[Dict[str, ProcessingJobResponse]] = None  # Processing jobs dict

class APIResponse(BaseModel):
    """Standard API response format - matches frontend APIResponse interface."""
    success: bool
    message: Optional[str] = None
    data: Optional[Dict | List | str | int | bool] = None
    errors: Optional[List[Dict[str, str]]] = None

class WifiNetwork(BaseModel):
    """WiFi network info - matches frontend WifiNetwork interface."""
    ssid: str
    signal: int
    secured: bool 