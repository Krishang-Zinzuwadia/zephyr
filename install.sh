#!/bin/bash
# Zephyr Installation Script
# Installs all dependencies and sets up the application

set -e

echo "========================================"
echo "Zephyr Voice Input - Installation"
echo "========================================"
echo ""

# Detect package manager
if command -v pacman &> /dev/null; then
    PKG_MANAGER="pacman"
    echo "✓ Detected Arch-based system (pacman)"
elif command -v apt &> /dev/null; then
    PKG_MANAGER="apt"
    echo "✓ Detected Debian-based system (apt)"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
    echo "✓ Detected Fedora-based system (dnf)"
else
    PKG_MANAGER="unknown"
    echo "⚠ Unknown package manager - you'll need to install system dependencies manually"
fi

echo ""
echo "Step 1: Installing system dependencies..."
echo "=========================================="

if [ "$PKG_MANAGER" = "pacman" ]; then
    echo "Installing with pacman..."
    sudo pacman -S --needed --noconfirm \
        python \
        python-pip \
        portaudio \
        gtk4 \
        python-gobject \
        python-yaml \
        python-numpy \
        python-pyaudio \
        base-devel || echo "Some packages may already be installed"
        
elif [ "$PKG_MANAGER" = "apt" ]; then
    echo "Installing with apt..."
    sudo apt update
    sudo apt install -y \
        python3 \
        python3-pip \
        portaudio19-dev \
        libgtk-4-dev \
        python3-gi \
        python3-yaml \
        python3-numpy \
        python3-pyaudio \
        build-essential || echo "Some packages may already be installed"
        
elif [ "$PKG_MANAGER" = "dnf" ]; then
    echo "Installing with dnf..."
    sudo dnf install -y \
        python3 \
        python3-pip \
        portaudio-devel \
        gtk4-devel \
        python3-gobject \
        python3-pyyaml \
        python3-numpy \
        python3-pyaudio \
        gcc || echo "Some packages may already be installed"
else
    echo "⚠ Please install these manually:"
    echo "  - Python 3.11+"
    echo "  - pip"
    echo "  - PortAudio"
    echo "  - GTK4"
    echo "  - Python GObject bindings"
fi

echo ""
echo "Step 2: Installing Python dependencies..."
echo "=========================================="

# Upgrade pip
python3 -m pip install --upgrade pip

# Install Python packages
echo "Installing from requirements.txt..."
python3 -m pip install -r requirements.txt --user

echo ""
echo "Step 3: Setting up configuration..."
echo "=========================================="

# Create config directory
mkdir -p ~/.config/zephyr
mkdir -p ~/.cache/zephyr/models
mkdir -p ~/.local/share/zephyr/logs

# Copy default config if it doesn't exist
if [ ! -f ~/.config/zephyr/config.yaml ]; then
    if [ -f config/default.yaml ]; then
        cp config/default.yaml ~/.config/zephyr/config.yaml
        echo "✓ Created default configuration at ~/.config/zephyr/config.yaml"
    else
        echo "⚠ Default config not found, will be created on first run"
    fi
else
    echo "✓ Configuration already exists at ~/.config/zephyr/config.yaml"
fi

echo ""
echo "Step 4: Testing installation..."
echo "=========================================="

# Test imports
echo "Testing Python imports..."
python3 -c "import sys; sys.path.insert(0, 'src'); from zephyr import __version__; print(f'✓ Zephyr version {__version__} imported successfully')" || {
    echo "✗ Import test failed"
    exit 1
}

echo ""
echo "========================================"
echo "✓ Installation Complete!"
echo "========================================"
echo ""
echo "To start using Zephyr:"
echo ""
echo "  1. Start the daemon:"
echo "     python3 -m src.zephyr"
echo ""
echo "  2. Press and hold the backslash (\\) key"
echo "  3. Speak your text"
echo "  4. Release the key"
echo ""
echo "Configuration: ~/.config/zephyr/config.yaml"
echo "Logs: ~/.local/share/zephyr/logs/"
echo ""
echo "Note: The Whisper model will be downloaded automatically"
echo "on first use (this may take a few minutes)."
echo ""
