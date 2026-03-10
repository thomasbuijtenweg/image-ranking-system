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
        
        # Similarity index UI state
        self._sim_build_thread = None
        self._sim_progress_label = None
        self._sim_status_label = None
        self._sim_build_btn = None
        self._sim_update_btn = None

        # Target count / cutline UI state
        self._target_count_var        = None
        self._cutline_buffer_var      = None
        self._zone_base_votes_var     = None
        self._zone_votes_per_tier_var = None
        self._cutline_preview_label   = None
    
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
        self.create_target_count_section(parent)
        self.create_similarity_section(parent)
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
        self.update_cutline_preview_display()
        self.update_similarity_status_display()
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

        # Apply cutline settings
        if self._target_count_var is not None:
            self.data_manager.algorithm_settings.set_value(
                'target_count', int(self._target_count_var.get()))
        if self._cutline_buffer_var is not None:
            self.data_manager.algorithm_settings.set_value(
                'cutline_buffer_tiers', int(self._cutline_buffer_var.get()))
        if self._zone_base_votes_var is not None:
            self.data_manager.algorithm_settings.set_value(
                'zone_base_votes', int(self._zone_base_votes_var.get()))
        if self._zone_votes_per_tier_var is not None:
            self.data_manager.algorithm_settings.set_value(
                'zone_votes_per_tier', round(float(self._zone_votes_per_tier_var.get()), 2))

        messagebox.showinfo("Success",
            "Settings updated successfully!\n\n"
            "Changes will take effect immediately and will be saved when you save your progress.")
        self.close_window()
    
    def create_similarity_section(self, parent: tk.Frame):
        """Create the visual similarity index section."""
        section = tk.Frame(parent, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=1)
        section.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(section, text="Visual Similarity Index (CLIP)",
                 font=('Arial', 14, 'bold'), fg=Colors.TEXT_PRIMARY,
                 bg=Colors.BG_SECONDARY).pack(pady=10)

        desc = ("When the index is built, the algorithm prefers pairing visually similar images "
                "together (30% similarity + 40% recency + 30% confidence). "
                "Without an index the original weights are used (60% recency + 40% confidence).\n"
                "Building takes 5–15 min for large datasets on CPU (seconds on GPU). "
                "Use 'Update' to add only newly added images.")
        tk.Label(section, text=desc, font=('Arial', 10, 'italic'),
                 fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY,
                 wraplength=850, justify=tk.LEFT).pack(padx=10, pady=5)

        # Status line
        self._sim_status_label = tk.Label(section, text="Status: checking…",
                                          font=('Arial', 10), fg=Colors.TEXT_PRIMARY,
                                          bg=Colors.BG_SECONDARY)
        self._sim_status_label.pack(padx=10, anchor=tk.W)

        # Progress line (hidden until a build starts)
        self._sim_progress_label = tk.Label(section, text="",
                                             font=('Arial', 10), fg=Colors.TEXT_WARNING,
                                             bg=Colors.BG_SECONDARY)
        self._sim_progress_label.pack(padx=10, anchor=tk.W)

        # Buttons
        btn_frame = tk.Frame(section, bg=Colors.BG_SECONDARY)
        btn_frame.pack(pady=10)

        self._sim_build_btn = tk.Button(btn_frame, text="Build Full Index",
                                         command=self._start_build_index,
                                         bg=Colors.BUTTON_INFO, fg='white',
                                         font=('Arial', 11), relief=tk.FLAT, width=18)
        self._sim_build_btn.pack(side=tk.LEFT, padx=5)

        self._sim_update_btn = tk.Button(btn_frame, text="Update Index (new images only)",
                                          command=self._start_update_index,
                                          bg=Colors.BUTTON_NEUTRAL, fg='white',
                                          font=('Arial', 11), relief=tk.FLAT, width=28)
        self._sim_update_btn.pack(side=tk.LEFT, padx=5)

        self.update_similarity_status_display()

    def update_similarity_status_display(self):
        """Refresh the similarity status label."""
        if self._sim_status_label is None:
            return

        sm = self.data_manager.similarity_manager
        folder = self.data_manager.image_folder

        if not folder:
            self._sim_status_label.config(
                text="Status: No image folder loaded yet.", fg=Colors.TEXT_SECONDARY)
            return

        total_images = len(self.data_manager.image_stats)
        if sm.is_ready:
            missing = sm.count_missing(list(self.data_manager.image_stats.keys()))
            disc_total = sum(len(v) for v in sm.discovered_vocab.values()) if hasattr(sm, 'discovered_vocab') else 0
            disc_info = f", {disc_total} discovered vocab terms" if disc_total else ""
            colour = Colors.TEXT_SUCCESS if missing == 0 else Colors.TEXT_WARNING
            self._sim_status_label.config(
                text=f"Status: ✅ Index ready — {len(sm.filenames)} embeddings"
                     f"{disc_info}"
                     f"{' (' + str(missing) + ' image(s) not yet indexed)' if missing else ' — all images covered'}",
                fg=colour)
        else:
            self._sim_status_label.config(
                text=f"Status: ⚠️  No index — {total_images} images need embedding. "
                     f"Click 'Build Full Index' to start.",
                fg=Colors.TEXT_WARNING)

    def _get_image_list(self):
        """Return a list of all image filenames currently tracked by the data manager."""
        return list(self.data_manager.image_stats.keys())

    def _get_prompt_lookup(self):
        """Return {filename: prompt} for all tracked images."""
        return {
            name: (stats.get('prompt') or '')
            for name, stats in self.data_manager.image_stats.items()
        }

    def _start_build_index(self):
        """Kick off a full index build in the background."""
        folder = self.data_manager.image_folder
        if not folder:
            messagebox.showwarning("No Folder", "Please load an image folder first.")
            return

        if self._sim_build_thread and self._sim_build_thread.is_alive():
            messagebox.showinfo("In Progress", "Index build is already running.")
            return

        self._sim_build_btn.config(state=tk.DISABLED)
        self._sim_update_btn.config(state=tk.DISABLED)
        self._sim_progress_label.config(text="Starting build…")

        def progress(current, total, name):
            if self.window and self.window.winfo_exists():
                pct = int(current / max(total, 1) * 100)
                msg = f"Embedding {current}/{total} ({pct}%)  —  {name}" if name != "done" else ""
                self.window.after(0, lambda m=msg: self._sim_progress_label.config(text=m))

        def completion(success, message):
            if self.window and self.window.winfo_exists():
                def _finish():
                    self._sim_progress_label.config(text="")
                    self._sim_build_btn.config(state=tk.NORMAL)
                    self._sim_update_btn.config(state=tk.NORMAL)
                    self.update_similarity_status_display()
                    if success:
                        messagebox.showinfo("Index Built", message)
                    else:
                        messagebox.showerror("Build Failed", message)
                self.window.after(0, _finish)

        image_names = self._get_image_list()
        prompt_lookup = self._get_prompt_lookup()
        self._sim_build_thread = self.data_manager.similarity_manager.build_index_async(
            folder, image_names, prompt_lookup, progress, completion)

    def _start_update_index(self):
        """Kick off an incremental index update in the background."""
        folder = self.data_manager.image_folder
        if not folder:
            messagebox.showwarning("No Folder", "Please load an image folder first.")
            return

        if self._sim_build_thread and self._sim_build_thread.is_alive():
            messagebox.showinfo("In Progress", "An index operation is already running.")
            return

        self._sim_build_btn.config(state=tk.DISABLED)
        self._sim_update_btn.config(state=tk.DISABLED)
        self._sim_progress_label.config(text="Checking for new images…")

        def progress(current, total, name):
            if self.window and self.window.winfo_exists():
                pct = int(current / max(total, 1) * 100)
                msg = f"Embedding {current}/{total} ({pct}%)  —  {name}" if name != "done" else ""
                self.window.after(0, lambda m=msg: self._sim_progress_label.config(text=m))

        def completion(success, message):
            if self.window and self.window.winfo_exists():
                def _finish():
                    self._sim_progress_label.config(text="")
                    self._sim_build_btn.config(state=tk.NORMAL)
                    self._sim_update_btn.config(state=tk.NORMAL)
                    self.update_similarity_status_display()
                    if success:
                        messagebox.showinfo("Index Updated", message)
                    else:
                        messagebox.showerror("Update Failed", message)
                self.window.after(0, _finish)

        image_names = self._get_image_list()
        prompt_lookup = self._get_prompt_lookup()
        self._sim_build_thread = self.data_manager.similarity_manager.update_index_async(
            folder, image_names, prompt_lookup, progress, completion)

    def create_target_count_section(self, parent: tk.Frame):
        """Create the Target Count / Cutline system settings section."""
        section = tk.Frame(parent, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=1)
        section.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(section, text="Target Count & Cutline System",
                 font=('Arial', 14, 'bold'), fg=Colors.TEXT_PRIMARY,
                 bg=Colors.BG_SECONDARY).pack(pady=10)

        desc = ("Set a target number of images to keep (e.g. 200). "
                "The algorithm will then focus comparisons on images near the cutline — "
                "those that could go either way. Images clearly above or below the cutline "
                "with sufficient votes are excluded from further pairing. "
                "Set to 0 to disable (existing sorting behaviour).")
        tk.Label(section, text=desc, font=('Arial', 10, 'italic'),
                 fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY,
                 wraplength=850, justify=tk.LEFT).pack(padx=10, pady=5)

        s = self.data_manager.algorithm_settings

        # --- Target count ---
        row1 = tk.Frame(section, bg=Colors.BG_SECONDARY)
        row1.pack(fill=tk.X, padx=20, pady=4)
        tk.Label(row1, text="Target Count (0 = disabled):",
                 font=('Arial', 11), fg=Colors.TEXT_PRIMARY,
                 bg=Colors.BG_SECONDARY, width=30, anchor='w').pack(side=tk.LEFT)
        self._target_count_var = tk.IntVar(value=s.target_count)
        tc_entry = tk.Spinbox(row1, from_=0, to=100000, increment=10,
                              textvariable=self._target_count_var, width=10,
                              command=self.update_cutline_preview_display)
        tc_entry.pack(side=tk.LEFT, padx=5)
        tc_entry.bind('<FocusOut>', lambda e: self.update_cutline_preview_display())
        tc_entry.bind('<Return>',   lambda e: self.update_cutline_preview_display())

        # --- Buffer tiers ---
        row2 = tk.Frame(section, bg=Colors.BG_SECONDARY)
        row2.pack(fill=tk.X, padx=20, pady=4)
        tk.Label(row2, text="Boundary Buffer (tiers):",
                 font=('Arial', 11), fg=Colors.TEXT_PRIMARY,
                 bg=Colors.BG_SECONDARY, width=30, anchor='w').pack(side=tk.LEFT)
        self._cutline_buffer_var = tk.IntVar(value=s.cutline_buffer_tiers)
        tk.Spinbox(row2, from_=1, to=10, textvariable=self._cutline_buffer_var,
                   width=6, command=self.update_cutline_preview_display).pack(side=tk.LEFT, padx=5)
        tk.Label(row2, text="tiers either side of cutline form the boundary zone",
                 font=('Arial', 9, 'italic'), fg=Colors.TEXT_SECONDARY,
                 bg=Colors.BG_SECONDARY).pack(side=tk.LEFT, padx=5)

        # --- Zone base votes ---
        row3 = tk.Frame(section, bg=Colors.BG_SECONDARY)
        row3.pack(fill=tk.X, padx=20, pady=4)
        tk.Label(row3, text="Zone Base Votes:",
                 font=('Arial', 11), fg=Colors.TEXT_PRIMARY,
                 bg=Colors.BG_SECONDARY, width=30, anchor='w').pack(side=tk.LEFT)
        self._zone_base_votes_var = tk.IntVar(value=s.zone_base_votes)
        tk.Spinbox(row3, from_=1, to=50, textvariable=self._zone_base_votes_var,
                   width=6, command=self.update_cutline_preview_display).pack(side=tk.LEFT, padx=5)
        tk.Label(row3, text="minimum votes before an image can be confirmed in/out",
                 font=('Arial', 9, 'italic'), fg=Colors.TEXT_SECONDARY,
                 bg=Colors.BG_SECONDARY).pack(side=tk.LEFT, padx=5)

        # --- Votes per tier ---
        row4 = tk.Frame(section, bg=Colors.BG_SECONDARY)
        row4.pack(fill=tk.X, padx=20, pady=4)
        tk.Label(row4, text="Extra Votes per Tier Distance:",
                 font=('Arial', 11), fg=Colors.TEXT_PRIMARY,
                 bg=Colors.BG_SECONDARY, width=30, anchor='w').pack(side=tk.LEFT)
        self._zone_votes_per_tier_var = tk.DoubleVar(value=s.zone_votes_per_tier)
        tk.Scale(row4, from_=0.0, to=5.0, resolution=0.1, orient=tk.HORIZONTAL,
                 variable=self._zone_votes_per_tier_var, length=200,
                 command=lambda v: self.update_cutline_preview_display(),
                 bg=Colors.BG_SECONDARY, fg=Colors.TEXT_PRIMARY,
                 troughcolor=Colors.BG_TERTIARY).pack(side=tk.LEFT, padx=5)

        # --- Live preview label ---
        self._cutline_preview_label = tk.Label(
            section, text="", font=('Arial', 10),
            fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY,
            justify=tk.LEFT, wraplength=850)
        self._cutline_preview_label.pack(padx=20, pady=8, anchor='w')

        self.update_cutline_preview_display()

    def update_cutline_preview_display(self):
        """Refresh the live cutline preview label."""
        if self._cutline_preview_label is None:
            return
        try:
            tc = int(self._target_count_var.get()) if self._target_count_var else 0
        except (ValueError, tk.TclError):
            tc = 0

        if tc == 0:
            self._cutline_preview_label.config(
                text="Target count is 0 — cutline system disabled. Existing sorting behaviour active.",
                fg=Colors.TEXT_SECONDARY)
            return

        # Build a temporary snapshot using current live vars
        try:
            buf   = int(self._cutline_buffer_var.get())   if self._cutline_buffer_var   else 2
            bv    = int(self._zone_base_votes_var.get())  if self._zone_base_votes_var  else 5
            vpt   = float(self._zone_votes_per_tier_var.get()) if self._zone_votes_per_tier_var else 0.5
        except (ValueError, tk.TclError):
            buf, bv, vpt = 2, 5, 0.5

        active = self.data_manager.get_active_images()
        n = len(active)
        if n < tc:
            self._cutline_preview_label.config(
                text=f"Only {n} active images — need at least {tc} to establish a cutline.",
                fg=Colors.TEXT_WARNING)
            return

        sorted_imgs = sorted(
            active,
            key=lambda img: self.data_manager.image_stats[img].get('current_tier', 0),
            reverse=True)
        cutline = self.data_manager.image_stats[sorted_imgs[tc - 1]].get('current_tier', 0)

        # Count zones using live parameter values
        confirmed_in = confirmed_out = boundary = 0
        for img in active:
            tier  = self.data_manager.image_stats[img].get('current_tier', 0)
            votes = self.data_manager.image_stats[img].get('votes', 0)
            dist  = abs(tier - cutline)
            min_v = max(1, bv + round(dist * vpt))
            if tier >= cutline + buf and votes >= min_v:
                confirmed_in += 1
            elif tier <= cutline - buf and votes >= min_v:
                confirmed_out += 1
            else:
                boundary += 1

        binned = self.data_manager.get_binned_image_count()
        resolved = confirmed_in + confirmed_out + binned
        total    = n + binned
        res_pct  = resolved / total * 100 if total > 0 else 0.0

        self._cutline_preview_label.config(
            text=(f"With {n} active images and target {tc}:\n"
                  f"  Cutline tier: {cutline}  |  "
                  f"✓ In: {confirmed_in}  ~  Boundary: {boundary}  ✗ Out: {confirmed_out}  "
                  f"Binned: {binned}  |  Resolution: {res_pct:.0f}%"),
            fg=Colors.TEXT_SUCCESS if tc <= n else Colors.TEXT_WARNING)

    def close_window(self):
        """Handle window closing."""
        if self.window:
            self.window.destroy()
            self.window = None
