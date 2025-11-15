#!/usr/bin/env python3
"""Check which dependencies are installed"""

import sys

deps = [
    ('gi', 'PyGObject'),
    ('yaml', 'PyYAML'),
    ('pynput', 'pynput'),
    ('pyaudio', 'PyAudio'),
    ('Xlib', 'python-xlib'),
    ('evdev', 'evdev'),
    ('watchdog', 'watchdog'),
]

print("Checking dependencies...")
print("=" * 50)

missing = []
for module, package in deps:
    try:
        __import__(module)
        print(f"✓ {package:20} - installed")
    except ImportError:
        print(f"✗ {package:20} - MISSING")
        missing.append(package)

print("=" * 50)

if missing:
    print(f"\nMissing {len(missing)} package(s):")
    for pkg in missing:
        print(f"  - {pkg}")
    print("\nInstall with:")
    print(f"  pip install --user {' '.join(missing)}")
    sys.exit(1)
else:
    print("\n✓ All dependencies installed!")
    sys.exit(0)
