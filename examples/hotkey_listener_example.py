#!/usr/bin/env python3
"""
Example demonstrating HotkeyListener integration with AudioCapture

This example shows how to:
1. Set up a hotkey listener
2. Connect it to audio capture
3. Start recording on key press
4. Stop recording and process audio on key release
"""

import sys
import time
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from zephyr.hotkey_listener import HotkeyListener, HotkeyError
from zephyr.audio_capture import AudioCapture, AudioDeviceError


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main example function"""
    print("=" * 60)
    print("Zephyr Hotkey Listener + Audio Capture Example")
    print("=" * 60)
    print()
    print("This example demonstrates push-to-talk functionality:")
    print("1. Press and hold the backslash (\\) key to start recording")
    print("2. Speak while holding the key")
    print("3. Release the key to stop recording")
    print()
    print("Press Ctrl+C to exit")
    print("=" * 60)
    print()
    
    # Initialize audio capture
    try:
        audio_capture = AudioCapture(
            sample_rate=16000,
            channels=1,
            chunk_duration=1.0
        )
        print("✓ Audio capture initialized")
    except ImportError as e:
        print(f"✗ Failed to initialize audio capture: {e}")
        print("  Install required dependencies: pip install PyAudio numpy")
        return 1
    except AudioDeviceError as e:
        print(f"✗ Audio device error: {e}")
        return 1
    
    # Define callbacks for hotkey events
    def on_press():
        """Called when hotkey is pressed - start recording"""
        try:
            print("\n[RECORDING] Microphone activated - speak now...")
            audio_capture.start_recording()
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            print(f"✗ Error starting recording: {e}")
    
    def on_release():
        """Called when hotkey is released - stop recording and process"""
        try:
            print("[PROCESSING] Stopping recording...")
            audio_data = audio_capture.stop_recording()
            
            # Calculate duration
            duration = len(audio_data) / (16000 * 1 * 2)  # sample_rate * channels * bytes_per_sample
            
            print(f"✓ Recording complete: {len(audio_data)} bytes ({duration:.2f} seconds)")
            print("  (In a real application, this would be sent to speech recognition)")
            print()
            print("Ready for next recording...")
            
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            print(f"✗ Error stopping recording: {e}")
    
    # Initialize hotkey listener
    try:
        hotkey_listener = HotkeyListener(
            hotkey='backslash',
            on_press_callback=on_press,
            on_release_callback=on_release,
            min_press_duration=100  # 100ms minimum
        )
        print("✓ Hotkey listener initialized")
    except ImportError as e:
        print(f"✗ Failed to initialize hotkey listener: {e}")
        print("  Install required dependency: pip install pynput")
        audio_capture.release_device()
        return 1
    except HotkeyError as e:
        print(f"✗ Hotkey error: {e}")
        audio_capture.release_device()
        return 1
    
    # Start listening
    try:
        hotkey_listener.start()
        print("✓ Hotkey listener started")
        print()
        print("Ready! Press and hold backslash (\\) to record...")
        print()
        
        # Keep running until interrupted
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        # Clean up
        hotkey_listener.stop()
        audio_capture.release_device()
        print("✓ Cleanup complete")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
