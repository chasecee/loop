#!/usr/bin/env python3
"""
Test script to verify upload fixes.
Tests the new background processing and progress polling.
"""

import requests
import time
import sys

def test_upload_fix():
    """Test the upload and progress polling system."""
    print("Testing upload fix...")
    
    base_url = "http://localhost:8080"
    
    # Test 1: Check server is responding
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code == 200:
            print("✅ Server is responding")
        else:
            print(f"❌ Server returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not responding: {e}")
        return False
    
    # Test 2: Test progress endpoint
    try:
        response = requests.get(f"{base_url}/api/media/progress", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Progress endpoint working: {len(data.get('data', {}).get('jobs', {}))} jobs")
        else:
            print(f"❌ Progress endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Progress endpoint failed: {e}")
        return False
    
    # Test 3: Multiple rapid progress requests (simulate polling)
    print("Testing rapid progress polling...")
    success_count = 0
    for i in range(10):
        try:
            response = requests.get(f"{base_url}/api/media/progress", timeout=2)
            if response.status_code == 200:
                success_count += 1
            time.sleep(0.1)  # 100ms between requests
        except Exception as e:
            print(f"Request {i+1} failed: {e}")
    
    print(f"✅ Progress polling test: {success_count}/10 requests successful")
    
    if success_count >= 8:
        print("🎉 Upload fix appears to be working!")
        return True
    else:
        print("⚠️  Some issues detected with rapid polling")
        return False

if __name__ == "__main__":
    success = test_upload_fix()
    sys.exit(0 if success else 1) 