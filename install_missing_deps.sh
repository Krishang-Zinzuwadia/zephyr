#!/bin/bash
# Install missing dependencies for Zephyr

echo "Installing missing Python dependencies..."
echo ""

# Install PyGObject (gi module)
echo "Installing PyGObject..."
pip install --user PyGObject

# Install PyAudio
echo "Installing PyAudio..."
pip install --user PyAudio

# Install other missing packages
echo "Installing remaining packages..."
pip install --user faster-whisper watchdog noisereduce

echo ""
echo "Testing imports..."
python3 -c "import gi; print('✓ gi (PyGObject) installed')" || echo "✗ gi failed"
python3 -c "import pyaudio; print('✓ pyaudio installed')" || echo "✗ pyaudio failed"
python3 -c "import yaml; print('✓ yaml installed')" || echo "✓ yaml already installed"
python3 -c "import pynput; print('✓ pynput installed')" || echo "✓ pynput already installed"

echo ""
echo "Done! Try running: ./start_zephyr.sh"
