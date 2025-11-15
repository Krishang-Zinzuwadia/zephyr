"""
Speech recognition module for Zephyr voice-to-text application

Handles speech-to-text transcription using faster-whisper with streaming support
"""

import logging
import threading
import time
from typing import Optional, Callable, List, Tuple
from dataclasses import dataclass
from collections import deque
from pathlib import Path

# Import dependencies with error handling
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    WhisperModel = None

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError as e:
    NUMPY_AVAILABLE = False
    np = None
    import sys
    print(f"ERROR: numpy not found in Python path: {sys.path}", file=sys.stderr)
    print(f"Import error: {e}", file=sys.stderr)
    raise ImportError(
        "numpy is required but not found. "
        "When running with sudo, use: sudo -H pip install numpy"
    )


logger = logging.getLogger(__name__)


@dataclass
class TranscriptionSegment:
    """Single segment of transcribed text"""
    text: str
    start: float
    end: float
    confidence: float


@dataclass
class TranscriptionResult:
    """Complete transcription result"""
    text: str
    confidence: float
    language: str
    duration: float
    segments: List[TranscriptionSegment]
    is_final: bool = True


class TranscriptionError(Exception):
    """Raised when transcription fails"""
    pass


class ModelLoadError(TranscriptionError):
    """Raised when model loading fails"""
    pass


class SpeechRecognizer:
    """
    Speech recognition class using faster-whisper
    
    Provides streaming transcription with real-time updates and multi-language support
    """
    
    def __init__(
        self,
        model_name: str = "base",
        language: str = "auto",
        device: str = "cpu",
        compute_type: str = "int8",
        beam_size: int = 5,
        best_of: int = 5,
        temperature: float = 0.0,
        vad_enabled: bool = True,
        vad_threshold: float = 0.5
    ):
        """
        Initialize SpeechRecognizer
        
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large)
            language: Language code or "auto" for automatic detection
            device: Device to run model on ("cpu" or "cuda")
            compute_type: Computation type (int8, float16, float32)
            beam_size: Beam size for beam search
            best_of: Number of candidates to consider
            temperature: Temperature for sampling (0.0 = greedy)
            vad_enabled: Enable Voice Activity Detection
            vad_threshold: VAD threshold (0.0 to 1.0)
        
        Raises:
            ImportError: If required dependencies are not installed
        """
        if not FASTER_WHISPER_AVAILABLE:
            raise ImportError(
                "faster-whisper is required for speech recognition. "
                "Install it with: pip install faster-whisper"
            )
        
        if not NUMPY_AVAILABLE:
            raise ImportError(
                "NumPy is required for audio processing. "
                "Install it with: pip install numpy"
            )
        
        self.model_name = model_name
        self.language = None if language == "auto" else language
        self.device = device
        self.compute_type = compute_type
        self.beam_size = beam_size
        self.best_of = best_of
        self.temperature = temperature
        self.vad_enabled = vad_enabled
        self.vad_threshold = vad_threshold
        
        # Model instance (lazy loaded)
        self._model: Optional[WhisperModel] = None
        self._model_lock = threading.Lock()
        self._model_loaded = False
        
        # Streaming state
        self._is_streaming = False
        self._streaming_callback: Optional[Callable[[str, bool], None]] = None
        self._audio_chunks: deque = deque()
        self._chunks_lock = threading.Lock()
        
        # Context window for streaming (stores last 2 seconds of audio)
        self._context_window: deque = deque(maxlen=2)
        
        # Transcription state
        self._current_transcription = ""
        self._transcription_lock = threading.Lock()
        
        # Model unload timer
        self._unload_timer: Optional[threading.Timer] = None
        self._unload_after_seconds = 0  # 0 = never unload
        
        logger.info(
            f"SpeechRecognizer initialized: model={model_name}, "
            f"language={language}, device={device}"
        )
    
    def _load_model(self) -> None:
        """
        Load Whisper model into memory
        
        Raises:
            ModelLoadError: If model loading fails
        """
        with self._model_lock:
            if self._model_loaded:
                return
            
            logger.info(f"Loading Whisper model: {self.model_name}")
            
            try:
                # Cancel any pending unload timer
                if self._unload_timer is not None:
                    self._unload_timer.cancel()
                    self._unload_timer = None
                
                # Load model
                self._model = WhisperModel(
                    self.model_name,
                    device=self.device,
                    compute_type=self.compute_type
                )
                
                self._model_loaded = True
                logger.info(f"Whisper model '{self.model_name}' loaded successfully")
                
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise ModelLoadError(f"Failed to load model '{self.model_name}': {e}")
    
    def _ensure_model_loaded(self) -> None:
        """Ensure model is loaded, load if necessary"""
        if not self._model_loaded:
            self._load_model()
    
    def set_language(self, language: str) -> None:
        """
        Set transcription language
        
        Args:
            language: Language code or "auto" for automatic detection
        """
        self.language = None if language == "auto" else language
        logger.info(f"Language set to: {language}")
    
    def set_unload_timeout(self, seconds: int) -> None:
        """
        Set model unload timeout
        
        Args:
            seconds: Seconds of inactivity before unloading model (0 = never)
        """
        self._unload_after_seconds = seconds
        logger.info(f"Model unload timeout set to: {seconds}s")
    
    def _schedule_model_unload(self) -> None:
        """
        Schedule model unload after timeout to free memory
        
        This helps maintain low idle resource usage by unloading the model
        when not in use, while keeping it cached during active periods.
        
        Requirements: 9.1, 9.2
        """
        if self._unload_after_seconds <= 0:
            return
        
        # Cancel existing timer
        if self._unload_timer is not None:
            self._unload_timer.cancel()
        
        # Schedule new timer
        self._unload_timer = threading.Timer(
            self._unload_after_seconds,
            self.unload_model
        )
        self._unload_timer.daemon = True
        self._unload_timer.start()
        
        logger.debug(f"Scheduled model unload in {self._unload_after_seconds}s to free memory")

    def unload_model(self) -> None:
        """
        Unload model from memory to free resources
        
        This significantly reduces idle memory usage by freeing the Whisper model
        when not in use. The model will be automatically reloaded on next use.
        
        Requirements: 9.1, 9.2
        """
        with self._model_lock:
            if not self._model_loaded:
                return
            
            logger.info("Unloading Whisper model to free memory")
            
            try:
                # Cancel unload timer
                if self._unload_timer is not None:
                    self._unload_timer.cancel()
                    self._unload_timer = None
                
                # Delete model to free memory
                del self._model
                self._model = None
                self._model_loaded = False
                
                logger.info("Whisper model unloaded, memory freed")
                
            except Exception as e:
                logger.error(f"Error unloading model: {e}")
    
    def _detect_language(self, audio_array: np.ndarray) -> Tuple[str, float]:
        """
        Detect language from audio
        
        Args:
            audio_array: Audio data as numpy array
        
        Returns:
            Tuple of (language_code, confidence)
        """
        try:
            self._ensure_model_loaded()
            
            # Detect language using first 30 seconds
            segments, info = self._model.transcribe(
                audio_array,
                language=None,  # Auto-detect
                beam_size=self.beam_size,
                best_of=self.best_of,
                temperature=self.temperature,
                vad_filter=self.vad_enabled,
                vad_parameters={"threshold": self.vad_threshold} if self.vad_enabled else None
            )
            
            detected_language = info.language
            language_probability = info.language_probability
            
            logger.info(
                f"Detected language: {detected_language} "
                f"(confidence: {language_probability:.2f})"
            )
            
            return detected_language, language_probability
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return "en", 0.0
    
    def _convert_audio_to_array(self, audio_data: bytes, sample_rate: int = 16000) -> np.ndarray:
        """
        Convert audio bytes to numpy array normalized for Whisper
        
        Args:
            audio_data: Raw audio data as bytes (16-bit PCM)
            sample_rate: Sample rate of audio
        
        Returns:
            Normalized audio array (float32, -1.0 to 1.0)
        """
        # Convert bytes to int16 array
        audio_int16 = np.frombuffer(audio_data, dtype=np.int16)
        
        # Convert to float32 and normalize to -1.0 to 1.0
        audio_float32 = audio_int16.astype(np.float32) / 32768.0
        
        return audio_float32
    
    def transcribe(
        self,
        audio_data: bytes,
        sample_rate: int = 16000
    ) -> TranscriptionResult:
        """
        Transcribe audio data to text (non-streaming)
        
        Args:
            audio_data: Raw audio data as bytes (16-bit PCM)
            sample_rate: Sample rate of audio
        
        Returns:
            TranscriptionResult with complete transcription
        
        Raises:
            TranscriptionError: If transcription fails
        """
        try:
            logger.info("Starting transcription")
            start_time = time.time()
            
            # Ensure model is loaded
            self._ensure_model_loaded()
            
            # Convert audio to numpy array
            audio_array = self._convert_audio_to_array(audio_data, sample_rate)
            
            # Detect language if auto mode
            detected_language = self.language
            if detected_language is None:
                detected_language, _ = self._detect_language(audio_array)
            
            # Transcribe
            segments, info = self._model.transcribe(
                audio_array,
                language=detected_language,
                beam_size=self.beam_size,
                best_of=self.best_of,
                temperature=self.temperature,
                vad_filter=self.vad_enabled,
                vad_parameters={"threshold": self.vad_threshold} if self.vad_enabled else None
            )
            
            # Collect segments
            transcription_segments = []
            full_text = []
            total_confidence = 0.0
            segment_count = 0
            
            for segment in segments:
                transcription_segments.append(
                    TranscriptionSegment(
                        text=segment.text,
                        start=segment.start,
                        end=segment.end,
                        confidence=segment.avg_logprob  # Use avg_logprob as confidence
                    )
                )
                full_text.append(segment.text)
                total_confidence += segment.avg_logprob
                segment_count += 1
            
            # Calculate average confidence
            avg_confidence = total_confidence / segment_count if segment_count > 0 else 0.0
            
            # Combine text
            final_text = "".join(full_text).strip()
            
            duration = time.time() - start_time
            
            logger.info(
                f"Transcription complete: {len(final_text)} chars, "
                f"{duration:.2f}s, confidence: {avg_confidence:.2f}"
            )
            
            # Schedule model unload
            self._schedule_model_unload()
            
            return TranscriptionResult(
                text=final_text,
                confidence=avg_confidence,
                language=detected_language or "unknown",
                duration=duration,
                segments=transcription_segments,
                is_final=True
            )
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise TranscriptionError(f"Transcription failed: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - unload model"""
        self.unload_model()
    
    def __del__(self):
        """Destructor - ensure model is unloaded"""
        try:
            self.unload_model()
        except Exception:
            pass

    def start_streaming_transcription(
        self,
        callback: Callable[[str, bool], None],
        sample_rate: int = 16000
    ) -> None:
        """
        Start streaming transcription mode
        
        Args:
            callback: Function called with (text, is_final) for each update
            sample_rate: Sample rate of incoming audio chunks
        
        Raises:
            RuntimeError: If streaming is already in progress
        """
        if self._is_streaming:
            raise RuntimeError("Streaming transcription already in progress")
        
        logger.info("Starting streaming transcription")
        
        # Ensure model is loaded
        self._ensure_model_loaded()
        
        # Reset state
        with self._chunks_lock:
            self._audio_chunks.clear()
        
        with self._transcription_lock:
            self._current_transcription = ""
        
        self._context_window.clear()
        
        # Set streaming state
        self._is_streaming = True
        self._streaming_callback = callback
        self._sample_rate = sample_rate
        
        logger.info("Streaming transcription started")
    
    def process_audio_chunk(self, audio_chunk: bytes) -> None:
        """
        Process a single audio chunk for streaming transcription
        
        Args:
            audio_chunk: Raw audio data chunk as bytes (16-bit PCM)
        """
        if not self._is_streaming:
            logger.warning("process_audio_chunk called but streaming not active")
            return
        
        try:
            # Convert chunk to numpy array
            chunk_array = self._convert_audio_to_array(audio_chunk, self._sample_rate)
            
            # Check for voice activity using simple energy-based VAD
            if self.vad_enabled and not self._has_voice_activity(chunk_array):
                logger.debug("No voice activity detected in chunk")
                return
            
            # Add to context window
            self._context_window.append(chunk_array)
            
            # Combine context window for transcription
            combined_audio = np.concatenate(list(self._context_window))
            
            # Transcribe combined audio
            try:
                segments, info = self._model.transcribe(
                    combined_audio,
                    language=self.language,
                    beam_size=self.beam_size,
                    best_of=self.best_of,
                    temperature=self.temperature,
                    vad_filter=False,  # We already did VAD
                    word_timestamps=False
                )
                
                # Collect text from segments
                text_parts = []
                for segment in segments:
                    text_parts.append(segment.text)
                
                new_transcription = "".join(text_parts).strip()
                
                # Update current transcription
                with self._transcription_lock:
                    if new_transcription != self._current_transcription:
                        self._current_transcription = new_transcription
                        
                        # Call callback with partial result
                        if self._streaming_callback:
                            try:
                                self._streaming_callback(new_transcription, False)
                            except Exception as e:
                                logger.error(f"Error in streaming callback: {e}")
                
            except Exception as e:
                logger.error(f"Error transcribing audio chunk: {e}")
        
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
    
    def _has_voice_activity(self, audio_array: np.ndarray) -> bool:
        """
        Simple energy-based Voice Activity Detection
        
        Args:
            audio_array: Audio data as numpy array
        
        Returns:
            True if voice activity detected, False otherwise
        """
        try:
            # Calculate RMS energy
            rms = np.sqrt(np.mean(audio_array ** 2))
            
            # Check if energy exceeds threshold
            has_activity = rms > self.vad_threshold * 0.01  # Scale threshold
            
            return has_activity
            
        except Exception as e:
            logger.debug(f"VAD check failed: {e}")
            return True  # Assume activity on error
    
    def stop_streaming_transcription(self) -> None:
        """Stop streaming transcription mode"""
        if not self._is_streaming:
            return
        
        logger.info("Stopping streaming transcription")
        
        self._is_streaming = False
        self._streaming_callback = None
        
        # Clear buffers
        with self._chunks_lock:
            self._audio_chunks.clear()
        
        self._context_window.clear()
        
        # Schedule model unload
        self._schedule_model_unload()
        
        logger.info("Streaming transcription stopped")
    
    def get_current_transcription(self) -> str:
        """
        Get current partial transcription
        
        Returns:
            Current transcription text
        """
        with self._transcription_lock:
            return self._current_transcription

    def finalize_transcription(self, audio_data: bytes = None) -> TranscriptionResult:
        """
        Finalize streaming transcription and return final result
        
        Args:
            audio_data: Optional complete audio data for final transcription.
                       If None, uses current streaming transcription.
        
        Returns:
            TranscriptionResult with final transcription
        
        Raises:
            TranscriptionError: If finalization fails
        """
        try:
            logger.info("Finalizing transcription")
            
            # If audio data provided, do a final complete transcription
            if audio_data is not None and len(audio_data) > 0:
                result = self.transcribe(audio_data, self._sample_rate)
                
                # Stop streaming if active
                if self._is_streaming:
                    self.stop_streaming_transcription()
                
                return result
            
            # Otherwise, use current streaming transcription
            with self._transcription_lock:
                final_text = self._current_transcription
            
            # Calculate confidence based on text length and quality indicators
            confidence = self._estimate_confidence(final_text)
            
            # Stop streaming
            if self._is_streaming:
                self.stop_streaming_transcription()
            
            # Create result
            result = TranscriptionResult(
                text=final_text,
                confidence=confidence,
                language=self.language or "unknown",
                duration=0.0,  # Duration not tracked in streaming mode
                segments=[],  # Segments not available in streaming mode
                is_final=True
            )
            
            logger.info(
                f"Transcription finalized: {len(final_text)} chars, "
                f"confidence: {confidence:.2f}"
            )
            
            # Emit final result via callback
            if self._streaming_callback:
                try:
                    self._streaming_callback(final_text, True)
                except Exception as e:
                    logger.error(f"Error in final callback: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription finalization failed: {e}")
            raise TranscriptionError(f"Finalization failed: {e}")
    
    def _estimate_confidence(self, text: str) -> float:
        """
        Estimate confidence score for transcription
        
        Args:
            text: Transcribed text
        
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not text:
            return 0.0
        
        # Simple heuristic-based confidence estimation
        confidence = 0.5  # Base confidence
        
        # Longer text generally indicates better transcription
        if len(text) > 10:
            confidence += 0.2
        
        # Presence of punctuation suggests better quality
        if any(char in text for char in ".,!?;:"):
            confidence += 0.1
        
        # Proper capitalization suggests better quality
        if text[0].isupper():
            confidence += 0.1
        
        # Multiple words suggest better quality
        word_count = len(text.split())
        if word_count > 3:
            confidence += 0.1
        
        # Cap at 1.0
        confidence = min(confidence, 1.0)
        
        return confidence
    
    def is_low_confidence(self, result: TranscriptionResult, threshold: float = 0.7) -> bool:
        """
        Check if transcription confidence is below threshold
        
        Args:
            result: TranscriptionResult to check
            threshold: Confidence threshold (default: 0.7)
        
        Returns:
            True if confidence is below threshold
        """
        return result.confidence < threshold
    
    def get_confidence_indicator(self, result: TranscriptionResult) -> str:
        """
        Get visual indicator for transcription confidence
        
        Args:
            result: TranscriptionResult to check
        
        Returns:
            String indicator (e.g., "✓", "~", "?")
        """
        if result.confidence >= 0.9:
            return "✓"  # High confidence
        elif result.confidence >= 0.7:
            return "~"  # Medium confidence
        else:
            return "?"  # Low confidence
