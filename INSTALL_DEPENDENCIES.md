# Installing Zephyr Dependencies

## The Issue

You're seeing: `ModuleNotFoundError: No module named 'gi'`

This means PyGObject (gi) is not installed in your Python environment.

## Solution

### Option 1: Use System Python (Recommended)

The system Python (`/usr/bin/python3`) already has the required packages installed via pacman.

**Already done!** The `start_zephyr.sh` script now uses `/usr/bin/python3`.

Just run:
```bash
./start_zephyr.sh
```

### Option 2: Install Missing Packages

If you want to use your current Python environment, install these packages:

```bash
# Install system dependencies first (if not already installed)
sudo pacman -S python-gobject gtk4 portaudio python-pyaudio python-yaml

# Then install Python packages
pip install --user PyYAML pynput python-xlib evdev watchdog faster-whisper
```

### Option 3: Complete Fresh Install

Run the full installation script:

```bash
bash install.sh
```

This will:
1. Install all system dependencies via pacman
2. Install all Python packages via pip
3. Set up configuration directories
4. Test the installation

## Verify Installation

Check which dependencies are installed:

```bash
/usr/bin/python3 check_deps.py
```

## Common Issues

### 1. "gi module not found"
**Solution**: Use system Python (`/usr/bin/python3`) or install `python-gobject` via pacman

### 2. "pyaudio not found"
**Solution**: `sudo pacman -S python-pyaudio portaudio`

### 3. "faster-whisper not found"
**Solution**: `pip install --user faster-whisper`

This will download on first use (takes a few minutes)

## Quick Test

Test if basic imports work:

```bash
/usr/bin/python3 -c "import gi; import yaml; import pynput; print('✓ Core deps OK')"
```

## Start Zephyr

Once dependencies are installed:

```bash
./start_zephyr.sh
```

Or directly:

```bash
/usr/bin/python3 -m src.zephyr
```

**Hotkey**: Press and hold **Ctrl + Right Alt** to activate voice input!
