"""
Main entry point for Zephyr application
"""

import sys
import os
import argparse
import signal
import logging
from pathlib import Path

# Import GTK before anything else to ensure proper initialization
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

from .daemon import ZephyrDaemon


# Set up basic logging for CLI
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def stop_daemon():
    """
    Stop a running Zephyr daemon
    
    Attempts to find and terminate the daemon process
    """
    import subprocess
    
    try:
        # Try to find the daemon process
        result = subprocess.run(
            ["pgrep", "-f", "zephyr.*daemon"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    logger.info(f"Stopping Zephyr daemon (PID: {pid})")
                    subprocess.run(["kill", "-TERM", pid])
            logger.info("Zephyr daemon stopped")
            return True
        else:
            logger.warning("No running Zephyr daemon found")
            return False
    
    except Exception as e:
        logger.error(f"Failed to stop daemon: {e}")
        return False


def main():
    """Main entry point for Zephyr CLI"""
    parser = argparse.ArgumentParser(
        description="Zephyr - Voice-to-text input for Linux",
        epilog="Press and hold Ctrl + Right Alt to activate voice input"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as background daemon (default behavior)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to custom configuration file"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Zephyr {__import__('zephyr').__version__}"
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop running daemon"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Handle --stop flag
    if args.stop:
        logger.info("Stopping Zephyr daemon...")
        success = stop_daemon()
        sys.exit(0 if success else 1)
    
    # Enable debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Determine config path
    if args.config:
        config_path = Path(args.config)
    else:
        config_path = Path.home() / ".config" / "zephyr" / "config.yaml"
    
    logger.info(f"Starting Zephyr with config: {config_path}")
    
    # Initialize GTK application
    app = Gtk.Application(application_id="com.zephyr.voiceinput")
    
    # Global daemon instance
    daemon = None
    
    def on_activate(application):
        """GTK application activation callback"""
        nonlocal daemon
        
        try:
            # Create and start daemon
            daemon = ZephyrDaemon(str(config_path))
            daemon.start()
            
            logger.info("Zephyr daemon started successfully")
            logger.info("Press and hold Ctrl + Right Alt to activate voice input")
            logger.info("Press Ctrl+C to stop")
            
        except Exception as e:
            logger.error(f"Failed to start Zephyr daemon: {e}", exc_info=True)
            application.quit()
            sys.exit(1)
    
    def on_shutdown(application):
        """GTK application shutdown callback"""
        nonlocal daemon
        
        logger.info("Shutting down Zephyr...")
        
        if daemon:
            try:
                daemon.stop()
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
    
    # Connect signals
    app.connect("activate", on_activate)
    app.connect("shutdown", on_shutdown)
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        if daemon:
            daemon.stop()
        app.quit()
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run GTK application
    try:
        exit_code = app.run(None)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\nKeyboard interrupt received, shutting down...")
        if daemon:
            daemon.stop()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        if daemon:
            daemon.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
