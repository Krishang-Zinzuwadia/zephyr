#!/usr/bin/env python3
"""
Example demonstrating speech recognition functionality

This example shows how to use the SpeechRecognizer class for both
standard and streaming transcription.
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zephyr.speech_recognition import SpeechRecognizer, TranscriptionResult
from zephyr.audio_capture import AudioCapture


def streaming_callback(text: str, is_final: bool):
    """Callback for streaming transcription updates"""
    status = "FINAL" if is_final else "PARTIAL"
    print(f"[{status}] {text}")


def example_basic_transcription():
    """Example: Basic transcription from recorded audio"""
    print("=== Basic Transcription Example ===\n")
    
    # Initialize components
    recognizer = SpeechRecognizer(
        model_name="base",
        language="auto",
        vad_enabled=True
    )
    
    audio_capture = AudioCapture(
        sample_rate=16000,
        channels=1
    )
    
    try:
        print("Press Enter to start recording...")
        input()
        
        print("Recording... (speak now)")
        audio_capture.start_recording()
        
        # Record for 5 seconds
        time.sleep(5)
        
        print("Stopping recording...")
        audio_data = audio_capture.stop_recording()
        
        print(f"Captured {len(audio_data)} bytes of audio")
        print("Transcribing...")
        
        # Transcribe
        result = recognizer.transcribe(audio_data)
        
        print(f"\nTranscription: {result.text}")
        print(f"Language: {result.language}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Duration: {result.duration:.2f}s")
        print(f"Segments: {len(result.segments)}")
        
        # Show confidence indicator
        indicator = recognizer.get_confidence_indicator(result)
        print(f"Quality: {indicator}")
        
        if recognizer.is_low_confidence(result):
            print("⚠️  Low confidence transcription")
        
    finally:
        audio_capture.release_device()
        recognizer.unload_model()


def example_streaming_transcription():
    """Example: Streaming transcription with real-time updates"""
    print("\n=== Streaming Transcription Example ===\n")
    
    # Initialize components
    recognizer = SpeechRecognizer(
        model_name="base",
        language="en",
        vad_enabled=True
    )
    
    audio_capture = AudioCapture(
        sample_rate=16000,
        channels=1,
        chunk_duration=1.0  # 1-second chunks
    )
    
    try:
        print("Press Enter to start streaming transcription...")
        input()
        
        # Start streaming transcription
        recognizer.start_streaming_transcription(
            callback=streaming_callback,
            sample_rate=16000
        )
        
        print("Recording with live transcription... (speak now)")
        
        # Start recording with chunk callback
        audio_capture.start_recording(
            chunk_callback=lambda chunk: recognizer.process_audio_chunk(chunk)
        )
        
        # Record for 10 seconds
        time.sleep(10)
        
        print("\nStopping recording...")
        audio_data = audio_capture.stop_recording()
        
        # Finalize transcription
        print("Finalizing transcription...")
        result = recognizer.finalize_transcription(audio_data)
        
        print(f"\n=== Final Result ===")
        print(f"Text: {result.text}")
        print(f"Confidence: {result.confidence:.2f}")
        
    finally:
        audio_capture.release_device()
        recognizer.unload_model()


def example_language_detection():
    """Example: Automatic language detection"""
    print("\n=== Language Detection Example ===\n")
    
    recognizer = SpeechRecognizer(
        model_name="base",
        language="auto"  # Auto-detect language
    )
    
    audio_capture = AudioCapture(sample_rate=16000, channels=1)
    
    try:
        print("Press Enter to start recording...")
        input()
        
        print("Recording... (speak in any language)")
        audio_capture.start_recording()
        
        time.sleep(5)
        
        print("Stopping recording...")
        audio_data = audio_capture.stop_recording()
        
        print("Transcribing with language detection...")
        result = recognizer.transcribe(audio_data)
        
        print(f"\nDetected Language: {result.language}")
        print(f"Transcription: {result.text}")
        
    finally:
        audio_capture.release_device()
        recognizer.unload_model()


def example_model_caching():
    """Example: Model caching for faster subsequent transcriptions"""
    print("\n=== Model Caching Example ===\n")
    
    recognizer = SpeechRecognizer(model_name="base")
    
    # Set unload timeout (model stays in memory for 5 minutes)
    recognizer.set_unload_timeout(300)
    
    audio_capture = AudioCapture(sample_rate=16000, channels=1)
    
    try:
        # First transcription (loads model)
        print("First transcription (loading model)...")
        audio_capture.start_recording()
        time.sleep(3)
        audio_data1 = audio_capture.stop_recording()
        
        start = time.time()
        result1 = recognizer.transcribe(audio_data1)
        duration1 = time.time() - start
        
        print(f"First transcription took: {duration1:.2f}s")
        print(f"Text: {result1.text}\n")
        
        # Second transcription (model already loaded)
        print("Second transcription (model cached)...")
        time.sleep(1)
        audio_capture.start_recording()
        time.sleep(3)
        audio_data2 = audio_capture.stop_recording()
        
        start = time.time()
        result2 = recognizer.transcribe(audio_data2)
        duration2 = time.time() - start
        
        print(f"Second transcription took: {duration2:.2f}s")
        print(f"Text: {result2.text}\n")
        
        print(f"Speedup: {duration1/duration2:.2f}x faster")
        
    finally:
        audio_capture.release_device()
        recognizer.unload_model()


if __name__ == "__main__":
    print("Zephyr Speech Recognition Examples")
    print("=" * 50)
    
    # Check if dependencies are available
    try:
        from faster_whisper import WhisperModel
        print("✓ faster-whisper available")
    except ImportError:
        print("✗ faster-whisper not installed")
        print("  Install with: pip install faster-whisper")
        sys.exit(1)
    
    print("\nSelect an example:")
    print("1. Basic Transcription")
    print("2. Streaming Transcription")
    print("3. Language Detection")
    print("4. Model Caching")
    print("5. Run All Examples")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1":
        example_basic_transcription()
    elif choice == "2":
        example_streaming_transcription()
    elif choice == "3":
        example_language_detection()
    elif choice == "4":
        example_model_caching()
    elif choice == "5":
        example_basic_transcription()
        example_streaming_transcription()
        example_language_detection()
        example_model_caching()
    else:
        print("Invalid choice")
        sys.exit(1)
    
    print("\n✓ Example completed successfully")
