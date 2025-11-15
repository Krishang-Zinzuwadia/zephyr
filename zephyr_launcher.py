#!/usr/bin/env python3
"""
Zephyr Voice Input Launcher
Simple launcher script for Zephyr
"""
import sys
import os
import signal
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import GTK before anything else
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

def main():
    print("=" * 60)
    print("Zephyr Voice Input")
    print("=" * 60)
    print()
    
    config_path = Path.home() / ".config" / "zephyr" / "config.yaml"
    
    if not config_path.exists():
        print("Error: Configuration file not found")
        print(f"Expected: {config_path}")
        print()
        print("Please create a configuration file first.")
        return 1
    
    print(f"Config: {config_path}")
    print()
    
    # Create GTK application
    app = Gtk.Application(application_id="com.zephyr.voiceinput")
    
    # Global daemon instance
    daemon = None
    
    def on_activate(application):
        """GTK application activation callback"""
        nonlocal daemon
        
        try:
            from zephyr.daemon import ZephyrDaemon
            
            print("Starting daemon...")
            daemon = ZephyrDaemon(str(config_path))
            daemon.start()
            
            print()
            print("✓ Zephyr is running!")
            print()
            print("Hotkey: Press and hold ` (backtick) to record")
            print("        Note: Backticks will be typed")
            print("Press Ctrl+C to stop")
            print()
            
            # Keep the application running
            application.hold()
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
            application.quit()
            sys.exit(1)
    
    def on_shutdown(application):
        """GTK application shutdown callback"""
        nonlocal daemon
        
        print("\nShutting down...")
        
        if daemon:
            try:
                daemon.stop()
            except Exception as e:
                print(f"Error during shutdown: {e}")
        
        print("Goodbye!")
        
        # Release the application hold
        try:
            application.release()
        except Exception:
            pass
    
    # Connect signals
    app.connect("activate", on_activate)
    app.connect("shutdown", on_shutdown)
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        if daemon:
            daemon.stop()
        app.quit()
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run GTK application
    try:
        exit_code = app.run(None)
        return exit_code
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received")
        if daemon:
            daemon.stop()
        return 0
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        if daemon:
            daemon.stop()
        return 1

if __name__ == "__main__":
    sys.exit(main())
