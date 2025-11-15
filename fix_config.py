#!/usr/bin/env python3
"""Fix Zephyr config for reliability"""
from pathlib import Path
import yaml

config_path = Path.home() / ".config" / "zephyr" / "config.yaml"

# Load config
with open(config_path) as f:
    config = yaml.safe_load(f)

# Make it more reliable
config['advanced']['vad_enabled'] = False  # Disable VAD (needs onnxruntime)
config['advanced']['beam_size'] = 1  # Faster, more predictable
config['advanced']['temperature'] = 0.0  # Deterministic
config['model'] = 'tiny'  # Fastest model for testing

# Save
with open(config_path, 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)

print("✓ Config updated for reliability:")
print(f"  - Model: {config['model']} (fastest)")
print(f"  - VAD: {config['advanced']['vad_enabled']} (disabled)")
print(f"  - Beam size: {config['advanced']['beam_size']} (fastest)")
print("\nRestart Zephyr and try again!")
