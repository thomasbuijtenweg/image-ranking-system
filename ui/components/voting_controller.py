"""Modern voting controller for the Image Ranking System."""

import tkinter as tk
from typing import Optional, Tuple, Callable

from config import Colors, Fonts, Styling, ButtonStyles
from ui.components.ui_builder import ModernButton, ModernFrame


class ModernVoteButton(ModernButton):
    """Enhanced vote button with modern styling and animations."""
    
    def __init__(self, parent, side='left', **kwargs):
        # Configure button text and style based on side
        if side == 'left':
            text = "← Vote Left"
            style = 'success'
            self.accent_color = Colors.SUCCESS
        else:
            text = "Vote Right →"
            style = 'primary'
            self.accent_color = Colors.PURPLE_PRIMARY
        
        # Initialize with modern styling
        super().__init__(parent, text=text, style=style, **kwargs)
        
        # Enhanced styling for vote buttons
        self.configure(
            font=Fonts.HEADING,
            pady=Styling.PADDING_LARGE,
            padx=Styling.PADDING_EXTRA_LARGE
        )
        
        # Store side for animations
        self.side = side
        self.is_voting = False
        
        # Bind additional events for enhanced feedback
        self.bind('<Button-1>', self._on_vote_click)
        self.bind('<ButtonRelease-1>', self._on_vote_release)
    
    def _on_vote_click(self, event):
        """Handle vote button click with enhanced visual feedback."""
        if self.cget('state') == tk.NORMAL and not self.is_voting:
            self.is_voting = True
            
            # Immediate visual feedback
            self.configure(bg=Colors.PURPLE_SECONDARY)
            
            # Add pulsing effect
            self._pulse_effect()
    
    def _on_vote_release(self, event):
        """Handle button release."""
        if self.is_voting:
            self.after(100, self._reset_button_state)
    
    def _pulse_effect(self):
        """Create a subtle pulse effect."""
        if self.is_voting:
            # Pulse animation
            self.configure(relief='raised', borderwidth=2)
            self.after(50, lambda: self.configure(relief='flat', borderwidth=0))
    
    def _reset_button_state(self):
        """Reset button to normal state."""
        self.is_voting = False
        if self.side == 'left':
            self.configure(bg=Colors.SUCCESS)
        else:
            self.configure(bg=Colors.PURPLE_PRIMARY)
    
    def set_enabled(self, enabled: bool):
        """Enable or disable the button with modern styling."""
        if enabled:
            self.configure(state=tk.NORMAL)
            if self.side == 'left':
                self.configure(bg=Colors.SUCCESS, fg=Colors.TEXT_PRIMARY)
            else:
                self.configure(bg=Colors.PURPLE_PRIMARY, fg=Colors.TEXT_PRIMARY)
        else:
            self.configure(state=tk.DISABLED, bg=Colors.BG_TERTIARY, fg=Colors.TEXT_MUTED)


class ModernVotingInterface:
    """Modern voting interface with enhanced visual feedback."""
    
    def __init__(self, parent_window):
        self.parent = parent_window
        self.left_button = None
        self.right_button = None
        self.vote_callback = None
        self.status_callback = None
        
        # Animation state
        self.voting_in_progress = False
    
    def create_vote_buttons(self, left_frame: tk.Frame, right_frame: tk.Frame) -> None:
        """Create modern vote buttons in the specified frames."""
        # Left vote button
        self.left_button = ModernVoteButton(
            left_frame,
            side='left',
            command=lambda: self._handle_vote('left'),
            state=tk.DISABLED
        )
        
        # Position in grid
        self.left_button.grid(row=3, column=0, sticky="ew", 
                             padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        # Right vote button
        self.right_button = ModernVoteButton(
            right_frame,
            side='right',
            command=lambda: self._handle_vote('right'),
            state=tk.DISABLED
        )
        
        # Position in grid
        self.right_button.grid(row=3, column=0, sticky="ew", 
                              padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
    
    def _handle_vote(self, side: str) -> None:
        """Handle vote with modern visual feedback."""
        if self.voting_in_progress:
            return
        
        self.voting_in_progress = True
        
        # Disable both buttons immediately
        self.set_buttons_enabled(False)
        
        # Update status
        if self.status_callback:
            self.status_callback(f"Recording vote for {side} image...", Colors.PURPLE_PRIMARY)
        
        # Call the vote callback
        if self.vote_callback:
            self.vote_callback(side)
        
        # Visual feedback animation
        self._animate_vote_success(side)
    
    def _animate_vote_success(self, side: str) -> None:
        """Animate successful vote with modern effects."""
        # Highlight the winning side
        winning_button = self.left_button if side == 'left' else self.right_button
        
        # Success animation
        winning_button.configure(bg=Colors.SUCCESS, text="✓ Voted!")
        
        # Reset after animation
        self.parent.after(1000, self._reset_voting_state)
    
    def _reset_voting_state(self) -> None:
        """Reset voting state after animation."""
        self.voting_in_progress = False
        
        # Reset button text
        if self.left_button:
            self.left_button.configure(text="← Vote Left")
        if self.right_button:
            self.right_button.configure(text="Vote Right →")
    
    def set_buttons_enabled(self, enabled: bool) -> None:
        """Enable or disable vote buttons with modern styling."""
        if self.left_button:
            self.left_button.set_enabled(enabled)
        if self.right_button:
            self.right_button.set_enabled(enabled)
    
    def set_vote_callback(self, callback: Callable[[str], None]) -> None:
        """Set the callback function for vote events."""
        self.vote_callback = callback
    
    def set_status_callback(self, callback: Callable[[str, str], None]) -> None:
        """Set the callback function for status updates."""
        self.status_callback = callback
    
    def can_vote(self) -> bool:
        """Check if voting is currently possible."""
        return (not self.voting_in_progress and 
                self.left_button and self.left_button.cget('state') == tk.NORMAL and
                self.right_button and self.right_button.cget('state') == tk.NORMAL)


class VotingController:
    """Modern voting controller with enhanced interface and feedback."""
    
    def __init__(self, parent: tk.Tk, data_manager, ranking_algorithm, image_processor, image_display):
        self.parent = parent
        self.data_manager = data_manager
        self.ranking_algorithm = ranking_algorithm
        self.image_processor = image_processor
        self.image_display = image_display
        
        # Modern voting interface
        self.voting_interface = ModernVotingInterface(parent)
        
        # Current state
        self.current_pair = (None, None)
        self.next_pair = (None, None)
        self.previous_pair = (None, None)
        
        # UI references
        self.status_bar = None
        self.stats_label = None
        
        # Preloading
        self.preload_timer = None
        
        # Callbacks
        self.on_vote_callback = None
        
        # Setup voting interface callbacks
        self.voting_interface.set_vote_callback(self._process_vote)
        self.voting_interface.set_status_callback(self._update_status)
    
    def create_vote_buttons(self, left_frame: tk.Frame, right_frame: tk.Frame) -> None:
        """Create modern vote buttons for both sides."""
        self.voting_interface.create_vote_buttons(left_frame, right_frame)
        
        # Bind image click handlers
        self.image_display.bind_click_handlers(
            lambda: self._handle_image_click('left'),
            lambda: self._handle_image_click('right')
        )
    
    def _handle_image_click(self, side: str) -> None:
        """Handle image click with modern feedback."""
        if self.voting_interface.can_vote():
            # Visual feedback on image
            if side == 'left':
                image_label = self.image_display.left_image_label
            else:
                image_label = self.image_display.right_image_label
            
            # Flash effect
            original_bg = image_label.cget('bg')
            image_label.configure(bg=Colors.PURPLE_SECONDARY)
            self.parent.after(100, lambda: image_label.configure(bg=original_bg))
            
            # Process vote
            self.voting_interface._handle_vote(side)
    
    def _process_vote(self, side: str) -> None:
        """Process the vote with modern feedback."""
        if not self.current_pair[0] or not self.current_pair[1]:
            return
        
        winner = self.current_pair[0] if side == 'left' else self.current_pair[1]
        loser = self.current_pair[1] if side == 'left' else self.current_pair[0]
        
        # Record vote
        self.data_manager.record_vote(winner, loser)
        self.ranking_algorithm.invalidate_cache()
        
        # Update stats
        if self.stats_label:
            self.stats_label.config(text=f"Total votes: {self.data_manager.vote_count}")
        
        # Update status with success message
        success_message = f"✅ {winner} wins over {loser}"
        if self.status_bar:
            self.status_bar.config(text=success_message, fg=Colors.SUCCESS)
        
        # Call external callback
        if self.on_vote_callback:
            self.on_vote_callback(winner, loser)
        
        # Schedule next pair
        self.parent.after(1500, self.show_next_pair)
    
    def _update_status(self, message: str, color: str) -> None:
        """Update status bar with modern styling."""
        if self.status_bar:
            self.status_bar.config(text=message, fg=color)
    
    def set_ui_references(self, status_bar: tk.Label, stats_label: tk.Label) -> None:
        """Set references to UI elements."""
        self.status_bar = status_bar
        self.stats_label = stats_label
    
    def set_vote_callback(self, callback: Callable[[str, str], None]) -> None:
        """Set callback function for vote events."""
        self.on_vote_callback = callback
    
    def show_next_pair(self) -> None:
        """Display the next pair of images with modern interface."""
        if self.data_manager.image_folder == "":
            return
        
        images = self.image_processor.get_image_files(self.data_manager.image_folder)
        if len(images) < 2:
            return
        
        # Clear previous images
        self.image_display.clear_images()
        
        # Store previous pair
        if self.current_pair[0] and self.current_pair[1]:
            self.previous_pair = self.current_pair
        
        # Get next pair
        img1, img2 = self.ranking_algorithm.select_next_pair(images, self.previous_pair)
        if not img1 or not img2:
            return
        
        self.current_pair = (img1, img2)
        
        # Display images
        self.image_display.display_image(img1, 'left')
        self.image_display.display_image(img2, 'right')
        
        # Enable voting
        self.voting_interface.set_buttons_enabled(True)
        
        # Update status
        explanation = self.ranking_algorithm.get_selection_explanation(img1, img2)
        if self.status_bar:
            self.status_bar.config(text=explanation, fg=Colors.TEXT_PRIMARY)
        
        # Schedule preloading
        if self.preload_timer:
            self.parent.after_cancel(self.preload_timer)
        self.preload_timer = self.parent.after(100, self.preload_next_pair)
    
    def preload_next_pair(self) -> None:
        """Preload the next pair of images."""
        if self.data_manager.image_folder == "":
            return
        
        images = self.image_processor.get_image_files(self.data_manager.image_folder)
        if len(images) < 2:
            return
        
        self.next_pair = self.ranking_algorithm.select_next_pair(images, self.current_pair)
        
        if self.next_pair[0] and self.next_pair[1]:
            self.image_display.preload_images(self.next_pair[0], self.next_pair[1])
    
    def setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts for modern voting."""
        from config import KeyBindings
        
        # Vote left shortcuts
        for key in KeyBindings.VOTE_LEFT:
            self.parent.bind(key, lambda e: self._handle_keyboard_vote('left'))
        
        # Vote right shortcuts
        for key in KeyBindings.VOTE_RIGHT:
            self.parent.bind(key, lambda e: self._handle_keyboard_vote('right'))
    
    def _handle_keyboard_vote(self, side: str) -> None:
        """Handle keyboard voting with modern feedback."""
        if self.voting_interface.can_vote():
            self.voting_interface._handle_vote(side)
    
    def refresh_current_pair(self) -> None:
        """Refresh the currently displayed pair."""
        if self.current_pair[0] and self.current_pair[1]:
            self.image_display.display_image(self.current_pair[0], 'left')
            self.image_display.display_image(self.current_pair[1], 'right')
    
    def reset_voting_state(self) -> None:
        """Reset voting state when loading new images."""
        self.current_pair = (None, None)
        self.next_pair = (None, None)
        self.previous_pair = (None, None)
        
        # Disable voting buttons
        self.voting_interface.set_buttons_enabled(False)
        
        # Update status
        if self.status_bar:
            self.status_bar.config(text="Select a folder to begin", fg=Colors.TEXT_SECONDARY)
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.preload_timer:
            self.parent.after_cancel(self.preload_timer)
        
        self.reset_voting_state()
