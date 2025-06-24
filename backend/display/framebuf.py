"""Frame buffer utilities for LOOP display playback.

Only `FrameSequence` is used at runtime; legacy FrameBuffer / FrameDecoder
implementations and heavy image-processing helpers have been removed to
trim bundle size and silence linters.
"""

# --- stdlib ---
from pathlib import Path
from typing import Optional
import queue
import threading
import time

# --- app ---
from utils.logger import get_logger


class FrameSequence:
    """Manages a sequence of RGB565 frame files using a producer-consumer queue."""
    
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
        
        self.logger.info(
            f"Initialized sequence with {frame_count} frames "
            "(producer-consumer buffer)"
        )

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