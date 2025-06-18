#!/usr/bin/env python3
"""Clean up stale processing jobs."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils.media_index import media_index

def cleanup_stale_jobs():
    """Clean up all processing jobs."""
    print("Cleaning up stale processing jobs...")
    
    jobs = media_index.list_processing_jobs()
    print(f"Found {len(jobs)} processing jobs")
    
    for job_id, job_data in jobs.items():
        print(f"Removing job {job_id}: {job_data.get('filename', 'unknown')}")
        media_index.remove_processing_job(job_id)
    
    print("✅ Cleanup completed")

if __name__ == "__main__":
    cleanup_stale_jobs() 