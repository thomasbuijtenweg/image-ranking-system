"""
Modern image display controller for the Image Ranking System.

This module handles all image display logic with modern UI styling,
including loading, resizing, and updating image information.
"""

import tkinter as tk
import os
import gc
from typing import Optional, Dict, Any

from config import Colors, Fonts, Styling, UIComponents


class ModernImageLabel(tk.Label):
    """Custom image label with modern styling and hover effects."""
    
    def __init__(self, parent, **kwargs):
        # Default modern styling
        style_config = {
            'bg': Colors.BG_TERTIARY,
            'fg': Colors.TEXT_SECONDARY,
            'font': Fonts.MEDIUM,
            'cursor': 'hand2',
            'relief': 'flat',
            'borderwidth': 0,
            'highlightthickness': 0
        }
        
        final_config = {**style_config, **kwargs}
        super().__init__(parent, **final_config)
        
        # Add hover effects
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
    
    def _on_enter(self, event):
        """Handle hover enter."""
        if self.cget('image'):
            self.configure(bg=Colors.BG_HOVER)
    
    def _on_leave(self, event):
        """Handle hover leave."""
        self.configure(bg=Colors.BG_TERTIARY)


class ModernInfoCard(tk.Frame):
    """Modern information card with sleek styling."""
    
    def __init__(self, parent, title="", **kwargs):
        style_config = {
            'bg': Colors.BG_CARD,
            'relief': 'flat',
            'borderwidth': 1,
            'highlightbackground': Colors.BORDER_PRIMARY,
            'highlightthickness': 1
        }
        
        final_config = {**style_config, **kwargs}
        super().__init__(parent, **final_config)
        
        # Title if provided
        if title:
            title_label = tk.Label(self, text=title,
                                  font=Fonts.HEADING,
                                  fg=Colors.PURPLE_PRIMARY,
                                  bg=Colors.BG_CARD)
            title_label.pack(anchor=tk.W, padx=Styling.PADDING_MEDIUM, pady=(Styling.PADDING_MEDIUM, 0))
        
        # Content frame
        self.content_frame = tk.Frame(self, bg=Colors.BG_CARD)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=Styling.PADDING_MEDIUM, pady=Styling.PADDING_MEDIUM)
    
    def add_content(self, widget):
        """Add content to the card."""
        widget.pack(in_=self.content_frame, fill=tk.X)


class ImageDisplayController:
    """
    Modern image display controller with sleek UI design.
    
    This controller manages the left and right image display areas,
    including image loading, resizing, and metadata display with modern styling.
    """
    
    def __init__(self, parent: tk.Tk, data_manager, image_processor, prompt_analyzer):
        """
        Initialize the modern image display controller.
        
        Args:
            parent: Parent tkinter window
            data_manager: DataManager instance
            image_processor: ImageProcessor instance
            prompt_analyzer: PromptAnalyzer instance
        """
        self.parent = parent
        self.data_manager = data_manager
        self.image_processor = image_processor
        self.prompt_analyzer = prompt_analyzer
        
        # UI references
        self.left_image_label = None
        self.left_info_card = None
        self.left_metadata_card = None
        self.right_image_label = None
        self.right_info_card = None
        self.right_metadata_card = None
        
        # Store references to frames for vote button creation
        self.left_frame = None
        self.right_frame = None
        
        # Current displayed images
        self.current_images = {'left': None, 'right': None}
        
        # Preloaded images
        self.next_pair_images = {'left': None, 'right': None}
        
        # Timer reference for resize handling
        self.resize_timer = None
        
        # Bind resize events
        self.parent.bind('<Configure>', self.on_window_resize)
    
    def create_image_frames(self, parent: tk.Frame) -> None:
        """
        Create modern image display frames with sleek styling.
        
        Args:
            parent: Parent frame to contain the image frames
        """
        # Configure grid for modern layout
        parent.grid_columnconfigure(0, weight=1, uniform="equal", minsize=450)
        parent.grid_columnconfigure(1, weight=0, minsize=100)  # VS section
        parent.grid_columnconfigure(2, weight=1, uniform="equal", minsize=450)
        parent.grid_rowconfigure(0, weight=1, minsize=600)
        
        # Create image frames
        self.left_frame = self._create_modern_image_frame(parent, 'left', 0)
        self._create_modern_vs_section(parent)
        self.right_frame = self._create_modern_image_frame(parent, 'right', 2)
    
    def _create_modern_image_frame(self, parent: tk.Frame, side: str, column: int) -> tk.Frame:
        """Create a modern image display frame for one side."""
        # Main frame with modern card styling
        frame = tk.Frame(parent, 
                        bg=Colors.BG_CARD,
                        relief='flat',
                        borderwidth=1,
                        highlightbackground=Colors.BORDER_PRIMARY,
                        highlightthickness=1)
        frame.grid(row=0, column=column, sticky="nsew", 
                  padx=(Styling.PADDING_LARGE if column == 0 else Styling.PADDING_MEDIUM,
                        Styling.PADDING_LARGE if column == 2 else Styling.PADDING_MEDIUM))
        
        # Configure frame grid
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1, minsize=450)     # Image area
        frame.grid_rowconfigure(1, weight=0, minsize=80)     # Info area
        frame.grid_rowconfigure(2, weight=0, minsize=100)    # Metadata area
        frame.grid_rowconfigure(3, weight=0, minsize=60)     # Button area
        
        # Image display area with modern styling
        image_container = tk.Frame(frame, bg=Colors.BG_CARD)
        image_container.grid(row=0, column=0, sticky="nsew", 
                           padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        image_label = ModernImageLabel(image_container, text="No image selected")
        image_label.pack(fill=tk.BOTH, expand=True)
        
        # Info card with modern styling
        info_card = ModernInfoCard(frame)
        info_card.grid(row=1, column=0, sticky="ew", 
                      padx=Styling.PADDING_LARGE, pady=(0, Styling.PADDING_SMALL))
        
        info_label = tk.Label(info_card.content_frame,
                             text="",
                             font=Fonts.MEDIUM,
                             fg=Colors.TEXT_PRIMARY,
                             bg=Colors.BG_CARD,
                             justify=tk.CENTER)
        info_label.pack(fill=tk.X)
        
        # Metadata card with modern styling
        metadata_card = ModernInfoCard(frame, title="Prompt")
        metadata_card.grid(row=2, column=0, sticky="ew", 
                          padx=Styling.PADDING_LARGE, pady=(0, Styling.PADDING_SMALL))
        
        metadata_label = tk.Label(metadata_card.content_frame,
                                 text="",
                                 font=Fonts.SMALL,
                                 fg=Colors.TEXT_SECONDARY,
                                 bg=Colors.BG_CARD,
                                 justify=tk.LEFT,
                                 wraplength=400)
        metadata_label.pack(fill=tk.X)
        
        # Store references
        if side == 'left':
            self.left_image_label = image_label
            self.left_info_card = info_label
            self.left_metadata_card = metadata_label
        else:
            self.right_image_label = image_label
            self.right_info_card = info_label
            self.right_metadata_card = metadata_label
        
        return frame
    
    def _create_modern_vs_section(self, parent: tk.Frame) -> None:
        """Create the modern VS section with sleek styling."""
        vs_frame = tk.Frame(parent, bg=Colors.BG_PRIMARY)
        vs_frame.grid(row=0, column=1, sticky="nsew", padx=Styling.PADDING_SMALL)
        
        # VS container with modern card styling
        vs_container = tk.Frame(vs_frame,
                               bg=Colors.BG_CARD,
                               relief='flat',
                               borderwidth=1,
                               highlightbackground=Colors.BORDER_PRIMARY,
                               highlightthickness=1)
        vs_container.pack(fill=tk.BOTH, expand=True, pady=Styling.PADDING_LARGE)
        
        # VS label with modern typography
        vs_label = tk.Label(vs_container,
                           text="VS",
                           font=Fonts.DISPLAY,
                           fg=Colors.PURPLE_PRIMARY,
                           bg=Colors.BG_CARD)
        vs_label.pack(expand=True)
        
        # Add decorative elements
        top_line = tk.Frame(vs_container, height=2, bg=Colors.PURPLE_PRIMARY)
        top_line.pack(fill=tk.X, padx=Styling.PADDING_LARGE, pady=(Styling.PADDING_LARGE, 0))
        
        bottom_line = tk.Frame(vs_container, height=2, bg=Colors.PURPLE_PRIMARY)
        bottom_line.pack(fill=tk.X, padx=Styling.PADDING_LARGE, pady=(0, Styling.PADDING_LARGE))
    
    def get_frames(self) -> tuple:
        """
        Get references to the left and right frames.
        
        Returns:
            Tuple of (left_frame, right_frame)
        """
        return self.left_frame, self.right_frame
    
    def bind_click_handlers(self, left_callback, right_callback) -> None:
        """
        Bind click handlers to the image labels.
        
        Args:
            left_callback: Function to call when left image is clicked
            right_callback: Function to call when right image is clicked
        """
        if self.left_image_label:
            self.left_image_label.bind("<Button-1>", lambda e: left_callback())
        if self.right_image_label:
            self.right_image_label.bind("<Button-1>", lambda e: right_callback())
    
    def display_image(self, filename: str, side: str) -> None:
        """
        Display an image on the specified side with modern styling.
        
        Args:
            filename: Name of the image file to display
            side: Which side to display on ('left' or 'right')
        """
        try:
            img_path = os.path.join(self.data_manager.image_folder, filename)
            
            # Force window to update and get dimensions
            self.parent.update_idletasks()
            
            # Get label dimensions
            if side == 'left':
                label_width = self.left_image_label.winfo_width()
                label_height = self.left_image_label.winfo_height()
            else:
                label_width = self.right_image_label.winfo_width()
                label_height = self.right_image_label.winfo_height()
            
            # Check if widget is rendered
            if label_width <= 1 or label_height <= 1:
                self.parent.after(100, lambda: self.display_image(filename, side))
                return
            
            # Calculate image size with padding
            max_image_width = max(label_width - 20, 350)
            max_image_height = max(label_height - 20, 350)
            
            # Load and resize image
            photo = self.image_processor.load_and_resize_image(
                img_path, max_image_width, max_image_height)
            
            if photo:
                # Update image display
                if side == 'left':
                    self.left_image_label.config(image=photo, text="")
                    self.current_images['left'] = photo
                else:
                    self.right_image_label.config(image=photo, text="")
                    self.current_images['right'] = photo
                
                # Update info and metadata
                self.update_image_info(filename, side)
            else:
                self._handle_image_load_error(filename, side)
            
        except Exception as e:
            print(f"Error displaying image {filename}: {e}")
            self._handle_image_load_error(filename, side)
    
    def update_image_info(self, filename: str, side: str) -> None:
        """
        Update the info and metadata displays with modern styling.
        
        Args:
            filename: Name of the image file
            side: Which side to update ('left' or 'right')
        """
        stats = self.data_manager.get_image_stats(filename)
        
        # Calculate metrics
        stability = 0.0
        confidence = 0.0
        if hasattr(self, 'ranking_algorithm'):
            stability = self.ranking_algorithm._calculate_tier_stability(filename)
            confidence = self.ranking_algorithm._calculate_image_confidence(filename)
        
        # Create modern info display
        tier = stats.get('current_tier', 0)
        tier_text = f"Tier {tier:+d}" if tier != 0 else "Tier 0"
        
        wins = stats.get('wins', 0)
        losses = stats.get('losses', 0)
        
        # Color-code tier
        if tier > 0:
            tier_color = Colors.SUCCESS
        elif tier < 0:
            tier_color = Colors.ERROR
        else:
            tier_color = Colors.TEXT_SECONDARY
        
        # Selection indicator with modern styling
        selection_indicator = "🔍 Low Confidence" if side == 'left' else "⭐ High Confidence"
        
        info_text = f"{tier_text} | {wins}W {losses}L | {selection_indicator}"
        
        # Get prompt for metadata
        prompt = stats.get('prompt')
        if prompt is None:
            try:
                img_path = os.path.join(self.data_manager.image_folder, filename)
                prompt = self.image_processor.extract_prompt_from_image(img_path)
                display_metadata = self.image_processor.get_image_metadata(img_path)
                self.data_manager.set_image_metadata(filename, prompt, display_metadata)
            except Exception as e:
                print(f"Error extracting metadata from {filename}: {e}")
                prompt = None
        
        # Format prompt with modern styling
        if prompt:
            main_prompt = self.prompt_analyzer.extract_main_prompt(prompt)
            if main_prompt:
                # Truncate long prompts elegantly
                if len(main_prompt) > 200:
                    prompt_text = main_prompt[:197] + "..."
                else:
                    prompt_text = main_prompt
            else:
                prompt_text = "No readable prompt data"
        else:
            prompt_text = "No prompt metadata found"
        
        # Update displays
        if side == 'left':
            self.left_info_card.config(text=info_text, fg=tier_color)
            self.left_metadata_card.config(text=prompt_text)
        else:
            self.right_info_card.config(text=info_text, fg=tier_color)
            self.right_metadata_card.config(text=prompt_text)
    
    def _handle_image_load_error(self, filename: str, side: str) -> None:
        """Handle image loading errors with modern error display."""
        error_text = "⚠️ Failed to load image"
        
        if side == 'left':
            self.left_image_label.config(image="", text=error_text, fg=Colors.ERROR)
            self.left_info_card.config(text=f"Error: {filename}", fg=Colors.ERROR)
            self.left_metadata_card.config(text="Unable to load image metadata")
            self.current_images['left'] = None
        else:
            self.right_image_label.config(image="", text=error_text, fg=Colors.ERROR)
            self.right_info_card.config(text=f"Error: {filename}", fg=Colors.ERROR)
            self.right_metadata_card.config(text="Unable to load image metadata")
            self.current_images['right'] = None
    
    def preload_images(self, img1: str, img2: str) -> None:
        """
        Preload images for better performance.
        
        Args:
            img1: First image filename
            img2: Second image filename
        """
        # Clear old preloaded images
        self.next_pair_images = {'left': None, 'right': None}
        
        try:
            # Calculate display dimensions
            self.parent.update_idletasks()
            window_width = self.parent.winfo_width()
            window_height = self.parent.winfo_height()
            max_image_width = max((window_width - 200) // 2, 350)
            max_image_height = max(window_height - 400, 350)
            
            # Preload images
            for idx, filename in enumerate([img1, img2]):
                img_path = os.path.join(self.data_manager.image_folder, filename)
                photo = self.image_processor.load_and_resize_image(
                    img_path, max_image_width, max_image_height)
                
                if photo:
                    side = 'left' if idx == 0 else 'right'
                    self.next_pair_images[side] = photo
                    
        except Exception as e:
            print(f"Error preloading images: {e}")
            self.next_pair_images = {'left': None, 'right': None}
    
    def on_window_resize(self, event) -> None:
        """Handle window resize events with debouncing."""
        if event.widget == self.parent:
            # Cancel previous timer
            if self.resize_timer:
                self.parent.after_cancel(self.resize_timer)
            
            # Set new timer
            self.resize_timer = self.parent.after(300, self.refresh_current_images)
    
    def refresh_current_images(self) -> None:
        """Refresh the currently displayed images with new size."""
        pass  # Will be called by parent with current pair
    
    def clear_images(self) -> None:
        """Clear all image references with modern styling."""
        # Clear current images
        self.current_images['left'] = None
        self.current_images['right'] = None
        
        # Clear preloaded images
        self.next_pair_images['left'] = None
        self.next_pair_images['right'] = None
        
        # Clear UI labels with modern no-image display
        no_image_text = "No image selected"
        if self.left_image_label:
            self.left_image_label.config(image="", text=no_image_text, fg=Colors.TEXT_SECONDARY)
        if self.right_image_label:
            self.right_image_label.config(image="", text=no_image_text, fg=Colors.TEXT_SECONDARY)
        
        # Clear info cards
        if self.left_info_card:
            self.left_info_card.config(text="", fg=Colors.TEXT_SECONDARY)
        if self.right_info_card:
            self.right_info_card.config(text="", fg=Colors.TEXT_SECONDARY)
        
        # Clear metadata cards
        if self.left_metadata_card:
            self.left_metadata_card.config(text="Select images to view prompts")
        if self.right_metadata_card:
            self.right_metadata_card.config(text="Select images to view prompts")
        
        # Force garbage collection
        gc.collect()
    
    def set_ranking_algorithm(self, ranking_algorithm) -> None:
        """Set the ranking algorithm reference."""
        self.ranking_algorithm = ranking_algorithm
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.resize_timer:
            self.parent.after_cancel(self.resize_timer)
        
        self.clear_images()
