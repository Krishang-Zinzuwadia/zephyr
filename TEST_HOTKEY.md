# Test Hotkey Detection

To verify that Ctrl + Right Alt is being detected correctly:

## Step 1: Run the Hotkey Test

```bash
python3 test_hotkey_live.py
```

This will:
- Start a simple hotkey listener
- Show messages when you press/release Ctrl + Right Alt
- Help verify the hotkey is working before testing the full app

## Step 2: Test the Hotkey

1. Wait for the message "✓ Listener is active!"
2. Press and hold **Ctrl + Right Alt** together
3. You should see: `>>> HOTKEY PRESSED!`
4. Release the keys
5. You should see: `<<< HOTKEY RELEASED!`

## Expected Output

```
✓ Listener is active!

Now press and hold: Ctrl + Right Alt
(You should see messages when you press/release)

Press Ctrl+C to stop

>>> HOTKEY PRESSED! (count: 1)
    Keep holding the keys...
<<< HOTKEY RELEASED! (count: 1)
    Press again to test
```

## If It Works

If you see the press/release messages, the hotkey detection is working!

Then run the full app:
```bash
python3 zephyr_launcher.py
```

And press Ctrl + Right Alt - the popup should appear.

## If It Doesn't Work

If you don't see any messages when pressing Ctrl + Right Alt:

1. **Check your keyboard**: Make sure you have a Right Alt key (Alt Gr on some keyboards)
2. **Try different keys**: Edit `~/.config/zephyr/config.yaml` and try:
   - `ctrl+space` - Ctrl + Space
   - `ctrl+alt_l` - Ctrl + Left Alt
   - `backslash` - Just the backslash key
3. **Check permissions**: Make sure your user can access keyboard events

## Debug Mode

For more detailed logs:
```bash
python3 debug_zephyr.py
```

This will show exactly which keys are being detected.
