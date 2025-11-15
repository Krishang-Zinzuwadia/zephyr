# Input Simulation Module

The input simulation module provides keyboard input simulation for both X11 and Wayland display servers, enabling Zephyr to type transcribed text into the active application.

## Features

- **Automatic Display Server Detection**: Detects X11 or Wayland and uses the appropriate backend
- **Streaming Text Updates**: Supports real-time text updates as transcription improves
- **Text Replacement**: Can delete and replace previously typed text
- **Configurable Typing Speed**: Adjustable characters per second
- **Clipboard Fallback**: Falls back to clipboard-based input if direct typing fails
- **Special Character Support**: Handles Unicode, punctuation, and special characters

## Architecture

### Components

1. **InputSimulator (Base Class)**: Provides common functionality and interface
2. **X11InputSimulator**: Implementation for X11 display servers using python-xlib
3. **WaylandInputSimulator**: Implementation for Wayland display servers using python-evdev
4. **X11Backend**: Low-level X11 keyboard event simulation
5. **WaylandBackend**: Low-level Wayland keyboard event simulation via uinput

### Display Server Detection

The module automatically detects the display server by checking:
1. `XDG_SESSION_TYPE` environment variable
2. `WAYLAND_DISPLAY` environment variable (for Wayland)
3. `DISPLAY` environment variable (for X11)

## Usage

### Basic Usage

```python
from zephyr.input_simulator import InputSimulator

# Create simulator (auto-detects display server)
simulator = InputSimulator.create(typing_speed=50)

# Check if a window is focused
if simulator.is_input_field_focused():
    # Type text
    simulator.type_text("Hello, world!")
```

### Streaming Mode

Streaming mode allows real-time text updates as transcription improves:

```python
# Start streaming mode
simulator.start_streaming_input()

# Type initial transcription
simulator.update_text("This is a test")

# Update with improved transcription (deletes old text and types new)
simulator.update_text("This is a demonstration")

# Append additional text
simulator.append_text(" of streaming input.")

# Finalize when done
simulator.finalize_input()
```

### Error Handling

```python
from zephyr.input_simulator import (
    InputSimulator,
    NoFocusedWindowError,
    TypingFailedError
)

try:
    simulator = InputSimulator.create()
    simulator.type_text("Hello!")
except NoFocusedWindowError:
    print("No window is focused")
except TypingFailedError as e:
    print(f"Typing failed: {e}")
```

## Configuration

The InputSimulator accepts the following configuration parameters:

- **typing_speed** (int): Characters per second (default: 50)
- **use_clipboard_fallback** (bool): Use clipboard if direct typing fails (default: True)

## Requirements

### X11 Backend

- **python-xlib**: For X11 keyboard event simulation
  ```bash
  pip install python-xlib
  ```

### Wayland Backend

- **python-evdev**: For Wayland keyboard event simulation
  ```bash
  pip install evdev
  ```
- **uinput permissions**: User must have access to `/dev/uinput`
  - Add user to `input` group: `sudo usermod -a -G input $USER`
  - Or create udev rule for `/dev/uinput`

## Implementation Details

### X11 Backend

The X11 backend uses python-xlib to:
1. Connect to the X11 display server
2. Build a keycode mapping from characters to X11 keycodes
3. Simulate keyboard events using the XTEST extension
4. Handle shift key for uppercase and special characters

### Wayland Backend

The Wayland backend uses python-evdev to:
1. Create a virtual keyboard device via uinput
2. Map characters to evdev key codes
3. Simulate key press and release events
4. Handle shift key for uppercase and special characters

### Text Replacement

When updating text in streaming mode:
1. Track the number of characters typed
2. Simulate backspace key presses to delete old text
3. Type the new text character by character
4. Update the character count

### Clipboard Fallback

If direct typing fails, the module can fall back to clipboard-based input:
1. Copy text to clipboard using `xclip` (X11) or `wl-copy` (Wayland)
2. User can paste manually with Ctrl+V
3. Future enhancement: Automatically simulate Ctrl+V

## Limitations

### Current Limitations

1. **Cursor Position**: Does not preserve cursor position or text selection state
2. **Accessibility**: Limited input field detection (assumes focused window has input field)
3. **Wayland Compositor Support**: Focused window detection varies by compositor
4. **Clipboard Paste**: Clipboard fallback requires manual paste or additional implementation

### Future Enhancements

1. Use accessibility APIs for better input field detection
2. Implement automatic Ctrl+V simulation for clipboard fallback
3. Support for more Wayland compositors in focused window detection
4. Cursor position preservation using accessibility APIs

## Testing

Run the example to test input simulation:

```bash
python3 examples/input_simulator_example.py
```

This will:
1. Detect the display server
2. Check for a focused window
3. Type example text with various features
4. Demonstrate streaming mode with text updates

## Troubleshooting

### X11: "Failed to connect to X11 display"

- Ensure `DISPLAY` environment variable is set
- Check X11 server is running
- Verify python-xlib is installed

### Wayland: "Permission denied accessing /dev/uinput"

- Add user to input group: `sudo usermod -a -G input $USER`
- Log out and log back in
- Or create udev rule for /dev/uinput

### "No keycode mapping found for character"

- Some special Unicode characters may not have key mappings
- Use clipboard fallback for unsupported characters
- Report missing characters for future enhancement

### Typing is too fast/slow

- Adjust `typing_speed` parameter
- Lower values = slower typing
- Higher values = faster typing
- Recommended range: 20-100 characters per second
