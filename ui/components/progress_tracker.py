"""
Progress tracker for the Image Ranking System.

This module handles progress windows and loading indicators
for long-running operations.
"""

import tkinter as tk
from tkinter import ttk

from config import Colors


class ProgressTracker:
    """
    Handles progress windows and loading indicators.
    
    This class manages progress windows for long-running operations
    like file scanning and metadata extraction.
    """
    
    def __init__(self, parent: tk.Tk):
        """
        Initialize the progress tracker.
        
        Args:
            parent: Parent tkinter window
        """
        self.parent = parent
        self.progress_window = None
        self.progress_var = None
        self.progress_label_var = None
        self.cancel_callback = None
    
    def show_progress_window(self, title: str, total_items: int, cancelable: bool = True) -> None:
        """
        Show a progress window for a long operation.
        
        Args:
            title: Title for the progress window
            total_items: Total number of items to process
            cancelable: Whether the operation can be cancelled
        """
        if self.progress_window:
            self.close_progress_window()
        
        self.progress_window = tk.Toplevel(self.parent)
        self.progress_window.title(title)
        self.progress_window.geometry("400x150")
        self.progress_window.configure(bg=Colors.BG_PRIMARY)
        self.progress_window.transient(self.parent)
        self.progress_window.grab_set()
        
        # Center the window
        self.progress_window.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 200,
            self.parent.winfo_rooty() + 200
        ))
        
        # Progress label
        self.progress_label_var = tk.StringVar(value="Starting...")
        label = tk.Label(self.progress_window, textvariable=self.progress_label_var,
                        font=('Arial', 12), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_PRIMARY)
        label.pack(pady=20)
        
        # Progress bar
        self.progress_var = tk.IntVar()
        progress_bar = ttk.Progressbar(self.progress_window, variable=self.progress_var,
                                     maximum=total_items, length=350)
        progress_bar.pack(pady=10)
        
        # Cancel button (if cancelable)
        if cancelable:
            cancel_button = tk.Button(self.progress_window, text="Cancel", 
                                    command=self.handle_cancel,
                                    bg=Colors.BUTTON_DANGER, fg='white', relief=tk.FLAT)
            cancel_button.pack(pady=10)
        
        # Handle window close
        self.progress_window.protocol("WM_DELETE_WINDOW", self.handle_cancel if cancelable else lambda: None)
    
    def update_progress(self, completed: int, total: int, message: str = "") -> None:
        """
        Update the progress window.
        
        Args:
            completed: Number of items completed
            total: Total number of items
            message: Status message to display
        """
        if not self.progress_window:
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
        
        # Update the window
        self.progress_window.update_idletasks()
    
    def set_cancel_callback(self, callback) -> None:
        """
        Set callback function for cancel button.
        
        Args:
            callback: Function to call when cancel is pressed
        """
        self.cancel_callback = callback
    
    def handle_cancel(self) -> None:
        """Handle cancel button press."""
        if self.cancel_callback:
            self.cancel_callback()
        self.close_progress_window()
    
    def close_progress_window(self) -> None:
        """Close the progress window."""
        if self.progress_window:
            self.progress_window.destroy()
            self.progress_window = None
            self.progress_var = None
            self.progress_label_var = None
    
    def is_showing(self) -> bool:
        """
        Check if progress window is currently showing.
        
        Returns:
            True if window is open, False otherwise
        """
        return self.progress_window is not None and self.progress_window.winfo_exists()
    
    def show_indeterminate_progress(self, title: str, message: str, cancelable: bool = True) -> None:
        """
        Show an indeterminate progress indicator.
        
        Args:
            title: Title for the progress window
            message: Message to display
            cancelable: Whether the operation can be cancelled
        """
        if self.progress_window:
            self.close_progress_window()
        
        self.progress_window = tk.Toplevel(self.parent)
        self.progress_window.title(title)
        self.progress_window.geometry("400x120")
        self.progress_window.configure(bg=Colors.BG_PRIMARY)
        self.progress_window.transient(self.parent)
        self.progress_window.grab_set()
        
        # Center the window
        self.progress_window.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 200,
            self.parent.winfo_rooty() + 200
        ))
        
        # Message label
        label = tk.Label(self.progress_window, text=message,
                        font=('Arial', 12), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_PRIMARY)
        label.pack(pady=20)
        
        # Indeterminate progress bar
        progress_bar = ttk.Progressbar(self.progress_window, mode='indeterminate', length=350)
        progress_bar.pack(pady=10)
        progress_bar.start()
        
        # Cancel button (if cancelable)
        if cancelable:
            cancel_button = tk.Button(self.progress_window, text="Cancel", 
                                    command=self.handle_cancel,
                                    bg=Colors.BUTTON_DANGER, fg='white', relief=tk.FLAT)
            cancel_button.pack(pady=10)
        
        # Handle window close
        self.progress_window.protocol("WM_DELETE_WINDOW", self.handle_cancel if cancelable else lambda: None)
    
    def update_indeterminate_message(self, message: str) -> None:
        """
        Update the message in an indeterminate progress window.
        
        Args:
            message: New message to display
        """
        if self.progress_window and self.progress_window.winfo_exists():
            # Find the label widget and update it
            for widget in self.progress_window.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(text=message)
                    break
            
            self.progress_window.update_idletasks()
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self.close_progress_window()
