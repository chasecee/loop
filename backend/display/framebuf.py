"""Frame buffer management for display."""

import struct
from pathlib import Path
from typing import List, Optional, Union, Dict
from PIL import Image
import io
import queue
import threading
import time

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


def _rgb_to_rgb565(r: int, g: int, b: int) -> int:
    """Convert RGB888 to RGB565 format."""
    # Pack RGB into 16-bit: RRRRR GGGGGG BBBBB
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


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
                return self._image_to_rgb565(img)
        except Exception as e:
            self.logger.error(f"Failed to decode JPEG file {file_path}: {e}")
            return None
    
    def decode_image_bytes(self, image_data: bytes) -> Optional[bytes]:
        """Decode image from bytes to RGB565."""
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                return self._image_to_rgb565(img)
        except Exception as e:
            self.logger.error(f"Failed to decode image bytes: {e}")
            return None
    
    def _image_to_rgb565(self, img: Image.Image) -> bytes:
        """Convert PIL Image to RGB565 bytes - pure Python implementation."""
        # Resize to display dimensions
        img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Get raw RGB data
        rgb_data = img.tobytes()
        
        # Convert to RGB565 - process 3 bytes at a time
        rgb565_data = bytearray()
        for i in range(0, len(rgb_data), 3):
            r, g, b = rgb_data[i], rgb_data[i+1], rgb_data[i+2]
            rgb565 = _rgb_to_rgb565(r, g, b)
            # Store as big-endian 16-bit
            rgb565_data.extend(struct.pack('>H', rgb565))
        
        return bytes(rgb565_data)


class FrameSequence:
    """Manages a sequence of frames for playback using a producer-consumer queue."""
    
    def __init__(self, frames_dir: Path, frame_count: int, frame_duration: float = 0.04):
        self.frames_dir = frames_dir
        self.frame_count = frame_count
        self.frame_duration = frame_duration
        
        # Generate frame paths on-the-fly (no need to store massive arrays)
        self.logger = get_logger("framebuf")

        # Bounded queue to hold pre-loaded frames
        # Buffer ~1 second of frames @ 30fps, or 30 frames.
        self.frame_queue = queue.Queue(maxsize=30)
        self._stop_event = threading.Event()
        self._producer_thread = threading.Thread(target=self._produce_frames, daemon=True)
        self._producer_thread.start()
        
        self.logger.info(f"Initialized sequence with {frame_count} frames (producer-consumer buffer)")

    def _get_frame_path(self, frame_idx: int) -> Path:
        """Generate frame path for given index."""
        return self.frames_dir / f"frame_{frame_idx+1:06d}.rgb"

    def _produce_frames(self):
        """Producer thread: loads frames from disk and puts them in the queue."""
        frame_idx = 0
        while not self._stop_event.is_set():
            if self.frame_count == 0:
                time.sleep(0.1)
                continue

            frame_path = self._get_frame_path(frame_idx)
            frame_data = self._load_frame(frame_path)
            
            # Use a timeout on put() to prevent deadlocking if the consumer stops reading.
            try:
                if frame_data:
                    self.frame_queue.put(frame_data, timeout=1)
                else:
                    # If a frame fails to load, put a placeholder to not hang the consumer
                    self.frame_queue.put(b'', timeout=1)
            except queue.Full:
                # This is okay. It means the consumer is paused or slow.
                # Continue to the next loop iteration to check _stop_event.
                continue

            frame_idx = (frame_idx + 1) % self.frame_count
            
    def get_next_frame(self, timeout=1.0) -> Optional[bytes]:
        """Get the next frame from the queue."""
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            self.logger.warning("Frame queue was empty")
            return None

    def stop(self):
        """Stop the producer thread."""
        self.logger.debug("Stopping frame producer thread...")
        self._stop_event.set()
        
        # Clear the queue to unblock the producer if it's waiting on a full queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
        
        if self._producer_thread and self._producer_thread.is_alive():
            self._producer_thread.join(timeout=1.0)
            if self._producer_thread.is_alive():
                self.logger.warning("Frame producer thread did not stop gracefully.")
        self.logger.debug("Frame producer thread stopped.")

    def get_frame_count(self) -> int:
        """Get total number of frames."""
        return self.frame_count
    
    def get_frame_duration(self, frame_idx: int) -> float:
        """Get duration for a specific frame."""
        return max(0.01, self.frame_duration)  # Minimum 10ms duration
    
    def _load_frame(self, frame_path: Path) -> Optional[bytes]:
        """Load a frame from disk."""
        try:
            with open(frame_path, 'rb') as f:
                data = f.read()
                if len(data) == 0:
                    self.logger.error(f"Frame file {frame_path} is empty")
                    return None
                return data
        except Exception as e:
            self.logger.error(f"Failed to load frame {frame_path}: {e}")
            return None 