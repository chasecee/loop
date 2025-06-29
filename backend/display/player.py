# backend/display/player.py

import json
import threading
import time
import asyncio
import subprocess
import signal
from pathlib import Path
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass, field
from enum import Enum

from config.schema import DisplayConfig, MediaConfig
from display.framebuf import FrameSequence
from display.spiout import ILI9341Driver
from display.messages import MessageDisplay, set_message_display
from utils.logger import get_logger
from utils.media_index import media_index


@dataclass
class NetworkStatus:
    """Immutable network status snapshot."""
    connected: bool = False
    hotspot_active: bool = False
    ip_address: Optional[str] = None
    hotspot_ssid: Optional[str] = None
    mdns_working: bool = False
    timestamp: float = field(default_factory=time.time)
    
    def is_stale(self, max_age: float = 30.0) -> bool:
        """Check if status is stale."""
        return (time.time() - self.timestamp) > max_age


class WiFiStatusManager:
    """Production-grade WiFi status manager with async mDNS testing."""
    
    def __init__(self, wifi_manager, logger):
        self.wifi_manager = wifi_manager
        self.logger = logger
        
        # Thread-safe caching
        self._lock = threading.RLock()
        self._status_cache: Optional[NetworkStatus] = None
        
        # Background checking
        self._checker_thread: Optional[threading.Thread] = None
        self._checker_running = False
        self._check_interval = 30.0  # seconds
        self._mdns_timeout = 2.0  # shorter timeout for production
        
        # Subprocess management
        self._active_processes = set()
        self._process_lock = threading.Lock()
        
        self.logger.info("WiFi status manager initialized")
    
    def start(self):
        """Start background status checking."""
        if self._checker_running:
            return
        
        self._checker_running = True
        self._checker_thread = threading.Thread(
            target=self._background_checker_loop,
            name="WiFiStatusChecker",
            daemon=True
        )
        self._checker_thread.start()
        self.logger.info("Background WiFi status checker started")
    
    def stop(self):
        """Stop background checking and cleanup."""
        self._checker_running = False
        
        # Cleanup active processes
        with self._process_lock:
            for proc in list(self._active_processes):
                try:
                    if proc.poll() is None:  # Still running
                        proc.terminate()
                        proc.wait(timeout=1.0)
                except (subprocess.TimeoutExpired, ProcessLookupError):
                    try:
                        proc.kill()
                    except ProcessLookupError:
                        pass
                except Exception as e:
                    self.logger.warning(f"Error cleaning up subprocess: {e}")
            self._active_processes.clear()
        
        if self._checker_thread and self._checker_thread.is_alive():
            self._checker_thread.join(timeout=2.0)
        
        self.logger.info("WiFi status manager stopped")
    
    def get_display_info(self) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Get display URL and hotspot info for UI.
        
        Returns:
            (web_url, hotspot_info) where:
            - web_url: URL to show users (or None if hotspot mode)
            - hotspot_info: dict with SSID/password (or None if not hotspot)
        """
        status = self._get_current_status()
        
        if status.hotspot_active:
            # Hotspot mode - show connection instructions
            return None, {
                'ssid': status.hotspot_ssid or 'LOOP-Setup',
                'password': '●●●●●●●●●'  # Never expose real password
            }
        elif status.connected and status.ip_address:
            # Connected mode - choose best URL
            if status.mdns_working:
                return "loop.local", None
            else:
                return status.ip_address, None
        else:
            # Fallback
            return "loop.local", None
    
    def _get_current_status(self) -> NetworkStatus:
        """Get current network status with caching."""
        with self._lock:
            if self._status_cache and not self._status_cache.is_stale():
                return self._status_cache
            
            # Cache miss - generate fresh status
            return self._generate_status()
    
    def _generate_status(self) -> NetworkStatus:
        """Generate fresh network status (called with lock held)."""
        try:
            if not self.wifi_manager:
                return NetworkStatus()
            
            wifi_status = self.wifi_manager.get_status()
            
            status = NetworkStatus(
                connected=wifi_status.get('connected', False),
                hotspot_active=wifi_status.get('hotspot_active', False),
                ip_address=wifi_status.get('ip_address'),
                hotspot_ssid=wifi_status.get('hotspot_ssid'),
                mdns_working=self._status_cache.mdns_working if self._status_cache else False
            )
            
            self._status_cache = status
            return status
            
        except Exception as e:
            self.logger.warning(f"Failed to generate network status: {e}")
            return NetworkStatus()
    
    def _background_checker_loop(self):
        """Background thread that periodically checks mDNS."""
        self.logger.debug("Background WiFi status checker started")
        
        while self._checker_running:
            try:
                # Check if we need to test mDNS
                current_status = self._get_current_status()
                
                if current_status.connected and current_status.ip_address:
                    # Only test mDNS when connected to WiFi
                    mdns_working = self._test_mdns_safe()
                    
                    # Update cache atomically
                    with self._lock:
                        if self._status_cache:
                            self._status_cache = NetworkStatus(
                                connected=self._status_cache.connected,
                                hotspot_active=self._status_cache.hotspot_active,
                                ip_address=self._status_cache.ip_address,
                                hotspot_ssid=self._status_cache.hotspot_ssid,
                                mdns_working=mdns_working
                            )
                
                # Sleep with early exit capability
                for _ in range(int(self._check_interval)):
                    if not self._checker_running:
                        break
                    time.sleep(1.0)
                    
            except Exception as e:
                self.logger.error(f"Background WiFi checker error: {e}")
                time.sleep(5.0)  # Back off on errors
        
        self.logger.debug("Background WiFi status checker stopped")
    
    def _test_mdns_safe(self) -> bool:
        """Safely test mDNS resolution with proper resource management."""
        commands = [
            ["avahi-resolve", "-n", "loop.local"],
            ["getent", "hosts", "loop.local"],
            ["ping", "-c", "1", "-W", "1", "loop.local"]
        ]
        
        for cmd in commands:
            if not self._checker_running:
                return False
            
            try:
                result = self._run_subprocess_safe(cmd, timeout=self._mdns_timeout)
                if result and self._validate_mdns_output(result, cmd[0]):
                    self.logger.debug(f"mDNS working via {cmd[0]}")
                    return True
                    
            except Exception as e:
                self.logger.debug(f"mDNS test {cmd[0]} failed: {e}")
                continue
        
        self.logger.debug("All mDNS tests failed")
        return False
    
    def _run_subprocess_safe(self, cmd: List[str], timeout: float) -> Optional[str]:
        """Run subprocess with proper resource management."""
        if not self._checker_running:
            return None
        
        proc = None
        try:
            # Validate command exists
            if not self._command_exists(cmd[0]):
                return None
            
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True  # Prevent signal propagation
            )
            
            # Track active process
            with self._process_lock:
                self._active_processes.add(proc)
            
            stdout, stderr = proc.communicate(timeout=timeout)
            
            if proc.returncode == 0:
                return stdout.strip()
            else:
                self.logger.debug(f"Command {cmd[0]} failed: {stderr.strip()}")
                return None
                
        except subprocess.TimeoutExpired:
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            return None
            
        except (FileNotFoundError, PermissionError):
            return None
            
        except Exception as e:
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                except:
                    pass
            self.logger.debug(f"Subprocess {cmd[0]} error: {e}")
            return None
            
        finally:
            if proc:
                with self._process_lock:
                    self._active_processes.discard(proc)
    
    def _command_exists(self, command: str) -> bool:
        """Check if command exists without running it."""
        try:
            result = subprocess.run(
                ["which", command],
                capture_output=True,
                timeout=1.0
            )
            return result.returncode == 0
        except:
            return False
    
    def _validate_mdns_output(self, output: str, command: str) -> bool:
        """Validate mDNS command output."""
        if not output or len(output) > 1000:  # Sanity check
            return False
        
        output_lower = output.lower()
        
        if command == "avahi-resolve":
            # Expected: "loop.local    192.168.1.100"
            return "loop.local" in output_lower and any(
                c.isdigit() for c in output  # Contains IP
            )
        elif command == "getent":
            # Expected: "192.168.1.100  loop.local"
            return "loop.local" in output_lower and any(
                c.isdigit() for c in output  # Contains IP
            )
        elif command == "ping":
            # Expected: "PING loop.local (192.168.1.100)"
            return ("ping" in output_lower and 
                   "loop.local" in output_lower and
                   "(" in output)  # IP in parentheses
        
        return False


class DisplayPlayer:
    """Main display playback engine."""
    
    def __init__(self, display_driver: ILI9341Driver, 
                 display_config: DisplayConfig, 
                 media_config: MediaConfig,
                 wifi_manager=None):
        """Initialize the display player."""
        self.display_driver = display_driver
        self.display_config = display_config
        self.media_config = media_config
        self.wifi_manager = wifi_manager
        self.logger = get_logger("player")
        
        # Initialize messaging system
        self.message_display = MessageDisplay(display_driver, display_config)
        set_message_display(self.message_display)  # Set global instance
        
        # Initialize WiFi status manager
        self.wifi_status_manager = WiFiStatusManager(wifi_manager, self.logger)
        
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
    
    def force_stop_progress_display(self) -> None:
        """Force stop any stale progress displays."""
        if self.showing_progress:
            self.logger.warning("Force stopping stale progress display")
            self.showing_progress = False
            self.progress_stop_event.set()
            
            if self.progress_thread and self.progress_thread.is_alive():
                self.progress_thread.join(timeout=5)
                if self.progress_thread.is_alive():
                    self.logger.error("Progress thread did not stop gracefully")
            
            self.logger.info("Force stopped stale progress display")
    
    def _processing_display_loop(self, job_ids: List[str]) -> None:
        """Loop that displays upload progress."""
        try:
            # Show initial progress
            self.show_progress_bar("Uploading Media", "Starting upload...", 0)
            
            # Add timeout to prevent getting stuck forever (15 minutes for large video processing)
            start_time = time.time()
            max_duration = 900  # 15 minutes - match frontend timeout
            no_jobs_count = 0  # Count consecutive checks with no jobs
            
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
                if elapsed % 10 == 0:  # Only log every 10 seconds to reduce spam
                    self.logger.info(f"Progress check {elapsed:.1f}s: tracking {len(job_ids)} jobs, found {len(relevant_jobs)} relevant")
                    for job_id, job_data in relevant_jobs.items():
                        status = job_data.get('status', 'unknown')
                        progress = job_data.get('progress', 0)
                        stage = job_data.get('stage', 'unknown')
                        self.logger.debug(f"  Job {job_id[:8]}: {status} {progress}% ({stage})")
                
                # Check if any of our original job IDs disappeared
                missing_jobs = [jid for jid in job_ids if jid not in processing_jobs]
                if missing_jobs:
                    self.logger.warning(f"Missing jobs: {[jid[:8] for jid in missing_jobs]}")
                
                # IMPROVED: More aggressive detection of completion/stale state
                if not relevant_jobs or len(missing_jobs) == len(job_ids):
                    no_jobs_count += 1
                    self.logger.info(f"No relevant processing jobs found or all jobs missing, stopping progress display (count: {no_jobs_count})")
                    # Stop immediately if no jobs found
                    break
                else:
                    no_jobs_count = 0  # Reset counter if we found jobs
                
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
        # Get the actual web URL based on network status
        web_url, hotspot_info = self.wifi_status_manager.get_display_info()
        
        self.message_display.show_no_media_message(web_url, hotspot_info)
    
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
                        self.logger.info(f"📸 Displaying static image ({len(frame_data)} bytes) for {self.static_image_display_time}s")
                        if self.display_available:
                            self.display_driver.display_frame(frame_data)
                        else:
                            # Demo mode - simulate display with longer delay
                            self.logger.debug("🔄 Demo mode: simulating static image display")
                        self._wait_interruptible(self.static_image_display_time)
                    else:
                        self.logger.warning("❌ Failed to get frame data for static image")
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
                                self.logger.debug(f"🖼️ Displaying frame {frame_idx+1}/{frame_count} ({len(frame_data)} bytes)")
                                self.display_driver.display_frame(frame_data)
                            except Exception as e:
                                # Display failed - mark hardware as unavailable
                                self.display_available = False
                                self.logger.error(f"❌ Display hardware failed, switching to demo mode: {e}")
                        else:
                            # Demo mode - simulate frame display timing
                            self.logger.debug(f"🔄 Demo mode: simulating frame {frame_idx+1}/{frame_count} display")
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
            self.wifi_status_manager.start()
            self.playback_thread = threading.Thread(target=self.run, daemon=True)
            self.playback_thread.start()
            self.logger.info("Display player started")
    
    def stop(self) -> None:
        """Stop the display player."""
        if self.running:
            self.running = False
            self.stop_processing_display()
            
            # Stop WiFi status manager
            self.wifi_status_manager.stop()
            
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

    # ------------------------------------------------------------
    # Explicit pause / resume helpers for external callers
    # ------------------------------------------------------------
    def pause(self) -> None:
        """Pause playback (idempotent)."""
        with self.lock:
            if not self.paused:
                self.paused = True
                self.pause_event.clear()
                self.logger.info("Playback paused (external)")

    def resume(self) -> None:
        """Resume playback if currently paused."""
        with self.lock:
            if self.paused:
                self.paused = False
                self.pause_event.set()
                self.logger.info("Playback resumed (external)") 