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
from utils.media_index import media_index


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
        self.media_list_changed = False  # Flag to interrupt playback when media list changes
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
            self.all_media = media_index.list_media()
            loop_order = media_index.list_loop()

            # Create mapping of slugs to media items
            slug_to_media = {m.get('slug'): m for m in self.all_media}
            
            # Build loop media list from loop order
            self.loop_media = [slug_to_media[s] for s in loop_order if s in slug_to_media]
            
            # Reset current index if needed
            if self.current_media_index >= len(self.loop_media):
                self.current_media_index = 0
            
            # Set active media if specified
            active_slug = media_index.get_active()
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
            
            # Use cached loop data for consistency
            self.current_media_index = (self.current_media_index + 1) % len(self.loop_media)
            
            # Load the new sequence
            if self.load_current_sequence():
                # Update active media in index
                new_slug = self.loop_media[self.current_media_index].get('slug')
                if new_slug:
                    media_index.set_active(new_slug)
                    
                    media_name = self.loop_media[self.current_media_index].get('original_filename', 'Unknown')
                    self.logger.info(f"Switched to next media: {media_name}")
            else:
                self.logger.error("Failed to load next media sequence")
    
    def previous_media(self) -> None:
        """Switch to previous media."""
        with self.lock:
            if len(self.loop_media) <= 1:
                return
            
            # Use cached loop data for consistency  
            self.current_media_index = (self.current_media_index - 1) % len(self.loop_media)
            
            # Load the new sequence
            if self.load_current_sequence():
                # Update active media in index
                new_slug = self.loop_media[self.current_media_index].get('slug')
                if new_slug:
                    media_index.set_active(new_slug)
                    
                    media_name = self.loop_media[self.current_media_index].get('original_filename', 'Unknown')
                    self.logger.info(f"Switched to previous media: {media_name}")
            else:
                self.logger.error("Failed to load previous media sequence")
    
    def set_active_media(self, slug: str) -> bool:
        """Set the active media to the specified slug."""
        with self.lock:
            for i, media in enumerate(self.loop_media):
                if media.get('slug') == slug:
                    self.current_media_index = i
                    self.load_current_sequence()
                    media_index.set_active(slug)
                    
                    media_name = media.get('original_filename', 'Unknown')
                    self.logger.info(f"Set active media: {media_name}")
                    return True
            
            self.logger.warning(f"Media with slug '{slug}' not found in loop")
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
        """Display a message on screen temporarily."""
        try:
            # Create image with message
            image = Image.new('RGB', (self.display_config.width, self.display_config.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Try to load a font, fall back to default if not available
            try:
                font_size = 24
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            except (OSError, IOError):
                try:
                    # Try default PIL font
                    font = ImageFont.load_default()
                except:
                    # If all else fails, use basic drawing without font
                    font = None
            
            if font:
                # Get text dimensions
                bbox = draw.textbbox((0, 0), message, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Center the text
                x = (self.display_config.width - text_width) // 2
                y = (self.display_config.height - text_height) // 2
                
                # Convert color to RGB
                if isinstance(color, int):
                    # Convert RGB565 to RGB888
                    r = (color >> 11) << 3
                    g = ((color >> 5) & 0x3F) << 2
                    b = (color & 0x1F) << 3
                    rgb_color = (r, g, b)
                else:
                    rgb_color = color
                
                # Draw text
                draw.text((x, y), message, fill=rgb_color, font=font)
            else:
                # Fallback: draw simple text
                # This is very basic - just put text roughly in center
                x = self.display_config.width // 4
                y = self.display_config.height // 2
                draw.text((x, y), message, fill=(255, 255, 255))
            
            # Convert to RGB565 format using FrameDecoder
            decoder = FrameDecoder(self.display_config.width, self.display_config.height)
            
            # Save image to bytes buffer
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            
            # Convert to RGB565 frame data
            frame_data = decoder.decode_image_bytes(buffer.getvalue())
            buffer.close()
            
            if frame_data:
                self.display_driver.display_frame(frame_data)
                
                # Sleep for specified duration if > 0
                if duration > 0:
                    time.sleep(duration)
            else:
                self.logger.error("Failed to convert message image to frame data")
            
        except Exception as e:
            self.logger.error(f"Failed to show message: {e}")
    
    def show_no_media_message(self) -> None:
        """Show a message when no media is available."""
        self.show_message("No media loaded", duration=0, color=0x07E0)  # Green text
    
    def run(self) -> None:
        """Main playback loop."""
        self.logger.info("Starting playback loop")
        
        while self.running:
            try:
                # Check if we have media to play
                if not self.loop_media:
                    self.load_media_index()
                    if not self.loop_media:
                        self.show_no_media_message()
                        time.sleep(1)
                        continue
                
                # Load current sequence if needed
                if not self.current_sequence:
                    if not self.load_current_sequence():
                        # Failed to load, try next media or wait
                        if len(self.loop_media) > 1:
                            self.next_media()
                        else:
                            time.sleep(1)
                        continue
                
                # Play current media sequence
                sequence_loops = 0
                infinite_loop = (self.loop_count <= 0)  # -1 or 0 means infinite
                
                # Keep playing until we hit the loop limit or it's infinite
                while self.running:
                    frame_count = self.current_sequence.get_frame_count()
                    
                    # Play all frames in the sequence
                    for frame_idx in range(frame_count):
                        if not self.running:
                            break
                        
                        # Handle pause
                        while self.paused and self.running:
                            time.sleep(0.1)
                        
                        if not self.running:
                            break
                        
                        # Check if media list changed (new media added)
                        with self.lock:
                            if self.media_list_changed:
                                self.media_list_changed = False
                                self.logger.info("Media list changed - interrupting playback to cycle through items")
                                # Break out of both loops to restart with new media list
                                break
                        
                        # Get frame data and duration
                        frame_data = self.current_sequence.get_frame_data(frame_idx)
                        frame_duration = self.current_sequence.get_frame_duration(frame_idx)
                        
                        if frame_data is None:
                            self.logger.error(f"Failed to get frame {frame_idx}")
                            break
                        
                        # Display frame
                        start_time = time.time()
                        self.display_driver.display_frame(frame_data)
                        
                        # Calculate sleep time to maintain frame rate
                        display_time = time.time() - start_time
                        target_duration = frame_duration if frame_duration > 0 else (1.0 / self.frame_rate)
                        sleep_time = max(0, target_duration - display_time)
                        
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                    
                    # Check if we broke out due to media list change
                    with self.lock:
                        if self.media_list_changed:
                            self.media_list_changed = False
                            self.logger.info("Breaking out of sequence loop due to media list change")
                            break
                    
                    # Completed one sequence loop
                    sequence_loops += 1
                    
                    # Check if we should stop looping this sequence
                    if not infinite_loop and sequence_loops >= self.loop_count:
                        break
                    
                    # If not running anymore, break
                    if not self.running:
                        break
                
                # Move to next media in the loop if we have multiple items
                if len(self.loop_media) > 1:
                    self.next_media()
                    # Reset current_sequence to None so it reloads the next media
                    self.current_sequence = None
                else:
                    # Check if media list changed - if so, reload before deciding what to do
                    with self.lock:
                        if self.media_list_changed:
                            self.media_list_changed = False
                            self.logger.info("Reloading media index due to pending changes")
                            self.load_media_index()
                            
                            # Now check again with fresh data
                            if len(self.loop_media) > 1:
                                self.logger.info("Found multiple items after reload - starting multi-item cycle")
                                self.next_media()
                                self.current_sequence = None
                                continue
                    
                    # Single media item - if infinite loop, continue playing
                    if infinite_loop:
                        # Just continue the outer while loop to replay
                        continue
                    else:
                        # Finite loops - we're done, just wait
                        self.logger.info("Finished playing all loops, waiting...")
                        time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error in playback loop: {e}")
                time.sleep(1)
        
        self.logger.info("Playback loop ended")
    
    def start(self) -> None:
        """Start the display player."""
        if not self.running:
            self.running = True
            self.playback_thread = threading.Thread(target=self.run, daemon=True)
            self.playback_thread.start()
            self.logger.info("Display player started")
    
    def stop(self) -> None:
        """Stop the display player."""
        if self.running:
            self.running = False
            if self.playback_thread:
                self.playback_thread.join(timeout=5)
                if self.playback_thread.is_alive():
                    self.logger.warning("Playback thread did not stop gracefully")
            self.logger.info("Display player stopped")
    
    def get_status(self) -> Dict:
        """Get current playback status."""
        current_media = None
        if 0 <= self.current_media_index < len(self.loop_media):
            current_media = self.loop_media[self.current_media_index].get('slug')
        
        return {
            "is_playing": self.running and not self.paused,
            "current_media": current_media,
            "loop_index": self.current_media_index,
            "total_media": len(self.loop_media),
            "frame_rate": self.frame_rate
        }
    
    def refresh_media_list(self) -> None:
        """Refresh the media list from index."""
        self.logger.info("Refreshing media list")
        
        # Store old state to detect changes
        old_loop_count = len(self.loop_media)
        old_loop_slugs = [m.get('slug') for m in self.loop_media]
        
        self.load_media_index()
        
        # If current media is no longer available, reset
        if self.current_media_index >= len(self.loop_media):
            self.current_media_index = 0
            self.current_sequence = None
        
        # Check if loop changed (count or content)
        new_loop_count = len(self.loop_media)
        new_loop_slugs = [m.get('slug') for m in self.loop_media]
        
        loop_changed = (new_loop_count != old_loop_count or old_loop_slugs != new_loop_slugs)
        
        if loop_changed:
            self.logger.info(f"Media loop changed: {old_loop_count} -> {new_loop_count} items")
            if old_loop_slugs != new_loop_slugs:
                self.logger.info("Loop content changed (different media items)")
            with self.lock:
                self.media_list_changed = True