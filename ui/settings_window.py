"""Modern settings window with sleek design and enhanced functionality."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict
import math

from config import Colors, Fonts, Styling
from ui.components.ui_builder import ModernFrame, ModernButton, ModernLabel


class ModernSlider(tk.Scale):
    """Custom slider with modern styling."""
    
    def __init__(self, parent, **kwargs):
        # Modern slider styling
        style_config = {
            'bg': Colors.BG_CARD,
            'fg': Colors.TEXT_PRIMARY,
            'troughcolor': Colors.BG_TERTIARY,
            'activebackground': Colors.PURPLE_PRIMARY,
            'highlightbackground': Colors.BG_CARD,
            'highlightcolor': Colors.PURPLE_PRIMARY,
            'borderwidth': 0,
            'relief': 'flat',
            'font': Fonts.SMALL,
            'length': 400,
            'width': 20
        }
        
        final_config = {**style_config, **kwargs}
        super().__init__(parent, **final_config)


class ModernCheckbox(tk.Checkbutton):
    """Custom checkbox with modern styling."""
    
    def __init__(self, parent, **kwargs):
        # Modern checkbox styling
        style_config = {
            'bg': Colors.BG_CARD,
            'fg': Colors.TEXT_PRIMARY,
            'selectcolor': Colors.PURPLE_PRIMARY,
            'activebackground': Colors.BG_CARD,
            'activeforeground': Colors.TEXT_PRIMARY,
            'borderwidth': 0,
            'relief': 'flat',
            'font': Fonts.MEDIUM,
            'cursor': 'hand2'
        }
        
        final_config = {**style_config, **kwargs}
        super().__init__(parent, **final_config)


class ModernSettingsCard(ModernFrame):
    """Modern settings card with title and content area."""
    
    def __init__(self, parent, title, icon="⚙️", **kwargs):
        super().__init__(parent, style='card', **kwargs)
        
        # Header
        header = ModernFrame(self)
        header.pack(fill=tk.X, padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        # Icon and title
        icon_label = ModernLabel(header, text=icon, font=Fonts.LARGE, fg=Colors.PURPLE_PRIMARY)
        icon_label.pack(side=tk.LEFT)
        
        title_label = ModernLabel(header, text=title, font=Fonts.HEADING, fg=Colors.TEXT_PRIMARY)
        title_label.pack(side=tk.LEFT, padx=(Styling.PADDING_MEDIUM, 0))
        
        # Content frame
        self.content_frame = ModernFrame(self)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=Styling.PADDING_LARGE, pady=(0, Styling.PADDING_LARGE))
    
    def add_description(self, text):
        """Add description text to the card."""
        desc_label = ModernLabel(self.content_frame, 
                                text=text, 
                                font=Fonts.SMALL, 
                                style='secondary',
                                wraplength=850,
                                justify=tk.LEFT)
        desc_label.pack(fill=tk.X, pady=(0, Styling.PADDING_MEDIUM))
    
    def add_widget(self, widget):
        """Add a widget to the card content."""
        widget.pack(in_=self.content_frame, fill=tk.X, pady=Styling.PADDING_SMALL)


class ModernSettingsWindow:
    """Modern settings window with sleek design and enhanced user experience."""
    
    def __init__(self, parent: tk.Tk, data_manager):
        self.parent = parent
        self.data_manager = data_manager
        self.window = None
        
        # Setting variables
        self.tier_std_var = None
        self.tier_std_label = None
        self.overflow_threshold_var = None
        self.overflow_threshold_label = None
        self.min_overflow_images_var = None
        self.min_overflow_images_label = None
        
        # Tier bounds variables
        self.tier_bounds_enabled_var = None
        self.tier_bounds_std_multiplier_var = None
        self.tier_bounds_std_multiplier_label = None
        self.tier_bounds_min_confidence_var = None
        self.tier_bounds_min_confidence_label = None
        self.tier_bounds_min_votes_var = None
        self.tier_bounds_min_votes_label = None
        self.tier_bounds_adaptive_var = None
        self.tier_bounds_status_label = None
        
        # Status display
        self.status_text_label = None
        
        # Initialize settings
        self._initialize_settings()
    
    def _initialize_settings(self):
        """Initialize settings with default values if they don't exist."""
        # Tier bounds settings
        if not hasattr(self.data_manager, 'tier_bounds_enabled'):
            self.data_manager.tier_bounds_enabled = True
        if not hasattr(self.data_manager, 'tier_bounds_std_multiplier'):
            self.data_manager.tier_bounds_std_multiplier = 3.0
        if not hasattr(self.data_manager, 'tier_bounds_min_confidence'):
            self.data_manager.tier_bounds_min_confidence = 0.8
        if not hasattr(self.data_manager, 'tier_bounds_min_votes'):
            self.data_manager.tier_bounds_min_votes = 10
        if not hasattr(self.data_manager, 'tier_bounds_adaptive'):
            self.data_manager.tier_bounds_adaptive = True
        
        # Other settings
        if not hasattr(self.data_manager, 'overflow_threshold'):
            self.data_manager.overflow_threshold = 1.0
        if not hasattr(self.data_manager, 'min_overflow_images'):
            self.data_manager.min_overflow_images = 2
        if not hasattr(self.data_manager, 'tier_distribution_std'):
            self.data_manager.tier_distribution_std = 1.5
    
    def show(self):
        """Show the modern settings window."""
        if self.window is None or not self.window.winfo_exists():
            self.create_window()
        else:
            self.window.lift()
            self.window.focus_force()
    
    def create_window(self):
        """Create the modern settings window."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("⚙️ Algorithm Settings")
        self.window.geometry("1000x900")
        self.window.configure(bg=Colors.BG_PRIMARY)
        self.window.resizable(True, True)
        
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # Main container
        main_container = ModernFrame(self.window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        # Create scrollable content
        self._create_scrollable_content(main_container)
    
    def _create_scrollable_content(self, parent):
        """Create scrollable content area."""
        # Create canvas and scrollbar
        canvas = tk.Canvas(parent, bg=Colors.BG_PRIMARY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ModernFrame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Create content
        self._create_settings_content(scrollable_frame)
        
        # Configure scrolling
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def configure_canvas_width(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        
        scrollable_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", configure_canvas_width)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
    
    def _create_settings_content(self, parent):
        """Create the main settings content with modern design."""
        # Header
        self._create_modern_header(parent)
        
        # Settings sections
        self._create_tier_bounds_section(parent)
        self._create_tier_distribution_section(parent)
        self._create_overflow_detection_section(parent)
        self._create_status_section(parent)
        
        # Action buttons
        self._create_action_buttons(parent)
    
    def _create_modern_header(self, parent):
        """Create modern header with algorithm explanation."""
        header_card = ModernSettingsCard(parent, "Algorithm Configuration", "🧠")
        header_card.pack(fill=tk.X, pady=(0, Styling.PADDING_LARGE))
        
        explanation = """The ranking algorithm uses advanced tier-overflow detection with intelligent bounds management:

• TIER BOUNDS: Prevent runaway tier inflation while allowing exceptional images to reach extremes
• CONFIDENCE GATING: High-confidence images (stable + many votes) can exceed normal bounds
• ADAPTIVE SCALING: Bounds grow intelligently with your collection size
• ELEGANT FALLBACK: Images that can't move stay in their current tier

This ensures a stable, bounded system while maintaining ranking quality."""
        
        header_card.add_description(explanation)
    
    def _create_tier_bounds_section(self, parent):
        """Create tier bounds settings section."""
        card = ModernSettingsCard(parent, "Tier Bounds Control", "🎯")
        card.pack(fill=tk.X, pady=(0, Styling.PADDING_LARGE))
        
        card.add_description("Control how extreme tiers can become. Prevents runaway inflation while allowing truly exceptional images to reach extremes.")
        
        # Enable/disable checkbox
        checkbox_frame = ModernFrame(card.content_frame)
        checkbox_frame.pack(fill=tk.X, pady=Styling.PADDING_MEDIUM)
        
        self.tier_bounds_enabled_var = tk.BooleanVar(value=getattr(self.data_manager, 'tier_bounds_enabled', True))
        
        enable_checkbox = ModernCheckbox(checkbox_frame,
                                        text="Enable Tier Bounds",
                                        variable=self.tier_bounds_enabled_var,
                                        command=self._on_tier_bounds_enabled_change)
        enable_checkbox.pack(anchor=tk.W)
        
        self.tier_bounds_status_label = ModernLabel(checkbox_frame,
                                                   text="Status: Enabled" if self.tier_bounds_enabled_var.get() else "Status: Disabled",
                                                   font=Fonts.SMALL,
                                                   fg=Colors.SUCCESS if self.tier_bounds_enabled_var.get() else Colors.ERROR)
        self.tier_bounds_status_label.pack(anchor=tk.W, padx=(Styling.PADDING_LARGE, 0))
        
        # Adaptive bounds
        self.tier_bounds_adaptive_var = tk.BooleanVar(value=getattr(self.data_manager, 'tier_bounds_adaptive', True))
        adaptive_checkbox = ModernCheckbox(checkbox_frame,
                                          text="Adaptive Bounds (grow with collection size)",
                                          variable=self.tier_bounds_adaptive_var)
        adaptive_checkbox.pack(anchor=tk.W, pady=(Styling.PADDING_SMALL, 0))
        
        # Bounds size slider
        self._create_bounds_size_control(card.content_frame)
        
        # Confidence requirement slider
        self._create_confidence_control(card.content_frame)
        
        # Votes requirement slider
        self._create_votes_control(card.content_frame)
        
        # Action buttons
        self._create_bounds_actions(card.content_frame)
    
    def _create_bounds_size_control(self, parent):
        """Create bounds size control."""
        control_frame = ModernFrame(parent)
        control_frame.pack(fill=tk.X, pady=Styling.PADDING_MEDIUM)
        
        label = ModernLabel(control_frame, text="Bounds Size (Standard Deviations)", font=Fonts.MEDIUM)
        label.pack(anchor=tk.W)
        
        desc = ModernLabel(control_frame, text="How many standard deviations to allow (3.0 = 99.7% containment)", 
                          font=Fonts.SMALL, style='secondary')
        desc.pack(anchor=tk.W)
        
        current_value = getattr(self.data_manager, 'tier_bounds_std_multiplier', 3.0)
        self.tier_bounds_std_multiplier_label = ModernLabel(control_frame, 
                                                           text=f"Current: {current_value:.1f} std devs",
                                                           font=Fonts.SMALL, fg=Colors.PURPLE_PRIMARY)
        self.tier_bounds_std_multiplier_label.pack(anchor=tk.W, pady=(Styling.PADDING_SMALL, 0))
        
        self.tier_bounds_std_multiplier_var = tk.DoubleVar(value=current_value)
        
        slider = ModernSlider(control_frame,
                             from_=1.0, to=5.0, resolution=0.1,
                             orient=tk.HORIZONTAL,
                             variable=self.tier_bounds_std_multiplier_var,
                             command=lambda v: self._update_bounds_size_display())
        slider.pack(fill=tk.X, pady=Styling.PADDING_SMALL)
    
    def _create_confidence_control(self, parent):
        """Create confidence requirement control."""
        control_frame = ModernFrame(parent)
        control_frame.pack(fill=tk.X, pady=Styling.PADDING_MEDIUM)
        
        label = ModernLabel(control_frame, text="Minimum Confidence to Exceed Bounds", font=Fonts.MEDIUM)
        label.pack(anchor=tk.W)
        
        desc = ModernLabel(control_frame, text="Images need this confidence level to go beyond bounds", 
                          font=Fonts.SMALL, style='secondary')
        desc.pack(anchor=tk.W)
        
        current_value = getattr(self.data_manager, 'tier_bounds_min_confidence', 0.8)
        self.tier_bounds_min_confidence_label = ModernLabel(control_frame, 
                                                           text=f"Current: {current_value:.1%}",
                                                           font=Fonts.SMALL, fg=Colors.PURPLE_PRIMARY)
        self.tier_bounds_min_confidence_label.pack(anchor=tk.W, pady=(Styling.PADDING_SMALL, 0))
        
        self.tier_bounds_min_confidence_var = tk.DoubleVar(value=current_value)
        
        slider = ModernSlider(control_frame,
                             from_=0.5, to=0.95, resolution=0.05,
                             orient=tk.HORIZONTAL,
                             variable=self.tier_bounds_min_confidence_var,
                             command=lambda v: self._update_confidence_display())
        slider.pack(fill=tk.X, pady=Styling.PADDING_SMALL)
    
    def _create_votes_control(self, parent):
        """Create votes requirement control."""
        control_frame = ModernFrame(parent)
        control_frame.pack(fill=tk.X, pady=Styling.PADDING_MEDIUM)
        
        label = ModernLabel(control_frame, text="Minimum Votes to Exceed Bounds", font=Fonts.MEDIUM)
        label.pack(anchor=tk.W)
        
        desc = ModernLabel(control_frame, text="Images need this many votes to go beyond bounds", 
                          font=Fonts.SMALL, style='secondary')
        desc.pack(anchor=tk.W)
        
        current_value = getattr(self.data_manager, 'tier_bounds_min_votes', 10)
        self.tier_bounds_min_votes_label = ModernLabel(control_frame, 
                                                      text=f"Current: {current_value} votes",
                                                      font=Fonts.SMALL, fg=Colors.PURPLE_PRIMARY)
        self.tier_bounds_min_votes_label.pack(anchor=tk.W, pady=(Styling.PADDING_SMALL, 0))
        
        self.tier_bounds_min_votes_var = tk.IntVar(value=current_value)
        
        slider = ModernSlider(control_frame,
                             from_=5, to=50, resolution=1,
                             orient=tk.HORIZONTAL,
                             variable=self.tier_bounds_min_votes_var,
                             command=lambda v: self._update_votes_display())
        slider.pack(fill=tk.X, pady=Styling.PADDING_SMALL)
    
    def _create_bounds_actions(self, parent):
        """Create action buttons for tier bounds."""
        button_frame = ModernFrame(parent)
        button_frame.pack(fill=tk.X, pady=Styling.PADDING_MEDIUM)
        
        preview_btn = ModernButton(button_frame, text="👁️ Preview Bounds", 
                                  command=self._preview_tier_bounds, style='secondary')
        preview_btn.pack(side=tk.LEFT, padx=(0, Styling.PADDING_SMALL))
        
        reset_btn = ModernButton(button_frame, text="🔄 Reset to Defaults", 
                                command=self._reset_tier_bounds, style='ghost')
        reset_btn.pack(side=tk.LEFT)
    
    def _create_tier_distribution_section(self, parent):
        """Create tier distribution section."""
        card = ModernSettingsCard(parent, "Tier Distribution", "📊")
        card.pack(fill=tk.X, pady=(0, Styling.PADDING_LARGE))
        
        card.add_description("Control how tiers should be distributed. Lower values create tighter clustering around tier 0.")
        
        # Standard deviation control
        control_frame = ModernFrame(card.content_frame)
        control_frame.pack(fill=tk.X, pady=Styling.PADDING_MEDIUM)
        
        label = ModernLabel(control_frame, text="Standard Deviation", font=Fonts.MEDIUM)
        label.pack(anchor=tk.W)
        
        current_value = getattr(self.data_manager, 'tier_distribution_std', 1.5)
        self.tier_std_label = ModernLabel(control_frame, 
                                         text=f"Current: {current_value:.2f}",
                                         font=Fonts.SMALL, fg=Colors.PURPLE_PRIMARY)
        self.tier_std_label.pack(anchor=tk.W, pady=(Styling.PADDING_SMALL, 0))
        
        self.tier_std_var = tk.DoubleVar(value=current_value)
        
        slider = ModernSlider(control_frame,
                             from_=0.5, to=3.0, resolution=0.1,
                             orient=tk.HORIZONTAL,
                             variable=self.tier_std_var,
                             command=lambda v: self._update_tier_std_display())
        slider.pack(fill=tk.X, pady=Styling.PADDING_SMALL)
        
        # Actions
        button_frame = ModernFrame(control_frame)
        button_frame.pack(fill=tk.X, pady=Styling.PADDING_MEDIUM)
        
        preview_btn = ModernButton(button_frame, text="📈 Preview Distribution", 
                                  command=self._preview_distribution, style='secondary')
        preview_btn.pack(side=tk.LEFT, padx=(0, Styling.PADDING_SMALL))
        
        reset_btn = ModernButton(button_frame, text="🔄 Reset (1.5)", 
                                command=lambda: self._reset_single_setting(self.tier_std_var, 1.5, self._update_tier_std_display),
                                style='ghost')
        reset_btn.pack(side=tk.LEFT)
    
    def _create_overflow_detection_section(self, parent):
        """Create overflow detection section."""
        card = ModernSettingsCard(parent, "Overflow Detection", "🚨")
        card.pack(fill=tk.X, pady=(0, Styling.PADDING_LARGE))
        
        card.add_description("Control when a tier is considered 'overflowing' and needs attention from the algorithm.")
        
        # Overflow threshold
        threshold_frame = ModernFrame(card.content_frame)
        threshold_frame.pack(fill=tk.X, pady=Styling.PADDING_MEDIUM)
        
        label = ModernLabel(threshold_frame, text="Overflow Threshold", font=Fonts.MEDIUM)
        label.pack(anchor=tk.W)
        
        current_value = getattr(self.data_manager, 'overflow_threshold', 1.0)
        self.overflow_threshold_label = ModernLabel(threshold_frame, 
                                                   text=f"Current: {current_value:.2f}x expected",
                                                   font=Fonts.SMALL, fg=Colors.PURPLE_PRIMARY)
        self.overflow_threshold_label.pack(anchor=tk.W, pady=(Styling.PADDING_SMALL, 0))
        
        self.overflow_threshold_var = tk.DoubleVar(value=current_value)
        
        slider = ModernSlider(threshold_frame,
                             from_=0.5, to=2.0, resolution=0.1,
                             orient=tk.HORIZONTAL,
                             variable=self.overflow_threshold_var,
                             command=lambda v: self._update_overflow_threshold_display())
        slider.pack(fill=tk.X, pady=Styling.PADDING_SMALL)
        
        # Minimum images
        min_images_frame = ModernFrame(card.content_frame)
        min_images_frame.pack(fill=tk.X, pady=Styling.PADDING_MEDIUM)
        
        label = ModernLabel(min_images_frame, text="Minimum Images for Overflow", font=Fonts.MEDIUM)
        label.pack(anchor=tk.W)
        
        current_value = getattr(self.data_manager, 'min_overflow_images', 2)
        self.min_overflow_images_label = ModernLabel(min_images_frame, 
                                                    text=f"Current: {current_value} images",
                                                    font=Fonts.SMALL, fg=Colors.PURPLE_PRIMARY)
        self.min_overflow_images_label.pack(anchor=tk.W, pady=(Styling.PADDING_SMALL, 0))
        
        self.min_overflow_images_var = tk.IntVar(value=current_value)
        
        slider = ModernSlider(min_images_frame,
                             from_=2, to=10, resolution=1,
                             orient=tk.HORIZONTAL,
                             variable=self.min_overflow_images_var,
                             command=lambda v: self._update_min_overflow_images_display())
        slider.pack(fill=tk.X, pady=Styling.PADDING_SMALL)
        
        # Reset button
        reset_btn = ModernButton(card.content_frame, text="🔄 Reset Overflow Settings", 
                                command=self._reset_overflow_settings, style='ghost')
        reset_btn.pack(pady=Styling.PADDING_MEDIUM)
    
    def _create_status_section(self, parent):
        """Create status display section."""
        card = ModernSettingsCard(parent, "Current Status", "📋")
        card.pack(fill=tk.X, pady=(0, Styling.PADDING_LARGE))
        
        card.add_description("Live preview of your current algorithm configuration and its effects.")
        
        # Status display
        status_frame = ModernFrame(card.content_frame, style='card')
        status_frame.pack(fill=tk.X, pady=Styling.PADDING_MEDIUM)
        
        self.status_text_label = ModernLabel(status_frame,
                                           text="Loading status...",
                                           font=Fonts.SMALL,
                                           fg=Colors.TEXT_SECONDARY,
                                           justify=tk.LEFT,
                                           wraplength=800)
        self.status_text_label.pack(padx=Styling.PADDING_MEDIUM, pady=Styling.PADDING_MEDIUM)
        
        # Refresh button
        refresh_btn = ModernButton(card.content_frame, text="🔄 Refresh Status", 
                                  command=self._update_status_display, style='secondary')
        refresh_btn.pack(pady=Styling.PADDING_MEDIUM)
    
    def _create_action_buttons(self, parent):
        """Create main action buttons."""
        button_frame = ModernFrame(parent)
        button_frame.pack(fill=tk.X, pady=Styling.PADDING_LARGE)
        
        # Apply button
        apply_btn = ModernButton(button_frame, text="✅ Apply Changes", 
                                command=self._apply_changes, style='success')
        apply_btn.pack(side=tk.LEFT, padx=(0, Styling.PADDING_MEDIUM))
        
        # Cancel button
        cancel_btn = ModernButton(button_frame, text="❌ Cancel", 
                                 command=self.close_window, style='error')
        cancel_btn.pack(side=tk.LEFT)
    
    # Display update methods
    def _update_bounds_size_display(self):
        """Update bounds size display."""
        if self.tier_bounds_std_multiplier_var:
            value = self.tier_bounds_std_multiplier_var.get()
            self.tier_bounds_std_multiplier_label.config(text=f"Current: {value:.1f} std devs")
    
    def _update_confidence_display(self):
        """Update confidence display."""
        if self.tier_bounds_min_confidence_var:
            value = self.tier_bounds_min_confidence_var.get()
            self.tier_bounds_min_confidence_label.config(text=f"Current: {value:.1%}")
    
    def _update_votes_display(self):
        """Update votes display."""
        if self.tier_bounds_min_votes_var:
            value = self.tier_bounds_min_votes_var.get()
            self.tier_bounds_min_votes_label.config(text=f"Current: {value} votes")
    
    def _update_tier_std_display(self):
        """Update tier std display."""
        if self.tier_std_var:
            value = self.tier_std_var.get()
            self.tier_std_label.config(text=f"Current: {value:.2f}")
    
    def _update_overflow_threshold_display(self):
        """Update overflow threshold display."""
        if self.overflow_threshold_var:
            value = self.overflow_threshold_var.get()
            self.overflow_threshold_label.config(text=f"Current: {value:.2f}x expected")
    
    def _update_min_overflow_images_display(self):
        """Update min overflow images display."""
        if self.min_overflow_images_var:
            value = self.min_overflow_images_var.get()
            self.min_overflow_images_label.config(text=f"Current: {value} images")
    
    def _update_status_display(self):
        """Update status display."""
        try:
            # Get current bounds info
            bounds_info = self.data_manager.get_tier_bounds_info()
            
            if bounds_info['enabled']:
                status_text = f"""🎯 TIER BOUNDS STATUS

Range: Tier {bounds_info['min_tier']:+d} to Tier {bounds_info['max_tier']:+d}
Total Images: {bounds_info['total_images']}
Images at Bounds: {bounds_info['images_at_min_bound']} (min) | {bounds_info['images_at_max_bound']} (max)
Qualified for Extremes: {bounds_info['qualified_for_bounds']} images

📊 CONFIGURATION
• Std Dev Multiplier: {bounds_info['std_multiplier']:.1f}
• Min Confidence: {bounds_info['min_confidence']:.1%}
• Min Votes: {bounds_info['min_votes']}
• Adaptive: {'Yes' if bounds_info['adaptive'] else 'No'}

✅ Tier bounds are actively managing your collection"""
            else:
                status_text = "❌ Tier bounds are disabled - tiers can grow indefinitely"
        
        except Exception as e:
            status_text = f"❌ Error loading status: {e}"
        
        if self.status_text_label:
            self.status_text_label.config(text=status_text)
    
    def _on_tier_bounds_enabled_change(self):
        """Handle tier bounds enabled change."""
        enabled = self.tier_bounds_enabled_var.get()
        
        if self.tier_bounds_status_label:
            self.tier_bounds_status_label.config(
                text="Status: Enabled" if enabled else "Status: Disabled",
                fg=Colors.SUCCESS if enabled else Colors.ERROR
            )
        
        self._update_status_display()
    
    # Preview methods
    def _preview_tier_bounds(self):
        """Preview tier bounds."""
        try:
            enabled = self.tier_bounds_enabled_var.get()
            std_mult = self.tier_bounds_std_multiplier_var.get()
            min_conf = self.tier_bounds_min_confidence_var.get()
            min_votes = self.tier_bounds_min_votes_var.get()
            adaptive = self.tier_bounds_adaptive_var.get()
            
            if not enabled:
                self._show_info_dialog("Tier Bounds Preview", "🚫 Tier bounds are disabled.\nTiers can grow indefinitely.")
                return
            
            tier_std = self.tier_std_var.get()
            base_bound = int(tier_std * std_mult)
            
            preview_text = f"""🎯 TIER BOUNDS PREVIEW

Base Bounds: Tier {-base_bound:+d} to Tier {+base_bound:+d}
(Based on {std_mult:.1f} × {tier_std:.1f} std dev)

"""
            
            if adaptive:
                total_images = len(self.data_manager.image_stats)
                adaptive_bonus = int(math.log10(max(total_images, 10)) - 2) if total_images > 100 else 0
                preview_text += f"""📈 Adaptive Bonus: +{adaptive_bonus} tiers
Final Bounds: Tier {-base_bound-adaptive_bonus:+d} to Tier {+base_bound+adaptive_bonus:+d}

"""
            
            preview_text += f"""⚙️ QUALIFICATION RULES
• Min Confidence: {min_conf:.1%}
• Min Votes: {min_votes}

Images within bounds move freely.
Images at bounds need qualification to move further."""
            
            self._show_info_dialog("Tier Bounds Preview", preview_text)
            
        except Exception as e:
            self._show_error_dialog("Preview Error", f"Error previewing bounds: {e}")
    
    def _preview_distribution(self):
        """Preview tier distribution."""
        std_dev = self.tier_std_var.get()
        
        tiers = list(range(-5, 6))
        proportions = []
        
        for tier in tiers:
            density = math.exp(-(tier ** 2) / (2 * std_dev ** 2))
            proportions.append(density)
        
        total_density = sum(proportions)
        normalized_proportions = [p / total_density for p in proportions]
        
        preview_text = f"📊 EXPECTED DISTRIBUTION (std dev = {std_dev:.1f})\n\n"
        
        for tier, proportion in zip(tiers, normalized_proportions):
            percentage = proportion * 100
            bar_length = int(percentage * 2)
            bar = "█" * bar_length
            preview_text += f"Tier {tier:+2d}: {percentage:5.1f}% {bar}\n"
        
        self._show_info_dialog("Distribution Preview", preview_text)
    
    # Reset methods
    def _reset_tier_bounds(self):
        """Reset tier bounds to defaults."""
        self.tier_bounds_enabled_var.set(True)
        self.tier_bounds_std_multiplier_var.set(3.0)
        self.tier_bounds_min_confidence_var.set(0.8)
        self.tier_bounds_min_votes_var.set(10)
        self.tier_bounds_adaptive_var.set(True)
        
        self._update_bounds_size_display()
        self._update_confidence_display()
        self._update_votes_display()
        self._on_tier_bounds_enabled_change()
    
    def _reset_single_setting(self, var, value, update_func):
        """Reset a single setting."""
        var.set(value)
        update_func()
    
    def _reset_overflow_settings(self):
        """Reset overflow settings."""
        self.overflow_threshold_var.set(1.0)
        self.min_overflow_images_var.set(2)
        self._update_overflow_threshold_display()
        self._update_min_overflow_images_display()
    
    def _apply_changes(self):
        """Apply all changes."""
        try:
            # Apply tier bounds settings
            self.data_manager.tier_bounds_enabled = self.tier_bounds_enabled_var.get()
            self.data_manager.tier_bounds_std_multiplier = self.tier_bounds_std_multiplier_var.get()
            self.data_manager.tier_bounds_min_confidence = self.tier_bounds_min_confidence_var.get()
            self.data_manager.tier_bounds_min_votes = self.tier_bounds_min_votes_var.get()
            self.data_manager.tier_bounds_adaptive = self.tier_bounds_adaptive_var.get()
            
            # Apply other settings
            self.data_manager.tier_distribution_std = self.tier_std_var.get()
            self.data_manager.overflow_threshold = self.overflow_threshold_var.get()
            self.data_manager.min_overflow_images = self.min_overflow_images_var.get()
            
            bounds_status = "enabled" if self.data_manager.tier_bounds_enabled else "disabled"
            self._show_success_dialog("Settings Applied", 
                                     f"✅ All settings updated successfully!\n\n"
                                     f"Tier bounds: {bounds_status}\n"
                                     f"Changes are active immediately.")
            
            self.close_window()
            
        except Exception as e:
            self._show_error_dialog("Apply Error", f"Error applying settings: {e}")
    
    # Dialog methods
    def _show_info_dialog(self, title, message):
        """Show info dialog."""
        messagebox.showinfo(title, message)
    
    def _show_success_dialog(self, title, message):
        """Show success dialog."""
        messagebox.showinfo(title, message)
    
    def _show_error_dialog(self, title, message):
        """Show error dialog."""
        messagebox.showerror(title, message)
    
    def close_window(self):
        """Close the settings window."""
        if self.window:
            self.window.destroy()
            self.window = None


# Backward compatibility
class SettingsWindow(ModernSettingsWindow):
    """Backward compatibility alias."""
    pass
