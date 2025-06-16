"""Media conversion utilities for GIF/video to RGB565 frames."""

import json
import struct
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from PIL import Image, ImageSequence, ImageOps
import tempfile
import hashlib
import numpy as np

from utils.logger import get_logger
from display.framebuf import FrameBuffer


class MediaConverter:
    """Convert media files to display-ready formats."""
    
    def __init__(self, target_width: int, target_height: int):
        """Initialize converter."""
        self.target_width = target_width
        self.target_height = target_height
        self.logger = get_logger("converter")
        
        # Check for ffmpeg availability
        self.ffmpeg_available = shutil.which('ffmpeg') is not None
        if not self.ffmpeg_available:
            self.logger.warning("ffmpeg not found - video conversion will be limited")
    
    def _generate_slug(self, filename: str) -> str:
        """Generate URL-safe slug from filename."""
        # Remove extension and create hash-based slug
        name = Path(filename).stem
        hash_part = hashlib.md5(filename.encode()).hexdigest()[:8]
        return f"{name}_{hash_part}".lower().replace(' ', '_').replace('-', '_')
    
    def convert_gif(self, gif_path: Path, output_dir: Path, format_type: str = "rgb565") -> Optional[Dict]:
        """Convert GIF to frame sequence."""
        try:
            self.logger.info(f"Converting GIF: {gif_path}")
            
            with Image.open(gif_path) as img:
                if not hasattr(img, 'is_animated') or not img.is_animated:
                    self.logger.error("File is not an animated GIF")
                    return None
                
                frames = []
                durations = []
                
                output_dir.mkdir(parents=True, exist_ok=True)
                frames_dir = output_dir / "frames"
                frames_dir.mkdir(exist_ok=True)
                
                frame_count = 0
                for frame in ImageSequence.Iterator(img):
                    # Resize & crop frame to fill the display
                    frame = self._resize_and_crop(frame)
                    
                    # Save frame
                    frame_path = self._save_frame(frame, frames_dir, frame_count, format_type)
                    if frame_path:
                        frames.append(frame_path.name)
                        
                        # Get frame duration (convert from milliseconds to seconds)
                        duration = frame.info.get('duration', 100) / 1000.0
                        durations.append(duration)
                        
                        frame_count += 1
                
                if not frames:
                    self.logger.error("No frames were converted")
                    return None
                
                # Generate metadata
                metadata = {
                    "type": "gif",
                    "slug": self._generate_slug(gif_path.name),
                    "original_filename": gif_path.name,
                    "width": self.target_width,
                    "height": self.target_height,
                    "frame_count": frame_count,
                    "frames": frames,
                    "durations": durations,
                    "format": format_type,
                    "loop_count": getattr(img, 'info', {}).get('loop', 0)  # 0 = infinite
                }
                
                # Save metadata
                metadata_path = output_dir / "metadata.json"
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                self.logger.info(f"Converted GIF to {frame_count} frames")
                return metadata
                
        except Exception as e:
            self.logger.error(f"Failed to convert GIF {gif_path}: {e}")
            return None
    
    def convert_video(self, video_path: Path, output_dir: Path, format_type: str = "rgb565", fps: float = 10.0) -> Optional[Dict]:
        """Convert video to frame sequence using ffmpeg."""
        if not self.ffmpeg_available:
            self.logger.error("ffmpeg not available for video conversion")
            return None
        
        try:
            self.logger.info(f"Converting video: {video_path}")
            
            output_dir.mkdir(parents=True, exist_ok=True)
            frames_dir = output_dir / "frames"
            frames_dir.mkdir(exist_ok=True)
            
            # Create temporary directory for intermediate frames
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Extract frames using ffmpeg
                cmd = [
                    'ffmpeg', '-i', str(video_path),
                    '-vf', f'fps={fps},scale={self.target_width}:{self.target_height}:flags=lanczos',
                    '-y',  # Overwrite output files
                    str(temp_path / 'frame_%06d.png')
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.error(f"ffmpeg failed: {result.stderr}")
                    return None
                
                # Convert extracted frames
                frame_files = sorted(temp_path.glob('frame_*.png'))
                if not frame_files:
                    self.logger.error("No frames extracted from video")
                    return None
                
                frames = []
                durations = []
                frame_duration = 1.0 / fps  # Duration per frame
                
                for i, frame_file in enumerate(frame_files):
                    with Image.open(frame_file) as img:
                        # Resize & crop frame to fill the display
                        img = self._resize_and_crop(img)
                        
                        # Convert to RGB if needed
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # Save frame
                        frame_path = self._save_frame(img, frames_dir, i, format_type)
                        if frame_path:
                            frames.append(frame_path.name)
                            durations.append(frame_duration)
                
                if not frames:
                    self.logger.error("No frames were converted")
                    return None
                
                # Generate metadata
                metadata = {
                    "type": "video",
                    "slug": self._generate_slug(video_path.name),
                    "original_filename": video_path.name,
                    "width": self.target_width,
                    "height": self.target_height,
                    "frame_count": len(frames),
                    "frames": frames,
                    "durations": durations,
                    "format": format_type,
                    "fps": fps,
                    "loop_count": -1  # Infinite loop for videos
                }
                
                # Save metadata
                metadata_path = output_dir / "metadata.json"
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                self.logger.info(f"Converted video to {len(frames)} frames at {fps} FPS")
                return metadata
                
        except Exception as e:
            self.logger.error(f"Failed to convert video {video_path}: {e}")
            return None
    
    def convert_image(self, image_path: Path, output_dir: Path, format_type: str = "rgb565") -> Optional[Dict]:
        """Convert static image to single frame."""
        try:
            self.logger.info(f"Converting image: {image_path}")
            
            with Image.open(image_path) as img:
                # Resize & crop image
                img = self._resize_and_crop(img)
                
                # Ensure output directories exist
                output_dir.mkdir(parents=True, exist_ok=True)
                frames_dir = output_dir / "frames"
                frames_dir.mkdir(exist_ok=True)
                
                # Save single frame
                frame_path = self._save_frame(img, frames_dir, 0, format_type)
                if not frame_path:
                    return None
                
                # Generate metadata
                metadata = {
                    "type": "image",
                    "slug": self._generate_slug(image_path.name),
                    "original_filename": image_path.name,
                    "width": self.target_width,
                    "height": self.target_height,
                    "frame_count": 1,
                    "frames": [frame_path.name],
                    "durations": [0.0],  # Static image
                    "format": format_type,
                    "loop_count": 0
                }
                
                # Save metadata
                metadata_path = output_dir / "metadata.json"
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                self.logger.info("Converted image to single frame")
                return metadata
                
        except Exception as e:
            self.logger.error(f"Failed to convert image {image_path}: {e}")
            return None
    
    def _save_frame(self, frame: Image.Image, frames_dir: Path, frame_index: int, format_type: str) -> Optional[Path]:
        """Save a frame in the specified format."""
        try:
            if format_type == "rgb565":
                # Convert to RGB565 binary using fast NumPy operations
                frame_path = frames_dir / f"frame_{frame_index:06d}.rgb565"
                
                # Convert PIL image to NumPy array (much faster than getpixel loops)
                img_array = np.array(frame, dtype=np.uint8)
                
                # Ensure 3-channel RGB array (GIF frames can be single-channel)
                if img_array.ndim == 2:
                    img_array = np.stack([img_array] * 3, axis=-1)

                # Extract R, G, B channels
                r = img_array[:, :, 0].astype(np.uint16)
                g = img_array[:, :, 1].astype(np.uint16)
                b = img_array[:, :, 2].astype(np.uint16)
                
                # Convert to RGB565 using vectorized operations
                # RGB565: RRRRR GGGGGG BBBBB (5-6-5 bits)
                rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                
                # Convert to big-endian bytes and save
                rgb565_bytes = rgb565.astype('>u2').tobytes()
                
                with open(frame_path, 'wb') as f:
                    f.write(rgb565_bytes)
                
                return frame_path
                
            elif format_type == "jpeg":
                # Save as JPEG with quality optimization
                frame_path = frames_dir / f"frame_{frame_index:06d}.jpg"
                frame.save(frame_path, "JPEG", quality=85, optimize=True)
                return frame_path
                
            else:
                self.logger.error(f"Unknown format type: {format_type}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to save frame {frame_index}: {e}")
            return None
    
    def convert_media_file(self, input_path: Path, output_dir: Path, format_type: str = "rgb565", **kwargs) -> Optional[Dict]:
        """Auto-detect and convert media file."""
        if not input_path.exists():
            self.logger.error(f"Input file does not exist: {input_path}")
            return None
        
        # Determine file type by extension
        ext = input_path.suffix.lower()
        
        if ext == '.gif':
            return self.convert_gif(input_path, output_dir, format_type)
        elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            fps = kwargs.get('fps', 10.0)
            return self.convert_video(input_path, output_dir, format_type, fps)
        elif ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
            return self.convert_image(input_path, output_dir, format_type)
        else:
            self.logger.error(f"Unsupported file type: {ext}")
            return None
    
    # ---------------------------------------------------------------------
    # Image helpers
    # ---------------------------------------------------------------------

    def _resize_and_crop(self, img: Image.Image) -> Image.Image:
        """Resize *and* crop an image to exactly fill the target area.

        The image is first scaled preserving aspect-ratio so that *both* dimensions
        are **at least** the requested size.  Any excess is then cropped from the
        centre so the final result is exactly `(target_width, target_height)`.
        This mimics a typical `object-fit: cover` behaviour found in CSS which is
        ideal for making content completely fill the screen without letter-boxing
        or distortion.
        """

        return ImageOps.fit(
            img,
            (self.target_width, self.target_height),
            Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        ) 