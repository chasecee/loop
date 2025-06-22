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
        self._software_brightness: float = 1.0  # extra dimming factor 0-1
        self._gamma: float = max(0.1, config.gamma) if hasattr(config, "gamma") else 2.4
        # Precompute gamma LUT (0-255 -> corrected)
        import numpy as _np
        self._gamma_lut = (_np.linspace(0, 1, 256) ** (1.0 / self._gamma) * 255).astype(_np.uint8)
        
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

        # The raw RGB565 fast-path currently assumes the buffer is already
        # in the panel's native orientation (landscape 320×240) and thus
        # ignores any additional rotation configured by the user.  Trying
        # to use it while a non-zero rotation is active results in
        # garbled / offset output.  Until we add full orientation support
        # to the raw path we therefore only enable it when *no* rotation
        # is requested (i.e. rotation == 0).

        can_send_raw = (
            abs(self._gamma - 1.0) < 0.05 and  # gamma disabled
            (self.config.rotation % 360) == 0   # no rotation
        )

        if can_send_raw:
            try:
                # --- optional brightness scaling in RGB565 domain ---
                if self._software_brightness < 0.999:
                    # View the buffer as big-endian uint16, make a copy we can mutate
                    pix = np.frombuffer(frame_data, dtype='>u2').astype(np.uint16)

                    # Separate 5-6-5 components
                    r5 = (pix >> 11) & 0x1F
                    g6 = (pix >> 5) & 0x3F
                    b5 = pix & 0x1F

                    factor = self._software_brightness
                    # Scale each component, clamp to valid range
                    r5 = np.clip((r5.astype(np.float32) * factor).round(), 0, 31).astype(np.uint16)
                    g6 = np.clip((g6.astype(np.float32) * factor).round(), 0, 63).astype(np.uint16)
                    b5 = np.clip((b5.astype(np.float32) * factor).round(), 0, 31).astype(np.uint16)

                    pix = (r5 << 11) | (g6 << 5) | b5
                    frame_bytes = pix.astype('>u2').tobytes()
                else:
                    frame_bytes = frame_data  # no brightness change

                # MADCTL value 0x78 gives us the same landscape orientation as
                # the standard ShowImage path when the source buffer is 320×240
                # laid out left-to-right, top-to-bottom.
                self.disp.command(0x36)
                self.disp.data(0x78)

                # Window to full screen
                self.disp.SetWindows(0, 0, self.disp.width, self.disp.height)
                # Switch to data mode
                self.disp.digital_write(self.disp.DC_PIN, True)

                # Send the buffer in 4 kB chunks (SPI driver limit)
                for offset in range(0, len(frame_bytes), 4096):
                    chunk = frame_bytes[offset:offset + 4096]
                    # spi_writebyte expects a list of ints
                    self.disp.spi_writebyte(list(chunk))
                return  # done
            except Exception as e:
                self.logger.error(f"Raw RGB565 blit failed, falling back to PIL path: {e}")

        # ---------- Slow fallback path (existing behaviour) ----------
        try:
            # Robust conversion: RGB565 big-endian -> RGB888 using NumPy (fast ~2ms)
            pixel_data = np.frombuffer(frame_data, dtype='>u2')  # big-endian uint16
            # Extract RGB components and reshape to 2-D before stacking
            r = (((pixel_data >> 11) & 0x1F).astype(np.uint8) << 3).reshape((base_height, base_width))
            g = (((pixel_data >> 5) & 0x3F).astype(np.uint8) << 2).reshape((base_height, base_width))
            b = (((pixel_data & 0x1F).astype(np.uint8) << 3)).reshape((base_height, base_width))
            rgb_array = np.dstack((r, g, b))

            # Apply software dimming to avoid PWM flicker at low brightness
            if self._software_brightness < 0.99:
                rgb_array = (rgb_array.astype(np.float32) * self._software_brightness).astype(np.uint8)

            # Apply gamma correction using LUT
            if self._gamma and abs(self._gamma - 1.0) > 0.05:
                lut = self._gamma_lut
                rgb_array = lut[rgb_array]

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

        if type(level) is bool:
            if level:
                duty_cycle = 100  # backlight on fully
                self._software_brightness = self.config.brightness / 100.0
            else:
                duty_cycle = 0
                self._software_brightness = 0.0
        else:
            pct = max(0, min(100, int(level)))
            if pct == 0:
                duty_cycle = 0
                self._software_brightness = 0.0
            else:
                duty_cycle = 100  # always full backlight to avoid flicker
                self._software_brightness = pct / 100.0

        self.disp.bl_DutyCycle(duty_cycle)
        self.logger.debug(
            f"Backlight PWM={duty_cycle}%, software_brightness={self._software_brightness:.2f}"
        )

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.initialized and self.disp:
            self.disp.module_exit()
            self.initialized = False
            self.logger.info("Waveshare display driver cleaned up")

    # ------------------- Gamma API --------------------
    def set_gamma(self, gamma: float) -> None:
        """Set display gamma (software correction)."""
        gamma = max(0.1, min(10.0, gamma))
        self._gamma = gamma
        import numpy as _np
        self._gamma_lut = (_np.linspace(0, 1, 256) ** (1.0 / gamma) * 255).astype(_np.uint8)
        self.logger.info(f"Set software gamma to {gamma:.2f}") 