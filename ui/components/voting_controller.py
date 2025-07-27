"""Voting controller for the Image Ranking System with toggle bin mode - UPDATED."""

import tkinter as tk
from tkinter import messagebox
from typing import Optional, Tuple

from config import Colors, Defaults
from core.image_binner import ImageBinner


class VotingController:
    """Handles voting logic and pair management for the main interface."""
    
    def __init__(self, parent: tk.Tk, data_manager, ranking_algorithm, image_processor, image_display):
        print("VotingController: Initializing...")
        self.parent = parent
        self.data_manager = data_manager
        self.ranking_algorithm = ranking_algorithm
        self.image_processor = image_processor
        self.image_display = image_display
        
        self.current_pair = (None, None)
        self.next_pair = (None, None)
        self.previous_pair = (None, None)
        self.last_vote_result = None  # Track last vote for binning
        
        # NEW: Bin mode toggle state
        self.bin_mode = False
        
        self.left_vote_button = None
        self.right_vote_button = None
        self.status_bar = None
        self.stats_label = None
        
        self.preload_timer = None
        
        self.on_vote_callback = None
        
        # Image binner - will be initialized when folder is set
        self.image_binner = None
        self.image_folder_path = None  # Track the folder path for debugging
        print("VotingController: Initialization complete")
    
    def create_vote_buttons(self, left_frame: tk.Frame, right_frame: tk.Frame) -> None:
        """Create vote buttons for both sides."""
        print("VotingController: Creating vote buttons...")
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
        
        self.image_display.bind_click_handlers(
            lambda: self.vote('left'),
            lambda: self.vote('right')
        )
        print("VotingController: Vote buttons created successfully")
    
    def set_ui_references(self, status_bar: tk.Label, stats_label: tk.Label) -> None:
        """Set references to UI elements that need to be updated."""
        print("VotingController: Setting UI references...")
        self.status_bar = status_bar
        self.stats_label = stats_label
        print("VotingController: UI references set")
    
    def set_vote_callback(self, callback) -> None:
        """Set callback function to be called after each vote."""
        self.on_vote_callback = callback
    
    def set_image_folder(self, folder_path: str) -> None:
        """Set the image folder and initialize the binner."""
        print(f"VotingController: Setting image folder to: {folder_path}")
        try:
            self.image_folder_path = folder_path
            self.image_binner = ImageBinner(folder_path)
            print(f"VotingController: ImageBinner initialized successfully for: {folder_path}")
            
            # Verify the binner is working
            if self.image_binner.ensure_bin_folder_exists():
                print(f"VotingController: Bin folder verified/created at: {self.image_binner.bin_folder}")
            else:
                print(f"VotingController: WARNING - Could not create/verify bin folder")
                
        except Exception as e:
            print(f"VotingController: ERROR initializing ImageBinner: {e}")
            self.image_binner = None
            self.image_folder_path = None
            raise e
    
    def _check_binner_ready(self) -> bool:
        """Check if the image binner is ready to use."""
        if not self.image_binner:
            print("VotingController: ERROR - Image binner not initialized")
            print(f"VotingController: DEBUG - image_folder_path: {self.image_folder_path}")
            print(f"VotingController: DEBUG - data_manager.image_folder: {self.data_manager.image_folder}")
            
            if self.status_bar:
                self.status_bar.config(text="Error: Image binner not initialized - binning disabled")
            return False
        
        if not self.image_folder_path:
            print("VotingController: ERROR - No image folder path set")
            if self.status_bar:
                self.status_bar.config(text="Error: No image folder set - binning disabled")
            return False
        
        return True
    
    def toggle_bin_mode(self) -> None:
        """
        Toggle bin mode on/off. When bin mode is active, the next vote will bin the loser.
        """
        print(f"VotingController: toggle_bin_mode called, current state: {self.bin_mode}")
        
        if not self.current_pair[0] or not self.current_pair[1]:
            if self.status_bar:
                self.status_bar.config(text="No images available to vote on")
            return
        
        if not self._check_binner_ready():
            return
        
        # Toggle the bin mode
        self.bin_mode = not self.bin_mode
        
        # Update button text and colors to show bin mode
        self._update_vote_buttons_for_bin_mode()
        
        # Update status bar
        if self.bin_mode:
            if self.status_bar:
                self.status_bar.config(
                    text="🗑️ BIN MODE ACTIVE - Next vote will bin the loser! Vote for winner (↓ or S to cancel)"
                )
            print("VotingController: Bin mode ACTIVATED")
        else:
            if self.status_bar:
                explanation = self.ranking_algorithm.get_selection_explanation(
                    self.current_pair[0], self.current_pair[1]
                )
                self.status_bar.config(text=explanation)
            print("VotingController: Bin mode DEACTIVATED")
    
    def _update_vote_buttons_for_bin_mode(self) -> None:
        """Update vote button appearance based on bin mode state."""
        if self.bin_mode:
            # Bin mode active - change button appearance
            self.left_vote_button.config(
                text="🗑️ Winner (bins right) (←)",
                bg=Colors.BUTTON_WARNING,
                fg='white'
            )
            self.right_vote_button.config(
                text="🗑️ Winner (bins left) (→)",
                bg=Colors.BUTTON_WARNING,
                fg='white'
            )
        else:
            # Normal mode - restore normal appearance
            self.left_vote_button.config(
                text="Vote for this image (←)",
                bg=Colors.BUTTON_SUCCESS,
                fg='white'
            )
            self.right_vote_button.config(
                text="Vote for this image (→)",
                bg=Colors.BUTTON_SUCCESS,
                fg='white'
            )
    
    def bin_last_loser(self) -> None:
        """
        Bin the loser from the last vote. This can be called after a normal vote.
        """
        print("VotingController: bin_last_loser called")
        
        if not self.last_vote_result:
            if self.status_bar:
                self.status_bar.config(text="No recent vote to bin from")
            return
        
        if not self._check_binner_ready():
            return
        
        winner, loser = self.last_vote_result
        
        # Check if already binned
        if self.data_manager.is_image_binned(loser):
            if self.status_bar:
                self.status_bar.config(text=f"{loser} is already binned")
            return
        
        # Bin the loser
        success = self.data_manager.bin_image(loser)
        if success:
            # Move the physical file
            move_success, error_msg = self.image_binner.move_image_to_bin(loser)
            if move_success:
                # Update UI
                if self.stats_label:
                    active_count = self.data_manager.get_active_image_count()
                    binned_count = self.data_manager.get_binned_image_count()
                    self.stats_label.config(
                        text=f"Votes: {self.data_manager.vote_count} | Active: {active_count} | Binned: {binned_count}"
                    )
                
                if self.status_bar:
                    self.status_bar.config(
                        text=f"Last loser {loser} binned to Bin folder (won by {winner})"
                    )
                
                print(f"Successfully binned last loser: {loser}")
            else:
                # File move failed - remove from binned set
                self.data_manager.binned_images.discard(loser)
                if self.status_bar:
                    self.status_bar.config(text=f"Error binning image: {error_msg}")
                print(f"Failed to bin image: {error_msg}")
        else:
            if self.status_bar:
                self.status_bar.config(text="Failed to bin image")
    
    def show_next_pair(self) -> None:
        """Display the next pair of images for voting."""
        if self.data_manager.image_folder == "":
            return
        
        if self.left_vote_button is None or self.right_vote_button is None:
            print("Warning: Vote buttons not created yet")
            return
        
        images = self.image_processor.get_image_files(self.data_manager.image_folder)
        if len(images) < 2:
            return
        
        self.image_display.clear_images()
        
        if self.current_pair[0] and self.current_pair[1]:
            self.previous_pair = self.current_pair
        
        img1, img2 = self.ranking_algorithm.select_next_pair(images, self.previous_pair)
        if not img1 or not img2:
            return
        
        self.current_pair = (img1, img2)
        print(f"VotingController: Showing new pair: {img1} vs {img2}")
        
        self.image_display.display_image(img1, 'left')
        self.image_display.display_image(img2, 'right')
        
        self.left_vote_button.config(state=tk.NORMAL)
        self.right_vote_button.config(state=tk.NORMAL)
        
        # Reset bin mode when showing new pair (optional - comment out if you want it to persist)
        if self.bin_mode:
            self.bin_mode = False
            self._update_vote_buttons_for_bin_mode()
        
        explanation = self.ranking_algorithm.get_selection_explanation(img1, img2)
        if self.status_bar:
            self.status_bar.config(text=explanation)
        
        if self.preload_timer:
            self.parent.after_cancel(self.preload_timer)
        
        self.preload_timer = self.parent.after(Defaults.PRELOAD_DELAY_MS, self.preload_next_pair)
    
    def preload_next_pair(self) -> None:
        """Preload the next pair of images in the background."""
        if self.data_manager.image_folder == "":
            return
        
        images = self.image_processor.get_image_files(self.data_manager.image_folder)
        if len(images) < 2:
            return
        
        self.next_pair = self.ranking_algorithm.select_next_pair(images, self.current_pair)
        
        if self.next_pair[0] and self.next_pair[1]:
            self.image_display.preload_images(self.next_pair[0], self.next_pair[1])
    
    def vote(self, side: str) -> None:
        """Process a vote for the specified side, with optional binning."""
        print(f"VotingController: Vote called for side: {side}, bin_mode: {self.bin_mode}")
        
        if not self.current_pair[0] or not self.current_pair[1]:
            return
        
        if self.left_vote_button is None or self.right_vote_button is None:
            print("Warning: Vote buttons not created yet")
            return
        
        winner = self.current_pair[0] if side == 'left' else self.current_pair[1]
        loser = self.current_pair[1] if side == 'left' else self.current_pair[0]
        
        print(f"VotingController: Winner: {winner}, Loser: {loser}")
        
        # IMPORTANT: Record the vote FIRST - this updates vote counts, win/loss records, 
        # tier changes, and all statistics for both images before any binning occurs
        self.data_manager.record_vote(winner, loser)
        
        # Store vote result for potential binning
        self.last_vote_result = (winner, loser)
        print("VotingController: Vote recorded and stored for potential binning")
        
        # Handle binning if bin mode is active (vote data is already preserved above)
        if self.bin_mode:
            print(f"VotingController: Bin mode active, binning loser: {loser}")
            
            if self._check_binner_ready():
                # Bin the loser
                bin_success = self.data_manager.bin_image(loser)
                if bin_success:
                    # Move the physical file
                    move_success, error_msg = self.image_binner.move_image_to_bin(loser)
                    if move_success:
                        if self.status_bar:
                            self.status_bar.config(
                                text=f"🗑️ Vote & Bin: {winner} beats {loser} - {loser} binned to Bin folder"
                            )
                        print(f"Successfully voted and binned: {winner} beats {loser}, {loser} binned")
                    else:
                        # File move failed - remove from binned set
                        self.data_manager.binned_images.discard(loser)
                        if self.status_bar:
                            self.status_bar.config(text=f"Vote recorded, but error binning: {error_msg}")
                        print(f"Vote recorded, but failed to bin image: {error_msg}")
                else:
                    if self.status_bar:
                        self.status_bar.config(text=f"Vote recorded: {winner} beats {loser} (image was already binned)")
            
            # Turn off bin mode after use
            self.bin_mode = False
            self._update_vote_buttons_for_bin_mode()
        else:
            # Normal vote
            if self.status_bar:
                self.status_bar.config(text=f"Vote recorded: {winner} wins over {loser}")
        
        # Update stats
        if self.stats_label:
            active_count = self.data_manager.get_active_image_count()
            binned_count = self.data_manager.get_binned_image_count()
            self.stats_label.config(
                text=f"Votes: {self.data_manager.vote_count} | Active: {active_count} | Binned: {binned_count}"
            )
        
        self.left_vote_button.config(state=tk.DISABLED)
        self.right_vote_button.config(state=tk.DISABLED)
        
        if self.on_vote_callback:
            self.on_vote_callback(winner, loser)
        
        self.parent.after(Defaults.VOTE_DELAY_MS, self.show_next_pair)
    
    def refresh_current_pair(self) -> None:
        """Refresh the currently displayed pair."""
        if self.current_pair[0] and self.current_pair[1]:
            self.image_display.display_image(self.current_pair[0], 'left')
            self.image_display.display_image(self.current_pair[1], 'right')
    
    def setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts for voting and binning."""
        print("VotingController: Setting up keyboard shortcuts...")
        from config import KeyBindings
        
        for key in KeyBindings.VOTE_LEFT:
            self.parent.bind(key, lambda e: self.vote('left') if self.left_vote_button and self.left_vote_button['state'] == tk.NORMAL else None)
            print(f"VotingController: Bound key {key} to vote left")
        
        for key in KeyBindings.VOTE_RIGHT:
            self.parent.bind(key, lambda e: self.vote('right') if self.right_vote_button and self.right_vote_button['state'] == tk.NORMAL else None)
            print(f"VotingController: Bound key {key} to vote right")
        
        # NEW: Toggle bin mode shortcuts
        for key in KeyBindings.TOGGLE_BIN_MODE:
            self.parent.bind(key, lambda e: self.toggle_bin_mode())
            print(f"VotingController: Bound key {key} to toggle_bin_mode")
        
        # Bin last loser shortcuts
        for key in KeyBindings.BIN_LAST_LOSER:
            self.parent.bind(key, lambda e: self.bin_last_loser())
        print("VotingController: Bound B/b keys to bin_last_loser")
        
        print("VotingController: Keyboard shortcuts setup complete")
    
    def reset_voting_state(self) -> None:
        """Reset voting state when loading new images."""
        print("VotingController: Resetting voting state...")
        self.current_pair = (None, None)
        self.next_pair = (None, None)
        self.previous_pair = (None, None)
        self.last_vote_result = None
        
        # Reset bin mode
        self.bin_mode = False
        
        if self.left_vote_button:
            self.left_vote_button.config(state=tk.DISABLED)
        if self.right_vote_button:
            self.right_vote_button.config(state=tk.DISABLED)
        
        # Reset button appearance
        self._update_vote_buttons_for_bin_mode()
        
        if self.status_bar:
            self.status_bar.config(text="Select a folder to begin")
        
        print("VotingController: Voting state reset complete")
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.preload_timer:
            self.parent.after_cancel(self.preload_timer)
        
        self.reset_voting_state()