# Zephyr - Voice-to-Text Input for Linux

Push-to-talk voice input that types transcribed text anywhere on your Linux system.

## Quick Start

```bash
sudo -E ./zephyr
```

The `-E` flag preserves your environment (Python packages, display access).

Then press and hold the **`** (backtick) key to record. Speak, then release to transcribe and type.

## Installation

### Dependencies

```bash
# Arch Linux
sudo pacman -S python python-pip gtk4 python-gobject portaudio

# Install Python packages
pip install sounddevice numpy faster-whisper pynput PyYAML watchdog evdev
```

### Configuration

Config file: `~/.config/zephyr/config.yaml`

```yaml
hotkey: "`"  # Backtick key
model: "base"  # Whisper model (tiny, base, small, medium, large)
language: "auto"  # or "en", "es", "fr", etc.
```

## Usage

1. **Start**: `sudo ./zephyr`
2. **Record**: Press and hold ` (backtick)
3. **Speak**: Say your text
4. **Release**: Let go to transcribe and type

## Why Sudo?

Zephyr needs root access to:
- Monitor keyboard events globally
- Suppress the hotkey so it doesn't type
- Simulate keyboard input reliably

Use `sudo -E` to preserve your user environment (Python packages, display access).

## Hotkey Options

Edit `~/.config/zephyr/config.yaml`:

```yaml
hotkey: "`"           # Backtick (default)
hotkey: "ctrl+space"  # Ctrl + Space
hotkey: "f12"         # F12 key
```

## Features

- ✓ Works in any application
- ✓ Real-time transcription with Whisper
- ✓ Automatic typing of transcribed text
- ✓ Visual feedback overlay
- ✓ Configurable hotkey
- ✓ Multiple language support

## Files

- `zephyr` - Main executable
- `src/` - Source code
- `config/` - Example configurations
- `~/.config/zephyr/config.yaml` - User configuration

## Troubleshooting

### Permission Denied

Make sure to run with sudo -E:
```bash
sudo -E ./zephyr
```

The `-E` flag is important - it preserves your environment.

### Model Download

First run will download the Whisper model (~150MB for base model). This is one-time.

### Hotkey Not Working

Try a different key in the config file. Some keys work better than others.

## License

See LICENSE file.
