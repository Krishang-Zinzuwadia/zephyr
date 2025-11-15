#!/usr/bin/env python3
"""Optimize Zephyr for better accuracy"""
from pathlib import Path
import yaml

config_path = Path.home() / ".config" / "zephyr" / "config.yaml"

with open(config_path) as f:
    config = yaml.safe_load(f)

# Better accuracy settings
config['model'] = 'base'  # Better than tiny
config['language'] = 'en'  # Specify English for better accuracy
config['advanced']['vad_enabled'] = False
config['advanced']['beam_size'] = 5  # Better accuracy
config['advanced']['best_of'] = 5  # Consider more candidates
config['advanced']['temperature'] = 0.0  # Deterministic

with open(config_path, 'w') as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)

print("✓ Config optimized for accuracy:")
print(f"  - Model: base (better accuracy)")
print(f"  - Language: en (English)")
print(f"  - Beam size: 5")
print(f"  - Best of: 5")
