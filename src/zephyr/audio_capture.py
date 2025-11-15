"""
Audio capture module for Zephyr voice-to-text application

Handles microphone input, audio buffering, and streaming audio chunks
"""

import threading
import logging
from typing import Optional, Callable, List
from collections import deque
from dataclasses import dataclass
from datetime import datetime

# Import dependencies with error handling
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    pyaudio = None

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    import noisereduce as nr
    NOISEREDUCE_AVAILABLE = True
except ImportError:
    NOISEREDUCE_AVAILABLE = False
    nr = None


logger = logging.getLogger(__name__)


@dataclass
class AudioBuffer:
    """Container for audio data"""
    sample_rate: int
    channels: int
    data: bytes
    duration: float
    timestamp: datetime


class AudioDeviceError(Exception):
    """Raised when audio device operations fail"""
    pass


class MicrophoneNotFoundError(AudioDeviceError):
    """Raised when no microphone is detected"""
    pass


class PermissionDeniedError(AudioDeviceError):
    """Raised when microphone access is denied"""
    pass


class DeviceBusyError(AudioDeviceError):
    """Raised when audio device is busy"""
    pass


class AudioCapture:
    """
    Audio capture class using PyAudio
    
    Captures audio from the default microphone with configurable sample rate
    and channels. Supports streaming audio chunks for real-time transcription.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_duration: float = 1.0,
        max_recording_duration: int = 60
    ):
        """
        Initialize AudioCapture
        
        Args:
            sample_rate: Audio sample rate in Hz (default: 16000)
            channels: Number of audio channels (default: 1 for mono)
            chunk_duration: Duration of each audio chunk in seconds (default: 1.0)
            max_recording_duration: Maximum recording duration in seconds (default: 60)
        
        Raises:
            ImportError: If required dependencies are not installed
        """
        if not PYAUDIO_AVAILABLE:
            raise ImportError(
                "PyAudio is required for audio capture. "
                "Install it with: pip install PyAudio"
            )
        
        if not NUMPY_AVAILABLE:
            raise ImportError(
                "NumPy is required for audio processing. "
                "Install it with: pip install numpy"
            )
        
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_duration = chunk_duration
        self.max_recording_duration = max_recording_duration
        
        # Calculate chunk size in frames
        self.chunk_size = int(sample_rate * chunk_duration)
        
        # PyAudio instance
        self._pyaudio: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None
        
        # Recording state
        self._is_recording = False
        self._recording_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Circular buffer for audio data (stores last max_recording_duration seconds)
        max_buffer_size = int(max_recording_duration / chunk_duration) + 1
        self._audio_buffer: deque = deque(maxlen=max_buffer_size)
        self._buffer_lock = threading.Lock()
        
        # Current audio level for visualization
        self._current_audio_level: float = 0.0
        self._level_lock = threading.Lock()
        
        # Streaming callback
        self._chunk_callback: Optional[Callable[[bytes], None]] = None
        
        # Noise reduction
        self._apply_noise_reduction = True
        
        logger.info(
            f"AudioCapture initialized: {sample_rate}Hz, {channels} channel(s), "
            f"{chunk_duration}s chunks"
        )
    
    def _initialize_pyaudio(self) -> None:
        """Initialize PyAudio instance and verify device availability"""
        if self._pyaudio is not None:
            return
        
        try:
            self._pyaudio = pyaudio.PyAudio()
            
            # Check if there's at least one input device
            device_count = self._pyaudio.get_device_count()
            has_input_device = False
            
            for i in range(device_count):
                device_info = self._pyaudio.get_device_info_by_index(i)
                if device_info.get('maxInputChannels', 0) > 0:
                    has_input_device = True
                    logger.debug(f"Found input device: {device_info.get('name')}")
                    break
            
            if not has_input_device:
                raise MicrophoneNotFoundError("No microphone device found")
            
            logger.info("PyAudio initialized successfully")
            
        except OSError as e:
            if "Permission denied" in str(e) or "EACCES" in str(e):
                raise PermissionDeniedError(
                    f"Permission denied accessing audio device: {e}"
                )
            raise AudioDeviceError(f"Failed to initialize audio device: {e}")
        except Exception as e:
            raise AudioDeviceError(f"Failed to initialize PyAudio: {e}")
    
    def _open_stream(self) -> None:
        """Open audio input stream"""
        if self._stream is not None and self._stream.is_active():
            return
        
        try:
            self._stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=None  # We'll use blocking read
            )
            logger.info("Audio stream opened")
            
        except OSError as e:
            error_msg = str(e).lower()
            if "permission denied" in error_msg or "eacces" in error_msg:
                raise PermissionDeniedError(
                    f"Permission denied opening audio stream: {e}"
                )
            elif "device busy" in error_msg or "ebusy" in error_msg:
                raise DeviceBusyError(
                    f"Audio device is busy: {e}"
                )
            raise AudioDeviceError(f"Failed to open audio stream: {e}")
        except Exception as e:
            raise AudioDeviceError(f"Failed to open audio stream: {e}")
    
    def start_recording(self, chunk_callback: Optional[Callable[[bytes], None]] = None) -> None:
        """
        Start recording audio from microphone
        
        Args:
            chunk_callback: Optional callback function called with each audio chunk
                          for streaming transcription
        
        Raises:
            AudioDeviceError: If audio device initialization fails
            RuntimeError: If recording is already in progress
        """
        if self._is_recording:
            raise RuntimeError("Recording already in progress")
        
        logger.info("Starting audio recording")
        
        # Initialize PyAudio if needed
        self._initialize_pyaudio()
        
        # Open audio stream
        self._open_stream()
        
        # Clear buffer and reset state
        with self._buffer_lock:
            self._audio_buffer.clear()
        
        self._stop_event.clear()
        self._is_recording = True
        self._chunk_callback = chunk_callback
        
        # Start recording thread
        self._recording_thread = threading.Thread(
            target=self._recording_loop,
            daemon=True
        )
        self._recording_thread.start()
        
        logger.info("Audio recording started")
    
    def _recording_loop(self) -> None:
        """
        Main recording loop (runs in separate thread)
        
        Uses efficient circular buffer to minimize memory allocation
        and prevent memory growth during long recordings.
        
        Requirements: 9.3, 9.5
        """
        try:
            while not self._stop_event.is_set():
                try:
                    # Read audio chunk (non-blocking with exception_on_overflow=False
                    # to prevent buffer overflow issues during high CPU usage)
                    audio_data = self._stream.read(
                        self.chunk_size,
                        exception_on_overflow=False
                    )
                    
                    # Calculate audio level for visualization
                    audio_level = self._calculate_audio_level(audio_data)
                    with self._level_lock:
                        self._current_audio_level = audio_level
                    
                    # Store in circular buffer (automatically drops oldest chunks
                    # when maxlen is reached, preventing unbounded memory growth)
                    with self._buffer_lock:
                        self._audio_buffer.append(audio_data)
                    
                    # Call streaming callback if provided
                    if self._chunk_callback is not None:
                        try:
                            self._chunk_callback(audio_data)
                        except Exception as e:
                            logger.error(f"Error in chunk callback: {e}")
                    
                except Exception as e:
                    logger.error(f"Error reading audio data: {e}")
                    break
        
        finally:
            logger.debug("Recording loop ended")
    
    def stop_recording(self) -> bytes:
        """
        Stop recording and return captured audio data
        
        Returns:
            Complete audio data as bytes
        
        Raises:
            RuntimeError: If recording is not in progress
        """
        if not self._is_recording:
            raise RuntimeError("Recording is not in progress")
        
        logger.info("Stopping audio recording")
        
        # Signal recording thread to stop
        self._stop_event.set()
        
        # Wait for recording thread to finish
        if self._recording_thread is not None:
            self._recording_thread.join(timeout=2.0)
            if self._recording_thread.is_alive():
                logger.warning("Recording thread did not stop gracefully")
        
        self._is_recording = False
        self._chunk_callback = None
        
        # Collect all audio data from buffer
        with self._buffer_lock:
            audio_data = b''.join(self._audio_buffer)
            self._audio_buffer.clear()
        
        # Apply noise reduction if enabled and we have data
        if self._apply_noise_reduction and len(audio_data) > 0:
            try:
                audio_data = self._apply_noise_reduction_filter(audio_data)
            except Exception as e:
                logger.warning(f"Failed to apply noise reduction: {e}")
        
        # Close stream to release device
        self._close_stream()
        
        logger.info(f"Audio recording stopped, captured {len(audio_data)} bytes")
        
        return audio_data
    
    def _calculate_audio_level(self, audio_data: bytes) -> float:
        """
        Calculate normalized audio level (0.0 to 1.0) for visualization
        
        Args:
            audio_data: Raw audio data as bytes
        
        Returns:
            Normalized audio level between 0.0 and 1.0
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Calculate RMS (Root Mean Square) amplitude
            rms = np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))
            
            # Normalize to 0.0-1.0 range (assuming 16-bit audio)
            max_amplitude = 32768.0  # 2^15 for 16-bit audio
            normalized_level = min(rms / max_amplitude, 1.0)
            
            return normalized_level
            
        except Exception as e:
            logger.debug(f"Error calculating audio level: {e}")
            return 0.0
    
    def get_audio_level(self) -> float:
        """
        Get current audio level for real-time visualization
        
        Returns:
            Normalized audio level between 0.0 and 1.0
        """
        with self._level_lock:
            return self._current_audio_level
    
    def _apply_noise_reduction_filter(self, audio_data: bytes) -> bytes:
        """
        Apply noise reduction to audio data
        
        Args:
            audio_data: Raw audio data as bytes
        
        Returns:
            Noise-reduced audio data as bytes
        """
        if not NOISEREDUCE_AVAILABLE:
            logger.warning("noisereduce library not available, skipping noise reduction")
            return audio_data
        
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Convert to float for processing
            audio_float = audio_array.astype(np.float32)
            
            # Apply noise reduction
            reduced_audio = nr.reduce_noise(
                y=audio_float,
                sr=self.sample_rate,
                stationary=True,
                prop_decrease=0.8
            )
            
            # Convert back to int16
            reduced_audio_int16 = reduced_audio.astype(np.int16)
            
            return reduced_audio_int16.tobytes()
            
        except Exception as e:
            logger.warning(f"Noise reduction failed: {e}")
            return audio_data
    
    def set_noise_reduction(self, enabled: bool) -> None:
        """
        Enable or disable noise reduction
        
        Args:
            enabled: True to enable noise reduction, False to disable
        """
        self._apply_noise_reduction = enabled
        logger.info(f"Noise reduction {'enabled' if enabled else 'disabled'}")
    
    def _close_stream(self) -> None:
        """Close audio stream"""
        if self._stream is not None:
            try:
                if self._stream.is_active():
                    self._stream.stop_stream()
                self._stream.close()
                logger.debug("Audio stream closed")
            except Exception as e:
                logger.error(f"Error closing audio stream: {e}")
            finally:
                self._stream = None
    
    def release_device(self) -> None:
        """
        Release audio device resources immediately
        
        This ensures minimal idle resource usage by freeing audio device
        and PyAudio resources as soon as recording is complete.
        
        Should be called when audio capture is no longer needed.
        
        Requirements: 9.2, 9.4
        """
        logger.debug("Releasing audio device")
        
        # Stop recording if in progress
        if self._is_recording:
            try:
                self.stop_recording()
            except Exception as e:
                logger.error(f"Error stopping recording during cleanup: {e}")
        
        # Close stream
        self._close_stream()
        
        # Terminate PyAudio to free resources
        if self._pyaudio is not None:
            try:
                self._pyaudio.terminate()
                logger.debug("PyAudio terminated, resources freed")
            except Exception as e:
                logger.error(f"Error terminating PyAudio: {e}")
            finally:
                self._pyaudio = None
        
        # Clear audio buffer to free memory
        with self._buffer_lock:
            self._audio_buffer.clear()
        
        # Reset audio level
        with self._level_lock:
            self._current_audio_level = 0.0
        
        logger.debug("Audio device released, resources freed")
    
    def is_recording(self) -> bool:
        """Check if currently recording"""
        return self._is_recording
    
    def get_audio_buffer(self) -> AudioBuffer:
        """
        Get current audio buffer as AudioBuffer object
        
        Returns:
            AudioBuffer containing current audio data
        """
        with self._buffer_lock:
            audio_data = b''.join(self._audio_buffer)
        
        duration = len(audio_data) / (self.sample_rate * self.channels * 2)  # 2 bytes per sample
        
        return AudioBuffer(
            sample_rate=self.sample_rate,
            channels=self.channels,
            data=audio_data,
            duration=duration,
            timestamp=datetime.now()
        )
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - release resources"""
        self.release_device()
    
    def __del__(self):
        """Destructor - ensure resources are released"""
        try:
            self.release_device()
        except Exception:
            pass
