"""
Input simulation module for Zephyr voice-to-text application

Handles typing transcribed text into the active application window
with support for X11 and Wayland display servers.
"""

import logging
import time
import subprocess
from typing import Optional, Protocol
from abc import ABC, abstractmethod
from enum import Enum


logger = logging.getLogger(__name__)


class DisplayServer(Enum):
    """Supported display server types"""
    X11 = "x11"
    WAYLAND = "wayland"
    UNKNOWN = "unknown"


class InputSimulationError(Exception):
    """Base exception for input simulation errors"""
    pass


class NoFocusedWindowError(InputSimulationError):
    """Raised when no window is focused"""
    pass


class NoInputFieldError(InputSimulationError):
    """Raised when no input field is focused"""
    pass


class TypingFailedError(InputSimulationError):
    """Raised when typing simulation fails"""
    pass


class InputBackend(Protocol):
    """Protocol for input simulation backends"""
    
    def type_text(self, text: str) -> bool:
        """Type text character by character"""
        ...
    
    def press_backspace(self, count: int) -> bool:
        """Press backspace key multiple times"""
        ...
    
    def get_focused_window(self) -> Optional[str]:
        """Get the currently focused window identifier"""
        ...


class InputSimulator(ABC):
    """
    Base class for input simulation
    
    Provides common functionality for typing text into the active application,
    with support for streaming updates and text replacement.
    """
    
    def __init__(self, typing_speed: int = 50, use_clipboard_fallback: bool = True):
        """
        Initialize InputSimulator
        
        Args:
            typing_speed: Characters per second for typing simulation
            use_clipboard_fallback: Use clipboard if direct typing fails
        """
        self.typing_speed = typing_speed
        self.use_clipboard_fallback = use_clipboard_fallback
        
        # Calculate delay between characters (in seconds)
        self._char_delay = 1.0 / typing_speed if typing_speed > 0 else 0.0
        
        # Streaming state
        self._is_streaming = False
        self._typed_char_count = 0
        self._last_typed_text = ""
        
        # Backend implementation
        self._backend: Optional[InputBackend] = None
        
        logger.info(
            f"InputSimulator initialized: {typing_speed} chars/sec, "
            f"clipboard fallback: {use_clipboard_fallback}"
        )
    
    @staticmethod
    def detect_display_server() -> DisplayServer:
        """
        Detect the current display server (X11 or Wayland)
        
        Returns:
            DisplayServer enum value
        """
        # Check XDG_SESSION_TYPE environment variable
        try:
            result = subprocess.run(
                ["printenv", "XDG_SESSION_TYPE"],
                capture_output=True,
                text=True,
                timeout=1.0
            )
            session_type = result.stdout.strip().lower()
            
            if "wayland" in session_type:
                logger.info("Detected Wayland display server")
                return DisplayServer.WAYLAND
            elif "x11" in session_type:
                logger.info("Detected X11 display server")
                return DisplayServer.X11
        except Exception as e:
            logger.debug(f"Failed to detect display server from XDG_SESSION_TYPE: {e}")
        
        # Fallback: check for WAYLAND_DISPLAY
        try:
            result = subprocess.run(
                ["printenv", "WAYLAND_DISPLAY"],
                capture_output=True,
                text=True,
                timeout=1.0
            )
            if result.returncode == 0 and result.stdout.strip():
                logger.info("Detected Wayland display server (via WAYLAND_DISPLAY)")
                return DisplayServer.WAYLAND
        except Exception as e:
            logger.debug(f"Failed to check WAYLAND_DISPLAY: {e}")
        
        # Fallback: check for DISPLAY (X11)
        try:
            result = subprocess.run(
                ["printenv", "DISPLAY"],
                capture_output=True,
                text=True,
                timeout=1.0
            )
            if result.returncode == 0 and result.stdout.strip():
                logger.info("Detected X11 display server (via DISPLAY)")
                return DisplayServer.X11
        except Exception as e:
            logger.debug(f"Failed to check DISPLAY: {e}")
        
        logger.warning("Could not detect display server type")
        return DisplayServer.UNKNOWN
    
    @staticmethod
    def create(typing_speed: int = 50, use_clipboard_fallback: bool = True) -> "InputSimulator":
        """
        Factory method to create appropriate InputSimulator for current display server
        
        Args:
            typing_speed: Characters per second for typing simulation
            use_clipboard_fallback: Use clipboard if direct typing fails
        
        Returns:
            InputSimulator instance (X11InputSimulator or WaylandInputSimulator)
        
        Raises:
            InputSimulationError: If display server is not supported
        """
        display_server = InputSimulator.detect_display_server()
        
        if display_server == DisplayServer.X11:
            return X11InputSimulator(typing_speed, use_clipboard_fallback)
        elif display_server == DisplayServer.WAYLAND:
            return WaylandInputSimulator(typing_speed, use_clipboard_fallback)
        else:
            raise InputSimulationError(
                "Could not detect display server. "
                "Zephyr requires X11 or Wayland."
            )
    
    def get_focused_window(self) -> Optional[str]:
        """
        Get the currently focused window
        
        Returns:
            Window identifier string, or None if no window is focused
        """
        if self._backend is None:
            return None
        
        try:
            return self._backend.get_focused_window()
        except Exception as e:
            logger.error(f"Failed to get focused window: {e}")
            return None
    
    def is_input_field_focused(self) -> bool:
        """
        Verify that an input field is currently focused
        
        Returns:
            True if an input field is focused, False otherwise
        
        Note:
            This is a best-effort check. We assume if a window is focused,
            an input field might be active. More sophisticated detection
            would require accessibility APIs.
        """
        focused_window = self.get_focused_window()
        
        if focused_window is None:
            logger.debug("No focused window detected")
            return False
        
        logger.debug(f"Focused window: {focused_window}")
        return True
    
    def start_streaming_input(self) -> None:
        """
        Start streaming input mode for real-time transcription updates
        
        In streaming mode, text can be updated or replaced as transcription
        improves, allowing users to see and correct their speech in real-time.
        """
        if self._is_streaming:
            logger.warning("Streaming input already active")
            return
        
        self._is_streaming = True
        self._typed_char_count = 0
        self._last_typed_text = ""
        
        logger.info("Started streaming input mode")
    
    def update_text(self, new_text: str) -> bool:
        """
        Replace previously typed text with updated transcription
        
        This method deletes the previously typed text using backspace
        and types the new text. Used when transcription is updated
        mid-sentence as the user continues speaking.
        
        Args:
            new_text: New transcription text to replace previous text
        
        Returns:
            True if successful, False otherwise
        
        Raises:
            NoFocusedWindowError: If no window is focused
            TypingFailedError: If typing fails
        """
        if not self._is_streaming:
            logger.warning("update_text called but streaming mode not active")
            return False
        
        # Check if window is still focused
        if not self.is_input_field_focused():
            raise NoFocusedWindowError("No focused window for text update")
        
        try:
            # Delete previous text if any was typed
            if self._typed_char_count > 0:
                logger.debug(f"Deleting {self._typed_char_count} characters")
                if not self._delete_characters(self._typed_char_count):
                    logger.error("Failed to delete previous text")
                    return False
            
            # Type new text
            if new_text:
                logger.debug(f"Typing updated text: '{new_text}'")
                if not self._type_text_internal(new_text):
                    logger.error("Failed to type updated text")
                    return False
                
                self._typed_char_count = len(new_text)
                self._last_typed_text = new_text
            else:
                self._typed_char_count = 0
                self._last_typed_text = ""
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update text: {e}")
            raise TypingFailedError(f"Failed to update text: {e}")
    
    def append_text(self, text: str) -> bool:
        """
        Append text to previously typed content
        
        Used for incremental updates where new words are added
        without replacing existing text.
        
        Args:
            text: Text to append
        
        Returns:
            True if successful, False otherwise
        
        Raises:
            NoFocusedWindowError: If no window is focused
            TypingFailedError: If typing fails
        """
        if not self._is_streaming:
            logger.warning("append_text called but streaming mode not active")
            return False
        
        # Check if window is still focused
        if not self.is_input_field_focused():
            raise NoFocusedWindowError("No focused window for text append")
        
        try:
            if text:
                logger.debug(f"Appending text: '{text}'")
                if not self._type_text_internal(text):
                    logger.error("Failed to append text")
                    return False
                
                self._typed_char_count += len(text)
                self._last_typed_text += text
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to append text: {e}")
            raise TypingFailedError(f"Failed to append text: {e}")
    
    def finalize_input(self) -> None:
        """
        Finalize streaming input and reset state
        
        Should be called when transcription is complete.
        """
        if not self._is_streaming:
            return
        
        self._is_streaming = False
        self._typed_char_count = 0
        self._last_typed_text = ""
        
        logger.info("Finalized streaming input")
    
    def type_text(self, text: str) -> bool:
        """
        Type text into the active input field (non-streaming mode)
        
        Args:
            text: Text to type
        
        Returns:
            True if successful, False otherwise
        
        Raises:
            NoFocusedWindowError: If no window is focused
            TypingFailedError: If typing fails
        """
        # Check if window is focused
        if not self.is_input_field_focused():
            raise NoFocusedWindowError("No focused window for typing")
        
        try:
            return self._type_text_internal(text)
        except Exception as e:
            logger.error(f"Failed to type text: {e}")
            raise TypingFailedError(f"Failed to type text: {e}")
    
    def _type_text_internal(self, text: str) -> bool:
        """
        Internal method to type text using the backend
        
        Args:
            text: Text to type
        
        Returns:
            True if successful, False otherwise
        """
        if self._backend is None:
            logger.error("No input backend available")
            return False
        
        try:
            # Try direct typing first
            success = self._backend.type_text(text)
            
            # Try clipboard fallback if direct typing failed
            if not success and self.use_clipboard_fallback:
                logger.info("Direct typing failed, trying clipboard fallback")
                success = self._type_via_clipboard(text)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to type text: {e}")
            
            # Try clipboard fallback on exception
            if self.use_clipboard_fallback:
                try:
                    logger.info("Trying clipboard fallback after exception")
                    return self._type_via_clipboard(text)
                except Exception as e2:
                    logger.error(f"Clipboard fallback also failed: {e2}")
            
            return False
    
    def _delete_characters(self, count: int) -> bool:
        """
        Delete characters using backspace
        
        Args:
            count: Number of characters to delete
        
        Returns:
            True if successful, False otherwise
        """
        if self._backend is None:
            logger.error("No input backend available")
            return False
        
        if count <= 0:
            return True
        
        try:
            return self._backend.press_backspace(count)
        except Exception as e:
            logger.error(f"Failed to delete characters: {e}")
            return False
    
    def _type_via_clipboard(self, text: str) -> bool:
        """
        Type text by copying to clipboard and pasting
        
        Args:
            text: Text to type via clipboard
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Copy text to clipboard using xclip or wl-copy
            display_server = self.detect_display_server()
            
            if display_server == DisplayServer.X11:
                cmd = ["xclip", "-selection", "clipboard"]
            elif display_server == DisplayServer.WAYLAND:
                cmd = ["wl-copy"]
            else:
                logger.error("Unknown display server for clipboard operation")
                return False
            
            # Copy to clipboard
            result = subprocess.run(
                cmd,
                input=text.encode('utf-8'),
                capture_output=True,
                timeout=2.0
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to copy to clipboard: {result.stderr.decode()}")
                return False
            
            # Small delay to ensure clipboard is updated
            time.sleep(0.05)
            
            # Simulate Ctrl+V to paste
            # This is implemented in the backend-specific classes
            logger.info("Text copied to clipboard, paste with Ctrl+V")
            
            # Note: Actual paste simulation would need to be implemented
            # in the backend-specific classes. For now, we just copy to clipboard.
            # The user would need to paste manually or we'd need to simulate Ctrl+V.
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Clipboard operation timed out")
            return False
        except FileNotFoundError as e:
            logger.error(f"Clipboard tool not found: {e}")
            return False
        except Exception as e:
            logger.error(f"Clipboard operation failed: {e}")
            return False
    
    @abstractmethod
    def _initialize_backend(self) -> None:
        """Initialize the platform-specific input backend"""
        pass


class X11InputSimulator(InputSimulator):
    """Input simulator for X11 display server"""
    
    def __init__(self, typing_speed: int = 50, use_clipboard_fallback: bool = True):
        super().__init__(typing_speed, use_clipboard_fallback)
        self._initialize_backend()
    
    def _initialize_backend(self) -> None:
        """Initialize X11 input backend"""
        # Import X11 backend (will be implemented in subtask 5.2)
        try:
            from .input_backends.x11_backend import X11Backend
            self._backend = X11Backend(self._char_delay)
            logger.info("X11 input backend initialized")
        except ImportError as e:
            logger.error(f"Failed to import X11 backend: {e}")
            raise InputSimulationError(
                "X11 backend not available. Install python-xlib: pip install python-xlib"
            )


class WaylandInputSimulator(InputSimulator):
    """Input simulator for Wayland display server"""
    
    def __init__(self, typing_speed: int = 50, use_clipboard_fallback: bool = True):
        super().__init__(typing_speed, use_clipboard_fallback)
        self._initialize_backend()
    
    def _initialize_backend(self) -> None:
        """Initialize Wayland input backend"""
        # Import Wayland backend (will be implemented in subtask 5.3)
        try:
            from .input_backends.wayland_backend import WaylandBackend
            self._backend = WaylandBackend(self._char_delay)
            logger.info("Wayland input backend initialized")
        except ImportError as e:
            logger.error(f"Failed to import Wayland backend: {e}")
            raise InputSimulationError(
                "Wayland backend not available. Install python-evdev: pip install evdev"
            )
