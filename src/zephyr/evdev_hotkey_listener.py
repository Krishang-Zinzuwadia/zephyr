"""
Evdev-based hotkey listener for Zephyr
Works better with sudo than pynput
"""

import logging
import threading
import time
from typing import Callable, Optional, Set
from pathlib import Path

try:
    import evdev
    from evdev import InputDevice, categorize, ecodes
    EVDEV_AVAILABLE = True
except ImportError:
    EVDEV_AVAILABLE = False
    evdev = None

logger = logging.getLogger(__name__)


class EvdevHotkeyListener:
    """Hotkey listener using evdev (works with sudo)"""
    
    def __init__(
        self,
        hotkey: str = '`',
        on_press_callback: Optional[Callable[[], None]] = None,
        on_release_callback: Optional[Callable[[], None]] = None,
        min_press_duration: int = 100
    ):
        if not EVDEV_AVAILABLE:
            raise ImportError("evdev is required. Install with: pip install evdev")
        
        self.hotkey = hotkey
        self.on_press_callback = on_press_callback
        self.on_release_callback = on_release_callback
        self.min_press_duration = min_press_duration / 1000.0
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._devices = []
        self._pressed_keys: Set[int] = set()
        self._hotkey_pressed = False
        self._press_start_time: Optional[float] = None
        
        # Parse hotkey
        self._target_key, self._required_modifiers = self._parse_hotkey(hotkey)
        
        logger.info(f"EvdevHotkeyListener initialized: hotkey='{hotkey}'")
    
    def _parse_hotkey(self, hotkey: str):
        """Parse hotkey string"""
        # Simple mapping for common keys
        key_map = {
            '`': ecodes.KEY_GRAVE,
            'space': ecodes.KEY_SPACE,
            'ctrl': ecodes.KEY_LEFTCTRL,
            'shift': ecodes.KEY_LEFTSHIFT,
            'alt': ecodes.KEY_LEFTALT,
        }
        
        if '+' in hotkey:
            parts = hotkey.lower().split('+')
            target = parts[-1]
            modifiers = set()
            
            for mod in parts[:-1]:
                if mod in key_map:
                    modifiers.add(key_map[mod])
            
            target_code = key_map.get(target, ecodes.KEY_GRAVE)
            return target_code, modifiers
        else:
            return key_map.get(hotkey.lower(), ecodes.KEY_GRAVE), set()
    
    def _find_keyboard_devices(self):
        """Find all keyboard input devices"""
        devices = []
        for path in Path('/dev/input').glob('event*'):
            try:
                device = InputDevice(str(path))
                # Check if it's a keyboard
                caps = device.capabilities()
                if ecodes.EV_KEY in caps:
                    devices.append(device)
                    logger.debug(f"Found keyboard: {device.name} at {path}")
            except (PermissionError, OSError) as e:
                logger.debug(f"Cannot access {path}: {e}")
        
        return devices
    
    def start(self):
        """Start listening for hotkey"""
        if self._running:
            return
        
        self._devices = self._find_keyboard_devices()
        if not self._devices:
            raise RuntimeError("No keyboard devices found. Run with sudo?")
        
        logger.info(f"Monitoring {len(self._devices)} keyboard device(s)")
        
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        
        logger.info("Evdev hotkey listener started")
    
    def stop(self):
        """Stop listening"""
        if not self._running:
            return
        
        self._running = False
        
        if self._thread:
            self._thread.join(timeout=1.0)
        
        for device in self._devices:
            try:
                device.close()
            except:
                pass
        
        self._devices = []
        logger.info("Evdev hotkey listener stopped")
    
    def _listen_loop(self):
        """Main listening loop"""
        while self._running:
            try:
                # Use select to monitor all devices
                import select
                r, w, x = select.select(self._devices, [], [], 0.1)
                
                for device in r:
                    try:
                        for event in device.read():
                            if event.type == ecodes.EV_KEY:
                                self._handle_key_event(event)
                    except (OSError, IOError):
                        # Device disconnected
                        pass
                        
            except Exception as e:
                logger.error(f"Error in listen loop: {e}")
                time.sleep(0.1)
    
    def _handle_key_event(self, event):
        """Handle a key event"""
        key_code = event.code
        key_state = event.value  # 0=release, 1=press, 2=hold
        
        # Track pressed keys
        if key_state == 1:  # Press
            self._pressed_keys.add(key_code)
            logger.info(f"KEY PRESS: code={key_code}, target={self._target_key}, pressed={self._pressed_keys}")
            
            # Check if this is our hotkey
            if key_code == self._target_key:
                # Check if required modifiers are pressed
                if self._required_modifiers.issubset(self._pressed_keys):
                    if not self._hotkey_pressed:
                        self._hotkey_pressed = True
                        self._press_start_time = time.time()
                        logger.info(f"Hotkey '{self.hotkey}' pressed")
                        
                        if self.on_press_callback:
                            try:
                                self.on_press_callback()
                            except Exception as e:
                                logger.error(f"Error in press callback: {e}")
        
        elif key_state == 0:  # Release
            if key_code in self._pressed_keys:
                self._pressed_keys.remove(key_code)
            
            logger.info(f"KEY RELEASE: code={key_code}, target={self._target_key}, was_pressed={self._hotkey_pressed}")
            
            # Check if hotkey was released
            if key_code == self._target_key and self._hotkey_pressed:
                press_duration = time.time() - self._press_start_time if self._press_start_time else 0
                self._hotkey_pressed = False
                self._press_start_time = None
                
                logger.info(f"Hotkey '{self.hotkey}' RELEASED after {press_duration*1000:.1f}ms - CALLING RELEASE CALLBACK")
                
                # Always call release callback if key was pressed, regardless of duration
                # This ensures push-to-talk behavior
                if self.on_release_callback:
                    try:
                        self.on_release_callback()
                        logger.info("Release callback completed")
                    except Exception as e:
                        logger.error(f"Error in release callback: {e}")
    
    def is_running(self):
        """Check if listener is running"""
        return self._running
