#!/usr/bin/env python3
"""
Test script for display progress system - simulates full upload flow.
"""

import time
import uuid
import threading
from utils.media_index import media_index
from config.schema import get_config
from display.spiout import ILI9341Driver
from display.player import DisplayPlayer

def test_display_progress():
    """Test the full progress display system."""
    print("Testing display progress system...")
    
    # Initialize the system like main.py does
    config = get_config()
    print(f"Config loaded - show_progress: {config.display.show_progress}")
    
    # Initialize display driver
    display_driver = ILI9341Driver(config.display)
    display_driver.init()
    print("Display driver initialized")
    
    # Initialize display player
    display_player = DisplayPlayer(display_driver, config.display, config.media)
    print("Display player initialized")
    
    # Create test jobs like the upload does
    job_ids = []
    for i in range(2):
        job_id = str(uuid.uuid4())
        filename = f"test_file_{i+1}.mov"
        job_ids.append(job_id)
        media_index.add_processing_job(job_id, filename)
        print(f"Created job {i+1}: {job_id} for {filename}")
    
    # Start progress display (this should show on physical display)
    print("\n🎨 Starting progress display...")
    display_player.start_processing_display(job_ids)
    
    # Simulate progress updates
    for job_idx, job_id in enumerate(job_ids):
        print(f"\n📈 Processing job {job_idx + 1}...")
        
        stages = [
            (10, "analyzing", "Analyzing video..."),
            (30, "extracting", "Extracting frames..."),
            (60, "processing", "Converting frames..."),
            (80, "processing", "Processing frame 45/50"),
            (95, "finalizing", "Creating metadata..."),
        ]
        
        for progress, stage, message in stages:
            media_index.update_processing_job(job_id, progress, stage, message)
            print(f"  {progress}% - {stage}: {message}")
            time.sleep(2)  # 2 second delays to see progress on display
        
        # Complete the job
        media_index.complete_processing_job(job_id, True)
        print(f"  ✅ Job {job_idx + 1} completed")
        time.sleep(1)
    
    # Let the completion message show
    print("\n⏳ Waiting for completion display...")
    time.sleep(3)
    
    # Stop progress display
    display_player.stop_processing_display()
    print("\n🛑 Stopped progress display")
    
    # Clean up jobs
    for job_id in job_ids:
        media_index.remove_processing_job(job_id)
    
    print("\n✅ Test completed! Check your display for progress bars.")

if __name__ == "__main__":
    test_display_progress() 