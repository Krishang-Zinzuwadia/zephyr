"""
Hotkey listener module for Zephyr voice-to-text application

Handles global hotkey registration and detection for push-to-talk activation
"""

import logging
import time
from typing import Callable, Optional
from threading import Thread, Event

# Import dependencies with error handling
try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    keyboard = None


logger = logging.getLogger(__name__)


class HotkeyError(Exception):
    """Base exception for hotkey-related errors"""
    pass


class HotkeyRegistrationError(HotkeyError):
    """Raised when hotkey registration fails"""
    pass


class HotkeyListener:
    """
    Global hotkey listener for push-to-talk activation
    
    Listens for a configurable hotkey (default: backslash) and triggers
    callbacks on key press and release events. Includes debouncing to
    filter out accidental short presses.
    """
    
    # Mapping of hotkey names to pynput Key objects
    KEY_MAPPING = {
        'backslash': '\\',
        'space': keyboard.Key.space if PYNPUT_AVAILABLE else None,
        'ctrl': keyboard.Key.ctrl if PYNPUT_AVAILABLE else None,
        'ctrl_l': keyboard.Key.ctrl_l if PYNPUT_AVAILABLE else None,
        'ctrl_r': keyboard.Key.ctrl_r if PYNPUT_AVAILABLE else None,
        'alt': keyboard.Key.alt if PYNPUT_AVAILABLE else None,
        'alt_l': keyboard.Key.alt_l if PYNPUT_AVAILABLE else None,
        'alt_r': keyboard.Key.alt_r if PYNPUT_AVAILABLE else None,
        'shift': keyboard.Key.shift if PYNPUT_AVAILABLE else None,
        'tab': keyboard.Key.tab if PYNPUT_AVAILABLE else None,
        'enter': keyboard.Key.enter if PYNPUT_AVAILABLE else None,
        'esc': keyboard.Key.esc if PYNPUT_AVAILABLE else None,
        # Function keys
        'f1': keyboard.Key.f1 if PYNPUT_AVAILABLE else None,
        'f2': keyboard.Key.f2 if PYNPUT_AVAILABLE else None,
        'f3': keyboard.Key.f3 if PYNPUT_AVAILABLE else None,
        'f4': keyboard.Key.f4 if PYNPUT_AVAILABLE else None,
        'f5': keyboard.Key.f5 if PYNPUT_AVAILABLE else None,
        'f6': keyboard.Key.f6 if PYNPUT_AVAILABLE else None,
        'f7': keyboard.Key.f7 if PYNPUT_AVAILABLE else None,
        'f8': keyboard.Key.f8 if PYNPUT_AVAILABLE else None,
        'f9': keyboard.Key.f9 if PYNPUT_AVAILABLE else None,
        'f10': keyboard.Key.f10 if PYNPUT_AVAILABLE else None,
        'f11': keyboard.Key.f11 if PYNPUT_AVAILABLE else None,
        'f12': keyboard.Key.f12 if PYNPUT_AVAILABLE else None,
    }
    
    def __init__(
        self,
        hotkey: str = 'backslash',
        on_press_callback: Optional[Callable[[], None]] = None,
        on_release_callback: Optional[Callable[[], None]] = None,
        min_press_duration: int = 100
    ):
        """
        Initialize HotkeyListener
        
        Args:
            hotkey: Name of the hotkey to listen for (default: 'backslash')
            on_press_callback: Function to call when hotkey is pressed
            on_release_callback: Function to call when hotkey is released
            min_press_duration: Minimum press duration in milliseconds to trigger (default: 100)
        
        Raises:
            ImportError: If pynput is not installed
            HotkeyRegistrationError: If hotkey is invalid
        """
        if not PYNPUT_AVAILABLE:
            raise ImportError(
                "pynput is required for hotkey listening. "
                "Install it with: pip install pynput"
            )
        
        self.hotkey = hotkey
        self.on_press_callback = on_press_callback
        self.on_release_callback = on_release_callback
        self.min_press_duration = min_press_duration / 1000.0  # Convert to seconds
        
        # Listener state
        self._listener: Optional[keyboard.Listener] = None
        self._is_running = False
        self._stop_event = Event()
        
        # Key press tracking for debouncing
        self._key_pressed = False
        self._press_start_time: Optional[float] = None
        
        # Track currently pressed modifier keys
        self._pressed_modifiers = set()
        
        # Get the actual key to listen for
        self._target_key, self._required_modifiers = self._parse_hotkey(hotkey)
        
        logger.info(
            f"HotkeyListener initialized: hotkey='{hotkey}', "
            f"min_press_duration={min_press_duration}ms"
        )
    
    def _parse_hotkey(self, hotkey: str):
        """
        Parse hotkey string to pynput Key object or character
        
        Supports combinations like "ctrl+alt_r" or single keys like "backslash"
        
        Args:
            hotkey: Hotkey name or character, optionally with modifiers (e.g., "ctrl+alt_r")
        
        Returns:
            Tuple of (target_key, required_modifiers_set)
        
        Raises:
            HotkeyRegistrationError: If hotkey is invalid
        """
        # Parse combination (e.g., "ctrl+alt_r")
        if '+' in hotkey:
            parts = [p.strip().lower() for p in hotkey.split('+')]
            
            if len(parts) < 2:
                raise HotkeyRegistrationError(
                    f"Invalid hotkey combination: '{hotkey}'. "
                    f"Expected format: 'modifier+key' (e.g., 'ctrl+alt_r')"
                )
            
            # Last part is the target key, others are modifiers
            target_key_name = parts[-1]
            modifier_names = parts[:-1]
            
            # Parse target key
            if target_key_name in self.KEY_MAPPING:
                target_key = self.KEY_MAPPING[target_key_name]
                if target_key is None:
                    raise HotkeyRegistrationError(f"Key '{target_key_name}' is not available")
            elif len(target_key_name) == 1:
                target_key = target_key_name
            else:
                raise HotkeyRegistrationError(
                    f"Invalid target key: '{target_key_name}'. "
                    f"Must be a single character or one of: {', '.join(self.KEY_MAPPING.keys())}"
                )
            
            # Parse modifiers
            required_modifiers = set()
            for mod_name in modifier_names:
                if mod_name in self.KEY_MAPPING:
                    mod_key = self.KEY_MAPPING[mod_name]
                    if mod_key is None:
                        raise HotkeyRegistrationError(f"Modifier '{mod_name}' is not available")
                    required_modifiers.add(mod_key)
                else:
                    raise HotkeyRegistrationError(
                        f"Invalid modifier: '{mod_name}'. "
                        f"Must be one of: {', '.join(self.KEY_MAPPING.keys())}"
                    )
            
            return target_key, required_modifiers
        
        # Single key (no modifiers)
        if hotkey.lower() in self.KEY_MAPPING:
            key = self.KEY_MAPPING[hotkey.lower()]
            if key is None:
                raise HotkeyRegistrationError(f"Hotkey '{hotkey}' is not available")
            return key, set()
        
        # If it's a single character, use it directly
        if len(hotkey) == 1:
            return hotkey, set()
        
        # Otherwise, it's invalid
        raise HotkeyRegistrationError(
            f"Invalid hotkey: '{hotkey}'. Must be a single character, a named key, "
            f"or a combination like 'ctrl+alt_r'. Available keys: {', '.join(self.KEY_MAPPING.keys())}"
        )
    
    def set_hotkey(self, hotkey: str) -> None:
        """
        Change the hotkey
        
        Args:
            hotkey: New hotkey name or character
        
        Raises:
            HotkeyRegistrationError: If hotkey is invalid
        """
        was_running = self._is_running
        
        # Stop listener if running
        if was_running:
            self.stop()
        
        # Update hotkey
        self.hotkey = hotkey
        self._target_key, self._required_modifiers = self._parse_hotkey(hotkey)
        
        logger.info(f"Hotkey changed to: '{hotkey}'")
        
        # Restart listener if it was running
        if was_running:
            self.start()
    
    def start(self) -> None:
        """
        Start listening for hotkey events
        
        Raises:
            RuntimeError: If listener is already running
        """
        if self._is_running:
            raise RuntimeError("Hotkey listener is already running")
        
        logger.info(f"Starting hotkey listener for '{self.hotkey}'")
        
        # Reset state
        self._stop_event.clear()
        self._key_pressed = False
        self._press_start_time = None
        self._pressed_modifiers = set()
        
        # Create and start keyboard listener
        # Note: suppress=True requires root permissions, so we use modifier combinations
        # that don't type anything instead
        self._listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self._listener.start()
        self._is_running = True
        
        logger.info("Hotkey listener started")
    
    def stop(self) -> None:
        """
        Stop listening for hotkey events
        """
        if not self._is_running:
            return
        
        logger.info("Stopping hotkey listener")
        
        # Signal stop
        self._stop_event.set()
        
        # Stop listener
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception as e:
                # pynput sometimes has issues during cleanup, ignore them
                logger.debug(f"Error stopping listener (ignored): {e}")
            self._listener = None
        
        self._is_running = False
        self._key_pressed = False
        self._press_start_time = None
        self._pressed_modifiers = set()
        
        logger.info("Hotkey listener stopped")
    
    def _on_key_press(self, key):
        """
        Internal callback for key press events
        
        Args:
            key: The key that was pressed
        
        Returns:
            False to suppress the key, True/None to allow it
        """
        # Debug: log every key press
        if hasattr(key, 'char') and key.char is not None:
            logger.debug(f"Key pressed: char='{key.char}' (repr={repr(key.char)})")
        else:
            logger.debug(f"Key pressed: {key}")
        
        # Track modifier keys
        if self._is_modifier_key(key):
            self._pressed_modifiers.add(key)
            logger.debug(f"Modifier pressed: {key}, current modifiers: {self._pressed_modifiers}")
            # Don't suppress modifier keys alone
            return True
        
        # Check if this is our target key
        is_target = self._is_target_key(key)
        logger.debug(f"Comparing key to target: key={key}, target={self._target_key}, match={is_target}")
        if not is_target:
            logger.debug(f"Key {key} is not target key {self._target_key}")
            return True  # Allow non-target keys
        
        logger.debug(f"Target key {key} detected!")
        
        # Check if required modifiers are pressed
        if not self._are_modifiers_pressed():
            logger.debug(f"Target key pressed but required modifiers not satisfied")
            logger.debug(f"Required: {self._required_modifiers}, Pressed: {self._pressed_modifiers}")
            return True  # Allow key if modifiers not satisfied
        
        # Ignore if already pressed (key repeat)
        if self._key_pressed:
            return False  # Suppress key repeat
        
        # Mark key as pressed and record time
        self._key_pressed = True
        self._press_start_time = time.time()
        
        logger.debug(f"Hotkey '{self.hotkey}' pressed - SUPPRESSING KEY")
        
        # Trigger on_press callback immediately
        if self.on_press_callback is not None:
            try:
                self.on_press_callback()
            except Exception as e:
                logger.error(f"Error in on_press callback: {e}", exc_info=True)
        
        # Suppress the hotkey so it doesn't get typed
        return False
    
    def _on_key_release(self, key):
        """
        Internal callback for key release events
        
        Args:
            key: The key that was released
        
        Returns:
            False to suppress the key, True/None to allow it
        """
        # Track modifier keys
        if self._is_modifier_key(key):
            self._pressed_modifiers.discard(key)
            logger.debug(f"Modifier released: {key}, current modifiers: {self._pressed_modifiers}")
            return True  # Don't suppress modifier keys
        
        # Check if this is our target key
        if not self._is_target_key(key):
            return True  # Allow non-target keys
        
        # Ignore if not currently pressed
        if not self._key_pressed:
            return True  # Allow if we didn't handle the press
        
        # Calculate press duration
        press_duration = time.time() - self._press_start_time if self._press_start_time else 0
        
        # Reset state
        self._key_pressed = False
        self._press_start_time = None
        
        logger.debug(
            f"Hotkey '{self.hotkey}' released after {press_duration*1000:.1f}ms - SUPPRESSING KEY"
        )
        
        # Check if press duration meets minimum threshold
        if press_duration < self.min_press_duration:
            logger.debug(
                f"Press duration {press_duration*1000:.1f}ms below minimum "
                f"{self.min_press_duration*1000:.1f}ms, ignoring"
            )
            return False  # Still suppress even if too short
        
        # Trigger callbacks
        self._trigger_callbacks(press_duration)
        
        # Suppress the hotkey release so it doesn't get typed
        return False
    
    def _is_target_key(self, key) -> bool:
        """
        Check if the given key matches our target key
        
        Args:
            key: Key to check
        
        Returns:
            True if key matches target, False otherwise
        """
        try:
            # Handle character keys
            if hasattr(key, 'char') and key.char is not None:
                return key.char == self._target_key
            
            # Handle special keys
            return key == self._target_key
            
        except AttributeError:
            return False
    
    def _is_modifier_key(self, key) -> bool:
        """
        Check if the given key is a modifier key
        
        Args:
            key: Key to check
        
        Returns:
            True if key is a modifier, False otherwise
        """
        modifier_keys = {
            keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
            keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r,
            keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r,
        }
        return key in modifier_keys
    
    def _are_modifiers_pressed(self) -> bool:
        """
        Check if all required modifiers are currently pressed
        
        Returns:
            True if all required modifiers are pressed, False otherwise
        """
        if not self._required_modifiers:
            # No modifiers required
            return True
        
        # Check if all required modifiers are pressed
        # We need to handle both specific (ctrl_l, ctrl_r) and generic (ctrl) modifiers
        for required_mod in self._required_modifiers:
            # Check if the exact modifier is pressed
            if required_mod in self._pressed_modifiers:
                continue
            
            # Check for generic modifier equivalents
            # e.g., if ctrl_r is required, check if it's pressed
            # or if ctrl is required, check if ctrl_l or ctrl_r is pressed
            if required_mod == keyboard.Key.ctrl:
                if keyboard.Key.ctrl_l in self._pressed_modifiers or keyboard.Key.ctrl_r in self._pressed_modifiers:
                    continue
            elif required_mod == keyboard.Key.alt:
                if keyboard.Key.alt_l in self._pressed_modifiers or keyboard.Key.alt_r in self._pressed_modifiers:
                    continue
            elif required_mod == keyboard.Key.shift:
                if keyboard.Key.shift_l in self._pressed_modifiers or keyboard.Key.shift_r in self._pressed_modifiers:
                    continue
            
            # Required modifier not pressed
            return False
        
        return True
    
    def _trigger_callbacks(self, press_duration: float) -> None:
        """
        Trigger release callback
        
        Args:
            press_duration: Duration the key was pressed in seconds
        """
        # Call on_release callback
        if self.on_release_callback is not None:
            try:
                self.on_release_callback()
            except Exception as e:
                logger.error(f"Error in on_release callback: {e}", exc_info=True)
    
    def is_running(self) -> bool:
        """
        Check if listener is currently running
        
        Returns:
            True if running, False otherwise
        """
        return self._is_running
    
    def is_key_pressed(self) -> bool:
        """
        Check if hotkey is currently pressed
        
        Returns:
            True if pressed, False otherwise
        """
        return self._key_pressed
    
    def on_key_press(self, callback: Callable[[], None]) -> None:
        """
        Set callback for key press events
        
        Args:
            callback: Function to call when hotkey is pressed
        """
        self.on_press_callback = callback
        logger.debug("on_press callback set")
    
    def on_key_release(self, callback: Callable[[], None]) -> None:
        """
        Set callback for key release events
        
        Args:
            callback: Function to call when hotkey is released
        """
        self.on_release_callback = callback
        logger.debug("on_release callback set")
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stop listener"""
        self.stop()
    
    def __del__(self):
        """Destructor - ensure listener is stopped"""
        try:
            self.stop()
        except Exception:
            pass
