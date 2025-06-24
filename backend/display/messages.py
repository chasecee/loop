"""Display messaging system for LOOP."""

import io
import time
import threading
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from config.schema import DisplayConfig
from display.framebuf import FrameDecoder
from utils.logger import get_logger


class MessageDisplay:
    """Handles all text messages and status displays for the screen."""
    
    def __init__(self, display_driver, display_config: DisplayConfig):
        """Initialize the message display system."""
        self.display_driver = display_driver
        self.config = display_config
        self.logger = get_logger("messages")
        
        # Cache for fonts to avoid reloading
        self._font_cache: Dict[Tuple[str, int], Any] = {}
        
        # Frame decoder for converting PIL images to display format
        self.decoder = FrameDecoder(self.config.width, self.config.height)
        
        # Message queue and display thread
        self._message_queue = []
        self._display_lock = threading.Lock()
        self._current_message = None
        self._message_end_time = 0
        
        self.logger.info("Message display system initialized")
    
    def _get_font(self, size: int, bold: bool = False) -> Any:
        """Get a font with caching. Falls back to default if system fonts unavailable."""
        cache_key = (f"{'bold' if bold else 'regular'}", size)
        
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]
        
        font = None
        
        # Try system fonts (works on Pi with proper fonts installed)
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Helvetica.ttc",  # macOS fallback
        ]
        
        for font_path in font_paths:
            try:
                if Path(font_path).exists():
                    font = ImageFont.truetype(font_path, size)
                    break
            except (OSError, IOError):
                continue
        
        # Fallback to default font
        if font is None:
            try:
                font = ImageFont.load_default()
                self.logger.debug(f"Using default font for size {size}")
            except Exception:
                font = None
        
        self._font_cache[cache_key] = font
        return font
    
    def _create_text_image(self, title: str, subtitle: str = "", 
                          bg_color: Tuple[int, int, int] = (0, 0, 0),
                          text_color: Tuple[int, int, int] = (255, 255, 255),
                          title_size: int = 24, subtitle_size: int = 16) -> Optional[bytes]:
        """Create an image with text and convert to display format."""
        try:
            # Create image with black background
            image = Image.new('RGB', (self.config.width, self.config.height), bg_color)
            draw = ImageDraw.Draw(image)
            
            # Get fonts
            title_font = self._get_font(title_size, bold=True)
            subtitle_font = self._get_font(subtitle_size, bold=False)
            
            # Calculate text positioning
            y_offset = 60  # Start 60px from top
            
            # Draw title (centered)
            if title and title_font:
                bbox = draw.textbbox((0, 0), title, font=title_font)
                title_width = bbox[2] - bbox[0]
                title_height = bbox[3] - bbox[1]
                title_x = (self.config.width - title_width) // 2
                draw.text((title_x, y_offset), title, fill=text_color, font=title_font)
                y_offset += title_height + 20
            
            # Draw subtitle (centered)
            if subtitle and subtitle_font:
                bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
                subtitle_width = bbox[2] - bbox[0]
                subtitle_x = (self.config.width - subtitle_width) // 2
                draw.text((subtitle_x, y_offset), subtitle, fill=text_color, font=subtitle_font)
            
            # Convert to display format
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            frame_data = self.decoder.decode_image_bytes(buffer.getvalue())
            buffer.close()
            
            return frame_data
            
        except Exception as e:
            self.logger.error(f"Failed to create text image: {e}")
            return None
    
    def show_message(self, title: str, subtitle: str = "", duration: float = 3.0,
                    bg_color: Tuple[int, int, int] = (0, 0, 0),
                    text_color: Tuple[int, int, int] = (255, 255, 255)) -> None:
        """Show a text message on the display."""
        try:
            frame_data = self._create_text_image(title, subtitle, bg_color, text_color)
            if frame_data:
                self.display_driver.display_frame(frame_data)
                if duration > 0:
                    time.sleep(duration)
            else:
                # Fallback to solid color if text rendering fails
                self.display_driver.fill_screen(0x07E0)  # Green
                if duration > 0:
                    time.sleep(duration)
        except Exception as e:
            self.logger.error(f"Failed to show message '{title}': {e}")
    
    def show_boot_message(self, version: str = "1.0") -> None:
        """Show boot message."""
        self.show_message(
            title="LOOP",
            subtitle=f"v{version}",
            duration=2.0,
            bg_color=(0, 0, 0),
            text_color=(0, 255, 0)  # Bright green text
        )
    
    def show_no_media_message(self) -> None:
        """Show no media available message."""
        self.show_message(
            title="No Media",
            subtitle="Upload files via web interface",
            duration=0,  # Persistent
            bg_color=(0, 0, 0),
            text_color=(255, 255, 0)  # Yellow text
        )
    
    def show_error_message(self, error: str) -> None:
        """Show an error message."""
        self.show_message(
            title="Error",
            subtitle=error,
            duration=5.0,
            bg_color=(0, 0, 0),
            text_color=(255, 0, 0)  # Red text
        )
    
    def show_processing_message(self, filename: str = "") -> None:
        """Show processing message."""
        subtitle = f"Processing {filename}" if filename else "Processing media..."
        self.show_message(
            title="Processing",
            subtitle=subtitle,
            duration=0,  # Persistent until replaced
            bg_color=(0, 0, 0),
            text_color=(0, 150, 255)  # Blue text
        )
    
    def show_upload_message(self, count: int = 1) -> None:
        """Show upload in progress message."""
        subtitle = f"Uploading {count} file{'s' if count != 1 else ''}..."
        self.show_message(
            title="Upload",
            subtitle=subtitle,
            duration=0,  # Persistent until replaced
            bg_color=(0, 0, 0),
            text_color=(255, 165, 0)  # Orange text
        )
    
    def show_progress_bar(self, title: str, subtitle: str, progress: float) -> None:
        """Display a progress bar with title and subtitle."""
        try:
            # Create image
            image = Image.new('RGB', (self.config.width, self.config.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Get fonts
            title_font = self._get_font(20, bold=True)
            subtitle_font = self._get_font(14, bold=False)
            
            y_pos = 40
            
            # Draw title
            if title and title_font:
                bbox = draw.textbbox((0, 0), title, font=title_font)
                title_width = bbox[2] - bbox[0]
                title_x = (self.config.width - title_width) // 2
                draw.text((title_x, y_pos), title, fill=(255, 255, 255), font=title_font)
                y_pos += 35
            
            # Draw subtitle  
            if subtitle and subtitle_font:
                bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
                subtitle_width = bbox[2] - bbox[0]
                subtitle_x = (self.config.width - subtitle_width) // 2
                draw.text((subtitle_x, y_pos), subtitle, fill=(200, 200, 200), font=subtitle_font)
                y_pos += 30
            
            # Draw progress bar
            bar_width = 180
            bar_height = 20
            bar_x = (self.config.width - bar_width) // 2
            bar_y = y_pos + 10
            
            # Progress bar background
            draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], 
                         outline=(100, 100, 100), fill=(30, 30, 30))
            
            # Progress bar fill
            fill_width = int((progress / 100.0) * bar_width)
            if fill_width > 0:
                # Use configured progress color or default blue
                color = getattr(self.config, 'progress_color', 0x07FF)  # Default cyan
                r = (color >> 11) << 3
                g = ((color >> 5) & 0x3F) << 2  
                b = (color & 0x1F) << 3
                draw.rectangle([bar_x, bar_y, bar_x + fill_width, bar_y + bar_height], 
                             fill=(r, g, b))
            
            # Progress percentage
            progress_text = f"{int(progress)}%"
            if title_font:
                bbox = draw.textbbox((0, 0), progress_text, font=title_font)
                progress_width = bbox[2] - bbox[0]
                progress_x = (self.config.width - progress_width) // 2
                draw.text((progress_x, bar_y + 35), progress_text, fill=(255, 255, 255), font=title_font)
            
            # Convert to RGB565 format and display
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            frame_data = self.decoder.decode_image_bytes(buffer.getvalue())
            buffer.close()
            
            if frame_data:
                self.display_driver.display_frame(frame_data)
            
        except Exception as e:
            self.logger.error(f"Failed to show progress bar: {e}")
    
    def clear_screen(self, color: int = 0x0000) -> None:
        """Clear the screen with a solid color."""
        self.display_driver.fill_screen(color)


# Global message display instance (set by player when initialized)
_message_display: Optional[MessageDisplay] = None


def set_message_display(message_display: MessageDisplay) -> None:
    """Set the global message display instance."""
    global _message_display
    _message_display = message_display


def get_message_display() -> Optional[MessageDisplay]:
    """Get the global message display instance."""
    return _message_display


# Convenience functions for easy access from anywhere in the codebase
def show_message(title: str, subtitle: str = "", duration: float = 3.0) -> None:
    """Show a message (convenience function)."""
    if _message_display:
        _message_display.show_message(title, subtitle, duration)


def show_error(error: str) -> None:
    """Show an error message (convenience function)."""
    if _message_display:
        _message_display.show_error_message(error)


def show_processing(filename: str = "") -> None:
    """Show processing message (convenience function)."""
    if _message_display:
        _message_display.show_processing_message(filename)


def show_upload(count: int = 1) -> None:
    """Show upload message (convenience function)."""
    if _message_display:
        _message_display.show_upload_message(count) 