"""
Resource monitoring utilities for Zephyr

Provides tools to monitor CPU and memory usage to ensure
resource optimization requirements are met.

Requirements: 9.1, 9.2, 9.3, 9.5
"""

import logging
import os
import threading
import time
from typing import Optional, Dict
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class ResourceUsage:
    """Resource usage snapshot"""
    cpu_percent: float  # CPU usage percentage
    memory_mb: float  # Memory usage in MB
    timestamp: float  # Unix timestamp


class ResourceMonitor:
    """
    Monitor CPU and memory usage of the Zephyr process
    
    Helps verify that resource optimization requirements are met:
    - Idle: <50MB RAM, <1% CPU
    - Active: <20% CPU during recording
    """
    
    def __init__(self, check_interval: float = 1.0):
        """
        Initialize ResourceMonitor
        
        Args:
            check_interval: Interval between resource checks in seconds
        """
        self.check_interval = check_interval
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Resource usage history
        self._usage_history: list[ResourceUsage] = []
        self._history_lock = threading.Lock()
        self._max_history_size = 60  # Keep last 60 samples
        
        # Try to import psutil for accurate monitoring
        try:
            import psutil
            self._psutil = psutil
            self._process = psutil.Process(os.getpid())
            self._psutil_available = True
            logger.info("ResourceMonitor initialized with psutil")
        except ImportError:
            self._psutil = None
            self._process = None
            self._psutil_available = False
            logger.warning(
                "psutil not available, resource monitoring will be limited. "
                "Install with: pip install psutil"
            )
    
    def start_monitoring(self) -> None:
        """Start background resource monitoring"""
        if self._monitoring:
            logger.warning("Resource monitoring already running")
            return
        
        if not self._psutil_available:
            logger.warning("Cannot start monitoring without psutil")
            return
        
        logger.info("Starting resource monitoring")
        
        self._monitoring = True
        self._stop_event.clear()
        
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop background resource monitoring"""
        if not self._monitoring:
            return
        
        logger.info("Stopping resource monitoring")
        
        self._monitoring = False
        self._stop_event.set()
        
        if self._monitor_thread is not None:
            self._monitor_thread.join(timeout=2.0)
            self._monitor_thread = None
    
    def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        while not self._stop_event.is_set():
            try:
                usage = self.get_current_usage()
                
                if usage is not None:
                    with self._history_lock:
                        self._usage_history.append(usage)
                        
                        # Trim history
                        if len(self._usage_history) > self._max_history_size:
                            self._usage_history.pop(0)
                
                # Sleep until next check
                self._stop_event.wait(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
    
    def get_current_usage(self) -> Optional[ResourceUsage]:
        """
        Get current resource usage
        
        Returns:
            ResourceUsage snapshot or None if monitoring unavailable
        """
        if not self._psutil_available or self._process is None:
            return None
        
        try:
            # Get CPU percentage (averaged over interval)
            cpu_percent = self._process.cpu_percent(interval=0.1)
            
            # Get memory usage in MB
            memory_info = self._process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)  # Convert bytes to MB
            
            return ResourceUsage(
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Error getting resource usage: {e}")
            return None
    
    def get_average_usage(self, seconds: int = 10) -> Optional[Dict[str, float]]:
        """
        Get average resource usage over recent period
        
        Args:
            seconds: Number of seconds to average over
        
        Returns:
            Dictionary with 'cpu_percent' and 'memory_mb' averages
        """
        with self._history_lock:
            if not self._usage_history:
                return None
            
            # Filter to recent samples
            cutoff_time = time.time() - seconds
            recent_samples = [
                u for u in self._usage_history
                if u.timestamp >= cutoff_time
            ]
            
            if not recent_samples:
                return None
            
            # Calculate averages
            avg_cpu = sum(u.cpu_percent for u in recent_samples) / len(recent_samples)
            avg_memory = sum(u.memory_mb for u in recent_samples) / len(recent_samples)
            
            return {
                'cpu_percent': avg_cpu,
                'memory_mb': avg_memory,
                'sample_count': len(recent_samples)
            }
    
    def check_idle_requirements(self) -> Dict[str, any]:
        """
        Check if idle resource requirements are met
        
        Requirements: 9.1, 9.2
        - RAM: <50MB when idle
        - CPU: <1% when idle
        
        Returns:
            Dictionary with check results
        """
        usage = self.get_current_usage()
        
        if usage is None:
            return {
                'available': False,
                'message': 'Resource monitoring not available'
            }
        
        ram_ok = usage.memory_mb < 50.0
        cpu_ok = usage.cpu_percent < 1.0
        
        return {
            'available': True,
            'ram_ok': ram_ok,
            'cpu_ok': cpu_ok,
            'ram_mb': usage.memory_mb,
            'cpu_percent': usage.cpu_percent,
            'message': (
                f"RAM: {usage.memory_mb:.1f}MB {'✓' if ram_ok else '✗ (>50MB)'}, "
                f"CPU: {usage.cpu_percent:.1f}% {'✓' if cpu_ok else '✗ (>1%)'}"
            )
        }
    
    def check_active_requirements(self) -> Dict[str, any]:
        """
        Check if active resource requirements are met
        
        Requirements: 9.3
        - CPU: <20% during recording
        
        Returns:
            Dictionary with check results
        """
        usage = self.get_current_usage()
        
        if usage is None:
            return {
                'available': False,
                'message': 'Resource monitoring not available'
            }
        
        cpu_ok = usage.cpu_percent < 20.0
        
        return {
            'available': True,
            'cpu_ok': cpu_ok,
            'cpu_percent': usage.cpu_percent,
            'message': (
                f"CPU: {usage.cpu_percent:.1f}% {'✓' if cpu_ok else '✗ (>20%)'}"
            )
        }
    
    def log_current_usage(self, state: str = "unknown") -> None:
        """
        Log current resource usage
        
        Args:
            state: Current state (e.g., "idle", "recording", "transcribing")
        """
        usage = self.get_current_usage()
        
        if usage is None:
            logger.info(f"Resource usage ({state}): monitoring not available")
            return
        
        logger.info(
            f"Resource usage ({state}): "
            f"CPU={usage.cpu_percent:.1f}%, "
            f"RAM={usage.memory_mb:.1f}MB"
        )
    
    def __enter__(self):
        """Context manager entry"""
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_monitoring()
