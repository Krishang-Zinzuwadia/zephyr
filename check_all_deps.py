#!/usr/bin/env python3
"""Check all Zephyr dependencies"""

import sys

deps = [
    ('gi', 'PyGObject'),
    ('sounddevice', 'sounddevice'),
    ('numpy', 'numpy'),
    ('faster_whisper', 'faster-whisper'),
    ('pynput', 'pynput'),
    ('yaml', 'PyYAML'),
    ('watchdog', 'watchdog'),
]

missing = []
installed = []

print("Checking dependencies...")
print()

for module, package in deps:
    try:
        __import__(module)
        print(f"✓ {package}")
        installed.append(package)
    except ImportError:
        print(f"✗ {package} - NOT INSTALLED")
        missing.append(package)

print()
print(f"Installed: {len(installed)}/{len(deps)}")
print(f"Missing: {len(missing)}/{len(deps)}")

if missing:
    print()
    print("To install missing dependencies:")
    print(f"  pip install {' '.join(missing)}")
    sys.exit(1)
else:
    print()
    print("All dependencies are installed!")
    sys.exit(0)
