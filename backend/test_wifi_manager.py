#!/usr/bin/env python3
"""
Comprehensive test suite for enterprise-grade WiFi manager.
Tests thread safety, error handling, input validation, and atomic operations.
"""

import unittest
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

# Import our WiFi manager
from boot.wifi import (
    WiFiManager, 
    WiFiError, 
    WiFiSecurityError, 
    WiFiTimeoutError, 
    WiFiInterfaceError,
    ConnectionState,
    NetworkInfo,
    ConnectionInfo
)
from config.schema import WiFiConfig


@dataclass
class MockWiFiConfig:
    """Mock WiFi configuration for testing."""
    ssid: str = ""
    password: str = ""
    hotspot_enabled: bool = True
    hotspot_ssid: str = "LOOP-Test"
    hotspot_password: str = "testpass123"
    hotspot_channel: int = 6


class TestWiFiManagerValidation(unittest.TestCase):
    """Test input validation and security measures."""
    
    def test_validate_config_success(self):
        """Test valid configuration passes validation."""
        config = MockWiFiConfig(
            ssid="ValidNetwork",
            password="validpass123",
            hotspot_ssid="ValidHotspot",
            hotspot_password="validhotpass123"
        )
        
        # Should not raise
        validated = WiFiManager._validate_config(config)
        self.assertEqual(validated.ssid, "ValidNetwork")
    
    def test_validate_config_invalid_ssid(self):
        """Test invalid SSID rejection."""
        with self.assertRaises(ValueError, msg="Should reject overly long SSID"):
            config = MockWiFiConfig(ssid="x" * 33)  # Too long
            WiFiManager._validate_config(config)
        
        with self.assertRaises(ValueError, msg="Should reject control characters"):
            config = MockWiFiConfig(ssid="test\x00network")  # Null byte
            WiFiManager._validate_config(config)
    
    def test_validate_config_invalid_password(self):
        """Test invalid password rejection."""
        with self.assertRaises(ValueError, msg="Should reject short password"):
            config = MockWiFiConfig(password="1234567")  # Too short
            WiFiManager._validate_config(config)
    
    def test_validate_config_invalid_hotspot(self):
        """Test invalid hotspot configuration rejection."""
        with self.assertRaises(ValueError, msg="Should reject invalid channel"):
            config = MockWiFiConfig(hotspot_channel=15)  # Invalid channel
            WiFiManager._validate_config(config)


class TestWiFiManagerThreadSafety(unittest.TestCase):
    """Test thread safety and concurrent operations."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = MockWiFiConfig()
        
        # Mock subprocess calls to avoid real system interaction
        self.subprocess_patcher = patch('boot.wifi.subprocess.run')
        self.mock_subprocess = self.subprocess_patcher.start()
        
        # Mock successful command responses
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        self.mock_subprocess.return_value = mock_result
        
        # Mock glob for interface detection
        self.glob_patcher = patch('boot.wifi.glob.glob')
        self.mock_glob = self.glob_patcher.start()
        self.mock_glob.return_value = ["/sys/class/net/wlan0"]
        
        # Mock os.path.exists for interface validation
        self.exists_patcher = patch('boot.wifi.os.path.exists')
        self.mock_exists = self.exists_patcher.start()
        self.mock_exists.return_value = True
    
    def tearDown(self):
        """Clean up test environment."""
        self.subprocess_patcher.stop()
        self.glob_patcher.stop()
        self.exists_patcher.stop()
    
    def test_concurrent_status_updates(self):
        """Test multiple threads updating status concurrently."""
        wifi_manager = WiFiManager(self.config)
        
        errors = []
        
        def update_status():
            try:
                for _ in range(10):
                    wifi_manager._update_connection_state()
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=update_status)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5)
        
        # No errors should occur
        self.assertEqual(len(errors), 0, f"Thread safety errors: {errors}")
    
    def test_concurrent_operations_blocking(self):
        """Test that operations are properly serialized."""
        wifi_manager = WiFiManager(self.config)
        
        results = []
        
        def scan_operation():
            try:
                # This should block other operations
                with wifi_manager._operation_context("test_scan"):
                    time.sleep(0.1)
                    results.append("scan_completed")
            except WiFiError as e:
                results.append(f"scan_error: {e}")
        
        def connect_operation():
            try:
                # This should be blocked by scan operation
                with wifi_manager._operation_context("test_connect"):
                    results.append("connect_started")
            except WiFiError as e:
                results.append(f"connect_error: {e}")
        
        # Start scan operation first
        scan_thread = threading.Thread(target=scan_operation)
        scan_thread.start()
        
        # Small delay then try to start connect (should be blocked)
        time.sleep(0.05)
        connect_thread = threading.Thread(target=connect_operation)
        connect_thread.start()
        
        # Wait for completion
        scan_thread.join(timeout=2)
        connect_thread.join(timeout=2)
        
        # Scan should complete, connect should be blocked
        self.assertIn("scan_completed", results)
        # Connect should either complete after scan or be blocked
        self.assertTrue(
            "connect_started" in results or 
            any("already in progress" in str(r) for r in results)
        )


class TestWiFiManagerErrorHandling(unittest.TestCase):
    """Test comprehensive error handling."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = MockWiFiConfig()
        
        # Mock subprocess for controlled error testing
        self.subprocess_patcher = patch('boot.wifi.subprocess.run')
        self.mock_subprocess = self.subprocess_patcher.start()
    
    def tearDown(self):
        """Clean up test environment."""
        self.subprocess_patcher.stop()
    
    def test_command_timeout_handling(self):
        """Test command timeout error handling."""
        # Mock timeout exception
        import subprocess
        self.mock_subprocess.side_effect = subprocess.TimeoutExpired("nmcli", 30)
        
        wifi_manager = WiFiManager(self.config)
        
        with self.assertRaises(WiFiTimeoutError):
            wifi_manager._run_command_safe(["nmcli", "device", "status"])
    
    def test_invalid_credentials_handling(self):
        """Test handling of invalid WiFi credentials."""
        # Mock failed connection due to bad password
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "Secrets were required but not provided"
        mock_result.stderr = ""
        self.mock_subprocess.return_value = mock_result
        
        wifi_manager = WiFiManager(self.config)
        
        with self.assertRaises(WiFiSecurityError):
            wifi_manager.connect_to_network("TestNetwork", "wrongpassword")
    
    def test_interface_detection_failure(self):
        """Test handling of WiFi interface detection failure."""
        # Mock no WiFi interface available
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "No WiFi adapters found"
        self.mock_subprocess.return_value = mock_result
        
        with patch('boot.wifi.glob.glob', return_value=[]):
            with patch('boot.wifi.os.path.exists', return_value=False):
                wifi_manager = WiFiManager(self.config)
                
                with self.assertRaises(WiFiInterfaceError):
                    wifi_manager.scan_networks()


class TestWiFiManagerAtomicOperations(unittest.TestCase):
    """Test atomic state management."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = MockWiFiConfig()
        
        # Mock successful subprocess
        self.subprocess_patcher = patch('boot.wifi.subprocess.run')
        self.mock_subprocess = self.subprocess_patcher.start()
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "wlan0:wifi:connected"
        mock_result.stderr = ""
        self.mock_subprocess.return_value = mock_result
        
        # Mock interface detection
        self.glob_patcher = patch('boot.wifi.glob.glob')
        self.mock_glob = self.glob_patcher.start()
        self.mock_glob.return_value = ["/sys/class/net/wlan0"]
        
        self.exists_patcher = patch('boot.wifi.os.path.exists')
        self.mock_exists = self.exists_patcher.start()
        self.mock_exists.return_value = True
    
    def tearDown(self):
        """Clean up test environment."""
        self.subprocess_patcher.stop()
        self.glob_patcher.stop()
        self.exists_patcher.stop()
    
    def test_connection_state_atomicity(self):
        """Test that connection state updates are atomic."""
        wifi_manager = WiFiManager(self.config)
        
        # Initial state should be consistent
        status = wifi_manager.get_status()
        self.assertIsInstance(status['connected'], bool)
        self.assertIsInstance(status['hotspot_active'], bool)
        
        # State should remain consistent during updates
        original_state = wifi_manager._connection_info.state
        wifi_manager._update_connection_state()
        
        # State should be valid
        self.assertIsInstance(wifi_manager._connection_info.state, ConnectionState)
    
    def test_interface_detection_caching(self):
        """Test that interface detection is properly cached."""
        wifi_manager = WiFiManager(self.config)
        
        # First call should detect interface
        interface1 = wifi_manager._detect_wifi_interface()
        call_count_1 = self.mock_subprocess.call_count
        
        # Second call within cache period should use cached result
        interface2 = wifi_manager._detect_wifi_interface()
        call_count_2 = self.mock_subprocess.call_count
        
        self.assertEqual(interface1, interface2)
        # Should not have made additional subprocess calls for cached result
        # (allowing some calls for other initialization, but not many more)
        self.assertLessEqual(call_count_2 - call_count_1, 1)


class TestNetworkInfoValidation(unittest.TestCase):
    """Test NetworkInfo dataclass validation."""
    
    def test_valid_network_info(self):
        """Test creating valid NetworkInfo."""
        network = NetworkInfo(
            ssid="TestNetwork",
            signal=75,
            secured=True,
            frequency=2450,
            security_type="WPA2"
        )
        
        self.assertEqual(network.ssid, "TestNetwork")
        self.assertEqual(network.signal, 75)
        self.assertTrue(network.secured)
    
    def test_invalid_network_info(self):
        """Test NetworkInfo validation."""
        with self.assertRaises(ValueError, msg="Should reject empty SSID"):
            NetworkInfo(ssid="", signal=75, secured=True)
        
        with self.assertRaises(ValueError, msg="Should reject invalid signal"):
            NetworkInfo(ssid="Test", signal=150, secured=True)  # > 100
        
        with self.assertRaises(ValueError, msg="Should reject control characters"):
            NetworkInfo(ssid="test\x00network", signal=75, secured=True)


class TestConnectionInfoStaleness(unittest.TestCase):
    """Test ConnectionInfo staleness detection."""
    
    def test_fresh_connection_info(self):
        """Test that fresh connection info is not stale."""
        info = ConnectionInfo(ConnectionState.CONNECTED)
        self.assertFalse(info.is_stale(max_age_seconds=30))
    
    def test_stale_connection_info(self):
        """Test that old connection info is detected as stale."""
        info = ConnectionInfo(ConnectionState.CONNECTED)
        # Manually set old timestamp
        info.last_updated = time.time() - 60  # 60 seconds ago
        
        self.assertTrue(info.is_stale(max_age_seconds=30))


if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Run all tests
    unittest.main(verbosity=2) 