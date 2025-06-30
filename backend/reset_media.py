#!/usr/bin/env python3
"""
Reset Media Script - Clear all media files and database to start fresh.

This script will:
- Delete media.db SQLite database (includes all media and jobs)
- Clear media/processed/ directory  
- Clear media/raw/ directory
- Reset to a clean state

Usage: 
  python3 reset_media.py              # Reset everything
  python3 reset_media.py --jobs-only  # Reset only processing jobs
"""

import shutil
import sys
import sqlite3
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
    db_file = media_dir / "media.db"
    
    if not db_file.exists():
        print("❌ No media database found.")
        return
    
    try:
        # Connect to SQLite database
        with sqlite3.connect(db_file) as conn:
            # Count existing jobs
            cursor = conn.execute("SELECT COUNT(*) FROM processing_jobs")
            job_count = cursor.fetchone()[0]
            
            # Clear only processing jobs
            conn.execute("DELETE FROM processing_jobs")
            conn.commit()
        
        print(f"✅ Cleared {job_count} processing jobs from database")
        print("📱 Media files and database records preserved, only jobs reset")
        
    except Exception as e:
        print(f"❌ Failed to reset jobs: {e}")

def main():
    """Reset all media files and database."""
    # Check for jobs-only flag
    if len(sys.argv) > 1 and sys.argv[1] == "--jobs-only":
        reset_jobs_only()
        return
        
    print("🧹 LOOP Media Reset Script")
    print("=" * 40)
    
    # Confirm with user
    response = input("⚠️  This will DELETE ALL media files and database. Continue? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("❌ Reset cancelled.")
        return
    
    media_dir = Path("media")
    db_file = media_dir / "media.db"
    wal_file = media_dir / "media.db-wal"
    shm_file = media_dir / "media.db-shm"
    raw_dir = media_dir / "raw"
    processed_dir = media_dir / "processed"
    
    removed_count = 0
    
    # Remove SQLite database files
    for db_path in [db_file, wal_file, shm_file]:
        if db_path.exists():
            db_path.unlink()
            print(f"✅ Removed database file: {db_path}")
            removed_count += 1
    
    # Remove legacy JSON file if it exists
    legacy_json = media_dir / "index.json"
    if legacy_json.exists():
        legacy_json.unlink()
        print(f"✅ Removed legacy JSON file: {legacy_json}")
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
    print("📝 SQLite database will be recreated automatically on next app startup.")

if __name__ == "__main__":
    main() 