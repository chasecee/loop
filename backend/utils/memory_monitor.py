"""
Memory monitoring utility for Pi Zero 2 optimization.
"""

import gc
import os
import time
import threading
from typing import Optional, Dict, Any
from pathlib import Path
from utils.logger import get_logger

logger = get_logger("memory_monitor")

class MemoryMonitor:
    """Monitor system memory usage and enable low-memory mode when needed."""
    
    def __init__(self, check_interval: float = 30.0):
        """Initialize memory monitor."""
        self.check_interval = check_interval
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Memory thresholds (in MB)
        self.low_memory_threshold = 100   # Switch to low-memory mode below 100MB
        self.critical_memory_threshold = 50  # Force garbage collection below 50MB
        
        # State tracking
        self.current_memory_mb = 0
        self.memory_available_mb = 0
        self.low_memory_mode = False
        self.last_gc_time = 0
        self.gc_cooldown = 30  # Don't run GC more than once per 30 seconds
        
        # Pi-specific optimizations
        self.is_pi_zero = self._detect_pi_zero()
        if self.is_pi_zero:
            self.low_memory_threshold = 150  # More conservative on Pi Zero
            self.critical_memory_threshold = 75
            logger.info("Pi Zero detected - using conservative memory thresholds")
    
    def _detect_pi_zero(self) -> bool:
        """Detect if running on Pi Zero (less memory available)."""
        try:
            with open("/proc/cpuinfo", "r") as f:
                content = f.read()
                # Pi Zero has different hardware identifiers
                return any(model in content.lower() for model in [
                    "pi zero", "bcm2708", "armv6"
                ])
        except Exception:
            return False
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get current memory information."""
        try:
            # Read from /proc/meminfo (most accurate on Linux)
            meminfo = {}
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith(("MemTotal:", "MemAvailable:", "MemFree:", "Buffers:", "Cached:")):
                        key, value = line.split(":")
                        # Convert from kB to MB
                        meminfo[key.strip()] = int(value.strip().split()[0]) // 1024
            
            # Calculate available memory
            available_mb = meminfo.get("MemAvailable", 0)
            if available_mb == 0:
                # Fallback calculation for older kernels
                available_mb = (meminfo.get("MemFree", 0) + 
                               meminfo.get("Buffers", 0) + 
                               meminfo.get("Cached", 0))
            
            total_mb = meminfo.get("MemTotal", 0)
            used_mb = total_mb - available_mb
            
            return {
                "total_mb": total_mb,
                "used_mb": used_mb,
                "available_mb": available_mb,
                "usage_percent": (used_mb / total_mb * 100) if total_mb > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to read memory info: {e}")
            return {"total_mb": 0, "used_mb": 0, "available_mb": 0, "usage_percent": 0}
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                memory_info = self.get_memory_info()
                self.memory_available_mb = memory_info["available_mb"]
                self.current_memory_mb = memory_info["used_mb"]
                
                # Check if we should enter low-memory mode
                was_low_memory = self.low_memory_mode
                self.low_memory_mode = self.memory_available_mb < self.low_memory_threshold
                
                if self.low_memory_mode and not was_low_memory:
                    logger.warning(f"Entering low-memory mode: {self.memory_available_mb}MB available")
                elif not self.low_memory_mode and was_low_memory:
                    logger.info(f"Exiting low-memory mode: {self.memory_available_mb}MB available")
                
                # Force garbage collection if critically low on memory
                if (self.memory_available_mb < self.critical_memory_threshold and 
                    time.time() - self.last_gc_time > self.gc_cooldown):
                    logger.warning(f"Critical memory pressure: {self.memory_available_mb}MB available, forcing GC")
                    gc.collect()
                    self.last_gc_time = time.time()
                
                # Log memory stats periodically
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    logger.info(f"Memory: {memory_info['usage_percent']:.1f}% used, "
                               f"{self.memory_available_mb}MB available")
                
            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
            
            time.sleep(self.check_interval)
    
    def start(self):
        """Start memory monitoring."""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Memory monitoring started")
    
    def stop(self):
        """Stop memory monitoring."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Memory monitoring stopped")
    
    def is_low_memory(self) -> bool:
        """Check if system is in low-memory mode."""
        return self.low_memory_mode
    
    def get_available_memory_mb(self) -> int:
        """Get available memory in MB."""
        return self.memory_available_mb
    
    def suggest_cache_size(self, base_size: int, max_size: int) -> int:
        """Suggest optimal cache size based on available memory."""
        if self.low_memory_mode:
            # In low-memory mode, use minimal cache
            return min(base_size // 4, max_size // 8)
        elif self.memory_available_mb < self.low_memory_threshold * 1.5:
            # Approaching low memory, reduce cache size
            return min(base_size // 2, max_size // 4)
        else:
            # Normal memory, use full cache
            return min(base_size, max_size)
    
    def should_preload_frames(self) -> bool:
        """Check if it's safe to preload frames."""
        return not self.low_memory_mode and self.memory_available_mb > 200
    
    def force_cleanup(self):
        """Force memory cleanup."""
        logger.info("Forcing memory cleanup")
        gc.collect()
        self.last_gc_time = time.time() 