"""SPI display driver for Waveshare 2.4" LCD Module."""

import sys
from pathlib import Path
from PIL import Image
from typing import Optional
import spidev

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
            self.initialized = True
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

        # The frame_data should be for a 320x240 landscape image, which matches our config.
        expected_width = 320
        expected_height = 240
        expected_size = expected_width * expected_height * 2
        
        if not frame_data or len(frame_data) != expected_size:
            self.logger.warning(f"Frame data has incorrect size. Expected {expected_size} (320x240), got {len(frame_data)}. Skipping frame.")
            return

        try:
            # The driver's ShowImage method handles the orientation based on image dimensions.
            # We create a 320x240 image and let the driver handle the rest.
            image = Image.frombytes('RGB', (expected_width, expected_height), frame_data, 'raw', 'RGB;16')
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

    def set_backlight(self, enabled: bool) -> None:
        """Control backlight."""
        if not self.initialized:
            self.init()
            
        if self.disp:
            duty_cycle = 100 if enabled else 0
            self.disp.bl_DutyCycle(duty_cycle)
            self.logger.debug(f"Backlight set to {'on' if enabled else 'off'}")

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.initialized and self.disp:
            self.disp.module_exit()
            self.initialized = False
            self.logger.info("Waveshare display driver cleaned up") 