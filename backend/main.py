#!/usr/bin/env python3
"""
LOOP - Little Optical Output Pal
Main entry point that orchestrates all components.
"""

import asyncio
import atexit
import signal
import sys
import threading
import time
from pathlib import Path
import traceback
import shutil
import subprocess
import os
import psutil
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
import gc

# Add systemd support for proper watchdog integration
try:
    from systemd import daemon
    SYSTEMD_AVAILABLE = True
except ImportError:
    SYSTEMD_AVAILABLE = False

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.schema import get_config, Config
from utils.logger import get_logger
from display.spiout import ILI9341Driver
from display.player import DisplayPlayer
from web.server import create_app
from boot.wifi import WiFiManager
from deployment.updater import SystemUpdater
import uvicorn


class ComponentManager:
    """Manages health monitoring and recovery of system components."""
    
    def __init__(self, logger):
        self.logger = logger
        self.components: Dict[str, Dict] = {}
        self.max_restart_attempts = 3
        self.health_check_interval = 30  # seconds
        self.last_health_check = datetime.now()
    
    def register_component(self, name: str, instance=None):
        """Register a component for health monitoring."""
        self.components[name] = {
            'instance': instance,
            'healthy': True,
            'last_heartbeat': datetime.now(),
            'failure_count': 0,
            'restart_attempts': 0
        }
        self.logger.info(f"Registered component: {name}")
    
    def heartbeat(self, name: str):
        """Update component heartbeat."""
        if name in self.components:
            self.components[name]['last_heartbeat'] = datetime.now()
            self.components[name]['healthy'] = True
    
    def mark_failure(self, name: str):
        """Mark component as failed."""
        if name in self.components:
            self.components[name]['failure_count'] += 1
            self.components[name]['healthy'] = False
            self.logger.warning(f"Component {name} marked as failed (count: {self.components[name]['failure_count']})")
    
    def get_unhealthy_components(self) -> Set[str]:
        """Get set of unhealthy component names."""
        unhealthy = set()
        for name, info in self.components.items():
            if not info['healthy'] or self._is_stale(name):
                unhealthy.add(name)
        return unhealthy
    
    def _is_stale(self, name: str) -> bool:
        """Check if component hasn't reported in too long."""
        if name not in self.components:
            return True
        last_heartbeat = self.components[name]['last_heartbeat']
        return (datetime.now() - last_heartbeat).total_seconds() > self.health_check_interval
    
    def can_restart(self, name: str) -> bool:
        """Check if component can be restarted."""
        if name not in self.components:
            return False
        return self.components[name]['restart_attempts'] < self.max_restart_attempts
    
    def attempt_restart(self, name: str):
        """Record restart attempt."""
        if name in self.components:
            self.components[name]['restart_attempts'] += 1


class LOOPApplication:
    """Main LOOP application coordinator with robust error handling."""
    
    def __init__(self):
        """Initialize the application."""
        self.logger = get_logger("app")
        self.logger.info("Initializing LOOP application...")
        
        # Configuration
        try:
            self._ensure_default_media()
            self.config = get_config()
            self.logger.info(f"Starting LOOP v{self.config.device.version}")
        except Exception as e:
            self.logger.error(f"Failed to initialize config: {e}")
            self._create_fallback_config()
        
        # Component management
        self.component_manager = ComponentManager(self.logger)
        
        # Component instances
        self.display_driver: Optional[ILI9341Driver] = None
        self.display_player: Optional[DisplayPlayer] = None
        self.wifi_manager: Optional[WiFiManager] = None
        self.updater: Optional[SystemUpdater] = None
        self.web_server_thread: Optional[threading.Thread] = None
        
        # Control flags
        self.running = False
        self.shutdown_event = threading.Event()
        
        # Watchdog
        self.last_watchdog_reset = datetime.now()
        
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _create_fallback_config(self):
        """Create fallback configuration if config loading fails."""
        from config.schema import DisplayConfig, MediaConfig, WiFiConfig, WebConfig, DeviceConfig, SyncConfig
        self.config = type('Config', (), {
            'display': DisplayConfig(),
            'media': MediaConfig(), 
            'wifi': WiFiConfig(),
            'web': WebConfig(),
            'device': DeviceConfig(),
            'sync': SyncConfig()
        })()
        self.logger.warning("Using fallback configuration")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.shutdown()
    
    def _ensure_default_media(self):
        """If media/processed is empty, copy from assets/default-media and update index.json."""
        backend_dir = Path(__file__).parent
        project_root = backend_dir.parent
        processed_dir = backend_dir / "media" / "processed"
        default_media_dir = project_root / "assets" / "default-media"
        index_file = backend_dir / "media" / "index.json"

        if (processed_dir.exists() and not any(processed_dir.iterdir()) and 
            default_media_dir.exists()):
            
            setup_logger = get_logger("default_media")
            setup_logger.info("Processing default media files...")

            # Default media should be pre-processed and deployed as ZIP files
            # during build/deployment process. No server-side conversion needed.
            setup_logger.info("Default media processing is now handled during deployment")
    
    def _reset_watchdog(self):
        """Reset the software watchdog timer and notify systemd."""
        self.last_watchdog_reset = datetime.now()
        
        if SYSTEMD_AVAILABLE:
            try:
                daemon.notify("WATCHDOG=1")
            except Exception:
                pass  # Don't let watchdog notification failures crash the app
    
    def _check_system_health(self) -> bool:
        """Perform system health check."""
        try:
            # Check process resources
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent()
            
            # Memory limit check (Pi has limited RAM)
            if memory_mb > 512:  # 512MB limit
                self.logger.warning(f"High memory usage: {memory_mb:.1f}MB")
                return False
            
            # CPU limit check
            if cpu_percent > 80:
                self.logger.warning(f"High CPU usage: {cpu_percent:.1f}%")
                return False
            
            # Disk space check
            disk_usage = psutil.disk_usage('/')
            free_percent = (disk_usage.free / disk_usage.total) * 100
            if free_percent < 10:
                self.logger.warning(f"Low disk space: {free_percent:.1f}% free")
                return False
            
            # Component health check
            unhealthy = self.component_manager.get_unhealthy_components()
            if unhealthy:
                self.logger.warning(f"Unhealthy components: {unhealthy}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return True  # Assume healthy if we can't check
    
    def initialize_display(self) -> bool:
        """Initialize the display system."""
        try:
            self.logger.info("Initializing display system...")
            
            # Create display driver with timeout
            def timeout_handler(signum, frame):
                raise TimeoutError("Display initialization timed out")
            
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)  # 30 second timeout
            
            try:
                self.display_driver = ILI9341Driver(self.config.display)
                self.display_driver.init()
                
                self.display_player = DisplayPlayer(
                    self.display_driver,
                    self.config.display,
                    self.config.media
                )
                
                self.component_manager.register_component("display", self.display_driver)
                self.component_manager.register_component("display_player", self.display_player)
                
                self.logger.info("Display system initialized successfully")
                return True
                
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize display: {e}")
            self.component_manager.mark_failure("display")
            return False
    
    def initialize_wifi(self) -> bool:
        """Initialize WiFi management."""
        try:
            self.logger.info("Initializing WiFi management...")
            
            self.wifi_manager = WiFiManager(self.config.wifi)
            self.component_manager.register_component("wifi", self.wifi_manager)
            
            if self.config.wifi.ssid:
                if self.wifi_manager.connect():
                    self.logger.info(f"Connected to WiFi: {self.config.wifi.ssid}")
                else:
                    self.logger.warning("Failed to connect to configured WiFi.")
                    if self.config.wifi.hotspot_enabled:
                        self.logger.info("Starting hotspot as fallback.")
                        self.wifi_manager.start_hotspot()
                    else:
                        self.logger.info("Hotspot is disabled, will not start.")
            else:
                if self.config.wifi.hotspot_enabled:
                    self.logger.info("No WiFi configured, starting hotspot.")
                    self.wifi_manager.start_hotspot()
                else:
                    self.logger.info("No WiFi configured and hotspot is disabled.")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WiFi: {e}")
            self.component_manager.mark_failure("wifi")
            return False
    
    def initialize_updater(self) -> bool:
        """Initialize the update system."""
        try:
            self.logger.info("Initializing update system...")
            
            current_dir = Path(__file__).parent
            update_config = {
                'git_enabled': True,
                'remote_url': self.config.sync.server_url if self.config.sync.enabled else None
            }
            
            self.updater = SystemUpdater(
                current_dir,
                self.config.device.version,
                update_config
            )
            
            self.component_manager.register_component("updater", self.updater)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize updater: {e}")
            self.component_manager.mark_failure("updater")
            return False
    
    def start_display_player(self) -> bool:
        """Start the display player."""
        if not self.display_player:
            return False
        
        try:
            # Use the player's built-in start() method instead of calling run() directly
            self.display_player.start()
            self.logger.info("Display player started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start display player: {e}")
            self.component_manager.mark_failure("display_player")
            return False
    
    def start_web_server(self) -> bool:
        """Start the web server."""
        try:
            self.logger.info("Starting web server...")
            
            # Create FastAPI app
            app = create_app(
                self.display_player,
                self.wifi_manager,
                self.updater,
                self.config
            )
            
            # Configure uvicorn with better connection handling
            config = uvicorn.Config(
                app,
                host=self.config.web.host,
                port=self.config.web.port,
                log_level="warning",  # Reduce noise
                access_log=False,
                # Connection management settings
                timeout_keep_alive=5,  # Reduce keep-alive timeout from default 20s
                timeout_graceful_shutdown=30,  # Graceful shutdown timeout
                limit_max_requests=None,  # Disable auto-restart; keeps web server alive
                backlog=50,  # Connection backlog queue size
                h11_max_incomplete_event_size=16 * 1024,  # 16KB max incomplete event
                # Large file upload settings
                limit_concurrency=self.config.web.max_concurrent_requests,  # Use config value
                timeout_notify=self.config.web.request_timeout_seconds,  # Use config timeout
                loop="asyncio",  # Use asyncio event loop for better performance
            )
            
            def run_server():
                try:
                    server = uvicorn.Server(config)
                    server.run()
                except Exception as e:
                    self.logger.error(f"Web server crashed: {e}")
                    self.component_manager.mark_failure("web_server")
            
            self.web_server_thread = threading.Thread(
                target=run_server,
                name="WebServer",
                daemon=True
            )
            self.web_server_thread.start()
            
            self.component_manager.register_component("web_server", None)
            
            self.logger.info(f"Web server started on {self.config.web.host}:{self.config.web.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start web server: {e}")
            self.component_manager.mark_failure("web_server")
            return False
    
    def start(self):
        """Start the application."""
        try:
            self.logger.info("Starting LOOP application...")
            self.running = True
            
            # Initialize components
            display_ok = self.initialize_display()
            wifi_ok = self.initialize_wifi()
            updater_ok = self.initialize_updater()
            
            # Start services
            if display_ok:
                self.start_display_player()
            
            web_ok = self.start_web_server()
            
            # Check if we have minimum viable system
            if not web_ok:
                raise RuntimeError("Critical failure: Web server failed to start")
            
            self.logger.info("LOOP started successfully!")
            
            # Notify systemd
            if SYSTEMD_AVAILABLE:
                try:
                    daemon.notify("READY=1")
                    self.logger.info("Notified systemd that service is ready")
                except Exception as e:
                    self.logger.warning(f"Failed to notify systemd: {e}")
            
            # Show welcome message
            if self.display_player:
                try:
                    self.display_player.show_message("LOOP Ready!", duration=3.0)
                except Exception:
                    pass
            
            # Main loop
            self._main_loop()
            
        except Exception as e:
            self.logger.error(f"Application failed to start: {e}")
            raise
        finally:
            self.cleanup()
    
    def _main_loop(self):
        """Main application loop with health monitoring."""
        last_health_check = datetime.now()
        heartbeat_counter = 0
        
        try:
            while self.running:
                # Wait for shutdown signal
                if self.shutdown_event.wait(timeout=1.0):
                    break
                
                # Reset watchdog
                self._reset_watchdog()
                heartbeat_counter += 1
                
                # Update component heartbeats
                for name in self.component_manager.components:
                    self.component_manager.heartbeat(name)
                
                # Periodic health checks
                now = datetime.now()
                if (now - last_health_check).total_seconds() >= 60:  # Every minute
                    try:
                        system_healthy = self._check_system_health()
                        if not system_healthy:
                            # Log but don't take drastic action - let systemd handle restarts
                            self.logger.warning("System health check failed")
                        
                        last_health_check = now
                        
                        # Periodic garbage collection
                        gc.collect()
                        
                    except Exception as e:
                        self.logger.error(f"Health check error: {e}")
                
                # Log heartbeat occasionally
                if heartbeat_counter % 300 == 0:  # Every 5 minutes
                    self.logger.info(f"System heartbeat #{heartbeat_counter}")
                    
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
    
    def shutdown(self):
        """Shutdown the application."""
        self.logger.info("Shutting down LOOP...")
        self.running = False
        self.shutdown_event.set()
    
    def cleanup(self):
        """Clean up resources."""
        self.logger.info("Starting cleanup...")
        
        errors = []
        
        # Stop display player
        if self.display_player:
            try:
                self.display_player.stop()
            except Exception as e:
                errors.append(f"Display player: {e}")
        
        # Cleanup display driver
        if self.display_driver:
            try:
                self.display_driver.fill_screen(0x0000)
                self.display_driver.cleanup()
            except Exception as e:
                errors.append(f"Display driver: {e}")
        
        # Stop WiFi manager
        if self.wifi_manager:
            try:
                self.wifi_manager.cleanup()
            except Exception as e:
                errors.append(f"WiFi manager: {e}")
        
        # Wait for web server thread
        if self.web_server_thread and self.web_server_thread.is_alive():
            try:
                self.web_server_thread.join(timeout=5.0)
                if self.web_server_thread.is_alive():
                    self.logger.warning("Web server thread did not stop gracefully")
            except Exception as e:
                errors.append(f"Web server thread: {e}")
        
        # Force garbage collection
        gc.collect()
        
        if errors:
            self.logger.warning(f"Cleanup completed with {len(errors)} errors:")
            for error in errors:
                self.logger.warning(f"  - {error}")
        else:
            self.logger.info("Cleanup completed successfully")


def main():
    """Main entry point."""
    try:
        app = LOOPApplication()
        app.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 