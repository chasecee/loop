#!/usr/bin/env python3
"""
Test script for processing progress display system.
"""

import time
import uuid
from pathlib import Path
from utils.media_index import media_index
from config.schema import get_config

def test_progress_system():
    """Test the progress tracking system."""
    print("Testing processing progress system...")
    
    # No converter needed - just testing progress tracking
    
    # Create test job
    job_id = str(uuid.uuid4())
    test_filename = "test_file.gif"
    
    print(f"Created test job: {job_id}")
    
    # Add processing job
    media_index.add_processing_job(job_id, test_filename)
    print("Added processing job to index")
    
    # Simulate progress updates
    stages = [
        (10, "analyzing", "Analyzing GIF structure..."),
        (20, "preparing", "Preparing frame extraction..."),
        (40, "processing", "Processing frame 10/50"),
        (60, "processing", "Processing frame 25/50"),
        (80, "processing", "Processing frame 40/50"),
        (90, "finalizing", "Generating metadata..."),
    ]
    
    for progress, stage, message in stages:
        media_index.update_processing_job(job_id, progress, stage, message)
        print(f"Progress: {progress}% - {stage}: {message}")
        
        # Check job status
        job_data = media_index.get_processing_job(job_id)
        if job_data:
            print(f"  Job status: {job_data['status']}, Progress: {job_data['progress']}%")
        
        time.sleep(1)  # Simulate processing time
    
    # Complete job
    media_index.complete_processing_job(job_id, True)
    print("Job completed successfully")
    
    # Check final status
    job_data = media_index.get_processing_job(job_id)
    if job_data:
        print(f"Final job status: {job_data['status']}, Progress: {job_data['progress']}%")
    
    # Clean up
    media_index.remove_processing_job(job_id)
    print("Test completed and cleaned up")

if __name__ == "__main__":
    test_progress_system() 