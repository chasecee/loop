"""Display playback engine for LOOP."""

import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont
import io

from config.schema import DisplayConfig, MediaConfig
from display.framebuf import FrameSequence, FrameDecoder, FrameBuffer
from display.spiout import ILI9341Driver
from utils.logger import get_logger
import utils.media_index as mi


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
        self.all_media: List[Dict] = []  # All available media
        self.loop_media: List[Dict] = []  # Only media in active loop
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
        
        self.logger.info(f"Display player initialized with {len(self.loop_media)} media items")
    
    def load_media_index(self) -> None:
        """Load the media index from file."""
        try:
            # Load all media and loop order
            self.all_media = mi.list_media()
            loop_order = mi.list_loop()

            # Create mapping of slugs to media items
            slug_to_media = {m.get('slug'): m for m in self.all_media}
            
            # Build loop media list from loop order
            self.loop_media = [slug_to_media[s] for s in loop_order if s in slug_to_media]
            
            # Reset current index if needed
            if self.current_media_index >= len(self.loop_media):
                self.current_media_index = 0
            
            # Set active media if specified
            active_slug = mi.get_active()
            if active_slug:
                for i, media in enumerate(self.loop_media):
                    if media.get('slug') == active_slug:
                        self.current_media_index = i
                        break
            
            self.logger.info(f"Loaded {len(self.all_media)} total media items, {len(self.loop_media)} in loop")
        except Exception as e:
            self.logger.error(f"Failed to load media index: {e}")
            self.all_media = []
            self.loop_media = []
    
    def get_current_media_slug(self) -> Optional[str]:
        """Get the slug of the currently selected media."""
        if 0 <= self.current_media_index < len(self.loop_media):
            return self.loop_media[self.current_media_index].get('slug')
        return None
    
    def load_current_sequence(self) -> bool:
        """Load the current media sequence."""
        if not self.loop_media or not (0 <= self.current_media_index < len(self.loop_media)):
            self.logger.warning("No media available to load")
            return False
        
        media_info = self.loop_media[self.current_media_index]
        media_slug = media_info.get('slug')
        
        if not media_slug:
            self.logger.error("Media has no slug")
            return False
        
        frames_dir = self.media_dir / media_slug / "frames"
        
        if not frames_dir.exists():
            self.logger.error(f"Frames directory not found: {frames_dir}")
            return False
        
        try:
            # Get frames and durations from media info
            frames = media_info.get('frames', [])
            durations = media_info.get('durations', [])
            
            if not frames:
                self.logger.error("No frames found in media info")
                return False
            
            # Create frame sequence with frames and durations
            self.current_sequence = FrameSequence(
                frames_dir,
                frames,
                durations
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
            if len(self.loop_media) <= 1:
                return
            
            # Get current loop order
            loop_slugs = mi.list_loop()
            if not loop_slugs:
                return  # No items in loop
            
            # Find current position in loop
            current_slug = self.get_current_media_slug()
            try:
                current_loop_idx = loop_slugs.index(current_slug) if current_slug else -1
            except ValueError:
                current_loop_idx = -1
            
            # Move to next item in loop
            next_loop_idx = (current_loop_idx + 1) % len(loop_slugs)
            next_slug = loop_slugs[next_loop_idx]
            
            # Find this item in media list
            for i, media in enumerate(self.loop_media):
                if media.get('slug') == next_slug:
                    self.current_media_index = i
                    self.load_current_sequence()
                    
                    # Update active media in index
                    mi.set_active(next_slug)
                    
                    media_name = self.loop_media[i].get('original_filename', 'Unknown')
                    self.logger.info(f"Switched to next media: {media_name}")
                    break
    
    def previous_media(self) -> None:
        """Switch to previous media."""
        with self.lock:
            if len(self.loop_media) <= 1:
                return
            
            # Get current loop order
            loop_slugs = mi.list_loop()
            if not loop_slugs:
                return  # No items in loop
            
            # Find current position in loop
            current_slug = self.get_current_media_slug()
            try:
                current_loop_idx = loop_slugs.index(current_slug) if current_slug else -1
            except ValueError:
                current_loop_idx = -1
            
            # Move to previous item in loop
            prev_loop_idx = (current_loop_idx - 1) % len(loop_slugs)
            prev_slug = loop_slugs[prev_loop_idx]
            
            # Find this item in media list
            for i, media in enumerate(self.loop_media):
                if media.get('slug') == prev_slug:
                    self.current_media_index = i
                    self.load_current_sequence()
                    
                    # Update active media in index
                    mi.set_active(prev_slug)
                    
                    media_name = self.loop_media[i].get('original_filename', 'Unknown')
                    self.logger.info(f"Switched to previous media: {media_name}")
                    break
    
    def set_active_media(self, slug: str) -> bool:
        """Set active media by slug."""
        with self.lock:
            for i, media in enumerate(self.loop_media):
                if media.get('slug') == slug:
                    self.current_media_index = i
                    success = self.load_current_sequence()
                    if success:
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
            
            # Calculate text position (center) with proper font handling
            try:
                bbox = draw.textbbox((0, 0), message, font=font)
            except Exception:
                # Fallback for older PIL versions or font issues
                bbox = (0, 0, len(message) * 8, 16)  # Approximate dimensions
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (self.display_config.width - text_width) // 2
            y = (self.display_config.height - text_height) // 2
            
            # Draw text
            draw.text((x, y), message, fill='white', font=font)
            
            # Encode to PNG so FrameDecoder can reopen it, then decode to RGB565
            decoder = FrameDecoder(self.display_config.width, self.display_config.height)
            img = img.convert('RGB')  # Ensure RGB mode
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            frame_data = decoder.decode_image_bytes(buffer.getvalue())
            buffer.close()
            
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
        min_frame_time = 1.0 / self.frame_rate if self.frame_rate > 0 else 0.0
        
        # Performance: cache frequently accessed values
        media_loop_count = self.loop_count if self.loop_count > 0 else 1
        
        try:
            while self.running:
                # Check if we have media to play
                if not self.loop_media:
                    self.show_no_media_message()
                    time.sleep(2)  # Check even less frequently when no media to reduce CPU usage
                    self.load_media_index()  # Refresh to check for new media
                    continue
                
                # Handle pause state
                if self.paused:
                    time.sleep(0.1)  # Reduced sleep time in pause
                    continue
                
                # Get current frame if sequence loaded
                if self.current_sequence:
                    try:
                        frame = self.current_sequence.get_frame()
                        if frame:
                            # Get frame duration for the frame we just displayed
                            # (current_frame was advanced by get_frame(), so we need the previous one)
                            displayed_frame_idx = (self.current_sequence.current_frame - 1) % self.current_sequence.frame_count
                            frame_duration = self.current_sequence.get_frame_duration(displayed_frame_idx)
                            frame_duration = max(frame_duration, min_frame_time)
                            
                            # Calculate sleep time (single time.time() call)
                            current_time = time.time()
                            elapsed = current_time - last_frame_time
                            
                            # Sleep only if needed (non-blocking for fast frames)
                            if elapsed < frame_duration:
                                time.sleep(frame_duration - elapsed)
                                last_frame_time = last_frame_time + frame_duration  # Precise timing
                            else:
                                last_frame_time = current_time  # Catch up timing
                            
                            # Display frame (the expensive operation)
                            self.display_driver.display_frame(frame)
                        else:
                            # Failed to get frame, skip to the next media
                            self.logger.warning(f"Failed to get frame, skipping to next media")
                            self.next_media()
                            last_frame_time = time.time()
                    except Exception as e:
                        self.logger.error(f"Error during frame processing: {e}")
                        # Try to recover by moving to next media
                        self.next_media()
                        last_frame_time = time.time()
                        
                        # Check if we've completed a loop
                        if self.current_sequence.is_complete():
                            loop_count += 1
                            
                            # Move to next media once we've completed the desired loops
                            if loop_count >= media_loop_count:
                                self.logger.info(f"Completed {loop_count} loops, moving to next media")
                                self.next_media()  # This now updates active media
                                loop_count = 0
                                last_frame_time = time.time()  # Reset timing for new media
                    else:
                        # Failed to get frame, skip to the next media
                        self.logger.warning(f"Failed to get frame, skipping to next media")
                        self.next_media()
                        last_frame_time = time.time()
                else:
                    # No sequence loaded, try to load current media
                    if not self.load_current_sequence():
                        self.logger.warning("Failed to load current sequence")
                        time.sleep(0.1)  # Brief pause before retry
                        # If we can't load the sequence, try moving to next media
                        self.next_media()
                        
        except Exception as e:
            self.logger.error(f"Playback loop error: {str(e)}")
            self.running = False
        
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
        if 0 <= self.current_media_index < len(self.loop_media):
            current_media = self.loop_media[self.current_media_index]
        
        return {
            'running': self.running,
            'paused': self.paused,
            'media_count': len(self.loop_media),
            'current_media_index': self.current_media_index,
            'current_media': current_media,
            'frame_count': self.current_sequence.get_frame_count() if self.current_sequence else 0,
            'current_frame': self.current_sequence.current_frame if self.current_sequence else 0
        }
    
    def refresh_media_list(self) -> None:
        """Refresh the media list from disk."""
        self.load_media_index()
        
        # If current media is no longer available, reset
        if (self.current_media_index >= len(self.loop_media) or 
            not self.loop_media):
            self.current_media_index = 0
            self.current_sequence = None
        
        self.logger.info(f"Refreshed media list: {len(self.loop_media)} items")