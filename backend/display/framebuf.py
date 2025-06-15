"""Frame buffer management for display."""

import struct
from pathlib import Path
from typing import List, Optional, Tuple, Union
from PIL import Image
import io
import numpy as np

from utils.logger import get_logger


class FrameBuffer:
    """Frame buffer for RGB565 pixel data."""
    
    def __init__(self, width: int, height: int):
        """Initialize frame buffer."""
        self.width = width
        self.height = height
        self.size = width * height * 2  # 2 bytes per RGB565 pixel
        self.data = bytearray(self.size)
        self.logger = get_logger("framebuf")
    
    def clear(self, color: int = 0x0000) -> None:
        """Clear buffer with specified RGB565 color."""
        color_bytes = struct.pack(">H", color)  # Big-endian 16-bit
        for i in range(0, self.size, 2):
            self.data[i:i+2] = color_bytes
    
    def set_pixel(self, x: int, y: int, color: int) -> None:
        """Set a single pixel."""
        if 0 <= x < self.width and 0 <= y < self.height:
            offset = (y * self.width + x) * 2
            self.data[offset:offset+2] = struct.pack(">H", color)
    
    def get_pixel(self, x: int, y: int) -> int:
        """Get a single pixel value."""
        if 0 <= x < self.width and 0 <= y < self.height:
            offset = (y * self.width + x) * 2
            return struct.unpack(">H", self.data[offset:offset+2])[0]
        return 0
    
    def load_from_bytes(self, data: bytes) -> None:
        """Load frame data from bytes."""
        if len(data) != self.size:
            raise ValueError(f"Data size mismatch: expected {self.size}, got {len(data)}")
        self.data[:] = data
    
    def get_bytes(self) -> bytes:
        """Get frame data as bytes."""
        return bytes(self.data)
    
    @staticmethod
    def rgb888_to_rgb565(r: int, g: int, b: int) -> int:
        """Convert RGB888 to RGB565."""
        return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    
    @staticmethod
    def rgb565_to_rgb888(color: int) -> Tuple[int, int, int]:
        """Convert RGB565 to RGB888."""
        r = (color >> 11) << 3
        g = ((color >> 5) & 0x3F) << 2
        b = (color & 0x1F) << 3
        return r, g, b


class FrameDecoder:
    """Decoder for different frame formats."""
    
    def __init__(self, width: int, height: int):
        """Initialize decoder."""
        self.width = width
        self.height = height
        self.logger = get_logger("decoder")
    
    def decode_rgb565_file(self, file_path: Path) -> Optional[bytes]:
        """Decode RGB565 binary file."""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            expected_size = self.width * self.height * 2
            if len(data) != expected_size:
                self.logger.error(f"RGB565 file size mismatch: {len(data)} vs {expected_size}")
                return None
            
            return data
        except Exception as e:
            self.logger.error(f"Failed to decode RGB565 file {file_path}: {e}")
            return None
    
    def decode_jpeg_file(self, file_path: Path) -> Optional[bytes]:
        """Decode JPEG file to RGB565."""
        try:
            with Image.open(file_path) as img:
                # Resize to display dimensions
                img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
                
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Convert to RGB565 using fast NumPy operations
                img_array = np.array(img, dtype=np.uint8)
                
                # Extract R, G, B channels
                r = img_array[:, :, 0].astype(np.uint16)
                g = img_array[:, :, 1].astype(np.uint16)
                b = img_array[:, :, 2].astype(np.uint16)
                
                # Convert to RGB565 using vectorized operations
                rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                
                # Convert to big-endian bytes
                return rgb565.astype('>u2').tobytes()
        
        except Exception as e:
            self.logger.error(f"Failed to decode JPEG file {file_path}: {e}")
            return None
    
    def decode_image_bytes(self, image_data: bytes) -> Optional[bytes]:
        """Decode image from bytes to RGB565."""
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # Resize to display dimensions
                img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
                
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Convert to RGB565 using fast NumPy operations
                img_array = np.array(img, dtype=np.uint8)
                
                # Extract R, G, B channels
                r = img_array[:, :, 0].astype(np.uint16)
                g = img_array[:, :, 1].astype(np.uint16)
                b = img_array[:, :, 2].astype(np.uint16)
                
                # Convert to RGB565 using vectorized operations
                rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                
                # Convert to big-endian bytes
                return rgb565.astype('>u2').tobytes()
        
        except Exception as e:
            self.logger.error(f"Failed to decode image bytes: {e}")
            return None


class FrameSequence:
    """Manages a sequence of frames for animation."""
    
    def __init__(self, frames_dir: Path, width: int, height: int):
        """Initialize frame sequence."""
        self.frames_dir = frames_dir
        self.width = width
        self.height = height
        self.logger = get_logger("sequence")
        self.decoder = FrameDecoder(width, height)
        
        # Load frame list
        self.frame_files = self._load_frame_list()
        self.frame_count = len(self.frame_files)
        self.current_frame = 0
        
        self.logger.info(f"Loaded {self.frame_count} frames from {frames_dir}")
    
    def _load_frame_list(self) -> List[Path]:
        """Load sorted list of frame files."""
        if not self.frames_dir.exists():
            return []
        
        frame_files = []
        
        # Look for RGB565 files first
        rgb_files = list(self.frames_dir.glob("frame_*.rgb565"))
        if rgb_files:
            frame_files = sorted(rgb_files, key=lambda x: int(x.stem.split('_')[1]))
        else:
            # Look for JPEG files
            jpg_files = list(self.frames_dir.glob("frame_*.jpg"))
            if jpg_files:
                frame_files = sorted(jpg_files, key=lambda x: int(x.stem.split('_')[1]))
        
        return frame_files
    
    def get_frame(self, frame_index: int = None) -> Optional[bytes]:
        """Get frame data by index."""
        if not self.frame_files:
            return None
        
        if frame_index is None:
            frame_index = self.current_frame
        
        if not (0 <= frame_index < self.frame_count):
            return None
        
        frame_file = self.frame_files[frame_index]
        
        # Decode based on file extension
        if frame_file.suffix == '.rgb565':
            return self.decoder.decode_rgb565_file(frame_file)
        elif frame_file.suffix == '.jpg':
            return self.decoder.decode_jpeg_file(frame_file)
        
        return None
    
    def next_frame(self) -> Optional[bytes]:
        """Get next frame in sequence."""
        if not self.frame_files:
            return None
        
        frame_data = self.get_frame(self.current_frame)
        self.current_frame = (self.current_frame + 1) % self.frame_count
        return frame_data
    
    def reset(self) -> None:
        """Reset to first frame."""
        self.current_frame = 0
    
    def get_frame_count(self) -> int:
        """Get total frame count."""
        return self.frame_count 