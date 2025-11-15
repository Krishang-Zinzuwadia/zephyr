# Zephyr is Ready to Use! 🎤

## Quick Start

### 1. Install Dependencies (if not done yet)

```bash
bash install.sh
```

Or just Python packages:
```bash
bash install_python_only.sh
```

### 2. Start Zephyr

```bash
./start_zephyr.sh
```

Or directly:
```bash
python3 -m src.zephyr
```

### 3. Use Voice Input

**Press and hold: Ctrl + Right Alt**
- Speak your text
- Release when done
- Text will be typed automatically!

## Configuration

Your config is at: `~/.config/zephyr/config.yaml`

Current hotkey: **Ctrl + Right Alt** (ctrl+alt_r)

To change it, edit the config:
```yaml
hotkey: "ctrl+alt_r"  # Change to your preference
```

Other hotkey examples:
- `"backslash"` - The \ key
- `"space"` - Spacebar
- `"ctrl+shift+v"` - Ctrl+Shift+V
- `"f12"` - F12 key

## What Happens on First Run

1. Zephyr will download the Whisper model (base) - takes a few minutes
2. Model is cached at `~/.cache/zephyr/models/`
3. After that, startup is instant!

## Troubleshooting

### Dependencies Missing?
```bash
# Install system packages (Arch)
sudo pacman -S python python-pip portaudio gtk4 python-gobject

# Install Python packages
pip install --user PyYAML pynput faster-whisper python-xlib evdev watchdog
```

### Check if it's running
```bash
ps aux | grep zephyr
```

### View logs
```bash
tail -f ~/.local/share/zephyr/logs/zephyr.log
```

### Stop the daemon
```bash
python3 -m src.zephyr --stop
```

## Tips

- Speak clearly and at normal pace
- Works in any application with text input
- Say "comma", "period", "question mark" for punctuation
- Keep holding the keys while speaking
- Release when you're done speaking

Enjoy! 🚀
