"""Modern reusable UI components for the Image Ranking System."""

import tkinter as tk
from tkinter import ttk
import os
from config import Colors, Fonts, Styling
from ui.components.ui_builder import ModernFrame, ModernLabel


class ModernImagePreviewCard(ModernFrame):
    """Modern card-style image preview with enhanced styling."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, style='card', **kwargs)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Image
        self.grid_rowconfigure(2, weight=0)  # Info
        self.grid_rowconfigure(3, weight=0)  # Stats
        self.grid_rowconfigure(4, weight=0)  # Prompt
        
        # Header
        self.header_frame = ModernFrame(self)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        icon_label = ModernLabel(self.header_frame, text="🖼️", font=Fonts.LARGE, fg=Colors.PURPLE_PRIMARY)
        icon_label.pack(side=tk.LEFT)
        
        title_label = ModernLabel(self.header_frame, text="Image Preview", font=Fonts.HEADING, fg=Colors.TEXT_PRIMARY)
        title_label.pack(side=tk.LEFT, padx=(Styling.PADDING_MEDIUM, 0))
        
        # Image display area
        self.image_frame = ModernFrame(self)
        self.image_frame.grid(row=1, column=0, sticky="nsew", padx=Styling.PADDING_LARGE, pady=(0, Styling.PADDING_MEDIUM))
        
        # Info section
        self.info_frame = ModernFrame(self, style='card')
        self.info_frame.grid(row=2, column=0, sticky="ew", padx=Styling.PADDING_LARGE, pady=(0, Styling.PADDING_MEDIUM))
        
        # Additional stats section
        self.stats_frame = ModernFrame(self, style='card')
        self.stats_frame.grid(row=3, column=0, sticky="ew", padx=Styling.PADDING_LARGE, pady=(0, Styling.PADDING_MEDIUM))
        
        # Prompt section
        self.prompt_frame = ModernFrame(self, style='card')
        self.prompt_frame.grid(row=4, column=0, sticky="ew", padx=Styling.PADDING_LARGE, pady=(0, Styling.PADDING_LARGE))


class ModernPromptDisplay(tk.Frame):
    """Modern prompt display with syntax highlighting and scrolling."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=Colors.BG_CARD, **kwargs)
        
        # Header
        header = ModernFrame(self)
        header.pack(fill=tk.X, pady=(0, Styling.PADDING_SMALL))
        
        prompt_icon = ModernLabel(header, text="💬", font=Fonts.MEDIUM, fg=Colors.PURPLE_PRIMARY)
        prompt_icon.pack(side=tk.LEFT)
        
        prompt_label = ModernLabel(header, text="Generation Prompt", font=Fonts.MEDIUM, fg=Colors.TEXT_PRIMARY)
        prompt_label.pack(side=tk.LEFT, padx=(Styling.PADDING_SMALL, 0))
        
        # Text area with scrollbar
        text_frame = ModernFrame(self)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure text widget with modern styling
        self.text_widget = tk.Text(text_frame, 
                                  height=4, 
                                  wrap=tk.WORD,
                                  bg=Colors.BG_TERTIARY,
                                  fg=Colors.TEXT_PRIMARY,
                                  font=Fonts.SMALL,
                                  relief='flat',
                                  borderwidth=0,
                                  highlightthickness=1,
                                  highlightbackground=Colors.BORDER_PRIMARY,
                                  highlightcolor=Colors.BORDER_ACCENT,
                                  selectbackground=Colors.PURPLE_PRIMARY,
                                  selectforeground=Colors.TEXT_PRIMARY,
                                  insertbackground=Colors.TEXT_PRIMARY,
                                  state=tk.DISABLED)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Pack text and scrollbar
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def set_text(self, text):
        """Set the prompt text with modern formatting."""
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        
        if text:
            self.text_widget.insert(1.0, text)
        else:
            self.text_widget.insert(1.0, "No prompt information available")
            self.text_widget.config(fg=Colors.TEXT_MUTED)
        
        self.text_widget.config(state=tk.DISABLED)


class ImagePreviewMixin:
    """Modern image preview mixin with enhanced styling and functionality."""
    
    def __init__(self):
        self.image_label = None
        self.image_info_label = None
        self.additional_stats_label = None
        self.prompt_display = None
        self.current_image = None
        self.current_displayed_image = None
        self.resize_timer = None
        self.image_processor = None
        self.preview_card = None
    
    def create_image_preview_area(self, parent, include_additional_stats=True):
        """Create modern image preview area with card-style layout."""
        # Main preview card
        self.preview_card = ModernImagePreviewCard(parent)
        self.preview_card.pack(fill=tk.BOTH, expand=True)
        
        # Image display in the image frame
        self.image_label = tk.Label(self.preview_card.image_frame,
                                   text="Hover over an image to preview",
                                   bg=Colors.BG_TERTIARY,
                                   fg=Colors.TEXT_MUTED,
                                   font=Fonts.MEDIUM,
                                   justify=tk.CENTER,
                                   relief='flat',
                                   borderwidth=0)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Image info in the info frame
        self.image_info_label = ModernLabel(self.preview_card.info_frame,
                                           text="",
                                           font=Fonts.MEDIUM,
                                           fg=Colors.TEXT_PRIMARY,
                                           justify=tk.CENTER)
        self.image_info_label.pack(padx=Styling.PADDING_MEDIUM, pady=Styling.PADDING_MEDIUM)
        
        # Additional stats if requested
        if include_additional_stats:
            stats_header = ModernFrame(self.preview_card.stats_frame)
            stats_header.pack(fill=tk.X, padx=Styling.PADDING_MEDIUM, pady=(Styling.PADDING_MEDIUM, 0))
            
            stats_icon = ModernLabel(stats_header, text="📊", font=Fonts.SMALL, fg=Colors.PURPLE_PRIMARY)
            stats_icon.pack(side=tk.LEFT)
            
            stats_title = ModernLabel(stats_header, text="Statistics", font=Fonts.SMALL, fg=Colors.TEXT_PRIMARY)
            stats_title.pack(side=tk.LEFT, padx=(Styling.PADDING_SMALL, 0))
            
            self.additional_stats_label = ModernLabel(self.preview_card.stats_frame,
                                                     text="",
                                                     font=Fonts.SMALL,
                                                     fg=Colors.TEXT_SECONDARY,
                                                     justify=tk.CENTER)
            self.additional_stats_label.pack(padx=Styling.PADDING_MEDIUM, pady=Styling.PADDING_MEDIUM)
        
        # Prompt display
        self.prompt_display = ModernPromptDisplay(self.preview_card.prompt_frame)
        self.prompt_display.pack(fill=tk.BOTH, expand=True, padx=Styling.PADDING_MEDIUM, pady=Styling.PADDING_MEDIUM)
        
        return self.preview_card
    
    def display_preview_image(self, filename):
        """Display a preview image with modern styling."""
        if not filename or not hasattr(self, 'data_manager') or not self.data_manager.image_folder:
            return
        
        # Check if image_label exists and is valid
        if not self.image_label or not self.image_label.winfo_exists():
            return

        try:
            img_path = os.path.join(self.data_manager.image_folder, filename)
            if not os.path.exists(img_path):
                return
            
            # Update window to get dimensions
            window_ref = self.window if hasattr(self, 'window') else self.root
            if not window_ref:
                return
                
            window_ref.update_idletasks()
            
            # Get label dimensions with safety checks
            try:
                label_width = self.image_label.winfo_width()
                label_height = self.image_label.winfo_height()
            except (tk.TclError, AttributeError):
                # If we can't get dimensions, use defaults
                label_width = 400
                label_height = 400
            
            if label_width <= 1 or label_height <= 1:
                # Try again later if widget isn't ready
                if window_ref:
                    window_ref.after(100, lambda: self.display_preview_image(filename))
                return
            
            # Calculate preview size
            preview_width = max(label_width - 20, 300)
            preview_height = max(label_height - 20, 300)
            
            # Load and display image
            if hasattr(self, 'image_processor') and self.image_processor:
                photo = self.image_processor.load_and_resize_image(
                    img_path, preview_width, preview_height)
                
                if photo:
                    self.current_image = photo
                    self.image_label.config(image=photo, text="", bg=Colors.BG_TERTIARY)
                    self.current_displayed_image = filename
                    self.update_image_info_display(filename)
                else:
                    self.handle_image_load_error(filename)
            else:
                self.handle_image_load_error(filename)
                
        except Exception as e:
            print(f"Error displaying preview for {filename}: {e}")
            self.handle_image_load_error(filename)
    
    def update_image_info_display(self, filename):
        """Update image info display with modern styling."""
        if not hasattr(self, 'data_manager'):
            return
        
        try:
            stats = self.data_manager.get_image_stats(filename)
            
            # Basic info
            votes = stats.get('votes', 0)
            wins = stats.get('wins', 0)
            losses = stats.get('losses', 0)
            tier = stats.get('current_tier', 0)
            win_rate = wins / votes if votes > 0 else 0
            
            # Format tier with color
            tier_text = f"Tier {tier:+d}" if tier != 0 else "Tier 0"
            
            # Main info text
            info_text = f"📁 {filename}\n🎯 {tier_text} • 🗳️ {votes} votes • 🏆 {wins}W {losses}L"
            
            if self.image_info_label:
                self.image_info_label.config(text=info_text)
            
            # Additional stats
            if hasattr(self, 'additional_stats_label') and self.additional_stats_label:
                stability = 0
                confidence = 0
                
                if hasattr(self, 'ranking_algorithm'):
                    try:
                        stability = self.ranking_algorithm._calculate_tier_stability(filename)
                        confidence = self.ranking_algorithm._calculate_image_confidence(filename)
                    except:
                        pass
                
                last_voted = stats.get('last_voted', -1)
                if last_voted == -1:
                    last_voted_text = "Never"
                elif hasattr(self, 'data_manager'):
                    votes_ago = self.data_manager.vote_count - last_voted
                    last_voted_text = f"{votes_ago} votes ago" if votes_ago > 0 else "Current"
                else:
                    last_voted_text = "Unknown"
                
                additional_text = (f"📈 Win Rate: {win_rate:.1%}\n"
                                 f"📊 Stability: {stability:.2f} • 🎯 Confidence: {confidence:.2f}\n"
                                 f"🕐 Last voted: {last_voted_text}")
                
                self.additional_stats_label.config(text=additional_text)
            
            # Update prompt display
            if self.prompt_display:
                prompt = stats.get('prompt', '')
                self.prompt_display.set_text(prompt)
        
        except Exception as e:
            print(f"Error updating image info display: {e}")
            if self.image_info_label:
                self.image_info_label.config(text=f"Error loading info for {filename}")
    
    def handle_image_load_error(self, filename):
        """Handle image loading errors with modern styling."""
        if self.image_label:
            self.image_label.config(
                image="",
                text="⚠️ Failed to load image",
                fg=Colors.ERROR,
                bg=Colors.BG_TERTIARY
            )
        
        if self.image_info_label:
            self.image_info_label.config(
                text=f"❌ Error loading: {filename}",
                fg=Colors.ERROR
            )
        
        if hasattr(self, 'additional_stats_label') and self.additional_stats_label:
            self.additional_stats_label.config(
                text="Unable to load image statistics",
                fg=Colors.TEXT_MUTED
            )
        
        if self.prompt_display:
            self.prompt_display.set_text("Error loading image")
        
        self.current_image = None
    
    def setup_preview_resize_handling(self):
        """Set up resize event handling for the preview area."""
        window_ref = self.window if hasattr(self, 'window') else self.root
        if window_ref:
            window_ref.bind('<Configure>', self.on_preview_window_resize)
    
    def on_preview_window_resize(self, event):
        """Handle window resize events with debouncing."""
        window_ref = self.window if hasattr(self, 'window') else self.root
        if window_ref and event.widget == window_ref:
            # Cancel previous timer
            if self.resize_timer:
                window_ref.after_cancel(self.resize_timer)
            
            # Set new timer
            self.resize_timer = window_ref.after(300, self.refresh_current_preview_image)
    
    def refresh_current_preview_image(self):
        """Refresh the currently displayed image with new size."""
        if self.current_displayed_image:
            self.display_preview_image(self.current_displayed_image)
    
    def cleanup_preview_resources(self):
        """Clean up preview-related resources."""
        # Cancel timers
        if self.resize_timer:
            window_ref = self.window if hasattr(self, 'window') else self.root
            if window_ref and hasattr(window_ref, 'after_cancel'):
                try:
                    window_ref.after_cancel(self.resize_timer)
                except (tk.TclError, AttributeError):
                    pass
            self.resize_timer = None
        
        # Clear image references
        self.current_image = None
        self.current_displayed_image = None
        
        # Clear UI elements
        if self.image_label:
            try:
                self.image_label.config(image="", text="Preview closed", fg=Colors.TEXT_MUTED)
            except (tk.TclError, AttributeError):
                pass
        
        if self.prompt_display:
            try:
                self.prompt_display.set_text("")
            except (tk.TclError, AttributeError):
                pass
        
        # Cleanup image processor
        if self.image_processor and hasattr(self.image_processor, 'cleanup_resources'):
            try:
                self.image_processor.cleanup_resources()
            except (AttributeError, Exception):
                pass
    
    def bind_hover_for_preview(self, widget, image_filename):
        """Bind hover events to show image preview with modern effects."""
        def on_enter(event):
            # Add hover effect to the widget
            try:
                if hasattr(widget, 'config'):
                    original_bg = widget.cget('bg')
                    widget.config(bg=Colors.BG_HOVER)
                    
                    # Store original background for restoration
                    if not hasattr(widget, '_original_bg'):
                        widget._original_bg = original_bg
            except:
                pass
            
            # Show preview
            self.display_preview_image(image_filename)
        
        def on_leave(event):
            # Restore original background
            try:
                if hasattr(widget, '_original_bg'):
                    widget.config(bg=widget._original_bg)
            except:
                pass
        
        try:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            
            # Bind to children as well
            def bind_to_children(parent_widget):
                try:
                    for child in parent_widget.winfo_children():
                        child.bind("<Enter>", on_enter)
                        child.bind("<Leave>", on_leave)
                        bind_to_children(child)
                except (tk.TclError, AttributeError):
                    pass
            
            bind_to_children(widget)
        except (tk.TclError, AttributeError):
            pass
    
    def set_preview_empty_state(self):
        """Set the preview to show empty state with modern styling."""
        if self.image_label:
            self.image_label.config(
                image="",
                text="🖼️\nHover over an image to preview",
                fg=Colors.TEXT_MUTED,
                bg=Colors.BG_TERTIARY,
                font=Fonts.MEDIUM
            )
        
        if self.image_info_label:
            self.image_info_label.config(text="Select an image to view details", fg=Colors.TEXT_MUTED)
        
        if hasattr(self, 'additional_stats_label') and self.additional_stats_label:
            self.additional_stats_label.config(text="Statistics will appear here", fg=Colors.TEXT_MUTED)
        
        if self.prompt_display:
            self.prompt_display.set_text("Prompt information will appear here")
    
    def highlight_preview_element(self, element_type):
        """Highlight a specific element in the preview."""
        if element_type == 'image' and self.image_label:
            # Add glow effect to image
            self.image_label.config(highlightbackground=Colors.PURPLE_PRIMARY, highlightthickness=2)
            self.image_label.after(1000, lambda: self.image_label.config(highlightthickness=0))
        
        elif element_type == 'stats' and hasattr(self, 'additional_stats_label') and self.additional_stats_label:
            # Highlight stats temporarily
            original_fg = self.additional_stats_label.cget('fg')
            self.additional_stats_label.config(fg=Colors.PURPLE_PRIMARY)
            self.additional_stats_label.after(1000, lambda: self.additional_stats_label.config(fg=original_fg))
        
        elif element_type == 'prompt' and self.prompt_display:
            # Highlight prompt area
            self.prompt_display.text_widget.config(highlightbackground=Colors.PURPLE_PRIMARY, highlightthickness=2)
            self.prompt_display.text_widget.after(1000, lambda: self.prompt_display.text_widget.config(highlightthickness=1))
