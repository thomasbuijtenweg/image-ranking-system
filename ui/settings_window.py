"""Enhanced Settings window with tier bounds configuration."""

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
        
        # Tier bounds settings
        self.tier_bounds_enabled_var = None
        self.tier_bounds_std_multiplier_var = None
        self.tier_bounds_std_multiplier_label = None
        self.tier_bounds_min_confidence_var = None
        self.tier_bounds_min_confidence_label = None
        self.tier_bounds_min_votes_var = None
        self.tier_bounds_min_votes_label = None
        self.tier_bounds_adaptive_var = None
        
        # Initialize new settings
        self._initialize_new_settings()
    
    def _initialize_new_settings(self):
        """Initialize new settings with default values if they don't exist."""
        # Ensure all tier bounds settings exist
        if not hasattr(self.data_manager, 'tier_bounds_enabled'):
            self.data_manager.tier_bounds_enabled = True
            print("Initialized tier_bounds_enabled to True")
        else:
            print(f"Found existing tier_bounds_enabled: {self.data_manager.tier_bounds_enabled}")
            
        if not hasattr(self.data_manager, 'tier_bounds_std_multiplier'):
            self.data_manager.tier_bounds_std_multiplier = 3.0
        if not hasattr(self.data_manager, 'tier_bounds_min_confidence'):
            self.data_manager.tier_bounds_min_confidence = 0.8
        if not hasattr(self.data_manager, 'tier_bounds_min_votes'):
            self.data_manager.tier_bounds_min_votes = 10
        if not hasattr(self.data_manager, 'tier_bounds_adaptive'):
            self.data_manager.tier_bounds_adaptive = True
        
        # Ensure existing settings exist
        if not hasattr(self.data_manager, 'overflow_threshold'):
            self.data_manager.overflow_threshold = 1.0
        if not hasattr(self.data_manager, 'min_overflow_images'):
            self.data_manager.min_overflow_images = 2
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
        self.window.geometry("900x900")
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
        
        tk.Label(explanation_frame, text="How the Algorithm Works", 
                font=('Arial', 14, 'bold'), fg=Colors.TEXT_SUCCESS, bg=Colors.BG_SECONDARY).pack(pady=5)
        
        explanation_text = """The algorithm uses tier-overflow detection and confidence-based pairing with intelligent tier bounds:

1. TIER BOUNDS: Prevents runaway tier inflation by limiting extreme tiers
2. CONFIDENCE GATING: Only high-confidence images (stable + many votes) can exceed bounds
3. ADAPTIVE SCALING: Bounds grow intelligently with collection size
4. ELEGANT FALLBACK: Images that can't move stay in current tier

This ensures a stable, bounded tier system while allowing truly exceptional images to reach extremes."""
        
        tk.Label(explanation_frame, text=explanation_text, 
                font=('Arial', 10), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY, 
                justify=tk.LEFT, wraplength=850).pack(padx=10, pady=5)
        
        # Settings sections
        self.create_tier_bounds_section(parent)
        self.create_tier_distribution_section(parent)
        self.create_overflow_detection_section(parent)
        self.create_status_section(parent)
        
        # Apply button
        tk.Button(parent, text="Apply Changes", 
                 command=self.apply_changes,
                 bg=Colors.BUTTON_SUCCESS, fg='white', font=('Arial', 12), relief=tk.FLAT).pack(pady=20)
    
    def create_tier_bounds_section(self, parent: tk.Frame):
        """Create the tier bounds settings section."""
        section = tk.Frame(parent, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=1)
        section.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(section, text="🎯 Tier Bounds (NEW)", 
                font=('Arial', 14, 'bold'), fg=Colors.TEXT_SUCCESS, bg=Colors.BG_SECONDARY).pack(pady=10)
        
        description_text = ("Intelligent tier bounds prevent runaway tier inflation while allowing exceptional images to reach extremes. "
                          "Images need high confidence (stability + votes) to exceed the bounds.")
        tk.Label(section, text=description_text, font=('Arial', 10, 'italic'), 
                fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY, wraplength=850, justify=tk.LEFT).pack(pady=5)
        
        controls_frame = tk.Frame(section, bg=Colors.BG_SECONDARY)
        controls_frame.pack(padx=20, pady=10)
        
        # Enable/disable tier bounds
        checkbox_frame = tk.Frame(controls_frame, bg=Colors.BG_SECONDARY)
        checkbox_frame.pack(fill=tk.X, pady=5)
        
        self.tier_bounds_enabled_var = tk.BooleanVar(value=getattr(self.data_manager, 'tier_bounds_enabled', True))
        
        # Create checkbox with proper styling to show check state
        checkbox = tk.Checkbutton(checkbox_frame, text="Enable Tier Bounds", 
                                 variable=self.tier_bounds_enabled_var,
                                 font=('Arial', 11, 'bold'), fg=Colors.TEXT_PRIMARY, 
                                 bg=Colors.BG_SECONDARY, 
                                 activebackground=Colors.BG_SECONDARY,
                                 selectcolor=Colors.BG_TERTIARY,  # Color when checked
                                 activeforeground=Colors.TEXT_PRIMARY,
                                 command=self.on_tier_bounds_enabled_change)
        checkbox.pack(anchor=tk.W)
        
        # Add status indicator
        self.tier_bounds_status_label = tk.Label(checkbox_frame, 
                                                text="Status: Enabled" if self.tier_bounds_enabled_var.get() else "Status: Disabled",
                                                font=('Arial', 9, 'italic'), 
                                                fg=Colors.TEXT_SUCCESS if self.tier_bounds_enabled_var.get() else Colors.TEXT_ERROR, 
                                                bg=Colors.BG_SECONDARY)
        self.tier_bounds_status_label.pack(anchor=tk.W, padx=20)
        
        # Adaptive bounds checkbox
        self.tier_bounds_adaptive_var = tk.BooleanVar(value=getattr(self.data_manager, 'tier_bounds_adaptive', True))
        adaptive_checkbox = tk.Checkbutton(checkbox_frame, text="Adaptive Bounds (grow with collection size)", 
                                          variable=self.tier_bounds_adaptive_var,
                                          font=('Arial', 10), fg=Colors.TEXT_SECONDARY, 
                                          bg=Colors.BG_SECONDARY, 
                                          activebackground=Colors.BG_SECONDARY,
                                          selectcolor=Colors.BG_TERTIARY,
                                          activeforeground=Colors.TEXT_SECONDARY)
        adaptive_checkbox.pack(anchor=tk.W, padx=20)
        
        # Standard deviation multiplier
        std_frame = tk.Frame(controls_frame, bg=Colors.BG_SECONDARY)
        std_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(std_frame, text="Bounds Size (Standard Deviations)", 
                font=('Arial', 11, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        tk.Label(std_frame, text="How many standard deviations from tier 0 to allow (3.0 = 99.7% containment)", 
                font=('Arial', 9, 'italic'), fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        current_value = getattr(self.data_manager, 'tier_bounds_std_multiplier', 3.0)
        self.tier_bounds_std_multiplier_label = tk.Label(std_frame, text=f"Current: {current_value:.1f} std devs", 
                                                       fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY)
        self.tier_bounds_std_multiplier_label.pack(anchor=tk.W)
        
        self.tier_bounds_std_multiplier_var = tk.DoubleVar(value=current_value)
        
        slider = tk.Scale(std_frame, from_=1.0, to=5.0, resolution=0.1,
                        orient=tk.HORIZONTAL, variable=self.tier_bounds_std_multiplier_var,
                        command=lambda v: self.update_tier_bounds_std_multiplier_display(),
                        bg=Colors.BG_SECONDARY, fg=Colors.TEXT_PRIMARY, 
                        troughcolor=Colors.BG_TERTIARY, activebackground=Colors.BUTTON_SUCCESS,
                        length=400)
        slider.pack(fill=tk.X, padx=20, pady=5)
        
        # Minimum confidence for bounds
        confidence_frame = tk.Frame(controls_frame, bg=Colors.BG_SECONDARY)
        confidence_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(confidence_frame, text="Minimum Confidence to Exceed Bounds", 
                font=('Arial', 11, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        tk.Label(confidence_frame, text="Images need this confidence level to go beyond bounds (0.8 = 80%)", 
                font=('Arial', 9, 'italic'), fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        current_value = getattr(self.data_manager, 'tier_bounds_min_confidence', 0.8)
        self.tier_bounds_min_confidence_label = tk.Label(confidence_frame, text=f"Current: {current_value:.1%}", 
                                                       fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY)
        self.tier_bounds_min_confidence_label.pack(anchor=tk.W)
        
        self.tier_bounds_min_confidence_var = tk.DoubleVar(value=current_value)
        
        slider = tk.Scale(confidence_frame, from_=0.5, to=0.95, resolution=0.05,
                        orient=tk.HORIZONTAL, variable=self.tier_bounds_min_confidence_var,
                        command=lambda v: self.update_tier_bounds_min_confidence_display(),
                        bg=Colors.BG_SECONDARY, fg=Colors.TEXT_PRIMARY, 
                        troughcolor=Colors.BG_TERTIARY, activebackground=Colors.BUTTON_SUCCESS,
                        length=400)
        slider.pack(fill=tk.X, padx=20, pady=5)
        
        # Minimum votes for bounds
        votes_frame = tk.Frame(controls_frame, bg=Colors.BG_SECONDARY)
        votes_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(votes_frame, text="Minimum Votes to Exceed Bounds", 
                font=('Arial', 11, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        tk.Label(votes_frame, text="Images need this many votes to go beyond bounds", 
                font=('Arial', 9, 'italic'), fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        current_value = getattr(self.data_manager, 'tier_bounds_min_votes', 10)
        self.tier_bounds_min_votes_label = tk.Label(votes_frame, text=f"Current: {current_value} votes", 
                                                  fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY)
        self.tier_bounds_min_votes_label.pack(anchor=tk.W)
        
        self.tier_bounds_min_votes_var = tk.IntVar(value=current_value)
        
        slider = tk.Scale(votes_frame, from_=5, to=50, resolution=1,
                        orient=tk.HORIZONTAL, variable=self.tier_bounds_min_votes_var,
                        command=lambda v: self.update_tier_bounds_min_votes_display(),
                        bg=Colors.BG_SECONDARY, fg=Colors.TEXT_PRIMARY, 
                        troughcolor=Colors.BG_TERTIARY, activebackground=Colors.BUTTON_SUCCESS,
                        length=400)
        slider.pack(fill=tk.X, padx=20, pady=5)
        
        # Buttons
        button_frame = tk.Frame(controls_frame, bg=Colors.BG_SECONDARY)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Preview Current Bounds", 
                 command=self.preview_tier_bounds,
                 bg=Colors.BUTTON_INFO, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Reset to Defaults", 
                 command=self.reset_tier_bounds_settings,
                 bg=Colors.BUTTON_NEUTRAL, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        # Debug button
        tk.Button(button_frame, text="Debug State", 
                 command=self.debug_tier_bounds_state,
                 bg=Colors.BUTTON_DANGER, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
    
    def create_tier_distribution_section(self, parent: tk.Frame):
        """Create the tier distribution settings section."""
        section = tk.Frame(parent, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=1)
        section.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(section, text="Tier Distribution", 
                font=('Arial', 14, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(pady=10)
        
        description_text = ("Controls how tiers should be distributed. Lower values create tighter distribution around tier 0. "
                          "This affects both the expected distribution and the tier bounds calculations.")
        tk.Label(section, text=description_text, font=('Arial', 10, 'italic'), 
                fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY, wraplength=850, justify=tk.LEFT).pack(pady=5)
        
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
    
    def create_overflow_detection_section(self, parent: tk.Frame):
        """Create the overflow detection settings section."""
        section = tk.Frame(parent, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=1)
        section.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(section, text="Tier Overflow Detection", 
                font=('Arial', 14, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(pady=10)
        
        description_text = ("Controls when a tier is considered 'overflowing' and needs attention. "
                          "The algorithm prioritizes pairs from overflowing tiers.")
        tk.Label(section, text=description_text, font=('Arial', 10, 'italic'), 
                fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY, wraplength=850, justify=tk.LEFT).pack(pady=5)
        
        controls_frame = tk.Frame(section, bg=Colors.BG_SECONDARY)
        controls_frame.pack(padx=20, pady=10)
        
        # Overflow threshold setting
        threshold_frame = tk.Frame(controls_frame, bg=Colors.BG_SECONDARY)
        threshold_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(threshold_frame, text="Overflow Threshold", 
                font=('Arial', 11, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
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
    
    def create_status_section(self, parent: tk.Frame):
        """Create the status section showing current tier bounds information."""
        section = tk.Frame(parent, bg=Colors.BG_TERTIARY, relief=tk.RAISED, borderwidth=1)
        section.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(section, text="📊 Current Status", 
                font=('Arial', 14, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_TERTIARY).pack(pady=10)
        
        # Status will be updated in update_status_display
        self.status_text_label = tk.Label(section, text="Loading status...", 
                                        font=('Arial', 10), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_TERTIARY, 
                                        justify=tk.LEFT, wraplength=850)
        self.status_text_label.pack(padx=10, pady=5)
        
        tk.Button(section, text="Refresh Status", 
                 command=self.update_status_display,
                 bg=Colors.BUTTON_INFO, fg='white', relief=tk.FLAT).pack(pady=10)
    
    def update_tier_bounds_std_multiplier_display(self):
        """Update the tier bounds standard deviation multiplier display."""
        if self.tier_bounds_std_multiplier_var is not None:
            value = self.tier_bounds_std_multiplier_var.get()
            self.tier_bounds_std_multiplier_label.config(text=f"Current: {value:.1f} std devs")
    
    def update_tier_bounds_min_confidence_display(self):
        """Update the tier bounds minimum confidence display."""
        if self.tier_bounds_min_confidence_var is not None:
            value = self.tier_bounds_min_confidence_var.get()
            self.tier_bounds_min_confidence_label.config(text=f"Current: {value:.1%}")
    
    def update_tier_bounds_min_votes_display(self):
        """Update the tier bounds minimum votes display."""
        if self.tier_bounds_min_votes_var is not None:
            value = self.tier_bounds_min_votes_var.get()
            self.tier_bounds_min_votes_label.config(text=f"Current: {value} votes")
    
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
    
    def update_status_display(self):
        """Update the status display with current tier bounds information."""
        try:
            # Temporarily apply current settings to get preview
            temp_enabled = self.tier_bounds_enabled_var.get()
            temp_std_mult = self.tier_bounds_std_multiplier_var.get()
            temp_min_conf = self.tier_bounds_min_confidence_var.get()
            temp_min_votes = self.tier_bounds_min_votes_var.get()
            temp_adaptive = self.tier_bounds_adaptive_var.get()
            
            # Save current settings
            old_enabled = getattr(self.data_manager, 'tier_bounds_enabled', True)
            old_std_mult = getattr(self.data_manager, 'tier_bounds_std_multiplier', 3.0)
            old_min_conf = getattr(self.data_manager, 'tier_bounds_min_confidence', 0.8)
            old_min_votes = getattr(self.data_manager, 'tier_bounds_min_votes', 10)
            old_adaptive = getattr(self.data_manager, 'tier_bounds_adaptive', True)
            
            # Temporarily set new values
            self.data_manager.tier_bounds_enabled = temp_enabled
            self.data_manager.tier_bounds_std_multiplier = temp_std_mult
            self.data_manager.tier_bounds_min_confidence = temp_min_conf
            self.data_manager.tier_bounds_min_votes = temp_min_votes
            self.data_manager.tier_bounds_adaptive = temp_adaptive
            
            # Get status
            bounds_info = self.data_manager.get_tier_bounds_info()
            
            # Restore old values
            self.data_manager.tier_bounds_enabled = old_enabled
            self.data_manager.tier_bounds_std_multiplier = old_std_mult
            self.data_manager.tier_bounds_min_confidence = old_min_conf
            self.data_manager.tier_bounds_min_votes = old_min_votes
            self.data_manager.tier_bounds_adaptive = old_adaptive
            
            if bounds_info['enabled']:
                status_text = f"""Current Tier Bounds Status (Preview):

Bounds Range: Tier {bounds_info['min_tier']:+d} to Tier {bounds_info['max_tier']:+d}
Total Images: {bounds_info['total_images']}
Images at Lower Bound: {bounds_info['images_at_min_bound']}
Images at Upper Bound: {bounds_info['images_at_max_bound']}
Images Qualified to Exceed Bounds: {bounds_info['qualified_for_bounds']}

Configuration:
• Standard Deviation Multiplier: {bounds_info['std_multiplier']:.1f}
• Minimum Confidence: {bounds_info['min_confidence']:.1%}
• Minimum Votes: {bounds_info['min_votes']}
• Adaptive Bounds: {'Yes' if bounds_info['adaptive'] else 'No'}

Status: {'✅ Tier bounds are active and managing tier growth' if bounds_info['enabled'] else '❌ Tier bounds are disabled'}"""
            else:
                status_text = "Tier bounds are disabled. Tiers can grow indefinitely."
        
        except Exception as e:
            status_text = f"Error getting status: {e}"
        
        if hasattr(self, 'status_text_label'):
            self.status_text_label.config(text=status_text)
    
    def on_tier_bounds_enabled_change(self):
        """Handle tier bounds enabled/disabled change."""
        enabled = self.tier_bounds_enabled_var.get()
        
        # Update status label
        if hasattr(self, 'tier_bounds_status_label'):
            self.tier_bounds_status_label.config(
                text="Status: Enabled" if enabled else "Status: Disabled",
                fg=Colors.TEXT_SUCCESS if enabled else Colors.TEXT_ERROR
            )
        
        # Update overall status display
        self.update_status_display()
    
    def debug_tier_bounds_state(self):
        """Debug function to show current state of all tier bounds variables."""
        try:
            debug_info = f"""DEBUG: Tier Bounds State
            
UI Variables:
• tier_bounds_enabled_var: {self.tier_bounds_enabled_var.get() if self.tier_bounds_enabled_var else 'None'}
• tier_bounds_std_multiplier_var: {self.tier_bounds_std_multiplier_var.get() if self.tier_bounds_std_multiplier_var else 'None'}
• tier_bounds_min_confidence_var: {self.tier_bounds_min_confidence_var.get() if self.tier_bounds_min_confidence_var else 'None'}
• tier_bounds_min_votes_var: {self.tier_bounds_min_votes_var.get() if self.tier_bounds_min_votes_var else 'None'}
• tier_bounds_adaptive_var: {self.tier_bounds_adaptive_var.get() if self.tier_bounds_adaptive_var else 'None'}

Data Manager Attributes:
• tier_bounds_enabled: {getattr(self.data_manager, 'tier_bounds_enabled', 'NOT SET')}
• tier_bounds_std_multiplier: {getattr(self.data_manager, 'tier_bounds_std_multiplier', 'NOT SET')}
• tier_bounds_min_confidence: {getattr(self.data_manager, 'tier_bounds_min_confidence', 'NOT SET')}
• tier_bounds_min_votes: {getattr(self.data_manager, 'tier_bounds_min_votes', 'NOT SET')}
• tier_bounds_adaptive: {getattr(self.data_manager, 'tier_bounds_adaptive', 'NOT SET')}

Status Label Text: {self.tier_bounds_status_label.cget('text') if hasattr(self, 'tier_bounds_status_label') else 'NOT SET'}"""
            
            messagebox.showinfo("Debug Info", debug_info)
        except Exception as e:
            messagebox.showerror("Debug Error", f"Error getting debug info: {e}")
    
    def preview_tier_bounds(self):
        """Show a preview of the current tier bounds."""
        try:
            # Get current settings
            enabled = self.tier_bounds_enabled_var.get()
            std_mult = self.tier_bounds_std_multiplier_var.get()
            min_conf = self.tier_bounds_min_confidence_var.get()
            min_votes = self.tier_bounds_min_votes_var.get()
            adaptive = self.tier_bounds_adaptive_var.get()
            
            if not enabled:
                messagebox.showinfo("Tier Bounds Preview", "Tier bounds are disabled. Tiers can grow indefinitely.")
                return
            
            # Calculate bounds
            tier_std = self.tier_std_var.get()
            base_bound = int(tier_std * std_mult)
            
            preview_text = f"Tier Bounds Preview:\n\n"
            preview_text += f"Base Bounds: Tier {-base_bound:+d} to Tier {+base_bound:+d}\n"
            preview_text += f"(Based on {std_mult:.1f} × {tier_std:.1f} std dev)\n\n"
            
            if adaptive:
                total_images = len(self.data_manager.image_stats)
                adaptive_bonus = int(math.log10(max(total_images, 10)) - 2) if total_images > 100 else 0
                preview_text += f"Adaptive Bonus: +{adaptive_bonus} tiers (collection size: {total_images})\n"
                preview_text += f"Final Bounds: Tier {-base_bound-adaptive_bonus:+d} to Tier {+base_bound+adaptive_bonus:+d}\n\n"
            
            preview_text += f"Qualification Requirements:\n"
            preview_text += f"• Minimum Confidence: {min_conf:.1%}\n"
            preview_text += f"• Minimum Votes: {min_votes}\n\n"
            
            preview_text += f"Effect: Images within bounds move freely.\n"
            preview_text += f"Images at bounds need high confidence to move further."
            
            messagebox.showinfo("Tier Bounds Preview", preview_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error previewing tier bounds: {e}")
    
    def reset_tier_bounds_settings(self):
        """Reset tier bounds settings to defaults."""
        self.tier_bounds_enabled_var.set(True)
        self.tier_bounds_std_multiplier_var.set(3.0)
        self.tier_bounds_min_confidence_var.set(0.8)
        self.tier_bounds_min_votes_var.set(10)
        self.tier_bounds_adaptive_var.set(True)
        
        # Update status label
        if hasattr(self, 'tier_bounds_status_label'):
            self.tier_bounds_status_label.config(
                text="Status: Enabled",
                fg=Colors.TEXT_SUCCESS
            )
        
        self.update_all_displays()
    
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
    
    def update_all_displays(self):
        """Update all setting displays."""
        self.update_tier_bounds_std_multiplier_display()
        self.update_tier_bounds_min_confidence_display()
        self.update_tier_bounds_min_votes_display()
        self.update_tier_std_display()
        self.update_overflow_threshold_display()
        self.update_min_overflow_images_display()
        self.update_status_display()
    
    def apply_changes(self):
        """Apply the setting changes."""
        # Apply tier bounds settings
        if self.tier_bounds_enabled_var is not None:
            self.data_manager.tier_bounds_enabled = self.tier_bounds_enabled_var.get()
        if self.tier_bounds_std_multiplier_var is not None:
            self.data_manager.tier_bounds_std_multiplier = self.tier_bounds_std_multiplier_var.get()
        if self.tier_bounds_min_confidence_var is not None:
            self.data_manager.tier_bounds_min_confidence = self.tier_bounds_min_confidence_var.get()
        if self.tier_bounds_min_votes_var is not None:
            self.data_manager.tier_bounds_min_votes = self.tier_bounds_min_votes_var.get()
        if self.tier_bounds_adaptive_var is not None:
            self.data_manager.tier_bounds_adaptive = self.tier_bounds_adaptive_var.get()
        
        # Apply existing settings
        if self.tier_std_var is not None:
            self.data_manager.tier_distribution_std = self.tier_std_var.get()
        if self.overflow_threshold_var is not None:
            self.data_manager.overflow_threshold = self.overflow_threshold_var.get()
        if self.min_overflow_images_var is not None:
            self.data_manager.min_overflow_images = self.min_overflow_images_var.get()
        
        bounds_status = "enabled" if self.data_manager.tier_bounds_enabled else "disabled"
        messagebox.showinfo("Success", f"Settings updated successfully!\n\nTier bounds are now {bounds_status}.\nChanges will take effect immediately and will be saved when you save your progress.")
        self.close_window()
    
    def close_window(self):
        """Handle window closing."""
        if self.window:
            self.window.destroy()
            self.window = None
