"""Media conversion utilities for GIF/video to RGB565 frames."""

import json
import struct
import subprocess
import shutil
import threading
import uuid
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Callable
from PIL import Image, ImageSequence, ImageOps
import tempfile
import hashlib
import numpy as np
import re  # Added for slug sanitization

from utils.logger import get_logger
from display.framebuf import FrameBuffer
from config.schema import get_config


class MediaConverter:
    """Convert media files to display-ready formats."""
    
    def __init__(self, target_width: int, target_height: int):
        """Initialize converter."""
        self.target_width = target_width
        self.target_height = target_height
        self.logger = get_logger("converter")
        
        # Pull gamma setting from global config (frontend slider updates config before upload)
        cfg = get_config()
        self.gamma: float = max(0.1, getattr(cfg.display, "gamma", 1.0))
        # Pre-compute 8-bit LUT for fast per-channel correction
        if abs(self.gamma - 1.0) < 0.05:
            self._gamma_lut = None  # No correction needed
        else:
            self._gamma_lut = (np.linspace(0, 1, 256) ** (1.0 / self.gamma) * 255).astype(np.uint8)

        # Check for ffmpeg availability
        self.ffmpeg_available = shutil.which('ffmpeg') is not None
        if not self.ffmpeg_available:
            self.logger.warning("ffmpeg not found - video conversion will be limited")
    
    def _update_progress(self, job_id: str, progress: float, stage: str, message: str = ""):
        """Update progress for a job using media_index."""
        if job_id:
            from utils.media_index import media_index
            media_index.update_processing_job(job_id, progress, stage, message)
    
    def _complete_job(self, job_id: str, success: bool, error: str = "") -> None:
        """Mark a job as completed using media_index."""
        if job_id:
            from utils.media_index import media_index
            media_index.complete_processing_job(job_id, success, error)
    
    def _generate_slug(self, filename: str) -> str:
        """Generate URL-safe slug from filename."""
        # Remove extension and sanitize name by stripping typical tempfile prefixes
        name = Path(filename).stem

        # Many uploads arrive with names like "tmpabcd123_myfile.gif" created by the
        # operating system's tempfile utilities.  Remove the leading tmp* segment so
        # the slug is more readable while still appending an 8-char hash for
        # deduplication.
        cleaned_name = re.sub(r"^tmp[a-zA-Z0-9]+(?:[_-])?", "", name)
        if not cleaned_name:
            cleaned_name = "media"

        # Append deterministic hash to guarantee uniqueness while remaining concise
        hash_part = hashlib.md5(filename.encode()).hexdigest()[:8]
        return f"{cleaned_name}_{hash_part}".lower().replace(' ', '_').replace('-', '_')
    
    def convert_gif(self, gif_path: Path, output_dir: Path, format_type: str = "rgb565", job_id: str = None) -> Optional[Dict]:
        """Convert GIF to frame sequence."""
        try:
            if job_id:
                self._update_progress(job_id, 10, "analyzing", "Analyzing GIF structure...")
            
            self.logger.info(f"Converting GIF: {gif_path}")
            
            with Image.open(gif_path) as img:
                if not hasattr(img, 'is_animated') or not img.is_animated:
                    self.logger.error("File is not an animated GIF")
                    if job_id:
                        self._complete_job(job_id, False, "File is not an animated GIF")
                    return None
                
                if job_id:
                    self._update_progress(job_id, 20, "preparing", "Preparing frame extraction...")
                
                frames = []
                durations = []
                
                output_dir.mkdir(parents=True, exist_ok=True)
                frames_dir = output_dir / "frames"
                frames_dir.mkdir(exist_ok=True)
                
                frame_count = getattr(img, 'n_frames', 0)
                self.logger.info(f"Processing {frame_count} frames")
                
                processed_frames = 0
                for frame in ImageSequence.Iterator(img):
                    if job_id:
                        progress = 20 + (processed_frames / frame_count) * 60  # 20-80% for frame processing
                        self._update_progress(job_id, progress, "processing", f"Processing frame {processed_frames + 1}/{frame_count}")
                    
                    # Resize & crop frame to fill the display (proper aspect ratio handling)
                    frame = self._resize_and_crop(frame)
                    
                    # Save frame
                    frame_path = self._save_frame(frame, frames_dir, processed_frames, format_type)
                    if frame_path:
                        frames.append(frame_path.name)
                        
                        # Get frame duration (convert from milliseconds to seconds)
                        duration = frame.info.get('duration', 100) / 1000.0
                        durations.append(duration)
                        
                        processed_frames += 1
                
                if not frames:
                    self.logger.error("No frames were converted")
                    if job_id:
                        self._complete_job(job_id, False, "No frames were converted")
                    return None
                
                if job_id:
                    self._update_progress(job_id, 90, "finalizing", "Generating metadata...")
                
                # Generate metadata
                metadata = {
                    "type": "gif",
                    "slug": self._generate_slug(gif_path.name),
                    "original_filename": gif_path.name,
                    "width": self.target_width,
                    "height": self.target_height,
                    "frame_count": processed_frames,
                    "frame_duration": durations[0] if durations else 0.1,  # Use first duration as default
                    "format": format_type,
                    "loop_count": getattr(img, 'info', {}).get('loop', 0),  # 0 = infinite
                    "_optimized": True  # Flag to indicate this uses optimized format
                }
                
                # Save metadata
                metadata_path = output_dir / "metadata.json"
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                self.logger.info(f"Converted GIF to {processed_frames} frames")
                
                if job_id:
                    self._complete_job(job_id, True)
                
                return metadata
                
        except Exception as e:
            self.logger.error(f"Failed to convert GIF {gif_path}: {e}")
            if job_id:
                self._complete_job(job_id, False, str(e))
            return None
    
    def convert_video(self, video_path: Path, output_dir: Path, format_type: str = "rgb565", fps: float = 25.0, job_id: str = None) -> Optional[Dict]:
        """Convert video to frame sequence using ffmpeg with proper aspect ratio handling."""
        if not self.ffmpeg_available:
            error_msg = "ffmpeg not available for video conversion. Install with: sudo apt-get install ffmpeg"
            self.logger.error(error_msg)
            if job_id:
                self._complete_job(job_id, False, error_msg)
            return None
        
        try:
            if job_id:
                self._update_progress(job_id, 10, "analyzing", "Analyzing video...")
            
            self.logger.info(f"Converting video: {video_path}")
            
            output_dir.mkdir(parents=True, exist_ok=True)
            frames_dir = output_dir / "frames"
            frames_dir.mkdir(exist_ok=True)
            
            if job_id:
                self._update_progress(job_id, 20, "extracting", "Extracting frames with ffmpeg...")
            
            # Use converter-wide gamma setting
            gamma = self.gamma

            filter_str = (
                f"fps={fps},"
                "format=rgb24,"
                f"eq=gamma={gamma:.2f},"
                "dither=bayer:bayer_scale=5,"
                f"scale={self.target_width}:{self.target_height}:force_original_aspect_ratio=increase,"
                f"crop={self.target_width}:{self.target_height},"
                "format=rgb565be"
            )

            cmd = [
                'ffmpeg', '-i', str(video_path),
                '-vf', filter_str,
                '-pix_fmt', 'rgb565be',
                '-vcodec', 'rawvideo',
                '-preset', 'ultrafast',
                '-threads', '4',
                '-f', 'image2',
                '-y',
                str(frames_dir / 'frame_%06d.rgb565')
            ]

            self.logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)

            if result.returncode != 0:
                error_msg = (
                    f"ffmpeg failed with exit code {result.returncode}.\n"
                    f"Stderr: {result.stderr.strip() if result.stderr else 'N/A'}\n"
                    f"Stdout: {result.stdout.strip() if result.stdout else 'N/A'}"
                )
                self.logger.error(error_msg)
                if job_id:
                    self._complete_job(job_id, False, f"ffmpeg error: {result.stderr.strip()}")
                return None

            # Collect generated frame files
            frames = [p.name for p in sorted(frames_dir.glob('frame_*.rgb565'))]
            if not frames:
                self.logger.error("No frames were generated by ffmpeg")
                if job_id:
                    self._complete_job(job_id, False, "No frames generated")
                return None

            frame_duration = 1.0 / fps
            durations = [frame_duration] * len(frames)
            
            if not frames:
                self.logger.error("No frames were converted")
                if job_id:
                    self._complete_job(job_id, False, "No frames were converted")
                return None
            
            if job_id:
                self._update_progress(job_id, 90, "finalizing", "Generating metadata...")
            
            # Generate metadata
            metadata = {
                "type": "video",
                "slug": self._generate_slug(video_path.name),
                "original_filename": video_path.name,
                "width": self.target_width,
                "height": self.target_height,
                "frame_count": len(frames),
                "fps": fps,
                "frame_duration": frame_duration,
                "format": format_type,
                "loop_count": -1,  # Infinite loop for videos
                "_optimized": True  # Flag to indicate this uses optimized format
            }
            
            # Save metadata
            metadata_path = output_dir / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"Converted video to {len(frames)} frames at {fps} FPS")
            
            if job_id:
                self._complete_job(job_id, True)
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to convert video {video_path}: {e}")
            if job_id:
                self._complete_job(job_id, False, str(e))
            return None
    
    def convert_image(self, image_path: Path, output_dir: Path, format_type: str = "rgb565", job_id: str = None) -> Optional[Dict]:
        """Convert static image to single frame."""
        try:
            if job_id:
                self._update_progress(job_id, 10, "analyzing", "Analyzing image...")
            
            self.logger.info(f"Converting image: {image_path}")
            
            with Image.open(image_path) as img:
                if job_id:
                    self._update_progress(job_id, 30, "processing", "Resizing and cropping...")
                
                # Resize & crop image
                img = self._resize_and_crop(img)
                
                # Ensure output directories exist
                output_dir.mkdir(parents=True, exist_ok=True)
                frames_dir = output_dir / "frames"
                frames_dir.mkdir(exist_ok=True)
                
                if job_id:
                    self._update_progress(job_id, 60, "saving", "Saving processed frame...")
                
                # Save single frame
                frame_path = self._save_frame(img, frames_dir, 0, format_type)
                if not frame_path:
                    if job_id:
                        self._complete_job(job_id, False, "Failed to save frame")
                    return None
                
                if job_id:
                    self._update_progress(job_id, 90, "finalizing", "Generating metadata...")
                
                # Generate metadata
                metadata = {
                    "type": "image",
                    "slug": self._generate_slug(image_path.name),
                    "original_filename": image_path.name,
                    "width": self.target_width,
                    "height": self.target_height,
                    "frame_count": 1,
                    "frame_duration": 0.0,  # Static image
                    "format": format_type,
                    "loop_count": 0,
                    "_optimized": True  # Flag to indicate this uses optimized format
                }
                
                # Save metadata
                metadata_path = output_dir / "metadata.json"
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                self.logger.info("Converted image to single frame")
                
                if job_id:
                    self._complete_job(job_id, True)
                
                return metadata
                
        except Exception as e:
            self.logger.error(f"Failed to convert image {image_path}: {e}")
            if job_id:
                self._complete_job(job_id, False, str(e))
            return None
    
    def _save_frame(self, frame: Image.Image, frames_dir: Path, frame_index: int, format_type: str) -> Optional[Path]:
        """Save a frame in the specified format."""
        try:
            if format_type == "rgb565":
                # Ensure RGB mode to avoid palette/grayscale misinterpretation
                if frame.mode != 'RGB':
                    frame = frame.convert('RGB')

                # Convert PIL image to NumPy array (much faster than getpixel loops)
                img_array = np.array(frame, dtype=np.uint8)
                
                # Apply gamma correction using LUT if needed (per-channel)
                if self._gamma_lut is not None:
                    img_array = self._gamma_lut[img_array]

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
                
                frame_path = frames_dir / f"frame_{frame_index:06d}.rgb565"
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
    
    def convert_media_file(self, input_path: Path, output_dir: Path, format_type: str = "rgb565", job_id: str = None, **kwargs) -> Optional[Dict]:
        """Auto-detect and convert media file with optional progress tracking."""
        if not input_path.exists():
            self.logger.error(f"Input file does not exist: {input_path}")
            if job_id:
                self._complete_job(job_id, False, f"Input file does not exist: {input_path}")
            return None
        
        # Determine file type by extension
        ext = input_path.suffix.lower()
        
        # Get framerate from kwargs for videos
        if ext == '.gif':
            return self.convert_gif(input_path, output_dir, format_type, job_id)
        elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            fps = kwargs.get('fps', 25.0) # Default to 25.0 if not provided
            return self.convert_video(input_path, output_dir, format_type, fps, job_id)
        elif ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
            return self.convert_image(input_path, output_dir, format_type, job_id)
        else:
            self.logger.error(f"Unsupported file type: {ext}")
            if job_id:
                self._complete_job(job_id, False, f"Unsupported file type: {ext}")
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