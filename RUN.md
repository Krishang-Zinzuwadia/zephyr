# Run Zephyr

## Start Zephyr

```bash
sudo -E ./zephyr
```

**Important:** Use `-E` to preserve your environment!

## Use It

1. Wait for "✓ Zephyr is running!"
2. Press and hold **`** (backtick key, top-left of keyboard)
3. Speak your text
4. Release the key
5. Text will be transcribed and typed

## Stop

Press **Ctrl+C** in the terminal

## That's It!

Running with sudo gives Zephyr the permissions it needs to:
- Detect keyboard events globally
- Suppress the hotkey
- Type the transcribed text

Everything should work now! 🎤
