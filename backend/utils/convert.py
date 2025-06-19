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
        # Remove extension and create hash-based slug
        name = Path(filename).stem
        hash_part = hashlib.md5(filename.encode()).hexdigest()[:8]
        return f"{name}_{hash_part}".lower().replace(' ', '_').replace('-', '_')
    
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
                    "frames": frames,
                    "durations": durations,
                    "format": format_type,
                    "loop_count": getattr(img, 'info', {}).get('loop', 0)  # 0 = infinite
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
            
            if format_type == "rgb565":
                # Direct RGB565 conversion with anti-tearing optimizations
                # This is MUCH faster than PNG intermediate files
                cmd = [
                    'ffmpeg', '-i', str(video_path),
                    '-vf', (
                        f'fps={fps},'
                        f'scale={self.target_width}:{self.target_height}:force_original_aspect_ratio=increase,'
                        f'crop={self.target_width}:{self.target_height}'
                    ),
                    '-pix_fmt', 'rgb24', # Use standard 24-bit RGB
                    '-preset', 'ultrafast',  # Prioritize speed
                    '-threads', '2',  # Use 2 threads for encoding
                    '-f', 'rawvideo',
                    '-y',  # Overwrite output files
                    str(frames_dir / 'frames.raw')
                ]
                
                self.logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                
                # Check for errors and provide detailed logging
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
                
                if job_id:
                    self._update_progress(job_id, 60, "processing", "Processing extracted frames...")
                
                # Split the raw video into individual frame files
                raw_file = frames_dir / 'frames.raw'
                if not raw_file.exists():
                    self.logger.error("No raw video data generated")
                    if job_id:
                        self._complete_job(job_id, False, "No raw video data generated")
                    return None
                
                frame_size = self.target_width * self.target_height * 3  # RGB24 = 3 bytes per pixel
                frames = []
                durations = []
                frame_duration = 1.0 / fps
                frame_index = 0
                
                raw_file_size = raw_file.stat().st_size
                estimated_frames = raw_file_size // frame_size
                
                with open(raw_file, 'rb') as f:
                    while True:
                        frame_data = f.read(frame_size)
                        if len(frame_data) != frame_size:
                            break
                        
                        if job_id and estimated_frames > 0:
                            progress = 60 + (frame_index / estimated_frames) * 20  # 60-80% for frame processing
                            self._update_progress(job_id, progress, "processing", f"Processing frame {frame_index + 1}/{estimated_frames}")
                        
                        # Create PIL image from raw RGB24 data
                        img = Image.frombytes('RGB', (self.target_width, self.target_height), frame_data)
                        
                        # Save individual frame using the reliable _save_frame method
                        frame_path = self._save_frame(img, frames_dir, frame_index, format_type)
                        
                        if frame_path:
                            frames.append(frame_path.name)
                            durations.append(frame_duration)
                        
                        frame_index += 1
                
                # Clean up raw file
                raw_file.unlink()
                
            else:
                # For JPEG format, use PNG intermediate (less efficient but works)
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    
                    # Extract frames using ffmpeg with proper aspect ratio handling
                    cmd = [
                        'ffmpeg', '-i', str(video_path),
                        '-vf', (
                            f'fps={fps},'
                            f'scale={self.target_width}:{self.target_height}:force_original_aspect_ratio=increase,'
                            f'crop={self.target_width}:{self.target_height}'
                        ),
                        '-pix_fmt', 'rgb565le', # Use little-endian as we will swap bytes
                        '-preset', 'ultrafast',  # Prioritize speed
                        '-threads', '2',  # Use 2 threads for encoding
                        '-f', 'rawvideo',
                        '-y',  # Overwrite output files
                        str(temp_path / 'frame_%06d.png')
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        self.logger.error(f"ffmpeg failed: {result.stderr}")
                        if job_id:
                            self._complete_job(job_id, False, f"ffmpeg failed: {result.stderr}")
                        return None
                    
                    if job_id:
                        self._update_progress(job_id, 60, "processing", "Converting extracted frames...")
                    
                    # Convert extracted frames (no need for _resize_and_crop since ffmpeg did it)
                    frame_files = sorted(temp_path.glob('frame_*.png'))
                    if not frame_files:
                        self.logger.error("No frames extracted from video")
                        if job_id:
                            self._complete_job(job_id, False, "No frames extracted from video")
                        return None
                    
                    frames = []
                    durations = []
                    frame_duration = 1.0 / fps
                    
                    for i, frame_file in enumerate(frame_files):
                        if job_id:
                            progress = 60 + (i / len(frame_files)) * 20  # 60-80% for frame processing
                            self._update_progress(job_id, progress, "processing", f"Processing frame {i + 1}/{len(frame_files)}")
                        
                        with Image.open(frame_file) as img:
                            # Convert to RGB if needed (no resizing needed!)
                            if img.mode != 'RGB':
                                img = img.convert('RGB')
                            
                            # Save frame directly (no cropping needed since ffmpeg handled it)
                            frame_path = self._save_frame(img, frames_dir, i, format_type)
                            if frame_path:
                                frames.append(frame_path.name)
                                durations.append(frame_duration)
            
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
    
    def convert_media_file(self, input_path: Path, output_dir: Path, format_type: str = "rgb565", job_id: str = None, **kwargs) -> Optional[Dict]:
        """Auto-detect and convert media file with optional progress tracking."""
        if not input_path.exists():
            self.logger.error(f"Input file does not exist: {input_path}")
            if job_id:
                self._complete_job(job_id, False, f"Input file does not exist: {input_path}")
            return None
        
        # Determine file type by extension
        ext = input_path.suffix.lower()
        
        # Get framerate from config for videos
        config = get_config()
        
        if ext == '.gif':
            return self.convert_gif(input_path, output_dir, format_type, job_id)
        elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            fps = kwargs.get('fps', config.display.framerate)
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