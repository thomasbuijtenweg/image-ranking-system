"""Reusable UI components for the Image Ranking System."""

import tkinter as tk
from tkinter import ttk
import os
from config import Colors


class ImagePreviewMixin:
    """Mixin class for image preview functionality."""
    
    def __init__(self):
        self.image_label = None
        self.image_info_label = None
        self.additional_stats_label = None
        self.prompt_text = None
        self.current_image = None
        self.current_displayed_image = None
        self.resize_timer = None
        self.image_processor = None
        
    def create_image_preview_area(self, parent, include_additional_stats=True):
        """Create the image preview area layout."""
        preview_frame = tk.Frame(parent, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=2)
        
        preview_frame.grid_columnconfigure(0, weight=1)
        row = 0
        
        # Title
        title_label = tk.Label(preview_frame, text="Image Preview", 
                              font=('Arial', 14, 'bold'), 
                              fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY,
                              height=2)
        title_label.grid(row=row, column=0, sticky="ew", pady=5)
        preview_frame.grid_rowconfigure(row, weight=0, minsize=50)
        row += 1
        
        # Image display
        self.image_label = tk.Label(preview_frame, text="Hover over an image\nto preview", 
                                   bg=Colors.BG_TERTIARY, fg=Colors.TEXT_SECONDARY,
                                   font=('Arial', 12), justify=tk.CENTER)
        self.image_label.grid(row=row, column=0, sticky="nsew", padx=10, pady=5)
        preview_frame.grid_rowconfigure(row, weight=1, minsize=400)
        row += 1
        
        # Image info
        self.image_info_label = tk.Label(preview_frame, text="", 
                                        font=('Arial', 11), 
                                        fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY,
                                        justify=tk.CENTER, height=2)
        self.image_info_label.grid(row=row, column=0, sticky="ew", pady=2)
        preview_frame.grid_rowconfigure(row, weight=0, minsize=60)
        row += 1
        
        # Additional stats
        if include_additional_stats:
            self.additional_stats_label = tk.Label(preview_frame, text="", 
                                                 font=('Arial', 10), 
                                                 fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY,
                                                 justify=tk.CENTER, height=2)
            self.additional_stats_label.grid(row=row, column=0, sticky="ew", pady=2)
            preview_frame.grid_rowconfigure(row, weight=0, minsize=60)
            row += 1
        
        # Prompt display
        prompt_frame = tk.Frame(preview_frame, bg=Colors.BG_SECONDARY)
        prompt_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        prompt_frame.grid_columnconfigure(0, weight=1)
        prompt_frame.grid_rowconfigure(0, weight=0)
        prompt_frame.grid_rowconfigure(1, weight=1)
        preview_frame.grid_rowconfigure(row, weight=0, minsize=120)
        
        tk.Label(prompt_frame, text="Prompt:", font=('Arial', 10, 'bold'), 
                fg=Colors.TEXT_SUCCESS, bg=Colors.BG_SECONDARY).grid(row=0, column=0, sticky="w")
        
        self.prompt_text = tk.Text(prompt_frame, height=4, wrap=tk.WORD, 
                                  bg=Colors.BG_TERTIARY, fg=Colors.TEXT_PRIMARY, 
                                  font=('Arial', 10), relief=tk.FLAT, state=tk.DISABLED)
        prompt_scrollbar = ttk.Scrollbar(prompt_frame, orient="vertical", command=self.prompt_text.yview)
        self.prompt_text.configure(yscrollcommand=prompt_scrollbar.set)
        
        self.prompt_text.grid(row=1, column=0, sticky="ew", pady=2)
        prompt_scrollbar.grid(row=1, column=1, sticky="ns")
        
        return preview_frame
    
    def display_preview_image(self, filename):
        """Display a preview image."""
        if not filename or not hasattr(self, 'data_manager') or not self.data_manager.image_folder:
            return
        
        try:
            img_path = os.path.join(self.data_manager.image_folder, filename)
            if not os.path.exists(img_path):
                return
            
            if hasattr(self, 'window'):
                self.window.update_idletasks()
            else:
                self.root.update_idletasks()
            
            label_width = self.image_label.winfo_width()
            label_height = self.image_label.winfo_height()
            
            if label_width <= 1 or label_height <= 1:
                window_ref = self.window if hasattr(self, 'window') else self.root
                window_ref.after(100, lambda: self.display_preview_image(filename))
                return
            
            preview_width = max(label_width - 10, 300)
            preview_height = max(label_height - 10, 300)
            
            photo = self.image_processor.load_and_resize_image(
                img_path, preview_width, preview_height)
            
            if photo:
                self.current_image = None
                self.image_label.config(image=photo, text="")
                self.current_image = photo
                self.current_displayed_image = filename
                self.update_image_info_display(filename)
            else:
                self.handle_image_load_error(filename)
                
        except Exception as e:
            print(f"Error displaying preview for {filename}: {e}")
            self.handle_image_load_error(filename)
    
    def update_image_info_display(self, filename):
        """Update the image info and stats displays."""
        if not hasattr(self, 'data_manager'):
            return
            
        stats = self.data_manager.get_image_stats(filename)
        
        votes = stats.get('votes', 0)
        wins = stats.get('wins', 0)
        win_rate = wins / votes if votes > 0 else 0
        
        info_text = (f"{filename}\n"
                    f"Tier: {stats.get('current_tier', 0)} | "
                    f"Votes: {votes}")
        self.image_info_label.config(text=info_text)
        
        if hasattr(self, 'additional_stats_label') and self.additional_stats_label:
            stability = 0
            if hasattr(self, 'ranking_algorithm'):
                stability = self.ranking_algorithm._calculate_tier_stability(filename)
            
            additional_text = (f"Win Rate: {win_rate:.1%} ({wins}/{votes})\n"
                             f"Stability: {stability:.2f} | "
                             f"Last voted: {stats.get('last_voted', 'Never')}")
            self.additional_stats_label.config(text=additional_text)
        
        if self.prompt_text:
            prompt = stats.get('prompt', '')
            self.prompt_text.config(state=tk.NORMAL)
            self.prompt_text.delete(1.0, tk.END)
            if prompt:
                self.prompt_text.insert(1.0, prompt)
            else:
                self.prompt_text.insert(1.0, "No prompt information available")
            self.prompt_text.config(state=tk.DISABLED)
    
    def handle_image_load_error(self, filename):
        """Handle image loading errors."""
        if self.image_label:
            self.image_label.config(image="", text="Failed to load image")
        
        if self.image_info_label:
            self.image_info_label.config(text=f"Error loading: {filename}")
        
        if hasattr(self, 'additional_stats_label') and self.additional_stats_label:
            self.additional_stats_label.config(text="")
        
        if self.prompt_text:
            self.prompt_text.config(state=tk.NORMAL)
            self.prompt_text.delete(1.0, tk.END)
            self.prompt_text.insert(1.0, "Error loading image")
            self.prompt_text.config(state=tk.DISABLED)
        
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
            if self.resize_timer:
                window_ref.after_cancel(self.resize_timer)
            
            self.resize_timer = window_ref.after(300, self.refresh_current_preview_image)
    
    def refresh_current_preview_image(self):
        """Refresh the currently displayed image with new size."""
        if self.current_displayed_image:
            self.display_preview_image(self.current_displayed_image)
    
    def cleanup_preview_resources(self):
        """Clean up preview-related resources."""
        if self.resize_timer:
            window_ref = self.window if hasattr(self, 'window') else self.root
            if window_ref and hasattr(window_ref, 'after_cancel'):
                try:
                    window_ref.after_cancel(self.resize_timer)
                except (tk.TclError, AttributeError):
                    pass
            self.resize_timer = None
        
        self.current_image = None
        self.current_displayed_image = None
        
        if self.image_label:
            try:
                self.image_label.config(image="")
            except (tk.TclError, AttributeError):
                pass
        
        if hasattr(self, 'prompt_text') and self.prompt_text:
            try:
                self.prompt_text.config(state=tk.NORMAL)
                self.prompt_text.delete(1.0, tk.END)
                self.prompt_text.config(state=tk.DISABLED)
            except (tk.TclError, AttributeError):
                pass
        
        if self.image_processor and hasattr(self.image_processor, 'cleanup_resources'):
            try:
                self.image_processor.cleanup_resources()
            except (AttributeError, Exception):
                pass
    
    def bind_hover_for_preview(self, widget, image_filename):
        """Bind hover events to show image preview."""
        def on_enter(event):
            self.display_preview_image(image_filename)
        
        def on_leave(event):
            pass
        
        try:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            
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