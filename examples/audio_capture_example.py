#!/usr/bin/env python3
"""
Example usage of AudioCapture module

This example demonstrates how to use the AudioCapture class to record
audio from the microphone with streaming support.
"""

import sys
import time
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.zephyr.audio_capture import (
    AudioCapture,
    AudioDeviceError,
    MicrophoneNotFoundError,
    PermissionDeniedError,
    DeviceBusyError,
    PYAUDIO_AVAILABLE,
    NUMPY_AVAILABLE
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def streaming_callback(audio_chunk: bytes):
    """
    Callback function for streaming audio chunks
    
    This would typically send the audio chunk to a speech recognition engine
    """
    logger.debug(f"Received audio chunk: {len(audio_chunk)} bytes")


def example_basic_recording():
    """Example: Basic audio recording"""
    print("\n" + "=" * 60)
    print("Example 1: Basic Audio Recording")
    print("=" * 60)
    
    if not PYAUDIO_AVAILABLE or not NUMPY_AVAILABLE:
        print("⚠ Dependencies not installed. Install with:")
        print("  pip install PyAudio numpy noisereduce")
        return
    
    try:
        # Create AudioCapture instance
        audio_capture = AudioCapture(
            sample_rate=16000,
            channels=1,
            chunk_duration=1.0
        )
        
        print("Press Enter to start recording...")
        input()
        
        # Start recording
        audio_capture.start_recording()
        print("🎤 Recording... (will record for 3 seconds)")
        
        # Record for 3 seconds
        for i in range(3):
            time.sleep(1)
            level = audio_capture.get_audio_level()
            print(f"  Audio level: {'█' * int(level * 50)}")
        
        # Stop recording
        audio_data = audio_capture.stop_recording()
        print(f"✓ Recording complete: {len(audio_data)} bytes captured")
        
        # Clean up
        audio_capture.release_device()
        
    except AudioDeviceError as e:
        print(f"✗ Audio device error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")


def example_streaming_recording():
    """Example: Streaming audio recording with callback"""
    print("\n" + "=" * 60)
    print("Example 2: Streaming Audio Recording")
    print("=" * 60)
    
    if not PYAUDIO_AVAILABLE or not NUMPY_AVAILABLE:
        print("⚠ Dependencies not installed. Install with:")
        print("  pip install PyAudio numpy noisereduce")
        return
    
    try:
        # Create AudioCapture instance
        audio_capture = AudioCapture(
            sample_rate=16000,
            channels=1,
            chunk_duration=1.0
        )
        
        print("Press Enter to start streaming recording...")
        input()
        
        # Start recording with streaming callback
        chunk_count = [0]  # Use list to modify in callback
        
        def chunk_callback(audio_chunk: bytes):
            chunk_count[0] += 1
            print(f"  Chunk {chunk_count[0]}: {len(audio_chunk)} bytes")
        
        audio_capture.start_recording(chunk_callback=chunk_callback)
        print("🎤 Recording with streaming... (will record for 3 seconds)")
        
        # Record for 3 seconds
        time.sleep(3)
        
        # Stop recording
        audio_data = audio_capture.stop_recording()
        print(f"✓ Recording complete: {len(audio_data)} bytes, {chunk_count[0]} chunks")
        
        # Clean up
        audio_capture.release_device()
        
    except AudioDeviceError as e:
        print(f"✗ Audio device error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")


def example_context_manager():
    """Example: Using AudioCapture as context manager"""
    print("\n" + "=" * 60)
    print("Example 3: Context Manager Usage")
    print("=" * 60)
    
    if not PYAUDIO_AVAILABLE or not NUMPY_AVAILABLE:
        print("⚠ Dependencies not installed. Install with:")
        print("  pip install PyAudio numpy noisereduce")
        return
    
    try:
        print("Press Enter to start recording...")
        input()
        
        # Use context manager for automatic cleanup
        with AudioCapture() as audio_capture:
            audio_capture.start_recording()
            print("🎤 Recording... (will record for 2 seconds)")
            time.sleep(2)
            audio_data = audio_capture.stop_recording()
            print(f"✓ Recording complete: {len(audio_data)} bytes")
        
        print("✓ Resources automatically released")
        
    except AudioDeviceError as e:
        print(f"✗ Audio device error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")


def example_error_handling():
    """Example: Error handling"""
    print("\n" + "=" * 60)
    print("Example 4: Error Handling")
    print("=" * 60)
    
    if not PYAUDIO_AVAILABLE or not NUMPY_AVAILABLE:
        print("⚠ Dependencies not installed. Install with:")
        print("  pip install PyAudio numpy noisereduce")
        return
    
    try:
        audio_capture = AudioCapture()
        
        # Try to stop recording without starting
        try:
            audio_capture.stop_recording()
        except RuntimeError as e:
            print(f"✓ Caught expected error: {e}")
        
        # Clean up
        audio_capture.release_device()
        
    except MicrophoneNotFoundError:
        print("✗ No microphone found")
    except PermissionDeniedError:
        print("✗ Permission denied to access microphone")
    except DeviceBusyError:
        print("✗ Audio device is busy")
    except AudioDeviceError as e:
        print(f"✗ Audio device error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")


def main():
    """Run all examples"""
    print("=" * 60)
    print("AudioCapture Module Examples")
    print("=" * 60)
    
    if not PYAUDIO_AVAILABLE or not NUMPY_AVAILABLE:
        print("\n⚠ Required dependencies are not installed!")
        print("\nTo run these examples, install:")
        print("  pip install PyAudio numpy noisereduce")
        print("\nNote: On Linux, you may need to install portaudio first:")
        print("  sudo apt-get install portaudio19-dev  # Debian/Ubuntu")
        print("  sudo pacman -S portaudio              # Arch Linux")
        return 1
    
    examples = [
        example_basic_recording,
        example_streaming_recording,
        example_context_manager,
        example_error_handling,
    ]
    
    for example in examples:
        try:
            example()
        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user")
            break
        except Exception as e:
            print(f"\n✗ Example failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
