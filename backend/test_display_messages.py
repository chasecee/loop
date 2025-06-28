#!/usr/bin/env python3
"""
Test script for diagnosing display message issues.
Run this to test if the message display system is working properly.
"""

import sys
import time
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config.schema import get_config
from display.spiout import ILI9341Driver
from display.messages import MessageDisplay
from utils.logger import get_logger

def test_display_messages():
    """Test the display message system."""
    logger = get_logger("test_display")
    logger.info("🧪 Starting display message test...")
    
    try:
        # Load config
        config = get_config()
        logger.info(f"✅ Config loaded: {config.device.version}")
        
        # Initialize display driver
        logger.info("🖥️  Initializing display driver...")
        display_driver = ILI9341Driver(config.display)
        display_driver.init()
        logger.info("✅ Display driver initialized")
        
        # Initialize message display
        logger.info("💬 Initializing message display...")
        message_display = MessageDisplay(display_driver, config.display)
        logger.info("✅ Message display initialized")
        
        # Test boot message
        logger.info("🚀 Testing boot message...")
        message_display.show_boot_message(config.device.version)
        logger.info("✅ Boot message sent")
        
        # Wait to see boot message
        logger.info("⏳ Waiting 3 seconds for boot message to display...")
        time.sleep(3)
        
        # Test other messages
        test_messages = [
            ("Success Test", "This is a test message", (0, 255, 0)),  # Green
            ("Warning Test", "This is a warning", (255, 255, 0)),    # Yellow  
            ("Error Test", "This is an error", (255, 0, 0)),         # Red
            ("Info Test", "This is info", (0, 150, 255)),            # Blue
        ]
        
        for title, subtitle, color in test_messages:
            logger.info(f"💬 Testing message: {title}")
            message_display.show_message(title, subtitle, duration=2.0, text_color=color)
            time.sleep(2.5)  # Wait for message to display
        
        # Test progress bar
        logger.info("📊 Testing progress bar...")
        for progress in [0, 25, 50, 75, 100]:
            message_display.show_progress_bar("Progress Test", f"{progress}% complete", progress)
            time.sleep(1)
        
        logger.info("✅ All display tests completed successfully!")
        
        # Final cleanup message
        message_display.show_message("Test Complete", "All messages working!", duration=3.0, text_color=(0, 255, 0))
        time.sleep(3)
        
    except Exception as e:
        logger.error(f"❌ Display test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        try:
            if 'message_display' in locals():
                message_display.stop()
            if 'display_driver' in locals():
                display_driver.cleanup()
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")
    
    return True

if __name__ == "__main__":
    print("🎨 LOOP Display Message Test")
    print("=" * 40)
    
    success = test_display_messages()
    
    if success:
        print("\n🎉 Display test completed successfully!")
        print("If you didn't see messages on the display, check the logs above.")
    else:
        print("\n💥 Display test failed! Check the error messages above.")
        sys.exit(1) 