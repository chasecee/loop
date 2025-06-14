"""Configuration schema and validation."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class DisplayConfig:
    """Display configuration."""
    type: str = "ILI9341"
    width: int = 240
    height: int = 320
    spi_bus: int = 0
    spi_device: int = 0
    dc_pin: int = 25
    rst_pin: int = 27
    bl_pin: int = 18
    rotation: int = 0
    framerate: int = 30


@dataclass
class WiFiConfig:
    """WiFi configuration."""
    ssid: str = ""
    password: str = ""
    hotspot_ssid: str = "VidBox-Setup"
    hotspot_password: str = "vidbox123"
    timeout: int = 10


@dataclass
class EncoderConfig:
    """Rotary encoder configuration."""
    pin_a: int = 2
    pin_b: int = 3
    button_pin: int = 4
    debounce_ms: int = 20


@dataclass
class MediaConfig:
    """Media configuration."""
    max_file_size_mb: int = 10
    active_media: Optional[str] = None
    loop_count: int = -1


@dataclass
class SyncConfig:
    """Sync configuration."""
    enabled: bool = False
    server_url: str = ""
    interval_minutes: int = 60
    last_sync: Optional[str] = None


@dataclass
class WebConfig:
    """Web server configuration."""
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False


@dataclass
class DeviceConfig:
    """Device identification."""
    name: str = "VidBox"
    version: str = "1.0.0"


@dataclass
class Config:
    """Main configuration class."""
    device: DeviceConfig
    display: DisplayConfig
    wifi: WiFiConfig
    encoder: EncoderConfig
    media: MediaConfig
    sync: SyncConfig
    web: WebConfig

    @classmethod
    def load(cls, config_path: Path = None) -> 'Config':
        """Load configuration from file."""
        if config_path is None:
            config_path = Path(__file__).parent / "config.json"
        
        if not config_path.exists():
            # Create default config
            default_config = cls.default()
            default_config.save(config_path)
            return default_config
        
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        return cls(
            device=DeviceConfig(**data.get('device', {})),
            display=DisplayConfig(**data.get('display', {})),
            wifi=WiFiConfig(**data.get('wifi', {})),
            encoder=EncoderConfig(**data.get('encoder', {})),
            media=MediaConfig(**data.get('media', {})),
            sync=SyncConfig(**data.get('sync', {})),
            web=WebConfig(**data.get('web', {}))
        )
    
    def save(self, config_path: Path = None) -> None:
        """Save configuration to file."""
        if config_path is None:
            config_path = Path(__file__).parent / "config.json"
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)
    
    @classmethod
    def default(cls) -> 'Config':
        """Create default configuration."""
        return cls(
            device=DeviceConfig(),
            display=DisplayConfig(),
            wifi=WiFiConfig(),
            encoder=EncoderConfig(),
            media=MediaConfig(),
            sync=SyncConfig(),
            web=WebConfig()
        )


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config


def reload_config() -> Config:
    """Reload configuration from file."""
    global _config
    _config = Config.load()
    return _config 