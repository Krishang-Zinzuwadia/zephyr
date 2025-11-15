"""
X11 input backend using python-xlib

Provides keyboard event simulation for X11 display servers
"""

import time
import logging
from typing import Optional

try:
    from Xlib import X, XK, display
    from Xlib.ext import xtest
    XLIB_AVAILABLE = True
except ImportError:
    XLIB_AVAILABLE = False
    display = None
    X = None
    XK = None
    xtest = None


logger = logging.getLogger(__name__)


class X11Backend:
    """
    X11 input backend using python-xlib
    
    Simulates keyboard input by sending X11 events directly to the X server.
    """
    
    def __init__(self, char_delay: float = 0.02):
        """
        Initialize X11 backend
        
        Args:
            char_delay: Delay between characters in seconds
        
        Raises:
            ImportError: If python-xlib is not available
        """
        if not XLIB_AVAILABLE:
            raise ImportError(
                "python-xlib is required for X11 input simulation. "
                "Install it with: pip install python-xlib"
            )
        
        self.char_delay = char_delay
        self._display = None
        self._root = None
        
        # Initialize X11 display connection
        self._initialize_display()
        
        # Build keycode mapping
        self._keycode_map = self._build_keycode_map()
        
        logger.info("X11 backend initialized")
    
    def _initialize_display(self) -> None:
        """Initialize X11 display connection"""
        try:
            self._display = display.Display()
            self._root = self._display.screen().root
            logger.debug("Connected to X11 display")
        except Exception as e:
            logger.error(f"Failed to connect to X11 display: {e}")
            raise RuntimeError(f"Failed to connect to X11 display: {e}")
    
    def _build_keycode_map(self) -> dict:
        """
        Build mapping from characters to X11 keycodes
        
        Returns:
            Dictionary mapping characters to (keycode, shift_needed) tuples
        """
        keycode_map = {}
        
        if self._display is None:
            return keycode_map
        
        # Get keyboard mapping
        min_keycode = self._display.display.info.min_keycode
        max_keycode = self._display.display.info.max_keycode
        keymap = self._display.get_keyboard_mapping(min_keycode, max_keycode - min_keycode + 1)
        
        # Build character to keycode mapping
        for keycode_idx, keysyms in enumerate(keymap):
            keycode = min_keycode + keycode_idx
            
            if len(keysyms) > 0:
                # First keysym (without shift)
                keysym = keysyms[0]
                if keysym != 0:
                    char = XK.keysym_to_string(keysym)
                    if char:
                        keycode_map[char] = (keycode, False)
                
                # Second keysym (with shift)
                if len(keysyms) > 1:
                    keysym_shift = keysyms[1]
                    if keysym_shift != 0:
                        char_shift = XK.keysym_to_string(keysym_shift)
                        if char_shift:
                            keycode_map[char_shift] = (keycode, True)
        
        logger.debug(f"Built keycode map with {len(keycode_map)} entries")
        return keycode_map
    
    def get_focused_window(self) -> Optional[str]:
        """
        Get the currently focused window
        
        Returns:
            Window ID as string, or None if no window is focused
        """
        if self._display is None:
            return None
        
        try:
            # Get the window with input focus
            focus = self._display.get_input_focus()
            focused_window = focus.focus
            
            if focused_window and hasattr(focused_window, 'id'):
                window_id = focused_window.id
                
                # Try to get window name
                try:
                    window_name = focused_window.get_wm_name()
                    if window_name:
                        return f"{window_id} ({window_name})"
                except Exception:
                    pass
                
                return str(window_id)
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to get focused window: {e}")
            return None
    
    def type_text(self, text: str) -> bool:
        """
        Type text character by character using X11 events
        
        Args:
            text: Text to type
        
        Returns:
            True if successful, False otherwise
        """
        if self._display is None:
            logger.error("X11 display not initialized")
            return False
        
        if not text:
            return True
        
        try:
            for char in text:
                if not self._type_character(char):
                    logger.warning(f"Failed to type character: '{char}'")
                    # Continue with remaining characters
                
                # Delay between characters
                if self.char_delay > 0:
                    time.sleep(self.char_delay)
            
            # Flush events to X server
            self._display.sync()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to type text: {e}")
            return False
    
    def _type_character(self, char: str) -> bool:
        """
        Type a single character
        
        Args:
            char: Character to type
        
        Returns:
            True if successful, False otherwise
        """
        # Handle special characters
        if char == '\n':
            return self._press_key('Return', False)
        elif char == '\t':
            return self._press_key('Tab', False)
        elif char == ' ':
            return self._press_key('space', False)
        
        # Look up keycode for character
        if char in self._keycode_map:
            keycode, needs_shift = self._keycode_map[char]
            return self._press_keycode(keycode, needs_shift)
        else:
            # Try to find keysym for character
            try:
                keysym = XK.string_to_keysym(char)
                if keysym == 0:
                    # Try Unicode keysym
                    if len(char) == 1:
                        code_point = ord(char)
                        keysym = 0x01000000 | code_point
                
                if keysym != 0:
                    keycode = self._display.keysym_to_keycode(keysym)
                    if keycode != 0:
                        return self._press_keycode(keycode, False)
            except Exception as e:
                logger.debug(f"Failed to find keysym for '{char}': {e}")
            
            logger.warning(f"No keycode mapping found for character: '{char}' (U+{ord(char):04X})")
            return False
    
    def _press_key(self, key_name: str, needs_shift: bool) -> bool:
        """
        Press a named key
        
        Args:
            key_name: Name of the key (e.g., 'Return', 'Tab')
            needs_shift: Whether shift key should be held
        
        Returns:
            True if successful, False otherwise
        """
        try:
            keysym = XK.string_to_keysym(key_name)
            if keysym == 0:
                logger.warning(f"Unknown key name: {key_name}")
                return False
            
            keycode = self._display.keysym_to_keycode(keysym)
            if keycode == 0:
                logger.warning(f"No keycode for key: {key_name}")
                return False
            
            return self._press_keycode(keycode, needs_shift)
            
        except Exception as e:
            logger.error(f"Failed to press key '{key_name}': {e}")
            return False
    
    def _press_keycode(self, keycode: int, needs_shift: bool) -> bool:
        """
        Press and release a keycode
        
        Args:
            keycode: X11 keycode to press
            needs_shift: Whether to hold shift key
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get shift keycode if needed
            shift_keycode = None
            if needs_shift:
                shift_keysym = XK.string_to_keysym('Shift_L')
                shift_keycode = self._display.keysym_to_keycode(shift_keysym)
            
            # Press shift if needed
            if shift_keycode:
                xtest.fake_input(self._display, X.KeyPress, shift_keycode)
                self._display.sync()
            
            # Press and release the key
            xtest.fake_input(self._display, X.KeyPress, keycode)
            self._display.sync()
            xtest.fake_input(self._display, X.KeyRelease, keycode)
            self._display.sync()
            
            # Release shift if needed
            if shift_keycode:
                xtest.fake_input(self._display, X.KeyRelease, shift_keycode)
                self._display.sync()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to press keycode {keycode}: {e}")
            return False
    
    def press_backspace(self, count: int) -> bool:
        """
        Press backspace key multiple times
        
        Args:
            count: Number of times to press backspace
        
        Returns:
            True if successful, False otherwise
        """
        if self._display is None:
            logger.error("X11 display not initialized")
            return False
        
        if count <= 0:
            return True
        
        try:
            # Get backspace keycode
            backspace_keysym = XK.string_to_keysym('BackSpace')
            backspace_keycode = self._display.keysym_to_keycode(backspace_keysym)
            
            if backspace_keycode == 0:
                logger.error("Failed to get backspace keycode")
                return False
            
            # Press backspace multiple times
            for _ in range(count):
                xtest.fake_input(self._display, X.KeyPress, backspace_keycode)
                self._display.sync()
                xtest.fake_input(self._display, X.KeyRelease, backspace_keycode)
                self._display.sync()
                
                # Small delay between backspaces
                if self.char_delay > 0:
                    time.sleep(self.char_delay)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to press backspace: {e}")
            return False
    
    def __del__(self):
        """Cleanup X11 display connection"""
        if self._display is not None:
            try:
                self._display.close()
            except Exception:
                pass
