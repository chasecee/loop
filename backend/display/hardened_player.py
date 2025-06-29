"""
HARDENED Display Player for LOOP - Single-threaded, bulletproof Pi deployment.
Eliminates thread chaos with simple, reliable synchronous operation.
"""

import os
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import struct
from dataclasses import dataclass, field

from config.schema import DisplayConfig, MediaConfig
from display.spiout import ILI9341Driver
from display.messages import MessageDisplay, set_message_display
from display.memory_pool import get_frame_buffer_pool
from utils.media_index import media_index
from utils.logger import get_logger


@dataclass
class MediaFrame:
    """Single media frame with timing info."""
    data: bytes
    duration: float = 0.04  # 25fps default


class SimpleFrameSequence:
    """Simplified frame sequence without threading chaos."""
    
    def __init__(self, frames_dir: Path, frame_count: int, frame_duration: float):
        self.frames_dir = frames_dir
        self.frame_count = frame_count
        self.frame_duration = frame_duration
        self.logger = get_logger("frames")
        
        # Pre-load frame list for performance
        self.frame_files = self._load_frame_list()
        
    def _load_frame_list(self) -> List[Path]:
        """Load and sort frame files."""
        if not self.frames_dir.exists():
            return []
        
        frame_files = []
        for i in range(self.frame_count):
            frame_file = self.frames_dir / f"frame_{i:06d}.rgb"
            if frame_file.exists():
                frame_files.append(frame_file)
            else:
                break  # Stop at first missing frame
        
        self.logger.info(f"Loaded {len(frame_files)} frames from {self.frames_dir}")
        return frame_files
    
    def get_frame_count(self) -> int:
        """Get number of available frames."""
        return len(self.frame_files)
    
    def get_frame(self, index: int) -> Optional[MediaFrame]:
        """Get frame by index synchronously."""
        if index >= len(self.frame_files):
            return None
        
        frame_file = self.frame_files[index]
        try:
            with open(frame_file, 'rb') as f:
                frame_data = f.read()
            return MediaFrame(frame_data, self.frame_duration)
        except Exception as e:
            self.logger.warning(f"Failed to load frame {index}: {e}")
            return None


class HardenedDisplayPlayer:
    """
    Hardened display player - single threaded, bulletproof.
    No WiFi status threads, no progress threads, no frame producer threads.
    """
    
    def __init__(self, display_driver: Optional[ILI9341Driver], 
                 display_config: DisplayConfig, 
                 media_config: MediaConfig,
                 wifi_manager=None):
        """Initialize the hardened display player."""
        self.display_driver = display_driver
        self.display_config = display_config
        self.media_config = media_config
        self.wifi_manager = wifi_manager
        self.logger = get_logger("player")
        
        # Hardware availability
        self.display_available = display_driver is not None
        if self.display_available:
            try:
                self.display_driver.init()
                self.display_available = self.display_driver.initialized
            except Exception as e:
                self.logger.warning(f"Display init failed: {e}")
                self.display_available = False
        
        if not self.display_available:
            self.logger.warning("Running in demo mode - no display hardware")
        
        # Simple messaging system (no worker thread)
        self.message_display = MessageDisplay(display_driver, display_config) if display_driver else None
        if self.message_display:
            set_message_display(self.message_display)
        
        # Media management
        self.media_dir = Path("media/processed")
        self.current_sequence: Optional[SimpleFrameSequence] = None
        self.current_frame_index = 0
        
        # Playback control
        self.running = False
        self.paused = False
        self.frame_rate = display_config.framerate
        self.loop_count = media_config.loop_count
        self.loop_mode = "all"
        
        # Per-media loop tracking
        self.current_media_loops = 0
        self.static_image_display_time = float(media_config.static_image_duration_sec)
        
        # Progress display (simplified - no threads)
        self.showing_progress = False
        self.progress_data = {}
        
        # Simple pause handling
        self.pause_event = threading.Event()
        self.pause_event.set()  # Start unpaused
        
        # Single playback thread
        self.playback_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # State tracking
        self.last_frame_time = 0
        self.last_media_check = 0
        self.last_wifi_check = 0
        
        self.logger.info("Hardened display player initialized")
    
    def start(self) -> None:
        """Start the display player."""
        if not self.running:
            self.running = True
            self.playback_thread = threading.Thread(target=self._main_loop, daemon=True)
            self.playback_thread.start()
            self.logger.info("Hardened display player started")
    
    def stop(self) -> None:
        """Stop the display player."""
        if self.running:
            self.running = False
            self.showing_progress = False
            
            if self.current_sequence:
                self.current_sequence = None
            
            if self.playback_thread:
                self.playback_thread.join(timeout=5)
                
            if self.message_display:
                self.message_display.stop()
                
            self.logger.info("Hardened display player stopped")
    
    def _main_loop(self) -> None:
        """Main playback loop - single threaded, handles everything."""
        self.logger.info("Starting hardened playback loop")
        
        while self.running:
            try:
                current_time = time.time()
                
                # Handle progress display (no separate thread)
                if self.showing_progress:
                    self._update_progress_display()
                    time.sleep(0.1)  # Fast updates during progress
                    continue
                
                # Check for media changes (every 2 seconds)
                if current_time - self.last_media_check >= 2.0:
                    self._check_media_changes()
                    self.last_media_check = current_time
                
                # Get current loop state
                loop_slugs = media_index.list_loop()
                
                # Show no media message if needed
                if not loop_slugs:
                    self._show_no_media_message()
                    time.sleep(2)  # Longer sleep when no media
                    continue
                
                # Load sequence if needed
                if not self.current_sequence:
                    if not self._load_current_sequence():
                        time.sleep(1)
                        continue
                
                # Display current frame
                if self.current_sequence and not self.paused:
                    self._display_next_frame()
                
                # Check for pause
                if self.paused:
                    time.sleep(0.1)
                    continue
                
                # Frame rate control
                target_frame_time = 1.0 / self.frame_rate
                elapsed = time.time() - current_time
                sleep_time = max(0, target_frame_time - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                self.logger.error(f"Main loop error: {e}")
                time.sleep(1)  # Back off on errors
        
        self.logger.info("Hardened playback loop stopped")
    
    def _check_media_changes(self) -> None:
        """Check for media changes and reload if needed."""
        try:
            current_active = media_index.get_active()
            
            # If no sequence loaded but we have active media, load it
            if not self.current_sequence and current_active:
                self._load_current_sequence()
            
            # If active media changed, reload
            elif self.current_sequence and current_active:
                loop_slugs = media_index.list_loop()
                if current_active in loop_slugs:
                    # Check if we need to reload due to media change
                    media_dict = media_index.get_media_dict()
                    current_media = media_dict.get(current_active)
                    if current_media:
                        expected_frames_dir = self.media_dir / current_active / "frames"
                        if self.current_sequence.frames_dir != expected_frames_dir:
                            self.logger.info("Media changed, reloading sequence")
                            self._load_current_sequence()
                            
        except Exception as e:
            self.logger.warning(f"Media change check failed: {e}")
    
    def _load_current_sequence(self) -> bool:
        """Load current media sequence."""
        try:
            active_slug = media_index.get_active()
            if not active_slug:
                return False
            
            media_dict = media_index.get_media_dict()
            media_info = media_dict.get(active_slug)
            if not media_info:
                return False
            
            frames_dir = self.media_dir / active_slug / "frames"
            if not frames_dir.exists():
                self.logger.warning(f"No frames directory for {active_slug}")
                return False
            
            # Get media properties
            frame_count = media_info.get('frame_count', 0)
            fps = media_info.get('fps', 25)
            frame_duration = 1.0 / fps
            
            # Create simple sequence
            self.current_sequence = SimpleFrameSequence(frames_dir, frame_count, frame_duration)
            self.current_frame_index = 0
            self.current_media_loops = 0
            
            if self.current_sequence.get_frame_count() == 0:
                self.logger.warning(f"No frames found for {active_slug}")
                self.current_sequence = None
                return False
            
            filename = media_info.get('filename', active_slug)
            self.logger.info(f"Loaded sequence: {filename} ({self.current_sequence.get_frame_count()} frames)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load sequence: {e}")
            return False
    
    def _display_next_frame(self) -> None:
        """Display the next frame in sequence."""
        if not self.current_sequence:
            return
        
        try:
            frame = self.current_sequence.get_frame(self.current_frame_index)
            if not frame:
                # End of sequence - handle looping
                self._handle_sequence_end()
                return
            
            # Display frame if hardware available
            if self.display_available and self.display_driver:
                try:
                    self.display_driver.display_frame(frame.data)
                except Exception as e:
                    self.logger.warning(f"Frame display failed: {e}")
                    self.display_available = False
            
            # Advance to next frame
            self.current_frame_index += 1
            self.last_frame_time = time.time()
            
        except Exception as e:
            self.logger.error(f"Frame display error: {e}")
    
    def _handle_sequence_end(self) -> None:
        """Handle end of sequence - looping logic."""
        self.current_media_loops += 1
        
        # Check if we should loop this media
        if self.loop_mode == "one" and self.current_media_loops < self.loop_count:
            # Loop current media
            self.current_frame_index = 0
            return
        
        # Move to next media
        self.current_media_loops = 0
        self.current_frame_index = 0
        self._advance_to_next_media()
    
    def _advance_to_next_media(self) -> None:
        """Advance to next media in loop."""
        try:
            loop_slugs = media_index.list_loop()
            if len(loop_slugs) <= 1:
                # Only one media, restart it
                self.current_frame_index = 0
                return
            
            current_active = media_index.get_active()
            if not current_active:
                return
            
            try:
                current_index = loop_slugs.index(current_active)
            except ValueError:
                current_index = 0
            
            # Move to next
            next_index = (current_index + 1) % len(loop_slugs)
            next_slug = loop_slugs[next_index]
            
            # Set active and clear sequence to trigger reload
            media_index.set_active(next_slug)
            self.current_sequence = None
            
        except Exception as e:
            self.logger.error(f"Failed to advance media: {e}")
    
    def _show_no_media_message(self) -> None:
        """Show no media message."""
        if not self.message_display:
            return
        
        try:
            # Get WiFi info for display
            web_url = "http://loop.local"
            hotspot_info = None
            
            if self.wifi_manager:
                try:
                    status = self.wifi_manager.get_status()
                    if status.get('connected'):
                        ip_address = status.get('ip_address')
                        if ip_address:
                            web_url = f"http://{ip_address}"
                    elif status.get('hotspot_active'):
                        hotspot_info = {
                            'ssid': status.get('hotspot_ssid', 'LOOP-Setup'),
                            'ip': '192.168.100.1'
                        }
                        web_url = "http://192.168.100.1"
                except Exception as e:
                    self.logger.debug(f"WiFi status check failed: {e}")
            
            self.message_display.show_no_media_message(web_url, hotspot_info)
            
        except Exception as e:
            self.logger.error(f"Failed to show no media message: {e}")
    
    def _update_progress_display(self) -> None:
        """Update progress display (simplified, no threads)."""
        if not self.message_display or not self.showing_progress:
            return
        
        try:
            # Get processing jobs
            processing_jobs = media_index.list_processing_jobs()
            
            # Find active jobs
            active_jobs = [job for job in processing_jobs.values() 
                          if job.get('status') == 'processing']
            
            if not active_jobs:
                # No active jobs, stop progress display
                self.showing_progress = False
                return
            
            # Show progress for first active job
            job = active_jobs[0]
            progress = job.get('progress', 0)
            stage = job.get('stage', 'Processing')
            
            self.message_display.show_progress_bar("Processing Media", stage, progress)
            
            # Auto-stop if completed
            if progress >= 100:
                self.showing_progress = False
                
        except Exception as e:
            self.logger.error(f"Progress update failed: {e}")
            self.showing_progress = False
    
    # Public API methods
    
    def get_status(self) -> Dict:
        """Get current playback status."""
        current_media = media_index.get_active()
        loop_slugs = media_index.list_loop()
        
        return {
            "is_playing": self.running and not self.paused,
            "current_media": current_media,
            "loop_index": self._get_current_media_index(),
            "total_media": len(loop_slugs),
            "frame_rate": self.frame_rate,
            "loop_mode": self.loop_mode,
            "showing_progress": self.showing_progress
        }
    
    def _get_current_media_index(self) -> int:
        """Get current media index in loop."""
        active_slug = media_index.get_active()
        if not active_slug:
            return 0
        
        loop_slugs = media_index.list_loop()
        try:
            return loop_slugs.index(active_slug)
        except ValueError:
            return 0
    
    def next_media(self) -> None:
        """Switch to next media."""
        with self.lock:
            self._advance_to_next_media()
    
    def previous_media(self) -> None:
        """Switch to previous media."""
        with self.lock:
            try:
                loop_slugs = media_index.list_loop()
                if len(loop_slugs) <= 1:
                    return
                
                current_active = media_index.get_active()
                try:
                    current_index = loop_slugs.index(current_active) if current_active else 0
                except ValueError:
                    current_index = 0
                
                # Move to previous
                prev_index = (current_index - 1) % len(loop_slugs)
                prev_slug = loop_slugs[prev_index]
                
                media_index.set_active(prev_slug)
                self.current_sequence = None  # Force reload
                
            except Exception as e:
                self.logger.error(f"Failed to go to previous media: {e}")
    
    def set_active_media(self, slug: str) -> bool:
        """Set active media."""
        with self.lock:
            try:
                media_dict = media_index.get_media_dict()
                if slug not in media_dict:
                    return False
                
                media_index.set_active(slug)
                self.current_sequence = None  # Force reload
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to set active media: {e}")
                return False
    
    def pause(self) -> None:
        """Pause playback."""
        with self.lock:
            self.paused = True
            self.pause_event.clear()
    
    def resume(self) -> None:
        """Resume playback."""
        with self.lock:
            self.paused = False
            self.pause_event.set()
    
    def toggle_pause(self) -> None:
        """Toggle pause state."""
        if self.paused:
            self.resume()
        else:
            self.pause()
    
    def is_paused(self) -> bool:
        """Check if paused."""
        return self.paused
    
    def toggle_loop_mode(self) -> str:
        """Toggle loop mode."""
        with self.lock:
            self.loop_mode = "one" if self.loop_mode == "all" else "all"
            return self.loop_mode
    
    def show_boot_message(self, version: str = "1.0") -> None:
        """Show boot message."""
        if self.message_display:
            self.message_display.show_boot_message(version)
    
    def show_message(self, title: str, subtitle: str = "", duration: float = 2.0) -> None:
        """Show message."""
        if self.message_display:
            self.message_display.show_message(title, subtitle, duration)
    
    def show_error_message(self, error: str) -> None:
        """Show error message."""
        if self.message_display:
            self.message_display.show_error_message(error)
    
    def start_processing_display(self, job_ids: List[str]) -> None:
        """Start showing progress (simplified)."""
        if self.display_config.show_progress:
            self.showing_progress = True
            self.progress_data = {"job_ids": job_ids, "start_time": time.time()}
    
    def stop_processing_display(self) -> None:
        """Stop showing progress."""
        self.showing_progress = False
        self.progress_data = {}
    
    def force_stop_progress_display(self) -> None:
        """Force stop progress display."""
        self.stop_processing_display()
    
    def handle_media_deletion(self, deleted_slug: str) -> None:
        """Handle media deletion."""
        with self.lock:
            if self.current_sequence:
                # Check if current sequence is for deleted media
                if deleted_slug in str(self.current_sequence.frames_dir):
                    self.current_sequence = None
            
            # Force media list refresh
            self.last_media_check = 0
    
    def refresh_media_list(self) -> None:
        """Refresh media list."""
        with self.lock:
            self.current_sequence = None
            self.last_media_check = 0
    
    # Notification methods for compatibility
    def notify_upload_start(self, count: int = 1) -> None:
        """Notify upload started."""
        pass  # Simplified - handled by polling
    
    def notify_processing(self, filename: str = "") -> None:
        """Notify processing started."""
        pass  # Simplified - handled by polling
    
    def notify_error(self, error: str) -> None:
        """Notify error."""
        self.show_error_message(error)
    
    def clear_messages(self) -> None:
        """Clear messages."""
        pass  # Simplified
