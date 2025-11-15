"""
Zephyr - Voice-to-text input application for Linux
"""

__version__ = "0.1.0"
__author__ = "Zephyr Contributors"
__description__ = "Push-to-talk voice input for Linux"

# Export main daemon class
from .daemon import ZephyrDaemon

__all__ = ['ZephyrDaemon']
