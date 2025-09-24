"""Settings window with tier bounds system removed."""

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
        self.window.geometry("900x600")
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
        
        explanation_text = """The algorithm uses tier-overflow detection and confidence-based pairing:

1. TIER OVERFLOW: Identifies tiers with more images than expected based on normal distribution
2. CONFIDENCE SELECTION: Pairs low-confidence images with high-confidence images within overflowing tiers
3. TIER MOVEMENT: Images move freely between tiers based on voting results
4. FALLBACK SELECTION: Random selection when no tier overflow is detected

This creates a dynamic ranking system that focuses attention on uncertain image positions while allowing 
tiers to grow naturally based on the collection's quality distribution."""
        
        tk.Label(explanation_frame, text=explanation_text, 
                font=('Arial', 10), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY, 
                justify=tk.LEFT, wraplength=850).pack(padx=10, pady=5)
        
        # Settings sections
        self.create_tier_distribution_section(parent)
        self.create_overflow_detection_section(parent)
        self.create_status_section(parent)
        
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
        
        description_text = ("Controls the expected tier distribution shape. Lower values create tighter distribution around tier 0. "
                          "This affects overflow detection - tiers further from 0 are expected to have fewer images.")
        tk.Label(section, text=description_text, font=('Arial', 10, 'italic'), 
                fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY, wraplength=850, justify=tk.LEFT).pack(pady=5)
        
        # Tier distribution std dev
        tier_frame = tk.Frame(section, bg=Colors.BG_SECONDARY)
        tier_frame.pack(padx=20, pady=10)
        
        tk.Label(tier_frame, text="Standard Deviation", 
                font=('Arial', 11, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        current_value = self.data_manager.algorithm_settings.tier_distribution_std
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
                          "The algorithm prioritizes pairs from overflowing tiers to balance the distribution.")
        tk.Label(section, text=description_text, font=('Arial', 10, 'italic'), 
                fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY, wraplength=850, justify=tk.LEFT).pack(pady=5)
        
        controls_frame = tk.Frame(section, bg=Colors.BG_SECONDARY)
        controls_frame.pack(padx=20, pady=10)
        
        # Overflow threshold setting
        threshold_frame = tk.Frame(controls_frame, bg=Colors.BG_SECONDARY)
        threshold_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(threshold_frame, text="Overflow Threshold", 
                font=('Arial', 11, 'bold'), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        tk.Label(threshold_frame, text="Multiplier of expected count to trigger overflow (1.0 = any excess)", 
                font=('Arial', 9, 'italic'), fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        current_value = self.data_manager.algorithm_settings.overflow_threshold
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
        
        tk.Label(min_images_frame, text="Minimum number of images in a tier to consider it for overflow", 
                font=('Arial', 9, 'italic'), fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        current_value = self.data_manager.algorithm_settings.min_overflow_images
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
        """Create the status section showing current algorithm state."""
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
        """Update the status display with current algorithm information."""
        try:
            # Get current settings
            tier_std = self.tier_std_var.get() if self.tier_std_var else self.data_manager.algorithm_settings.tier_distribution_std
            overflow_threshold = self.overflow_threshold_var.get() if self.overflow_threshold_var else self.data_manager.algorithm_settings.overflow_threshold
            min_overflow = self.min_overflow_images_var.get() if self.min_overflow_images_var else self.data_manager.algorithm_settings.min_overflow_images
            
            # Get tier distribution
            tier_distribution = self.data_manager.get_tier_distribution()
            total_images = sum(tier_distribution.values())
            
            # Calculate expected vs actual for key tiers
            tier_analysis = []
            if tier_distribution and total_images > 0:
                for tier in sorted(tier_distribution.keys()):
                    actual_count = tier_distribution[tier]
                    
                    # Calculate expected proportion
                    density = math.exp(-(tier ** 2) / (2 * tier_std ** 2))
                    all_densities = [math.exp(-(t ** 2) / (2 * tier_std ** 2)) for t in tier_distribution.keys()]
                    total_density = sum(all_densities)
                    expected_proportion = density / total_density if total_density > 0 else 0
                    expected_count = expected_proportion * total_images
                    
                    # Check if overflowing
                    is_overflowing = (actual_count > expected_count * overflow_threshold and 
                                    actual_count >= min_overflow)
                    
                    tier_analysis.append({
                        'tier': tier,
                        'actual': actual_count,
                        'expected': expected_count,
                        'overflowing': is_overflowing
                    })
            
            # Format status text
            status_text = f"""Algorithm Configuration Status:

Tier Distribution Standard Deviation: {tier_std:.1f}
Overflow Threshold: {overflow_threshold:.1f}x expected count
Minimum Images for Overflow: {min_overflow}

Current Collection:
Total Active Images: {total_images}
Total Tiers in Use: {len(tier_distribution)}

Tier Analysis:"""
            
            if tier_analysis:
                overflowing_tiers = [t for t in tier_analysis if t['overflowing']]
                
                for analysis in tier_analysis[:10]:  # Show first 10 tiers
                    tier = analysis['tier']
                    actual = analysis['actual']
                    expected = analysis['expected']
                    overflow_status = " 🔥 OVERFLOWING" if analysis['overflowing'] else ""
                    
                    status_text += f"\n• Tier {tier:+2d}: {actual:3d} images (expected: {expected:4.1f}){overflow_status}"
                
                if len(tier_analysis) > 10:
                    status_text += f"\n... and {len(tier_analysis) - 10} more tiers"
                
                status_text += f"\n\nOverflowing Tiers: {len(overflowing_tiers)} (will be prioritized for voting)"
            else:
                status_text += "\nNo images loaded yet."
            
            status_text += f"\n\nNote: Tiers can grow freely - no bounds restrictions applied."
        
        except Exception as e:
            status_text = f"Error getting status: {e}"
        
        if hasattr(self, 'status_text_label'):
            self.status_text_label.config(text=status_text)
    
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
        
        preview_text += f"\nThis distribution determines when tiers are considered 'overflowing'."
        
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
        self.update_tier_std_display()
        self.update_overflow_threshold_display()
        self.update_min_overflow_images_display()
        self.update_status_display()
    
    def apply_changes(self):
        """Apply the setting changes."""
        # Apply algorithm settings
        if self.tier_std_var is not None:
            self.data_manager.algorithm_settings.tier_distribution_std = self.tier_std_var.get()
        if self.overflow_threshold_var is not None:
            self.data_manager.algorithm_settings.overflow_threshold = self.overflow_threshold_var.get()
        if self.min_overflow_images_var is not None:
            self.data_manager.algorithm_settings.min_overflow_images = self.min_overflow_images_var.get()
        
        messagebox.showinfo("Success", f"Settings updated successfully!\n\nChanges will take effect immediately and will be saved when you save your progress.")
        self.close_window()
    
    def close_window(self):
        """Handle window closing."""
        if self.window:
            self.window.destroy()
            self.window = None
