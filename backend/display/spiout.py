"""SPI display driver for Waveshare 2.4" LCD Module - Simplified."""

import sys
from pathlib import Path
from PIL import Image
from typing import Optional, Union
import spidev
import struct
from contextlib import contextmanager

# Add the Waveshare library path to Python's search path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "waveshare" / "LCD_Module_RPI_code" / "RaspberryPi" / "python" / "lib"))

from config.schema import DisplayConfig
from display.memory_pool import get_frame_buffer_pool, get_spi_chunk_pool
from utils.logger import get_logger

try:
    from LCD_2inch4 import LCD_2inch4
    WAVESHARE_AVAILABLE = True
except ImportError:
    WAVESHARE_AVAILABLE = False
    LCD_2inch4 = None

class ILI9341Driver:
    """Driver for ILI9341 display with memory pool optimization."""

    def __init__(self, config: DisplayConfig):
        """Initialize the display driver."""
        self.config = config
        self.logger = get_logger("display")
        self.disp: Optional[LCD_2inch4] = None
        self.initialized = False
        
        self.logger.info(
            f"Initializing Waveshare 2.4\" LCD driver with pins "
            f"RST={self.config.rst_pin}, DC={self.config.dc_pin}, BL={self.config.bl_pin} "
            f"on SPI bus {self.config.spi_bus}, device {self.config.spi_device}"
        )
    
    @contextmanager
    def _get_frame_buffer(self):
        """Context manager to get and automatically return frame buffer."""
        pool = get_frame_buffer_pool()
        buffer = pool.get_buffer()
        try:
            yield buffer
        finally:
            pool.return_buffer(buffer)

    def init(self) -> None:
        """Initialize the display hardware."""
        if self.initialized:
            return
        
        if not WAVESHARE_AVAILABLE:
            self.logger.error("Waveshare library not available - display disabled")
            return

        self.logger.info("Initializing LCD...")
        try:
            self.disp = LCD_2inch4(
                rst=self.config.rst_pin,
                dc=self.config.dc_pin,
                bl=self.config.bl_pin
            )
            self.disp.Init()
            self.disp.clear()
            # Mark as initialized before controlling backlight to avoid recursion
            self.initialized = True
            # Increase PWM frequency to minimize visible flicker
            try:
                if hasattr(self.disp, "bl_Frequency"):
                    self.disp.bl_Frequency(self.config.backlight_freq)
            except Exception as freq_err:
                self.logger.debug(f"Unable to set backlight PWM frequency: {freq_err}")
            # Set initial brightness from config after initialization
            self.set_backlight(self.config.brightness)
            self.logger.info("LCD initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize LCD: {e}")
            self.initialized = False
            self.disp = None
            raise RuntimeError("Could not initialize Waveshare display") from e

    def display_frame(self, frame_data: bytes) -> None:
        """Display a frame of RGB565 pixel data - optimized with memory pools."""
        if not self.initialized:
            self.init()
        
        if not self.disp:
            self.logger.error("Display screen not initialized, cannot display frame.")
            return

        # Raw framebuffer is always generated as 320x240 RGB565 (little-endian) in landscape.
        base_width  = 320
        base_height = 240
        expected_size = base_width * base_height * 2

        if not frame_data or len(frame_data) != expected_size:
            self.logger.warning(
                f"Frame data has incorrect size. Expected {expected_size} (320x240), got {len(frame_data)}. Skipping frame."
            )
            return

        try:
            # ---------------- Orientation handling ----------------
            rot = self.config.rotation % 360
            if rot == 0:
                madctl = 0x48  # MX | BGR
                win_w, win_h = self.disp.width, self.disp.height
            elif rot == 90:
                madctl = 0x28  # MV | BGR
                win_w, win_h = self.disp.height, self.disp.width
            elif rot == 180:
                madctl = 0x88  # MY | BGR
                win_w, win_h = self.disp.width, self.disp.height
            elif rot == 270:
                # Remove MY to undo the unwanted flip along the long (320-pixel) axis.
                madctl = 0x68  # MX | MV | BGR
                win_w, win_h = self.disp.height, self.disp.width

            # Program MADCTL register
            self.disp.command(0x36)
            self.disp.data(madctl)

            # Set the drawing window to cover the full panel in the chosen orientation
            self.disp.SetWindows(0, 0, win_w, win_h)
            # Switch to data mode
            self.disp.digital_write(self.disp.DC_PIN, True)

            # Send the buffer in 4 kB chunks using memory pool
            spi_pool = get_spi_chunk_pool()
            for offset in range(0, len(frame_data), 4096):
                chunk_list = spi_pool.get_chunk_list(frame_data, offset)
                try:
                    # spi_writebyte expects a list of ints
                    self.disp.spi_writebyte(chunk_list)
                finally:
                    # Return chunk list to pool
                    spi_pool.return_chunk_list(chunk_list)
                
        except Exception as e:
            self.logger.error(f"Frame display failed: {e}")
            return

    def fill_screen(self, color: int = 0x0000) -> None:
        """Fill the screen with a color - optimized with memory pool."""
        if not self.initialized:
            self.init()
            
        if not self.disp:
            return
            
        # Use memory pool for frame buffer
        with self._get_frame_buffer() as frame_data:
            if frame_data is None:
                self.logger.error("Failed to get frame buffer from pool")
                return
            
            color_bytes = struct.pack('>H', color)
            
            # Fill buffer with color
            for i in range(0, len(frame_data), 2):
                frame_data[i:i+2] = color_bytes
            
            # Use existing RGB565 display path - pass copy since buffer will be returned
            self.display_frame(bytes(frame_data))

    def set_backlight(self, level: Union[int, bool]) -> None:
        """Set backlight brightness - hardware PWM only.

        Args:
            level: If bool, True = use configured brightness, False = off.
                   If int, 0-100 percentage duty cycle.
        """
        if not self.initialized:
            self.init()
            
        if not self.disp:
            return

        if type(level) is bool:
            duty_cycle = self.config.brightness if level else 0
        else:
            duty_cycle = max(0, min(100, int(level)))

        self.disp.bl_DutyCycle(duty_cycle)
        self.logger.debug(f"Backlight PWM set to {duty_cycle}%")

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.initialized and self.disp:
            self.disp.module_exit()
            self.initialized = False
            self.logger.info("Waveshare display driver cleaned up") 