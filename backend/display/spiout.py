"""SPI display driver for Waveshare 2.4" LCD Hat."""

import sys
import time
from pathlib import Path
from PIL import Image
from typing import Optional

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
        
        self.logger.info("Initializing Waveshare 2.4\" LCD driver")
    
    def init(self) -> None:
        """Initialize the display hardware."""
        if self.initialized:
            return
        
        self.logger.info("Initializing LCD...")
        try:
            self.disp = LCD_2inch4()
            self.disp.Init()
            self.disp.clear()
            self.initialized = True
            self.logger.info("LCD initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize LCD: {e}")
            self.initialized = False
            # Exit if display cannot be initialized, as it's critical
            raise RuntimeError("Could not initialize Waveshare display") from e

    def display_frame(self, frame_data: bytes) -> None:
        """Display a frame of RGB565 pixel data."""
        if not self.initialized:
            self.init()
        
        if not self.disp:
            self.logger.error("Display screen not initialized, cannot display frame.")
            return

        expected_size = self.config.width * self.config.height * 2
        if not frame_data or len(frame_data) != expected_size:
            self.logger.warning(f"Frame data has incorrect size. Expected {expected_size}, got {len(frame_data)}. Skipping frame.")
            return

        try:
            # Create a PIL Image from the raw RGB565 bytes
            image = Image.frombytes('RGB', (self.config.width, self.config.height), frame_data, 'raw', 'RGB;16')
            
            # Display the image
            self.disp.ShowImage(image)
            
        except Exception as e:
            self.logger.error(f"Failed to display frame: {e}")

    def fill_screen(self, color: int = 0x0000) -> None:
        """Fill the screen with a color."""
        if not self.initialized:
            self.init()
            
        if self.disp:
            # The library's clear function doesn't take a color, it clears to black.
            # We can create a single-color image to simulate a fill.
            r = ((color >> 11) & 0x1F) << 3
            g = ((color >> 5) & 0x3F) << 2
            b = (color & 0x1F) << 3
            
            image = Image.new('RGB', (self.config.width, self.config.height), (r, g, b))
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