#!/usr/bin/env python3
"""Boot Display - Set screen to black during system startup."""

import sys
import time
import logging
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from display.ili9341_driver import ILI9341Display
    from config.schema import DisplayConfig
except ImportError as e:
    import logging
    logging.error(f"Failed to import display modules: {e}")
    sys.exit(1)

def setup_logging():
    """Setup basic logging for boot display."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - BOOT-DISPLAY - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger("boot-display")

def init_black_screen():
    """Initialize display to black screen."""
    logger = setup_logging()
    
    try:
        logger.info("Initializing boot display to black screen...")
        
        # Use default display config
        config = DisplayConfig()
        
        # Initialize display with minimal setup
        disp = ILI9341Display(
            rst=config.rst_pin,
            dc=config.dc_pin,  
            bl=config.bl_pin,
            spi_bus=config.spi_bus,
            spi_device=config.spi_device,
            spi_freq=config.spi_speed_hz,
            bl_freq=config.backlight_freq
        )
        
        # Initialize hardware
        disp.Init()
        
        # Fill with black (RGB565 color 0x0000)
        disp.clear_color(0x0000)
        
        # Set backlight to configured brightness
        disp.bl_DutyCycle(config.brightness)
        
        logger.info("Boot display initialized - screen is now black")
        
        # Clean exit - main LOOP service will reinitialize display
        disp.module_exit()
        
    except Exception as e:
        logger.error(f"Failed to initialize boot display: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_black_screen() 