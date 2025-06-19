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
        self.spi_speed = 16000000  # Start with 16MHz, will try to optimize
        
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
        
        # Initialize SPI with speed optimization
        self.spi = spidev.SpiDev()
        self.spi.open(self.config.spi_bus, self.config.spi_device)
        self._optimize_spi_speed()
        self.spi.mode = 0
        
        self.logger.info(f"Initialized ILI9341 driver: {self.config.width}x{self.config.height} @ {self.spi_speed/1000000:.1f}MHz")
    
    def _optimize_spi_speed(self) -> None:
        """Try to find the optimal SPI speed with fallback."""
        # Try speeds from fastest to slowest (aggressive optimization)
        test_speeds = [24000000, 20000000, 18000000, 16000000, 12000000]
        
        for speed in test_speeds:
            try:
                self.spi.max_speed_hz = speed
                # Test with a small write to validate speed
                self.spi.writebytes([0x00])  # Dummy write to test
                self.spi_speed = speed
                self.logger.info(f"SPI speed optimized to {speed/1000000:.1f}MHz")
                return
            except Exception as e:
                self.logger.debug(f"SPI speed {speed/1000000:.1f}MHz failed: {e}")
                continue
        
        # Fallback to conservative speed
        self.spi_speed = 16000000
        self.spi.max_speed_hz = self.spi_speed
        self.logger.warning("Using fallback SPI speed: 16MHz")
    
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
        
        # Validate data before writing
        if isinstance(data, int):
            GPIO.output(self.config.dc_pin, GPIO.HIGH)  # Data mode
            self.spi.writebytes([data])
        elif data:  # Only write if data is not empty
            GPIO.output(self.config.dc_pin, GPIO.HIGH)  # Data mode
            self.spi.writebytes(data)
        # If data is empty, do nothing (no error)
    
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
        """Write pixel data to display with maximum performance optimization."""
        if not SPI_AVAILABLE or not data:
            return
        
        # Set data mode ONCE at the start - major optimization
        GPIO.output(self.config.dc_pin, GPIO.HIGH)
        
        # AGGRESSIVE OPTIMIZATION: Try larger chunk sizes for better performance
        # The Pi Zero 2 W might handle larger chunks than 4KB
        chunk_sizes = [8192, 6144, 4096]  # Try 8KB, 6KB, then fallback to 4KB
        
        for chunk_size in chunk_sizes:
            try:
                if len(data) <= chunk_size:
                    # Single write for small data - fastest path
                    self.spi.writebytes(data)
                    return
                else:
                    # Chunked write - minimize overhead
                    chunks_written = 0
                    for i in range(0, len(data), chunk_size):
                        chunk = data[i:i + chunk_size]
                        self.spi.writebytes(chunk)
                        chunks_written += 1
                    
                    # If we got here without exception, this chunk size works
                    return
                    
            except (OSError, IOError) as e:
                # This chunk size failed, try smaller
                if chunk_size == 4096:  # Last resort failed
                    self.logger.warning(f"SPI write failed even with 4KB chunks: {e}")
                    return
                continue
            except Exception as e:
                # Unexpected error - log and exit
                self.logger.error(f"Unexpected display error: {e}")
                raise
    
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
        """Display a frame of RGB565 pixel data with anti-tearing optimizations."""
        if not self.initialized:
            self.init()
        
        # Quick validation without logging for performance
        expected_size = self.config.width * self.config.height * 2  # 2 bytes per RGB565 pixel
        if not frame_data or len(frame_data) != expected_size:
            return
        
        # ANTI-TEARING OPTIMIZATION: Set window and write data in one atomic operation
        # This minimizes the time between setting the window and writing data
        
        # Set window once for entire frame
        self.set_window(0, 0, self.config.width - 1, self.config.height - 1)
        
        # Write all pixel data in optimized chunks
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
        except (RuntimeError, ValueError) as e:
            # GPIO cleanup can fail if already cleaned up or pins unavailable
            self.logger.debug(f"GPIO backlight cleanup failed (expected): {e}")
        
        GPIO.cleanup()
        self.logger.info("Display driver cleaned up") 