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


class LOOPApplication:
    """Main LOOP application coordinator."""
    
    def __init__(self):
        """Initialize the application."""
        self._ensure_default_media()
        self.config = get_config()
        self.logger = get_logger("app")
        self.logger.info(f"Starting LOOP v{self.config.device.version}")
        
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
        
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
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
        """Initialize the display system."""
        try:
            self.logger.info("Initializing display system...")
            
            # Create display driver
            self.display_driver = ILI9341Driver(self.config.display)
            self.display_driver.init()
            
            # Create display player
            from display.player import DisplayPlayer
            self.display_player = DisplayPlayer(
                self.display_driver,
                self.config.display,
                self.config.media
            )
            
            self.logger.info("Display system initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize display: {e}")
            # Continue running headless – don't crash the whole service
            self.logger.warning("Continuing without display (headless mode)")
    
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
        """Initialize WiFi management."""
        try:
            self.logger.info("Initializing WiFi management...")
            
            from boot.wifi import WiFiManager
            self.wifi_manager = WiFiManager(self.config.wifi)
            
            # Try to connect to configured WiFi
            if self.config.wifi.ssid:
                if self.wifi_manager.connect():
                    self.logger.info(f"Connected to WiFi: {self.config.wifi.ssid}")
                else:
                    self.logger.warning("Failed to connect to configured WiFi")
                    # Start hotspot mode
                    self.wifi_manager.start_hotspot()
            else:
                self.logger.info("No WiFi configured, starting in hotspot mode")
                self.wifi_manager.start_hotspot()
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WiFi: {e}")
    
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
            
            # Configure uvicorn
            config = uvicorn.Config(
                app,
                host=self.config.web.host,
                port=self.config.web.port,
                log_level="info" if self.config.web.debug else "warning",
                access_log=self.config.web.debug
            )
            
            # Run server in thread
            server = uvicorn.Server(config)
            server_thread = threading.Thread(
                target=server.run,
                name="WebServer",
                daemon=True
            )
            server_thread.start()
            self.threads.append(server_thread)
            
            self.logger.info(f"Web server started on {self.config.web.host}:{self.config.web.port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start web server: {e}")
            raise
    
    def start_display_player(self):
        """Start the display player."""
        if self.display_player:
            try:
                self.logger.info("Starting display player...")
                
                player_thread = threading.Thread(
                    target=self.display_player.run,
                    name="DisplayPlayer",
                    daemon=True
                )
                player_thread.start()
                self.threads.append(player_thread)
                
                self.logger.info("Display player started")
                
            except Exception as e:
                self.logger.error(f"Failed to start display player: {e}")
    
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
            
            # Main loop - wait for shutdown signal instead of busy polling
            try:
                while self.running:
                    # Wait for shutdown signal with timeout for responsiveness
                    if self.shutdown_event.wait(timeout=1.0):
                        break
                        
                    # Optional: Add periodic maintenance tasks here
                    # self._periodic_maintenance()
                    
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
        """Clean up resources."""
        if hasattr(self, 'logger'):
            self.logger.info("Cleaning up resources...")
        
        # Stop display player
        if self.display_player:
            self.display_player.stop()
        
        # Stop encoder
        if self.encoder:
            self.encoder.stop()
        
        # Cleanup display driver
        if self.display_driver:
            try:
                self.display_driver.fill_screen(0x0000)  # Clear screen
                self.display_driver.cleanup()
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"Error cleaning up display: {e}")
        
        # Stop WiFi manager
        if self.wifi_manager:
            self.wifi_manager.cleanup()
        
        # Wait for threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=2.0)
        
        if hasattr(self, 'logger'):
            self.logger.info("Cleanup completed")


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