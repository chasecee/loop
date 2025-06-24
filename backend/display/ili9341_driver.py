"""Clean ILI9341 Display Driver - No Waveshare cruft needed."""

import time
import spidev
from gpiozero import DigitalOutputDevice, PWMOutputDevice
from typing import Optional
from utils.logger import get_logger


class ILI9341Display:
    """Direct ILI9341 display driver - clean and minimal."""
    
    width = 240
    height = 320
    
    def __init__(self, rst: int = 27, dc: int = 25, bl: int = 18, 
                 spi_bus: int = 0, spi_device: int = 0, spi_freq: int = 40000000,
                 bl_freq: int = 1000):
        """Initialize ILI9341 display driver.
        
        Args:
            rst: Reset pin number
            dc: Data/Command pin number  
            bl: Backlight pin number
            spi_bus: SPI bus number
            spi_device: SPI device number
            spi_freq: SPI frequency in Hz
            bl_freq: Backlight PWM frequency in Hz
        """
        self.logger = get_logger("ili9341")
        
        # GPIO pins
        self.RST_PIN = DigitalOutputDevice(rst, active_high=True, initial_value=False)
        self.DC_PIN = DigitalOutputDevice(dc, active_high=True, initial_value=False)
        self.BL_PIN = PWMOutputDevice(bl, frequency=bl_freq)
        
        # SPI setup
        self.SPI = spidev.SpiDev()
        self.SPI.open(spi_bus, spi_device)
        self.SPI.max_speed_hz = spi_freq
        self.SPI.mode = 0b00
        
        # Initialize backlight off
        self.bl_DutyCycle(0)
        
        self.logger.info(f"ILI9341 driver initialized: RST={rst}, DC={dc}, BL={bl}")
    
    def command(self, cmd: int) -> None:
        """Send command to display."""
        self.digital_write(self.DC_PIN, False)
        self.spi_writebyte([cmd])
    
    def data(self, val: int) -> None:
        """Send data to display.""" 
        self.digital_write(self.DC_PIN, True)
        self.spi_writebyte([val])
    
    def digital_write(self, pin: DigitalOutputDevice, value: bool) -> None:
        """Write digital value to GPIO pin."""
        if value:
            pin.on()
        else:
            pin.off()
    
    def spi_writebyte(self, data: list) -> None:
        """Write data over SPI."""
        self.SPI.writebytes(data)
    
    def bl_DutyCycle(self, duty: float) -> None:
        """Set backlight PWM duty cycle (0-100%)."""
        self.BL_PIN.value = duty / 100
    
    def bl_Frequency(self, freq: int) -> None:
        """Set backlight PWM frequency."""
        self.BL_PIN.frequency = freq
    
    def reset(self) -> None:
        """Hardware reset the display."""
        self.digital_write(self.RST_PIN, True)
        time.sleep(0.01)
        self.digital_write(self.RST_PIN, False)
        time.sleep(0.01)
        self.digital_write(self.RST_PIN, True)
        time.sleep(0.01)
    
    def Init(self) -> None:
        """Initialize the ILI9341 display with proper register sequence."""
        self.logger.info("Initializing ILI9341 display...")
        
        # Hardware reset
        self.reset()
        
        # ILI9341 initialization sequence (extracted from Waveshare)
        self.command(0x11)  # Sleep out
        time.sleep(0.12)    # Wait 120ms
        
        # Power control registers
        self.command(0xCF)
        self.data(0x00)
        self.data(0xC1)
        self.data(0x30)
        
        self.command(0xED)
        self.data(0x64)
        self.data(0x03)
        self.data(0x12)
        self.data(0x81)
        
        self.command(0xE8)
        self.data(0x85)
        self.data(0x00)
        self.data(0x79)
        
        self.command(0xCB)
        self.data(0x39)
        self.data(0x2C)
        self.data(0x00)
        self.data(0x34)
        self.data(0x02)
        
        self.command(0xF7)
        self.data(0x20)
        
        self.command(0xEA)
        self.data(0x00)
        self.data(0x00)
        
        # Power control
        self.command(0xC0)  # Power control
        self.data(0x1D)     # VRH[5:0]
        
        self.command(0xC1)  # Power control
        self.data(0x12)     # SAP[2:0], BT[3:0]
        
        # VCM control
        self.command(0xC5)
        self.data(0x33)
        self.data(0x3F)
        
        self.command(0xC7)
        self.data(0x92)
        
        # Memory access control
        self.command(0x3A)  # Pixel format
        self.data(0x55)     # 16-bit RGB565
        
        self.command(0x36)  # Memory access control
        self.data(0x08)     # Default orientation
        
        # Frame rate control
        self.command(0xB1)
        self.data(0x00)
        self.data(0x12)
        
        # Display function control
        self.command(0xB6)
        self.data(0x0A)
        self.data(0xA2)
        
        self.command(0x44)
        self.data(0x02)
        
        # Gamma correction
        self.command(0xF2)  # 3Gamma function disable
        self.data(0x00)
        
        self.command(0x26)  # Gamma curve selected
        self.data(0x01)
        
        # Positive gamma correction
        self.command(0xE0)
        gamma_pos = [0x0F, 0x22, 0x1C, 0x1B, 0x08, 0x0F, 0x48, 0xB8,
                     0x34, 0x05, 0x0C, 0x09, 0x0F, 0x07, 0x00]
        for val in gamma_pos:
            self.data(val)
        
        # Negative gamma correction  
        self.command(0xE1)
        gamma_neg = [0x00, 0x23, 0x24, 0x07, 0x10, 0x07, 0x38, 0x47,
                     0x4B, 0x0A, 0x13, 0x06, 0x30, 0x38, 0x0F]
        for val in gamma_neg:
            self.data(val)
        
        # Display on
        self.command(0x29)
        
        self.logger.info("ILI9341 initialization complete")
    
    def SetWindows(self, x_start: int, y_start: int, x_end: int, y_end: int) -> None:
        """Set the drawing window coordinates."""
        # Set column address
        self.command(0x2A)
        self.data(x_start >> 8)
        self.data(x_start & 0xFF)
        self.data(x_end >> 8)
        self.data((x_end - 1) & 0xFF)
        
        # Set row address
        self.command(0x2B)
        self.data(y_start >> 8)
        self.data(y_start & 0xFF)
        self.data(x_end >> 8)
        self.data((y_end - 1) & 0xFF)
        
        # Memory write command
        self.command(0x2C)
    
    def clear(self) -> None:
        """Clear the display to white."""
        buffer = [0xFF] * (self.width * self.height * 2)
        time.sleep(0.02)
        self.SetWindows(0, 0, self.width, self.height)
        self.digital_write(self.DC_PIN, True)
        
        # Send in 4KB chunks
        for i in range(0, len(buffer), 4096):
            self.spi_writebyte(buffer[i:i+4096])
    
    def clear_color(self, color: int) -> None:
        """Clear the display to specified RGB565 color."""
        buffer = [color >> 8, color & 0xFF] * (self.width * self.height)
        time.sleep(0.02)
        self.SetWindows(0, 0, self.width, self.height)
        self.digital_write(self.DC_PIN, True)
        
        # Send in 4KB chunks
        for i in range(0, len(buffer), 4096):
            self.spi_writebyte(buffer[i:i+4096])
    
    def module_exit(self) -> None:
        """Clean up resources."""
        self.logger.info("Cleaning up ILI9341 driver...")
        
        # Close SPI
        self.SPI.close()
        
        # Clean up GPIO
        self.digital_write(self.RST_PIN, True)
        self.digital_write(self.DC_PIN, False)
        self.BL_PIN.close()
        
        time.sleep(0.001)
        self.logger.info("ILI9341 cleanup complete") 