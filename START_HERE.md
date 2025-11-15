# Start Here - Get Zephyr Running

## Current Status

✅ Hotkey changed to **Ctrl + Right Alt**  
✅ Code is complete and ready  
⚠️  Need to install dependencies

## Step 1: Install System Dependencies

Run this command:

```bash
sudo pacman -S python-gobject gtk4 portaudio python-pyaudio python-yaml python-numpy
```

## Step 2: Install Python Packages

```bash
pip install --user pynput python-xlib evdev watchdog faster-whisper noisereduce
```

Or run the install script:

```bash
bash install.sh
```

## Step 3: Test Dependencies

```bash
/usr/bin/python3 test_imports.py
```

This will show which packages are installed and which are missing.

## Step 4: Start Zephyr

```bash
./start_zephyr.sh
```

Or:

```bash
/usr/bin/python3 -m src.zephyr
```

## Step 5: Use It!

1. Make sure Zephyr is running (you'll see a message)
2. Click in any text field (browser, editor, terminal, etc.)
3. **Press and hold Ctrl + Right Alt**
4. Speak your text clearly
5. Release the keys when done
6. Text will appear!

## First Run Note

The first time you use it, Zephyr will download the Whisper model (about 150MB for the "base" model). This takes 2-5 minutes depending on your internet speed. After that, it's instant!

## Troubleshooting

### If you see "ModuleNotFoundError: No module named 'gi'"
```bash
sudo pacman -S python-gobject gtk4
```

### If you see "ModuleNotFoundError: No module named 'pyaudio'"
```bash
sudo pacman -S python-pyaudio portaudio
```

### If you see "ModuleNotFoundError: No module named 'faster_whisper'"
```bash
pip install --user faster-whisper
```

### Check what's installed
```bash
/usr/bin/python3 check_deps.py
```

### View logs
```bash
tail -f ~/.local/share/zephyr/logs/zephyr.log
```

## Configuration

Config file: `~/.config/zephyr/config.yaml`

Change hotkey, model, language, typing speed, and more!

## Need Help?

1. Check `INSTALL_DEPENDENCIES.md` for detailed dependency info
2. Check `READY_TO_USE.md` for usage tips
3. Check `QUICK_START.md` for configuration options

---

**TL;DR**: Install deps, run `./start_zephyr.sh`, press Ctrl+Right Alt, speak, release!
