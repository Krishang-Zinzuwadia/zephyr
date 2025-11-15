#!/bin/bash
# Install Python dependencies only (no sudo required)

set -e

echo "========================================"
echo "Installing Python Dependencies"
echo "========================================"
echo ""

# Upgrade pip
echo "Upgrading pip..."
python3 -m pip install --upgrade pip --user

echo ""
echo "Installing Python packages..."
echo "========================================"

# Install each package individually to see progress
packages=(
    "PyYAML>=6.0"
    "pynput>=1.7.6"
    "faster-whisper>=0.10.0"
    "python-xlib>=0.33"
    "evdev>=1.6.1"
    "watchdog>=3.0.0"
    "noisereduce>=3.0.0"
)

for pkg in "${packages[@]}"; do
    echo ""
    echo "Installing $pkg..."
    python3 -m pip install "$pkg" --user || echo "⚠ Failed to install $pkg (may need system packages)"
done

echo ""
echo "========================================"
echo "Setting up directories..."
echo "========================================"

mkdir -p ~/.config/zephyr
mkdir -p ~/.cache/zephyr/models
mkdir -p ~/.local/share/zephyr/logs

echo "✓ Created config directories"

echo ""
echo "========================================"
echo "Testing installation..."
echo "========================================"

python3 -c "import sys; sys.path.insert(0, 'src'); from zephyr import __version__; print(f'✓ Zephyr {__version__} ready!')"

echo ""
echo "========================================"
echo "✓ Python dependencies installed!"
echo "========================================"
echo ""
echo "To start Zephyr:"
echo "  python3 -m src.zephyr"
echo ""
