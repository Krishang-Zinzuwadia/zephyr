#!/usr/bin/env python3
"""
Example demonstrating the InputSimulator module

This example shows how to use the InputSimulator to type text
into the active application window.
"""

import sys
import time
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zephyr.input_simulator import InputSimulator, InputSimulationError


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main example function"""
    print("=" * 60)
    print("Zephyr Input Simulator Example")
    print("=" * 60)
    print()
    
    try:
        # Create input simulator (auto-detects X11 or Wayland)
        print("Creating input simulator...")
        simulator = InputSimulator.create(typing_speed=30)
        print(f"✓ Input simulator created")
        print()
        
        # Check focused window
        print("Checking focused window...")
        focused_window = simulator.get_focused_window()
        if focused_window:
            print(f"✓ Focused window: {focused_window}")
        else:
            print("✗ No focused window detected")
            return
        print()
        
        # Give user time to focus a text editor
        print("Please focus a text editor or input field...")
        print("Typing will begin in 5 seconds...")
        for i in range(5, 0, -1):
            print(f"  {i}...")
            time.sleep(1)
        print()
        
        # Example 1: Simple text typing
        print("Example 1: Simple text typing")
        print("-" * 40)
        text1 = "Hello from Zephyr!"
        print(f"Typing: '{text1}'")
        simulator.type_text(text1)
        print("✓ Text typed")
        time.sleep(2)
        print()
        
        # Example 2: Streaming mode with updates
        print("Example 2: Streaming mode with text updates")
        print("-" * 40)
        print("Starting streaming mode...")
        simulator.start_streaming_input()
        
        # Type initial text
        initial_text = "This is a test"
        print(f"Typing initial: '{initial_text}'")
        simulator.update_text(initial_text)
        time.sleep(1.5)
        
        # Update with corrected text
        updated_text = "This is a demonstration"
        print(f"Updating to: '{updated_text}'")
        simulator.update_text(updated_text)
        time.sleep(1.5)
        
        # Append more text
        append_text = " of streaming input."
        print(f"Appending: '{append_text}'")
        simulator.append_text(append_text)
        time.sleep(1)
        
        # Finalize
        simulator.finalize_input()
        print("✓ Streaming mode finalized")
        print()
        
        # Example 3: Special characters
        print("Example 3: Special characters and punctuation")
        print("-" * 40)
        text3 = "\nSpecial chars: !@#$%^&*()_+-=[]{}|;':\",./<>?"
        print(f"Typing: '{text3}'")
        simulator.type_text(text3)
        print("✓ Special characters typed")
        print()
        
        print("=" * 60)
        print("Example completed successfully!")
        print("=" * 60)
        
    except InputSimulationError as e:
        print(f"✗ Input simulation error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n✗ Interrupted by user")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        logger.exception("Unexpected error")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
