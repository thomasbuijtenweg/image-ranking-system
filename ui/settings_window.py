"""
Settings window module for the Image Ranking System.

This module implements the settings window that allows users to
configure the ranking algorithm weights and other preferences.
Now supports separate weight configuration and priority preferences 
for left and right image selection.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict

from config import Colors


class SettingsWindow:
    """
    Window for configuring system settings and algorithm parameters.
    
    This window allows users to adjust the weights used in the ranking
    algorithm and other system preferences. Now supports separate
    weight configuration and priority preferences for left and right image selection.
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
        
        # Separate weight variables for left and right
        self.left_weight_vars = {}
        self.left_weight_labels = {}
        self.right_weight_vars = {}
        self.right_weight_labels = {}
        
        # Priority preference variables for left and right
        self.left_preference_vars = {}
        self.right_preference_vars = {}
        
        # Total weight labels
        self.left_total_weight_label = None
        self.left_weight_warning_label = None
        self.right_total_weight_label = None
        self.right_weight_warning_label = None
        
        # Tier distribution variables
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
        self.window.geometry("1000x800")  # Even wider to accommodate new controls
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
        self.create_preference_section(parent)
        self.create_tier_distribution_section(parent)
        
        # Apply button
        tk.Button(parent, text="Apply Changes", 
                 command=self.apply_changes,
                 bg=Colors.BUTTON_SUCCESS, fg='white', font=('Arial', 12), relief=tk.FLAT).pack(pady=20)
    
    def create_weight_section(self, parent: tk.Frame):
        """Create the weight adjustment section with separate left/right controls."""
        # Weight section frame
        weight_section = tk.Frame(parent, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=1)
        weight_section.pack(fill=tk.X, padx=10, pady=10)
        
        # Section title
        tk.Label(weight_section, text="Selection Weights", 
                font=('Arial', 14, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(pady=10)
        
        tk.Label(weight_section, text="These weights determine how images are prioritized for comparison. Left and right images are now selected independently.",
                font=('Arial', 10, 'italic'), fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY).pack(pady=5)
        
        # Main weights container with side-by-side layout
        weights_container = tk.Frame(weight_section, bg=Colors.BG_SECONDARY)
        weights_container.pack(padx=20, pady=10, fill=tk.X)
        
        # Configure grid for side-by-side layout
        weights_container.grid_columnconfigure(0, weight=1, uniform="equal")
        weights_container.grid_columnconfigure(1, weight=1, uniform="equal")
        
        # Left weights frame
        left_frame = tk.Frame(weights_container, bg=Colors.BG_TERTIARY, relief=tk.RAISED, borderwidth=1)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
        
        # Right weights frame
        right_frame = tk.Frame(weights_container, bg=Colors.BG_TERTIARY, relief=tk.RAISED, borderwidth=1)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)
        
        # Create weight controls for both sides
        self.create_side_weight_controls(left_frame, 'left', "Left Image Selection Weights")
        self.create_side_weight_controls(right_frame, 'right', "Right Image Selection Weights")
        
        # Global controls frame
        global_controls_frame = tk.Frame(weight_section, bg=Colors.BG_SECONDARY)
        global_controls_frame.pack(pady=10)
        
        # Utility buttons
        button_frame = tk.Frame(global_controls_frame, bg=Colors.BG_SECONDARY)
        button_frame.pack()
        
        tk.Button(button_frame, text="Copy Left → Right", command=self.copy_left_to_right,
                 bg=Colors.BUTTON_INFO, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Copy Right → Left", command=self.copy_right_to_left,
                 bg=Colors.BUTTON_INFO, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Normalize Both", command=self.normalize_both_weights,
                 bg=Colors.BUTTON_WARNING, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Reset to Defaults", command=self.reset_to_defaults,
                 bg=Colors.BUTTON_DANGER, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
    
    def create_preference_section(self, parent: tk.Frame):
        """Create the priority preference section with separate left/right controls."""
        # Preference section frame
        preference_section = tk.Frame(parent, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=1)
        preference_section.pack(fill=tk.X, padx=10, pady=10)
        
        # Section title
        tk.Label(preference_section, text="Priority Preferences", 
                font=('Arial', 14, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(pady=10)
        
        tk.Label(preference_section, text="These preferences determine whether high or low values are prioritized for stability and vote counts.",
                font=('Arial', 10, 'italic'), fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY).pack(pady=5)
        
        # Main preferences container with side-by-side layout
        preferences_container = tk.Frame(preference_section, bg=Colors.BG_SECONDARY)
        preferences_container.pack(padx=20, pady=10, fill=tk.X)
        
        # Configure grid for side-by-side layout
        preferences_container.grid_columnconfigure(0, weight=1, uniform="equal")
        preferences_container.grid_columnconfigure(1, weight=1, uniform="equal")
        
        # Left preferences frame
        left_pref_frame = tk.Frame(preferences_container, bg=Colors.BG_TERTIARY, relief=tk.RAISED, borderwidth=1)
        left_pref_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
        
        # Right preferences frame
        right_pref_frame = tk.Frame(preferences_container, bg=Colors.BG_TERTIARY, relief=tk.RAISED, borderwidth=1)
        right_pref_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)
        
        # Create preference controls for both sides
        self.create_side_preference_controls(left_pref_frame, 'left', "Left Image Priority Preferences")
        self.create_side_preference_controls(right_pref_frame, 'right', "Right Image Priority Preferences")
        
        # Global preference controls frame
        global_pref_controls_frame = tk.Frame(preference_section, bg=Colors.BG_SECONDARY)
        global_pref_controls_frame.pack(pady=10)
        
        # Utility buttons for preferences
        pref_button_frame = tk.Frame(global_pref_controls_frame, bg=Colors.BG_SECONDARY)
        pref_button_frame.pack()
        
        tk.Button(pref_button_frame, text="Copy Left → Right", command=self.copy_left_preferences_to_right,
                 bg=Colors.BUTTON_INFO, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(pref_button_frame, text="Copy Right → Left", command=self.copy_right_preferences_to_left,
                 bg=Colors.BUTTON_INFO, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(pref_button_frame, text="Reset Preferences to Defaults", command=self.reset_preferences_to_defaults,
                 bg=Colors.BUTTON_DANGER, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
    
    def create_side_weight_controls(self, parent: tk.Frame, side: str, title: str):
        """Create weight controls for one side (left or right)."""
        # Title
        tk.Label(parent, text=title, font=('Arial', 12, 'bold'), 
                fg=Colors.TEXT_PRIMARY, bg=Colors.BG_TERTIARY).pack(pady=10)
        
        # Get appropriate weight variables and labels dictionaries
        if side == 'left':
            weight_vars = self.left_weight_vars
            weight_labels = self.left_weight_labels
            current_weights = self.data_manager.get_left_weights()
        else:
            weight_vars = self.right_weight_vars
            weight_labels = self.right_weight_labels
            current_weights = self.data_manager.get_right_weights()
        
        # Weight controls frame
        controls_frame = tk.Frame(parent, bg=Colors.BG_TERTIARY)
        controls_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Weight information
        weights_info = [
            ('recency', 'Recency Weight', 'Prioritize images not voted recently'),
            ('low_votes', 'Vote Count Weight', 'Weight for vote count priority (see preferences below)'),
            ('instability', 'Stability Weight', 'Weight for stability priority (see preferences below)'),
            ('tier_size', 'Tier Size Weight', 'Prioritize images in over-populated tiers')
        ]
        
        # Create individual weight controls
        for key, title, description in weights_info:
            self.create_individual_weight_control(controls_frame, key, title, description, 
                                                 weight_vars, weight_labels, current_weights, side)
        
        # Total weight display
        if side == 'left':
            self.left_total_weight_label = tk.Label(controls_frame, text="Total: 0.00",
                                                   font=('Arial', 10, 'bold'), 
                                                   fg=Colors.TEXT_PRIMARY, bg=Colors.BG_TERTIARY)
            self.left_total_weight_label.pack(pady=(10, 5))
            
            self.left_weight_warning_label = tk.Label(controls_frame, text="", 
                                                     fg=Colors.TEXT_ERROR, bg=Colors.BG_TERTIARY)
            self.left_weight_warning_label.pack()
        else:
            self.right_total_weight_label = tk.Label(controls_frame, text="Total: 0.00",
                                                    font=('Arial', 10, 'bold'), 
                                                    fg=Colors.TEXT_PRIMARY, bg=Colors.BG_TERTIARY)
            self.right_total_weight_label.pack(pady=(10, 5))
            
            self.right_weight_warning_label = tk.Label(controls_frame, text="", 
                                                      fg=Colors.TEXT_ERROR, bg=Colors.BG_TERTIARY)
            self.right_weight_warning_label.pack()
        
        # Normalize button for this side
        normalize_text = f"Normalize {side.title()} Weights"
        normalize_cmd = self.normalize_left_weights if side == 'left' else self.normalize_right_weights
        tk.Button(controls_frame, text=normalize_text, command=normalize_cmd,
                 bg=Colors.BUTTON_SECONDARY, fg='white', relief=tk.FLAT).pack(pady=10)
    
    def create_side_preference_controls(self, parent: tk.Frame, side: str, title: str):
        """Create priority preference controls for one side (left or right)."""
        # Title
        tk.Label(parent, text=title, font=('Arial', 12, 'bold'), 
                fg=Colors.TEXT_PRIMARY, bg=Colors.BG_TERTIARY).pack(pady=10)
        
        # Get appropriate preference variables and current preferences
        if side == 'left':
            preference_vars = self.left_preference_vars
            current_preferences = self.data_manager.get_left_priority_preferences()
        else:
            preference_vars = self.right_preference_vars
            current_preferences = self.data_manager.get_right_priority_preferences()
        
        # Preference controls frame
        controls_frame = tk.Frame(parent, bg=Colors.BG_TERTIARY)
        controls_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Stability preference
        stability_frame = tk.Frame(controls_frame, bg=Colors.BG_TERTIARY)
        stability_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(stability_frame, text="Stability Priority:", font=('Arial', 10, 'bold'), 
                fg=Colors.TEXT_PRIMARY, bg=Colors.BG_TERTIARY).pack(anchor=tk.W)
        
        current_stability_pref = current_preferences.get('prioritize_high_stability', False)
        stability_var = tk.BooleanVar(value=current_stability_pref)
        preference_vars['prioritize_high_stability'] = stability_var
        
        stability_checkbox = tk.Checkbutton(stability_frame, 
                                          text="Prioritize HIGH stability (stable images)", 
                                          variable=stability_var,
                                          fg=Colors.TEXT_PRIMARY, bg=Colors.BG_TERTIARY,
                                          selectcolor=Colors.BG_PRIMARY, activebackground=Colors.BG_TERTIARY)
        stability_checkbox.pack(anchor=tk.W, padx=20)
        
        tk.Label(stability_frame, text="Unchecked = Prioritize LOW stability (unstable images)", 
                font=('Arial', 9, 'italic'), fg=Colors.TEXT_SECONDARY, bg=Colors.BG_TERTIARY).pack(anchor=tk.W, padx=20)
        
        # Vote count preference
        votes_frame = tk.Frame(controls_frame, bg=Colors.BG_TERTIARY)
        votes_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(votes_frame, text="Vote Count Priority:", font=('Arial', 10, 'bold'), 
                fg=Colors.TEXT_PRIMARY, bg=Colors.BG_TERTIARY).pack(anchor=tk.W)
        
        current_votes_pref = current_preferences.get('prioritize_high_votes', False)
        votes_var = tk.BooleanVar(value=current_votes_pref)
        preference_vars['prioritize_high_votes'] = votes_var
        
        votes_checkbox = tk.Checkbutton(votes_frame, 
                                      text="Prioritize HIGH vote counts (heavily voted images)", 
                                      variable=votes_var,
                                      fg=Colors.TEXT_PRIMARY, bg=Colors.BG_TERTIARY,
                                      selectcolor=Colors.BG_PRIMARY, activebackground=Colors.BG_TERTIARY)
        votes_checkbox.pack(anchor=tk.W, padx=20)
        
        tk.Label(votes_frame, text="Unchecked = Prioritize LOW vote counts (lightly voted images)", 
                font=('Arial', 9, 'italic'), fg=Colors.TEXT_SECONDARY, bg=Colors.BG_TERTIARY).pack(anchor=tk.W, padx=20)
    
    def create_individual_weight_control(self, parent: tk.Frame, key: str, title: str, description: str,
                                       weight_vars: Dict, weight_labels: Dict, current_weights: Dict, side: str):
        """Create a single weight control widget."""
        # Frame for this weight
        weight_frame = tk.Frame(parent, bg=Colors.BG_TERTIARY)
        weight_frame.pack(fill=tk.X, pady=5)
        
        # Title and description
        tk.Label(weight_frame, text=title, font=('Arial', 10, 'bold'), 
                fg=Colors.TEXT_PRIMARY, bg=Colors.BG_TERTIARY).pack(anchor=tk.W)
        tk.Label(weight_frame, text=description, font=('Arial', 8, 'italic'), 
                fg=Colors.TEXT_SECONDARY, bg=Colors.BG_TERTIARY, wraplength=200).pack(anchor=tk.W)
        
        # Current value label
        current_value = current_weights.get(key, 0.25)
        value_label = tk.Label(weight_frame, text=f"Current: {current_value:.2f}", 
                             fg=Colors.TEXT_PRIMARY, bg=Colors.BG_TERTIARY)
        value_label.pack(anchor=tk.W)
        weight_labels[key] = value_label
        
        # Slider
        var = tk.DoubleVar(value=current_value)
        weight_vars[key] = var
        
        slider = tk.Scale(weight_frame, from_=0, to=1, resolution=0.05,
                        orient=tk.HORIZONTAL, variable=var,
                        command=lambda v, k=key, s=side: self.update_weight_label(k, s),
                        bg=Colors.BG_TERTIARY, fg=Colors.TEXT_PRIMARY, 
                        troughcolor=Colors.BG_PRIMARY, 
                        activebackground=Colors.BUTTON_SUCCESS if side == 'left' else Colors.BUTTON_INFO,
                        length=200)
        slider.pack(fill=tk.X, padx=10)
    
    def update_weight_label(self, key: str, side: str):
        """Update the label showing the current weight value."""
        if side == 'left':
            value = self.left_weight_vars[key].get()
            self.left_weight_labels[key].config(text=f"Current: {value:.2f}")
        else:
            value = self.right_weight_vars[key].get()
            self.right_weight_labels[key].config(text=f"Current: {value:.2f}")
        
        self.update_weight_display()
    
    def update_weight_display(self):
        """Update the total weight display and warnings for both sides."""
        # Update left side
        if self.left_weight_vars:
            left_total = sum(var.get() for var in self.left_weight_vars.values())
            if self.left_total_weight_label:
                self.left_total_weight_label.config(text=f"Total: {left_total:.2f}")
            
            if self.left_weight_warning_label:
                if abs(left_total - 1.0) > 0.01:
                    self.left_weight_warning_label.config(text="⚠️ Should sum to 1.0")
                else:
                    self.left_weight_warning_label.config(text="✓ Sums to 1.0")
        
        # Update right side
        if self.right_weight_vars:
            right_total = sum(var.get() for var in self.right_weight_vars.values())
            if self.right_total_weight_label:
                self.right_total_weight_label.config(text=f"Total: {right_total:.2f}")
            
            if self.right_weight_warning_label:
                if abs(right_total - 1.0) > 0.01:
                    self.right_weight_warning_label.config(text="⚠️ Should sum to 1.0")
                else:
                    self.right_weight_warning_label.config(text="✓ Sums to 1.0")
    
    def copy_left_to_right(self):
        """Copy left weights to right weights."""
        if self.left_weight_vars and self.right_weight_vars:
            for key in self.left_weight_vars:
                if key in self.right_weight_vars:
                    value = self.left_weight_vars[key].get()
                    self.right_weight_vars[key].set(value)
                    self.right_weight_labels[key].config(text=f"Current: {value:.2f}")
            self.update_weight_display()
    
    def copy_right_to_left(self):
        """Copy right weights to left weights."""
        if self.left_weight_vars and self.right_weight_vars:
            for key in self.right_weight_vars:
                if key in self.left_weight_vars:
                    value = self.right_weight_vars[key].get()
                    self.left_weight_vars[key].set(value)
                    self.left_weight_labels[key].config(text=f"Current: {value:.2f}")
            self.update_weight_display()
    
    def copy_left_preferences_to_right(self):
        """Copy left preferences to right preferences."""
        if self.left_preference_vars and self.right_preference_vars:
            for key in self.left_preference_vars:
                if key in self.right_preference_vars:
                    value = self.left_preference_vars[key].get()
                    self.right_preference_vars[key].set(value)
    
    def copy_right_preferences_to_left(self):
        """Copy right preferences to left preferences."""
        if self.left_preference_vars and self.right_preference_vars:
            for key in self.right_preference_vars:
                if key in self.left_preference_vars:
                    value = self.right_preference_vars[key].get()
                    self.left_preference_vars[key].set(value)
    
    def normalize_left_weights(self):
        """Normalize left weights to sum to 1.0."""
        if self.left_weight_vars:
            total = sum(var.get() for var in self.left_weight_vars.values())
            if total > 0:
                for key, var in self.left_weight_vars.items():
                    new_value = var.get() / total
                    var.set(new_value)
                    self.left_weight_labels[key].config(text=f"Current: {new_value:.2f}")
                self.update_weight_display()
    
    def normalize_right_weights(self):
        """Normalize right weights to sum to 1.0."""
        if self.right_weight_vars:
            total = sum(var.get() for var in self.right_weight_vars.values())
            if total > 0:
                for key, var in self.right_weight_vars.items():
                    new_value = var.get() / total
                    var.set(new_value)
                    self.right_weight_labels[key].config(text=f"Current: {new_value:.2f}")
                self.update_weight_display()
    
    def normalize_both_weights(self):
        """Normalize both left and right weights to sum to 1.0."""
        self.normalize_left_weights()
        self.normalize_right_weights()
    
    def reset_to_defaults(self):
        """Reset both weight sets to default values."""
        from config import Defaults
        
        # Reset left weights
        if self.left_weight_vars:
            for key, default_value in Defaults.LEFT_SELECTION_WEIGHTS.items():
                if key in self.left_weight_vars:
                    self.left_weight_vars[key].set(default_value)
                    self.left_weight_labels[key].config(text=f"Current: {default_value:.2f}")
        
        # Reset right weights
        if self.right_weight_vars:
            for key, default_value in Defaults.RIGHT_SELECTION_WEIGHTS.items():
                if key in self.right_weight_vars:
                    self.right_weight_vars[key].set(default_value)
                    self.right_weight_labels[key].config(text=f"Current: {default_value:.2f}")
        
        self.update_weight_display()
    
    def reset_preferences_to_defaults(self):
        """Reset both preference sets to default values."""
        from config import Defaults
        
        # Reset left preferences
        if self.left_preference_vars:
            for key, default_value in Defaults.LEFT_PRIORITY_PREFERENCES.items():
                if key in self.left_preference_vars:
                    self.left_preference_vars[key].set(default_value)
        
        # Reset right preferences
        if self.right_preference_vars:
            for key, default_value in Defaults.RIGHT_PRIORITY_PREFERENCES.items():
                if key in self.right_preference_vars:
                    self.right_preference_vars[key].set(default_value)
    
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
    
    def update_tier_std_display(self):
        """Update the tier standard deviation display."""
        if self.tier_std_var is not None:
            value = self.tier_std_var.get()
            self.tier_std_label.config(text=f"Current: {value:.2f}")
    
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
        """Apply the weight changes and preference changes and close the window."""
        # Update left weights in data manager
        if self.left_weight_vars:
            left_weights = {}
            for key, var in self.left_weight_vars.items():
                left_weights[key] = var.get()
            self.data_manager.set_left_weights(left_weights)
        
        # Update right weights in data manager
        if self.right_weight_vars:
            right_weights = {}
            for key, var in self.right_weight_vars.items():
                right_weights[key] = var.get()
            self.data_manager.set_right_weights(right_weights)
        
        # Update left preferences in data manager
        if self.left_preference_vars:
            left_preferences = {}
            for key, var in self.left_preference_vars.items():
                left_preferences[key] = var.get()
            self.data_manager.set_left_priority_preferences(left_preferences)
        
        # Update right preferences in data manager
        if self.right_preference_vars:
            right_preferences = {}
            for key, var in self.right_preference_vars.items():
                right_preferences[key] = var.get()
            self.data_manager.set_right_priority_preferences(right_preferences)
        
        # Update tier distribution parameter (ensure it exists)
        if not hasattr(self.data_manager, 'tier_distribution_std'):
            self.data_manager.tier_distribution_std = 1.5  # Set default if missing
        if self.tier_std_var is not None:
            self.data_manager.tier_distribution_std = self.tier_std_var.get()
        
        messagebox.showinfo("Success", "Settings updated successfully!\n\nLeft and right images will now be selected using their respective weight sets and priority preferences.")
        self.close_window()
    
    def close_window(self):
        """Handle window closing."""
        if self.window:
            self.window.destroy()
            self.window = None