"""Framebuffer display driver using Pygame."""

import os
import pygame
import numpy as np
from typing import Optional
import time

try:
    import RPi.GPIO as GPIO
    IS_RPI = True
except (ImportError, RuntimeError):
    IS_RPI = False

from config.schema import DisplayConfig
from utils.logger import get_logger

class ILI9341Driver:
    """A display driver that writes to the system framebuffer using Pygame."""
    
    def __init__(self, config: DisplayConfig):
        """Initialize the Pygame display driver."""
        self.config = config
        self.logger = get_logger("display")
        self.screen: Optional[pygame.Surface] = None
        self.initialized = False
        
        if IS_RPI:
            self._setup_gpio()

        # Point to the primary framebuffer
        os.putenv('SDL_FBDEV', '/dev/fb0')
        os.putenv('SDL_VIDEODRIVER', 'fbcon')
        
        self.logger.info(f"Initializing framebuffer driver for /dev/fb0")
    
    def _setup_gpio(self):
        """Set up GPIO pins for display control."""
        self.logger.info(f"Setting up GPIO: DC={self.config.dc_pin}, RST={self.config.rst_pin}")
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.config.dc_pin, GPIO.OUT)
        GPIO.setup(self.config.rst_pin, GPIO.OUT)
        
    def _reset_display(self):
        """Perform a hardware reset of the display."""
        if not IS_RPI:
            self.logger.warning("Not on a Raspberry Pi, skipping hardware reset.")
            return
            
        self.logger.info("Performing hardware reset...")
        GPIO.output(self.config.rst_pin, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(self.config.rst_pin, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.config.rst_pin, GPIO.HIGH)
        time.sleep(0.1)

    def init(self) -> None:
        """Initialize the Pygame display."""
        if self.initialized:
            return
        
        self._reset_display()

        self.logger.info("Initializing Pygame for framebuffer...")
        try:
            pygame.init()
            pygame.mouse.set_visible(False)
            
            # Use display dimensions from config
            self.screen = pygame.display.set_mode(
                (self.config.width, self.config.height), 
                pygame.NOFRAME
            )
            
            self.initialized = True
            self.logger.info("Pygame framebuffer initialized successfully")
        except pygame.error as e:
            self.logger.error(f"Failed to initialize Pygame framebuffer: {e}")
            self.initialized = False
            # Exit if display cannot be initialized, as it's critical
            raise RuntimeError("Could not initialize framebuffer display") from e

    def display_frame(self, frame_data: bytes) -> None:
        """Display a frame of RGB565 pixel data."""
        if not self.initialized:
            self.init()
        
        if not self.screen:
            self.logger.error("Display screen not initialized, cannot display frame.")
            return

        expected_size = self.config.width * self.config.height * 2
        if not frame_data or len(frame_data) != expected_size:
            return

        try:
            # Convert RGB565 bytes to an RGB888 surface that Pygame can display
            # 1. Create a NumPy array from the raw bytes
            frame_array = np.frombuffer(frame_data, dtype=np.uint16)
            
            # 2. Reshape to the screen dimensions
            frame_array = frame_array.reshape((self.config.height, self.config.width))

            # 3. Efficiently convert RGB565 to RGB888 using bitwise operations
            r = ((frame_array >> 11) & 0x1F) << 3
            g = ((frame_array >> 5) & 0x3F) << 2
            b = (frame_array & 0x1F) << 3
            
            # 4. Stack the channels to create a 3D RGB888 array
            rgb888_array = np.dstack((r, g, b)).astype(np.uint8)
            
            # 5. Create a Pygame surface from the RGB888 array (no memory copy)
            surface = pygame.surfarray.make_surface(rgb888_array)
            
            # 6. Blit the surface to the screen and update the display
            self.screen.blit(surface, (0, 0))
            pygame.display.update()
            
        except Exception as e:
            self.logger.error(f"Failed to display frame: {e}")

    def fill_screen(self, color: int = 0x0000) -> None:
        """Fill the screen with a color (not implemented for fbcp)."""
        # This is less relevant when using fbcp, but can be used for blanking.
        if self.screen:
            # Convert RGB565 to RGB888 for Pygame
            r = ((color >> 11) & 0x1F) << 3
            g = ((color >> 5) & 0x3F) << 2
            b = (color & 0x1F) << 3
            self.screen.fill((r, g, b))
            pygame.display.update()

    def set_backlight(self, enabled: bool) -> None:
        """Control backlight (not implemented, fbcp handles this)."""
        # fbcp-ili9341 handles backlight control via its own configuration
        self.logger.debug("Backlight control is handled by the fbcp service.")
        pass

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.initialized:
            pygame.quit()
            if IS_RPI:
                GPIO.cleanup([self.config.dc_pin, self.config.rst_pin])
            self.initialized = False
            self.logger.info("Pygame display driver cleaned up") 