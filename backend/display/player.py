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
        
        # Media management - SIMPLIFIED: no more caching
        self.media_dir = Path("media/processed")
        self.current_sequence: Optional[FrameSequence] = None
        
        # Playback control
        self.running = False
        self.paused = False
        self.frame_rate = display_config.framerate
        self.loop_count = media_config.loop_count
        self.loop_mode = "all"  # "all" or "one"
        
        # Threading
        self.playback_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # Status display
        self.frame_buffer = FrameBuffer(display_config.width, display_config.height)
        
        self.logger.info("Display player initialized (simplified architecture)")
    
    def get_current_loop_media(self) -> List[Dict]:
        """Get current loop media from authoritative source."""
        loop_slugs = media_index.list_loop()
        media_dict = media_index.get_media_dict()
        return [media_dict[slug] for slug in loop_slugs if slug in media_dict]
    
    def get_current_media_index(self) -> int:
        """Get index of currently active media in loop."""
        active_slug = media_index.get_active()
        if not active_slug:
            return 0
        
        loop_slugs = media_index.list_loop()
        try:
            return loop_slugs.index(active_slug)
        except ValueError:
            return 0
    
    def get_current_media_slug(self) -> Optional[str]:
        """Get the slug of the currently active media."""
        return media_index.get_active()
    
    def load_current_sequence(self) -> bool:
        """Load the current media sequence."""
        loop_media = self.get_current_loop_media()
        current_index = self.get_current_media_index()
        
        if not loop_media or current_index >= len(loop_media):
            self.logger.warning("No media available to load")
            return False
        
        media_info = loop_media[current_index]
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
            loop_slugs = media_index.list_loop()
            
            if len(loop_slugs) <= 1:
                return
            
            current_slug = media_index.get_active()
            try:
                current_index = loop_slugs.index(current_slug) if current_slug else 0
            except ValueError:
                current_index = 0
            
            # Move to next item in loop
            next_index = (current_index + 1) % len(loop_slugs)
            next_slug = loop_slugs[next_index]
            
            # Set as active and reload sequence
            media_index.set_active(next_slug)
            if self.load_current_sequence():
                media_dict = media_index.get_media_dict()
                media_name = media_dict.get(next_slug, {}).get('original_filename', 'Unknown')
                self.logger.info(f"Switched to next media: {media_name}")
            else:
                self.logger.error("Failed to load next media sequence")
    
    def previous_media(self) -> None:
        """Switch to previous media."""
        with self.lock:
            loop_slugs = media_index.list_loop()
            
            if len(loop_slugs) <= 1:
                return
            
            current_slug = media_index.get_active()
            try:
                current_index = loop_slugs.index(current_slug) if current_slug else 0
            except ValueError:
                current_index = 0
            
            # Move to previous item in loop
            prev_index = (current_index - 1) % len(loop_slugs)
            prev_slug = loop_slugs[prev_index]
            
            # Set as active and reload sequence
            media_index.set_active(prev_slug)
            if self.load_current_sequence():
                media_dict = media_index.get_media_dict()
                media_name = media_dict.get(prev_slug, {}).get('original_filename', 'Unknown')
                self.logger.info(f"Switched to previous media: {media_name}")
            else:
                self.logger.error("Failed to load previous media sequence")
    
    def set_active_media(self, slug: str) -> bool:
        """Set the active media to the specified slug."""
        with self.lock:
            # Check if slug exists in media
            media_dict = media_index.get_media_dict()
            if slug not in media_dict:
                self.logger.warning(f"Media with slug '{slug}' not found")
                return False
            
            # Set as active and reload sequence
            media_index.set_active(slug)
            if self.load_current_sequence():
                media_name = media_dict.get(slug, {}).get('original_filename', 'Unknown')
                self.logger.info(f"Set active media: {media_name}")
                return True
            else:
                self.logger.error(f"Failed to load sequence for media: {slug}")
                return False
    
    def toggle_pause(self) -> None:
        """Toggle playback pause state."""
        with self.lock:
            self.paused = not self.paused
            self.logger.info(f"Playback {'paused' if self.paused else 'resumed'}")
    
    def is_paused(self) -> bool:
        """Check if playback is paused."""
        return self.paused
    
    def toggle_loop_mode(self) -> str:
        """Toggle between 'all' and 'one' loop modes."""
        with self.lock:
            self.loop_mode = "one" if self.loop_mode == "all" else "all"
            self.logger.info(f"Loop mode changed to: {self.loop_mode}")
            return self.loop_mode
    
    def get_loop_mode(self) -> str:
        """Get current loop mode."""
        return self.loop_mode
    
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
        """Main playback loop - SIMPLIFIED."""
        self.logger.info("Starting simplified playback loop")
        
        while self.running:
            try:
                # Get current loop state fresh every cycle
                loop_slugs = media_index.list_loop()
                
                # Check if we have media to play
                if not loop_slugs:
                    self.show_no_media_message()
                    time.sleep(1)
                    continue
                
                # Load current sequence if needed
                if not self.current_sequence:
                    if not self.load_current_sequence():
                        # Failed to load, try next media or wait
                        if len(loop_slugs) > 1:
                            self.next_media()
                        else:
                            time.sleep(1)
                        continue
                
                # Play current media sequence
                # For loop mode behavior, we only play the media once, then decide what to do next
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
                
                # Handle loop mode behavior
                current_loop_slugs = media_index.list_loop()  # Re-check in case it changed
                if self.loop_mode == "one":
                    # Loop one mode - keep playing same media (just continue to reload same sequence)
                    continue
                elif len(current_loop_slugs) > 1:
                    # Loop all mode with multiple items - move to next
                    self.next_media()
                    # Clear current sequence to force reload of next media
                    self.current_sequence = None
                else:
                    # Single media item in loop all mode - just replay it
                    continue
                
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
        current_media = media_index.get_active()
        loop_slugs = media_index.list_loop()
        current_index = self.get_current_media_index()
        
        return {
            "is_playing": self.running and not self.paused,
            "current_media": current_media,
            "loop_index": current_index,
            "total_media": len(loop_slugs),
            "frame_rate": self.frame_rate,
            "loop_mode": self.loop_mode
        }
    
    def refresh_media_list(self) -> None:
        """Refresh the media list - now just clears current sequence to force reload."""
        self.logger.info("Refreshing media list (clearing current sequence)")
        with self.lock:
            # Simply clear the current sequence to force reload on next cycle
            self.current_sequence = None