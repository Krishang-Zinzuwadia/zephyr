# Implementation Plan

- [x] 1. Set up project structure and packaging
  - Create Python package structure with src/zephyr directory
  - Set up setup.py with all dependencies and entry points
  - Create PKGBUILD file for AUR with proper dependencies and install hooks
  - Create systemd user service file for auto-start
  - Create default configuration YAML file template
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 2. Implement configuration management
  - [x] 2.1 Create Config dataclass with all settings
    - Define Config class with hotkey, model, language, audio, typing, and UI settings
    - Implement default values for all configuration options
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 2.2 Implement ConfigManager class
    - Write YAML file loading and parsing logic
    - Implement configuration validation with error handling
    - Add file watcher for live configuration reloading
    - Create user config directory if it doesn't exist
    - _Requirements: 7.1, 7.5_

- [x] 3. Implement audio capture module
  - [x] 3.1 Create AudioCapture class with PyAudio
    - Initialize audio device with 16kHz sample rate, mono channel
    - Implement start_recording() and stop_recording() methods
    - Create circular buffer for audio data storage
    - Implement get_audio_level() for real-time volume feedback
    - Add proper device resource cleanup
    - _Requirements: 1.1, 1.2, 1.3, 8.4_
  
  - [x] 3.2 Add streaming audio chunk processing
    - Implement 1-second audio chunk generation during recording
    - Create callback mechanism for streaming chunks to transcription
    - Add noise reduction using noisereduce library
    - _Requirements: 8.1, 8.4_
  
  - [x] 3.3 Implement error handling for audio devices
    - Handle microphone not found errors
    - Handle permission denied errors
    - Handle device busy errors with user notifications
    - _Requirements: 1.1_

- [x] 4. Implement speech recognition engine
  - [x] 4.1 Create SpeechRecognizer class with faster-whisper
    - Initialize faster-whisper model with configurable size
    - Implement model caching to keep model in memory
    - Add language detection and multi-language support
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 4.2 Implement streaming transcription
    - Create start_streaming_transcription() method with callback
    - Implement process_audio_chunk() for 1-second audio chunks
    - Add Voice Activity Detection using silero-vad
    - Emit partial transcription results via callback
    - Implement sliding window for context preservation
    - _Requirements: 8.1, 8.2, 8.4_
  
  - [x] 4.3 Add transcription finalization
    - Implement finalize_transcription() for final result
    - Calculate confidence scores for transcription quality
    - Handle low-confidence transcriptions with indicators
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 5. Implement input simulation module
  - [x] 5.1 Create InputSimulator base class
    - Implement focused window detection
    - Create input field focus verification
    - Add typing speed configuration
    - _Requirements: 2.1, 2.2, 2.3, 2.5_
  
  - [x] 5.2 Implement X11 input simulation
    - Use python-xlib for keyboard event simulation
    - Implement character-by-character typing
    - Handle special characters and Unicode
    - _Requirements: 2.1, 2.5_
  
  - [x] 5.3 Implement Wayland input simulation
    - Use python-evdev with uinput for input simulation
    - Implement same typing interface as X11
    - _Requirements: 2.1, 2.5_
  
  - [x] 5.4 Add streaming text update support
    - Implement start_streaming_input() method
    - Create update_text() to replace previous transcription
    - Track typed character count for accurate backspace simulation
    - Implement backspace simulation to delete old text
    - Add append_text() for incremental updates
    - _Requirements: 8.2, 8.3_
  
  - [x] 5.5 Add clipboard fallback mechanism
    - Detect when direct typing fails
    - Implement clipboard-based text insertion as fallback
    - _Requirements: 2.4_

- [x] 6. Implement UI overlay
  - [x] 6.1 Create GTK4 overlay window
    - Create borderless, always-on-top window
    - Implement rounded rectangle with 16px border radius using CSS
    - Add semi-transparent background with blur effect
    - Center window on screen using monitor geometry
    - Implement lazy initialization (create only on key press)
    - _Requirements: 6.1, 6.2, 6.4, 6.5_
  
  - [x] 6.2 Implement waveform visualization
    - Create custom Cairo drawing for animated waveform bars
    - Implement update_audio_level() to animate bars based on volume
    - Use GLib timeout for 60fps animation
    - _Requirements: 6.2_
  
  - [x] 6.3 Add live transcription display
    - Create text display area below waveform
    - Implement update_transcription() method
    - Show partial results in lighter color
    - Show final results in full opacity
    - Add smooth fade transition when text updates
    - Implement dynamic height adjustment for text wrapping
    - _Requirements: 8.1, 8.5_
  
  - [x] 6.4 Implement animations
    - Create fade-in animation (200ms) on show
    - Create fade-out animation (300ms) on hide
    - Add checkmark animation on completion
    - Implement smooth text transition animations
    - _Requirements: 6.4_
  
  - [x] 6.5 Add error notification display
    - Implement show_error() method with error message
    - Style error state with red accent color
    - _Requirements: 6.1_

- [x] 7. Implement hotkey listener
  - [x] 7.1 Create HotkeyListener class
    - Use pynput for global hotkey registration
    - Register backslash key as default hotkey
    - Implement configurable hotkey support
    - _Requirements: 1.4, 7.2_
  
  - [x] 7.2 Add key press/release detection
    - Implement on_key_press() callback
    - Implement on_key_release() callback
    - Add debouncing for minimum press duration (100ms)
    - Filter out accidental short presses
    - _Requirements: 1.1, 1.3, 1.5, 7.4_
  
  - [x] 7.3 Connect hotkey to audio capture
    - Trigger audio recording on key press
    - Stop recording and start transcription on key release
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 8. Implement main daemon process
  - [x] 8.1 Create ZephyrDaemon class
    - Initialize all subsystems (config, audio, recognition, input, UI, hotkey)
    - Implement start() method to begin daemon
    - Implement stop() method for graceful shutdown
    - Add signal handlers for SIGTERM and SIGINT
    - _Requirements: 5.5, 9.1, 9.2_
  
  - [x] 8.2 Wire up component communication
    - Connect hotkey listener to audio capture
    - Connect audio capture to speech recognition via streaming
    - Connect speech recognition to input simulator via callbacks
    - Connect audio capture to UI overlay for waveform
    - Connect speech recognition to UI overlay for text display
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 6.2, 8.1, 8.2_
  
  - [x] 8.3 Implement error handling and logging
    - Set up logging to ~/.local/share/zephyr/logs/
    - Add error handlers for all component failures
    - Display user-friendly error notifications
    - Implement automatic recovery for transient errors
    - _Requirements: 9.4_
  
  - [x] 8.4 Add command-line interface
    - Create CLI entry point with --daemon flag
    - Add --config flag for custom config path
    - Add --version flag
    - Add --stop flag to stop running daemon
    - _Requirements: 5.1_

- [x] 9. Create AUR package files
  - [x] 9.1 Write PKGBUILD
    - Define package metadata (name, version, description)
    - List all dependencies: python, portaudio, gtk4, python packages
    - Add optional dependencies: whisper.cpp, noisereduce
    - Implement build() function using Python setuptools
    - Implement package() function to install files
    - _Requirements: 5.1, 5.2_
  
  - [x] 9.2 Create systemd service file
    - Write zephyr.service for user service
    - Set up auto-start with graphical-session.target
    - Configure restart on failure
    - _Requirements: 5.5_
  
  - [x] 9.3 Create installation script
    - Write zephyr.install for post-install hooks
    - Enable systemd service on installation
    - Create config directory structure
    - Download default Whisper model on first install
    - _Requirements: 5.3, 5.4_
  
  - [x] 9.4 Write package documentation
    - Create README.md with installation instructions
    - Document configuration options
    - Add troubleshooting section
    - Include usage examples
    - _Requirements: 5.1_

- [x] 10. Implement resource optimization
  - [x] 10.1 Optimize idle resource usage
    - Ensure daemon uses <50MB RAM when idle
    - Minimize CPU usage to <1% when idle
    - Release audio device immediately after use
    - Destroy UI overlay window when hidden
    - _Requirements: 9.1, 9.2, 9.4_
  
  - [x] 10.2 Optimize active resource usage
    - Limit CPU usage to <20% during recording
    - Use efficient audio buffering
    - Implement model caching to avoid reloading
    - Use threading for parallel audio capture and transcription
    - _Requirements: 9.3, 9.5_

- [x] 11. Create entry point and final integration
  - [x] 11.1 Create main entry point script
    - Write zephyr CLI script in src/zephyr/__main__.py
    - Parse command-line arguments
    - Initialize and start ZephyrDaemon
    - Handle keyboard interrupt for clean shutdown
    - _Requirements: 5.1_
  
  - [x] 11.2 Test complete workflow
    - Verify hotkey detection works globally
    - Test audio capture and streaming
    - Verify real-time transcription updates
    - Test text replacement when user changes mind
    - Verify UI overlay animations
    - Test with multiple accents using sample audio
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 3.1, 3.2, 3.3, 4.1, 4.2, 6.1, 6.2, 8.1, 8.2, 8.3_
  
  - [x] 11.3 Verify AUR package installation
    - Build package using makepkg
    - Install package and verify all files are in correct locations
    - Test systemd service auto-start
    - Verify configuration file is created
    - Test package removal and cleanup
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
