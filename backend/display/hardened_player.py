"""
HARDENED Display Player for LOOP - Single-threaded, bulletproof Pi deployment.
Eliminates thread chaos with simple, reliable synchronous operation.
"""

import os
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import struct
from dataclasses import dataclass, field

from config.schema import DisplayConfig, MediaConfig
from display.spiout import ILI9341Driver
from display.messages import MessageDisplay, set_message_display
from display.memory_pool import get_frame_buffer_pool
from utils.media_index import media_index
from utils.logger import get_logger
from utils.memory_monitor import MemoryMonitor


@dataclass
class MediaFrame:
    """Single media frame with timing info."""
    data: bytes
    duration: float = 0.04  # 25fps default


class BinaryFrameSequence:
    """Binary frame sequence - loads from single frames.bin file."""
    
    def __init__(self, frames_dir: Path):
        self.frames_dir = frames_dir
        self.frames_file = frames_dir / "frames.bin"
        self.logger = get_logger("frames")
        
        # Load frame data from binary file
        self.frame_count = 0
        self.frame_size = 0
        self.frame_data: Optional[bytes] = None
        
        self._load_binary_frames()
        
    def _load_binary_frames(self) -> None:
        """Load frames from binary file format."""
        if not self.frames_file.exists():
            self.logger.warning(f"No frames.bin file at {self.frames_file}")
            return
        
        try:
            with open(self.frames_file, 'rb') as f:
                # Read header: [frame_count:4][frame_size:4]
                header = f.read(8)
                if len(header) != 8:
                    self.logger.error("Invalid frames.bin header")
                    return
                
                # Parse header (big-endian)
                self.frame_count, self.frame_size = struct.unpack('>II', header)
                
                # Read all frame data
                expected_size = self.frame_count * self.frame_size
                self.frame_data = f.read(expected_size)
                
                if len(self.frame_data) != expected_size:
                    self.logger.error(f"Frame data size mismatch: expected {expected_size}, got {len(self.frame_data)}")
                    self.frame_data = None
                    self.frame_count = 0
                    return
                
                self.logger.info(f"Loaded {self.frame_count} frames from {self.frames_file} ({len(self.frame_data)} bytes)")
                
        except Exception as e:
            self.logger.error(f"Failed to load binary frames: {e}")
            self.frame_count = 0
            self.frame_data = None
    
    def get_frame_count(self) -> int:
        """Get number of available frames."""
        return self.frame_count
    
    def get_frame(self, index: int) -> Optional[MediaFrame]:
        """Get frame by index from binary data."""
        if not self.frame_data or index >= self.frame_count:
            return None
        
        try:
            # Calculate offset for this frame
            offset = index * self.frame_size
            frame_bytes = self.frame_data[offset:offset + self.frame_size]
            
            if len(frame_bytes) != self.frame_size:
                self.logger.warning(f"Frame {index} incomplete: {len(frame_bytes)} bytes")
                return None
            
            return MediaFrame(frame_bytes, 0.04)  # 25fps default
            
        except Exception as e:
            self.logger.warning(f"Failed to get frame {index}: {e}")
            return None


class SimpleFrameSequence:
    """DEPRECATED: Fallback for old individual frame files."""
    
    def __init__(self, frames_dir: Path, frame_count: int, frame_duration: float):
        self.frames_dir = frames_dir
        self.frame_count = frame_count
        self.frame_duration = frame_duration
        self.logger = get_logger("frames")
        
        # Pre-load frame list for performance
        self.frame_files = self._load_frame_list()
        
    def _load_frame_list(self) -> List[Path]:
        """Load and sort frame files - HARDENED: scan directory, don't trust metadata."""
        if not self.frames_dir.exists():
            return []
        
        frame_files = []
        
        # Scan directory for actual frames instead of trusting frame_count
        i = 0
        while True:
            frame_file = self.frames_dir / f"frame_{i:06d}.rgb"
            if frame_file.exists():
                frame_files.append(frame_file)
                i += 1
            else:
                break  # No more consecutive frames
        
        # Fallback: if no consecutive frames found, scan all .rgb files
        if not frame_files:
            try:
                rgb_files = sorted(self.frames_dir.glob("*.rgb"))
                frame_files = [f for f in rgb_files if f.name.startswith("frame_")]
            except Exception as e:
                self.logger.warning(f"Directory scan fallback failed: {e}")
        
        self.logger.info(f"Loaded {len(frame_files)} frames from {self.frames_dir} (metadata claimed {self.frame_count})")
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
        
        # Memory pressure monitoring
        self.memory_monitor = MemoryMonitor()
        self.low_memory_mode = False
        self.frame_cache_size = 10  # Start with small cache
        self.max_frame_cache_size = 50  # Max frames to keep in memory
        
        # Hardware availability with fallback chain
        self.display_available = False
        self.display_failure_count = 0
        self.max_display_failures = 5
        self.display_recovery_attempts = 0
        self.max_recovery_attempts = 3
        
        # Initialize display with comprehensive error handling
        self._initialize_display_with_fallbacks()
        
        # Simple messaging system (robust fallback handling)
        self.message_display = None
        if self.display_available and self.display_driver:
            try:
                self.message_display = MessageDisplay(self.display_driver, display_config)
                set_message_display(self.message_display)
            except Exception as e:
                self.logger.warning(f"Message display initialization failed: {e}")
                self.display_available = False
        
        if not self.display_available:
            self.logger.warning("Running in headless mode - display functionality disabled")
        
        # Media management with memory optimization
        self.media_dir = Path("media/processed")
        self.current_sequence: Optional[Union[BinaryFrameSequence, SimpleFrameSequence]] = None
        self.current_frame_index = 0
        self.frame_cache: Dict[int, bytes] = {}  # LRU frame cache
        self.frame_cache_order: List[int] = []   # Track access order for LRU
        
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
        self.last_display_check = 0
        self.last_memory_check = 0
        
        self.logger.info("Hardened display player initialized with memory monitoring")
        
        # Start memory monitoring
        self.memory_monitor.start()
    
    def _initialize_display_with_fallbacks(self) -> None:
        """Initialize display with comprehensive fallback chain."""
        if not self.display_driver:
            self.logger.info("No display driver provided - running headless")
            return
        
        # Primary initialization attempt
        try:
            self.display_driver.init()
            if hasattr(self.display_driver, 'initialized') and self.display_driver.initialized:
                self.display_available = True
                self.logger.info("Display driver initialized successfully")
                return
        except PermissionError as e:
            self.logger.error(f"Display permission error (check SPI permissions): {e}")
        except OSError as e:
            self.logger.error(f"Display hardware error (check SPI/GPIO connections): {e}")
        except Exception as e:
            self.logger.error(f"Display initialization failed: {e}")
        
        # Fallback: Try alternative initialization methods
        fallback_methods = [
            self._try_display_recovery,
            self._try_display_reset,
            self._try_display_minimal_init
        ]
        
        for i, fallback_method in enumerate(fallback_methods):
            try:
                self.logger.info(f"Attempting display fallback method {i + 1}/{len(fallback_methods)}")
                if fallback_method():
                    self.display_available = True
                    self.logger.info(f"Display recovered using fallback method {i + 1}")
                    return
            except Exception as e:
                self.logger.warning(f"Display fallback method {i + 1} failed: {e}")
        
        # All fallbacks failed
        self.display_available = False
        self.logger.warning("All display initialization methods failed - continuing headless")
    
    def _try_display_recovery(self) -> bool:
        """Attempt display recovery with delay."""
        import time
        time.sleep(0.5)  # Brief delay for hardware reset
        
        try:
            if hasattr(self.display_driver, 'cleanup'):
                self.display_driver.cleanup()
        except Exception as e:
            self.logger.debug(f"Display cleanup failed: {e}")
        
        try:
            self.display_driver.init()
            return hasattr(self.display_driver, 'initialized') and self.display_driver.initialized
        except Exception as e:
            self.logger.debug(f"Display init failed: {e}")
            return False
    
    def _try_display_reset(self) -> bool:
        """Attempt display reset sequence."""
        try:
            # Try to reset display if reset method exists
            if hasattr(self.display_driver, 'reset'):
                self.display_driver.reset()
            
            # Re-initialize
            self.display_driver.init()
            return hasattr(self.display_driver, 'initialized') and self.display_driver.initialized
        except Exception as e:
            self.logger.debug(f"Display reset failed: {e}")
            return False
    
    def _try_display_minimal_init(self) -> bool:
        """Attempt minimal display initialization."""
        try:
            # Try minimal initialization if available
            if hasattr(self.display_driver, 'minimal_init'):
                return self.display_driver.minimal_init()
            return False
        except Exception as e:
            self.logger.debug(f"Minimal display init failed: {e}")
            return False
    
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
                
                # Check for media changes - more frequent when no media loaded
                media_check_interval = 0.5 if not self.current_sequence else 2.0
                if current_time - self.last_media_check >= media_check_interval:
                    self._check_media_changes()
                    self.last_media_check = current_time
                
                # Get current loop state
                loop_slugs = media_index.list_loop()
                
                # Show no media message if needed
                if not loop_slugs:
                    self._show_no_media_message()
                    time.sleep(5)  # Show message for 5 seconds before checking again
                    continue
                
                # Load sequence if needed
                if not self.current_sequence:
                    if not self._load_current_sequence():
                        # Failed to load any sequence - treat as no media
                        self.logger.warning("Failed to load any media sequence")
                        time.sleep(2)
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
            loop_slugs = media_index.list_loop()
            
            # If no sequence loaded but we have active media, load it
            if not self.current_sequence and current_active:
                self.logger.info(f"No sequence loaded but found active media: {current_active}")
                self._load_current_sequence()
            
            # If no active media but we have media in loop, activate the first one
            elif not current_active and loop_slugs:
                first_slug = loop_slugs[0]
                self.logger.info(f"No active media but found loop content, activating: {first_slug}")
                media_index.set_active(first_slug)
                self._load_current_sequence()
            
            # If active media changed, reload
            elif self.current_sequence and current_active:
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
        """Load current media sequence - tries binary format first, falls back to individual files."""
        try:
            active_slug = media_index.get_active()
            if not active_slug:
                self.logger.debug("No active media to load")
                return False
            
            media_dict = media_index.get_media_dict()
            media_info = media_dict.get(active_slug)
            if not media_info:
                self.logger.warning(f"Active media {active_slug} not found in index, clearing")
                media_index.set_active(None)
                return False
            
            frames_dir = self.media_dir / active_slug / "frames"
            if not frames_dir.exists():
                self.logger.warning(f"No frames directory for {active_slug}, removing from index")
                # Clean up stale media reference
                media_index.remove_from_loop(active_slug)
                if media_index.get_active() == active_slug:
                    media_index.set_active(None)
                return False
            
            # Try binary format first (new efficient format)
            binary_sequence = BinaryFrameSequence(frames_dir)
            if binary_sequence.get_frame_count() > 0:
                self.current_sequence = binary_sequence
                self.current_frame_index = 0
                self.current_media_loops = 0
                
                filename = media_info.get('filename', active_slug)
                self.logger.info(f"Loaded binary sequence: {filename} ({binary_sequence.get_frame_count()} frames)")
                return True
            
            # Fall back to individual frame files (legacy format)
            self.logger.info("Binary format not available, falling back to individual frame files")
            
            # Get media properties for legacy format
            frame_count = media_info.get('frame_count', 0)
            fps = media_info.get('fps', 25)
            frame_duration = 1.0 / fps
            
            # Create legacy sequence
            legacy_sequence = SimpleFrameSequence(frames_dir, frame_count, frame_duration)
            
            if legacy_sequence.get_frame_count() == 0:
                self.logger.warning(f"No frames found for {active_slug} in either format, cleaning up")
                # Clean up stale media reference
                media_index.remove_from_loop(active_slug)
                if media_index.get_active() == active_slug:
                    media_index.set_active(None)
                self.current_sequence = None
                return False
            
            self.current_sequence = legacy_sequence
            self.current_frame_index = 0
            self.current_media_loops = 0
            
            filename = media_info.get('filename', active_slug)
            self.logger.info(f"Loaded legacy sequence: {filename} ({legacy_sequence.get_frame_count()} frames)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load sequence: {e}")
            # On any error, clear the current sequence and try to clean up
            self.current_sequence = None
            return False
    
    def _display_next_frame(self) -> None:
        """Display the next frame in sequence with error recovery and memory optimization."""
        if not self.current_sequence:
            return
        
        try:
            # Check memory pressure periodically
            current_time = time.time()
            if current_time - self.last_memory_check > 30:
                self._adapt_to_memory_pressure()
                self.last_memory_check = current_time
            
            # Get frame with caching
            frame_data = self._get_frame_cached(self.current_frame_index)
            if not frame_data:
                # End of sequence - handle looping
                self._handle_sequence_end()
                return
            
            # Display frame with comprehensive error handling
            if self.display_available and self.display_driver:
                display_success = self._safe_display_frame(frame_data)
                
                if not display_success:
                    # Display failed - attempt recovery
                    self._handle_display_failure()
                    return
            
            # Advance to next frame only if display succeeded or no display
            self.current_frame_index += 1
            self.last_frame_time = time.time()
            
            # Preload next few frames if memory allows
            if self.memory_monitor.should_preload_frames():
                self._preload_next_frames()
            
        except Exception as e:
            self.logger.error(f"Frame display error: {e}")
            self._handle_display_failure()
    
    def _get_frame_cached(self, frame_index: int) -> Optional[bytes]:
        """Get frame with LRU caching."""
        # Check cache first
        if frame_index in self.frame_cache:
            # Move to end of access order (most recently used)
            self.frame_cache_order.remove(frame_index)
            self.frame_cache_order.append(frame_index)
            return self.frame_cache[frame_index]
        
        # Cache miss - load frame
        if not self.current_sequence:
            return None
        
        frame = self.current_sequence.get_frame(frame_index)
        if not frame:
            return None
        
        frame_data = frame.data
        
        # Add to cache if there's room or memory allows
        if self._can_cache_frame():
            self._add_frame_to_cache(frame_index, frame_data)
        
        return frame_data
    
    def _can_cache_frame(self) -> bool:
        """Check if we can add another frame to cache."""
        current_cache_size = len(self.frame_cache)
        optimal_cache_size = self.memory_monitor.suggest_cache_size(
            self.frame_cache_size, 
            self.max_frame_cache_size
        )
        
        return current_cache_size < optimal_cache_size
    
    def _add_frame_to_cache(self, frame_index: int, frame_data: bytes) -> None:
        """Add frame to LRU cache."""
        # Check if we need to evict old frames
        while len(self.frame_cache) >= self.memory_monitor.suggest_cache_size(
            self.frame_cache_size, self.max_frame_cache_size
        ):
            if not self.frame_cache_order:
                break
            
            # Remove least recently used frame
            lru_index = self.frame_cache_order.pop(0)
            if lru_index in self.frame_cache:
                del self.frame_cache[lru_index]
        
        # Add new frame
        self.frame_cache[frame_index] = frame_data
        self.frame_cache_order.append(frame_index)
    
    def _preload_next_frames(self) -> None:
        """Preload next few frames if memory allows."""
        if not self.current_sequence or self.memory_monitor.is_low_memory():
            return
        
        # Preload next 3-5 frames
        preload_count = 3 if self.memory_monitor.is_low_memory() else 5
        
        for i in range(1, preload_count + 1):
            next_index = self.current_frame_index + i
            
            if next_index in self.frame_cache:
                continue  # Already cached
            
            if not self._can_cache_frame():
                break  # Cache full
            
            # Load frame in background
            try:
                frame = self.current_sequence.get_frame(next_index)
                if frame:
                    self._add_frame_to_cache(next_index, frame.data)
                else:
                    break  # End of sequence
            except Exception as e:
                self.logger.debug(f"Preload failed for frame {next_index}: {e}")
                break
    
    def _adapt_to_memory_pressure(self) -> None:
        """Adapt behavior based on current memory pressure."""
        if self.memory_monitor.is_low_memory():
            if not self.low_memory_mode:
                self.logger.warning("Entering low-memory mode - reducing frame cache")
                self.low_memory_mode = True
                self._clear_excess_cache()
        else:
            if self.low_memory_mode:
                self.logger.info("Exiting low-memory mode - normal caching resumed")
                self.low_memory_mode = False
    
    def _clear_excess_cache(self) -> None:
        """Clear excess frames from cache when in low-memory mode."""
        optimal_size = self.memory_monitor.suggest_cache_size(
            self.frame_cache_size, self.max_frame_cache_size
        )
        
        while len(self.frame_cache) > optimal_size and self.frame_cache_order:
            # Remove least recently used frames
            lru_index = self.frame_cache_order.pop(0)
            if lru_index in self.frame_cache:
                del self.frame_cache[lru_index]
        
        if len(self.frame_cache) < len(self.frame_cache_order):
            # Clean up order list
            self.frame_cache_order = [i for i in self.frame_cache_order if i in self.frame_cache]
    
    def _safe_display_frame(self, frame_data: bytes) -> bool:
        """Safely display a frame with error handling."""
        try:
            self.display_driver.display_frame(frame_data)
            # Reset failure count on successful display
            self.display_failure_count = 0
            return True
            
        except PermissionError as e:
            self.logger.error(f"Display permission error: {e}")
            self.display_failure_count += 1
            return False
        except OSError as e:
            self.logger.warning(f"Display hardware error: {e}")
            self.display_failure_count += 1
            return False
        except Exception as e:
            self.logger.warning(f"Display frame failed: {e}")
            self.display_failure_count += 1
            return False
    
    def _handle_display_failure(self) -> None:
        """Handle display failures with recovery attempts."""
        self.display_failure_count += 1
        
        if self.display_failure_count >= self.max_display_failures:
            self.logger.error(f"Display failed {self.display_failure_count} times, attempting recovery")
            
            if self.display_recovery_attempts < self.max_recovery_attempts:
                self.display_recovery_attempts += 1
                self.logger.info(f"Attempting display recovery {self.display_recovery_attempts}/{self.max_recovery_attempts}")
                
                # Try to recover display
                recovery_success = self._attempt_display_recovery()
                
                if recovery_success:
                    self.logger.info("Display recovery successful")
                    self.display_failure_count = 0
                    self.display_available = True
                else:
                    self.logger.warning(f"Display recovery attempt {self.display_recovery_attempts} failed")
                    
                    if self.display_recovery_attempts >= self.max_recovery_attempts:
                        self.logger.error("All display recovery attempts exhausted - switching to headless mode")
                        self.display_available = False
                        self.message_display = None
            else:
                # Already tried max recovery attempts
                if self.display_available:
                    self.logger.warning("Display recovery exhausted - continuing headless")
                    self.display_available = False
                    self.message_display = None
    
    def _attempt_display_recovery(self) -> bool:
        """Attempt to recover the display driver."""
        try:
            # Try cleanup first
            if hasattr(self.display_driver, 'cleanup'):
                try:
                    self.display_driver.cleanup()
                except Exception as e:
                    self.logger.debug(f"Display cleanup during recovery failed: {e}")
            
            # Brief delay for hardware reset
            import time
            time.sleep(1.0)
            
            # Try re-initialization
            self.display_driver.init()
            
            # Test with a simple frame
            if hasattr(self.display_driver, 'initialized') and self.display_driver.initialized:
                # Try to display a black frame to test
                test_frame = b'\x00\x00' * (320 * 240)  # Black frame for 320x240 display
                try:
                    self.display_driver.display_frame(test_frame)
                    return True
                except Exception as e:
                    self.logger.debug(f"Test frame display failed: {e}")
                    return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Display recovery failed: {e}")
            return False
    
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
            self.logger.debug("No message display available for no media message")
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
                            'ip': '192.168.24.1'
                        }
                        web_url = "http://192.168.24.1"
                except Exception as e:
                    self.logger.debug(f"WiFi status check failed: {e}")
            
            # Show the no media message - this will persist until replaced
            self.message_display.show_no_media_message(web_url, hotspot_info)
            self.logger.debug(f"Displayed no media message with URL: {web_url}")
            
        except Exception as e:
            self.logger.error(f"Failed to show no media message: {e}")
            # Fallback: try to show a simple error message
            try:
                if self.message_display:
                    self.message_display.show_message("No Media", "Upload media via web interface", 0)
            except Exception as fallback_error:
                self.logger.error(f"Fallback message also failed: {fallback_error}")
    
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
    
    def force_media_check(self) -> None:
        """Force immediate media check - useful after uploads."""
        with self.lock:
            self.last_media_check = 0  # Force immediate check on next loop iteration
            self.logger.debug("Forced media check - will check on next loop iteration")
    
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
