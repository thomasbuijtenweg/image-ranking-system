"""
Settings window module for the Image Ranking System.

This module implements the settings window that allows users to
configure the ranking algorithm weights and other preferences.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict

from config import Colors


class SettingsWindow:
    """
    Window for configuring system settings and algorithm parameters.
    
    This window allows users to adjust the weights used in the ranking
    algorithm and other system preferences.
    """
    
    def __init__(self, parent: tk.Tk, data_manager):
        """
        Initialize the settings window.
        
        Args:
            parent: Parent window
            data_manager: DataManager instance
        """
        self.parent = parent
        self.data_manager = data_manager
        self.window = None
        self.weight_vars = {}
        self.weight_labels = {}
        self.total_weight_label = None
        self.weight_warning_label = None
        self.tier_std_var = None
        self.tier_std_label = None
    
    def show(self):
        """Show the settings window, creating it if necessary."""
        if self.window is None or not self.window.winfo_exists():
            self.create_window()
        else:
            self.window.lift()
            self.window.focus_force()
    
    def create_window(self):
        """Create the settings window with all its components."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Algorithm Settings")
        self.window.geometry("600x650")
        self.window.configure(bg=Colors.BG_PRIMARY)
        
        # Handle window closing
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # Create main frame with scrollbar
        main_frame = tk.Frame(self.window, bg=Colors.BG_PRIMARY)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(main_frame, bg=Colors.BG_PRIMARY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=Colors.BG_PRIMARY)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Create content
        self.create_settings_content(scrollable_frame)
        
        # Configure scrolling
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Update initial display
        self.update_weight_display()
        self.update_tier_std_display()
    
    def create_settings_content(self, parent: tk.Frame):
        """Create the main settings content."""
        # Title
        tk.Label(parent, text="Algorithm Settings", 
                font=('Arial', 16, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_PRIMARY).pack(pady=10)
        
        # Create sections
        self.create_weight_section(parent)
        self.create_tier_distribution_section(parent)
        
        # Apply button
        tk.Button(parent, text="Apply Changes", 
                 command=self.apply_changes,
                 bg=Colors.BUTTON_SUCCESS, fg='white', font=('Arial', 12), relief=tk.FLAT).pack(pady=20)
    
    def create_weight_section(self, parent: tk.Frame):
        """Create the weight adjustment section."""
        # Weight section frame
        weight_section = tk.Frame(parent, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=1)
        weight_section.pack(fill=tk.X, padx=10, pady=10)
        
        # Section title
        tk.Label(weight_section, text="Selection Weights", 
                font=('Arial', 14, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(pady=10)
        
        tk.Label(weight_section, text="These weights determine how images are prioritized for comparison",
                font=('Arial', 10, 'italic'), fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY).pack(pady=5)
        
        # Weight adjustment frame
        weights_frame = tk.Frame(weight_section, bg=Colors.BG_SECONDARY)
        weights_frame.pack(padx=20, pady=10)
        
        # Create weight controls
        self.create_weight_controls(weights_frame)
    
    def create_tier_distribution_section(self, parent: tk.Frame):
        """Create the tier distribution section."""
        # Tier distribution section frame
        tier_section = tk.Frame(parent, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=1)
        tier_section.pack(fill=tk.X, padx=10, pady=10)
        
        # Section title
        tk.Label(tier_section, text="Tier Distribution", 
                font=('Arial', 14, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(pady=10)
        
        # Description
        description_text = ("Controls how tiers should be distributed. Lower values create a tighter distribution "
                          "around tier 0, higher values create a wider spread.")
        tk.Label(tier_section, text=description_text, font=('Arial', 10, 'italic'), 
                fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY, wraplength=500, justify=tk.LEFT).pack(pady=5)
        
        # Tier distribution controls
        tier_frame = tk.Frame(tier_section, bg=Colors.BG_SECONDARY)
        tier_frame.pack(padx=20, pady=10)
        
        # Standard deviation control
        tk.Label(tier_frame, text="Tier Distribution Standard Deviation", 
                font=('Arial', 11, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        detail_text = ("Lower values (0.5-1.0): Tighter distribution, most images in tier 0\n"
                      "Medium values (1.0-2.0): Balanced distribution\n"
                      "Higher values (2.0-3.0): Wider distribution, more images in outer tiers")
        tk.Label(tier_frame, text=detail_text, font=('Arial', 9), 
                fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY, justify=tk.LEFT).pack(anchor=tk.W, pady=5)
        
        # Get current value with fallback for backward compatibility
        if not hasattr(self.data_manager, 'tier_distribution_std'):
            self.data_manager.tier_distribution_std = 1.5  # Set default value
        current_value = self.data_manager.tier_distribution_std
        
        self.tier_std_label = tk.Label(tier_frame, text=f"Current: {current_value:.2f}", 
                                      fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY)
        self.tier_std_label.pack(anchor=tk.W)
        
        # Slider
        self.tier_std_var = tk.DoubleVar(value=current_value)
        
        slider = tk.Scale(tier_frame, from_=0.5, to=3.0, resolution=0.1,
                        orient=tk.HORIZONTAL, variable=self.tier_std_var,
                        command=lambda v: self.update_tier_std_display(),
                        bg=Colors.BG_SECONDARY, fg=Colors.TEXT_PRIMARY, 
                        troughcolor=Colors.BG_TERTIARY, activebackground=Colors.BUTTON_INFO,
                        length=400)
        slider.pack(fill=tk.X, padx=20, pady=5)
        
        # Preview distribution button
        tk.Button(tier_frame, text="Preview Distribution", 
                 command=self.preview_distribution,
                 bg=Colors.BUTTON_INFO, fg='white', relief=tk.FLAT).pack(pady=10)
    
    def create_weight_controls(self, parent: tk.Frame):
        """Create the weight adjustment controls."""
        weights_info = [
            ('recency', 'Recency Weight', 'Higher = prioritize images not voted recently'),
            ('low_votes', 'Low Votes Weight', 'Higher = prioritize images with fewer total votes'),
            ('instability', 'Instability Weight', 'Higher = prioritize images with unstable tiers'),
            ('tier_size', 'Tier Size Weight', 'Higher = prioritize images in over-populated tiers')
        ]
        
        for key, title, description in weights_info:
            self.create_weight_control(parent, key, title, description)
        
        # Total weight label
        self.total_weight_label = tk.Label(parent, 
                                         text="Total: 0.00",
                                         font=('Arial', 10), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY)
        self.total_weight_label.pack(pady=10)
        
        # Warning label
        self.weight_warning_label = tk.Label(parent, text="", fg=Colors.TEXT_ERROR, bg=Colors.BG_SECONDARY)
        self.weight_warning_label.pack()
        
        # Normalize button
        tk.Button(parent, text="Normalize Weights (make sum = 1.0)",
                 command=self.normalize_weights, bg=Colors.BUTTON_DANGER, fg='white', relief=tk.FLAT).pack(pady=10)
    
    def create_weight_control(self, parent: tk.Frame, key: str, title: str, description: str):
        """Create a single weight control widget."""
        # Frame for this weight
        weight_frame = tk.Frame(parent, bg=Colors.BG_SECONDARY)
        weight_frame.pack(fill=tk.X, pady=10)
        
        # Title and description
        tk.Label(weight_frame, text=title, font=('Arial', 11, 'bold'), 
                fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        tk.Label(weight_frame, text=description, font=('Arial', 9, 'italic'), 
                fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        # Current value label
        current_value = self.data_manager.weights.get(key, 0.25)
        value_label = tk.Label(weight_frame, text=f"Current: {current_value:.2f}", 
                             fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY)
        value_label.pack(anchor=tk.W)
        self.weight_labels[key] = value_label
        
        # Slider
        var = tk.DoubleVar(value=current_value)
        self.weight_vars[key] = var
        
        slider = tk.Scale(weight_frame, from_=0, to=1, resolution=0.05,
                        orient=tk.HORIZONTAL, variable=var,
                        command=lambda v, k=key: self.update_weight_label(k),
                        bg=Colors.BG_SECONDARY, fg=Colors.TEXT_PRIMARY, 
                        troughcolor=Colors.BG_TERTIARY, activebackground=Colors.BUTTON_SUCCESS)
        slider.pack(fill=tk.X, padx=20)
    
    def update_weight_label(self, key: str):
        """Update the label showing the current weight value."""
        value = self.weight_vars[key].get()
        self.weight_labels[key].config(text=f"Current: {value:.2f}")
        self.update_weight_display()
    
    def update_weight_display(self):
        """Update the total weight display and warning."""
        total = sum(var.get() for var in self.weight_vars.values())
        self.total_weight_label.config(text=f"Total: {total:.2f}")
        
        if abs(total - 1.0) > 0.01:
            self.weight_warning_label.config(
                text="⚠️ Weights should sum to 1.0 for balanced selection")
        else:
            self.weight_warning_label.config(text="✓ Weights sum to 1.0")
    
    def update_tier_std_display(self):
        """Update the tier standard deviation display."""
        if self.tier_std_var is not None:
            value = self.tier_std_var.get()
            self.tier_std_label.config(text=f"Current: {value:.2f}")
    
    def normalize_weights(self):
        """Normalize weights to sum to 1.0."""
        total = sum(var.get() for var in self.weight_vars.values())
        if total > 0:
            for var in self.weight_vars.values():
                var.set(var.get() / total)
            self.update_weight_display()
    
    def preview_distribution(self):
        """Show a preview of what the tier distribution should look like."""
        import math
        
        std_dev = self.tier_std_var.get()
        
        # Calculate expected proportions for tiers -5 to +5
        tiers = list(range(-5, 6))
        proportions = []
        
        for tier in tiers:
            density = math.exp(-(tier ** 2) / (2 * std_dev ** 2))
            proportions.append(density)
        
        # Normalize proportions
        total_density = sum(proportions)
        normalized_proportions = [p / total_density for p in proportions]
        
        # Create preview text
        preview_text = f"Expected Distribution (std dev = {std_dev:.1f}):\n\n"
        
        for tier, proportion in zip(tiers, normalized_proportions):
            percentage = proportion * 100
            bar_length = int(percentage * 2)  # Scale for visual bar
            bar = "█" * bar_length
            preview_text += f"Tier {tier:+2d}: {percentage:5.1f}% {bar}\n"
        
        # Show in message box
        messagebox.showinfo("Tier Distribution Preview", preview_text)
    
    def apply_changes(self):
        """Apply the weight changes and close the window."""
        # Update weights in data manager
        for key, var in self.weight_vars.items():
            self.data_manager.weights[key] = var.get()
        
        # Update tier distribution parameter (ensure it exists)
        if not hasattr(self.data_manager, 'tier_distribution_std'):
            self.data_manager.tier_distribution_std = 1.5  # Set default if missing
        if self.tier_std_var is not None:
            self.data_manager.tier_distribution_std = self.tier_std_var.get()
        
        messagebox.showinfo("Success", "Settings updated successfully!")
        self.close_window()
    
    def close_window(self):
        """Handle window closing."""
        if self.window:
            self.window.destroy()
            self.window = None