"""
Image display controller for the Image Ranking System.

This module handles all image display logic, including loading, resizing,
and updating image information in the UI, including tier-based color theming.
"""

import tkinter as tk
import os
import gc
from typing import Optional, Dict, Any

from config import Colors, Defaults


class ImageDisplayController:
    """
    Handles image display and management for the main voting interface.
    
    This controller manages the left and right image display areas,
    including image loading, resizing, metadata display, and tier-based color theming.
    """
    
    def __init__(self, parent: tk.Tk, data_manager, image_processor, prompt_analyzer):
        """
        Initialize the image display controller.
        
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
        self.left_info_label = None
        self.left_metadata_label = None
        self.right_image_label = None
        self.right_info_label = None
        self.right_metadata_label = None
        
        # Store references to the left and right frames for vote button creation
        self.left_frame = None
        self.right_frame = None
        
        # Current displayed images (keep references to prevent garbage collection)
        self.current_images = {'left': None, 'right': None}
        
        # Preloaded images for better performance
        self.next_pair_images = {'left': None, 'right': None}
        
        # Timer reference for resize handling
        self.resize_timer = None
        
        # Bind resize events
        self.parent.bind('<Configure>', self.on_window_resize)
    
    def create_image_frames(self, parent: tk.Frame) -> None:
        """
        Create the left and right image display frames.
        
        Args:
            parent: Parent frame to contain the image frames
        """
        # Configure grid for side-by-side layout
        parent.grid_columnconfigure(0, weight=1, uniform="equal", minsize=400)
        parent.grid_columnconfigure(1, weight=0, minsize=80)  # VS label column
        parent.grid_columnconfigure(2, weight=1, uniform="equal", minsize=400)
        parent.grid_rowconfigure(0, weight=1, minsize=500)
        
        # Create left and right image frames and store references
        self.left_frame = self._create_single_image_frame(parent, 'left', 0)
        self._create_vs_label(parent)
        self.right_frame = self._create_single_image_frame(parent, 'right', 2)
    
    def _create_single_image_frame(self, parent: tk.Frame, side: str, column: int) -> tk.Frame:
        """Create an image display frame for one side of the comparison."""
        frame = tk.Frame(parent, relief=tk.RAISED, borderwidth=2, bg=Colors.BG_SECONDARY)
        frame.grid(row=0, column=column, sticky="nsew", padx=5)
        
        # Configure frame grid - text areas have fixed minimum sizes
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1, minsize=400)     # Image - expandable with minimum
        frame.grid_rowconfigure(1, weight=0, minsize=30)     # Info - fixed minimum
        frame.grid_rowconfigure(2, weight=0, minsize=60)     # Metadata - fixed minimum
        frame.grid_rowconfigure(3, weight=0, minsize=60)     # Vote button - fixed minimum
        
        # Image display label - expandable, takes most space
        image_label = tk.Label(frame, text="No image", 
                              bg=Colors.BG_TERTIARY, fg=Colors.TEXT_PRIMARY, cursor="hand2")
        image_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Info label showing stats - fixed minimum height
        info_label = tk.Label(frame, text="", font=('Arial', 10), 
                             fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY, height=2)
        info_label.grid(row=1, column=0, sticky="ew", pady=2)
        
        # Metadata label - fixed minimum height with text wrapping
        metadata_label = tk.Label(frame, text="", font=('Arial', 10), 
                                 fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY, 
                                 justify=tk.LEFT, height=3)
        metadata_label.grid(row=2, column=0, sticky="ew", padx=10, pady=2)
        
        # Store references
        if side == 'left':
            self.left_image_label = image_label
            self.left_info_label = info_label
            self.left_metadata_label = metadata_label
        else:
            self.right_image_label = image_label
            self.right_info_label = info_label
            self.right_metadata_label = metadata_label
        
        # Return the frame so it can be stored
        return frame
    
    def get_frames(self) -> tuple:
        """
        Get references to the left and right frames.
        
        Returns:
            Tuple of (left_frame, right_frame)
        """
        return self.left_frame, self.right_frame
    
    def _create_vs_label(self, parent: tk.Frame) -> None:
        """Create the VS label in the center of the main frame."""
        vs_label = tk.Label(parent, text="VS", font=('Arial', 24, 'bold'), 
                          fg=Colors.TEXT_PRIMARY, bg=Colors.BG_PRIMARY)
        vs_label.grid(row=0, column=1, padx=20)
    
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
    
    def _get_tier_colors(self, tier: int) -> Dict[str, str]:
        """
        Get color scheme based on image tier.
        
        Args:
            tier: The tier level of the image
            
        Returns:
            Dictionary with color values for different UI elements
        """
        if tier <= -2:
            # Red warning colors for tier -2 and lower (binning candidates)
            return {
                'frame_bg': Colors.BG_BINNING_SECONDARY,
                'image_bg': Colors.BG_BINNING_TERTIARY,
                'info_bg': Colors.BG_BINNING_SECONDARY,
                'metadata_bg': Colors.BG_BINNING_SECONDARY,
                'border_color': Colors.BORDER_BINNING
            }
        else:
            # Normal colors for all other tiers
            return {
                'frame_bg': Colors.BG_SECONDARY,
                'image_bg': Colors.BG_TERTIARY,
                'info_bg': Colors.BG_SECONDARY,
                'metadata_bg': Colors.BG_SECONDARY,
                'border_color': Colors.BORDER
            }
    
    def _update_frame_colors(self, side: str, tier: int) -> None:
        """
        Update the color scheme of a frame based on tier.
        
        Args:
            side: Which side to update ('left' or 'right')
            tier: The tier level to determine colors
        """
        colors = self._get_tier_colors(tier)
        
        if side == 'left':
            frame = self.left_frame
            image_label = self.left_image_label
            info_label = self.left_info_label
            metadata_label = self.left_metadata_label
        else:
            frame = self.right_frame
            image_label = self.right_image_label
            info_label = self.right_info_label
            metadata_label = self.right_metadata_label
        
        # Update frame colors
        if frame:
            frame.config(bg=colors['frame_bg'])
        
        # Only update label colors if they don't have images
        # (to avoid tkinter errors with image references)
        if image_label:
            try:
                # Check if label has an image by trying to get the image option
                current_image = image_label.cget('image')
                if not current_image or current_image == '':
                    # No image, safe to change background
                    image_label.config(bg=colors['image_bg'])
            except:
                # If there's any error, just update the background
                try:
                    image_label.config(bg=colors['image_bg'])
                except:
                    pass
        
        if info_label:
            info_label.config(bg=colors['info_bg'])
        if metadata_label:
            metadata_label.config(bg=colors['metadata_bg'])
    
    def display_image(self, filename: str, side: str) -> None:
        """
        Display an image on the specified side with tier-based coloring.
        
        Args:
            filename: Name of the image file to display
            side: Which side to display on ('left' or 'right')
        """
        try:
            img_path = os.path.join(self.data_manager.image_folder, filename)
            
            # Get tier for color scheme
            stats = self.data_manager.get_image_stats(filename)
            tier = stats.get('current_tier', 0)
            
            # Update frame colors based on tier
            self._update_frame_colors(side, tier)
            
            # Force window to update and get actual dimensions
            self.parent.update_idletasks()
            
            # Get the actual size of the image label area after layout
            if side == 'left':
                label_width = self.left_image_label.winfo_width()
                label_height = self.left_image_label.winfo_height()
            else:
                label_width = self.right_image_label.winfo_width()
                label_height = self.right_image_label.winfo_height()
            
            # Only proceed if we have valid dimensions (widget has been rendered)
            if label_width <= 1 or label_height <= 1:
                # Widget not yet rendered, try again after a short delay
                self.parent.after(100, lambda: self.display_image(filename, side))
                return
            
            # Use almost all available space, leaving small margin, but with reasonable minimums
            max_image_width = max(label_width - 20, 300)
            max_image_height = max(label_height - 20, 300)
            
            # Load and resize image to fill the available space
            photo = self.image_processor.load_and_resize_image(
                img_path, max_image_width, max_image_height)
            
            if photo:
                # Update image display
                if side == 'left':
                    self.left_image_label.config(image=photo, text="")
                    self.current_images['left'] = photo  # Keep reference
                else:
                    self.right_image_label.config(image=photo, text="")
                    self.current_images['right'] = photo  # Keep reference
                
                # Update info and metadata
                self.update_image_info(filename, side)
            else:
                # Handle image loading failure
                self._handle_image_load_error(filename, side)
            
        except Exception as e:
            print(f"Error displaying image {filename}: {e}")
            self._handle_image_load_error(filename, side)
    
    def update_image_info(self, filename: str, side: str) -> None:
        """
        Update the info and metadata labels for an image.
        
        Args:
            filename: Name of the image file
            side: Which side to update ('left' or 'right')
        """
        stats = self.data_manager.get_image_stats(filename)
        tier = stats.get('current_tier', 0)
        
        # Calculate individual stability (requires ranking algorithm)
        stability = 0.0
        confidence = 0.0
        if hasattr(self, 'ranking_algorithm'):
            stability = self.ranking_algorithm._calculate_tier_stability(filename)
            confidence = self.ranking_algorithm._calculate_image_confidence(filename)
        
        # Add binning warning indicator for low tiers
        tier_indicator = f"Tier: {tier}"
        if tier <= -2:
            tier_indicator += " ⚠️ BINNING CANDIDATE"
        
        # Create info text with selection method indication
        selection_indicator = "(Low confidence)" if side == 'left' else "(High confidence, low recency)"
        info_text = (f"{tier_indicator} | "
                    f"Wins: {stats.get('wins', 0)} | "
                    f"Losses: {stats.get('losses', 0)} | "
                    f"Stability: {stability:.2f} | "
                    f"Confidence: {confidence:.2f} {selection_indicator}")
        
        # Get prompt with lazy loading
        prompt = stats.get('prompt')
        if prompt is None:
            # Extract metadata on-demand for this specific image
            try:
                img_path = os.path.join(self.data_manager.image_folder, filename)
                prompt = self.image_processor.extract_prompt_from_image(img_path)
                # Also get display metadata while we're at it
                display_metadata = self.image_processor.get_image_metadata(img_path)
                self.data_manager.set_image_metadata(filename, prompt, display_metadata)
            except Exception as e:
                print(f"Error extracting metadata from {filename}: {e}")
                prompt = None
        
        # Format prompt text
        if prompt:
            # Extract only the main/positive prompt using the prompt analyzer
            main_prompt = self.prompt_analyzer.extract_main_prompt(prompt)
            if main_prompt:
                prompt_text = f"Prompt: {main_prompt}"
            else:
                prompt_text = "Prompt: (empty or unreadable)"
        else:
            prompt_text = "Prompt: No prompt found"
        
        # Update labels with dynamic wraplength
        if side == 'left':
            self.left_info_label.config(text=info_text)
            self._update_metadata_label(self.left_metadata_label, prompt_text)
        else:
            self.right_info_label.config(text=info_text)
            self._update_metadata_label(self.right_metadata_label, prompt_text)
    
    def _update_metadata_label(self, label: tk.Label, text: str) -> None:
        """Update a metadata label with proper text wrapping."""
        try:
            self.parent.update_idletasks()
            frame_width = label.winfo_width()
            if frame_width > 100:  # Only update if frame has been rendered
                label.config(text=text, wraplength=max(frame_width - 20, 300))
            else:
                label.config(text=text, wraplength=400)
        except:
            label.config(text=text, wraplength=400)
    
    def _handle_image_load_error(self, filename: str, side: str) -> None:
        """Handle image loading errors by updating UI appropriately."""
        if side == 'left':
            self.left_image_label.config(image="", text="Error loading image")
            self.current_images['left'] = None
        else:
            self.right_image_label.config(image="", text="Error loading image")
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
            max_image_width = max((window_width - 150) // 2, Defaults.MIN_IMAGE_WIDTH)
            max_image_height = max(window_height - 300, Defaults.MIN_IMAGE_HEIGHT)
            
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
            # Clear partially loaded images to prevent memory issues
            self.next_pair_images = {'left': None, 'right': None}
    
    def on_window_resize(self, event) -> None:
        """Handle window resize events with debouncing."""
        if event.widget == self.parent:
            # Cancel previous timer if it exists
            if self.resize_timer:
                self.parent.after_cancel(self.resize_timer)
            
            # Set a new timer to redraw images after resize stops
            self.resize_timer = self.parent.after(Defaults.RESIZE_DEBOUNCE_MS, self.refresh_current_images)
    
    def refresh_current_images(self) -> None:
        """Refresh the currently displayed images with new size."""
        # This will be called by the parent with the current pair
        pass
    
    def clear_images(self) -> None:
        """Clear all image references to help with garbage collection."""
        # Clear UI labels FIRST (before updating colors)
        if self.left_image_label:
            self.left_image_label.config(image="", text="No image")
        if self.right_image_label:
            self.right_image_label.config(image="", text="No image")
        
        # Clear current displayed images
        self.current_images['left'] = None
        self.current_images['right'] = None
        
        # Clear preloaded images
        self.next_pair_images['left'] = None
        self.next_pair_images['right'] = None
        
        # NOW reset frame colors to normal (after clearing images)
        self._update_frame_colors('left', 0)
        self._update_frame_colors('right', 0)
        
        # Force garbage collection
        gc.collect()
    
    def set_ranking_algorithm(self, ranking_algorithm) -> None:
        """Set the ranking algorithm reference for stability calculations."""
        self.ranking_algorithm = ranking_algorithm
    
    def cleanup(self) -> None:
        """Clean up resources."""
        # Cancel any pending timers
        if self.resize_timer:
            self.parent.after_cancel(self.resize_timer)
        
        # Clear all image references
        self.clear_images()
