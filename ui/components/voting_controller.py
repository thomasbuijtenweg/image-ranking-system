"""Voting controller for the Image Ranking System with binning support and debug logging."""

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
        # Bin mode: 0 = off, 1 = bin loser only, 2 = bin both images
        self.bin_mode = 0
        
        self.left_vote_button = None
        self.right_vote_button = None
        self.status_bar = None
        self.stats_label = None
        
        self.preload_timer = None
        
        self.on_vote_callback = None
        
        # Image binner - will be initialized when folder is set
        self.image_binner = None
        
        # Filter manager - will be set by main window
        self.filter_manager = None
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
    
    def set_filter_manager(self, filter_manager) -> None:
        """Set the filter manager for prompt-based filtering."""
        print("VotingController: Setting filter manager...")
        self.filter_manager = filter_manager
        print("VotingController: Filter manager set")
    
    def set_image_folder(self, folder_path: str) -> None:
        """Set the image folder and initialize the binner."""
        print(f"VotingController: set_image_folder called with: {folder_path}")
        try:
            if not folder_path:
                print("VotingController: ERROR - Empty folder path received")
                return
            
            self.image_binner = ImageBinner(folder_path)
            print(f"VotingController: Image binner initialized successfully for folder: {folder_path}")
            
            # Test if binner is working
            bin_folder_exists = self.image_binner.ensure_bin_folder_exists()
            print(f"VotingController: Bin folder creation test: {bin_folder_exists}")
            
        except Exception as e:
            print(f"VotingController: ERROR initializing image binner: {e}")
            import traceback
            traceback.print_exc()
            self.image_binner = None
    
    def prepare_to_bin_next_loser(self) -> None:
        """Cycle bin mode: 0 (off) → 1 (bin loser) → 2 (bin both) → 0 (off).
        
        Press ↓ once : next vote bins the loser only.
        Press ↓ twice: next vote bins BOTH images.
        Press ↓ again: cancel, return to normal voting.
        """
        print("VotingController: prepare_to_bin_next_loser called")

        if not self.current_pair[0] or not self.current_pair[1]:
            print("VotingController: No current pair available")
            if self.status_bar:
                self.status_bar.config(text="No images available - load images first")
            return

        if not self.image_binner:
            print("VotingController: ERROR - Image binner not initialized")
            if self.status_bar:
                self.status_bar.config(
                    text="Error: Image binner not initialized - select a folder first")
            return

        # Advance through the three states
        self.bin_mode = (self.bin_mode + 1) % 3
        print(f"VotingController: bin_mode → {self.bin_mode}")

        if self.bin_mode == 1:
            if self.status_bar:
                self.status_bar.config(
                    text="🗑️ BIN LOSER: Next loser will be binned — vote normally")
            if self.left_vote_button:
                self.left_vote_button.config(
                    text="Vote for this image (← + BIN LOSER)", bg=Colors.BUTTON_WARNING)
            if self.right_vote_button:
                self.right_vote_button.config(
                    text="Vote for this image (→ + BIN LOSER)", bg=Colors.BUTTON_WARNING)

        elif self.bin_mode == 2:
            if self.status_bar:
                self.status_bar.config(
                    text="🗑️🗑️ BIN BOTH: Next vote will bin BOTH images — vote to confirm")
            if self.left_vote_button:
                self.left_vote_button.config(
                    text="Vote (← + BIN BOTH)", bg=Colors.BUTTON_DANGER)
            if self.right_vote_button:
                self.right_vote_button.config(
                    text="Vote (→ + BIN BOTH)", bg=Colors.BUTTON_DANGER)

        else:  # mode 0 — cancelled
            if self.status_bar:
                self.status_bar.config(text="Bin mode cancelled — voting normally")
            self._reset_button_appearance()
    
    def bin_last_loser(self) -> None:
        """
        Bin the loser from the last vote. This can be called after a normal vote.
        """
        print("VotingController: bin_last_loser called")
        
        if not self.last_vote_result:
            print("VotingController: No last vote result available")
            if self.status_bar:
                self.status_bar.config(text="No recent vote to bin from - vote first, then press B to bin the loser")
            return
        
        if not self.image_binner:
            print("VotingController: ERROR - Image binner not initialized")
            if self.status_bar:
                self.status_bar.config(text="Error: Image binner not initialized - select a folder first")
            return
        
        winner, loser = self.last_vote_result
        print(f"VotingController: Attempting to bin last loser: {loser} (winner was: {winner})")
        
        # Check if already binned (compatible with existing data manager)
        if hasattr(self.data_manager, 'is_image_binned'):
            if self.data_manager.is_image_binned(loser):
                print(f"VotingController: {loser} is already binned")
                if self.status_bar:
                    self.status_bar.config(text=f"{loser} is already binned")
                return
        elif hasattr(self.data_manager, 'binned_images'):
            if loser in self.data_manager.binned_images:
                print(f"VotingController: {loser} is already binned")
                if self.status_bar:
                    self.status_bar.config(text=f"{loser} is already binned")
                return
        
        # Bin the loser (compatible with existing data manager)
        success = False
        if hasattr(self.data_manager, 'bin_image'):
            success = self.data_manager.bin_image(loser)
            print(f"VotingController: data_manager.bin_image result: {success}")
        elif hasattr(self.data_manager, 'binned_images'):
            if loser not in self.data_manager.binned_images:
                self.data_manager.binned_images.add(loser)
                success = True
                print(f"VotingController: Added {loser} to binned_images set")
        else:
            # Create binned_images set if it doesn't exist
            if not hasattr(self.data_manager, 'binned_images'):
                self.data_manager.binned_images = set()
                print("VotingController: Created new binned_images set")
            self.data_manager.binned_images.add(loser)
            success = True
            print(f"VotingController: Added {loser} to new binned_images set")
        
        if success:
            # Purge votes involving the binned image from all active images
            purge_result = None
            if hasattr(self.data_manager, 'purge_binned_image_votes'):
                purge_result = self.data_manager.purge_binned_image_votes(loser)
                print(f"VotingController: Vote purge result: {purge_result}")
            
            # Move the physical file
            print(f"VotingController: Attempting to move file {loser} to bin")
            move_success, error_msg = self.image_binner.move_image_to_bin(loser)
            print(f"VotingController: File move result: {move_success}, error: {error_msg}")
            
            if move_success:
                # Update UI
                self._update_stats_display()
                
                purge_info = ""
                if purge_result:
                    purge_info = f" | Purged {purge_result['total_votes_removed']} vote(s) from {purge_result['affected_images']} image(s)"
                
                if self.status_bar:
                    self.status_bar.config(
                        text=f"Binned: {loser} moved to Bin folder (last loser vs {winner}){purge_info}"
                    )
                
                print(f"VotingController: Successfully binned last loser: {loser}")
            else:
                # File move failed - remove from binned set
                if hasattr(self.data_manager, 'binned_images'):
                    self.data_manager.binned_images.discard(loser)
                    print(f"VotingController: Removed {loser} from binned set due to file move failure")
                if self.status_bar:
                    self.status_bar.config(text=f"Error binning image: {error_msg}")
                print(f"VotingController: Failed to bin image: {error_msg}")
        else:
            print("VotingController: Failed to mark image as binned")
            if self.status_bar:
                self.status_bar.config(text="Failed to bin image")
    
    def _update_stats_display(self):
        """Update stats display — shows zone progress when cutline is active."""
        if not self.stats_label:
            return
        try:
            active_count = self.data_manager.get_active_image_count()
            binned_count = self.data_manager.get_binned_image_count()
            votes        = self.data_manager.vote_count
            target_count = self.data_manager.algorithm_settings.target_count

            if target_count > 0:
                # Cutline mode: show zone-based progress
                summary = self.data_manager.get_progress_summary()
                ct      = summary.get('cutline_tier')
                ct_str  = f"Tier {ct}" if ct is not None else "—"
                res     = summary.get('resolution_pct', 0.0)
                self.stats_label.config(
                    text=(
                        f"Votes: {votes}  |  "
                        f"✓ In: {summary['confirmed_in']}  "
                        f"~ Boundary: {summary['boundary']}  "
                        f"✗ Out: {summary['confirmed_out']}  "
                        f"Binned: {summary['eliminated']}  |  "
                        f"Cutline: {ct_str} (target {target_count})  |  "
                        f"Resolution: {res:.0f}%"
                    )
                )
            else:
                # Disabled: existing display
                self.stats_label.config(
                    text=f"Votes: {votes} | Active: {active_count} | Binned: {binned_count}"
                )
        except Exception as e:
            print(f"VotingController: Error updating stats display: {e}")
    
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
        
        # Get images list for backwards compatibility
        images = self.image_processor.get_image_files(self.data_manager.image_folder)
        
        # Pass filter_manager to ranking algorithm
        img1, img2 = self.ranking_algorithm.select_next_pair(
            available_images=images,
            exclude_pair=self.previous_pair,
            filter_manager=self.filter_manager
        )
        if not img1 or not img2:
            return
        
        self.current_pair = (img1, img2)
        print(f"VotingController: Showing new pair: {img1} vs {img2}")
        
        self.image_display.display_image(img1, 'left')
        self.image_display.display_image(img2, 'right')
        
        # Set button state and appearance based on bin mode
        self.left_vote_button.config(state=tk.NORMAL)
        self.right_vote_button.config(state=tk.NORMAL)
        
        if self.bin_mode == 1:
            self.left_vote_button.config(
                text="Vote for this image (← + BIN LOSER)", bg=Colors.BUTTON_WARNING)
            self.right_vote_button.config(
                text="Vote for this image (→ + BIN LOSER)", bg=Colors.BUTTON_WARNING)
            print("VotingController: Buttons set to bin-loser mode appearance")
        elif self.bin_mode == 2:
            self.left_vote_button.config(
                text="Vote (← + BIN BOTH)", bg=Colors.BUTTON_DANGER)
            self.right_vote_button.config(
                text="Vote (→ + BIN BOTH)", bg=Colors.BUTTON_DANGER)
            print("VotingController: Buttons set to bin-both mode appearance")
        else:
            self.left_vote_button.config(
                text="Vote for this image (←)", bg=Colors.BUTTON_SUCCESS)
            self.right_vote_button.config(
                text="Vote for this image (→)", bg=Colors.BUTTON_SUCCESS)

        explanation = self.ranking_algorithm.get_selection_explanation(img1, img2)
        if self.status_bar and self.bin_mode == 0:  # Don't override bin mode message
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
        
        # Pass filter_manager to ranking algorithm for preload
        self.next_pair = self.ranking_algorithm.select_next_pair(
            available_images=images,
            exclude_pair=self.previous_pair,
            filter_manager=self.filter_manager
        )
        
        if self.next_pair[0] and self.next_pair[1]:
            self.image_display.preload_images(self.next_pair[0], self.next_pair[1])
    
    def vote(self, side: str) -> None:
        """Process a vote for the specified side, with optional binning."""
        print(f"VotingController: Vote called for side: {side}")
        
        if not self.current_pair[0] or not self.current_pair[1]:
            print("VotingController: No current pair available for voting")
            return
        
        if self.left_vote_button is None or self.right_vote_button is None:
            print("Warning: Vote buttons not created yet")
            return
        
        winner = self.current_pair[0] if side == 'left' else self.current_pair[1]
        loser = self.current_pair[1] if side == 'left' else self.current_pair[0]
        print(f"VotingController: Winner: {winner}, Loser: {loser}")
        
        self.data_manager.record_vote(winner, loser)
        
        # Store vote result for potential binning
        self.last_vote_result = (winner, loser)
        print(f"VotingController: Vote recorded and stored for potential binning")
        
        # Handle binning based on current bin_mode
        if self.bin_mode == 1:
            print("VotingController: bin_mode=1, binning loser")
            self._bin_loser_immediately(winner, loser)
            self.bin_mode = 0
            self._reset_button_appearance()
            print("VotingController: Bin mode reset after use")
        elif self.bin_mode == 2:
            print("VotingController: bin_mode=2, binning both images")
            self._bin_both_immediately(winner, loser)
            self.bin_mode = 0
            self._reset_button_appearance()
            print("VotingController: Bin-both mode reset after use")
        else:
            # Normal vote without binning
            self._update_stats_display()
            
            if self.status_bar:
                self.status_bar.config(text=f"Vote recorded: {winner} wins over {loser}")
        
        self.left_vote_button.config(state=tk.DISABLED)
        self.right_vote_button.config(state=tk.DISABLED)
        
        if self.on_vote_callback:
            self.on_vote_callback(winner, loser)
        
        self.parent.after(Defaults.VOTE_DELAY_MS, self.show_next_pair)
    
    def _bin_loser_immediately(self, winner: str, loser: str) -> None:
        """Bin the loser immediately after a vote."""
        print(f"VotingController: _bin_loser_immediately called for {loser}")
        
        if not self.image_binner:
            print("VotingController: ERROR - Image binner not initialized")
            if self.status_bar:
                self.status_bar.config(text="Error: Image binner not initialized")
            return
        
        # Bin the loser (compatible with existing data manager)
        success = False
        if hasattr(self.data_manager, 'bin_image'):
            success = self.data_manager.bin_image(loser)
            print(f"VotingController: data_manager.bin_image result: {success}")
        elif hasattr(self.data_manager, 'binned_images'):
            if not hasattr(self.data_manager.binned_images, '__contains__'):
                self.data_manager.binned_images = set()
            if loser not in self.data_manager.binned_images:
                self.data_manager.binned_images.add(loser)
                success = True
                print(f"VotingController: Added {loser} to binned_images set")
        else:
            # Create binned_images set if it doesn't exist
            if not hasattr(self.data_manager, 'binned_images'):
                self.data_manager.binned_images = set()
                print("VotingController: Created new binned_images set")
            self.data_manager.binned_images.add(loser)
            success = True
            print(f"VotingController: Added {loser} to new binned_images set")
        
        if success:
            # Purge votes involving the binned image from all active images
            if hasattr(self.data_manager, 'purge_binned_image_votes'):
                purge_result = self.data_manager.purge_binned_image_votes(loser)
                print(f"VotingController: Vote purge result: {purge_result}")
            
            # Move the physical file
            print(f"VotingController: Attempting to move file {loser} to bin")
            move_success, error_msg = self.image_binner.move_image_to_bin(loser)
            print(f"VotingController: File move result: {move_success}, error: {error_msg}")
            
            if move_success:
                # Update UI
                self._update_stats_display()
                
                purge_info = ""
                if hasattr(self.data_manager, 'purge_binned_image_votes') and purge_result:
                    purge_info = f" | Purged {purge_result['total_votes_removed']} vote(s) from {purge_result['affected_images']} image(s)"
                
                if self.status_bar:
                    self.status_bar.config(
                        text=f"Vote + Bin: {winner} beats {loser} → {loser} binned{purge_info}"
                    )
                
                print(f"VotingController: Vote and bin successful: {winner} beats {loser}, {loser} binned")
            else:
                # File move failed - remove from binned set
                if hasattr(self.data_manager, 'binned_images'):
                    self.data_manager.binned_images.discard(loser)
                    print(f"VotingController: Removed {loser} from binned set due to file move failure")
                if self.status_bar:
                    self.status_bar.config(text=f"Vote recorded but binning failed: {error_msg}")
                print(f"VotingController: Vote succeeded but binning failed: {error_msg}")
        else:
            print("VotingController: Failed to mark image as binned")
            if self.status_bar:
                self.status_bar.config(text=f"Vote recorded but {loser} was already binned")
    
    def _reset_button_appearance(self) -> None:
        """Restore vote buttons to their normal (non-bin) appearance."""
        if self.left_vote_button:
            self.left_vote_button.config(
                text="Vote for this image (←)", bg=Colors.BUTTON_SUCCESS)
        if self.right_vote_button:
            self.right_vote_button.config(
                text="Vote for this image (→)", bg=Colors.BUTTON_SUCCESS)

    def _bin_both_immediately(self, winner: str, loser: str) -> None:
        """Bin both the winner and the loser after a vote (bin-both mode).

        Uses an atomic pattern to avoid partial-purge inconsistencies:
          1. Mark BOTH as binned first.
          2. Purge each image's votes from remaining active images.
             Because both are already binned, the cross-vote between them
             is skipped by the purge loop — neither contaminates the other.
             All other active images are cleaned correctly.
          3. Move files. If a file move fails, only that image's bin mark is
             reversed (the other image stays binned and its purge already ran).
        """
        print(f"VotingController: _bin_both_immediately: {winner} and {loser}")

        if not self.image_binner:
            if self.status_bar:
                self.status_bar.config(text="Error: Image binner not initialized")
            return

        # Step 1 — Mark BOTH as binned atomically before any purge runs.
        marked = []
        for image in (winner, loser):
            if hasattr(self.data_manager, 'bin_image'):
                success = self.data_manager.bin_image(image)
            else:
                if not hasattr(self.data_manager, 'binned_images'):
                    self.data_manager.binned_images = set()
                success = image not in self.data_manager.binned_images
                if success:
                    self.data_manager.binned_images.add(image)
            if success:
                marked.append(image)
                print(f"VotingController: Marked {image} as binned")
            else:
                print(f"VotingController: {image} was already binned, skipping")

        if not marked:
            if self.status_bar:
                self.status_bar.config(text="Both images were already binned")
            return

        # Step 2 — Purge each marked image's vote history from active images.
        # Both images are already in binned_images, so the cross-vote between
        # them is safely skipped by purge_binned_image_votes — no interleaving
        # needed. Every remaining active image is cleaned correctly.
        for image in marked:
            if hasattr(self.data_manager, 'purge_binned_image_votes'):
                result = self.data_manager.purge_binned_image_votes(image)
                print(f"VotingController: Purged {image}: {result}")

        # Step 3 — Move files physically.
        binned, errors = [], []
        for image in marked:
            move_ok, err = self.image_binner.move_image_to_bin(image)
            if move_ok:
                binned.append(image)
                print(f"VotingController: Moved {image} to Bin")
            else:
                # File move failed — reverse only this image's bin mark.
                # Its votes were already purged from active images, which is
                # an acceptable trade-off vs. leaving stale data in the pool.
                if hasattr(self.data_manager, 'binned_images'):
                    self.data_manager.binned_images.discard(image)
                errors.append(f"{image}: {err}")
                print(f"VotingController: File move failed for {image}: {err}")

        self._update_stats_display()

        if binned:
            msg = f"🗑️🗑️ Both binned: {', '.join(binned)}"
            if errors:
                msg += f" | Errors: {'; '.join(errors)}"
        else:
            msg = f"Bin-both failed: {'; '.join(errors)}"

        if self.status_bar:
            self.status_bar.config(text=msg)

    def refresh_current_pair(self) -> None:
        """Refresh the currently displayed pair."""
        if self.current_pair[0] and self.current_pair[1]:
            self.image_display.display_image(self.current_pair[0], 'left')
            self.image_display.display_image(self.current_pair[1], 'right')
    
    def setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts for voting and binning."""
        print("VotingController: Setting up keyboard shortcuts...")
        
        # Hardcoded key bindings to avoid import issues
        VOTE_LEFT = ['<Left>', '<a>']
        VOTE_RIGHT = ['<Right>', '<d>']
        BIN_LOSER = ['<Down>']
        
        for key in VOTE_LEFT:
            self.parent.bind(key, lambda e: self.vote('left') if self.left_vote_button and self.left_vote_button['state'] == tk.NORMAL else None)
            print(f"VotingController: Bound key {key} to vote left")
        
        for key in VOTE_RIGHT:
            self.parent.bind(key, lambda e: self.vote('right') if self.right_vote_button and self.right_vote_button['state'] == tk.NORMAL else None)
            print(f"VotingController: Bound key {key} to vote right")
        
        # Binning shortcut - toggle bin mode for next vote
        for key in BIN_LOSER:
            self.parent.bind(key, lambda e: self.prepare_to_bin_next_loser())
            print(f"VotingController: Bound key {key} to prepare_to_bin_next_loser")
        
        # Alternative binning keys - bin last loser retroactively
        self.parent.bind('<b>', lambda e: self.bin_last_loser())
        self.parent.bind('<B>', lambda e: self.bin_last_loser())
        print("VotingController: Bound B/b keys to bin_last_loser")
        
        print("VotingController: Keyboard shortcuts setup complete")
    
    def reset_voting_state(self) -> None:
        """Reset voting state when loading new images."""
        print("VotingController: Resetting voting state...")
        self.current_pair = (None, None)
        self.next_pair = (None, None)
        self.previous_pair = (None, None)
        self.last_vote_result = None
        self.bin_mode = 0  # Reset bin mode
        
        if self.left_vote_button:
            self.left_vote_button.config(state=tk.DISABLED, text="Vote for this image (←)", bg=Colors.BUTTON_SUCCESS)
        if self.right_vote_button:
            self.right_vote_button.config(state=tk.DISABLED, text="Vote for this image (→)", bg=Colors.BUTTON_SUCCESS)
        
        if self.status_bar:
            self.status_bar.config(text="Select a folder to begin")
        
        print("VotingController: Voting state reset complete")
    
    def cleanup(self) -> None:
        """Clean up resources."""
        print("VotingController: Cleaning up...")
        if self.preload_timer:
            self.parent.after_cancel(self.preload_timer)
        
        self.reset_voting_state()
        print("VotingController: Cleanup complete")
