# Requirements Document

## Introduction

Zephyr is a voice-to-text input application for Omarchy Linux that enables users to dictate text using voice commands. The application activates when the user presses and holds the backslash (\) key, captures audio input, transcribes it using speech recognition, and types the transcribed text into the active input field. The application is designed to support multiple accents and voices with high accuracy, and will be distributed via the Arch User Repository (AUR).

## Glossary

- **Zephyr**: The voice-to-text input application being developed
- **Push-to-Talk (PTT)**: A method of activating voice input by pressing and holding a key
- **Speech Recognition Engine**: The component that converts audio to text
- **Input Field**: Any text entry area in the active application window
- **AUR (Arch User Repository)**: A community-driven repository for Arch Linux packages
- **PKGBUILD**: The build script used to create AUR packages
- **Global Hotkey**: A keyboard shortcut that works across all applications
- **Audio Buffer**: Temporary storage for captured audio data
- **Transcription**: The process of converting speech audio to written text

## Requirements

### Requirement 1

**User Story:** As a user, I want to activate voice input by pressing and holding the backslash key, so that I can quickly dictate text without switching applications

#### Acceptance Criteria

1. WHEN the user presses the backslash (\) key, THE Zephyr SHALL activate the microphone and begin capturing audio
2. WHILE the backslash key is held down, THE Zephyr SHALL continuously record audio from the default microphone
3. WHEN the user releases the backslash key, THE Zephyr SHALL stop recording and begin transcription
4. THE Zephyr SHALL register the backslash key as a global hotkey that works across all applications
5. IF the backslash key is pressed for less than 100 milliseconds, THEN THE Zephyr SHALL ignore the input to prevent accidental activation

### Requirement 2

**User Story:** As a user, I want the transcribed text to be automatically typed into the active input field, so that I can seamlessly continue my work without manual copying

#### Acceptance Criteria

1. WHEN transcription is complete, THE Zephyr SHALL identify the currently focused input field in the active application
2. THE Zephyr SHALL simulate keyboard input to type the transcribed text into the focused input field
3. THE Zephyr SHALL preserve the original cursor position and text selection state before typing
4. IF no input field is focused, THEN THE Zephyr SHALL display a notification indicating that no target field was found
5. THE Zephyr SHALL type the transcribed text at a rate that ensures all characters are captured by the target application

### Requirement 3

**User Story:** As a user with a specific accent or voice characteristic, I want the application to accurately recognize my speech, so that I can use voice input effectively regardless of my speaking style

#### Acceptance Criteria

1. THE Zephyr SHALL use a speech recognition engine that supports multiple English accents including American, British, Australian, Indian, and South African
2. THE Zephyr SHALL use a speech recognition engine that supports non-English languages and accents
3. THE Zephyr SHALL maintain transcription accuracy above 90 percent for clear speech across supported accents
4. THE Zephyr SHALL process audio with noise reduction to improve recognition accuracy in varied environments
5. WHERE the user configures a preferred language or accent, THE Zephyr SHALL prioritize that configuration during transcription

### Requirement 4

**User Story:** As a user, I want the transcription to be lossless for typing, so that every word I speak is accurately captured without missing characters or words

#### Acceptance Criteria

1. THE Zephyr SHALL transcribe all spoken words without omitting any content from the audio input
2. THE Zephyr SHALL preserve punctuation marks when explicitly spoken by the user
3. THE Zephyr SHALL handle continuous speech without introducing artificial breaks or truncation
4. IF the speech recognition confidence for a word is below 70 percent, THEN THE Zephyr SHALL include the best-guess transcription with a visual indicator
5. THE Zephyr SHALL buffer the complete audio recording until transcription is finished to prevent data loss

### Requirement 5

**User Story:** As an Omarchy Linux user, I want to install Zephyr from the AUR, so that I can easily manage the application using my package manager

#### Acceptance Criteria

1. THE Zephyr SHALL include a PKGBUILD file that follows AUR packaging guidelines
2. THE Zephyr SHALL declare all runtime dependencies in the PKGBUILD file
3. THE Zephyr SHALL install all required binaries to /usr/bin with appropriate permissions
4. THE Zephyr SHALL install configuration files to /etc/zephyr or the user's home directory
5. WHEN installed via the AUR, THE Zephyr SHALL automatically start on system login

### Requirement 6

**User Story:** As a user, I want visual feedback when voice input is active, so that I know when the application is listening to my speech

#### Acceptance Criteria

1. WHEN the microphone is activated, THE Zephyr SHALL display a visual indicator on the screen
2. THE Zephyr SHALL show real-time audio level feedback while recording
3. WHEN transcription is in progress, THE Zephyr SHALL display a processing indicator
4. THE Zephyr SHALL hide all visual indicators within 500 milliseconds after transcription is complete
5. WHERE the user configures minimal UI mode, THE Zephyr SHALL display only essential status information

### Requirement 7

**User Story:** As a user, I want to configure application settings, so that I can customize the behavior to match my preferences

#### Acceptance Criteria

1. THE Zephyr SHALL provide a configuration file for user-customizable settings
2. WHERE the user specifies a custom hotkey, THE Zephyr SHALL use that key instead of the default backslash key
3. WHERE the user specifies a preferred speech recognition model, THE Zephyr SHALL use that model for transcription
4. THE Zephyr SHALL allow users to configure the minimum key press duration threshold
5. THE Zephyr SHALL reload configuration changes without requiring application restart

### Requirement 8

**User Story:** As a user, I want to see what I'm saying in real-time and be able to change my mind mid-sentence, so that I can correct myself naturally without starting over

#### Acceptance Criteria

1. WHILE the user is speaking, THE Zephyr SHALL display partial transcription results in the UI overlay
2. WHILE the user is speaking, THE Zephyr SHALL type partial transcription results into the active input field
3. WHEN the transcription updates with new text, THE Zephyr SHALL replace the previously typed text with the updated transcription
4. THE Zephyr SHALL process audio in chunks of 1 second or less to provide real-time feedback
5. THE Zephyr SHALL visually distinguish between partial transcription and final transcription in the UI overlay

### Requirement 9

**User Story:** As a system administrator, I want the application to have minimal resource usage, so that it does not impact system performance when idle

#### Acceptance Criteria

1. WHILE idle and not recording, THE Zephyr SHALL consume less than 50 megabytes of RAM
2. WHILE idle and not recording, THE Zephyr SHALL consume less than 1 percent CPU on a modern processor
3. WHEN recording audio, THE Zephyr SHALL limit CPU usage to less than 20 percent
4. THE Zephyr SHALL release audio device resources immediately after recording stops
5. THE Zephyr SHALL use efficient audio buffering to minimize memory allocation during recording
