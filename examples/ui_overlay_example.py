#!/usr/bin/env python3
"""
Example demonstrating the UI overlay functionality

This example shows:
- Creating and showing the overlay
- Animating the waveform with simulated audio levels
- Displaying live transcription updates
- Error display
- Completion animation
"""

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib
import sys
import math
import time

# Add src to path for imports
sys.path.insert(0, 'src')

from zephyr.ui_overlay import UIOverlay


class UIOverlayDemo:
    """Demo application for UI overlay"""
    
    def __init__(self):
        self.overlay = UIOverlay(
            width=400,
            height=120,
            border_radius=16,
            background_opacity=0.95,
            animation_speed=1.0
        )
        self.demo_step = 0
        self.time = 0.0
    
    def run_demo(self):
        """Run the demo sequence"""
        print("Starting UI overlay demo...")
        print("Step 1: Show recording with animated waveform")
        
        # Step 1: Show recording
        self.overlay.show_recording()
        
        # Animate waveform
        def update_waveform():
            self.time += 0.05
            # Simulate audio level with sine wave
            level = (math.sin(self.time) + 1) / 2 * 0.8 + 0.2
            self.overlay.update_audio_level(level)
            return True
        
        GLib.timeout_add(50, update_waveform)
        
        # Step 2: Show partial transcription after 2 seconds
        def show_partial():
            print("Step 2: Show partial transcription")
            self.overlay.update_transcription("Hello, this is a test", is_final=False)
            return False
        
        GLib.timeout_add(2000, show_partial)
        
        # Step 3: Update transcription after 3 seconds
        def update_transcription():
            print("Step 3: Update transcription (user changed their mind)")
            self.overlay.update_transcription("Hello, this is a demonstration of the overlay", is_final=False)
            return False
        
        GLib.timeout_add(3000, update_transcription)
        
        # Step 4: Show final transcription after 5 seconds
        def show_final():
            print("Step 4: Show final transcription")
            self.overlay.update_transcription(
                "Hello, this is a demonstration of the overlay system with live updates",
                is_final=True
            )
            return False
        
        GLib.timeout_add(5000, show_final)
        
        # Step 5: Show completion after 7 seconds
        def show_completion():
            print("Step 5: Show completion animation")
            self.overlay.show_completion()
            return False
        
        GLib.timeout_add(7000, show_completion)
        
        # Step 6: Show error after 9 seconds
        def show_error():
            print("Step 6: Show error message")
            self.overlay.show_error("Microphone not found")
            return False
        
        GLib.timeout_add(9000, show_error)
        
        # Step 7: Hide after 11 seconds
        def hide_overlay():
            print("Step 7: Hide overlay")
            self.overlay.hide()
            return False
        
        GLib.timeout_add(11000, hide_overlay)
        
        # Exit after 12 seconds
        def exit_demo():
            print("Demo complete!")
            self.overlay.destroy()
            app.quit()
            return False
        
        GLib.timeout_add(12000, exit_demo)


def on_activate(app):
    """Application activation callback"""
    demo = UIOverlayDemo()
    demo.run_demo()


if __name__ == "__main__":
    app = Gtk.Application(application_id="com.zephyr.overlay_demo")
    app.connect("activate", on_activate)
    
    print("=" * 60)
    print("Zephyr UI Overlay Demo")
    print("=" * 60)
    print("\nThis demo will show:")
    print("1. Recording overlay with animated waveform")
    print("2. Partial transcription display")
    print("3. Transcription updates (text replacement)")
    print("4. Final transcription")
    print("5. Completion animation")
    print("6. Error display")
    print("7. Hide animation")
    print("\nWatch the overlay window that appears on screen!")
    print("=" * 60)
    print()
    
    app.run(None)
