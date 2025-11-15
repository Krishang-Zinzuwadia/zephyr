#!/bin/bash
# Quick start script for Zephyr

echo "Starting Zephyr Voice Input..."
echo ""
echo "Hotkey: Press and hold Ctrl + Right Alt to activate voice input"
echo "Press Ctrl+C to stop"
echo ""

# Set Python path and run with system Python
export PYTHONPATH="$PWD/src:$PYTHONPATH"
/usr/bin/python3 -m zephyr "$@"
