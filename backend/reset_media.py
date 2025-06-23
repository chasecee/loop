#!/usr/bin/env python3
"""
Reset Media Script - Clear all media files and index to start fresh.

This script will:
- Delete media/index.json (includes jobs)
- Clear media/processed/ directory  
- Clear media/raw/ directory
- Reset to a clean state

Usage: 
  python3 reset_media.py              # Reset everything
  python3 reset_media.py --jobs-only  # Reset only processing jobs
"""

import shutil
import sys
import json
from pathlib import Path

def reset_jobs_only():
    """Reset only processing jobs, keep media files."""
    print("🧹 LOOP Jobs Reset Script")
    print("=" * 40)
    
    response = input("⚠️  This will DELETE ALL processing jobs but keep media. Continue? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ Jobs reset cancelled.")
        return
    
    media_dir = Path("media")
    index_file = media_dir / "index.json"
    
    if not index_file.exists():
        print("❌ No media index found.")
        return
    
    try:
        # Read current index
        with open(index_file, "r") as f:
            data = json.load(f)
        
        # Clear only processing jobs
        job_count = len(data.get("processing", {}))
        data["processing"] = {}
        
        # Write back
        with open(index_file, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Cleared {job_count} processing jobs")
        print("📱 Media files preserved, only jobs reset")
        
    except Exception as e:
        print(f"❌ Failed to reset jobs: {e}")

def main():
    """Reset all media files and index."""
    # Check for jobs-only flag
    if len(sys.argv) > 1 and sys.argv[1] == "--jobs-only":
        reset_jobs_only()
        return
        
    print("🧹 LOOP Media Reset Script")
    print("=" * 40)
    
    # Confirm with user
    response = input("⚠️  This will DELETE ALL media files and reset the index. Continue? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ Reset cancelled.")
        return
    
    media_dir = Path("media")
    index_file = media_dir / "index.json"
    raw_dir = media_dir / "raw"
    processed_dir = media_dir / "processed"
    
    removed_count = 0
    
    # Remove index file and any temp files
    if index_file.exists():
        index_file.unlink()
        print(f"✅ Removed media index: {index_file}")
        removed_count += 1
    
    # Clean up any orphaned temp files
    temp_files = list(media_dir.glob("*.tmp"))
    for temp_file in temp_files:
        temp_file.unlink()
        print(f"✅ Removed temp file: {temp_file}")
        removed_count += 1
    
    # Clear raw directory
    if raw_dir.exists():
        file_count = len(list(raw_dir.glob("*")))
        shutil.rmtree(raw_dir)
        raw_dir.mkdir(exist_ok=True)
        print(f"✅ Cleared raw media directory: {file_count} files removed")
        removed_count += file_count
    else:
        raw_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created raw media directory: {raw_dir}")
    
    # Clear processed directory
    if processed_dir.exists():
        dir_count = len([d for d in processed_dir.iterdir() if d.is_dir()])
        shutil.rmtree(processed_dir)
        processed_dir.mkdir(exist_ok=True)
        print(f"✅ Cleared processed media directory: {dir_count} directories removed")
        removed_count += dir_count
    else:
        processed_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created processed media directory: {processed_dir}")
    
    print("=" * 40)
    print(f"🎉 Media reset complete! Removed {removed_count} items.")
    print("📱 You can now upload media to test the new optimized format.")
    print("🚀 The system will use the new efficient metadata structure.")

if __name__ == "__main__":
    main() 