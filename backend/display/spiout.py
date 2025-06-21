"""SPI display driver for Waveshare 2.4" LCD Module."""

import sys
from pathlib import Path
from PIL import Image
from typing import Optional, Union
import spidev
import numpy as np

# Add the Waveshare library path to Python's search path
sys.path.append(str(Path(__file__).parent.parent.parent / 'waveshare' / 'LCD_Module_RPI_code' / 'RaspberryPi' / 'python'))

from lib.LCD_2inch4 import LCD_2inch4
from config.schema import DisplayConfig
from utils.logger import get_logger

class ILI9341Driver:
    """A display driver that writes to the Waveshare 2.4" LCD via SPI."""
    
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
    
    def init(self) -> None:
        """Initialize the display hardware."""
        if self.initialized:
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
            # Set initial brightness from config after initialization
            self.set_backlight(self.config.brightness)
            self.logger.info("LCD initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize LCD: {e}")
            self.initialized = False
            raise RuntimeError("Could not initialize Waveshare display") from e

    def display_frame(self, frame_data: bytes) -> None:
        """Display a frame of RGB565 pixel data."""
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
            # Robust conversion: RGB565 big-endian -> RGB888 using NumPy (fast ~2ms)
            pixel_data = np.frombuffer(frame_data, dtype='>u2')  # big-endian uint16
            # Extract RGB components and reshape to 2-D before stacking
            r = (((pixel_data >> 11) & 0x1F).astype(np.uint8) << 3).reshape((base_height, base_width))
            g = (((pixel_data >> 5) & 0x3F).astype(np.uint8) << 2).reshape((base_height, base_width))
            b = (((pixel_data & 0x1F).astype(np.uint8) << 3)).reshape((base_height, base_width))
            rgb_array = np.dstack((r, g, b))
            image = Image.fromarray(rgb_array, 'RGB')

            # Apply rotation from config (values: 0, 90, 180, 270). PIL rotates CCW.
            rotation = self.config.rotation % 360
            if rotation:
                image = image.rotate(rotation, expand=True)

            self.disp.ShowImage(image)
        except Exception as e:
            self.logger.error(f"Failed to display frame: {e}")

    def fill_screen(self, color: int = 0x0000) -> None:
        """Fill the screen with a color."""
        if not self.initialized:
            self.init()
            
        if self.disp:
            r = ((color >> 11) & 0x1F) << 3
            g = ((color >> 5) & 0x3F) << 2
            b = (color & 0x1F) << 3
            
            # Create a 320x240 image to match the config
            image = Image.new('RGB', (320, 240), (r, g, b))
            self.disp.ShowImage(image)

    def set_backlight(self, level: Union[int, bool]) -> None:
        """Set backlight brightness.

        Args:
            level: If bool, True = use configured brightness, False = off.
                   If int, 0-100 percentage duty cycle.
        """
        if not self.initialized:
            self.init()
            
        if not self.disp:
            return

        # Distinguish between real bools and ints (since bool is a subclass of int)
        if type(level) is bool:
            duty_cycle = self.config.brightness if level else 0
        else:
            duty_cycle = max(0, min(100, int(level)))

        self.disp.bl_DutyCycle(duty_cycle)
        self.logger.debug(f"Backlight set to {duty_cycle}%")

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.initialized and self.disp:
            self.disp.module_exit()
            self.initialized = False
            self.logger.info("Waveshare display driver cleaned up") 