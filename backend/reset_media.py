#!/usr/bin/env python3
"""
Reset Media Script - Clear all media files and index to start fresh.

This script will:
- Delete media/index.json
- Clear media/processed/ directory
- Clear media/raw/ directory
- Reset to a clean state

Usage: python3 reset_media.py
"""

import shutil
import sys
from pathlib import Path

def main():
    """Reset all media files and index."""
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
    
    # Remove index file
    if index_file.exists():
        index_file.unlink()
        print(f"✅ Removed media index: {index_file}")
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