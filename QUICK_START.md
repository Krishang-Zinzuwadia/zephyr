# Zephyr Voice Input - Quick Start Guide

## Installation

### Option 1: From AUR (Recommended for Arch Linux)

```bash
# Build and install
makepkg -si

# Enable and start the service
systemctl --user enable --now zephyr.service
```

### Option 2: From Source

```bash
# Install dependencies
pip install -r requirements.txt

# Run directly
python3 -m src.zephyr
```

## Basic Usage

1. **Start Zephyr** (if not using systemd):
   ```bash
   zephyr
   ```

2. **Use voice input**:
   - Press and hold **Ctrl + Right Alt** keys together
   - Speak your text clearly
   - Release the keys when done
   - Text will be typed automatically

## Configuration

Edit `~/.config/zephyr/config.yaml`:

```yaml
# Change the activation key
hotkey: "ctrl+alt_r"  # or "backslash", "space", "ctrl+shift+v", etc.

# Choose Whisper model (tiny, base, small, medium, large)
model: "base"  # base is recommended for balance

# Set language (auto-detect or specific: en, es, fr, etc.)
language: "auto"

# Adjust typing speed (characters per second)
typing:
  speed: 50
```

Changes are applied automatically - no restart needed!

## Commands

```bash
# Start daemon
zephyr

# Start with custom config
zephyr --config /path/to/config.yaml

# Stop running daemon
zephyr --stop

# Show version
zephyr --version

# Enable debug logging
zephyr --debug
```

## Systemd Service

```bash
# Enable auto-start on login
systemctl --user enable zephyr.service

# Start now
systemctl --user start zephyr.service

# Check status
systemctl --user status zephyr.service

# View logs
journalctl --user -u zephyr.service -f

# Stop service
systemctl --user stop zephyr.service

# Disable auto-start
systemctl --user disable zephyr.service
```

## Troubleshooting

### No microphone detected
```bash
# Check audio devices
arecord -l

# Test microphone
arecord -d 5 test.wav && aplay test.wav
```

### Hotkey not working
- Check if another application is using the same key
- Try a different hotkey in config
- Ensure Zephyr is running: `ps aux | grep zephyr`

### Text not being typed
- Make sure an input field is focused
- Check if clipboard fallback is enabled in config
- Verify input permissions for X11/Wayland

### High resource usage
- Use a smaller Whisper model (tiny or base)
- Check logs: `journalctl --user -u zephyr.service`
- Ensure only one instance is running

### Model download issues
- Models are downloaded automatically on first use
- Check internet connection
- Verify cache directory: `~/.cache/zephyr/models/`

## Tips

- **Speak clearly** for best accuracy
- **Use punctuation words**: Say "comma", "period", "question mark"
- **Change your mind**: Keep holding the key and correct yourself
- **Short phrases**: Better accuracy with shorter utterances
- **Quiet environment**: Reduces background noise interference

## Testing

```bash
# Run integration tests
python3 test_integration_workflow.py

# Verify AUR package
bash test_aur_package.sh

# Manual testing guide
cat test_manual_workflow.md
```

## File Locations

- **Config**: `~/.config/zephyr/config.yaml`
- **Logs**: `~/.local/share/zephyr/logs/`
- **Cache**: `~/.cache/zephyr/models/`
- **System config**: `/etc/zephyr/config.yaml` (default template)

## Support

For issues, questions, or contributions:
- Check the documentation in `docs/`
- Review examples in `examples/`
- Read the full README.md

## Uninstallation

```bash
# Stop and disable service
systemctl --user stop zephyr.service
systemctl --user disable zephyr.service

# Remove package (AUR)
sudo pacman -R zephyr-voice-input

# Remove config and cache (optional)
rm -rf ~/.config/zephyr ~/.cache/zephyr ~/.local/share/zephyr
```

---

**Enjoy hands-free typing with Zephyr!** 🎤✨
