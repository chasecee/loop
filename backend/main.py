#!/usr/bin/env python3
"""
LOOP - Little Optical Output Pal
HARDENED VERSION: Single-threaded system manager, bulletproof Pi deployment.
"""

import atexit
import signal
import sys
import threading
import time
from pathlib import Path
import traceback
import os
import psutil
from typing import Optional
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
from display.hardened_player import HardenedDisplayPlayer as DisplayPlayer
from web.server import create_app
from boot.wifi import WiFiManager
from deployment.updater import SystemUpdater
import uvicorn


class HardwareCircuitBreaker:
    """Circuit breaker for hardware components that fail frequently."""
    
    def __init__(self, name: str, max_failures: int = 3, timeout: int = 60):
        self.name = name
        self.failure_count = 0
        self.last_failure_time = 0
        self.max_failures = max_failures
        self.timeout = timeout
        self.is_open = False
        
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        current_time = time.time()
        
        # Reset circuit breaker after timeout
        if self.is_open and (current_time - self.last_failure_time) > self.timeout:
            self.failure_count = 0
            self.is_open = False
        
        # Fail fast if circuit is open
        if self.is_open:
            raise RuntimeError(f"{self.name} circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            # Reset failure count on success
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = current_time
            
            if self.failure_count >= self.max_failures:
                self.is_open = True
                
            raise


class HardenedSystemManager:
    """
    Single-threaded system manager that replaces all the scattered threads.
    Handles WiFi, display health, system monitoring, and watchdog in one place.
    """
    
    def __init__(self, logger):
        self.logger = logger
        self.running = False
        self.last_wifi_check = 0
        self.last_health_check = 0
        self.last_watchdog_reset = 0
        self.last_gc_collect = 0
        
        # Circuit breakers for hardware components
        self.display_breaker = HardwareCircuitBreaker("display", max_failures=5, timeout=120)
        self.wifi_breaker = HardwareCircuitBreaker("wifi", max_failures=3, timeout=60)
        
        # Component references (set later)
        self.display_player = None
        self.wifi_manager = None
        
        # System health tracking
        self.health_stats = {
            "memory_warnings": 0,
            "disk_warnings": 0,
            "component_failures": 0
        }
    
    def register_components(self, display_player=None, wifi_manager=None):
        """Register components for monitoring."""
        self.display_player = display_player
        self.wifi_manager = wifi_manager
    
    def start(self):
        """Start the unified system manager."""
        self.running = True
        self.logger.info("Hardened system manager started (single thread)")
    
    def stop(self):
        """Stop the system manager."""
        self.running = False
    
    def run_cycle(self):
        """Run one monitoring cycle - called from main loop."""
        current_time = time.time()
        
        try:
            # Reset watchdog every cycle (most important)
            self._reset_watchdog()
            
            # WiFi health check (every 30 seconds)
            if current_time - self.last_wifi_check >= 30:
                self._check_wifi_health()
                self.last_wifi_check = current_time
            
            # System health check (every 60 seconds)  
            if current_time - self.last_health_check >= 60:
                self._check_system_health()
                self.last_health_check = current_time
            
            # Garbage collection (every 5 minutes)
            if current_time - self.last_gc_collect >= 300:
                gc.collect()
                self.last_gc_collect = current_time
                
        except Exception as e:
            self.logger.error(f"System manager cycle error: {e}")
            self.health_stats["component_failures"] += 1
    
    def _reset_watchdog(self):
        """Reset systemd watchdog."""
        if SYSTEMD_AVAILABLE:
            try:
                daemon.notify("WATCHDOG=1")
                self.last_watchdog_reset = time.time()
            except Exception as e:
                self.logger.debug(f"Watchdog reset failed: {e}")
    
    def _check_wifi_health(self):
        """Check WiFi health with circuit breaker."""
        if not self.wifi_manager:
            return
            
        try:
            self.wifi_breaker.call(self.wifi_manager.get_status)
        except Exception as e:
            self.logger.warning(f"WiFi health check failed: {e}")
            if "circuit breaker" in str(e):
                self.logger.warning("WiFi circuit breaker is open - skipping checks")
    
    def _check_system_health(self):
        """Check overall system health."""
        try:
            # Memory check
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb > 512:  # 512MB limit for Pi
                self.health_stats["memory_warnings"] += 1
                self.logger.warning(f"High memory usage: {memory_mb:.1f}MB")
                
                # Force garbage collection on high memory
                gc.collect()
                
                # If still high, we have a leak
                new_memory = process.memory_info().rss / 1024 / 1024
                if new_memory > 400:
                    self.logger.error(f"Memory leak detected: {new_memory:.1f}MB after GC")
            
            # Disk space check
            disk_usage = psutil.disk_usage('/')
            free_percent = (disk_usage.free / disk_usage.total) * 100
            
            if free_percent < 10:
                self.health_stats["disk_warnings"] += 1
                self.logger.warning(f"Low disk space: {free_percent:.1f}% free")
            
            # Display health check with circuit breaker
            if self.display_player:
                try:
                    self.display_breaker.call(self._check_display_health)
                except Exception as e:
                    self.logger.warning(f"Display health check failed: {e}")
            
        except Exception as e:
            self.logger.error(f"System health check failed: {e}")
    
    def _check_display_health(self):
        """Check display health (called via circuit breaker)."""
        if not self.display_player:
            return
            
        # Simple health check - is the player running?
        if not self.display_player.running:
            raise RuntimeError("Display player not running")
        
        # Check if display is available
        if hasattr(self.display_player, 'display_available'):
            if not self.display_player.display_available:
                raise RuntimeError("Display hardware not available")


class HardenedLOOPApplication:
    """Hardened LOOP application with minimal threads and maximum reliability."""
    
    def __init__(self):
        """Initialize the hardened application."""
        self.logger = get_logger("app")
        self.logger.info("Initializing hardened LOOP application...")
        
        # Configuration with fallback
        try:
            self._ensure_media_directories()
            self.config = get_config()
            self.logger.info(f"Starting LOOP v{self.config.device.version}")
        except Exception as e:
            self.logger.error(f"Failed to initialize config: {e}")
            self._create_fallback_config()
        
        # Single system manager instead of scattered threads
        self.system_manager = HardenedSystemManager(self.logger)
        
        # Component instances
        self.display_driver: Optional[ILI9341Driver] = None
        self.display_player: Optional[DisplayPlayer] = None
        self.wifi_manager: Optional[WiFiManager] = None
        self.updater: Optional[SystemUpdater] = None
        self.web_server_thread: Optional[threading.Thread] = None
        
        # Control flags
        self.running = False
        self.shutdown_event = threading.Event()
        
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
    
    def _ensure_media_directories(self):
        """Ensure media directories exist."""
        backend_dir = Path(__file__).parent
        processed_dir = backend_dir / "media" / "processed"
        raw_dir = backend_dir / "media" / "raw"
        
        processed_dir.mkdir(parents=True, exist_ok=True)
        raw_dir.mkdir(parents=True, exist_ok=True)
    
    def initialize_display(self) -> bool:
        """Initialize display with circuit breaker protection."""
        try:
            self.logger.info("Initializing display system...")
            
            # Timeout protection for hardware initialization
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
                    self.config.media,
                    None  # No WiFi manager dependency for simplified startup
                )
                
                self.logger.info("Display system initialized successfully")
                return True
                
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize display: {e}")
            # Create demo mode player for headless operation
            self.display_player = DisplayPlayer(
                None,  # No driver
                self.config.display,
                self.config.media,
                None
            )
            self.logger.warning("Display failed, running in demo mode")
            return False
    
    def initialize_wifi(self) -> bool:
        """Initialize WiFi with safety checks."""
        try:
            self.logger.info("Initializing WiFi management...")
            
            self.wifi_manager = WiFiManager(self.config.wifi)
            
            # Check current status safely
            try:
                status = self.wifi_manager.get_status()
                if status.get('connected'):
                    self.logger.info(f"Already connected to WiFi: {status.get('current_ssid')}")
                else:
                    self.logger.info("No active WiFi connection")
            except Exception as e:
                self.logger.warning(f"Failed to get initial WiFi status: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WiFi: {e}")
            return False
    
    def initialize_updater(self) -> bool:
        """Initialize update system."""
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
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize updater: {e}")
            return False
    
    def start_display_player(self) -> bool:
        """Start display player safely."""
        if not self.display_player:
            return False
        
        try:
            self.display_player.start()
            self.logger.info("Display player started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start display player: {e}")
            return False
    
    def start_web_server(self) -> bool:
        """Start web server with hardened configuration."""
        try:
            self.logger.info("Starting web server...")
            
            app = create_app(
                self.display_player,
                self.wifi_manager,
                self.updater,
                self.config
            )
            
            # Hardened uvicorn configuration for Pi deployment
            config = uvicorn.Config(
                app,
                host=self.config.web.host,
                port=self.config.web.port,
                log_level="warning",  # Reduce log spam
                access_log=False,    # Disable access logs to save resources
                timeout_keep_alive=30,
                timeout_graceful_shutdown=15,
                limit_max_requests=None,
                backlog=25,  # Reduce backlog for Pi
                limit_concurrency=20,  # Increased for static files + API requests
                loop="asyncio",
            )
            
            def run_server():
                try:
                    server = uvicorn.Server(config)
                    server.run()
                except Exception as e:
                    self.logger.error(f"Web server crashed: {e}")
            
            self.web_server_thread = threading.Thread(
                target=run_server,
                name="WebServer",
                daemon=True
            )
            self.web_server_thread.start()
            
            self.logger.info(f"Web server started on {self.config.web.host}:{self.config.web.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start web server: {e}")
            return False
    
    def start(self):
        """Start the hardened application."""
        try:
            self.logger.info("Starting hardened LOOP application...")
            self.running = True
            
            # Initialize components with graceful degradation
            display_ok = self.initialize_display()
            wifi_ok = self.initialize_wifi()
            updater_ok = self.initialize_updater()
            
            # Register components with system manager
            self.system_manager.register_components(self.display_player, self.wifi_manager)
            self.system_manager.start()
            
            # Start services
            if display_ok:
                self.start_display_player()
            
            web_ok = self.start_web_server()
            
            # We can run without display, but not without web server
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
            
            # Show boot message if display available
            if self.display_player and display_ok:
                try:
                    time.sleep(0.5)  # Brief delay for system to settle
                    self.display_player.show_boot_message(self.config.device.version)
                except Exception as e:
                    self.logger.warning(f"Failed to show boot message: {e}")
            
            # Main monitoring loop (single thread)
            self._main_loop()
            
        except Exception as e:
            self.logger.error(f"Application failed to start: {e}")
            raise
        finally:
            self.cleanup()
    
    def _main_loop(self):
        """Main application loop with integrated monitoring."""
        heartbeat_counter = 0
        
        try:
            while self.running:
                # Check for shutdown signal
                if self.shutdown_event.wait(timeout=5.0):  # 5 second cycles
                    break
                
                # Run system manager cycle (replaces all the scattered threads)
                self.system_manager.run_cycle()
                
                heartbeat_counter += 1
                
                # Log heartbeat every 5 minutes (60 cycles)
                if heartbeat_counter % 60 == 0:
                    self.logger.info(f"System heartbeat #{heartbeat_counter // 60}")
                    
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
    
    def shutdown(self):
        """Shutdown the application."""
        self.logger.info("Shutting down hardened LOOP...")
        self.running = False
        self.shutdown_event.set()
        self.system_manager.stop()
    
    def cleanup(self):
        """Clean up resources safely."""
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
        
        # Stop system manager
        self.system_manager.stop()
        
        # Wait for web server thread
        if self.web_server_thread and self.web_server_thread.is_alive():
            try:
                self.web_server_thread.join(timeout=5.0)
            except Exception as e:
                errors.append(f"Web server thread: {e}")
        
        # Final cleanup from media index
        try:
            from utils.media_index import media_index
            media_index.shutdown()
        except Exception as e:
            errors.append(f"Media index: {e}")
        
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
        app = HardenedLOOPApplication()
        app.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 