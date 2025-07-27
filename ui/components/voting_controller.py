"""Voting controller for the Image Ranking System with binning support."""

import tkinter as tk
from tkinter import messagebox
from typing import Optional, Tuple

from config import Colors, Defaults
from core.image_binner import ImageBinner


class VotingController:
    """Handles voting logic and pair management for the main interface."""
    
    def __init__(self, parent: tk.Tk, data_manager, ranking_algorithm, image_processor, image_display):
        self.parent = parent
        self.data_manager = data_manager
        self.ranking_algorithm = ranking_algorithm
        self.image_processor = image_processor
        self.image_display = image_display
        
        self.current_pair = (None, None)
        self.next_pair = (None, None)
        self.previous_pair = (None, None)
        self.last_vote_result = None  # Track last vote for binning
        
        self.left_vote_button = None
        self.right_vote_button = None
        self.status_bar = None
        self.stats_label = None
        
        self.preload_timer = None
        
        self.on_vote_callback = None
        
        # Image binner - will be initialized when folder is set
        self.image_binner = None
    
    def create_vote_buttons(self, left_frame: tk.Frame, right_frame: tk.Frame) -> None:
        """Create vote buttons for both sides."""
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
    
    def set_ui_references(self, status_bar: tk.Label, stats_label: tk.Label) -> None:
        """Set references to UI elements that need to be updated."""
        self.status_bar = status_bar
        self.stats_label = stats_label
    
    def set_vote_callback(self, callback) -> None:
        """Set callback function to be called after each vote."""
        self.on_vote_callback = callback
    
    def set_image_folder(self, folder_path: str) -> None:
        """Set the image folder and initialize the binner."""
        self.image_binner = ImageBinner(folder_path)
    
    def bin_current_loser(self) -> None:
        """
        Bin an image after voting. Shows dialog to choose winner, then bins the loser.
        This is called by the down arrow key.
        """
        if not self.current_pair[0] or not self.current_pair[1]:
            if self.status_bar:
                self.status_bar.config(text="No images available to vote on")
            return
        
        if not self.image_binner:
            print("Error: Image binner not initialized")
            if self.status_bar:
                self.status_bar.config(text="Error: Image binner not initialized")
            return
        
        # Create a dialog to choose the winner
        dialog = tk.Toplevel(self.parent)
        dialog.title("Choose Winner Before Binning")
        dialog.geometry("500x200")
        dialog.configure(bg=Colors.BG_PRIMARY)
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 200,
            self.parent.winfo_rooty() + 200
        ))
        
        # Result variable
        result = tk.StringVar()
        
        # Title
        tk.Label(dialog, text="Which image should win?", 
                font=('Arial', 14, 'bold'), fg=Colors.TEXT_PRIMARY, 
                bg=Colors.BG_PRIMARY).pack(pady=10)
        
        tk.Label(dialog, text="The loser will be binned to the Bin folder.", 
                font=('Arial', 10), fg=Colors.TEXT_WARNING, 
                bg=Colors.BG_PRIMARY).pack(pady=5)
        
        # Button frame
        button_frame = tk.Frame(dialog, bg=Colors.BG_PRIMARY)
        button_frame.pack(pady=20)
        
        # Left image button
        left_img_name = self.current_pair[0]
        left_display_name = left_img_name[:30] + "..." if len(left_img_name) > 30 else left_img_name
        
        tk.Button(button_frame, text=f"Left Image Wins\n({left_display_name})", 
                 command=lambda: [result.set('left'), dialog.destroy()],
                 bg=Colors.BUTTON_SUCCESS, fg='white', font=('Arial', 10), 
                 relief=tk.FLAT, width=20, height=3).pack(side=tk.LEFT, padx=10)
        
        # Right image button  
        right_img_name = self.current_pair[1]
        right_display_name = right_img_name[:30] + "..." if len(right_img_name) > 30 else right_img_name
        
        tk.Button(button_frame, text=f"Right Image Wins\n({right_display_name})", 
                 command=lambda: [result.set('right'), dialog.destroy()],
                 bg=Colors.BUTTON_SUCCESS, fg='white', font=('Arial', 10), 
                 relief=tk.FLAT, width=20, height=3).pack(side=tk.LEFT, padx=10)
        
        # Cancel button
        tk.Button(button_frame, text="Cancel", 
                 command=lambda: [result.set('cancel'), dialog.destroy()],
                 bg=Colors.BUTTON_NEUTRAL, fg='white', font=('Arial', 10), 
                 relief=tk.FLAT, width=10, height=2).pack(side=tk.LEFT, padx=10)
        
        # Wait for user choice
        dialog.wait_window()
        
        choice = result.get()
        if choice == 'cancel' or not choice:
            if self.status_bar:
                self.status_bar.config(text="Binning cancelled")
            return
        
        # Determine winner and loser based on user choice
        if choice == 'left':
            winner = self.current_pair[0]
            loser = self.current_pair[1]
        else:  # choice == 'right'
            winner = self.current_pair[1]
            loser = self.current_pair[0]
        
        # Record the vote first
        self.data_manager.record_vote(winner, loser)
        
        # Store vote result for potential future use
        self.last_vote_result = (winner, loser)
        
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
                        text=f"Vote recorded: {winner} beats {loser} - {loser} binned to Bin folder"
                    )
                
                print(f"Successfully voted and binned: {winner} beats {loser}, {loser} binned")
            else:
                # File move failed - remove from binned set
                self.data_manager.binned_images.discard(loser)
                if self.status_bar:
                    self.status_bar.config(text=f"Error binning image: {error_msg}")
                print(f"Failed to bin image: {error_msg}")
        else:
            if self.status_bar:
                self.status_bar.config(text="Image was already binned")
        
        # Disable buttons and proceed to next pair
        if self.left_vote_button:
            self.left_vote_button.config(state=tk.DISABLED)
        if self.right_vote_button:
            self.right_vote_button.config(state=tk.DISABLED)
        
        if self.on_vote_callback:
            self.on_vote_callback(winner, loser)
        
        self.parent.after(Defaults.VOTE_DELAY_MS, self.show_next_pair)
    
    def bin_last_loser(self) -> None:
        """
        Bin the loser from the last vote. This can be called after a normal vote.
        """
        if not self.last_vote_result:
            if self.status_bar:
                self.status_bar.config(text="No recent vote to bin from")
            return
        
        if not self.image_binner:
            print("Error: Image binner not initialized")
            if self.status_bar:
                self.status_bar.config(text="Error: Image binner not initialized")
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
        
        self.image_display.display_image(img1, 'left')
        self.image_display.display_image(img2, 'right')
        
        self.left_vote_button.config(state=tk.NORMAL)
        self.right_vote_button.config(state=tk.NORMAL)
        
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
        """Process a vote for the specified side."""
        if not self.current_pair[0] or not self.current_pair[1]:
            return
        
        if self.left_vote_button is None or self.right_vote_button is None:
            print("Warning: Vote buttons not created yet")
            return
        
        winner = self.current_pair[0] if side == 'left' else self.current_pair[1]
        loser = self.current_pair[1] if side == 'left' else self.current_pair[0]
        
        self.data_manager.record_vote(winner, loser)
        
        # Store vote result for potential binning
        self.last_vote_result = (winner, loser)
        
        if self.stats_label:
            active_count = self.data_manager.get_active_image_count()
            binned_count = self.data_manager.get_binned_image_count()
            self.stats_label.config(
                text=f"Votes: {self.data_manager.vote_count} | Active: {active_count} | Binned: {binned_count}"
            )
        
        if self.status_bar:
            self.status_bar.config(text=f"Vote recorded: {winner} wins over {loser}")
        
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
        from config import KeyBindings
        
        for key in KeyBindings.VOTE_LEFT:
            self.parent.bind(key, lambda e: self.vote('left') if self.left_vote_button and self.left_vote_button['state'] == tk.NORMAL else None)
        
        for key in KeyBindings.VOTE_RIGHT:
            self.parent.bind(key, lambda e: self.vote('right') if self.right_vote_button and self.right_vote_button['state'] == tk.NORMAL else None)
        
        # Binning shortcuts
        for key in KeyBindings.BIN_LOSER:
            self.parent.bind(key, lambda e: self.bin_current_loser() if self.left_vote_button and self.left_vote_button['state'] == tk.NORMAL else None)
        
        # Optional: Add a key to bin the last loser (e.g., 'b' key)
        self.parent.bind('<b>', lambda e: self.bin_last_loser())
        self.parent.bind('<B>', lambda e: self.bin_last_loser())
    
    def reset_voting_state(self) -> None:
        """Reset voting state when loading new images."""
        self.current_pair = (None, None)
        self.next_pair = (None, None)
        self.previous_pair = (None, None)
        self.last_vote_result = None
        
        if self.left_vote_button:
            self.left_vote_button.config(state=tk.DISABLED)
        if self.right_vote_button:
            self.right_vote_button.config(state=tk.DISABLED)
        
        if self.status_bar:
            self.status_bar.config(text="Select a folder to begin")
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.preload_timer:
            self.parent.after_cancel(self.preload_timer)
        
        self.reset_voting_state()