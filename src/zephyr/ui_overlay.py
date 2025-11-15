"""
UI overlay for Zephyr voice-to-text application

Provides visual feedback during voice input with:
- Animated waveform visualization
- Live transcription display
- Smooth animations and transitions
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk, GLib, Pango
import cairo
import math
import logging
from typing import Optional
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class WaveformBar:
    """Represents a single bar in the waveform visualization"""
    height: float = 0.0
    target_height: float = 0.0
    velocity: float = 0.0


class UIOverlay:
    """
    GTK4 overlay window for visual feedback during voice input
    
    Features:
    - Borderless, always-on-top window
    - Rounded corners with semi-transparent background
    - Animated waveform visualization
    - Live transcription display with smooth updates
    - Fade-in/fade-out animations
    """
    
    def __init__(self, width: int = 400, height: int = 120, 
                 border_radius: int = 16, background_opacity: float = 0.95,
                 animation_speed: float = 1.0):
        """
        Initialize UI overlay (lazy - window created on first show)
        
        Args:
            width: Window width in pixels
            height: Initial window height in pixels
            border_radius: Corner radius in pixels
            background_opacity: Background opacity (0.0 to 1.0)
            animation_speed: Animation speed multiplier
        """
        self.width = width
        self.min_height = height
        self.current_height = height
        self.border_radius = border_radius
        self.background_opacity = background_opacity
        self.animation_speed = animation_speed
        
        # Window and widgets (created lazily)
        self.window: Optional[Gtk.Window] = None
        self.drawing_area: Optional[Gtk.DrawingArea] = None
        self.text_label: Optional[Gtk.Label] = None
        self.error_label: Optional[Gtk.Label] = None
        self.main_box: Optional[Gtk.Box] = None
        
        # Animation state
        self.opacity = 0.0
        self.target_opacity = 0.0
        self.is_visible = False
        self.animation_timer: Optional[int] = None
        self.waveform_timer: Optional[int] = None
        
        # Waveform state
        self.num_bars = 20
        self.bars = [WaveformBar() for _ in range(self.num_bars)]
        self.audio_level = 0.0
        
        # Transcription state
        self.current_text = ""
        self.is_final_text = False
        self.text_opacity = 0.0
        self.target_text_opacity = 0.0
        
        # Error state
        self.is_error = False
        self.error_message = ""
        
        # Checkmark animation
        self.show_checkmark = False
        self.checkmark_progress = 0.0
        
        logger.debug("UIOverlay initialized (window not created yet)")
    
    def _create_window(self) -> None:
        """Create the GTK window and widgets (lazy initialization)"""
        if self.window is not None:
            return
        
        logger.debug("Creating GTK overlay window")
        
        # Create window
        self.window = Gtk.Window()
        self.window.set_decorated(False)
        self.window.set_resizable(False)
        self.window.set_default_size(self.width, self.current_height)
        
        # Make window always on top and skip taskbar
        self.window.set_modal(False)
        
        # Try to position in lower right
        # Note: On Wayland, window positioning is restricted
        # We can try using window hints
        try:
            # Set window to appear in bottom-right corner
            self.window.set_gravity(Gdk.Gravity.SOUTH_EAST)
        except Exception as e:
            logger.debug(f"Could not set window gravity: {e}")
        
        # Set up CSS for styling
        css_provider = Gtk.CssProvider()
        css = f"""
        window {{
            background-color: rgba(30, 30, 30, {self.background_opacity});
            border-radius: {self.border_radius}px;
        }}
        
        .transcription-text {{
            color: rgba(255, 255, 255, 0.9);
            font-family: monospace;
            font-size: 14px;
            padding: 8px 16px;
        }}
        
        .transcription-partial {{
            color: rgba(255, 255, 255, 0.6);
        }}
        
        .error-text {{
            color: rgba(255, 100, 100, 1.0);
            font-family: sans-serif;
            font-size: 13px;
            padding: 8px 16px;
        }}
        """
        css_provider.load_from_data(css.encode())
        
        # Apply CSS to display
        display = Gdk.Display.get_default()
        Gtk.StyleContext.add_provider_for_display(
            display,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        # Create main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window.set_child(self.main_box)
        
        # Create drawing area for waveform (40px height)
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_size_request(self.width, 40)
        self.drawing_area.set_draw_func(self._draw_waveform)
        self.main_box.append(self.drawing_area)
        
        # Create text label for transcription
        self.text_label = Gtk.Label()
        self.text_label.set_wrap(True)
        self.text_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.text_label.set_max_width_chars(50)
        self.text_label.set_xalign(0.0)
        self.text_label.add_css_class("transcription-text")
        self.main_box.append(self.text_label)
        
        # Create error label (hidden by default)
        self.error_label = Gtk.Label()
        self.error_label.set_wrap(True)
        self.error_label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.error_label.set_max_width_chars(50)
        self.error_label.set_xalign(0.0)
        self.error_label.add_css_class("error-text")
        self.error_label.set_visible(False)
        self.main_box.append(self.error_label)
        
        # Set initial opacity to 0
        self.window.set_opacity(0.0)
        
        # Center window on screen
        self._center_window()
        
        logger.info("GTK overlay window created")
    
    def _center_window(self) -> None:
        """Center the window on the screen"""
        if self.window is None:
            return
        
        # Get display and monitor geometry
        display = Gdk.Display.get_default()
        if display is None:
            logger.warning("Could not get default display")
            return
        
        # Get the monitor where the mouse is
        seat = display.get_default_seat()
        if seat is None:
            logger.warning("Could not get default seat")
            return
        
        pointer = seat.get_pointer()
        if pointer is None:
            logger.warning("Could not get pointer device")
            return
        
        surface = self.window.get_surface()
        if surface is None:
            # Window not realized yet, we'll center on first show
            return
        
        monitor = display.get_monitor_at_surface(surface)
        if monitor is None:
            logger.warning("Could not get monitor")
            return
        
        geometry = monitor.get_geometry()
        
        # Calculate position: lower right area (5/6 down the screen, right side)
        # Position at 83% down (5/6) and with some margin from right edge
        margin = 20  # pixels from edge
        x = geometry.x + geometry.width - self.width - margin
        y = geometry.y + int(geometry.height * 0.83) - self.current_height // 2
        
        # GTK4 doesn't support set_position directly
        # We'll use CSS to position it
        # For now, log the desired position
        logger.debug(f"Window should be at ({x}, {y}) - lower right area")
    
    def show_recording(self) -> None:
        """
        Show the overlay with fade-in animation
        
        Requirements: 6.1, 6.4
        """
        logger.debug("Showing recording overlay")
        
        # Create window if not exists
        self._create_window()
        
        # Reset state
        self.is_error = False
        self.show_checkmark = False
        self.checkmark_progress = 0.0
        self.current_text = ""
        self.is_final_text = False
        self.text_opacity = 0.0
        self.target_text_opacity = 0.0
        
        # Hide error label
        if self.error_label:
            self.error_label.set_visible(False)
        
        # Show window
        if self.window:
            self.window.present()
            self.is_visible = True
        
        # Start fade-in animation (200ms)
        self.target_opacity = 1.0
        self._start_fade_animation()
        
        # Set initial audio level for testing
        self.audio_level = 0.5
        
        # Start waveform animation
        self._start_waveform_animation()
        
        # Show initial text
        if self.text_label:
            self.text_label.set_text("Recording...")
            self.text_label.set_visible(True)
        
        logger.info("UI overlay shown with recording state")
    
    def hide(self) -> None:
        """
        Hide the overlay with fade-out animation
        
        Destroys window after fade-out to minimize resource usage
        
        Requirements: 6.4, 9.2, 9.4
        """
        logger.debug("Hiding overlay")
        
        if not self.is_visible or self.window is None:
            return
        
        # Start fade-out animation (300ms)
        self.target_opacity = 0.0
        self._start_fade_animation()
        
        # Stop waveform animation
        self._stop_waveform_animation()
        
        # Schedule window destruction after fade-out completes
        # This releases all GTK resources when overlay is not visible
        GLib.timeout_add(350, self._destroy_window_after_hide)
    
    def show_completion(self) -> None:
        """
        Show completion state (checkmark) but DON'T auto-hide
        Keep the UI visible until user presses hotkey again
        """
        logger.info("Showing completion - UI stays visible")
        
        # Show checkmark animation
        self.show_checkmark = True
        self.checkmark_progress = 0.0
        
        # Stop waveform animation
        self._stop_waveform_animation()
        
        # DON'T call hide() - let the UI stay visible
        # It will be hidden when user presses hotkey again
    
    def update_audio_level(self, level: float) -> None:
        """
        Update waveform visualization based on audio level
        
        Args:
            level: Audio level (0.0 to 1.0)
        
        Requirements: 6.2
        """
        self.audio_level = max(0.0, min(1.0, level))
    
    def update_transcription(self, text: str, is_final: bool = False) -> None:
        """
        Update the displayed transcription text
        
        Args:
            text: Transcription text to display
            is_final: Whether this is the final transcription
        
        Requirements: 8.1, 8.5
        """
        if self.text_label is None:
            return
        
        logger.debug(f"Updating transcription: '{text}' (final={is_final})")
        
        # Update text
        self.current_text = text
        self.is_final_text = is_final
        self.text_label.set_text(text)
        
        # Update styling based on final/partial
        if is_final:
            self.text_label.remove_css_class("transcription-partial")
            self.target_text_opacity = 1.0
        else:
            self.text_label.add_css_class("transcription-partial")
            self.target_text_opacity = 0.8
        
        # Adjust window height for text wrapping
        self._adjust_window_height()
        
        # Fade in text
        if self.text_opacity < self.target_text_opacity:
            self._animate_text_opacity()
    
    def show_error(self, message: str) -> None:
        """
        Display an error message
        
        Args:
            message: Error message to display
        
        Requirements: 6.1
        """
        logger.debug(f"Showing error: {message}")
        
        # Create window if not exists
        self._create_window()
        
        self.is_error = True
        self.error_message = message
        
        if self.error_label:
            self.error_label.set_text(message)
            self.error_label.set_visible(True)
        
        if self.text_label:
            self.text_label.set_visible(False)
        
        # Show window if not visible
        if not self.is_visible and self.window:
            self.window.present()
            self.is_visible = True
            self.target_opacity = 1.0
            self._start_fade_animation()
    
    def show_completion(self) -> None:
        """
        Show completion animation (checkmark) then hide
        
        Requirements: 6.4
        """
        logger.debug("Showing completion animation")
        
        self.show_checkmark = True
        self.checkmark_progress = 0.0
        
        # Animate checkmark
        def animate_checkmark():
            self.checkmark_progress += 0.1
            if self.drawing_area:
                self.drawing_area.queue_draw()
            
            if self.checkmark_progress >= 1.0:
                # Checkmark complete, hide after brief delay
                GLib.timeout_add(300, self.hide)
                return False
            return True
        
        GLib.timeout_add(16, animate_checkmark)  # ~60fps
    
    def _adjust_window_height(self) -> None:
        """Adjust window height based on text content"""
        if self.text_label is None or self.window is None:
            return
        
        # Get natural height of text label
        nat_size = self.text_label.get_preferred_size()
        text_height = nat_size.natural_size.height if nat_size.natural_size else 0
        
        # Calculate new height (waveform + text + padding)
        new_height = max(self.min_height, 40 + text_height + 16)
        new_height = min(new_height, 300)  # Max height
        
        if new_height != self.current_height:
            self.current_height = new_height
            self.window.set_default_size(self.width, self.current_height)
            self._center_window()
    
    def _start_fade_animation(self) -> None:
        """Start opacity fade animation"""
        if self.animation_timer is not None:
            GLib.source_remove(self.animation_timer)
        
        def animate():
            if self.window is None:
                return False
            
            # Calculate animation speed based on direction
            if self.target_opacity > self.opacity:
                # Fade in: 200ms
                speed = (1.0 / 200.0) * 16 * self.animation_speed
            else:
                # Fade out: 300ms
                speed = (1.0 / 300.0) * 16 * self.animation_speed
            
            # Update opacity
            diff = self.target_opacity - self.opacity
            if abs(diff) < 0.01:
                self.opacity = self.target_opacity
                self.window.set_opacity(self.opacity)
                
                # If faded out completely, hide window
                if self.opacity == 0.0:
                    self.window.set_visible(False)
                    self.is_visible = False
                
                return False
            
            self.opacity += diff * speed
            self.window.set_opacity(self.opacity)
            return True
        
        self.animation_timer = GLib.timeout_add(16, animate)  # ~60fps
    
    def _animate_text_opacity(self) -> None:
        """Animate text opacity transition"""
        def animate():
            if self.text_label is None:
                return False
            
            diff = self.target_text_opacity - self.text_opacity
            if abs(diff) < 0.01:
                self.text_opacity = self.target_text_opacity
                return False
            
            self.text_opacity += diff * 0.2
            # Update label opacity via CSS would require dynamic CSS updates
            # For simplicity, we rely on the CSS classes
            return True
        
        GLib.timeout_add(16, animate)
    
    def _start_waveform_animation(self) -> None:
        """Start waveform animation timer"""
        if self.waveform_timer is not None:
            return
        
        def animate():
            if not self.is_visible:
                return False
            
            # Update bar heights based on audio level
            for i, bar in enumerate(self.bars):
                # Create wave pattern with some randomness
                phase = (i / self.num_bars) * math.pi * 2
                base_height = math.sin(phase + GLib.get_monotonic_time() / 150000.0) * 0.4 + 0.6
                
                # Modulate by audio level (more responsive)
                bar.target_height = base_height * max(0.3, self.audio_level)
                
                # FASTER animation with spring physics for better responsiveness
                diff = bar.target_height - bar.height
                bar.velocity += diff * 0.5  # Increased from 0.3
                bar.velocity *= 0.8  # Increased damping from 0.7
                bar.height += bar.velocity
                
                # Clamp
                bar.height = max(0.0, min(1.0, bar.height))
            
            # Redraw
            if self.drawing_area:
                self.drawing_area.queue_draw()
            
            return True
        
        self.waveform_timer = GLib.timeout_add(16, animate)  # ~60fps
    
    def _stop_waveform_animation(self) -> None:
        """Stop waveform animation timer"""
        if self.waveform_timer is not None:
            GLib.source_remove(self.waveform_timer)
            self.waveform_timer = None
    
    def _draw_waveform(self, area: Gtk.DrawingArea, cr: cairo.Context, 
                       width: int, height: int) -> None:
        """
        Draw waveform visualization using Cairo
        
        Args:
            area: Drawing area widget
            cr: Cairo context
            width: Drawing width
            height: Drawing height
        
        Requirements: 6.2
        """
        # Clear background
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        
        if self.show_checkmark:
            # Draw checkmark animation
            self._draw_checkmark(cr, width, height)
            return
        
        # Draw waveform bars
        bar_width = width / self.num_bars
        bar_spacing = bar_width * 0.2
        bar_width = bar_width * 0.8
        
        for i, bar in enumerate(self.bars):
            x = i * (bar_width + bar_spacing) + bar_spacing / 2
            bar_height = bar.height * height * 0.8
            y = (height - bar_height) / 2
            
            # Color gradient based on position
            hue = i / self.num_bars
            if self.is_error:
                # Red for errors
                cr.set_source_rgba(1.0, 0.4, 0.4, 0.9)
            else:
                # Blue-green gradient
                cr.set_source_rgba(0.3 + hue * 0.3, 0.6 + hue * 0.2, 0.9, 0.9)
            
            # Draw rounded rectangle
            self._draw_rounded_rect(cr, x, y, bar_width, bar_height, bar_width / 2)
            cr.fill()
    
    def _draw_checkmark(self, cr: cairo.Context, width: int, height: int) -> None:
        """Draw animated checkmark"""
        # Center of drawing area
        cx = width / 2
        cy = height / 2
        
        # Checkmark size
        size = min(width, height) * 0.5
        
        # Draw circle background
        cr.set_source_rgba(0.3, 0.8, 0.3, 0.9)
        cr.arc(cx, cy, size * 0.6, 0, 2 * math.pi)
        cr.fill()
        
        # Draw checkmark path
        progress = self.checkmark_progress
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.9)
        cr.set_line_width(size * 0.15)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)
        
        # Checkmark coordinates
        x1, y1 = cx - size * 0.3, cy
        x2, y2 = cx - size * 0.1, cy + size * 0.25
        x3, y3 = cx + size * 0.35, cy - size * 0.3
        
        if progress < 0.5:
            # First part of checkmark
            t = progress * 2
            cr.move_to(x1, y1)
            cr.line_to(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)
        else:
            # Second part of checkmark
            t = (progress - 0.5) * 2
            cr.move_to(x1, y1)
            cr.line_to(x2, y2)
            cr.line_to(x2 + (x3 - x2) * t, y2 + (y3 - y2) * t)
        
        cr.stroke()
    
    def _draw_rounded_rect(self, cr: cairo.Context, x: float, y: float, 
                          width: float, height: float, radius: float) -> None:
        """Draw a rounded rectangle"""
        if height < radius * 2:
            radius = height / 2
        
        cr.new_sub_path()
        cr.arc(x + width - radius, y + radius, radius, -math.pi / 2, 0)
        cr.arc(x + width - radius, y + height - radius, radius, 0, math.pi / 2)
        cr.arc(x + radius, y + height - radius, radius, math.pi / 2, math.pi)
        cr.arc(x + radius, y + radius, radius, math.pi, 3 * math.pi / 2)
        cr.close_path()
    
    def _destroy_window_after_hide(self) -> bool:
        """
        Destroy window after fade-out to free resources
        
        Returns:
            False to stop the timer
        """
        if not self.is_visible and self.window is not None:
            logger.debug("Destroying window to free resources")
            self._cleanup_window()
        return False
    
    def _cleanup_window(self) -> None:
        """Clean up window and widget resources"""
        # Stop animations
        if self.animation_timer is not None:
            GLib.source_remove(self.animation_timer)
            self.animation_timer = None
        
        if self.waveform_timer is not None:
            GLib.source_remove(self.waveform_timer)
            self.waveform_timer = None
        
        # Destroy window and clear references
        if self.window is not None:
            self.window.close()
            self.window = None
            self.drawing_area = None
            self.text_label = None
            self.error_label = None
            self.main_box = None
            logger.debug("Window resources freed")
    
    def destroy(self) -> None:
        """Clean up resources and destroy window"""
        logger.debug("Destroying UI overlay")
        
        self.is_visible = False
        self._cleanup_window()
        
        logger.info("UI overlay destroyed")
