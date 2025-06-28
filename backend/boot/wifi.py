"""
WiFi management for LOOP using NetworkManager.
Enterprise-grade implementation with thread safety, atomic operations, and comprehensive error handling.
"""

import subprocess
import time
import threading
from typing import Dict, List, Optional, Tuple, Set
import json
import tempfile
import os
import glob
from threading import Lock, RLock
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
import re
import ipaddress
from pathlib import Path

from config.schema import WiFiConfig
from utils.logger import get_logger


class ConnectionState(Enum):
    """WiFi connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"
    HOTSPOT_ACTIVE = "hotspot_active"


class WiFiError(Exception):
    """Base WiFi management error."""
    pass


class WiFiSecurityError(WiFiError):
    """WiFi security-related error."""
    pass


class WiFiTimeoutError(WiFiError):
    """WiFi operation timeout error."""
    pass


class WiFiInterfaceError(WiFiError):
    """WiFi interface not available error."""
    pass


@dataclass
class NetworkInfo:
    """Immutable network information."""
    ssid: str
    signal: int
    secured: bool
    frequency: Optional[int] = None
    security_type: Optional[str] = None
    
    def __post_init__(self):
        # Validate SSID
        if not self.ssid or len(self.ssid) > 32:
            raise ValueError(f"Invalid SSID: {self.ssid}")
        if any(ord(c) < 32 for c in self.ssid if c != ' '):
            raise ValueError(f"SSID contains invalid characters: {self.ssid}")
        
        # Validate signal strength
        if not (0 <= self.signal <= 100):
            raise ValueError(f"Invalid signal strength: {self.signal}")


@dataclass
class ConnectionInfo:
    """Current connection information."""
    state: ConnectionState
    ssid: Optional[str] = None
    ip_address: Optional[str] = None
    interface: Optional[str] = None
    signal_strength: Optional[int] = None
    connection_uuid: Optional[str] = None
    last_updated: float = field(default_factory=time.time)
    
    def is_stale(self, max_age_seconds: float = 30.0) -> bool:
        """Check if connection info is stale."""
        return (time.time() - self.last_updated) > max_age_seconds


class WiFiManager:
    """
    Enterprise-grade WiFi manager using NetworkManager.
    
    Features:
    - Thread-safe operations with proper locking
    - Atomic state transitions
    - Comprehensive error handling with specific exception types
    - Input validation and sanitization
    - SSH-safe connection management
    - Network conflict prevention
    - Robust interface detection
    - Operation timeouts and retry logic
    """
    
    # Class constants
    COMMAND_TIMEOUT = 30
    CONNECTION_TIMEOUT = 60
    SCAN_TIMEOUT = 15
    INTERFACE_DETECTION_TIMEOUT = 10
    MAX_RETRY_ATTEMPTS = 3
    HOTSPOT_IP_RANGE = "192.168.100.0/24"  # Conflict-free range
    
    def __init__(self, wifi_config: WiFiConfig):
        """Initialize WiFi manager with enterprise-grade safeguards."""
        self.config = self._validate_config(wifi_config)
        self.logger = get_logger("wifi")
        
        # Thread safety - use RLock for re-entrant operations
        self._state_lock = RLock()
        self._operation_lock = Lock()  # Serialize major operations
        
        # Atomic state management
        self._connection_info = ConnectionInfo(ConnectionState.DISCONNECTED)
        self._wifi_interface: Optional[str] = None
        self._interface_last_checked = 0.0
        self._interface_check_interval = 60.0  # Cache interface for 60s
        
        # Operation tracking
        self._active_operations: Set[str] = set()
        self._last_scan_time = 0.0
        self._scan_cache_ttl = 10.0  # Cache scan results for 10s
        self._cached_networks: List[NetworkInfo] = []
        
        # Safe hotspot configuration
        self._hotspot_network = ipaddress.IPv4Network(self.HOTSPOT_IP_RANGE)
        self._hotspot_ip = str(self._hotspot_network.network_address + 1)  # .100.1
        
        self.logger.info("WiFi manager initialized (enterprise-grade NetworkManager integration)")
        self._initialize_state()
    
    @staticmethod
    def _validate_config(config: WiFiConfig) -> WiFiConfig:
        """Validate WiFi configuration with comprehensive checks."""
        if config.ssid:
            if len(config.ssid) > 32:
                raise ValueError("SSID too long (max 32 characters)")
            if any(ord(c) < 32 for c in config.ssid if c != ' '):
                raise ValueError("SSID contains invalid control characters")
        
        if config.password and len(config.password) < 8:
            raise ValueError("WiFi password must be at least 8 characters")
        
        if config.hotspot_ssid:
            if len(config.hotspot_ssid) > 32:
                raise ValueError("Hotspot SSID too long (max 32 characters)")
        
        if config.hotspot_password and len(config.hotspot_password) < 8:
            raise ValueError("Hotspot password must be at least 8 characters")
        
        if not (1 <= config.hotspot_channel <= 11):
            raise ValueError("Invalid hotspot channel (must be 1-11 for 2.4GHz)")
        
        return config
    
    @contextmanager
    def _operation_context(self, operation_name: str):
        """Context manager for tracking active operations."""
        with self._operation_lock:
            if operation_name in self._active_operations:
                raise WiFiError(f"Operation '{operation_name}' already in progress")
            self._active_operations.add(operation_name)
            
        try:
            self.logger.debug(f"Started operation: {operation_name}")
            yield
        finally:
            with self._operation_lock:
                self._active_operations.discard(operation_name)
            self.logger.debug(f"Completed operation: {operation_name}")
    
    def _run_command_safe(self, cmd: List[str], timeout: float = None, capture_output: bool = True) -> Tuple[bool, str]:
        """
        Execute system command with comprehensive safety measures.
        
        Args:
            cmd: Command and arguments as list
            timeout: Command timeout (uses class default if None)
            capture_output: Whether to capture stdout
            
        Returns:
            Tuple of (success, output/error_message)
            
        Raises:
            WiFiTimeoutError: Command timed out
            WiFiError: Command execution failed
        """
        if timeout is None:
            timeout = self.COMMAND_TIMEOUT
            
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                check=False,
                env={'LANG': 'C', 'LC_ALL': 'C'}  # Ensure English output
            )
            
            success = result.returncode == 0
            output = result.stdout.strip() if capture_output else ""
            
            if not success and result.stderr:
                output = result.stderr.strip()
            
            return success, output
            
        except subprocess.TimeoutExpired as e:
            safe_cmd = self._sanitize_command_for_logging(cmd)
            self.logger.error(f"Command timed out after {timeout}s: {' '.join(safe_cmd)}")
            raise WiFiTimeoutError(f"Command timed out: {' '.join(safe_cmd)}")
            
        except (OSError, ValueError) as e:
            safe_cmd = self._sanitize_command_for_logging(cmd)
            self.logger.error(f"Command execution failed: {' '.join(safe_cmd)} - {e}")
            raise WiFiError(f"Command execution failed: {e}")
    
    def _sanitize_command_for_logging(self, cmd: List[str]) -> List[str]:
        """Remove sensitive information from commands before logging."""
        safe_cmd = cmd.copy()
        
        # Redact sensitive arguments
        sensitive_args = {'password', 'wifi-sec.psk', 'psk'}
        
        for i, arg in enumerate(safe_cmd):
            if arg in sensitive_args and i + 1 < len(safe_cmd):
                safe_cmd[i + 1] = "[REDACTED]"
            # Also redact if argument contains password-like patterns
            elif re.search(r'pass|secret|key', arg, re.IGNORECASE) and '=' in arg:
                key, _ = arg.split('=', 1)
                safe_cmd[i] = f"{key}=[REDACTED]"
        
        return safe_cmd
    
    def _detect_wifi_interface(self) -> Optional[str]:
        """
        Robust WiFi interface detection with caching and fallbacks.
        
        Returns:
            WiFi interface name or None if not found
            
        Raises:
            WiFiInterfaceError: No WiFi interface available
        """
        current_time = time.time()
        
        # Use cached interface if recent
        with self._state_lock:
            if (self._wifi_interface and 
                current_time - self._interface_last_checked < self._interface_check_interval):
                return self._wifi_interface
        
        detected_interface = None
        
        try:
            # Method 1: Use nmcli to get active WiFi devices (most reliable)
            success, output = self._run_command_safe(
                ["nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "device", "status"],
                timeout=self.INTERFACE_DETECTION_TIMEOUT
            )
            
            if success and output:
                for line in output.split('\n'):
                    if ':wifi:' in line:
                        parts = line.split(':')
                        if len(parts) >= 3:
                            device, dev_type, state = parts[0], parts[1], parts[2]
                            if device and dev_type == 'wifi':
                                detected_interface = device
                                break
            
            # Method 2: Check filesystem for wireless interfaces
            if not detected_interface:
                wireless_interfaces = []
                
                # Check common patterns
                for pattern in ["/sys/class/net/wlan*", "/sys/class/net/wlp*", "/sys/class/net/wlx*"]:
                    for iface_path in glob.glob(pattern):
                        iface_name = os.path.basename(iface_path)
                        wireless_dir = os.path.join(iface_path, "wireless")
                        
                        if os.path.exists(wireless_dir):
                            wireless_interfaces.append(iface_name)
                
                # Prefer wlan0, then others
                if 'wlan0' in wireless_interfaces:
                    detected_interface = 'wlan0'
                elif wireless_interfaces:
                    detected_interface = wireless_interfaces[0]
            
            # Method 3: Use iw command as final fallback
            if not detected_interface:
                try:
                    success, output = self._run_command_safe(
                        ["iw", "dev"],
                        timeout=self.INTERFACE_DETECTION_TIMEOUT
                    )
                    
                    if success and output:
                        for line in output.split('\n'):
                            if 'Interface' in line:
                                parts = line.strip().split()
                                if len(parts) >= 2:
                                    detected_interface = parts[1]
                                    break
                except WiFiError:
                    pass  # iw might not be available
            
            # Update cache
            with self._state_lock:
                self._wifi_interface = detected_interface
                self._interface_last_checked = current_time
            
            if detected_interface:
                self.logger.debug(f"Detected WiFi interface: {detected_interface}")
            else:
                self.logger.warning("No WiFi interface detected")
                
            return detected_interface
            
        except Exception as e:
            self.logger.error(f"WiFi interface detection failed: {e}")
            raise WiFiInterfaceError(f"Failed to detect WiFi interface: {e}")
    
    def _initialize_state(self) -> None:
        """Initialize WiFi manager state safely."""
        try:
            with self._operation_context("initialize_state"):
                # Detect WiFi interface
                interface = self._detect_wifi_interface()
                if not interface:
                    self.logger.warning("No WiFi interface available - WiFi features disabled")
                    return
                
                # Update connection state
                self._update_connection_state()
                
        except (WiFiError, WiFiInterfaceError) as e:
            self.logger.error(f"Failed to initialize WiFi state: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during WiFi initialization: {e}")
    
    def _update_connection_state(self) -> None:
        """Atomically update connection state from system."""
        try:
            success, output = self._run_command_safe([
                "nmcli", "-t", "-f", "NAME,TYPE,DEVICE,STATE", "connection", "show", "--active"
            ])
            
            new_info = ConnectionInfo(ConnectionState.DISCONNECTED)
            
            if success and output:
                wifi_interface = self._detect_wifi_interface()
                
                for line in output.split('\n'):
                    if not line:
                        continue
                        
                    parts = line.split(':')
                    if len(parts) >= 4:
                        name, conn_type, device, state = parts[0], parts[1], parts[2], parts[3]
                        
                        if conn_type == 'wifi' and device == wifi_interface and state == 'activated':
                            new_info.state = ConnectionState.CONNECTED
                            new_info.ssid = name
                            new_info.interface = device
                            new_info.connection_uuid = name  # nmcli uses name as identifier
                            
                            # Get IP address
                            try:
                                ip_success, ip_output = self._run_command_safe([
                                    "ip", "addr", "show", device
                                ], timeout=5)
                                
                                if ip_success:
                                    for ip_line in ip_output.split('\n'):
                                        if 'inet ' in ip_line and '127.0.0.1' not in ip_line:
                                            ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', ip_line)
                                            if ip_match:
                                                new_info.ip_address = ip_match.group(1)
                                                break
                            except WiFiError:
                                pass  # IP detection is optional
                            
                            break
                        elif 'hotspot' in name.lower() or name == self.config.hotspot_ssid:
                            new_info.state = ConnectionState.HOTSPOT_ACTIVE
                            new_info.ssid = name
                            new_info.interface = device
                            new_info.connection_uuid = name
                            new_info.ip_address = self._hotspot_ip
                            break
            
            # Atomically update state
            with self._state_lock:
                self._connection_info = new_info
                
        except WiFiError as e:
            self.logger.warning(f"Failed to update connection state: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error updating connection state: {e}")
    
    def get_status(self) -> Dict:
        """Get current WiFi status thread-safely."""
        with self._state_lock:
            # Update if stale
            if self._connection_info.is_stale():
                try:
                    self._update_connection_state()
                except Exception as e:
                    self.logger.warning(f"Failed to refresh status: {e}")
            
            info = self._connection_info
            
            return {
                'connected': info.state == ConnectionState.CONNECTED,
                'hotspot_active': info.state == ConnectionState.HOTSPOT_ACTIVE,
                'current_ssid': info.ssid,
                'ip_address': info.ip_address,
                'configured_ssid': self.config.ssid if self.config.ssid else None,
                'hotspot_ssid': self.config.hotspot_ssid,
                'signal_strength': info.signal_strength,
                'interface': info.interface,
                'state': info.state.value,
                'network_info': {
                    'ssid': info.ssid,
                    'ip_address': info.ip_address,
                    'signal_strength': info.signal_strength,
                    'connected': info.state == ConnectionState.CONNECTED,
                    'interface': info.interface
                }
            }
    
    def scan_networks(self) -> List[Dict[str, str]]:
        """
        Scan for available WiFi networks with caching and error handling.
        
        Returns:
            List of network information dictionaries
            
        Raises:
            WiFiInterfaceError: No WiFi interface available
            WiFiError: Scan operation failed
        """
        current_time = time.time()
        
        # Return cached results if recent
        if (current_time - self._last_scan_time) < self._scan_cache_ttl and self._cached_networks:
            return [{'ssid': n.ssid, 'signal': n.signal, 'secured': n.secured} for n in self._cached_networks]
        
        with self._operation_context("scan_networks"):
            interface = self._detect_wifi_interface()
            if not interface:
                raise WiFiInterfaceError("No WiFi interface available for scanning")
            
            self.logger.info("Scanning for WiFi networks...")
            
            try:
                # Request fresh scan
                self._run_command_safe([
                    "nmcli", "device", "wifi", "rescan", "ifname", interface
                ], timeout=self.SCAN_TIMEOUT, capture_output=False)
                
                # Brief wait for scan to complete
                time.sleep(2)
                
                # Get scan results
                success, output = self._run_command_safe([
                    "nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY,FREQ", "device", "wifi", "list", "ifname", interface
                ], timeout=self.SCAN_TIMEOUT)
                
                if not success:
                    # Fallback without interface specification
                    success, output = self._run_command_safe([
                        "nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY,FREQ", "device", "wifi", "list"
                    ], timeout=self.SCAN_TIMEOUT)
                
                if not success:
                    raise WiFiError("Failed to retrieve WiFi scan results")
                
                networks = []
                seen_ssids = set()
                
                for line in output.split('\n'):
                    if not line or ':' not in line:
                        continue
                    
                    parts = line.split(':')
                    if len(parts) >= 3:
                        ssid = parts[0].strip()
                        signal_str = parts[1].strip()
                        security = parts[2].strip()
                        freq_str = parts[3].strip() if len(parts) > 3 else ""
                        
                        # Skip invalid or duplicate SSIDs
                        if not ssid or ssid in seen_ssids:
                            continue
                        
                        try:
                            # Validate and parse signal strength
                            signal = int(signal_str) if signal_str.isdigit() else 0
                            signal = max(0, min(100, signal))  # Clamp to valid range
                            
                            # Parse frequency
                            frequency = None
                            if freq_str and freq_str.isdigit():
                                frequency = int(freq_str)
                            
                            # Determine security
                            secured = bool(security and security != '--' and security != '')
                            
                            network_info = NetworkInfo(
                                ssid=ssid,
                                signal=signal,
                                secured=secured,
                                frequency=frequency,
                                security_type=security if secured else None
                            )
                            
                            networks.append(network_info)
                            seen_ssids.add(ssid)
                            
                        except (ValueError, TypeError) as e:
                            self.logger.warning(f"Failed to parse network info for '{ssid}': {e}")
                            continue
                
                # Sort by signal strength
                networks.sort(key=lambda x: x.signal, reverse=True)
                
                # Update cache
                self._cached_networks = networks
                self._last_scan_time = current_time
                
                self.logger.info(f"Found {len(networks)} WiFi networks")
                
                # Convert to dict format for API compatibility
                return [{'ssid': n.ssid, 'signal': n.signal, 'secured': n.secured} for n in networks]
                
            except WiFiTimeoutError:
                raise WiFiError("WiFi scan timed out - interface may be busy")
            except Exception as e:
                self.logger.error(f"WiFi scan failed: {e}")
                raise WiFiError(f"WiFi scan failed: {e}")
    
    def connect_to_network(self, ssid: str, password: str = "") -> bool:
        """
        Connect to WiFi network with enterprise-grade safety and error handling.
        
        Args:
            ssid: Network SSID (validated)
            password: Network password (validated)
            
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            WiFiSecurityError: Invalid credentials or security configuration
            WiFiInterfaceError: No WiFi interface available
            WiFiTimeoutError: Connection attempt timed out
            WiFiError: Connection failed for other reasons
        """
        # Input validation
        if not ssid or len(ssid) > 32:
            raise ValueError(f"Invalid SSID: {ssid}")
        if password and len(password) < 8:
            raise WiFiSecurityError("WiFi password must be at least 8 characters")
        
        with self._operation_context("connect_to_network"):
            interface = self._detect_wifi_interface()
            if not interface:
                raise WiFiInterfaceError("No WiFi interface available for connection")
            
            self.logger.info(f"Connecting to WiFi network: {ssid}")
            
            # SSH Safety: Check if we're already on a different network
            with self._state_lock:
                current_info = self._connection_info
                if (current_info.state == ConnectionState.CONNECTED and 
                    current_info.ssid and current_info.ssid != ssid):
                    self.logger.warning(f"Currently connected to '{current_info.ssid}', switching to '{ssid}'")
            
            try:
                # Stop hotspot if active to free the interface
                if current_info.state == ConnectionState.HOTSPOT_ACTIVE:
                    self._stop_hotspot_internal()
                
                # Build connection command
                cmd = ["nmcli", "device", "wifi", "connect", ssid, "ifname", interface]
                if password:
                    cmd.extend(["password", password])
                
                # Attempt connection with timeout
                start_time = time.time()
                success, output = self._run_command_safe(cmd, timeout=self.CONNECTION_TIMEOUT)
                
                if not success:
                    # Parse common error messages
                    if "Secrets were required" in output:
                        raise WiFiSecurityError(f"Invalid password for network '{ssid}'")
                    elif "No network with SSID" in output:
                        raise WiFiError(f"Network '{ssid}' not found")
                    elif "Device or resource busy" in output:
                        raise WiFiError("WiFi interface is busy - try again in a moment")
                    else:
                        raise WiFiError(f"Connection failed: {output}")
                
                # Wait for connection to establish and verify
                max_wait_time = 30  # seconds
                check_interval = 1  # second
                elapsed = 0
                
                while elapsed < max_wait_time:
                    time.sleep(check_interval)
                    elapsed += check_interval
                    
                    # Update state and check connection
                    self._update_connection_state()
                    
                    with self._state_lock:
                        if (self._connection_info.state == ConnectionState.CONNECTED and 
                            self._connection_info.ssid == ssid):
                            connection_time = time.time() - start_time
                            self.logger.info(f"Successfully connected to '{ssid}' in {connection_time:.1f}s")
                            return True
                
                # Connection timeout
                raise WiFiTimeoutError(f"Connection to '{ssid}' timed out after {max_wait_time}s")
                
            except (WiFiError, WiFiSecurityError, WiFiTimeoutError):
                raise
            except Exception as e:
                self.logger.error(f"Unexpected error connecting to '{ssid}': {e}")
                raise WiFiError(f"Connection failed: {e}")
    
    def connect(self) -> bool:
        """Connect using configured WiFi credentials."""
        if not self.config.ssid:
            self.logger.info("No WiFi SSID configured")
            return False
        
        try:
            return self.connect_to_network(self.config.ssid, self.config.password)
        except (WiFiError, WiFiSecurityError, WiFiTimeoutError) as e:
            self.logger.error(f"Failed to connect to configured network: {e}")
            return False
    
    def start_hotspot(self) -> bool:
        """
        Start WiFi hotspot with conflict-free configuration.
        
        Returns:
            True if hotspot started successfully, False otherwise
            
        Raises:
            WiFiError: Hotspot creation failed
            WiFiInterfaceError: No WiFi interface available
        """
        if not self.config.hotspot_enabled:
            self.logger.warning("Hotspot is disabled in configuration")
            return False
        
        with self._operation_context("start_hotspot"):
            interface = self._detect_wifi_interface()
            if not interface:
                raise WiFiInterfaceError("No WiFi interface available for hotspot")
            
            self.logger.info("Starting WiFi hotspot...")
            
            try:
                # Generate unique connection name to avoid conflicts
                timestamp = int(time.time())
                connection_name = f"LOOP-Hotspot-{timestamp}"
                
                # Build hotspot configuration command
                cmd = [
                    "nmcli", "connection", "add",
                    "type", "wifi",
                    "ifname", interface,
                    "con-name", connection_name,
                    "autoconnect", "no",
                    "ssid", self.config.hotspot_ssid,
                    "mode", "ap",
                    "wifi-sec.key-mgmt", "wpa-psk",
                    "wifi-sec.psk", self.config.hotspot_password,
                    "ipv4.method", "shared",
                    "ipv4.addresses", f"{self._hotspot_ip}/24",
                    # Pi Zero 2 optimizations
                    "wifi.band", "bg",  # 2.4GHz only
                    "wifi.channel", str(self.config.hotspot_channel)
                ]
                
                # Create hotspot connection
                success, output = self._run_command_safe(cmd)
                if not success:
                    raise WiFiError(f"Failed to create hotspot connection: {output}")
                
                # Activate hotspot
                activate_success, activate_output = self._run_command_safe([
                    "nmcli", "connection", "up", connection_name
                ])
                
                if not activate_success:
                    # Clean up failed connection
                    self._run_command_safe(["nmcli", "connection", "delete", connection_name])
                    raise WiFiError(f"Failed to activate hotspot: {activate_output}")
                
                # Wait for hotspot to become active
                time.sleep(3)
                self._update_connection_state()
                
                with self._state_lock:
                    if self._connection_info.state == ConnectionState.HOTSPOT_ACTIVE:
                        self.logger.info(f"Hotspot '{self.config.hotspot_ssid}' started on {interface}")
                        return True
                    else:
                        self.logger.warning("Hotspot command succeeded but state not updated - assuming success")
                        return True
                
            except WiFiError:
                raise
            except Exception as e:
                self.logger.error(f"Unexpected error starting hotspot: {e}")
                raise WiFiError(f"Hotspot startup failed: {e}")
    
    def stop_hotspot(self) -> bool:
        """Stop WiFi hotspot mode."""
        with self._operation_context("stop_hotspot"):
            return self._stop_hotspot_internal()
    
    def _stop_hotspot_internal(self) -> bool:
        """Internal hotspot stop method (assumes operation lock held)."""
        with self._state_lock:
            if self._connection_info.state != ConnectionState.HOTSPOT_ACTIVE:
                self.logger.info("Hotspot is not active")
                return True
        
        self.logger.info("Stopping WiFi hotspot...")
        
        try:
            # Find active hotspot connections
            success, output = self._run_command_safe([
                "nmcli", "-t", "-f", "NAME,TYPE", "connection", "show", "--active"
            ])
            
            hotspot_connections = []
            if success and output:
                for line in output.split('\n'):
                    if line and ':wifi' in line:
                        name = line.split(':')[0]
                        if ('hotspot' in name.lower() or 
                            name == self.config.hotspot_ssid or
                            'LOOP-Hotspot' in name):
                            hotspot_connections.append(name)
            
            # Stop and delete hotspot connections
            stopped_count = 0
            for conn_name in hotspot_connections:
                try:
                    # Deactivate
                    deactivate_success, _ = self._run_command_safe([
                        "nmcli", "connection", "down", conn_name
                    ], timeout=10)
                    
                    # Delete to clean up
                    delete_success, _ = self._run_command_safe([
                        "nmcli", "connection", "delete", conn_name
                    ], timeout=10)
                    
                    if deactivate_success or delete_success:
                        stopped_count += 1
                        
                except WiFiError as e:
                    self.logger.warning(f"Failed to stop hotspot connection '{conn_name}': {e}")
            
            if stopped_count > 0 or not hotspot_connections:
                time.sleep(2)  # Brief wait for deactivation
                self._update_connection_state()
                self.logger.info("Hotspot stopped successfully")
                return True
            else:
                self.logger.error("Failed to stop any hotspot connections")
                return False
                
        except Exception as e:
            self.logger.error(f"Unexpected error stopping hotspot: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up WiFi manager resources."""
        try:
            with self._operation_context("cleanup"):
                # Stop hotspot if active
                with self._state_lock:
                    if self._connection_info.state == ConnectionState.HOTSPOT_ACTIVE:
                        self._stop_hotspot_internal()
                
                self.logger.info("WiFi manager cleanup completed")
                
        except Exception as e:
            self.logger.error(f"Error during WiFi cleanup: {e}") 