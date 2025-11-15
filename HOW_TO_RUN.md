# How to Run Zephyr

Zephyr is now installed and ready to use!

## Quick Start

Run Zephyr with:

```bash
python3 zephyr_launcher.py
```

Or use the original start script:

```bash
./start_zephyr.sh
```

## Usage

1. **Start Zephyr**: Run the launcher script
2. **Activate voice input**: Press and hold **Ctrl + Right Alt**
3. **Speak**: While holding the keys, speak your text
4. **Release**: Release the keys to stop recording and insert the transcribed text
5. **Stop Zephyr**: Press `Ctrl+C` in the terminal

## Hotkey

The default hotkey is **Ctrl + Right Alt**. You can change this in the config file:

```bash
~/.config/zephyr/config.yaml
```

Available hotkey options:
- **Single keys**:
  - `backslash` - The backslash key
  - `space` - Spacebar
  - `tab` - Tab key
  - `enter` - Enter key
  - `esc` - Escape key
  - Any single character (e.g., `a`, `1`, etc.)

- **Key combinations** (format: `modifier+key`):
  - `ctrl+alt_r` - Ctrl + Right Alt (default)
  - `ctrl+alt_l` - Ctrl + Left Alt
  - `ctrl+space` - Ctrl + Space
  - `shift+space` - Shift + Space
  - And many more combinations!

Available modifiers: `ctrl`, `ctrl_l`, `ctrl_r`, `alt`, `alt_l`, `alt_r`, `shift`

## Configuration

Edit the configuration file at:
```
~/.config/zephyr/config.yaml
```

Key settings:
- `hotkey`: The key to activate voice input
- `model`: Speech recognition model (`tiny`, `base`, `small`, `medium`, `large`)
- `language`: Language code (e.g., `en`, `es`, `fr`) or `auto` for automatic detection
- `typing.speed`: Typing speed in characters per second

## Troubleshooting

### Permission Issues

If you get permission errors for `/dev/uinput`, you need to set up permissions:

```bash
# Add your user to the input group
sudo usermod -a -G input $USER

# Create udev rule
sudo tee /etc/udev/rules.d/99-uinput.rules << EOF
KERNEL=="uinput", MODE="0660", GROUP="input", OPTIONS+="static_node=uinput"
EOF

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Log out and log back in for group changes to take effect
```

### Model Download

The first time you run Zephyr, it will download the Whisper model (about 150MB for the `base` model). This may take a few minutes depending on your internet connection.

## Logs

Logs are stored at:
```
~/.local/share/zephyr/logs/zephyr.log
```

## Dependencies

All required dependencies should already be installed:
- PyGObject (GTK 4)
- sounddevice
- numpy
- faster-whisper
- pynput
- PyYAML
- watchdog
- evdev

If you encounter missing dependencies, run:
```bash
pip install sounddevice numpy faster-whisper pynput PyYAML watchdog evdev
```
