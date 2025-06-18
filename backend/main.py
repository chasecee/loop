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

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.schema import get_config
from utils.logger import get_logger
from display.spiout import ILI9341Driver
from display.player import DisplayPlayer
# from input.encoder import RotaryEncoder  # TODO: Implement encoder later
from web.server import create_app
from boot.wifi import WiFiManager
from deployment.updater import SystemUpdater
import uvicorn


class ComponentHealth:
    """Tracks health of individual components."""
    
    def __init__(self, name: str):
        self.name = name
        self.last_heartbeat = datetime.now()
        self.failure_count = 0
        self.is_healthy = True
        self.restart_attempts = 0
        self.max_restart_attempts = 3
    
    def heartbeat(self):
        """Update component heartbeat."""
        self.last_heartbeat = datetime.now()
        self.is_healthy = True
    
    def mark_failure(self):
        """Mark component as failed."""
        self.failure_count += 1
        self.is_healthy = False
        
    def can_restart(self) -> bool:
        """Check if component can be restarted."""
        return self.restart_attempts < self.max_restart_attempts
    
    def attempt_restart(self):
        """Record restart attempt."""
        self.restart_attempts += 1
    
    def is_stale(self, max_age_seconds: int = 30) -> bool:
        """Check if component hasn't reported in too long."""
        return (datetime.now() - self.last_heartbeat).total_seconds() > max_age_seconds


class LOOPApplication:
    """Main LOOP application coordinator with robust error handling."""
    
    def __init__(self):
        """Initialize the application."""
        # Setup logging first
        self.logger = get_logger("app")
        self.logger.info("Initializing LOOP application with robust error handling...")
        
        try:
            self._ensure_default_media()
            self.config = get_config()
            self.logger.info(f"Starting LOOP v{self.config.device.version}")
        except Exception as e:
            self.logger.error(f"Failed to initialize config: {e}")
            # Use fallback config to continue
            from config.schema import DisplayConfig, MediaConfig, WiFiConfig, WebConfig, DeviceConfig, SyncConfig
            self.config = type('Config', (), {
                'display': DisplayConfig(),
                'media': MediaConfig(), 
                'wifi': WiFiConfig(),
                'web': WebConfig(),
                'device': DeviceConfig(),
                'sync': SyncConfig()
            })()
        
        # Component instances
        self.display_driver = None
        self.display_player = None
        self.encoder = None
        self.wifi_manager = None
        self.updater = None
        self.web_server = None
        
        # Control flags
        self.running = False
        self.threads = []
        self.component_health = {}
        
        # Watchdog and monitoring
        self.watchdog_enabled = True
        self.last_watchdog_reset = datetime.now()
        self.system_health_check_interval = 10  # seconds
        
        # Recovery mechanisms
        self.emergency_recovery_mode = False
        self.critical_failures = 0
        self.max_critical_failures = 5
        
        # Process monitoring
        self.process_info = {
            'pid': os.getpid(),
            'start_time': datetime.now(),
            'memory_limit_mb': 512,  # Pi memory limit
            'cpu_limit_percent': 80
        }
        
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGUSR1, self._health_check_handler)  # Custom health check signal
    
    def _signal_handler(self, signum, frame):
        """Handle system signals."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.shutdown()
    
    def _health_check_handler(self, signum, frame):
        """Handle health check signal."""
        self.logger.info("Health check requested via signal")
        self._perform_health_check()
    
    def _register_component(self, name: str) -> ComponentHealth:
        """Register a component for health monitoring."""
        health = ComponentHealth(name)
        self.component_health[name] = health
        self.logger.info(f"Registered component for monitoring: {name}")
        return health
    
    def _reset_watchdog(self):
        """Reset the software watchdog timer."""
        self.last_watchdog_reset = datetime.now()
    
    def _check_system_resources(self) -> bool:
        """Check system resource usage."""
        try:
            # Check memory usage
            process = psutil.Process(self.process_info['pid'])
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent()
            
            if memory_mb > self.process_info['memory_limit_mb']:
                self.logger.warning(f"High memory usage: {memory_mb:.1f}MB (limit: {self.process_info['memory_limit_mb']}MB)")
                return False
            
            if cpu_percent > self.process_info['cpu_limit_percent']:
                self.logger.warning(f"High CPU usage: {cpu_percent:.1f}% (limit: {self.process_info['cpu_limit_percent']}%)")
                return False
            
            # Check disk space
            disk_usage = psutil.disk_usage('/')
            free_percent = (disk_usage.free / disk_usage.total) * 100
            if free_percent < 10:  # Less than 10% free space
                self.logger.warning(f"Low disk space: {free_percent:.1f}% free")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to check system resources: {e}")
            return True  # Assume healthy if we can't check
    
    def _perform_health_check(self):
        """Perform comprehensive health check."""
        try:
            self.logger.info("Performing system health check...")
            
            # Check system resources
            resources_ok = self._check_system_resources()
            
            # Check component health
            unhealthy_components = []
            for name, health in self.component_health.items():
                if not health.is_healthy or health.is_stale():
                    unhealthy_components.append(name)
                    self.logger.warning(f"Component {name} is unhealthy (failures: {health.failure_count}, last heartbeat: {health.last_heartbeat})")
            
            # Check if watchdog has been reset recently
            watchdog_age = (datetime.now() - self.last_watchdog_reset).total_seconds()
            if watchdog_age > 60:  # 1 minute without reset
                self.logger.warning(f"Watchdog hasn't been reset in {watchdog_age:.1f} seconds")
            
            # Log health summary
            self.logger.info(f"Health check complete - Resources: {'OK' if resources_ok else 'WARNING'}, "
                           f"Unhealthy components: {len(unhealthy_components)}")
            
            return resources_ok and len(unhealthy_components) == 0
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def _attempt_component_recovery(self, component_name: str):
        """Attempt to recover a failed component."""
        health = self.component_health.get(component_name)
        if not health or not health.can_restart():
            self.logger.error(f"Cannot restart component {component_name} (max attempts reached)")
            return False
        
        try:
            self.logger.info(f"Attempting to recover component: {component_name}")
            health.attempt_restart()
            
            # Component-specific recovery logic
            if component_name == "display":
                self._recover_display()
            elif component_name == "web_server":
                self._recover_web_server()
            elif component_name == "wifi":
                self._recover_wifi()
            elif component_name == "display_player":
                self._recover_display_player()
            
            health.heartbeat()  # Mark as healthy if recovery succeeded
            self.logger.info(f"Successfully recovered component: {component_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to recover component {component_name}: {e}")
            health.mark_failure()
            return False
    
    def _recover_display(self):
        """Recover display component."""
        try:
            if self.display_driver:
                self.display_driver.cleanup()
            self.initialize_display()
        except Exception as e:
            raise Exception(f"Display recovery failed: {e}")
    
    def _recover_web_server(self):
        """Recover web server component."""
        try:
            # Web server runs in thread, so just restart it
            self.start_web_server()
        except Exception as e:
            raise Exception(f"Web server recovery failed: {e}")
    
    def _recover_wifi(self):
        """Recover WiFi component."""
        try:
            if self.wifi_manager:
                self.wifi_manager.cleanup()
            self.initialize_wifi()
        except Exception as e:
            raise Exception(f"WiFi recovery failed: {e}")
    
    def _recover_display_player(self):
        """Recover display player component."""
        try:
            if self.display_player:
                self.display_player.stop()
            self.start_display_player()
        except Exception as e:
            raise Exception(f"Display player recovery failed: {e}")
    
    def _emergency_recovery(self):
        """Last resort recovery measures."""
        self.logger.critical("Entering emergency recovery mode!")
        self.emergency_recovery_mode = True
        
        try:
            # Stop all non-essential components
            if self.display_player:
                self.display_player.stop()
            
            # Clear display
            if self.display_driver:
                try:
                    self.display_driver.fill_screen(0x0000)
                    self.display_driver.cleanup()
                except:
                    pass
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Sleep to let system stabilize
            time.sleep(5)
            
            # Try to restart minimal services
            self.initialize_display()
            self.start_display_player()
            
            self.emergency_recovery_mode = False
            self.logger.info("Emergency recovery completed")
            
        except Exception as e:
            self.logger.critical(f"Emergency recovery failed: {e}")
            # At this point, we should probably restart the entire process
            self._request_system_restart()
    
    def _request_system_restart(self):
        """Request system restart as last resort."""
        self.logger.critical("Requesting system restart due to critical failures")
        try:
            # Try graceful shutdown first
            self.cleanup()
            
            # Write restart flag for systemd or init system
            Path("/tmp/loop_restart_requested").touch()
            
            # Exit with special code that systemd can restart on
            sys.exit(42)  # Special exit code for restart
            
        except Exception as e:
            self.logger.critical(f"Failed to request restart: {e}")
            os._exit(1)  # Force exit
    
    def _ensure_default_media(self):
        """If media/processed is empty, copy from assets/default-media and update index.json."""
        backend_dir = Path(__file__).parent
        project_root = backend_dir.parent
        processed_dir = backend_dir / "media" / "processed"
        default_media_dir = project_root / "assets" / "default-media"
        index_file = backend_dir / "media" / "index.json"

        if processed_dir.exists() and not any(processed_dir.iterdir()) and default_media_dir.exists():
            self_logger = get_logger("default_media")
            self_logger.info("Processing default media files...")

            # Lazy import to avoid heavy deps if not needed
            from utils.convert import MediaConverter

            # Use fallback resolution (will be updated later when config loaded)
            converter = MediaConverter(240, 320)

            media_meta = []
            for media_file in default_media_dir.iterdir():
                if media_file.is_file():
                    slug = converter._generate_slug(media_file.name)
                    out_dir = processed_dir / slug
                    try:
                        meta = converter.convert_media_file(media_file, out_dir)
                        if meta:
                            media_meta.append(meta)
                            self_logger.info("Converted default media %s", media_file.name)
                    except Exception as e:
                        self_logger.error("Failed to convert default media %s: %s", media_file.name, e)

            # Build index.json
            active = media_meta[0]["slug"] if media_meta else None
            with open(index_file, "w") as f:
                import json
                json.dump({"media": media_meta, "active": active, "last_updated": int(time.time())}, f, indent=2)

            self_logger.info("Default media processing complete: %d items", len(media_meta))
    
    def initialize_display(self):
        """Initialize the display system with health monitoring."""
        display_health = self._register_component("display")
        
        try:
            self.logger.info("Initializing display system...")
            
            # Create display driver with timeout protection
            import signal
            def timeout_handler(signum, frame):
                raise TimeoutError("Display initialization timed out")
            
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)  # 30 second timeout
            
            try:
                self.display_driver = ILI9341Driver(self.config.display)
                self.display_driver.init()
                display_health.heartbeat()
                
                # Create display player
                from display.player import DisplayPlayer
                self.display_player = DisplayPlayer(
                    self.display_driver,
                    self.config.display,
                    self.config.media
                )
                display_health.heartbeat()
                
                self.logger.info("Display system initialized successfully")
                
            finally:
                signal.alarm(0)  # Cancel timeout
                signal.signal(signal.SIGALRM, old_handler)
            
        except TimeoutError:
            self.logger.error("Display initialization timed out")
            display_health.mark_failure()
            self._handle_critical_failure("display")
        except Exception as e:
            self.logger.error(f"Failed to initialize display: {e}")
            display_health.mark_failure()
            # Continue running headless – don't crash the whole service
            self.logger.warning("Continuing without display (headless mode)")
    
    def _handle_critical_failure(self, component_name: str):
        """Handle critical component failure."""
        self.critical_failures += 1
        self.logger.error(f"Critical failure in {component_name} (total: {self.critical_failures})")
        
        if self.critical_failures >= self.max_critical_failures:
            self.logger.critical("Too many critical failures, entering emergency recovery")
            self._emergency_recovery()
        else:
            # Try to recover the component
            self._attempt_component_recovery(component_name)
    
    def initialize_input(self):
        """Initialize the input system."""
        try:
            self.logger.info("Initializing input system...")
            
            # TODO: Implement encoder later
            # self.encoder = RotaryEncoder(
            #     self.config.encoder,
            #     on_clockwise=self._on_encoder_cw,
            #     on_counterclockwise=self._on_encoder_ccw,
            #     on_button_press=self._on_encoder_button
            # )
            
            self.logger.info("Input system initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize input: {e}")
            # Continue without encoder – don't crash the whole service
            self.logger.warning("Continuing without encoder (headless mode)")
    
    def initialize_wifi(self):
        """Initialize WiFi management with health monitoring."""
        wifi_health = self._register_component("wifi")
        
        try:
            self.logger.info("Initializing WiFi management...")
            
            from boot.wifi import WiFiManager
            self.wifi_manager = WiFiManager(self.config.wifi)
            wifi_health.heartbeat()
            
            # Try to connect to configured WiFi with timeout
            if self.config.wifi.ssid:
                connection_timeout = 30  # seconds
                start_time = time.time()
                
                if self.wifi_manager.connect():
                    self.logger.info(f"Connected to WiFi: {self.config.wifi.ssid}")
                    wifi_health.heartbeat()
                else:
                    self.logger.warning("Failed to connect to configured WiFi")
                    # Start hotspot mode as fallback
                    self.wifi_manager.start_hotspot()
                    wifi_health.heartbeat()
            else:
                self.logger.info("No WiFi configured, starting in hotspot mode")
                self.wifi_manager.start_hotspot()
                wifi_health.heartbeat()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WiFi: {e}")
            wifi_health.mark_failure()
            # WiFi failure is not critical - system can run without it
    
    def initialize_updater(self):
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
            
            self.logger.info("Update system initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize updater: {e}")
    
    def start_web_server(self):
        """Start the web server with health monitoring."""
        web_health = self._register_component("web_server")
        
        try:
            self.logger.info("Starting web server...")
            
            # Create FastAPI app
            app = create_app(
                self.display_player,
                self.wifi_manager,
                self.updater,
                self.config
            )
            web_health.heartbeat()
            
            # Configure uvicorn
            config = uvicorn.Config(
                app,
                host=self.config.web.host,
                port=self.config.web.port,
                log_level="info" if self.config.web.debug else "warning",
                access_log=self.config.web.debug
            )
            
            # Run server in thread with error handling
            server = uvicorn.Server(config)
            
            def run_server_with_monitoring():
                try:
                    server.run()
                except Exception as e:
                    self.logger.error(f"Web server crashed: {e}")
                    web_health.mark_failure()
                    if not self.emergency_recovery_mode:
                        self._attempt_component_recovery("web_server")
            
            server_thread = threading.Thread(
                target=run_server_with_monitoring,
                name="WebServer",
                daemon=True
            )
            server_thread.start()
            self.threads.append(server_thread)
            web_health.heartbeat()
            
            self.logger.info(f"Web server started on {self.config.web.host}:{self.config.web.port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start web server: {e}")
            web_health.mark_failure()
            self._handle_critical_failure("web_server")
    
    def start_display_player(self):
        """Start the display player with health monitoring."""
        if self.display_player:
            player_health = self._register_component("display_player")
            
            try:
                self.logger.info("Starting display player...")
                
                def run_player_with_monitoring():
                    try:
                        self.display_player.run()
                    except Exception as e:
                        self.logger.error(f"Display player crashed: {e}")
                        player_health.mark_failure()
                        if not self.emergency_recovery_mode:
                            self._attempt_component_recovery("display_player")
                
                player_thread = threading.Thread(
                    target=run_player_with_monitoring,
                    name="DisplayPlayer",
                    daemon=True
                )
                player_thread.start()
                self.threads.append(player_thread)
                player_health.heartbeat()
                
                self.logger.info("Display player started")
                
            except Exception as e:
                self.logger.error(f"Failed to start display player: {e}")
                player_health.mark_failure()
                self._handle_critical_failure("display_player")
    
    def start_input_handler(self):
        """Start the input handler."""
        if self.encoder:
            try:
                self.logger.info("Starting input handler...")
                
                input_thread = threading.Thread(
                    target=self.encoder.start,
                    name="InputHandler",
                    daemon=True
                )
                input_thread.start()
                self.threads.append(input_thread)
                
                self.logger.info("Input handler started")
                
            except Exception as e:
                self.logger.error(f"Failed to start input handler: {e}")
    
    def _on_encoder_cw(self):
        """Handle clockwise encoder rotation."""
        if self.display_player:
            self.display_player.next_media()
            self.logger.debug("Encoder: Next media")
    
    def _on_encoder_ccw(self):
        """Handle counter-clockwise encoder rotation."""
        if self.display_player:
            self.display_player.previous_media()
            self.logger.debug("Encoder: Previous media")
    
    def _on_encoder_button(self):
        """Handle encoder button press."""
        if self.display_player:
            self.display_player.toggle_pause()
            self.logger.debug("Encoder: Toggle pause")
    
    def _init_components(self):
        """Initialize all core components in the correct order."""
        self.running = True
        self.initialize_display()
        self.initialize_input()
        self.initialize_wifi()
        self.initialize_updater()
        self.start_display_player()
        self.start_input_handler()
    
    def start(self):
        """Start the application."""
        try:
            self.logger.info("Starting LOOP application...")
            
            # Initialize components
            self._init_components()
            
            # Start web server
            self.start_web_server()
            
            self.logger.info("LOOP started successfully!")
            
            # Show welcome message
            if self.display_player:
                self.display_player.show_message("LOOP Ready!", duration=3.0)
            
            # Create shutdown event for clean thread management
            self.shutdown_event = threading.Event()
            
            # Main loop with health monitoring and watchdog
            try:
                last_health_check = datetime.now()
                heartbeat_counter = 0
                
                while self.running:
                    # Wait for shutdown signal with timeout for responsiveness
                    if self.shutdown_event.wait(timeout=1.0):
                        break
                    
                    # Reset watchdog timer
                    self._reset_watchdog()
                    heartbeat_counter += 1
                    
                    # Periodic health checks
                    now = datetime.now()
                    if (now - last_health_check).total_seconds() >= self.system_health_check_interval:
                        try:
                            # Update component heartbeats for running components
                            for name, health in self.component_health.items():
                                if health.is_healthy:
                                    # All healthy components get heartbeat updates
                                    health.heartbeat()
                            
                            # Perform health check
                            system_healthy = self._perform_health_check()
                            if not system_healthy and not self.emergency_recovery_mode:
                                self.logger.warning("System health check failed, attempting recovery")
                                # Try to recover unhealthy components
                                for name, health in self.component_health.items():
                                    if not health.is_healthy and health.can_restart():
                                        self._attempt_component_recovery(name)
                            
                            last_health_check = now
                            
                        except Exception as e:
                            self.logger.error(f"Health check failed: {e}")
                    
                    # Log heartbeat every 60 seconds for monitoring
                    if heartbeat_counter % 60 == 0:
                        self.logger.info(f"System heartbeat #{heartbeat_counter} - {len(self.component_health)} components monitored")
                        
                        # Force garbage collection periodically to prevent memory leaks
                        import gc
                        gc.collect()
                    
            except KeyboardInterrupt:
                self.logger.info("Received keyboard interrupt")
                
        except Exception as e:
            self.logger.error(f"Application failed to start: {e}")
            raise
        finally:
            self.cleanup()
    
    def shutdown(self):
        """Shutdown the application."""
        self.logger.info("Shutting down LOOP...")
        self.running = False
        if hasattr(self, 'shutdown_event'):
            self.shutdown_event.set()
    
    def cleanup(self):
        """Clean up resources with robust error handling."""
        if hasattr(self, 'logger'):
            self.logger.info("Starting comprehensive cleanup...")
        
        cleanup_errors = []
        
        # Stop display player with timeout
        if self.display_player:
            try:
                self.logger.info("Stopping display player...")
                self.display_player.stop()
            except Exception as e:
                cleanup_errors.append(f"Display player cleanup: {e}")
                if hasattr(self, 'logger'):
                    self.logger.error(f"Error stopping display player: {e}")
        
        # Stop encoder
        if self.encoder:
            try:
                self.logger.info("Stopping encoder...")
                self.encoder.stop()
            except Exception as e:
                cleanup_errors.append(f"Encoder cleanup: {e}")
                if hasattr(self, 'logger'):
                    self.logger.error(f"Error stopping encoder: {e}")
        
        # Cleanup display driver
        if self.display_driver:
            try:
                self.logger.info("Cleaning up display driver...")
                self.display_driver.fill_screen(0x0000)  # Clear screen
                self.display_driver.cleanup()
            except Exception as e:
                cleanup_errors.append(f"Display driver cleanup: {e}")
                if hasattr(self, 'logger'):
                    self.logger.error(f"Error cleaning up display: {e}")
        
        # Stop WiFi manager
        if self.wifi_manager:
            try:
                self.logger.info("Cleaning up WiFi manager...")
                self.wifi_manager.cleanup()
            except Exception as e:
                cleanup_errors.append(f"WiFi manager cleanup: {e}")
                if hasattr(self, 'logger'):
                    self.logger.error(f"Error cleaning up WiFi: {e}")
        
        # Stop all threads gracefully
        if hasattr(self, 'logger'):
            self.logger.info(f"Waiting for {len(self.threads)} threads to finish...")
        
        for thread in self.threads:
            if thread.is_alive():
                try:
                    thread.join(timeout=5.0)  # Increased timeout
                    if thread.is_alive():
                        self.logger.warning(f"Thread {thread.name} did not stop gracefully")
                except Exception as e:
                    cleanup_errors.append(f"Thread {thread.name} cleanup: {e}")
        
        # Force garbage collection
        try:
            import gc
            gc.collect()
        except Exception as e:
            cleanup_errors.append(f"Garbage collection: {e}")
        
        # Clear component health tracking
        if hasattr(self, 'component_health'):
            self.component_health.clear()
        
        if hasattr(self, 'logger'):
            if cleanup_errors:
                self.logger.warning(f"Cleanup completed with {len(cleanup_errors)} errors:")
                for error in cleanup_errors:
                    self.logger.warning(f"  - {error}")
            else:
                self.logger.info("Cleanup completed successfully")
            
            # Write final status to help with debugging
            try:
                runtime = datetime.now() - self.process_info['start_time']
                self.logger.info(f"Total runtime: {runtime}")
                self.logger.info(f"Critical failures encountered: {self.critical_failures}")
            except:
                pass


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