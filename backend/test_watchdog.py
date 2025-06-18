#!/usr/bin/env python3
"""
Simple test to verify systemd watchdog integration.
Run this to test if watchdog notifications are working.
"""

import time
import sys

try:
    from systemd import daemon
    SYSTEMD_AVAILABLE = True
    print("✅ systemd module available")
except ImportError:
    SYSTEMD_AVAILABLE = False
    print("❌ systemd module not available")
    sys.exit(1)

def test_watchdog():
    """Test watchdog notifications."""
    print("🐕 Testing systemd watchdog...")
    
    # Notify systemd we're ready
    try:
        daemon.notify("READY=1")
        print("✅ Sent READY=1 to systemd")
    except Exception as e:
        print(f"❌ Failed to send READY: {e}")
        return False
    
    # Test watchdog notifications
    for i in range(10):
        try:
            daemon.notify("WATCHDOG=1")
            print(f"✅ Watchdog ping #{i+1}")
            time.sleep(5)  # Wait 5 seconds between pings
        except Exception as e:
            print(f"❌ Watchdog ping #{i+1} failed: {e}")
            return False
    
    print("🎉 Watchdog test completed successfully!")
    return True

if __name__ == "__main__":
    test_watchdog() 