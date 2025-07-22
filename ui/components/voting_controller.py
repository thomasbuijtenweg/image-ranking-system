"""Updated Voting controller with binning integration for the Image Ranking System."""

import tkinter as tk
from typing import Optional, Tuple

from config import Colors, Defaults


class VotingController:
    """Handles voting logic and pair management with binning support for the main interface."""
    
    def __init__(self, parent: tk.Tk, data_manager, ranking_algorithm, image_processor, image_display, binning_ui_controller=None):
        self.parent = parent
        self.data_manager = data_manager
        self.ranking_algorithm = ranking_algorithm
        self.image_processor = image_processor
        self.image_display = image_display
        self.binning_ui_controller = binning_ui_controller
        
        self.current_pair = (None, None)
        self.next_pair = (None, None)
        self.previous_pair = (None, None)
        
        self.left_vote_button = None
        self.right_vote_button = None
        self.status_bar = None
        self.stats_label = None
        
        self.preload_timer = None
        
        self.on_vote_callback = None
        
        # Setup binning callbacks if binning controller is available
        if self.binning_ui_controller:
            self.binning_ui_controller.set_image_binned_callback(self._on_image_binned)
            self.binning_ui_controller.set_both_binned_callback(self._on_both_binned)
    
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
        
        # Setup binning buttons if binning controller is available
        if self.binning_ui_controller:
            # Create a center frame for the "Bin Both" button
            center_frame = self._get_or_create_center_frame()
            self.binning_ui_controller.create_bin_buttons(left_frame, right_frame, center_frame)
    
    def _get_or_create_center_frame(self) -> tk.Frame:
        """Get or create a center frame for the bin both button."""
        # Get the parent of the left and right frames (main frame)
        left_frame, right_frame = self.image_display.get_frames()
        main_frame = left_frame.master
        
        # Create a center frame between the left and right frames
        center_frame = tk.Frame(main_frame, bg=Colors.BG_PRIMARY)
        center_frame.grid(row=1, column=1, sticky="", padx=10, pady=20)  # Position below VS label
        
        return center_frame
    
    def set_ui_references(self, status_bar: tk.Label, stats_label: tk.Label) -> None:
        """Set references to UI elements that need to be updated."""
        self.status_bar = status_bar
        self.stats_label = stats_label
    
    def set_vote_callback(self, callback) -> None:
        """Set callback function to be called after each vote."""
        self.on_vote_callback = callback
    
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
        
        # Check if we have enough available images for voting (excluding binned)
        if not self.ranking_algorithm.can_select_pairs():
            available_count = self.ranking_algorithm.get_available_image_count()
            binned_count = self.ranking_algorithm.get_binned_image_count()
            
            self._show_insufficient_images_message(available_count, binned_count)
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
        
        # Update binning UI with current pair
        if self.binning_ui_controller:
            self.binning_ui_controller.update_current_pair(img1, img2)
        
        explanation = self.ranking_algorithm.get_selection_explanation(img1, img2)
        if self.status_bar:
            self.status_bar.config(text=explanation)
        
        if self.preload_timer:
            self.parent.after_cancel(self.preload_timer)
        
        self.preload_timer = self.parent.after(Defaults.PRELOAD_DELAY_MS, self.preload_next_pair)
    
    def _show_insufficient_images_message(self, available_count: int, binned_count: int) -> None:
        """Show message when there aren't enough images to vote on."""
        if available_count == 0:
            message = "No images available for voting!"
            if binned_count > 0:
                message += f"\n\nAll {binned_count} images have been binned."
                message += "\nTo continue voting, move some images back from the Bin folder."
        elif available_count == 1:
            message = f"Only 1 image available for voting (need at least 2)."
            if binned_count > 0:
                message += f"\n\n{binned_count} images have been binned."
                message += "\nTo continue voting, move some images back from the Bin folder."
        else:
            message = f"Unexpected state: {available_count} available images"
        
        if self.status_bar:
            self.status_bar.config(text=message)
        
        # Disable voting buttons
        self.left_vote_button.config(state=tk.DISABLED)
        self.right_vote_button.config(state=tk.DISABLED)
        
        # Disable binning buttons
        if self.binning_ui_controller:
            self.binning_ui_controller.update_button_states(False)
    
    def preload_next_pair(self) -> None:
        """Preload the next pair of images in the background."""
        if self.data_manager.image_folder == "":
            return
        
        images = self.image_processor.get_image_files(self.data_manager.image_folder)
        if len(images) < 2:
            return
        
        # Only preload if we have enough available images
        if not self.ranking_algorithm.can_select_pairs():
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
        
        # Clean filenames - remove any Bin/ prefix that shouldn't be there
        original_winner = winner[4:] if winner.startswith('Bin/') else winner
        original_loser = loser[4:] if loser.startswith('Bin/') else loser
        
        # Double-check that neither image is binned (shouldn't happen but let's be safe)
        if self.data_manager.is_image_binned(original_winner) or self.data_manager.is_image_binned(original_loser):
            print(f"Warning: Attempted to vote on binned image(s): {original_winner}, {original_loser}")
            self.show_next_pair()  # Get a new pair
            return
        
        # Verify that both images exist in image_stats
        if original_winner not in self.data_manager.image_stats:
            print(f"Error: Winner {original_winner} not found in image_stats")
            print(f"Available keys: {list(self.data_manager.image_stats.keys())[:5]}...")  # Show first 5 keys for debugging
            self.show_next_pair()
            return
            
        if original_loser not in self.data_manager.image_stats:
            print(f"Error: Loser {original_loser} not found in image_stats")
            print(f"Available keys: {list(self.data_manager.image_stats.keys())[:5]}...")  # Show first 5 keys for debugging
            self.show_next_pair()
            return
        
        # Use the cleaned filenames for voting
        self.data_manager.record_vote(original_winner, original_loser)
        
        self.ranking_algorithm.invalidate_cache()
        
        if self.stats_label:
            self.stats_label.config(text=f"Total votes: {self.data_manager.vote_count}")
        
        if self.status_bar:
            self.status_bar.config(text=f"Vote recorded: {original_winner} wins over {original_loser}")
        
        self.left_vote_button.config(state=tk.DISABLED)
        self.right_vote_button.config(state=tk.DISABLED)
        
        # Disable binning buttons during transition
        if self.binning_ui_controller:
            self.binning_ui_controller.update_button_states(False)
        
        if self.on_vote_callback:
            self.on_vote_callback(original_winner, original_loser)
        
        self.parent.after(Defaults.VOTE_DELAY_MS, self.show_next_pair)
    
    def _on_image_binned(self, side: str, image_name: str) -> None:
        """Handle callback when a single image is binned."""
        print(f"Voting controller: {side} image {image_name} was binned")
        
        # Update stats display
        if self.stats_label:
            available_count = self.ranking_algorithm.get_available_image_count()
            binned_count = self.ranking_algorithm.get_binned_image_count() 
            self.stats_label.config(text=f"Total votes: {self.data_manager.vote_count} | Available: {available_count} | Binned: {binned_count}")
        
        # Show next pair after a brief delay
        self.parent.after(500, self.show_next_pair)
    
    def _on_both_binned(self, image1: str, image2: str) -> None:
        """Handle callback when both images are binned."""
        print(f"Voting controller: Both images binned: {image1}, {image2}")
        
        # Update stats display
        if self.stats_label:
            available_count = self.ranking_algorithm.get_available_image_count()
            binned_count = self.ranking_algorithm.get_binned_image_count()
            self.stats_label.config(text=f"Total votes: {self.data_manager.vote_count} | Available: {available_count} | Binned: {binned_count}")
        
        # Show next pair after a brief delay
        self.parent.after(500, self.show_next_pair)
    
    def refresh_current_pair(self) -> None:
        """Refresh the currently displayed pair."""
        if self.current_pair[0] and self.current_pair[1]:
            # Check if either image was binned
            if self.data_manager.is_image_binned(self.current_pair[0]) or self.data_manager.is_image_binned(self.current_pair[1]):
                print("Current pair contains binned image(s), getting new pair")
                self.show_next_pair()
                return
            
            self.image_display.display_image(self.current_pair[0], 'left')
            self.image_display.display_image(self.current_pair[1], 'right')
    
    def setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts for voting and binning."""
        from config import KeyBindings
        
        # Voting shortcuts
        for key in KeyBindings.VOTE_LEFT:
            self.parent.bind(key, lambda e: self.vote('left') if self.left_vote_button and self.left_vote_button['state'] == tk.NORMAL else None)
        
        for key in KeyBindings.VOTE_RIGHT:
            self.parent.bind(key, lambda e: self.vote('right') if self.right_vote_button and self.right_vote_button['state'] == tk.NORMAL else None)
        
        # Binning shortcuts
        if self.binning_ui_controller:
            self.binning_ui_controller.setup_keyboard_shortcuts()
    
    def reset_voting_state(self) -> None:
        """Reset voting state when loading new images."""
        self.current_pair = (None, None)
        self.next_pair = (None, None)
        self.previous_pair = (None, None)
        
        if self.left_vote_button:
            self.left_vote_button.config(state=tk.DISABLED)
        if self.right_vote_button:
            self.right_vote_button.config(state=tk.DISABLED)
        
        if self.binning_ui_controller:
            self.binning_ui_controller.update_button_states(False)
        
        if self.status_bar:
            self.status_bar.config(text="Select a folder to begin")
    
    def get_current_pair(self) -> Tuple[Optional[str], Optional[str]]:
        """Get the currently displayed pair."""
        return self.current_pair
    
    def set_binning_ui_controller(self, binning_ui_controller) -> None:
        """Set the binning UI controller (for late initialization)."""
        self.binning_ui_controller = binning_ui_controller
        
        # Setup callbacks
        if self.binning_ui_controller:
            self.binning_ui_controller.set_image_binned_callback(self._on_image_binned)
            self.binning_ui_controller.set_both_binned_callback(self._on_both_binned)
    
    def get_voting_statistics(self) -> dict:
        """Get current voting statistics."""
        available_count = self.ranking_algorithm.get_available_image_count()
        binned_count = self.ranking_algorithm.get_binned_image_count()
        
        return {
            'total_votes': self.data_manager.vote_count,
            'available_images': available_count,
            'binned_images': binned_count,
            'total_images': available_count + binned_count,
            'current_pair': self.current_pair,
            'can_vote': available_count >= 2
        }
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.preload_timer:
            self.parent.after_cancel(self.preload_timer)
        
        self.reset_voting_state()
        
        # Clean up binning UI controller if it exists
        if self.binning_ui_controller:
            self.binning_ui_controller.cleanup()
