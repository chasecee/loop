"""Memory pool for display operations to minimize allocations on Pi Zero 2."""

import threading
from typing import List, Optional
from collections import deque

from utils.logger import get_logger

logger = get_logger("memory_pool")


class FrameBufferPool:
    """Memory pool for RGB565 frame buffers (320x240 = 153,600 bytes each)."""
    
    def __init__(self, pool_size: int = 4):
        """Initialize pool with pre-allocated frame buffers."""
        self.pool_size = pool_size
        self.frame_size = 320 * 240 * 2  # RGB565 frame size
        self._pool: deque = deque()
        self._in_use: set = set()
        self._lock = threading.Lock()
        
        # Pre-allocate frame buffers
        for _ in range(pool_size):
            frame_buffer = bytearray(self.frame_size)
            self._pool.append(frame_buffer)
        
        logger.info(f"FrameBufferPool initialized with {pool_size} buffers ({self.frame_size * pool_size} bytes)")
    
    def get_buffer(self) -> Optional[bytearray]:
        """Get a frame buffer from the pool."""
        with self._lock:
            if self._pool:
                buffer = self._pool.popleft()
                self._in_use.add(id(buffer))
                return buffer
            else:
                # Pool exhausted - allocate new buffer (should be rare)
                logger.warning("FrameBufferPool exhausted, allocating new buffer")
                buffer = bytearray(self.frame_size)
                self._in_use.add(id(buffer))
                return buffer
    
    def return_buffer(self, buffer: bytearray) -> None:
        """Return a frame buffer to the pool."""
        if buffer is None:
            return
            
        with self._lock:
            buffer_id = id(buffer)
            if buffer_id in self._in_use:
                self._in_use.remove(buffer_id)
                if len(self._pool) < self.pool_size:
                    # Clear buffer contents for reuse
                    buffer[:] = b'\x00' * len(buffer)
                    self._pool.append(buffer)
                # If pool is full, let buffer be garbage collected
    
    def get_stats(self) -> dict:
        """Get pool statistics."""
        with self._lock:
            return {
                "pool_size": self.pool_size,
                "available": len(self._pool),
                "in_use": len(self._in_use),
                "frame_size": self.frame_size
            }


class SpiChunkPool:
    """Memory pool for SPI transmission lists to avoid repeated list() conversions."""
    
    def __init__(self, pool_size: int = 8, chunk_size: int = 4096):
        """Initialize pool with pre-allocated lists."""
        self.pool_size = pool_size
        self.chunk_size = chunk_size
        self._pool: deque = deque()
        self._lock = threading.Lock()
        
        # Pre-allocate lists
        for _ in range(pool_size):
            chunk_list = [0] * chunk_size
            self._pool.append(chunk_list)
        
        logger.info(f"SpiChunkPool initialized with {pool_size} chunks ({chunk_size} bytes each)")
    
    def get_chunk_list(self, data: bytes, offset: int = 0) -> List[int]:
        """Get a list populated with byte data, reusing memory when possible."""
        chunk_data = data[offset:offset + self.chunk_size]
        
        with self._lock:
            if self._pool:
                # Reuse existing list
                chunk_list = self._pool.popleft()
                # Resize if needed
                if len(chunk_list) != len(chunk_data):
                    chunk_list = chunk_list[:len(chunk_data)] if len(chunk_list) > len(chunk_data) else chunk_list + [0] * (len(chunk_data) - len(chunk_list))
                
                # Copy data
                for i, byte_val in enumerate(chunk_data):
                    chunk_list[i] = byte_val
                
                return chunk_list
            else:
                # Pool exhausted - create new list
                return list(chunk_data)
    
    def return_chunk_list(self, chunk_list: List[int]) -> None:
        """Return a chunk list to the pool."""
        if chunk_list is None:
            return
            
        with self._lock:
            if len(self._pool) < self.pool_size and len(chunk_list) <= self.chunk_size:
                self._pool.append(chunk_list)
    
    def get_stats(self) -> dict:
        """Get pool statistics."""
        with self._lock:
            return {
                "pool_size": self.pool_size,
                "available": len(self._pool),
                "chunk_size": self.chunk_size
            }


# Global memory pools - initialized once per process
_frame_buffer_pool: Optional[FrameBufferPool] = None
_spi_chunk_pool: Optional[SpiChunkPool] = None


def get_frame_buffer_pool() -> FrameBufferPool:
    """Get the global frame buffer pool."""
    global _frame_buffer_pool
    if _frame_buffer_pool is None:
        _frame_buffer_pool = FrameBufferPool(pool_size=4)
    return _frame_buffer_pool


def get_spi_chunk_pool() -> SpiChunkPool:
    """Get the global SPI chunk pool."""
    global _spi_chunk_pool
    if _spi_chunk_pool is None:
        _spi_chunk_pool = SpiChunkPool(pool_size=8)
    return _spi_chunk_pool


def get_memory_stats() -> dict:
    """Get statistics for all memory pools."""
    return {
        "frame_buffer_pool": get_frame_buffer_pool().get_stats(),
        "spi_chunk_pool": get_spi_chunk_pool().get_stats()
    } 