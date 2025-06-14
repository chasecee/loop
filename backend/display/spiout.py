"""ILI9341 SPI display driver for Waveshare 2.4" LCD."""

import time
from typing import Optional, Tuple
try:
    import spidev
    import RPi.GPIO as GPIO
    SPI_AVAILABLE = True
except ImportError:
    SPI_AVAILABLE = False

from config.schema import DisplayConfig
from utils.logger import get_logger


class ILI9341Driver:
    """ILI9341 display driver."""
    
    # ILI9341 Commands
    ILI9341_SWRESET = 0x01
    ILI9341_SLPOUT = 0x11
    ILI9341_DISPOFF = 0x28
    ILI9341_DISPON = 0x29
    ILI9341_CASET = 0x2A
    ILI9341_PASET = 0x2B
    ILI9341_RAMWR = 0x2C
    ILI9341_MADCTL = 0x36
    ILI9341_COLMOD = 0x3A
    ILI9341_PWCTR1 = 0xC0
    ILI9341_PWCTR2 = 0xC1
    ILI9341_VMCTR1 = 0xC5
    ILI9341_VMCTR2 = 0xC7
    ILI9341_GMCTRP1 = 0xE0
    ILI9341_GMCTRN1 = 0xE1
    
    def __init__(self, config: DisplayConfig):
        """Initialize the display driver."""
        self.config = config
        self.logger = get_logger("display")
        self.spi: Optional[spidev.SpiDev] = None
        self.initialized = False
        
        if not SPI_AVAILABLE:
            self.logger.warning("SPI libraries not available - running in simulation mode")
            return
        
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup pins
        GPIO.setup(self.config.dc_pin, GPIO.OUT)
        GPIO.setup(self.config.rst_pin, GPIO.OUT)
        GPIO.setup(self.config.bl_pin, GPIO.OUT)
        
        # Initialize SPI
        self.spi = spidev.SpiDev()
        self.spi.open(self.config.spi_bus, self.config.spi_device)
        self.spi.max_speed_hz = 32000000  # 32MHz
        self.spi.mode = 0
        
        self.logger.info(f"Initialized ILI9341 driver: {self.config.width}x{self.config.height}")
    
    def _write_command(self, cmd: int) -> None:
        """Write command to display."""
        if not SPI_AVAILABLE:
            return
        
        GPIO.output(self.config.dc_pin, GPIO.LOW)  # Command mode
        self.spi.writebytes([cmd])
    
    def _write_data(self, data) -> None:
        """Write data to display."""
        if not SPI_AVAILABLE:
            return
        
        GPIO.output(self.config.dc_pin, GPIO.HIGH)  # Data mode
        if isinstance(data, int):
            self.spi.writebytes([data])
        else:
            self.spi.writebytes(data)
    
    def _reset(self) -> None:
        """Hardware reset the display."""
        if not SPI_AVAILABLE:
            return
        
        GPIO.output(self.config.rst_pin, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self.config.rst_pin, GPIO.HIGH)
        time.sleep(0.1)
    
    def init(self) -> None:
        """Initialize the display."""
        if not SPI_AVAILABLE:
            self.logger.warning("Cannot initialize display - SPI not available")
            return
        
        if self.initialized:
            return
        
        self.logger.info("Initializing ILI9341 display...")
        
        # Reset display
        self._reset()
        
        # Initialize sequence
        self._write_command(self.ILI9341_SWRESET)
        time.sleep(0.15)
        
        self._write_command(self.ILI9341_SLPOUT)
        time.sleep(0.15)
        
        # Power control
        self._write_command(self.ILI9341_PWCTR1)
        self._write_data([0x23])
        
        self._write_command(self.ILI9341_PWCTR2)
        self._write_data([0x10])
        
        # VCOM control
        self._write_command(self.ILI9341_VMCTR1)
        self._write_data([0x3e, 0x28])
        
        self._write_command(self.ILI9341_VMCTR2)
        self._write_data([0x86])
        
        # Memory access control (rotation)
        self._write_command(self.ILI9341_MADCTL)
        rotation_values = {0: 0x48, 90: 0x28, 180: 0x88, 270: 0xE8}
        self._write_data([rotation_values.get(self.config.rotation, 0x48)])
        
        # Pixel format (RGB565)
        self._write_command(self.ILI9341_COLMOD)
        self._write_data([0x55])
        
        # Gamma correction
        self._write_command(self.ILI9341_GMCTRP1)
        self._write_data([0x0F, 0x31, 0x2B, 0x0C, 0x0E, 0x08, 0x4E, 0xF1,
                         0x37, 0x07, 0x10, 0x03, 0x0E, 0x09, 0x00])
        
        self._write_command(self.ILI9341_GMCTRN1)
        self._write_data([0x00, 0x0E, 0x14, 0x03, 0x11, 0x07, 0x31, 0xC1,
                         0x48, 0x08, 0x0F, 0x0C, 0x31, 0x36, 0x0F])
        
        # Display on
        self._write_command(self.ILI9341_DISPON)
        time.sleep(0.1)
        
        # Turn on backlight
        GPIO.output(self.config.bl_pin, GPIO.HIGH)
        
        self.initialized = True
        self.logger.info("ILI9341 display initialized successfully")
    
    def set_window(self, x0: int, y0: int, x1: int, y1: int) -> None:
        """Set drawing window."""
        if not SPI_AVAILABLE:
            return
        
        # Column address
        self._write_command(self.ILI9341_CASET)
        self._write_data([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF])
        
        # Page address
        self._write_command(self.ILI9341_PASET)
        self._write_data([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF])
        
        # Write to RAM
        self._write_command(self.ILI9341_RAMWR)
    
    def write_pixel_data(self, data: bytes) -> None:
        """Write pixel data to display."""
        if not SPI_AVAILABLE:
            return
        
        GPIO.output(self.config.dc_pin, GPIO.HIGH)  # Data mode
        
        # Write data in chunks to avoid SPI buffer overflow
        chunk_size = 4096
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            self.spi.writebytes(chunk)
    
    def fill_screen(self, color: int = 0x0000) -> None:
        """Fill entire screen with color (RGB565)."""
        if not self.initialized:
            self.init()
        
        self.set_window(0, 0, self.config.width - 1, self.config.height - 1)
        
        # Convert 16-bit color to bytes
        color_bytes = [(color >> 8) & 0xFF, color & 0xFF]
        pixel_data = color_bytes * (self.config.width * self.config.height)
        
        self.write_pixel_data(bytes(pixel_data))
    
    def display_frame(self, frame_data: bytes) -> None:
        """Display a frame of RGB565 pixel data."""
        if not self.initialized:
            self.init()
        
        expected_size = self.config.width * self.config.height * 2  # 2 bytes per RGB565 pixel
        if len(frame_data) != expected_size:
            self.logger.error(f"Frame data size mismatch: got {len(frame_data)}, expected {expected_size}")
            return
        
        self.set_window(0, 0, self.config.width - 1, self.config.height - 1)
        self.write_pixel_data(frame_data)
    
    def set_backlight(self, enabled: bool) -> None:
        """Control backlight."""
        if not SPI_AVAILABLE:
            return
        
        GPIO.output(self.config.bl_pin, GPIO.HIGH if enabled else GPIO.LOW)
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if not SPI_AVAILABLE:
            return
        
        if self.spi:
            self.spi.close()
        
        # Turn off backlight
        try:
            GPIO.output(self.config.bl_pin, GPIO.LOW)
        except:
            pass
        
        GPIO.cleanup()
        self.logger.info("Display driver cleaned up") 