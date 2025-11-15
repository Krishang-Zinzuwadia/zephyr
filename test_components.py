#!/usr/bin/env python3
"""Test each Zephyr component individually"""
import sys
sys.path.insert(0, 'src')

print("Testing Zephyr components...")
print()

# Test 1: Audio capture
print("1. Testing audio capture...")
try:
    from zephyr.audio_capture import AudioCapture
    audio = AudioCapture()
    print("   ✓ Audio capture initialized")
except Exception as e:
    print(f"   ✗ Audio capture failed: {e}")

# Test 2: Speech recognition
print("2. Testing speech recognition...")
try:
    from zephyr.speech_recognition import SpeechRecognizer
    recognizer = SpeechRecognizer(model_name='tiny', vad_enabled=False)
    print("   ✓ Speech recognizer initialized")
    
    # Try to load model
    print("   Loading tiny model...")
    import numpy as np
    test_audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence
    result = recognizer.transcribe(test_audio)
    print(f"   ✓ Model loaded, test transcription: '{result.text}'")
except Exception as e:
    print(f"   ✗ Speech recognition failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Input simulation
print("3. Testing input simulation...")
try:
    from zephyr.input_simulator import InputSimulator
    simulator = InputSimulator.create()
    print("   ✓ Input simulator initialized")
except Exception as e:
    print(f"   ✗ Input simulator failed: {e}")

# Test 4: Hotkey listener
print("4. Testing hotkey listener...")
try:
    import os
    if os.geteuid() == 0:
        from zephyr.evdev_hotkey_listener import EvdevHotkeyListener
        listener = EvdevHotkeyListener(hotkey='`')
        print("   ✓ Evdev hotkey listener initialized")
    else:
        from zephyr.hotkey_listener import HotkeyListener
        listener = HotkeyListener(hotkey='`')
        print("   ✓ Pynput hotkey listener initialized")
except Exception as e:
    print(f"   ✗ Hotkey listener failed: {e}")

print()
print("Component test complete!")
