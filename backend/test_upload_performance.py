#!/usr/bin/env python3
"""
Upload Coordinator Performance Test - Pi Edition

Tests upload coordinator performance on Raspberry Pi hardware.
Validates the ZIP processing optimizations work as expected.

Usage:
    cd /home/pi/loop/backend
    python test_upload_performance.py
"""

import asyncio
import json
import time
import tempfile
import zipfile
import sys
import os
from pathlib import Path
from typing import Dict, Any

# Add backend to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the required modules for testing
class MockBroadcaster:
    async def upload_progress_simple(self, filename: str, progress: int, status: str):
        print(f"📊 Progress: {filename} - {progress}% - {status}")
    
    async def media_uploaded(self, metadata: Dict[str, Any]):
        print(f"📤 Media uploaded: {metadata.get('slug', 'unknown')}")
    
    async def loop_updated(self, loop_data: list):
        print(f"🔄 Loop updated: {len(loop_data)} items")

class MockMediaIndex:
    def __init__(self):
        self.media = {}
    
    def get_media_dict(self):
        return self.media
    
    def add_media(self, metadata: Dict[str, Any], make_active: bool = True):
        slug = metadata.get('slug')
        if slug:
            self.media[slug] = metadata
        print(f"📚 Added to media index: {slug} (active={make_active})")
    
    def remove_media(self, slug: str):
        if slug in self.media:
            del self.media[slug]
        print(f"🗑️ Removed from media index: {slug}")

async def create_test_zip(frame_count: int = 100) -> bytes:
    """Create a test ZIP file with frames for Pi performance testing."""
    print(f"🏗️ Creating test ZIP with {frame_count} frames...")
    start_time = time.time()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "test_frames.zip"
        
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            # Add metadata
            metadata = {
                "original_filename": "test_video.mp4",
                "frame_count": frame_count,
                "width": 320,
                "height": 240,
                "type": "video/mp4"
            }
            zf.writestr("metadata.json", json.dumps(metadata))
            
            # Add test frames (realistic RGB565 frame data for Pi)
            frame_data = b'\x00\xFF' * (320 * 240)  # RGB565 frame data (153.6KB per frame)
            for i in range(frame_count):
                zf.writestr(f"frame_{i:04d}.rgb", frame_data)
        
        # Read ZIP content
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
    
    creation_time = time.time() - start_time
    print(f"✅ Created test ZIP: {len(zip_content)/1024/1024:.1f}MB in {creation_time:.2f}s")
    return zip_content

async def test_upload_performance():
    """Test upload coordinator performance on Pi hardware."""
    
    print("🧪 Upload Coordinator Performance Test - Pi Edition")
    print("=" * 60)
    print(f"🔧 Running on: {os.uname().machine} ({os.uname().sysname})")
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Mock the dependencies
    from unittest.mock import patch
    
    try:
        with patch('web.core.upload_coordinator.broadcaster', MockBroadcaster()), \
             patch('web.core.upload_coordinator.media_index', MockMediaIndex()):
            
            from web.core.upload_coordinator import UploadCoordinator
            print("✅ Upload coordinator imported successfully")
            
            coordinator = UploadCoordinator()
            
            # Pi-optimized test cases (smaller sizes for Pi Zero 2)
            test_cases = [
                {"name": "Small ZIP (5 frames)", "frame_count": 5, "expected_time": 1.0},
                {"name": "Medium ZIP (25 frames)", "frame_count": 25, "expected_time": 3.0},
                {"name": "Large ZIP (100 frames)", "frame_count": 100, "expected_time": 10.0},
            ]
            
            print(f"\n🎯 Running {len(test_cases)} performance tests...")
            
            overall_start = time.time()
            results = []
            
            for i, test_case in enumerate(test_cases, 1):
                print(f"\n{'='*60}")
                print(f"🔬 Test {i}/{len(test_cases)}: {test_case['name']}")
                print(f"🎯 Target: <{test_case['expected_time']:.1f}s")
                print("-" * 60)
                
                # Create test data
                zip_content = await create_test_zip(test_case['frame_count'])
                
                # Mock file info
                file_info = {
                    'filename': f"test_{test_case['frame_count']}_frames.zip",
                    'content': zip_content,
                    'hash': f"test_hash_{test_case['frame_count']}",
                    'size': len(zip_content),
                    'content_type': 'application/zip'
                }
                
                # Create mock transaction
                from web.core.upload_coordinator import UploadTransaction
                from datetime import datetime
                
                transaction = UploadTransaction(
                    id=f"test_{test_case['frame_count']}",
                    files=[{'filename': file_info['filename'], 'hash': file_info['hash'], 'size': file_info['size']}],
                    state='processing',
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                # Test the optimized ZIP processing
                print(f"🏃 Starting ZIP processing...")
                start_time = time.time()
                
                try:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        processed_dir = Path(tmpdir)
                        
                        result_slug = await coordinator._process_zip_file(
                            transaction, file_info, processed_dir
                        )
                        
                        end_time = time.time()
                        processing_time = end_time - start_time
                        
                        # Verify results
                        final_dir = processed_dir / result_slug
                        frames_dir = final_dir / "frames"
                        
                        frame_count = len(list(frames_dir.glob("*.rgb"))) if frames_dir.exists() else 0
                        
                        # Calculate metrics
                        frames_per_sec = test_case['frame_count'] / processing_time
                        throughput_mbps = len(zip_content) / 1024 / 1024 / processing_time
                        vs_target = processing_time / test_case['expected_time']
                        
                        # Performance rating
                        if processing_time <= test_case['expected_time'] * 0.5:
                            rating = "🚀 EXCELLENT"
                        elif processing_time <= test_case['expected_time']:
                            rating = "✅ GOOD"
                        elif processing_time <= test_case['expected_time'] * 2:
                            rating = "⚠️ ACCEPTABLE"
                        else:
                            rating = "🐌 SLOW"
                        
                        print(f"✅ Processing completed successfully!")
                        print(f"   ⏱️  Time: {processing_time:.2f}s (target: {test_case['expected_time']:.1f}s)")
                        print(f"   🏁 Speed: {frames_per_sec:.1f} frames/sec")
                        print(f"   📈 Throughput: {throughput_mbps:.1f} MB/s")
                        print(f"   📁 Extracted: {frame_count}/{test_case['frame_count']} frames")
                        print(f"   🎯 vs Target: {vs_target:.1f}x")
                        print(f"   🏆 Rating: {rating}")
                        
                        # Store results
                        results.append({
                            'name': test_case['name'],
                            'time': processing_time,
                            'target': test_case['expected_time'],
                            'frames': frame_count,
                            'throughput': throughput_mbps,
                            'rating': rating,
                            'success': True
                        })
                        
                except Exception as e:
                    end_time = time.time()
                    processing_time = end_time - start_time
                    print(f"❌ Processing failed after {processing_time:.2f}s")
                    print(f"   Error: {str(e)}")
                    
                    results.append({
                        'name': test_case['name'],
                        'time': processing_time,
                        'target': test_case['expected_time'],
                        'error': str(e),
                        'success': False
                    })
            
            # Summary report
            overall_time = time.time() - overall_start
            print(f"\n{'='*60}")
            print(f"🏁 PERFORMANCE TEST SUMMARY")
            print(f"{'='*60}")
            print(f"⏱️  Total test time: {overall_time:.2f}s")
            print(f"🧪 Tests run: {len(results)}")
            
            successful = [r for r in results if r['success']]
            failed = [r for r in results if not r['success']]
            
            print(f"✅ Successful: {len(successful)}")
            print(f"❌ Failed: {len(failed)}")
            
            if successful:
                avg_time = sum(r['time'] for r in successful) / len(successful)
                avg_throughput = sum(r.get('throughput', 0) for r in successful) / len(successful)
                print(f"📊 Average processing time: {avg_time:.2f}s")
                print(f"📊 Average throughput: {avg_throughput:.1f} MB/s")
            
            print(f"\n📋 Detailed Results:")
            for result in results:
                status = "✅" if result['success'] else "❌"
                print(f"   {status} {result['name']}: {result['time']:.2f}s")
                if result['success']:
                    print(f"      {result['rating']}")
            
            # Recommendations
            print(f"\n💡 RECOMMENDATIONS:")
            if all(r['success'] for r in results):
                if all(r['time'] <= r['target'] for r in successful):
                    print("   🎉 All tests passed! Upload coordinator is well optimized.")
                else:
                    slow_tests = [r for r in successful if r['time'] > r['target']]
                    print(f"   ⚠️  {len(slow_tests)} test(s) exceeded target times.")
                    print("   Consider further optimization for larger files.")
            else:
                print("   ❌ Some tests failed. Check error messages above.")
                print("   Verify all dependencies are properly installed.")
            
            if any(r.get('throughput', 0) < 1.0 for r in successful):
                print("   📈 Low throughput detected. Check SD card performance:")
                print("      sudo hdparm -t /dev/mmcblk0p1")
            
    except ImportError as e:
        print(f"❌ Failed to import upload coordinator: {e}")
        print("   Make sure you're running from the backend directory")
        print("   Current directory: {os.getcwd()}")
    except Exception as e:
        print(f"❌ Test failed with unexpected error: {e}")

if __name__ == "__main__":
    print("🔧 Starting upload coordinator performance test on Pi...")
    asyncio.run(test_upload_performance()) 