# backend/display/player.py

import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont
import io

from config.schema import DisplayConfig, MediaConfig
from display.framebuf import FrameSequence, FrameDecoder, FrameBuffer
from display.spiout import ILI9341Driver
from utils.logger import get_logger
from utils.media_index import media_index


class DisplayPlayer:
    """Main display playback engine."""
    
    def __init__(self, display_driver: ILI9341Driver, 
                 display_config: DisplayConfig, 
                 media_config: MediaConfig):
        """Initialize the display player."""
        self.display_driver = display_driver
        self.display_config = display_config
        self.media_config = media_config
        self.logger = get_logger("player")
        
        # Media management - SIMPLIFIED: no more caching
        self.media_dir = Path("media/processed")
        self.current_sequence: Optional[FrameSequence] = None
        
        # Playback control
        self.running = False
        self.paused = False
        self.frame_rate = display_config.framerate
        self.loop_count = media_config.loop_count
        self.loop_mode = "all"  # "all" or "one"
        
        # Per-media loop tracking
        self.current_media_loops = 0  # How many times current media has looped
        self.static_image_display_time = float(media_config.static_image_duration_sec)  # Configurable static image duration
        
        # Processing progress display
        self.showing_progress = False
        self.progress_thread: Optional[threading.Thread] = None
        self.progress_stop_event = threading.Event()
        
        # Event-based pause handling (eliminates busy-waiting)
        self.pause_event = threading.Event()
        self.pause_event.set()  # Start unpaused
        
        # Threading
        self.playback_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # Status display
        self.frame_buffer = FrameBuffer(display_config.width, display_config.height)
        
        # Pre-generate status message frames for performance (no runtime PIL operations)
        self._status_frames = self._pregenerate_status_frames()
        
        self.logger.info("Display player initialized (simplified architecture)")
    
    def _wait_interruptible(self, duration: float) -> bool:
        """Wait for duration but return immediately if interrupted or paused.
        
        Returns:
            True if wait completed normally, False if interrupted
        """
        if duration <= 0:
            return True
        
        # Wait for pause to be cleared (if paused)
        if not self.pause_event.wait(timeout=duration):
            return False  # Interrupted by pause
        
        # If not paused, do the actual wait with interrupt checking
        start_time = time.time()
        while time.time() - start_time < duration:
            if not self.running or self.showing_progress:
                return False  # Interrupted
            
            # Check if we got paused during the wait
            if not self.pause_event.is_set():
                # We got paused, wait for unpause
                if not self.pause_event.wait(timeout=0.1):
                    continue  # Still paused, check again
            
            # Sleep for remainder or 0.1s max to stay responsive
            remaining = duration - (time.time() - start_time)
            sleep_time = min(remaining, 0.1)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        return True  # Completed normally
    
    def _pregenerate_status_frames(self) -> Dict[str, bytes]:
        """Pre-generate common status message frames to avoid runtime PIL operations."""
        frames = {}
        
        # Common status messages to pre-generate
        messages = [
            ("No Media", "Add media files to start playback"),
            ("Processing", "Converting media files..."),
            ("Paused", "Playback paused"),
            ("Loading", "Loading media..."),
            ("Error", "Media playback error")
        ]
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            for title, subtitle in messages:
                # Create image
                image = Image.new('RGB', (self.display_config.width, self.display_config.height), (0, 0, 0))
                draw = ImageDraw.Draw(image)
                
                # Try to load fonts
                try:
                    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
                    subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
                except (OSError, IOError):
                    try:
                        title_font = ImageFont.load_default()
                        subtitle_font = ImageFont.load_default()
                    except (OSError, IOError) as e:
                        self.logger.debug(f"Default font loading failed: {e}")
                        title_font = None
                        subtitle_font = None
                
                if title_font and subtitle_font:
                    # Draw title
                    title_bbox = draw.textbbox((0, 0), title, font=title_font)
                    title_width = title_bbox[2] - title_bbox[0]
                    title_x = (self.display_config.width - title_width) // 2
                    title_y = self.display_config.height // 2 - 30
                    draw.text((title_x, title_y), title, fill=(255, 255, 255), font=title_font)
                    
                    # Draw subtitle
                    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
                    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
                    subtitle_x = (self.display_config.width - subtitle_width) // 2
                    subtitle_y = title_y + 35
                    draw.text((subtitle_x, subtitle_y), subtitle, fill=(200, 200, 200), font=subtitle_font)
                
                # Convert to RGB565 bytes directly (no PNG conversion)
                import numpy as np
                img_array = np.array(image, dtype=np.uint8)
                r = img_array[:, :, 0].astype(np.uint16)
                g = img_array[:, :, 1].astype(np.uint16)
                b = img_array[:, :, 2].astype(np.uint16)
                rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
                frame_data = rgb565.astype('>u2').tobytes()
                
                frames[title.lower()] = frame_data
                
        except Exception as e:
            self.logger.warning(f"Failed to pre-generate status frames: {e}")
            # Return empty dict - fallback to basic display
            return {}
        
        self.logger.info(f"Pre-generated {len(frames)} status message frames")
        return frames
    
    def get_current_loop_media(self) -> List[Dict]:
        """Get current loop media from authoritative source."""
        loop_slugs = media_index.list_loop()
        media_dict = media_index.get_media_dict()
        return [media_dict[slug] for slug in loop_slugs if slug in media_dict]
    
    def get_current_media_index(self) -> int:
        """Get index of currently active media in loop."""
        active_slug = media_index.get_active()
        if not active_slug:
            return 0
        
        loop_slugs = media_index.list_loop()
        try:
            return loop_slugs.index(active_slug)
        except ValueError:
            return 0
    
    def get_current_media_slug(self) -> Optional[str]:
        """Get the slug of the currently active media."""
        return media_index.get_active()
    
    def load_current_sequence(self) -> bool:
        """Load the current media sequence."""
        # Stop previous sequence's producer thread before starting a new one
        if self.current_sequence:
            self.current_sequence.stop()
            self.current_sequence = None

        loop_media = self.get_current_loop_media()
        current_index = self.get_current_media_index()
        
        if not loop_media or current_index >= len(loop_media):
            self.logger.warning("No media available to load")
            return False
        
        media_info = loop_media[current_index]
        media_slug = media_info.get('slug')
        
        if not media_slug:
            self.logger.error("Media has no slug")
            return False
        
        frames_dir = self.media_dir / media_slug / "frames"
        
        if not frames_dir.exists():
            self.logger.error(f"Frames directory not found: {frames_dir}")
            return False
        
        try:
            # Get frames and durations from media info
            frames = media_info.get('frames', [])
            durations = media_info.get('durations', [])
            
            if not frames:
                self.logger.error("No frames found in media info")
                return False
            
            # Create frame sequence with frames and durations
            self.current_sequence = FrameSequence(
                frames_dir,
                frames,
                durations
            )
            
            if self.current_sequence.get_frame_count() == 0:
                self.logger.error(f"No frames found in {frames_dir}")
                return False
            
            self.logger.info(f"Loaded media: {media_info.get('original_filename', media_slug)}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load sequence: {e}")
            return False
    
    def next_media(self) -> None:
        """Switch to next media."""
        with self.lock:
            # Stop the producer thread of the current sequence
            if self.current_sequence:
                self.current_sequence.stop()
                self.current_sequence = None

            loop_slugs = media_index.list_loop()
            
            if len(loop_slugs) <= 1:
                return
            
            current_slug = media_index.get_active()
            try:
                current_index = loop_slugs.index(current_slug) if current_slug else 0
            except ValueError:
                current_index = 0
            
            # Move to next item in loop
            next_index = (current_index + 1) % len(loop_slugs)
            next_slug = loop_slugs[next_index]
            
            # Set as active - sequence will be loaded in main loop
            media_index.set_active(next_slug)
            media_dict = media_index.get_media_dict()
            media_name = media_dict.get(next_slug, {}).get('original_filename', 'Unknown')
            self.logger.info(f"Switched to next media: {media_name}")
    
    def previous_media(self) -> None:
        """Switch to previous media."""
        with self.lock:
            # Stop the producer thread of the current sequence
            if self.current_sequence:
                self.current_sequence.stop()
                self.current_sequence = None

            loop_slugs = media_index.list_loop()
            
            if len(loop_slugs) <= 1:
                return
            
            current_slug = media_index.get_active()
            try:
                current_index = loop_slugs.index(current_slug) if current_slug else 0
            except ValueError:
                current_index = 0
            
            # Move to previous item in loop
            prev_index = (current_index - 1) % len(loop_slugs)
            prev_slug = loop_slugs[prev_index]
            
            # Set as active - sequence will be loaded in main loop
            media_index.set_active(prev_slug)
            media_dict = media_index.get_media_dict()
            media_name = media_dict.get(prev_slug, {}).get('original_filename', 'Unknown')
            self.logger.info(f"Switched to previous media: {media_name}")
    
    def set_active_media(self, slug: str) -> bool:
        """Set the active media to the specified slug."""
        with self.lock:
            # Stop the producer thread of the current sequence
            if self.current_sequence:
                self.current_sequence.stop()

            # Check if slug exists in media
            media_dict = media_index.get_media_dict()
            if slug not in media_dict:
                self.logger.warning(f"Media with slug '{slug}' not found")
                return False
            
            # Set as active and clear current sequence to trigger reload
            media_index.set_active(slug)
            self.current_sequence = None  # Force reload on next cycle
            media_name = media_dict.get(slug, {}).get('original_filename', 'Unknown')
            self.logger.info(f"Set active media: {media_name}")
            return True
    
    def toggle_pause(self) -> None:
        """Toggle playback pause state."""
        with self.lock:
            self.paused = not self.paused
            if self.paused:
                self.pause_event.clear()  # Block playback
            else:
                self.pause_event.set()    # Resume playback
            self.logger.info(f"Playback {'paused' if self.paused else 'resumed'}")
    
    def is_paused(self) -> bool:
        """Check if playback is paused."""
        return self.paused
    
    def toggle_loop_mode(self) -> str:
        """Toggle between 'all' and 'one' loop modes."""
        with self.lock:
            self.loop_mode = "one" if self.loop_mode == "all" else "all"
            self.logger.info(f"Loop mode changed to: {self.loop_mode}")
            return self.loop_mode
    
    def get_loop_mode(self) -> str:
        """Get current loop mode."""
        return self.loop_mode
    
    def show_message(self, message: str, duration: float = 2.0, color: int = 0xFFFF) -> None:
        """Display a message on screen temporarily using pre-generated frames."""
        try:
            # Try to use pre-generated frame first (MUCH faster - no PIL operations)
            message_key = message.lower()
            if message_key in self._status_frames:
                frame_data = self._status_frames[message_key]
                self.display_driver.display_frame(frame_data)
                if duration > 0:
                    time.sleep(duration)
                return
            
            # Fallback to simple colored fill for unknown messages (fast)
            self.display_driver.fill_screen(0x0000)  # Black background
            if duration > 0:
                time.sleep(duration)
            
        except Exception as e:
            self.logger.error(f"Failed to show message: {e}")
    
    def show_progress_bar(self, title: str, subtitle: str, progress: float, color: Optional[int] = None) -> None:
        """Display a progress bar with title and subtitle."""
        # Use configured color if none provided
        if color is None:
            color = self.display_config.progress_color
        try:
            # Create image
            image = Image.new('RGB', (self.display_config.width, self.display_config.height), (0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Try to load fonts
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
                subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            except (OSError, IOError):
                try:
                    title_font = ImageFont.load_default()
                    subtitle_font = ImageFont.load_default()
                except (OSError, IOError) as e:
                    self.logger.debug(f"Default font loading failed: {e}")
                    title_font = None
                    subtitle_font = None
            
            # Convert RGB565 color to RGB888
            if isinstance(color, int):
                r = (color >> 11) << 3
                g = ((color >> 5) & 0x3F) << 2
                b = (color & 0x1F) << 3
                rgb_color = (r, g, b)
            else:
                rgb_color = color
            
            # Draw title
            if title_font:
                bbox = draw.textbbox((0, 0), title, font=title_font)
                title_width = bbox[2] - bbox[0]
                title_x = (self.display_config.width - title_width) // 2
                title_y = 40
                draw.text((title_x, title_y), title, fill=(255, 255, 255), font=title_font)
            
            # Draw subtitle
            if subtitle_font and subtitle:
                bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
                subtitle_width = bbox[2] - bbox[0]
                subtitle_x = (self.display_config.width - subtitle_width) // 2
                subtitle_y = 80
                draw.text((subtitle_x, subtitle_y), subtitle, fill=(200, 200, 200), font=subtitle_font)
            
            # Draw progress bar
            bar_width = 180
            bar_height = 20
            bar_x = (self.display_config.width - bar_width) // 2
            bar_y = 140
            
            # Progress bar background
            draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], 
                         outline=(100, 100, 100), fill=(30, 30, 30))
            
            # Progress bar fill
            fill_width = int((progress / 100.0) * bar_width)
            if fill_width > 0:
                draw.rectangle([bar_x, bar_y, bar_x + fill_width, bar_y + bar_height], 
                             fill=rgb_color)
            
            # Progress percentage
            progress_text = f"{int(progress)}%"
            if title_font:
                bbox = draw.textbbox((0, 0), progress_text, font=title_font)
                progress_width = bbox[2] - bbox[0]
                progress_x = (self.display_config.width - progress_width) // 2
                progress_y = 180
                draw.text((progress_x, progress_y), progress_text, fill=(255, 255, 255), font=title_font)
            
            # Convert to RGB565 format
            decoder = FrameDecoder(self.display_config.width, self.display_config.height)
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            frame_data = decoder.decode_image_bytes(buffer.getvalue())
            buffer.close()
            
            if frame_data:
                self.display_driver.display_frame(frame_data)
            
        except Exception as e:
            self.logger.error(f"Failed to show progress bar: {e}")
    
    def start_processing_display(self, job_ids: List[str]) -> None:
        """Start displaying processing progress for given job IDs."""
        self.logger.info(f"start_processing_display called with job_ids: {job_ids}")
        
        # Check if progress display is enabled in config
        if not self.display_config.show_progress:
            self.logger.warning("Processing progress display disabled in config")
            return
        
        if self.showing_progress:
            self.logger.info("Progress display already showing, stopping previous")
            self.stop_processing_display()
        
        self.showing_progress = True
        self.progress_stop_event.clear()
        
        self.progress_thread = threading.Thread(
            target=self._processing_display_loop, 
            args=(job_ids,),
            daemon=True
        )
        self.progress_thread.start()
        self.logger.info(f"✅ Started processing display thread for {len(job_ids)} jobs")
    
    def stop_processing_display(self) -> None:
        """Stop displaying processing progress."""
        if self.showing_progress:
            self.showing_progress = False
            self.progress_stop_event.set()
            
            if self.progress_thread:
                self.progress_thread.join(timeout=2)
                if self.progress_thread.is_alive():
                    self.logger.warning("Processing display thread did not stop gracefully")
            
            self.logger.info("Stopped processing display")
    
    def _processing_display_loop(self, job_ids: List[str]) -> None:
        """Loop that displays processing progress."""
        try:
            self.logger.info(f"🎨 Processing display loop started for jobs: {job_ids}")
            
            # Immediately show initial progress to take over display
            self.show_progress_bar("Processing Media", "Starting conversion...", 0)
            self.logger.info("📊 Showed initial progress bar")
            
            while not self.progress_stop_event.is_set():
                # Get processing jobs
                processing_jobs = media_index.list_processing_jobs()
                
                # Filter to our job IDs
                relevant_jobs = {
                    job_id: job_data for job_id, job_data in processing_jobs.items()
                    if job_id in job_ids
                }
                
                if not relevant_jobs:
                    self.logger.info("No relevant jobs found, stopping display loop")
                    break
                
                # Calculate overall progress
                total_jobs = len(job_ids)
                completed_jobs = sum(1 for job in relevant_jobs.values() 
                                   if job.get('status') in ['completed', 'error'])
                
                if total_jobs > 0:
                    overall_progress = (completed_jobs / total_jobs) * 100
                else:
                    overall_progress = 100
                
                # Find an active job for current status
                active_job = None
                for job in relevant_jobs.values():
                    if job.get('status') == 'processing':
                        active_job = job
                        break
                
                if active_job:
                    # Show individual job progress
                    title = "Processing Media"
                    subtitle = f"{active_job.get('stage', 'Processing')}"
                    if 'message' in active_job and active_job['message']:
                        subtitle = active_job['message'][:30] + "..." if len(active_job['message']) > 30 else active_job['message']
                    
                    job_progress = active_job.get('progress', 0)
                    self.show_progress_bar(title, subtitle, job_progress)
                else:
                    # Show overall progress
                    title = "Processing Media"
                    subtitle = f"Completed {completed_jobs}/{total_jobs} files"
                    self.show_progress_bar(title, subtitle, overall_progress)
                
                # Check if all jobs are completed
                all_completed = all(
                    job.get('status') in ['completed', 'error'] 
                    for job in relevant_jobs.values()
                )
                
                if all_completed:
                    # Show completion message briefly
                    self.show_progress_bar("Processing Complete", 
                                         f"Processed {total_jobs} files", 100)
                    time.sleep(2)
                    break
                
                # Wait before next update
                if not self.progress_stop_event.wait(1.0):  # 1 second update interval
                    continue
                else:
                    break
                    
        except Exception as e:
            self.logger.error(f"Error in processing display loop: {e}")
        finally:
            self.showing_progress = False
    
    def show_no_media_message(self) -> None:
        """Show a message when no media is available."""
        self.show_message("No Media", duration=0, color=0x07E0)  # Green text - matches pre-generated frame
    
    def run(self) -> None:
        """Main playback loop - FIXED to respect loop counts and proper timing."""
        self.logger.info("Starting fixed playback loop")
        
        while self.running:
            try:
                # Don't interfere with processing display
                if self.showing_progress:
                    time.sleep(0.5)
                    continue
                
                # Get current loop state fresh every cycle
                loop_slugs = media_index.list_loop()
                
                # Check if we have media to play
                if not loop_slugs:
                    self.show_no_media_message()
                    time.sleep(1)
                    continue
                
                # Load current sequence if needed
                if not self.current_sequence:
                    if not self.load_current_sequence():
                        # Failed to load, try next media or wait
                        if len(loop_slugs) > 1:
                            self.next_media()
                        else:
                            time.sleep(1)
                        continue
                    # Reset loop counter when loading new media
                    self.current_media_loops = 0
                
                # Play current media sequence
                if not self.current_sequence:
                    self.logger.warning("Current sequence is None, attempting to reload")
                    if not self.load_current_sequence():
                        time.sleep(1)
                        continue
                
                frame_count = self.current_sequence.get_frame_count()
                is_static_image = frame_count == 1 and self.current_sequence.get_frame_duration(0) == 0.0
                
                if is_static_image:
                    # Display static image for the configured duration
                    frame_data = self.current_sequence.get_next_frame(timeout=2.0)
                    if frame_data:
                        self.logger.info(f"Displaying static image for {self.static_image_display_time} seconds")
                        self.display_driver.display_frame(frame_data)
                        
                        # Efficient interruptible wait (no busy-waiting)
                        start_time = time.time()
                        wait_completed = self._wait_interruptible(self.static_image_display_time)
                        actual_time = time.time() - start_time
                        
                        if wait_completed:
                            self.logger.info(f"Static image display completed after {actual_time:.1f}s")
                        else:
                            self.logger.info(f"Static image interrupted after {actual_time:.1f}s")
                else:
                    # Play all frames in animated sequence
                    sequence_completed = True
                    frame_times = []  # Track frame performance for diagnostics
                    
                    for frame_idx in range(frame_count):
                        frame_start = time.time()
                        
                        if not self.running:
                            sequence_completed = False
                            break
                        
                        # Don't interfere with processing display
                        if self.showing_progress:
                            sequence_completed = False
                            break
                        
                        # Handle pause efficiently (no busy-waiting)
                        if self.paused and self.running and not self.showing_progress:
                            self.pause_event.wait()  # Block until unpaused
                        
                        if not self.running or self.showing_progress:
                            sequence_completed = False
                            break
                        
                        # Get frame data and duration
                        frame_data = self.current_sequence.get_next_frame(timeout=2.0)
                        frame_duration = self.current_sequence.get_frame_duration(frame_idx)
                        
                        if not frame_data:
                            self.logger.error(f"Failed to get frame {frame_idx} from queue")
                            sequence_completed = False
                            break
                        
                        # CRITICAL PATH: Display frame as fast as possible
                        display_start = time.time()
                        self.display_driver.display_frame(frame_data)
                        display_time = time.time() - display_start
                        
                        # FRAME TIMING: Use the most restrictive timing (either media duration or framerate)
                        if frame_duration > 0:
                            # Media has specific timing (GIF frames)
                            target_frame_time = frame_duration
                        else:
                            # Use configured framerate
                            target_frame_time = 1.0 / self.frame_rate
                        
                        # Calculate remaining sleep time after display
                        sleep_time = max(0, target_frame_time - display_time)
                        
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                        
                        # Performance tracking
                        total_frame_time = time.time() - frame_start
                        frame_times.append((display_time, total_frame_time))
                        
                        # Log performance every 30 frames for diagnostics
                        if len(frame_times) >= 30:
                            avg_display = sum(times[0] for times in frame_times) / len(frame_times)
                            avg_total = sum(times[1] for times in frame_times) / len(frame_times)
                            actual_fps = 1.0 / avg_total if avg_total > 0 else 0
                            self.logger.debug(f"Frame performance: {actual_fps:.1f} FPS (display: {avg_display*1000:.1f}ms, total: {avg_total*1000:.1f}ms)")
                            frame_times = []  # Reset for next batch
                    
                    if not sequence_completed:
                        continue  # Skip loop logic if sequence was interrupted
                
                # Increment loop counter after completing one full playthrough
                self.current_media_loops += 1
                self.logger.info(f"Completed loop {self.current_media_loops}/{self.loop_count if self.loop_count > 0 else '∞'} of current media")
                
                # Decide what to do next based on loop configuration
                should_continue_current_media = True
                
                if self.loop_mode == "one":
                    # Loop one mode - check if we should keep looping this media
                    if self.loop_count > 0 and self.current_media_loops >= self.loop_count:
                        # Finished required loops for this media, but stay on it
                        self.current_media_loops = 0  # Reset for next round
                    # Always continue with same media in "one" mode
                    should_continue_current_media = True
                else:
                    # Loop all mode - check if we should move to next media
                    current_loop_slugs = media_index.list_loop()  # Re-check in case it changed
                    
                    if len(current_loop_slugs) <= 1:
                        # Only one media item - keep looping it
                        if self.loop_count > 0 and self.current_media_loops >= self.loop_count:
                            self.current_media_loops = 0  # Reset for next round
                        should_continue_current_media = True
                    else:
                        # Multiple media items - check if we should switch
                        if not self.media_config.auto_advance_enabled:
                            # Auto-advance disabled - stay on current media
                            should_continue_current_media = True
                        elif self.loop_count <= 0:
                            # Infinite loops - play each media once then move to next
                            should_continue_current_media = False
                        elif self.current_media_loops >= self.loop_count:
                            # Completed required loops - move to next
                            should_continue_current_media = False
                        else:
                            # Still need more loops of current media
                            should_continue_current_media = True
                
                if not should_continue_current_media:
                    # Time to switch to next media
                    self.logger.info(f"Switching to next media (mode: {self.loop_mode}, loops completed: {self.current_media_loops})")
                    self.next_media()
                    # Clear current sequence to force reload of next media
                    self.current_sequence = None
                    self.current_media_loops = 0
                else:
                    # Continue with same media - just loop again (no sequence reload needed)
                    self.logger.debug(f"Continuing current media loop (mode: {self.loop_mode})")
                
            except Exception as e:
                self.logger.error(f"Error in playback loop: {e}")
                time.sleep(1)
        
        self.logger.info("Playback loop ended")
    
    def start(self) -> None:
        """Start the display player."""
        if not self.running:
            self.running = True
            self.playback_thread = threading.Thread(target=self.run, daemon=True)
            self.playback_thread.start()
            self.logger.info("Display player started")
    
    def stop(self) -> None:
        """Stop the display player."""
        if self.running:
            self.running = False
            self.stop_processing_display()  # Stop progress display too
            
            # Stop the frame producer thread
            if self.current_sequence:
                self.current_sequence.stop()
                self.current_sequence = None

            if self.playback_thread:
                self.playback_thread.join(timeout=5)
                if self.playback_thread.is_alive():
                    self.logger.warning("Playback thread did not stop gracefully")
            self.logger.info("Display player stopped")
    
    def get_status(self) -> Dict:
        """Get current playback status."""
        current_media = media_index.get_active()
        loop_slugs = media_index.list_loop()
        current_index = self.get_current_media_index()
        
        return {
            "is_playing": self.running and not self.paused,
            "current_media": current_media,
            "loop_index": current_index,
            "total_media": len(loop_slugs),
            "frame_rate": self.frame_rate,
            "loop_mode": self.loop_mode,
            "showing_progress": self.showing_progress
        }
    
    def refresh_media_list(self) -> None:
        """Refresh the media list - now just clears current sequence to force reload."""
        self.logger.info("Refreshing media list (clearing current sequence)")
        with self.lock:
            # Simply clear the current sequence to force reload on next cycle
            if self.current_sequence:
                self.current_sequence.stop()
            self.current_sequence = None
            
            # If no media exists, ensure we're in a clean state
            loop_slugs = media_index.list_loop()
            if not loop_slugs:
                self.logger.info("No media in loop, clearing active media")
                media_index.set_active(None)
                self.current_media_loops = 0 