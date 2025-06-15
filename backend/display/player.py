"""Display playback engine for LOOP."""

import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont

from config.schema import DisplayConfig, MediaConfig
from display.framebuf import FrameSequence, FrameDecoder, FrameBuffer
from display.spiout import ILI9341Driver
from utils.logger import get_logger


class DisplayPlayer:
    """Main display playback engine."""
    
    def __init__(self, display_driver: ILI9341Driver, 
                 display_config: DisplayConfig, 
                 media_config: MediaConfig):
        """Initialize the display player."""
        self.display_driver = display_driver
        self.display_config = display_config
        self.media_config = media_config
        self.logger = get_logger("player")
        
        # Media management
        self.media_dir = Path("media/processed")
        self.media_index_file = Path("media/index.json")
        self.current_sequence: Optional[FrameSequence] = None
        self.media_list: List[Dict] = []
        self.current_media_index = 0
        
        # Playback control
        self.running = False
        self.paused = False
        self.frame_rate = display_config.framerate
        self.loop_count = media_config.loop_count
        
        # Threading
        self.playback_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # Status display
        self.frame_buffer = FrameBuffer(display_config.width, display_config.height)
        
        # Load media index
        self.load_media_index()
        
        self.logger.info(f"Display player initialized with {len(self.media_list)} media items")
    
    def load_media_index(self) -> None:
        """Load the media index from file."""
        try:
            if self.media_index_file.exists():
                with open(self.media_index_file, 'r') as f:
                    data = json.load(f)
                    self.media_list = data.get('media', [])
                    
                    # Set active media if specified
                    active_slug = data.get('active')
                    if active_slug:
                        for i, media in enumerate(self.media_list):
                            if media.get('slug') == active_slug:
                                self.current_media_index = i
                                break
                                
                self.logger.info(f"Loaded {len(self.media_list)} media items from index")
            else:
                self.logger.info("No media index found, creating empty list")
                self.save_media_index()
                
        except Exception as e:
            self.logger.error(f"Failed to load media index: {e}")
            self.media_list = []
    
    def save_media_index(self) -> None:
        """Save the media index to file."""
        try:
            data = {
                'media': self.media_list,
                'active': self.get_current_media_slug(),
                'last_updated': time.time()
            }
            
            with open(self.media_index_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save media index: {e}")
    
    def get_current_media_slug(self) -> Optional[str]:
        """Get the slug of the currently selected media."""
        if 0 <= self.current_media_index < len(self.media_list):
            return self.media_list[self.current_media_index].get('slug')
        return None
    
    def load_current_sequence(self) -> bool:
        """Load the current media sequence."""
        if not self.media_list or not (0 <= self.current_media_index < len(self.media_list)):
            self.logger.warning("No media available to load")
            return False
        
        media_info = self.media_list[self.current_media_index]
        media_slug = media_info.get('slug')
        
        if not media_slug:
            self.logger.error("Media has no slug")
            return False
        
        frames_dir = self.media_dir / media_slug / "frames"
        
        if not frames_dir.exists():
            self.logger.error(f"Frames directory not found: {frames_dir}")
            return False
        
        try:
            self.current_sequence = FrameSequence(
                frames_dir, 
                self.display_config.width, 
                self.display_config.height
            )
            
            if self.current_sequence.get_frame_count() == 0:
                self.logger.error(f"No frames found in {frames_dir}")
                return False
            
            self.logger.info(f"Loaded media: {media_info.get('original_filename', media_slug)}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load sequence: {e}")
            return False
    
    def next_media(self) -> None:
        """Switch to next media."""
        with self.lock:
            if len(self.media_list) <= 1:
                return
            
            self.current_media_index = (self.current_media_index + 1) % len(self.media_list)
            self.load_current_sequence()
            self.save_media_index()
            
            media_name = self.media_list[self.current_media_index].get('original_filename', 'Unknown')
            self.logger.info(f"Switched to next media: {media_name}")
    
    def previous_media(self) -> None:
        """Switch to previous media."""
        with self.lock:
            if len(self.media_list) <= 1:
                return
            
            self.current_media_index = (self.current_media_index - 1) % len(self.media_list)
            self.load_current_sequence()
            self.save_media_index()
            
            media_name = self.media_list[self.current_media_index].get('original_filename', 'Unknown')
            self.logger.info(f"Switched to previous media: {media_name}")
    
    def set_active_media(self, slug: str) -> bool:
        """Set active media by slug."""
        with self.lock:
            for i, media in enumerate(self.media_list):
                if media.get('slug') == slug:
                    self.current_media_index = i
                    success = self.load_current_sequence()
                    if success:
                        self.save_media_index()
                        self.logger.info(f"Set active media: {media.get('original_filename', slug)}")
                    return success
            
            self.logger.error(f"Media not found: {slug}")
            return False
    
    def toggle_pause(self) -> None:
        """Toggle playback pause state."""
        with self.lock:
            self.paused = not self.paused
            self.logger.info(f"Playback {'paused' if self.paused else 'resumed'}")
    
    def is_paused(self) -> bool:
        """Check if playback is paused."""
        return self.paused
    
    def show_message(self, message: str, duration: float = 2.0, color: int = 0xFFFF) -> None:
        """Display a text message on screen."""
        try:
            # Create a simple text display using PIL
            img = Image.new('RGB', (self.display_config.width, self.display_config.height), 'black')
            draw = ImageDraw.Draw(img)
            
            # Try to use a simple font - fallback to default if not available
            try:
                # Use a reasonable font size for the display
                font_size = min(self.display_config.width, self.display_config.height) // 10
                font = ImageFont.load_default()  # Use default font
            except:
                font = None
            
            # Calculate text position (center)
            bbox = draw.textbbox((0, 0), message, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (self.display_config.width - text_width) // 2
            y = (self.display_config.height - text_height) // 2
            
            # Draw text
            draw.text((x, y), message, fill='white', font=font)
            
            # Convert to RGB565 and display
            decoder = FrameDecoder(self.display_config.width, self.display_config.height)
            
            # Convert PIL image to RGB mode and get raw bytes
            img = img.convert('RGB')  # Ensure RGB mode
            frame_data = decoder.decode_image_bytes(img.tobytes('raw', 'RGB'))
            
            if frame_data:
                self.display_driver.display_frame(frame_data)
                
                # Keep message on screen for duration
                if duration > 0:
                    time.sleep(duration)
            
        except Exception as e:
            self.logger.error(f"Failed to show message: {e}")
    
    def show_no_media_message(self) -> None:
        """Show 'no media' message."""
        self.show_message("No Media\nUpload GIFs via\nWeb Interface", duration=0)
    
    def run(self) -> None:
        """Main playback loop."""
        self.running = True
        self.logger.info("Starting display playback loop")
        
        # Initial setup
        if not self.display_driver.initialized:
            self.display_driver.init()
        
        last_frame_time = time.time()
        loop_count = 0
        
        try:
            while self.running:
                # Check if we have media to play
                if not self.media_list:
                    self.show_no_media_message()
                    time.sleep(5)  # Check again in 5 seconds
                    self.load_media_index()  # Reload in case new media was added
                    continue
                
                # Load current sequence if needed
                if not self.current_sequence:
                    if not self.load_current_sequence():
                        self.show_message("Error loading media", duration=3.0)
                        time.sleep(1)
                        continue
                
                # Skip frame if paused
                if self.paused:
                    time.sleep(0.1)
                    continue
                
                # Get current media info
                if 0 <= self.current_media_index < len(self.media_list):
                    media_info = self.media_list[self.current_media_index]
                    durations = media_info.get('durations', [0.1])
                    
                    # Get next frame
                    frame_data = self.current_sequence.next_frame()
                    
                    if frame_data:
                        # Display frame
                        self.display_driver.display_frame(frame_data)
                        
                        # Calculate frame timing
                        frame_index = self.current_sequence.current_frame - 1
                        if frame_index < 0:
                            frame_index = self.current_sequence.frame_count - 1
                        
                        # Get duration for this frame
                        if frame_index < len(durations):
                            frame_duration = durations[frame_index]
                        else:
                            frame_duration = durations[0] if durations else 0.1
                        
                        # For static images, use a longer duration
                        if frame_duration == 0.0:
                            frame_duration = 5.0  # Show static images for 5 seconds
                        
                        # Wait for next frame
                        current_time = time.time()
                        elapsed = current_time - last_frame_time
                        sleep_time = max(0, frame_duration - elapsed)
                        
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                        
                        last_frame_time = time.time()
                        
                        # Check for loop completion
                        if self.current_sequence.current_frame == 0:
                            loop_count += 1
                            media_loop_count = media_info.get('loop_count', -1)
                            
                            # Check if we should stop looping
                            if media_loop_count > 0 and loop_count >= media_loop_count:
                                self.logger.info(f"Completed {loop_count} loops, moving to next media")
                                self.next_media()
                                loop_count = 0
                    else:
                        # Failed to get frame, skip to the next media to avoid a loop
                        self.logger.warning(f"Failed to get frame for {media_info.get('slug')}, skipping to next media")
                        self.next_media()
                        time.sleep(0.1)
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.001)
                
        except Exception as e:
            self.logger.error(f"Playback loop error: {e}")
        finally:
            self.logger.info("Playback loop stopped")
    
    def start(self) -> None:
        """Start the playback thread."""
        if self.playback_thread and self.playback_thread.is_alive():
            self.logger.warning("Playback thread already running")
            return
        
        self.playback_thread = threading.Thread(target=self.run, name="DisplayPlayer", daemon=True)
        self.playback_thread.start()
        self.logger.info("Playback thread started")
    
    def stop(self) -> None:
        """Stop the playback loop."""
        self.running = False
        
        if self.playback_thread:
            self.playback_thread.join(timeout=2.0)
            if self.playback_thread.is_alive():
                self.logger.warning("Playback thread did not stop gracefully")
        
        self.logger.info("Display player stopped")
    
    def get_status(self) -> Dict:
        """Get current playback status."""
        current_media = None
        if 0 <= self.current_media_index < len(self.media_list):
            current_media = self.media_list[self.current_media_index]
        
        return {
            'running': self.running,
            'paused': self.paused,
            'media_count': len(self.media_list),
            'current_media_index': self.current_media_index,
            'current_media': current_media,
            'frame_count': self.current_sequence.get_frame_count() if self.current_sequence else 0,
            'current_frame': self.current_sequence.current_frame if self.current_sequence else 0
        }
    
    def refresh_media_list(self) -> None:
        """Refresh the media list from disk."""
        self.load_media_index()
        
        # If current media is no longer available, reset
        if (self.current_media_index >= len(self.media_list) or 
            not self.media_list):
            self.current_media_index = 0
            self.current_sequence = None
        
        self.logger.info(f"Refreshed media list: {len(self.media_list)} items")