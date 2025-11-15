"""
Wayland input backend using python-evdev and uinput

Provides keyboard event simulation for Wayland display servers
"""

import time
import logging
import subprocess
from typing import Optional

try:
    import evdev
    from evdev import UInput, ecodes as e
    EVDEV_AVAILABLE = True
except ImportError:
    EVDEV_AVAILABLE = False
    evdev = None
    UInput = None
    e = None


logger = logging.getLogger(__name__)


class WaylandBackend:
    """
    Wayland input backend using python-evdev and uinput
    
    Creates a virtual keyboard device to simulate keyboard input.
    Requires appropriate permissions for /dev/uinput.
    """
    
    def __init__(self, char_delay: float = 0.02):
        """
        Initialize Wayland backend
        
        Args:
            char_delay: Delay between characters in seconds
        
        Raises:
            ImportError: If python-evdev is not available
            PermissionError: If uinput access is denied
        """
        if not EVDEV_AVAILABLE:
            raise ImportError(
                "python-evdev is required for Wayland input simulation. "
                "Install it with: pip install evdev"
            )
        
        self.char_delay = char_delay
        self._uinput = None
        
        # Initialize virtual keyboard
        self._initialize_uinput()
        
        # Build key mapping
        self._key_map = self._build_key_map()
        
        logger.info("Wayland backend initialized")
    
    def _initialize_uinput(self) -> None:
        """Initialize uinput virtual keyboard device"""
        try:
            # Define capabilities for the virtual keyboard
            # Include all keyboard keys
            capabilities = {
                e.EV_KEY: [
                    # Letter keys
                    e.KEY_A, e.KEY_B, e.KEY_C, e.KEY_D, e.KEY_E, e.KEY_F, e.KEY_G,
                    e.KEY_H, e.KEY_I, e.KEY_J, e.KEY_K, e.KEY_L, e.KEY_M, e.KEY_N,
                    e.KEY_O, e.KEY_P, e.KEY_Q, e.KEY_R, e.KEY_S, e.KEY_T, e.KEY_U,
                    e.KEY_V, e.KEY_W, e.KEY_X, e.KEY_Y, e.KEY_Z,
                    
                    # Number keys
                    e.KEY_0, e.KEY_1, e.KEY_2, e.KEY_3, e.KEY_4,
                    e.KEY_5, e.KEY_6, e.KEY_7, e.KEY_8, e.KEY_9,
                    
                    # Special keys
                    e.KEY_SPACE, e.KEY_ENTER, e.KEY_TAB, e.KEY_BACKSPACE,
                    e.KEY_ESC, e.KEY_DELETE,
                    
                    # Modifier keys
                    e.KEY_LEFTSHIFT, e.KEY_RIGHTSHIFT,
                    e.KEY_LEFTCTRL, e.KEY_RIGHTCTRL,
                    e.KEY_LEFTALT, e.KEY_RIGHTALT,
                    
                    # Punctuation and symbols
                    e.KEY_MINUS, e.KEY_EQUAL, e.KEY_LEFTBRACE, e.KEY_RIGHTBRACE,
                    e.KEY_SEMICOLON, e.KEY_APOSTROPHE, e.KEY_GRAVE,
                    e.KEY_BACKSLASH, e.KEY_COMMA, e.KEY_DOT, e.KEY_SLASH,
                ]
            }
            
            # Create virtual keyboard device
            self._uinput = UInput(
                capabilities,
                name='zephyr-virtual-keyboard',
                vendor=0x1234,
                product=0x5678,
                version=1
            )
            
            # Small delay to ensure device is ready
            time.sleep(0.1)
            
            logger.debug("Created virtual keyboard device")
            
        except PermissionError as err:
            logger.error(f"Permission denied accessing /dev/uinput: {err}")
            raise PermissionError(
                "Permission denied accessing /dev/uinput. "
                "You may need to add your user to the 'input' group or "
                "set up udev rules for /dev/uinput."
            )
        except Exception as err:
            logger.error(f"Failed to initialize uinput: {err}")
            raise RuntimeError(f"Failed to initialize uinput: {err}")
    
    def _build_key_map(self) -> dict:
        """
        Build mapping from characters to evdev key codes
        
        Returns:
            Dictionary mapping characters to (keycode, needs_shift) tuples
        """
        key_map = {
            # Lowercase letters
            'a': (e.KEY_A, False), 'b': (e.KEY_B, False), 'c': (e.KEY_C, False),
            'd': (e.KEY_D, False), 'e': (e.KEY_E, False), 'f': (e.KEY_F, False),
            'g': (e.KEY_G, False), 'h': (e.KEY_H, False), 'i': (e.KEY_I, False),
            'j': (e.KEY_J, False), 'k': (e.KEY_K, False), 'l': (e.KEY_L, False),
            'm': (e.KEY_M, False), 'n': (e.KEY_N, False), 'o': (e.KEY_O, False),
            'p': (e.KEY_P, False), 'q': (e.KEY_Q, False), 'r': (e.KEY_R, False),
            's': (e.KEY_S, False), 't': (e.KEY_T, False), 'u': (e.KEY_U, False),
            'v': (e.KEY_V, False), 'w': (e.KEY_W, False), 'x': (e.KEY_X, False),
            'y': (e.KEY_Y, False), 'z': (e.KEY_Z, False),
            
            # Uppercase letters
            'A': (e.KEY_A, True), 'B': (e.KEY_B, True), 'C': (e.KEY_C, True),
            'D': (e.KEY_D, True), 'E': (e.KEY_E, True), 'F': (e.KEY_F, True),
            'G': (e.KEY_G, True), 'H': (e.KEY_H, True), 'I': (e.KEY_I, True),
            'J': (e.KEY_J, True), 'K': (e.KEY_K, True), 'L': (e.KEY_L, True),
            'M': (e.KEY_M, True), 'N': (e.KEY_N, True), 'O': (e.KEY_O, True),
            'P': (e.KEY_P, True), 'Q': (e.KEY_Q, True), 'R': (e.KEY_R, True),
            'S': (e.KEY_S, True), 'T': (e.KEY_T, True), 'U': (e.KEY_U, True),
            'V': (e.KEY_V, True), 'W': (e.KEY_W, True), 'X': (e.KEY_X, True),
            'Y': (e.KEY_Y, True), 'Z': (e.KEY_Z, True),
            
            # Numbers
            '0': (e.KEY_0, False), '1': (e.KEY_1, False), '2': (e.KEY_2, False),
            '3': (e.KEY_3, False), '4': (e.KEY_4, False), '5': (e.KEY_5, False),
            '6': (e.KEY_6, False), '7': (e.KEY_7, False), '8': (e.KEY_8, False),
            '9': (e.KEY_9, False),
            
            # Special characters (with shift)
            '!': (e.KEY_1, True), '@': (e.KEY_2, True), '#': (e.KEY_3, True),
            '$': (e.KEY_4, True), '%': (e.KEY_5, True), '^': (e.KEY_6, True),
            '&': (e.KEY_7, True), '*': (e.KEY_8, True), '(': (e.KEY_9, True),
            ')': (e.KEY_0, True),
            
            # Punctuation
            ' ': (e.KEY_SPACE, False),
            '\n': (e.KEY_ENTER, False),
            '\t': (e.KEY_TAB, False),
            '-': (e.KEY_MINUS, False),
            '_': (e.KEY_MINUS, True),
            '=': (e.KEY_EQUAL, False),
            '+': (e.KEY_EQUAL, True),
            '[': (e.KEY_LEFTBRACE, False),
            '{': (e.KEY_LEFTBRACE, True),
            ']': (e.KEY_RIGHTBRACE, False),
            '}': (e.KEY_RIGHTBRACE, True),
            ';': (e.KEY_SEMICOLON, False),
            ':': (e.KEY_SEMICOLON, True),
            "'": (e.KEY_APOSTROPHE, False),
            '"': (e.KEY_APOSTROPHE, True),
            '`': (e.KEY_GRAVE, False),
            '~': (e.KEY_GRAVE, True),
            '\\': (e.KEY_BACKSLASH, False),
            '|': (e.KEY_BACKSLASH, True),
            ',': (e.KEY_COMMA, False),
            '<': (e.KEY_COMMA, True),
            '.': (e.KEY_DOT, False),
            '>': (e.KEY_DOT, True),
            '/': (e.KEY_SLASH, False),
            '?': (e.KEY_SLASH, True),
        }
        
        logger.debug(f"Built key map with {len(key_map)} entries")
        return key_map
    
    def get_focused_window(self) -> Optional[str]:
        """
        Get the currently focused window
        
        Returns:
            Window information as string, or None if unavailable
        
        Note:
            Getting focused window on Wayland is compositor-specific.
            This implementation tries common methods but may not work
            on all Wayland compositors.
        """
        # Try swaymsg for Sway/i3
        try:
            result = subprocess.run(
                ["swaymsg", "-t", "get_tree"],
                capture_output=True,
                text=True,
                timeout=1.0
            )
            if result.returncode == 0:
                # Parse JSON to find focused window
                import json
                tree = json.loads(result.stdout)
                focused = self._find_focused_node(tree)
                if focused:
                    return focused.get('name', 'Unknown')
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
            pass
        
        # Try hyprctl for Hyprland
        try:
            result = subprocess.run(
                ["hyprctl", "activewindow"],
                capture_output=True,
                text=True,
                timeout=1.0
            )
            if result.returncode == 0:
                # Parse output to get window title
                for line in result.stdout.split('\n'):
                    if line.strip().startswith('title:'):
                        return line.split(':', 1)[1].strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Fallback: assume a window is focused
        logger.debug("Could not determine focused window on Wayland")
        return "wayland-window"
    
    def _find_focused_node(self, node: dict) -> Optional[dict]:
        """Recursively find focused node in Sway tree"""
        if node.get('focused'):
            return node
        
        for child in node.get('nodes', []) + node.get('floating_nodes', []):
            result = self._find_focused_node(child)
            if result:
                return result
        
        return None
    
    def type_text(self, text: str) -> bool:
        """
        Type text character by character using uinput
        
        Args:
            text: Text to type
        
        Returns:
            True if successful, False otherwise
        """
        if self._uinput is None:
            logger.error("uinput device not initialized")
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
        # Look up key code for character
        if char in self._key_map:
            keycode, needs_shift = self._key_map[char]
            return self._press_key(keycode, needs_shift)
        else:
            logger.warning(f"No key mapping for character: '{char}' (U+{ord(char):04X})")
            return False
    
    def _press_key(self, keycode: int, needs_shift: bool) -> bool:
        """
        Press and release a key
        
        Args:
            keycode: evdev key code to press
            needs_shift: Whether to hold shift key
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Press shift if needed
            if needs_shift:
                self._uinput.write(e.EV_KEY, e.KEY_LEFTSHIFT, 1)
                self._uinput.syn()
            
            # Press the key
            self._uinput.write(e.EV_KEY, keycode, 1)
            self._uinput.syn()
            
            # Release the key
            self._uinput.write(e.EV_KEY, keycode, 0)
            self._uinput.syn()
            
            # Release shift if needed
            if needs_shift:
                self._uinput.write(e.EV_KEY, e.KEY_LEFTSHIFT, 0)
                self._uinput.syn()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to press key {keycode}: {e}")
            return False
    
    def press_backspace(self, count: int) -> bool:
        """
        Press backspace key multiple times
        
        Args:
            count: Number of times to press backspace
        
        Returns:
            True if successful, False otherwise
        """
        if self._uinput is None:
            logger.error("uinput device not initialized")
            return False
        
        if count <= 0:
            return True
        
        try:
            # Press backspace multiple times
            for _ in range(count):
                self._uinput.write(e.EV_KEY, e.KEY_BACKSPACE, 1)
                self._uinput.syn()
                self._uinput.write(e.EV_KEY, e.KEY_BACKSPACE, 0)
                self._uinput.syn()
                
                # Small delay between backspaces
                if self.char_delay > 0:
                    time.sleep(self.char_delay)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to press backspace: {e}")
            return False
    
    def __del__(self):
        """Cleanup uinput device"""
        if self._uinput is not None:
            try:
                self._uinput.close()
            except Exception:
                pass
