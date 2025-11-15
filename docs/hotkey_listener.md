# Hotkey Listener

The `HotkeyListener` module provides global hotkey detection for push-to-talk voice input activation in Zephyr.

## Features

- **Global Hotkey Registration**: Listen for keyboard events across all applications
- **Configurable Hotkey**: Support for various keys (default: backslash)
- **Debouncing**: Filter out accidental short presses with configurable minimum duration
- **Separate Callbacks**: Distinct callbacks for key press and release events
- **Error Handling**: Comprehensive error handling for hotkey registration failures

## Usage

### Basic Example

```python
from zephyr.hotkey_listener import HotkeyListener

def on_press():
    print("Key pressed - start recording")

def on_release():
    print("Key released - stop recording")

# Create listener
listener = HotkeyListener(
    hotkey='backslash',
    on_press_callback=on_press,
    on_release_callback=on_release,
    min_press_duration=100  # milliseconds
)

# Start listening
listener.start()

# ... do other work ...

# Stop listening
listener.stop()
```

### Context Manager

```python
from zephyr.hotkey_listener import HotkeyListener

with HotkeyListener(hotkey='backslash') as listener:
    listener.on_key_press(lambda: print("Pressed"))
    listener.on_key_release(lambda: print("Released"))
    # Listener automatically starts and stops
```

### Integration with Audio Capture

```python
from zephyr.hotkey_listener import HotkeyListener
from zephyr.audio_capture import AudioCapture

audio = AudioCapture()

def start_recording():
    audio.start_recording()
    print("Recording...")

def stop_recording():
    data = audio.stop_recording()
    print(f"Captured {len(data)} bytes")

listener = HotkeyListener(
    on_press_callback=start_recording,
    on_release_callback=stop_recording
)
listener.start()
```

## Configuration

### Supported Hotkeys

The following hotkey names are supported:

- `'backslash'` - The backslash key (\\)
- `'space'` - Space bar
- `'ctrl'` - Control key
- `'alt'` - Alt key
- `'shift'` - Shift key
- `'tab'` - Tab key
- `'enter'` - Enter/Return key
- `'esc'` - Escape key
- Any single character (e.g., `'a'`, `'z'`, `'1'`)

### Minimum Press Duration

The `min_press_duration` parameter (in milliseconds) filters out accidental short presses:

```python
listener = HotkeyListener(
    hotkey='backslash',
    min_press_duration=100  # Ignore presses shorter than 100ms
)
```

### Changing Hotkey

You can change the hotkey dynamically:

```python
listener = HotkeyListener(hotkey='backslash')
listener.start()

# Change to space bar
listener.set_hotkey('space')  # Automatically restarts listener
```

## API Reference

### HotkeyListener

#### Constructor

```python
HotkeyListener(
    hotkey: str = 'backslash',
    on_press_callback: Optional[Callable[[], None]] = None,
    on_release_callback: Optional[Callable[[], None]] = None,
    min_press_duration: int = 100
)
```

**Parameters:**
- `hotkey`: Name of the hotkey to listen for
- `on_press_callback`: Function called when key is pressed
- `on_release_callback`: Function called when key is released (after minimum duration)
- `min_press_duration`: Minimum press duration in milliseconds

#### Methods

##### start()
Start listening for hotkey events.

```python
listener.start()
```

##### stop()
Stop listening for hotkey events.

```python
listener.stop()
```

##### set_hotkey(hotkey: str)
Change the hotkey. Automatically restarts listener if running.

```python
listener.set_hotkey('space')
```

##### on_key_press(callback: Callable[[], None])
Set the callback for key press events.

```python
listener.on_key_press(lambda: print("Pressed"))
```

##### on_key_release(callback: Callable[[], None])
Set the callback for key release events.

```python
listener.on_key_release(lambda: print("Released"))
```

##### is_running() -> bool
Check if listener is currently running.

```python
if listener.is_running():
    print("Listener is active")
```

##### is_key_pressed() -> bool
Check if hotkey is currently pressed.

```python
if listener.is_key_pressed():
    print("Key is held down")
```

## Error Handling

### Exceptions

- `HotkeyError`: Base exception for hotkey-related errors
- `HotkeyRegistrationError`: Raised when hotkey registration fails

### Example

```python
from zephyr.hotkey_listener import HotkeyListener, HotkeyRegistrationError

try:
    listener = HotkeyListener(hotkey='invalid_key')
except HotkeyRegistrationError as e:
    print(f"Invalid hotkey: {e}")
```

## Requirements

- Python 3.8+
- pynput library

Install with:
```bash
pip install pynput
```

## Implementation Details

### Debouncing

The listener implements debouncing to prevent accidental activations:

1. Key press is detected and timestamp recorded
2. Callbacks are triggered immediately on press
3. On key release, press duration is calculated
4. If duration < minimum, release callback is NOT triggered
5. If duration >= minimum, release callback is triggered

This ensures that only intentional key presses trigger the full press/release cycle.

### Threading

The hotkey listener runs in a separate thread managed by pynput. Callbacks are executed in this thread, so ensure thread-safety if accessing shared resources.

## Examples

See `examples/hotkey_listener_example.py` for a complete working example demonstrating integration with audio capture.

## Testing

Run the unit tests:

```bash
python test_hotkey_listener.py
```

The test suite covers:
- Initialization
- Hotkey parsing
- Callback registration
- State management
- Error handling
