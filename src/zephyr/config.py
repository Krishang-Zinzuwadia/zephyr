"""
Configuration management for Zephyr voice-to-text application
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Callable, Any
import yaml
import logging

# Make watchdog optional - only needed for live config reloading
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None
    FileModifiedEvent = None


logger = logging.getLogger(__name__)


@dataclass
class AudioConfig:
    """Audio capture configuration"""
    sample_rate: int = 16000
    channels: int = 1
    chunk_duration: float = 1.0  # seconds - for streaming transcription


@dataclass
class TypingConfig:
    """Text input simulation configuration"""
    speed: int = 50  # characters per second
    use_clipboard_fallback: bool = True


@dataclass
class UIConfig:
    """UI overlay configuration"""
    width: int = 400
    height: int = 120
    border_radius: int = 16
    background_opacity: float = 0.95
    blur_enabled: bool = True
    animation_speed: float = 1.0  # multiplier for animation timing
    show_confidence: bool = False  # Show transcription confidence scores


@dataclass
class AdvancedConfig:
    """Advanced configuration options"""
    min_press_duration: int = 100  # milliseconds
    auto_start: bool = True
    log_level: str = "INFO"
    log_file: str = "~/.local/share/zephyr/logs/zephyr.log"
    
    # Voice Activity Detection
    vad_enabled: bool = True
    vad_threshold: float = 0.5  # 0.0 to 1.0
    
    # Transcription settings
    beam_size: int = 5
    best_of: int = 5
    temperature: float = 0.0
    
    # Resource management (optimized for low idle usage)
    # Requirements: 9.1, 9.2, 9.3, 9.5
    unload_model_after: int = 300  # seconds (0 = never) - unload model to free memory when idle
    max_recording_duration: int = 60  # seconds - limit recording duration to prevent memory issues


@dataclass
class Config:
    """Main configuration class for Zephyr application"""
    
    # Core settings
    hotkey: str = "backslash"
    model: str = "base"
    language: str = "auto"
    
    # Nested configuration sections
    audio: AudioConfig = field(default_factory=AudioConfig)
    typing: TypingConfig = field(default_factory=TypingConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    advanced: AdvancedConfig = field(default_factory=AdvancedConfig)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create Config instance from dictionary"""
        # Extract nested configs
        audio_data = data.get("audio", {})
        typing_data = data.get("typing", {})
        ui_data = data.get("ui", {})
        advanced_data = data.get("advanced", {})
        
        return cls(
            hotkey=data.get("hotkey", "backslash"),
            model=data.get("model", "base"),
            language=data.get("language", "auto"),
            audio=AudioConfig(**audio_data) if audio_data else AudioConfig(),
            typing=TypingConfig(**typing_data) if typing_data else TypingConfig(),
            ui=UIConfig(**ui_data) if ui_data else UIConfig(),
            advanced=AdvancedConfig(**advanced_data) if advanced_data else AdvancedConfig(),
        )
    
    def to_dict(self) -> dict:
        """Convert Config instance to dictionary"""
        return {
            "hotkey": self.hotkey,
            "model": self.model,
            "language": self.language,
            "audio": asdict(self.audio),
            "typing": asdict(self.typing),
            "ui": asdict(self.ui),
            "advanced": asdict(self.advanced),
        }
    
    def validate(self) -> list[str]:
        """
        Validate configuration values
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate hotkey
        if not self.hotkey or not isinstance(self.hotkey, str):
            errors.append("hotkey must be a non-empty string")
        
        # Validate model
        valid_models = ["tiny", "base", "small", "medium", "large"]
        if self.model not in valid_models:
            errors.append(f"model must be one of {valid_models}, got '{self.model}'")
        
        # Validate language
        if not self.language or not isinstance(self.language, str):
            errors.append("language must be a non-empty string")
        
        # Validate audio config
        if self.audio.sample_rate <= 0:
            errors.append("audio.sample_rate must be positive")
        if self.audio.channels not in [1, 2]:
            errors.append("audio.channels must be 1 (mono) or 2 (stereo)")
        if self.audio.chunk_duration <= 0:
            errors.append("audio.chunk_duration must be positive")
        
        # Validate typing config
        if self.typing.speed <= 0:
            errors.append("typing.speed must be positive")
        
        # Validate UI config
        if self.ui.width <= 0:
            errors.append("ui.width must be positive")
        if self.ui.height <= 0:
            errors.append("ui.height must be positive")
        if self.ui.border_radius < 0:
            errors.append("ui.border_radius must be non-negative")
        if not 0.0 <= self.ui.background_opacity <= 1.0:
            errors.append("ui.background_opacity must be between 0.0 and 1.0")
        if self.ui.animation_speed <= 0:
            errors.append("ui.animation_speed must be positive")
        
        # Validate advanced config
        if self.advanced.min_press_duration < 0:
            errors.append("advanced.min_press_duration must be non-negative")
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.advanced.log_level not in valid_log_levels:
            errors.append(f"advanced.log_level must be one of {valid_log_levels}")
        if not 0.0 <= self.advanced.vad_threshold <= 1.0:
            errors.append("advanced.vad_threshold must be between 0.0 and 1.0")
        if self.advanced.beam_size <= 0:
            errors.append("advanced.beam_size must be positive")
        if self.advanced.best_of <= 0:
            errors.append("advanced.best_of must be positive")
        if self.advanced.temperature < 0:
            errors.append("advanced.temperature must be non-negative")
        if self.advanced.unload_model_after < 0:
            errors.append("advanced.unload_model_after must be non-negative")
        if self.advanced.max_recording_duration <= 0:
            errors.append("advanced.max_recording_duration must be positive")
        
        return errors


if WATCHDOG_AVAILABLE:
    class ConfigFileWatcher(FileSystemEventHandler):
        """File system event handler for configuration file changes"""
        
        def __init__(self, config_path: Path, callback: Callable[[], None]):
            self.config_path = config_path
            self.callback = callback
            super().__init__()
        
        def on_modified(self, event):
            """Handle file modification events"""
            if isinstance(event, FileModifiedEvent):
                if Path(event.src_path).resolve() == self.config_path.resolve():
                    logger.info(f"Configuration file modified: {self.config_path}")
                    self.callback()
else:
    ConfigFileWatcher = None


class ConfigManager:
    """
    Configuration manager for Zephyr application
    
    Handles loading, saving, validation, and live reloading of configuration
    """
    
    def __init__(self, config_path: str):
        """
        Initialize ConfigManager
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self._config: Optional[Config] = None
        self._observer: Optional[Observer] = None
        self._watch_callback: Optional[Callable[[], None]] = None
    
    def load(self) -> Config:
        """
        Load configuration from file
        
        Returns:
            Config instance with loaded or default values
        
        Raises:
            ValueError: If configuration validation fails
        """
        # Create config directory if it doesn't exist
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load from file if it exists
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {self.config_path}")
            except yaml.YAMLError as e:
                logger.error(f"Failed to parse configuration file: {e}")
                raise ValueError(f"Invalid YAML in configuration file: {e}")
            except Exception as e:
                logger.error(f"Failed to read configuration file: {e}")
                raise ValueError(f"Failed to read configuration file: {e}")
        else:
            # Use default configuration
            logger.info(f"Configuration file not found at {self.config_path}, using defaults")
            data = {}
        
        # Create Config instance
        try:
            config = Config.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to create configuration: {e}")
            raise ValueError(f"Failed to create configuration: {e}")
        
        # Validate configuration
        errors = config.validate()
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Save default configuration if file doesn't exist
        if not self.config_path.exists():
            self.save(config)
            logger.info(f"Created default configuration at {self.config_path}")
        
        self._config = config
        return config
    
    def save(self, config: Config) -> None:
        """
        Save configuration to file
        
        Args:
            config: Config instance to save
        
        Raises:
            ValueError: If configuration validation fails
        """
        # Validate before saving
        errors = config.validate()
        if errors:
            error_msg = "Cannot save invalid configuration:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Create directory if it doesn't exist
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to file
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(config.to_dict(), f, default_flow_style=False, sort_keys=False)
            logger.info(f"Saved configuration to {self.config_path}")
            self._config = config
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise ValueError(f"Failed to save configuration: {e}")
    
    def watch_for_changes(self, callback: Callable[[], None]) -> None:
        """
        Watch configuration file for changes and call callback on modification
        
        Args:
            callback: Function to call when configuration file is modified
        
        Note:
            Requires watchdog package. If not available, config watching is disabled.
        """
        if not WATCHDOG_AVAILABLE:
            logger.warning("watchdog package not available - config file watching disabled")
            logger.info("Install watchdog to enable live config reloading: pip install watchdog")
            return
        
        if self._observer is not None:
            logger.warning("Configuration watcher already running")
            return
        
        self._watch_callback = callback
        
        # Set up file watcher
        event_handler = ConfigFileWatcher(self.config_path, self._on_config_changed)
        self._observer = Observer()
        
        # Watch the parent directory (watching individual files can be unreliable)
        watch_path = self.config_path.parent
        self._observer.schedule(event_handler, str(watch_path), recursive=False)
        self._observer.start()
        
        logger.info(f"Started watching configuration file: {self.config_path}")
    
    def stop_watching(self) -> None:
        """Stop watching configuration file for changes"""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info("Stopped watching configuration file")
    
    def _on_config_changed(self) -> None:
        """Internal callback when configuration file changes"""
        try:
            # Reload configuration
            new_config = self.load()
            logger.info("Configuration reloaded successfully")
            
            # Call user callback
            if self._watch_callback:
                self._watch_callback()
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
    
    @property
    def config(self) -> Optional[Config]:
        """Get current configuration"""
        return self._config
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stop watching"""
        self.stop_watching()
