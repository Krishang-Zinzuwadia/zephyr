#!/usr/bin/env python3
"""
Example usage of Zephyr configuration management

This demonstrates how to use the Config and ConfigManager classes.
"""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zephyr.config import Config, ConfigManager


def example_basic_usage():
    """Example: Basic configuration usage"""
    print("=" * 60)
    print("Example 1: Basic Configuration Usage")
    print("=" * 60)
    
    # Create a default configuration
    config = Config()
    
    print(f"Hotkey: {config.hotkey}")
    print(f"Model: {config.model}")
    print(f"Language: {config.language}")
    print(f"Sample Rate: {config.audio.sample_rate} Hz")
    print(f"Typing Speed: {config.typing.speed} chars/sec")
    print(f"UI Width: {config.ui.width}px")
    print(f"Min Press Duration: {config.advanced.min_press_duration}ms")
    print()


def example_custom_config():
    """Example: Creating custom configuration"""
    print("=" * 60)
    print("Example 2: Custom Configuration")
    print("=" * 60)
    
    # Create custom configuration
    config = Config(
        hotkey="ctrl+space",
        model="small",
        language="en"
    )
    
    # Modify nested settings
    config.audio.sample_rate = 22050
    config.typing.speed = 100
    config.ui.width = 500
    
    print(f"Custom Hotkey: {config.hotkey}")
    print(f"Custom Model: {config.model}")
    print(f"Custom Sample Rate: {config.audio.sample_rate} Hz")
    print()


def example_validation():
    """Example: Configuration validation"""
    print("=" * 60)
    print("Example 3: Configuration Validation")
    print("=" * 60)
    
    # Valid configuration
    config = Config()
    errors = config.validate()
    print(f"Valid config errors: {errors}")
    
    # Invalid configuration
    config.model = "invalid_model"
    config.audio.sample_rate = -1
    errors = config.validate()
    print(f"\nInvalid config errors:")
    for error in errors:
        print(f"  - {error}")
    print()


def example_config_manager():
    """Example: Using ConfigManager"""
    print("=" * 60)
    print("Example 4: ConfigManager Usage")
    print("=" * 60)
    
    # Use a temporary config path for this example
    config_path = "/tmp/zephyr_example_config.yaml"
    
    # Create manager and load config
    manager = ConfigManager(config_path)
    config = manager.load()
    
    print(f"Loaded config from: {config_path}")
    print(f"Hotkey: {config.hotkey}")
    
    # Modify and save
    config.hotkey = "f12"
    manager.save(config)
    print(f"Saved modified config with hotkey: {config.hotkey}")
    
    # Load again to verify
    manager2 = ConfigManager(config_path)
    config2 = manager2.load()
    print(f"Reloaded config, hotkey is: {config2.hotkey}")
    print()


def example_dict_conversion():
    """Example: Converting to/from dictionary"""
    print("=" * 60)
    print("Example 5: Dictionary Conversion")
    print("=" * 60)
    
    # Create config
    config = Config(hotkey="ctrl+alt+v", model="small")
    
    # Convert to dictionary
    config_dict = config.to_dict()
    print("Config as dictionary:")
    print(f"  hotkey: {config_dict['hotkey']}")
    print(f"  model: {config_dict['model']}")
    print(f"  audio.sample_rate: {config_dict['audio']['sample_rate']}")
    
    # Create from dictionary
    config2 = Config.from_dict(config_dict)
    print(f"\nRecreated config from dict:")
    print(f"  hotkey: {config2.hotkey}")
    print(f"  model: {config2.model}")
    print()


def example_file_watcher():
    """Example: Configuration file watching"""
    print("=" * 60)
    print("Example 6: File Watching")
    print("=" * 60)
    
    config_path = "/tmp/zephyr_watch_example.yaml"
    
    manager = ConfigManager(config_path)
    config = manager.load()
    
    # Set up file watcher
    def on_config_changed():
        print("Configuration file changed! Reloading...")
        new_config = manager.load()
        print(f"New hotkey: {new_config.hotkey}")
    
    manager.watch_for_changes(on_config_changed)
    print(f"Watching {config_path} for changes...")
    print("(In a real application, this would run in the background)")
    
    # Stop watching
    manager.stop_watching()
    print("Stopped watching")
    print()


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "Zephyr Configuration Examples" + " " * 18 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    example_basic_usage()
    example_custom_config()
    example_validation()
    example_config_manager()
    example_dict_conversion()
    example_file_watcher()
    
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
