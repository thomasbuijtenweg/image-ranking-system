"""
Voting controller for the Image Ranking System.

This module handles all voting logic, pair selection, and voting state management.
"""

import tkinter as tk
from typing import Optional, Tuple

from config import Colors, Defaults


class VotingController:
    """
    Handles voting logic and pair management for the main interface.
    
    This controller manages the voting process, pair selection,
    and coordination between different components.
    """
    
    def __init__(self, parent: tk.Tk, data_manager, ranking_algorithm, image_processor, image_display):
        """
        Initialize the voting controller.
        
        Args:
            parent: Parent tkinter window
            data_manager: DataManager instance
            ranking_algorithm: RankingAlgorithm instance
            image_processor: ImageProcessor instance
            image_display: ImageDisplayController instance
        """
        self.parent = parent
        self.data_manager = data_manager
        self.ranking_algorithm = ranking_algorithm
        self.image_processor = image_processor
        self.image_display = image_display
        
        # Voting state
        self.current_pair = (None, None)
        self.next_pair = (None, None)
        self.previous_pair = (None, None)
        
        # UI references
        self.left_vote_button = None
        self.right_vote_button = None
        self.status_bar = None
        self.stats_label = None
        
        # Timer references
        self.preload_timer = None
        
        # Callbacks
        self.on_vote_callback = None
    
    def create_vote_buttons(self, left_frame: tk.Frame, right_frame: tk.Frame) -> None:
        """
        Create vote buttons for both sides.
        
        Args:
            left_frame: Frame for the left vote button
            right_frame: Frame for the right vote button
        """
        # Left vote button
        self.left_vote_button = tk.Button(
            left_frame, 
            text="Vote for this image (←)", 
            command=lambda: self.vote('left'), 
            state=tk.DISABLED, 
            font=('Arial', 12, 'bold'),
            bg=Colors.BUTTON_SUCCESS, 
            fg='white', 
            height=2, 
            relief=tk.FLAT
        )
        self.left_vote_button.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        
        # Right vote button
        self.right_vote_button = tk.Button(
            right_frame, 
            text="Vote for this image (→)", 
            command=lambda: self.vote('right'), 
            state=tk.DISABLED, 
            font=('Arial', 12, 'bold'),
            bg=Colors.BUTTON_SUCCESS, 
            fg='white', 
            height=2, 
            relief=tk.FLAT
        )
        self.right_vote_button.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        
        # Bind click handlers to image labels
        self.image_display.bind_click_handlers(
            lambda: self.vote('left'),
            lambda: self.vote('right')
        )
    
    def set_ui_references(self, status_bar: tk.Label, stats_label: tk.Label) -> None:
        """
        Set references to UI elements that need to be updated.
        
        Args:
            status_bar: Status bar label
            stats_label: Statistics label
        """
        self.status_bar = status_bar
        self.stats_label = stats_label
    
    def set_vote_callback(self, callback) -> None:
        """
        Set callback function to be called after each vote.
        
        Args:
            callback: Function to call after voting
        """
        self.on_vote_callback = callback
    
    def show_next_pair(self) -> None:
        """Display the next pair of images for voting."""
        if self.data_manager.image_folder == "":
            return
        
        # Safety check - ensure vote buttons exist
        if self.left_vote_button is None or self.right_vote_button is None:
            print("Warning: Vote buttons not created yet")
            return
        
        # Get available images
        images = self.image_processor.get_image_files(self.data_manager.image_folder)
        if len(images) < 2:
            return
        
        # Clear old images before loading new ones
        self.image_display.clear_images()
        
        # Store current pair as previous
        if self.current_pair[0] and self.current_pair[1]:
            self.previous_pair = self.current_pair
        
        # Get next pair using ranking algorithm with separate weights
        img1, img2 = self.ranking_algorithm.select_next_pair(images, self.previous_pair)
        if not img1 or not img2:
            return
        
        self.current_pair = (img1, img2)
        
        # Display images
        self.image_display.display_image(img1, 'left')
        self.image_display.display_image(img2, 'right')
        
        # Enable voting buttons
        self.left_vote_button.config(state=tk.NORMAL)
        self.right_vote_button.config(state=tk.NORMAL)
        
        # Update status with explanation
        explanation = self.ranking_algorithm.get_selection_explanation(img1, img2)
        if self.status_bar:
            self.status_bar.config(text=explanation)
        
        # Cancel any existing preload timer
        if self.preload_timer:
            self.parent.after_cancel(self.preload_timer)
        
        # Preload next pair in background
        self.preload_timer = self.parent.after(Defaults.PRELOAD_DELAY_MS, self.preload_next_pair)
    
    def preload_next_pair(self) -> None:
        """Preload the next pair of images in the background."""
        if self.data_manager.image_folder == "":
            return
        
        images = self.image_processor.get_image_files(self.data_manager.image_folder)
        if len(images) < 2:
            return
        
        # Get next pair (excluding current pair)
        self.next_pair = self.ranking_algorithm.select_next_pair(images, self.current_pair)
        
        if self.next_pair[0] and self.next_pair[1]:
            # Preload the images
            self.image_display.preload_images(self.next_pair[0], self.next_pair[1])
    
    def vote(self, side: str) -> None:
        """
        Process a vote for the specified side.
        
        Args:
            side: Which side won ('left' or 'right')
        """
        if not self.current_pair[0] or not self.current_pair[1]:
            return
        
        # Safety check - ensure vote buttons exist
        if self.left_vote_button is None or self.right_vote_button is None:
            print("Warning: Vote buttons not created yet")
            return
        
        winner = self.current_pair[0] if side == 'left' else self.current_pair[1]
        loser = self.current_pair[1] if side == 'left' else self.current_pair[0]
        
        # Record the vote
        self.data_manager.record_vote(winner, loser)
        
        # Invalidate cached rankings
        self.ranking_algorithm.invalidate_cache()
        
        # Update UI
        if self.stats_label:
            self.stats_label.config(text=f"Total votes: {self.data_manager.vote_count}")
        
        if self.status_bar:
            self.status_bar.config(text=f"Vote recorded: {winner} wins over {loser}")
        
        # Disable buttons temporarily
        self.left_vote_button.config(state=tk.DISABLED)
        self.right_vote_button.config(state=tk.DISABLED)
        
        # Call callback if set
        if self.on_vote_callback:
            self.on_vote_callback(winner, loser)
        
        # Show next pair after delay
        self.parent.after(Defaults.VOTE_DELAY_MS, self.show_next_pair)
    
    def refresh_current_pair(self) -> None:
        """Refresh the currently displayed pair (e.g., after window resize)."""
        if self.current_pair[0] and self.current_pair[1]:
            self.image_display.display_image(self.current_pair[0], 'left')
            self.image_display.display_image(self.current_pair[1], 'right')
    
    def setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts for voting."""
        from config import KeyBindings
        
        # Voting shortcuts
        for key in KeyBindings.VOTE_LEFT:
            self.parent.bind(key, lambda e: self.vote('left') if self.left_vote_button and self.left_vote_button['state'] == tk.NORMAL else None)
        
        for key in KeyBindings.VOTE_RIGHT:
            self.parent.bind(key, lambda e: self.vote('right') if self.right_vote_button and self.right_vote_button['state'] == tk.NORMAL else None)
    
    def reset_voting_state(self) -> None:
        """Reset voting state when loading new images."""
        self.current_pair = (None, None)
        self.next_pair = (None, None)
        self.previous_pair = (None, None)
        
        # Disable voting buttons
        if self.left_vote_button:
            self.left_vote_button.config(state=tk.DISABLED)
        if self.right_vote_button:
            self.right_vote_button.config(state=tk.DISABLED)
        
        # Clear status
        if self.status_bar:
            self.status_bar.config(text="Select a folder to begin")
    
    def cleanup(self) -> None:
        """Clean up resources."""
        # Cancel any pending timers
        if self.preload_timer:
            self.parent.after_cancel(self.preload_timer)
        
        # Reset state
        self.reset_voting_state()
