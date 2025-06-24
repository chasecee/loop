# backend/display/player.py

import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

from config.schema import DisplayConfig, MediaConfig
from display.framebuf import FrameSequence, FrameDecoder, FrameBuffer
from display.spiout import ILI9341Driver
from display.messages import MessageDisplay, set_message_display
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
        
        # Initialize messaging system
        self.message_display = MessageDisplay(display_driver, display_config)
        set_message_display(self.message_display)  # Set global instance
        
        # Media management
        self.media_dir = Path("media/processed")
        self.current_sequence: Optional[FrameSequence] = None
        
        # Playback control
        self.running = False
        self.paused = False
        self.frame_rate = display_config.framerate
        self.loop_count = media_config.loop_count
        self.loop_mode = "all"  # "all" or "one"
        
        # Per-media loop tracking
        self.current_media_loops = 0
        self.static_image_display_time = float(media_config.static_image_duration_sec)
        
        # Upload progress display
        self.showing_progress = False
        self.progress_thread: Optional[threading.Thread] = None
        self.progress_stop_event = threading.Event()
        
        # Event-based pause handling
        self.pause_event = threading.Event()
        self.pause_event.set()
        
        # Threading
        self.playback_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # Track logged missing frames to avoid spam
        self._logged_missing_frames = set()
        
        # Display hardware detection
        self.display_available = self._check_display_availability()
        if not self.display_available:
            self.logger.warning("Display hardware not available - running in demo mode")
        
        self.logger.info("Display player initialized")
    
    def _check_display_availability(self) -> bool:
        """Check if display hardware is actually available."""
        try:
            # Try to initialize and test display
            self.display_driver.init()
            return self.display_driver.initialized
        except Exception as e:
            self.logger.debug(f"Display hardware not available: {e}")
            return False
    
    def _wait_interruptible(self, duration: float) -> bool:
        """Wait for duration but return immediately if interrupted or paused."""
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
                if not self.pause_event.wait(timeout=0.1):
                    continue  # Still paused, check again
            
            # Sleep for remainder or 0.1s max to stay responsive
            remaining = duration - (time.time() - start_time)
            sleep_time = min(remaining, 0.1)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        return True  # Completed normally
    
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
            # Log only once per media to avoid spam
            if media_slug not in self._logged_missing_frames:
                self.logger.warning(f"Frames directory not found for {media_info.get('filename', media_slug)}: {frames_dir}")
                self.logger.info(f"Media {media_slug} is video-only (no processed frames)")
                self._logged_missing_frames.add(media_slug)
            
            # Don't show error message or return False - this causes switching loop
            # Instead, try to find next valid media automatically
            return self._find_and_load_next_valid_media()
        
        try:
            # Get frame info from media metadata
            frame_count = media_info.get('frame_count', 0)
            fps = media_info.get('fps', 25)  # Default 25fps
            frame_duration = 1.0 / fps
            
            # Create frame sequence
            self.current_sequence = FrameSequence(frames_dir, frame_count, frame_duration)
            
            if self.current_sequence.get_frame_count() == 0:
                self.logger.error(f"No frames found in {frames_dir}")
                return False

            # Clear the logged missing frames for this media since it loaded successfully
            if media_slug in self._logged_missing_frames:
                self._logged_missing_frames.remove(media_slug)

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
    
    def show_message(self, title: str, subtitle: str = "", duration: float = 2.0) -> None:
        """Display a text message on screen."""
        self.message_display.show_message(title, subtitle, duration)
    
    def show_boot_message(self, version: str = "1.0") -> None:
        """Show boot message."""
        self.message_display.show_boot_message(version)
    
    def show_error_message(self, error: str) -> None:
        """Show an error message."""
        self.message_display.show_error_message(error)
    

    
    def show_progress_bar(self, title: str, subtitle: str, progress: float) -> None:
        """Display a progress bar with title and subtitle."""
        self.message_display.show_progress_bar(title, subtitle, progress)
    
    def start_processing_display(self, job_ids: List[str]) -> None:
        """Start displaying upload progress for given job IDs."""
        if not self.display_config.show_progress:
            return
        
        if self.showing_progress:
            self.stop_processing_display()
        
        self.showing_progress = True
        self.progress_stop_event.clear()
        
        self.progress_thread = threading.Thread(
            target=self._processing_display_loop, 
            args=(job_ids,),
            daemon=True
        )
        self.progress_thread.start()
        self.logger.info(f"Started upload progress display for {len(job_ids)} jobs")
    
    def stop_processing_display(self) -> None:
        """Stop displaying upload progress."""
        if self.showing_progress:
            self.showing_progress = False
            self.progress_stop_event.set()
            
            if self.progress_thread:
                self.progress_thread.join(timeout=2)
            
            self.logger.info("Stopped upload progress display")
    
    def _processing_display_loop(self, job_ids: List[str]) -> None:
        """Loop that displays upload progress."""
        try:
            # Show initial progress
            self.show_progress_bar("Uploading Media", "Starting upload...", 0)
            
            # Add timeout to prevent getting stuck forever (90 seconds for ZIP processing)
            start_time = time.time()
            max_duration = 90  # 90 seconds - ZIP processing can take time
            
            while not self.progress_stop_event.is_set():
                # Get current processing jobs
                processing_jobs = media_index.list_processing_jobs()
                
                # Filter to our job IDs - also check for jobs with matching filenames
                # (in case job IDs were swapped during coordination)
                relevant_jobs = {}
                job_filenames = set()
                
                # First pass: get jobs by ID
                for job_id, job_data in processing_jobs.items():
                    if job_id in job_ids:
                        relevant_jobs[job_id] = job_data
                        job_filenames.add(job_data.get('filename', ''))
                
                # Second pass: if we lost jobs, find by filename
                if len(relevant_jobs) < len(job_ids):
                    for job_id, job_data in processing_jobs.items():
                        if job_id not in relevant_jobs and job_data.get('filename') in job_filenames:
                            relevant_jobs[job_id] = job_data
                            self.logger.info(f"Found related job {job_id} for filename {job_data.get('filename')}")
                
                # Debug logging for job states  
                elapsed = time.time() - start_time
                self.logger.info(f"Progress check {elapsed:.1f}s: tracking {len(job_ids)} jobs, found {len(relevant_jobs)} relevant")
                for job_id, job_data in relevant_jobs.items():
                    status = job_data.get('status', 'unknown')
                    progress = job_data.get('progress', 0)
                    stage = job_data.get('stage', 'unknown')
                    self.logger.info(f"  Job {job_id[:8]}: {status} {progress}% ({stage})")
                
                # Check if any of our original job IDs disappeared
                missing_jobs = [jid for jid in job_ids if jid not in processing_jobs]
                if missing_jobs:
                    self.logger.warning(f"Missing jobs: {[jid[:8] for jid in missing_jobs]}")
                
                if not relevant_jobs:
                    self.logger.info("No relevant processing jobs found, stopping progress display")
                    break
                
                # Calculate overall progress
                total_jobs = len(job_ids)
                completed_jobs = sum(1 for job in relevant_jobs.values() 
                                   if job.get('status') in ['completed', 'error'])
                
                overall_progress = (completed_jobs / total_jobs) * 100 if total_jobs > 0 else 100
                
                # Find active job for status
                active_job = None
                for job in relevant_jobs.values():
                    if job.get('status') == 'processing':
                        active_job = job
                        break
                
                if active_job:
                    # Show individual job progress
                    subtitle = active_job.get('stage', 'Processing')
                    job_progress = active_job.get('progress', 0)
                    self.show_progress_bar("Uploading Media", subtitle, job_progress)
                else:
                    # Show overall progress
                    subtitle = f"Completed {completed_jobs}/{total_jobs} files"
                    self.show_progress_bar("Uploading Media", subtitle, overall_progress)
                
                # Check if all jobs completed (or if we have any jobs at 100%)
                all_completed = all(
                    job.get('status') in ['completed', 'error'] 
                    for job in relevant_jobs.values()
                )
                
                # More aggressive completion detection
                any_at_100 = any(
                    job.get('progress', 0) >= 100 
                    for job in relevant_jobs.values()
                )
                
                # CRITICAL: Check if our original job IDs disappeared (completed elsewhere)
                original_jobs_missing = [jid for jid in job_ids if jid not in processing_jobs]
                if original_jobs_missing:
                    self.logger.info(f"🎯 Original jobs completed externally: {[jid[:8] for jid in original_jobs_missing]}")
                    all_completed = True
                
                # Also detect completion if progress hasn't changed for a while
                any_stalled = any(
                    job.get('progress', 0) >= 90 and elapsed > 60  # 90%+ for over 60 seconds
                    for job in relevant_jobs.values()
                )
                
                if all_completed or any_at_100 or any_stalled:
                    # Show completion briefly
                    reason = "all_completed" if all_completed else "100%" if any_at_100 else "timeout"
                    if original_jobs_missing:
                        reason = "jobs_completed_externally"
                    self.logger.info(f"Upload progress stopping: {reason} - tracked {len(job_ids)} jobs, found {len(relevant_jobs)} relevant")
                    self.show_progress_bar("Upload Complete", 
                                         f"Processed {total_jobs} files", 100)
                    time.sleep(2)
                    break
                
                # Check timeout
                if time.time() - start_time > max_duration:
                    self.logger.warning(f"Upload progress display timed out after {max_duration}s")
                    self.show_progress_bar("Processing Complete", "Media will appear shortly...", 100)
                    time.sleep(2)
                    break
                
                # Also break if we have no relevant jobs (they were cleaned up)
                if not relevant_jobs:
                    self.logger.info("No processing jobs found, stopping progress display")
                    break
                
                # Wait before next update
                if self.progress_stop_event.wait(1.0):
                    break
                    
        except Exception as e:
            self.logger.error(f"Error in upload progress display: {e}")
        finally:
            self.showing_progress = False
    
    def show_no_media_message(self) -> None:
        """Show a message when no media is available."""
        self.message_display.show_no_media_message()
    
    def run(self) -> None:
        """Main playback loop."""
        self.logger.info("Starting playback loop")
        
        while self.running:
            try:
                # Don't interfere with upload progress display
                if self.showing_progress:
                    time.sleep(0.5)
                    continue
                
                # Get current loop state
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
                            time.sleep(2)
                        else:
                            time.sleep(5)  # Wait longer for single media to reduce spam
                        continue
                    # Reset loop counter when loading new media
                    self.current_media_loops = 0
                
                # Snapshot sequence to avoid race conditions
                sequence = self.current_sequence
                if sequence is None:
                    continue

                frame_count = sequence.get_frame_count()
                is_static_image = frame_count == 1 and sequence.get_frame_duration(0) == 0.0
                
                if is_static_image:
                    # Display static image for configured duration
                    frame_data = sequence.get_next_frame(timeout=2.0)
                    if frame_data:
                        if self.display_available:
                            self.display_driver.display_frame(frame_data)
                        else:
                            # Demo mode - simulate display with longer delay
                            self.logger.debug("Demo mode: simulating static image display")
                        self._wait_interruptible(self.static_image_display_time)
                else:
                    # Play animated sequence
                    sequence_completed = True
                    
                    for frame_idx in range(frame_count):
                        if not self.running or self.showing_progress:
                            sequence_completed = False
                            break
                        
                        # Handle pause efficiently
                        if self.paused and self.running and not self.showing_progress:
                            self.pause_event.wait()
                        
                        if not self.running or self.showing_progress:
                            sequence_completed = False
                            break
                        
                        # Get and display frame
                        frame_data = sequence.get_next_frame(timeout=2.0)
                        frame_duration = sequence.get_frame_duration(frame_idx)
                        
                        if not frame_data:
                            sequence_completed = False
                            break
                        
                        # Display frame with hardware availability check
                        display_start = time.time()
                        if self.display_available:
                            try:
                                self.display_driver.display_frame(frame_data)
                            except Exception as e:
                                # Display failed - mark hardware as unavailable
                                self.display_available = False
                                self.logger.warning(f"Display hardware failed, switching to demo mode: {e}")
                        else:
                            # Demo mode - simulate frame display timing
                            time.sleep(0.001)  # Minimal delay to simulate display processing
                        
                        display_time = time.time() - display_start
                        
                        # Frame timing
                        target_frame_time = frame_duration if frame_duration > 0 else (1.0 / self.frame_rate)
                        sleep_time = max(0, target_frame_time - display_time)
                        
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                    
                    if not sequence_completed:
                        continue
                
                # Handle loop logic after completing sequence
                self.current_media_loops += 1
                
                should_continue_current_media = True
                
                if self.loop_mode == "one":
                    # Loop one mode - keep looping current media
                    if self.loop_count > 0 and self.current_media_loops >= self.loop_count:
                        self.current_media_loops = 0
                else:
                    # Loop all mode - decide whether to switch media
                    current_loop_slugs = media_index.list_loop()
                    
                    if len(current_loop_slugs) <= 1:
                        # Only one media - keep looping
                        if self.loop_count > 0 and self.current_media_loops >= self.loop_count:
                            self.current_media_loops = 0
                    else:
                        # Multiple media - check if should switch
                        if not self.media_config.auto_advance_enabled:
                            should_continue_current_media = True
                        elif self.loop_count <= 0:
                            # Infinite loops - play once then move to next
                            should_continue_current_media = False
                        elif self.current_media_loops >= self.loop_count:
                            # Completed required loops - move to next
                            should_continue_current_media = False
                
                if not should_continue_current_media:
                    # Switch to next media
                    self.next_media()
                    self.current_sequence = None
                    self.current_media_loops = 0
                
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
            self.stop_processing_display()
            
            # Stop current sequence
            if self.current_sequence:
                self.current_sequence.stop()
                self.current_sequence = None

            if self.playback_thread:
                self.playback_thread.join(timeout=5)
            self.logger.info("Display player stopped")

            # Stop the message display worker thread gracefully
            try:
                self.message_display.stop()
            except Exception:
                pass
    
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
    
    # Convenience methods for server interaction
    def notify_upload_start(self, count: int = 1) -> None:
        """Notify that upload has started."""
        self.message_display.show_upload_message(count)
    
    def notify_processing(self, filename: str = "") -> None:
        """Notify that processing has started."""
        self.message_display.show_processing_message(filename)
    
    def notify_error(self, error: str) -> None:
        """Notify of an error."""
        self.message_display.show_error_message(error)
    
    def clear_messages(self) -> None:
        """Clear the display (back to normal playback)."""
        # This will be handled by the main run loop automatically
        pass
    
    def refresh_media_list(self) -> None:
        """Refresh the media list by clearing current sequence to force reload."""
        with self.lock:
            if self.current_sequence:
                self.current_sequence.stop()
            self.current_sequence = None
            
            # If no media exists, clear active media
            loop_slugs = media_index.list_loop()
            if not loop_slugs:
                media_index.set_active(None)
                self.current_media_loops = 0
    
    def handle_media_deletion(self, deleted_slug: str) -> None:
        """Handle immediate media deletion to prevent frame loading errors."""
        with self.lock:
            # Check if the deleted media is currently playing
            current_active = media_index.get_active()
            
            # Stop current sequence immediately if it matches deleted media
            if self.current_sequence:
                self.current_sequence.stop()
                self.current_sequence = None
            
            # Clear logged missing frames for deleted media to avoid spam
            if deleted_slug in self._logged_missing_frames:
                self._logged_missing_frames.remove(deleted_slug)
            
            # Force immediate switch to new active media
            self.current_media_loops = 0
            
            # Log the switch
            if current_active:
                new_active = media_index.get_active()
                if new_active != deleted_slug:
                    self.logger.info(f"Switched from deleted media {deleted_slug} to {new_active}")
                else:
                    self.logger.info(f"No valid media remaining after deleting {deleted_slug}")
            
            self.logger.info(f"Handled deletion of media: {deleted_slug}")
    
    def _find_and_load_next_valid_media(self) -> bool:
        """Find and load the next valid media with wraparound search."""
        loop_media = self.get_current_loop_media()
        current_index = self.get_current_media_index()
        
        if not loop_media:
            self.logger.warning("No media available to load")
            return False
        
        # Search all media in loop with wraparound
        total_media = len(loop_media)
        for offset in range(total_media):
            # Calculate wrapped index (start from current, wrap to beginning)
            search_index = (current_index + offset) % total_media
            media_info = loop_media[search_index]
            media_slug = media_info.get('slug')
            
            if not media_slug:
                continue
                
            frames_dir = self.media_dir / media_slug / "frames"
            
            if frames_dir.exists():
                try:
                    # Get frame info from media metadata
                    frame_count = media_info.get('frame_count', 0)
                    fps = media_info.get('fps', 25)  # Default 25fps
                    frame_duration = 1.0 / fps
                    
                    # Create frame sequence
                    self.current_sequence = FrameSequence(frames_dir, frame_count, frame_duration)
                    
                    if self.current_sequence.get_frame_count() == 0:
                        self.logger.error(f"No frames found in {frames_dir}")
                        self.current_sequence = None
                        continue

                    # CRITICAL: Set this media as active to prevent switching loop
                    media_index.set_active(media_slug)

                    # Clear the logged missing frames for this media since it loaded successfully
                    if media_slug in self._logged_missing_frames:
                        self._logged_missing_frames.remove(media_slug)

                    self.logger.info(f"Found and loaded valid media: {media_info.get('original_filename', media_slug)}")
                    return True
                    
                except Exception as e:
                    self.logger.error(f"Failed to load sequence for {media_slug}: {e}")
                    if self.current_sequence:
                        self.current_sequence.stop()
                        self.current_sequence = None
                    continue
        
        # If we get here, NO media in the loop has valid frames
        self.logger.warning("No valid media found in entire loop - all media missing frames")
        self.show_message("No Media Available", "All media missing frames", duration=5.0)
        return False 