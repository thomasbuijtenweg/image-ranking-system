"""
Modern progress tracker for the Image Ranking System.

This module handles modern progress windows and loading indicators
with sleek styling and enhanced user experience.
"""

import tkinter as tk
from tkinter import ttk

from config import Colors, Fonts, Styling
from ui.components.ui_builder import ModernFrame, ModernLabel, ModernButton


class ModernProgressBar(ttk.Progressbar):
    """Custom progress bar with modern styling."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Apply modern styling through ttk.Style
        style = ttk.Style()
        style.configure("Modern.TProgressbar",
                       background=Colors.PURPLE_PRIMARY,
                       troughcolor=Colors.BG_TERTIARY,
                       borderwidth=0,
                       lightcolor=Colors.PURPLE_PRIMARY,
                       darkcolor=Colors.PURPLE_PRIMARY,
                       relief='flat')
        
        self.configure(style="Modern.TProgressbar")


class ModernProgressWindow:
    """Modern progress window with sleek design and animations."""
    
    def __init__(self, parent, title, total_items, cancelable=True):
        self.parent = parent
        self.title = title
        self.total_items = total_items
        self.cancelable = cancelable
        
        self.window = None
        self.progress_var = None
        self.progress_label_var = None
        self.progress_bar = None
        self.cancel_callback = None
        
        # Animation state
        self.animation_step = 0
        self.animation_timer = None
        
        self._create_window()
    
    def _create_window(self):
        """Create the modern progress window."""
        # Create window
        self.window = tk.Toplevel(self.parent)
        self.window.title(self.title)
        self.window.geometry("500x200")
        self.window.configure(bg=Colors.BG_PRIMARY)
        self.window.resizable(False, False)
        
        # Center window
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Calculate center position
        self.window.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + (self.parent.winfo_width() // 2) - 250,
            self.parent.winfo_rooty() + (self.parent.winfo_height() // 2) - 100
        ))
        
        # Main container
        main_container = ModernFrame(self.window, style='card')
        main_container.pack(fill=tk.BOTH, expand=True, padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        # Header
        self._create_header(main_container)
        
        # Progress section
        self._create_progress_section(main_container)
        
        # Actions
        if self.cancelable:
            self._create_action_buttons(main_container)
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._handle_close)
    
    def _create_header(self, parent):
        """Create modern header with icon and title."""
        header_frame = ModernFrame(parent)
        header_frame.pack(fill=tk.X, pady=(0, Styling.PADDING_LARGE))
        
        # Icon
        icon_label = ModernLabel(header_frame, text="⚡", font=Fonts.DISPLAY, fg=Colors.PURPLE_PRIMARY)
        icon_label.pack(side=tk.LEFT)
        
        # Title
        title_label = ModernLabel(header_frame, text=self.title, font=Fonts.TITLE, fg=Colors.TEXT_PRIMARY)
        title_label.pack(side=tk.LEFT, padx=(Styling.PADDING_MEDIUM, 0))
        
        # Animated dots
        self.dots_label = ModernLabel(header_frame, text="", font=Fonts.TITLE, fg=Colors.PURPLE_PRIMARY)
        self.dots_label.pack(side=tk.LEFT, padx=(Styling.PADDING_SMALL, 0))
        
        # Start animation
        self._animate_dots()
    
    def _create_progress_section(self, parent):
        """Create progress section with modern styling."""
        progress_frame = ModernFrame(parent)
        progress_frame.pack(fill=tk.X, pady=(0, Styling.PADDING_LARGE))
        
        # Progress label
        self.progress_label_var = tk.StringVar(value="Starting...")
        progress_label = ModernLabel(progress_frame, 
                                   textvariable=self.progress_label_var,
                                   font=Fonts.MEDIUM,
                                   fg=Colors.TEXT_PRIMARY)
        progress_label.pack(pady=(0, Styling.PADDING_MEDIUM))
        
        # Progress bar
        self.progress_var = tk.IntVar()
        self.progress_bar = ModernProgressBar(progress_frame, 
                                            variable=self.progress_var,
                                            maximum=self.total_items,
                                            length=400,
                                            height=20,
                                            mode='determinate')
        self.progress_bar.pack(pady=(0, Styling.PADDING_MEDIUM))
        
        # Progress info
        self.progress_info_var = tk.StringVar(value="0 / 0")
        progress_info = ModernLabel(progress_frame,
                                   textvariable=self.progress_info_var,
                                   font=Fonts.SMALL,
                                   fg=Colors.TEXT_SECONDARY)
        progress_info.pack()
    
    def _create_action_buttons(self, parent):
        """Create action buttons."""
        button_frame = ModernFrame(parent)
        button_frame.pack(fill=tk.X)
        
        # Cancel button
        cancel_button = ModernButton(button_frame, 
                                   text="Cancel", 
                                   command=self._handle_cancel,
                                   style='error')
        cancel_button.pack(side=tk.RIGHT)
    
    def _animate_dots(self):
        """Animate loading dots."""
        dots = ["", ".", "..", "..."]
        self.dots_label.config(text=dots[self.animation_step % len(dots)])
        self.animation_step += 1
        
        # Continue animation
        self.animation_timer = self.window.after(500, self._animate_dots)
    
    def update_progress(self, completed, total, message=""):
        """Update progress with modern styling."""
        if not self.window or not self.window.winfo_exists():
            return
        
        # Update progress bar
        if self.progress_var:
            self.progress_var.set(completed)
        
        # Update label
        if self.progress_label_var:
            if message:
                self.progress_label_var.set(message)
            else:
                self.progress_label_var.set(f"Processing: {completed}/{total}")
        
        # Update progress info
        if self.progress_info_var:
            percentage = (completed / total * 100) if total > 0 else 0
            self.progress_info_var.set(f"{completed} / {total} ({percentage:.1f}%)")
        
        # Update window
        self.window.update_idletasks()
    
    def set_cancel_callback(self, callback):
        """Set callback for cancel button."""
        self.cancel_callback = callback
    
    def _handle_cancel(self):
        """Handle cancel button press."""
        if self.cancel_callback:
            self.cancel_callback()
        self.close()
    
    def _handle_close(self):
        """Handle window close."""
        if self.cancelable:
            self._handle_cancel()
    
    def close(self):
        """Close the progress window."""
        # Stop animation
        if self.animation_timer:
            self.window.after_cancel(self.animation_timer)
            self.animation_timer = None
        
        # Close window
        if self.window:
            self.window.destroy()
            self.window = None
    
    def is_open(self):
        """Check if window is open."""
        return self.window is not None and self.window.winfo_exists()


class ModernIndeterminateProgress:
    """Modern indeterminate progress indicator."""
    
    def __init__(self, parent, title, message, cancelable=True):
        self.parent = parent
        self.title = title
        self.message = message
        self.cancelable = cancelable
        
        self.window = None
        self.progress_bar = None
        self.message_label = None
        self.cancel_callback = None
        
        # Animation state
        self.animation_step = 0
        self.animation_timer = None
        
        self._create_window()
    
    def _create_window(self):
        """Create indeterminate progress window."""
        # Create window
        self.window = tk.Toplevel(self.parent)
        self.window.title(self.title)
        self.window.geometry("450x150")
        self.window.configure(bg=Colors.BG_PRIMARY)
        self.window.resizable(False, False)
        
        # Center window
        self.window.transient(self.parent)
        self.window.grab_set()
        
        self.window.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + (self.parent.winfo_width() // 2) - 225,
            self.parent.winfo_rooty() + (self.parent.winfo_height() // 2) - 75
        ))
        
        # Main container
        main_container = ModernFrame(self.window, style='card')
        main_container.pack(fill=tk.BOTH, expand=True, padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        # Header
        header_frame = ModernFrame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, Styling.PADDING_LARGE))
        
        # Icon and title
        icon_label = ModernLabel(header_frame, text="🔄", font=Fonts.LARGE, fg=Colors.PURPLE_PRIMARY)
        icon_label.pack(side=tk.LEFT)
        
        title_label = ModernLabel(header_frame, text=self.title, font=Fonts.HEADING, fg=Colors.TEXT_PRIMARY)
        title_label.pack(side=tk.LEFT, padx=(Styling.PADDING_MEDIUM, 0))
        
        # Message
        self.message_label = ModernLabel(main_container, 
                                       text=self.message,
                                       font=Fonts.MEDIUM,
                                       fg=Colors.TEXT_SECONDARY)
        self.message_label.pack(pady=(0, Styling.PADDING_MEDIUM))
        
        # Indeterminate progress bar
        self.progress_bar = ModernProgressBar(main_container, 
                                            mode='indeterminate',
                                            length=350,
                                            height=15)
        self.progress_bar.pack(pady=(0, Styling.PADDING_MEDIUM))
        self.progress_bar.start(10)  # Start animation
        
        # Cancel button
        if self.cancelable:
            cancel_button = ModernButton(main_container, 
                                       text="Cancel", 
                                       command=self._handle_cancel,
                                       style='secondary')
            cancel_button.pack()
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self._handle_close if self.cancelable else lambda: None)
    
    def update_message(self, message):
        """Update the message."""
        if self.message_label and self.window and self.window.winfo_exists():
            self.message_label.config(text=message)
            self.window.update_idletasks()
    
    def set_cancel_callback(self, callback):
        """Set callback for cancel button."""
        self.cancel_callback = callback
    
    def _handle_cancel(self):
        """Handle cancel button press."""
        if self.cancel_callback:
            self.cancel_callback()
        self.close()
    
    def _handle_close(self):
        """Handle window close."""
        if self.cancelable:
            self._handle_cancel()
    
    def close(self):
        """Close the progress window."""
        # Stop progress bar
        if self.progress_bar:
            self.progress_bar.stop()
        
        # Close window
        if self.window:
            self.window.destroy()
            self.window = None
    
    def is_open(self):
        """Check if window is open."""
        return self.window is not None and self.window.winfo_exists()


class ProgressTracker:
    """
    Modern progress tracker with enhanced styling and user experience.
    
    This class manages progress windows for long-running operations
    with modern design and smooth animations.
    """
    
    def __init__(self, parent: tk.Tk):
        """
        Initialize the modern progress tracker.
        
        Args:
            parent: Parent tkinter window
        """
        self.parent = parent
        self.progress_window = None
        self.indeterminate_window = None
        self.cancel_callback = None
    
    def show_progress_window(self, title: str, total_items: int, cancelable: bool = True) -> None:
        """
        Show a modern progress window for a long operation.
        
        Args:
            title: Title for the progress window
            total_items: Total number of items to process
            cancelable: Whether the operation can be cancelled
        """
        if self.progress_window:
            self.close_progress_window()
        
        self.progress_window = ModernProgressWindow(self.parent, title, total_items, cancelable)
        
        if self.cancel_callback:
            self.progress_window.set_cancel_callback(self.cancel_callback)
    
    def update_progress(self, completed: int, total: int, message: str = "") -> None:
        """
        Update the progress window with modern styling.
        
        Args:
            completed: Number of items completed
            total: Total number of items
            message: Status message to display
        """
        if self.progress_window and self.progress_window.is_open():
            self.progress_window.update_progress(completed, total, message)
    
    def show_indeterminate_progress(self, title: str, message: str, cancelable: bool = True) -> None:
        """
        Show modern indeterminate progress indicator.
        
        Args:
            title: Title for the progress window
            message: Message to display
            cancelable: Whether the operation can be cancelled
        """
        if self.indeterminate_window:
            self.close_indeterminate_window()
        
        self.indeterminate_window = ModernIndeterminateProgress(self.parent, title, message, cancelable)
        
        if self.cancel_callback:
            self.indeterminate_window.set_cancel_callback(self.cancel_callback)
    
    def update_indeterminate_message(self, message: str) -> None:
        """
        Update the message in an indeterminate progress window.
        
        Args:
            message: New message to display
        """
        if self.indeterminate_window and self.indeterminate_window.is_open():
            self.indeterminate_window.update_message(message)
    
    def set_cancel_callback(self, callback) -> None:
        """
        Set callback function for cancel button.
        
        Args:
            callback: Function to call when cancel is pressed
        """
        self.cancel_callback = callback
        
        # Update existing windows
        if self.progress_window:
            self.progress_window.set_cancel_callback(callback)
        if self.indeterminate_window:
            self.indeterminate_window.set_cancel_callback(callback)
    
    def handle_cancel(self) -> None:
        """Handle cancel button press."""
        if self.cancel_callback:
            self.cancel_callback()
        self.close_progress_window()
        self.close_indeterminate_window()
    
    def close_progress_window(self) -> None:
        """Close the progress window."""
        if self.progress_window:
            self.progress_window.close()
            self.progress_window = None
    
    def close_indeterminate_window(self) -> None:
        """Close the indeterminate progress window."""
        if self.indeterminate_window:
            self.indeterminate_window.close()
            self.indeterminate_window = None
    
    def is_showing(self) -> bool:
        """
        Check if any progress window is currently showing.
        
        Returns:
            True if any window is open, False otherwise
        """
        return ((self.progress_window and self.progress_window.is_open()) or
                (self.indeterminate_window and self.indeterminate_window.is_open()))
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self.close_progress_window()
        self.close_indeterminate_window()
    
    def show_completion_message(self, title: str, message: str, success: bool = True) -> None:
        """
        Show a modern completion message.
        
        Args:
            title: Title for the dialog
            message: Success/failure message
            success: Whether the operation was successful
        """
        # Close any existing progress windows
        self.close_progress_window()
        self.close_indeterminate_window()
        
        # Create completion dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title(title)
        dialog.geometry("400x180")
        dialog.configure(bg=Colors.BG_PRIMARY)
        dialog.resizable(False, False)
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center dialog
        dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + (self.parent.winfo_width() // 2) - 200,
            self.parent.winfo_rooty() + (self.parent.winfo_height() // 2) - 90
        ))
        
        # Main container
        main_container = ModernFrame(dialog, style='card')
        main_container.pack(fill=tk.BOTH, expand=True, padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        # Header
        header_frame = ModernFrame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, Styling.PADDING_LARGE))
        
        # Icon based on success/failure
        icon = "✅" if success else "❌"
        icon_color = Colors.SUCCESS if success else Colors.ERROR
        
        icon_label = ModernLabel(header_frame, text=icon, font=Fonts.DISPLAY, fg=icon_color)
        icon_label.pack(side=tk.LEFT)
        
        title_label = ModernLabel(header_frame, text=title, font=Fonts.HEADING, fg=Colors.TEXT_PRIMARY)
        title_label.pack(side=tk.LEFT, padx=(Styling.PADDING_MEDIUM, 0))
        
        # Message
        message_label = ModernLabel(main_container, 
                                   text=message,
                                   font=Fonts.MEDIUM,
                                   fg=Colors.TEXT_SECONDARY,
                                   wraplength=350,
                                   justify=tk.LEFT)
        message_label.pack(pady=(0, Styling.PADDING_LARGE))
        
        # OK button
        ok_button = ModernButton(main_container, 
                               text="OK", 
                               command=dialog.destroy,
                               style='success' if success else 'error')
        ok_button.pack()
        
        # Auto-close after 3 seconds for success messages
        if success:
            dialog.after(3000, dialog.destroy)
