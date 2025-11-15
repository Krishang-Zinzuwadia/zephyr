"""
Zephyr daemon - Main orchestrator for voice-to-text application

Coordinates all subsystems and manages the application lifecycle
"""

import logging
import signal
import sys
import threading
from pathlib import Path
from typing import Optional

from .config import ConfigManager, Config
from .audio_capture import AudioCapture, AudioDeviceError
from .speech_recognition import SpeechRecognizer, TranscriptionError
from .input_simulator import InputSimulator, InputSimulationError
from .ui_overlay import UIOverlay
from .hotkey_listener import HotkeyListener, HotkeyError


logger = logging.getLogger(__name__)


class ZephyrDaemon:
    """
    Main daemon process for Zephyr voice-to-text application
    
    Coordinates all subsystems:
    - Configuration management
    - Audio capture
    - Speech recognition
    - Input simulation
    - UI overlay
    - Hotkey listening
    
    Requirements: 5.5, 9.1, 9.2
    """
    
    def __init__(self, config_path: str):
        """
        Initialize ZephyrDaemon
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self._running = False
        self._shutdown_event = threading.Event()
        
        # Subsystems (initialized in start())
        self.config_manager: Optional[ConfigManager] = None
        self.config: Optional[Config] = None
        self.audio_capture: Optional[AudioCapture] = None
        self.speech_recognizer: Optional[SpeechRecognizer] = None
        self.input_simulator: Optional[InputSimulator] = None
        self.ui_overlay: Optional[UIOverlay] = None
        self.hotkey_listener: Optional[HotkeyListener] = None
        
        # State tracking
        self._is_recording = False
        self._recording_lock = threading.Lock()
        
        logger.info(f"ZephyrDaemon initialized with config: {config_path}")
    
    def _setup_logging(self) -> None:
        """Set up logging configuration"""
        if self.config is None:
            return
        
        # Create log directory
        log_file = Path(self.config.advanced.log_file).expanduser()
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        log_level = getattr(logging, self.config.advanced.log_level, logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        logger.info(f"Logging configured: level={self.config.advanced.log_level}, file={log_file}")
    
    def _initialize_subsystems(self) -> None:
        """
        Initialize all subsystems
        
        Raises:
            Exception: If any subsystem fails to initialize
        """
        logger.info("Initializing subsystems...")
        
        # Load configuration
        logger.info("Loading configuration...")
        self.config_manager = ConfigManager(self.config_path)
        self.config = self.config_manager.load()
        
        # Set up logging based on config
        self._setup_logging()
        
        # Initialize audio capture
        logger.info("Initializing audio capture...")
        self.audio_capture = AudioCapture(
            sample_rate=self.config.audio.sample_rate,
            channels=self.config.audio.channels,
            chunk_duration=self.config.audio.chunk_duration,
            max_recording_duration=self.config.advanced.max_recording_duration
        )
        
        # Initialize speech recognizer
        logger.info("Initializing speech recognizer...")
        self.speech_recognizer = SpeechRecognizer(
            model_name=self.config.model,
            language=self.config.language,
            beam_size=self.config.advanced.beam_size,
            best_of=self.config.advanced.best_of,
            temperature=self.config.advanced.temperature,
            vad_enabled=self.config.advanced.vad_enabled,
            vad_threshold=self.config.advanced.vad_threshold
        )
        
        # Set model unload timeout
        self.speech_recognizer.set_unload_timeout(self.config.advanced.unload_model_after)
        
        # Initialize input simulator
        logger.info("Initializing input simulator...")
        self.input_simulator = InputSimulator.create(
            typing_speed=self.config.typing.speed,
            use_clipboard_fallback=self.config.typing.use_clipboard_fallback
        )
        
        # Initialize UI overlay
        logger.info("Initializing UI overlay...")
        self.ui_overlay = UIOverlay(
            width=self.config.ui.width,
            height=self.config.ui.height,
            border_radius=self.config.ui.border_radius,
            background_opacity=self.config.ui.background_opacity,
            animation_speed=self.config.ui.animation_speed
        )
        
        # Initialize hotkey listener
        logger.info("Initializing hotkey listener...")
        
        # Use evdev listener if running as root (better sudo support)
        import os
        if os.geteuid() == 0:
            logger.info("Running as root, using evdev hotkey listener")
            from .evdev_hotkey_listener import EvdevHotkeyListener
            self.hotkey_listener = EvdevHotkeyListener(
                hotkey=self.config.hotkey,
                on_press_callback=self._on_hotkey_press,
                on_release_callback=self._on_hotkey_release,
                min_press_duration=self.config.advanced.min_press_duration
            )
        else:
            logger.info("Using pynput hotkey listener")
            self.hotkey_listener = HotkeyListener(
                hotkey=self.config.hotkey,
                on_press_callback=self._on_hotkey_press,
                on_release_callback=self._on_hotkey_release,
                min_press_duration=self.config.advanced.min_press_duration
            )
        
        logger.info("All subsystems initialized successfully")
    
    def start(self) -> None:
        """
        Start the daemon
        
        Initializes all subsystems and begins listening for hotkey events
        
        Raises:
            RuntimeError: If daemon is already running
            Exception: If initialization fails
        """
        if self._running:
            raise RuntimeError("Daemon is already running")
        
        logger.info("Starting Zephyr daemon...")
        
        try:
            # Initialize all subsystems
            self._initialize_subsystems()
            
            # Set up signal handlers
            self._setup_signal_handlers()
            
            # Start configuration file watcher
            if self.config_manager:
                self.config_manager.watch_for_changes(self._on_config_changed)
            
            # Start hotkey listener
            if self.hotkey_listener:
                self.hotkey_listener.start()
            
            self._running = True
            logger.info("Zephyr daemon started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start daemon: {e}", exc_info=True)
            self.stop()
            raise
    
    def stop(self) -> None:
        """
        Stop the daemon gracefully
        
        Cleans up all resources and shuts down subsystems
        """
        if not self._running:
            return
        
        logger.info("Stopping Zephyr daemon...")
        
        self._running = False
        self._shutdown_event.set()
        
        # Stop hotkey listener
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
            except Exception as e:
                logger.error(f"Error stopping hotkey listener: {e}")
        
        # Stop recording if in progress
        if self._is_recording and self.audio_capture:
            try:
                self.audio_capture.stop_recording()
            except Exception as e:
                logger.error(f"Error stopping recording: {e}")
        
        # Stop configuration watcher
        if self.config_manager:
            try:
                self.config_manager.stop_watching()
            except Exception as e:
                logger.error(f"Error stopping config watcher: {e}")
        
        # Release audio device
        if self.audio_capture:
            try:
                self.audio_capture.release_device()
            except Exception as e:
                logger.error(f"Error releasing audio device: {e}")
        
        # Unload speech recognition model
        if self.speech_recognizer:
            try:
                self.speech_recognizer.unload_model()
            except Exception as e:
                logger.error(f"Error unloading model: {e}")
        
        # Destroy UI overlay
        if self.ui_overlay:
            try:
                self.ui_overlay.destroy()
            except Exception as e:
                logger.error(f"Error destroying UI overlay: {e}")
        
        logger.info("Zephyr daemon stopped")
    
    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        logger.debug("Signal handlers registered")
    
    def _on_config_changed(self) -> None:
        """
        Callback when configuration file changes
        
        Reloads configuration and updates subsystems
        """
        logger.info("Configuration changed, reloading...")
        
        try:
            # Reload configuration
            if self.config_manager:
                new_config = self.config_manager.load()
                self.config = new_config
            
            # Update subsystems with new configuration
            # Note: Some changes may require restart
            
            # Update hotkey
            if self.hotkey_listener and self.config:
                self.hotkey_listener.set_hotkey(self.config.hotkey)
            
            # Update speech recognizer language
            if self.speech_recognizer and self.config:
                self.speech_recognizer.set_language(self.config.language)
                self.speech_recognizer.set_unload_timeout(self.config.advanced.unload_model_after)
            
            logger.info("Configuration reloaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}", exc_info=True)
    
    def _on_hotkey_press(self) -> None:
        """
        Callback when hotkey is pressed - start recording OR close UI if already done
        
        Uses threading for parallel audio capture and transcription to
        limit CPU usage and maintain responsiveness.
        
        Requirements: 9.3, 9.5
        """
        with self._recording_lock:
            # If already recording, ignore
            if self._is_recording:
                logger.warning("Already recording, ignoring hotkey press")
                return
            
            # If UI is visible but not recording, hide it (toggle behavior)
            if self.ui_overlay and self.ui_overlay.is_visible:
                logger.info("UI visible but not recording - hiding UI")
                self.ui_overlay.hide()
                return
            
            logger.info("Hotkey pressed, starting recording")
            
            try:
                # Show UI overlay
                if self.ui_overlay:
                    self.ui_overlay.show_recording()
                
                # Start streaming transcription (runs in separate thread internally)
                if self.speech_recognizer:
                    self.speech_recognizer.start_streaming_transcription(
                        callback=self._on_transcription_update,
                        sample_rate=self.config.audio.sample_rate if self.config else 16000
                    )
                
                # Start streaming input
                if self.input_simulator:
                    self.input_simulator.start_streaming_input()
                
                # Start audio recording with streaming callback
                # Audio capture runs in separate thread to avoid blocking
                if self.audio_capture:
                    self.audio_capture.start_recording(
                        chunk_callback=self._on_audio_chunk
                    )
                
                self._is_recording = True
                
            except Exception as e:
                logger.error(f"Failed to start recording: {e}", exc_info=True)
                self._handle_error(f"Failed to start recording: {e}")
                self._is_recording = False
    
    def _on_hotkey_release(self) -> None:
        """Callback when hotkey is released - stop recording and transcribe"""
        with self._recording_lock:
            if not self._is_recording:
                logger.warning("Not recording, ignoring hotkey release")
                return
            
            logger.info("Hotkey released, stopping recording")
            
            try:
                # Stop audio recording
                audio_data = None
                if self.audio_capture:
                    audio_data = self.audio_capture.stop_recording()
                
                # Finalize transcription
                if self.speech_recognizer and audio_data:
                    result = self.speech_recognizer.finalize_transcription(audio_data)
                    
                    # Update UI with final transcription
                    if self.ui_overlay:
                        self.ui_overlay.update_transcription(result.text, is_final=True)
                    
                    # Show completion animation
                    if self.ui_overlay:
                        self.ui_overlay.show_completion()
                
                # Finalize input
                if self.input_simulator:
                    self.input_simulator.finalize_input()
                
                self._is_recording = False
                
                # Release audio device immediately to minimize idle resource usage
                # Requirements: 9.2, 9.4
                if self.audio_capture:
                    self.audio_capture.release_device()
                
            except Exception as e:
                logger.error(f"Failed to stop recording: {e}", exc_info=True)
                self._handle_error(f"Failed to process recording: {e}")
                self._is_recording = False
                
                # Ensure audio device is released even on error
                if self.audio_capture:
                    try:
                        self.audio_capture.release_device()
                    except Exception as release_error:
                        logger.error(f"Failed to release audio device: {release_error}")
    
    def _on_audio_chunk(self, audio_chunk: bytes) -> None:
        """
        Callback for streaming audio chunks
        
        Args:
            audio_chunk: Raw audio data chunk
        """
        try:
            # Update UI with audio level MORE FREQUENTLY for better visual feedback
            if self.audio_capture and self.ui_overlay:
                audio_level = self.audio_capture.get_audio_level()
                # Amplify the audio level for better visual feedback
                audio_level = min(1.0, audio_level * 2.0)
                self.ui_overlay.update_audio_level(audio_level)
            
            # Process audio chunk for streaming transcription
            if self.speech_recognizer:
                self.speech_recognizer.process_audio_chunk(audio_chunk)
        
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
    
    def _on_transcription_update(self, text: str, is_final: bool) -> None:
        """
        Callback for streaming transcription updates
        
        Args:
            text: Transcribed text
            is_final: Whether this is the final transcription
        """
        try:
            logger.debug(f"Transcription update: '{text}' (final={is_final})")
            
            # Update UI overlay
            if self.ui_overlay:
                self.ui_overlay.update_transcription(text, is_final)
            
            # Update input field (only for partial results, final is handled in release)
            if not is_final and self.input_simulator:
                try:
                    self.input_simulator.update_text(text)
                except Exception as e:
                    logger.error(f"Failed to update input text: {e}")
        
        except Exception as e:
            logger.error(f"Error handling transcription update: {e}")
    
    def _handle_error(self, message: str) -> None:
        """
        Handle errors by displaying user-friendly notifications
        
        Args:
            message: Error message to display
        """
        logger.error(message)
        
        # Show error in UI overlay
        if self.ui_overlay:
            try:
                self.ui_overlay.show_error(message)
            except Exception as e:
                logger.error(f"Failed to show error in UI: {e}")
    
    def is_running(self) -> bool:
        """Check if daemon is running"""
        return self._running
    
    def wait_for_shutdown(self) -> None:
        """Block until shutdown is requested"""
        try:
            self._shutdown_event.wait()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self.stop()
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
