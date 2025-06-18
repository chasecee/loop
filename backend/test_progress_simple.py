#!/usr/bin/env python3
"""
Simple test script for progress tracking.
Run this to verify progress tracking is working.
"""

import time
import uuid
from utils.media_index import media_index

def test_progress():
    """Test progress tracking."""
    print("Testing progress tracking system...")
    
    # Create a test job
    job_id = str(uuid.uuid4())
    filename = "test_conversion.gif"
    
    print(f"Creating job: {job_id}")
    media_index.add_processing_job(job_id, filename)
    
    # Simulate progress updates
    stages = [
        (10, "analyzing", "Starting conversion..."),
        (30, "processing", "Converting frames 1/10"),
        (50, "processing", "Converting frames 5/10"), 
        (80, "processing", "Converting frames 8/10"),
        (95, "finalizing", "Creating metadata..."),
    ]
    
    for progress, stage, message in stages:
        media_index.update_processing_job(job_id, progress, stage, message)
        print(f"Progress: {progress}% - {stage}: {message}")
        
        # Check the job status
        job_data = media_index.get_processing_job(job_id)
        if job_data:
            print(f"  Status: {job_data['status']}, Progress: {job_data['progress']}%")
        
        time.sleep(1)
    
    # Complete the job
    media_index.complete_processing_job(job_id, True)
    print("Job completed!")
    
    # Show final status
    job_data = media_index.get_processing_job(job_id)
    if job_data:
        print(f"Final status: {job_data['status']}, Progress: {job_data['progress']}%")
    
    # List all jobs
    all_jobs = media_index.list_processing_jobs()
    print(f"Total processing jobs in system: {len(all_jobs)}")
    
    # Clean up
    media_index.remove_processing_job(job_id)
    print("Test completed and cleaned up!")

if __name__ == "__main__":
    test_progress() 