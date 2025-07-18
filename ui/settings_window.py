"""Settings window for the Image Ranking System - Simplified square root approach."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict
import math

from config import Colors


class SettingsWindow:
    """Window for configuring system settings and algorithm parameters."""
    
    def __init__(self, parent: tk.Tk, data_manager):
        self.parent = parent
        self.data_manager = data_manager
        self.window = None
        
        # Current algorithm settings
        self.tier_std_var = None
        self.tier_std_label = None
        self.overflow_threshold_var = None
        self.overflow_threshold_label = None
        self.min_overflow_images_var = None
        self.min_overflow_images_label = None
        
        # Add new settings to data_manager if they don't exist
        self._initialize_new_settings()
    
    def _initialize_new_settings(self):
        """Initialize new settings with default values if they don't exist."""
        # Add new algorithm parameters with defaults
        if not hasattr(self.data_manager, 'overflow_threshold'):
            self.data_manager.overflow_threshold = 1.0  # 100% of expected count
        
        if not hasattr(self.data_manager, 'min_overflow_images'):
            self.data_manager.min_overflow_images = 2  # Minimum images needed for overflow
        
        # Ensure tier distribution std exists
        if not hasattr(self.data_manager, 'tier_distribution_std'):
            self.data_manager.tier_distribution_std = 1.5
    
    def show(self):
        """Show the settings window."""
        if self.window is None or not self.window.winfo_exists():
            self.create_window()
        else:
            self.window.lift()
            self.window.focus_force()
    
    def create_window(self):
        """Create the settings window."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Algorithm Settings")
        self.window.geometry("800x700")
        self.window.configure(bg=Colors.BG_PRIMARY)
        
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # Create scrollable content
        main_frame = tk.Frame(self.window, bg=Colors.BG_PRIMARY)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(main_frame, bg=Colors.BG_PRIMARY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=Colors.BG_PRIMARY)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        self.create_settings_content(scrollable_frame)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.update_all_displays()
    
    def create_settings_content(self, parent: tk.Frame):
        """Create the main settings content."""
        # Header
        header_frame = tk.Frame(parent, bg=Colors.BG_PRIMARY)
        header_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(header_frame, text="Algorithm Settings", 
                font=('Arial', 16, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_PRIMARY).pack()
        
        # Algorithm explanation
        explanation_frame = tk.Frame(parent, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=1)
        explanation_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(explanation_frame, text="How the Current Algorithm Works", 
                font=('Arial', 14, 'bold'), fg=Colors.TEXT_SUCCESS, bg=Colors.BG_SECONDARY).pack(pady=5)
        
        explanation_text = """The algorithm uses a pure tier-overflow and confidence-based approach:

1. TIER OVERFLOW DETECTION: Finds tiers with more images than expected based on normal distribution
2. CONFIDENCE CALCULATION: Uses simplified formula: confidence = 1 / (1 + tier_stability / sqrt(votes))
3. ELEGANT SIMPLICITY: Vote count is automatically factored into confidence via square root scaling
4. INTELLIGENT PAIRING: Left side gets lowest confidence image, right side gets high confidence + low recency
5. FALLBACK: Uses random selection when no overflowing tiers are found

This approach eliminates redundant vote counting and uses a single, mathematically sound confidence metric."""
        
        tk.Label(explanation_frame, text=explanation_text, 
                font=('Arial', 10), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY, 
                justify=tk.LEFT, wraplength=750).pack(padx=10, pady=5)
        
        # Settings sections
        self.create_tier_distribution_section(parent)
        self.create_overflow_detection_section(parent)
        self.create_deprecated_settings_section(parent)
        
        # Apply button
        tk.Button(parent, text="Apply Changes", 
                 command=self.apply_changes,
                 bg=Colors.BUTTON_SUCCESS, fg='white', font=('Arial', 12), relief=tk.FLAT).pack(pady=20)
    
    def create_tier_distribution_section(self, parent: tk.Frame):
        """Create the tier distribution settings section."""
        section = tk.Frame(parent, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=1)
        section.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(section, text="Tier Distribution", 
                font=('Arial', 14, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(pady=10)
        
        description_text = ("Controls how tiers should be distributed. Lower values create tighter distribution around tier 0. "
                          "Higher values spread images more evenly across tiers.")
        tk.Label(section, text=description_text, font=('Arial', 10, 'italic'), 
                fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY, wraplength=750, justify=tk.LEFT).pack(pady=5)
        
        # Tier distribution std dev
        tier_frame = tk.Frame(section, bg=Colors.BG_SECONDARY)
        tier_frame.pack(padx=20, pady=10)
        
        tk.Label(tier_frame, text="Standard Deviation", 
                font=('Arial', 11, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        current_value = getattr(self.data_manager, 'tier_distribution_std', 1.5)
        self.tier_std_label = tk.Label(tier_frame, text=f"Current: {current_value:.2f}", 
                                      fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY)
        self.tier_std_label.pack(anchor=tk.W)
        
        self.tier_std_var = tk.DoubleVar(value=current_value)
        
        slider = tk.Scale(tier_frame, from_=0.5, to=3.0, resolution=0.1,
                        orient=tk.HORIZONTAL, variable=self.tier_std_var,
                        command=lambda v: self.update_tier_std_display(),
                        bg=Colors.BG_SECONDARY, fg=Colors.TEXT_PRIMARY, 
                        troughcolor=Colors.BG_TERTIARY, activebackground=Colors.BUTTON_INFO,
                        length=400)
        slider.pack(fill=tk.X, padx=20, pady=5)
        
        button_frame = tk.Frame(tier_frame, bg=Colors.BG_SECONDARY)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Preview Distribution", 
                 command=self.preview_distribution,
                 bg=Colors.BUTTON_INFO, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Reset to Default (1.5)", 
                 command=lambda: self.reset_setting(self.tier_std_var, 1.5, self.update_tier_std_display),
                 bg=Colors.BUTTON_NEUTRAL, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
    
    def create_confidence_calculation_section(self, parent: tk.Frame):
        """Create the confidence calculation settings section."""
        section = tk.Frame(parent, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=1)
        section.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(section, text="Confidence Calculation", 
                font=('Arial', 14, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(pady=10)
        
        description_text = ("Image confidence combines tier stability and vote count using the simplified approach: "
                          "stability_confidence = 1 / (1 + tier_stability / sqrt(votes)). "
                          "Left side gets lowest confidence images, right side gets high confidence images.")
        tk.Label(section, text=description_text, font=('Arial', 10, 'italic'), 
                fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY, wraplength=750, justify=tk.LEFT).pack(pady=5)
        
        controls_frame = tk.Frame(section, bg=Colors.BG_SECONDARY)
        controls_frame.pack(padx=20, pady=10)
        
        # Vote scale setting
        vote_frame = tk.Frame(controls_frame, bg=Colors.BG_SECONDARY)
        vote_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(vote_frame, text="Vote Count Scale", 
                font=('Arial', 11, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        tk.Label(vote_frame, text="How many votes = full confidence from vote count", 
                font=('Arial', 9, 'italic'), fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        current_value = getattr(self.data_manager, 'confidence_vote_scale', 20.0)
        self.confidence_vote_scale_label = tk.Label(vote_frame, text=f"Current: {current_value:.0f} votes", 
                                                   fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY)
        self.confidence_vote_scale_label.pack(anchor=tk.W)
        
        self.confidence_vote_scale_var = tk.DoubleVar(value=current_value)
        
        slider = tk.Scale(vote_frame, from_=5, to=50, resolution=1,
                        orient=tk.HORIZONTAL, variable=self.confidence_vote_scale_var,
                        command=lambda v: self.update_confidence_vote_scale_display(),
                        bg=Colors.BG_SECONDARY, fg=Colors.TEXT_PRIMARY, 
                        troughcolor=Colors.BG_TERTIARY, activebackground=Colors.BUTTON_SUCCESS,
                        length=400)
        slider.pack(fill=tk.X, padx=20, pady=5)
        
        # Balance setting
        balance_frame = tk.Frame(controls_frame, bg=Colors.BG_SECONDARY)
        balance_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(balance_frame, text="Stability vs Vote Count Balance", 
                font=('Arial', 11, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        tk.Label(balance_frame, text="0.0 = only stability matters, 1.0 = only vote count matters", 
                font=('Arial', 9, 'italic'), fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        current_value = getattr(self.data_manager, 'confidence_balance', 0.5)
        self.confidence_balance_label = tk.Label(balance_frame, text=f"Current: {current_value:.2f} (balanced)", 
                                               fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY)
        self.confidence_balance_label.pack(anchor=tk.W)
        
        self.confidence_balance_var = tk.DoubleVar(value=current_value)
        
        slider = tk.Scale(balance_frame, from_=0.0, to=1.0, resolution=0.05,
                        orient=tk.HORIZONTAL, variable=self.confidence_balance_var,
                        command=lambda v: self.update_confidence_balance_display(),
                        bg=Colors.BG_SECONDARY, fg=Colors.TEXT_PRIMARY, 
                        troughcolor=Colors.BG_TERTIARY, activebackground=Colors.BUTTON_SUCCESS,
                        length=400)
        slider.pack(fill=tk.X, padx=20, pady=5)
        
        # Reset button
        tk.Button(controls_frame, text="Reset Confidence Settings to Defaults", 
                 command=self.reset_confidence_settings,
                 bg=Colors.BUTTON_NEUTRAL, fg='white', relief=tk.FLAT).pack(pady=10)
    
    def create_overflow_detection_section(self, parent: tk.Frame):
        """Create the overflow detection settings section."""
        section = tk.Frame(parent, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=1)
        section.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(section, text="Tier Overflow Detection", 
                font=('Arial', 14, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(pady=10)
        
        description_text = ("Controls when a tier is considered 'overflowing' and needs attention. "
                          "The algorithm prioritizes pairs from overflowing tiers.")
        tk.Label(section, text=description_text, font=('Arial', 10, 'italic'), 
                fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY, wraplength=750, justify=tk.LEFT).pack(pady=5)
        
        controls_frame = tk.Frame(section, bg=Colors.BG_SECONDARY)
        controls_frame.pack(padx=20, pady=10)
        
        # Overflow threshold setting
        threshold_frame = tk.Frame(controls_frame, bg=Colors.BG_SECONDARY)
        threshold_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(threshold_frame, text="Overflow Threshold", 
                font=('Arial', 11, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        tk.Label(threshold_frame, text="Multiplier of expected count to trigger overflow (1.0 = 100% of expected)", 
                font=('Arial', 9, 'italic'), fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        current_value = getattr(self.data_manager, 'overflow_threshold', 1.0)
        self.overflow_threshold_label = tk.Label(threshold_frame, text=f"Current: {current_value:.2f}x expected", 
                                               fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY)
        self.overflow_threshold_label.pack(anchor=tk.W)
        
        self.overflow_threshold_var = tk.DoubleVar(value=current_value)
        
        slider = tk.Scale(threshold_frame, from_=0.5, to=2.0, resolution=0.1,
                        orient=tk.HORIZONTAL, variable=self.overflow_threshold_var,
                        command=lambda v: self.update_overflow_threshold_display(),
                        bg=Colors.BG_SECONDARY, fg=Colors.TEXT_PRIMARY, 
                        troughcolor=Colors.BG_TERTIARY, activebackground=Colors.BUTTON_WARNING,
                        length=400)
        slider.pack(fill=tk.X, padx=20, pady=5)
        
        # Minimum images setting
        min_images_frame = tk.Frame(controls_frame, bg=Colors.BG_SECONDARY)
        min_images_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(min_images_frame, text="Minimum Images for Overflow", 
                font=('Arial', 11, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        tk.Label(min_images_frame, text="Minimum number of images needed in a tier to consider it for overflow", 
                font=('Arial', 9, 'italic'), fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        current_value = getattr(self.data_manager, 'min_overflow_images', 2)
        self.min_overflow_images_label = tk.Label(min_images_frame, text=f"Current: {current_value} images", 
                                                fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY)
        self.min_overflow_images_label.pack(anchor=tk.W)
        
        self.min_overflow_images_var = tk.IntVar(value=current_value)
        
        slider = tk.Scale(min_images_frame, from_=2, to=10, resolution=1,
                        orient=tk.HORIZONTAL, variable=self.min_overflow_images_var,
                        command=lambda v: self.update_min_overflow_images_display(),
                        bg=Colors.BG_SECONDARY, fg=Colors.TEXT_PRIMARY, 
                        troughcolor=Colors.BG_TERTIARY, activebackground=Colors.BUTTON_WARNING,
                        length=400)
        slider.pack(fill=tk.X, padx=20, pady=5)
        
        # Reset button
        tk.Button(controls_frame, text="Reset Overflow Settings to Defaults", 
                 command=self.reset_overflow_settings,
                 bg=Colors.BUTTON_NEUTRAL, fg='white', relief=tk.FLAT).pack(pady=10)
    
    def create_deprecated_settings_section(self, parent: tk.Frame):
        """Create a section explaining deprecated settings."""
        section = tk.Frame(parent, bg=Colors.BG_TERTIARY, relief=tk.RAISED, borderwidth=1)
        section.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(section, text="⚠️ Deprecated Settings", 
                font=('Arial', 14, 'bold'), fg=Colors.TEXT_ERROR, bg=Colors.BG_TERTIARY).pack(pady=10)
        
        explanation_text = """The following settings from previous versions are no longer used:

• Selection Weights (recency, low_votes, instability, tier_size)
• Priority Preferences (prioritize_high_stability, prioritize_high_votes)
• Minimum Votes for Stability (replaced by square root scaling)
• Confidence Vote Scale (redundant with square root scaling)
• Confidence Balance (no longer needed with pure square root approach)

These have been replaced by the pure square root confidence algorithm above. Your old settings 
are still saved in your data files for compatibility, but they no longer affect how pairs are selected."""
        
        tk.Label(section, text=explanation_text, 
                font=('Arial', 10), fg=Colors.TEXT_SECONDARY, bg=Colors.BG_TERTIARY, 
                justify=tk.LEFT, wraplength=750).pack(padx=10, pady=5)
        
        # Option to clean up old settings
        tk.Button(section, text="Clean Up Deprecated Settings from Save Files", 
                 command=self.clean_deprecated_settings,
                 bg=Colors.BUTTON_DANGER, fg='white', relief=tk.FLAT).pack(pady=10)
    
    def update_tier_std_display(self):
        """Update the tier standard deviation display."""
        if self.tier_std_var is not None:
            value = self.tier_std_var.get()
            self.tier_std_label.config(text=f"Current: {value:.2f}")
    
    def update_overflow_threshold_display(self):
        """Update the overflow threshold display."""
        if self.overflow_threshold_var is not None:
            value = self.overflow_threshold_var.get()
            self.overflow_threshold_label.config(text=f"Current: {value:.2f}x expected")
    
    def update_min_overflow_images_display(self):
        """Update the minimum overflow images display."""
        if self.min_overflow_images_var is not None:
            value = self.min_overflow_images_var.get()
            self.min_overflow_images_label.config(text=f"Current: {value} images")
    
    def update_all_displays(self):
        """Update all setting displays."""
        self.update_tier_std_display()
        self.update_overflow_threshold_display()
        self.update_min_overflow_images_display()
    
    def reset_setting(self, var, default_value, update_func):
        """Reset a single setting to its default value."""
        var.set(default_value)
        update_func()
    
    def reset_overflow_settings(self):
        """Reset overflow detection settings to defaults."""
        self.overflow_threshold_var.set(1.0)
        self.min_overflow_images_var.set(2)
        self.update_overflow_threshold_display()
        self.update_min_overflow_images_display()
    
    def preview_distribution(self):
        """Show a preview of the tier distribution."""
        std_dev = self.tier_std_var.get()
        
        tiers = list(range(-5, 6))
        proportions = []
        
        for tier in tiers:
            density = math.exp(-(tier ** 2) / (2 * std_dev ** 2))
            proportions.append(density)
        
        total_density = sum(proportions)
        normalized_proportions = [p / total_density for p in proportions]
        
        preview_text = f"Expected Distribution (std dev = {std_dev:.1f}):\n\n"
        
        for tier, proportion in zip(tiers, normalized_proportions):
            percentage = proportion * 100
            bar_length = int(percentage * 2)
            bar = "█" * bar_length
            preview_text += f"Tier {tier:+2d}: {percentage:5.1f}% {bar}\n"
        
        messagebox.showinfo("Tier Distribution Preview", preview_text)
    
    def clean_deprecated_settings(self):
        """Clean up deprecated settings from the data manager."""
        removed_settings = []
        
        # Remove old weight manager settings from data_manager
        if hasattr(self.data_manager, 'weight_manager'):
            removed_settings.append("Weight Manager")
            # Don't actually remove it to maintain compatibility, just note it
        
        # Check for old-style weights
        old_attrs = ['left_weights', 'right_weights', 'left_priority_preferences', 'right_priority_preferences']
        for attr in old_attrs:
            if hasattr(self.data_manager, attr):
                removed_settings.append(attr)
        
        # Note removed confidence settings
        if hasattr(self.data_manager, 'confidence_vote_scale'):
            removed_settings.append("confidence_vote_scale (redundant with square root scaling)")
        if hasattr(self.data_manager, 'confidence_balance'):
            removed_settings.append("confidence_balance (no longer needed)")
        if hasattr(self.data_manager, 'min_votes_for_stability'):
            removed_settings.append("min_votes_for_stability (replaced by square root scaling)")
        
        if removed_settings:
            message = f"The following deprecated settings are still in your data files:\n\n"
            message += "\n".join(f"• {setting}" for setting in removed_settings)
            message += "\n\nThese settings no longer affect the algorithm but are kept for compatibility."
            message += "\nYour new settings will be saved when you save your progress."
        else:
            message = "No deprecated settings found in your current data."
        
        messagebox.showinfo("Deprecated Settings", message)
    
    def apply_changes(self):
        """Apply the setting changes."""
        # Apply tier distribution std
        if self.tier_std_var is not None:
            self.data_manager.tier_distribution_std = self.tier_std_var.get()
        
        # Apply overflow detection settings
        if self.overflow_threshold_var is not None:
            self.data_manager.overflow_threshold = self.overflow_threshold_var.get()
        
        if self.min_overflow_images_var is not None:
            self.data_manager.min_overflow_images = self.min_overflow_images_var.get()
        
        messagebox.showinfo("Success", "Settings updated successfully!\n\nThese changes will take effect immediately and will be saved when you save your progress.")
        self.close_window()
    
    def close_window(self):
        """Handle window closing."""
        if self.window:
            self.window.destroy()
            self.window = None
