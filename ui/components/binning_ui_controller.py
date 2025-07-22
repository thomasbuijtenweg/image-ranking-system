"""
Binning UI Controller for the Image Ranking System.

This module handles the user interface components for the binning functionality,
including bin buttons and their integration with the voting interface.
"""

import tkinter as tk
from tkinter import messagebox
from typing import Optional, Tuple, Callable

from config import Colors


class BinningUIController:
    """
    Handles the user interface for binning functionality.
    
    Manages bin buttons, user interactions, and integration with the voting system.
    """
    
    def __init__(self, parent: tk.Tk, binning_controller, voting_controller):
        """
        Initialize the binning UI controller.
        
        Args:
            parent: Parent tkinter window
            binning_controller: BinningController instance
            voting_controller: VotingController instance
        """
        self.parent = parent
        self.binning_controller = binning_controller
        self.voting_controller = voting_controller
        
        # UI elements
        self.bin_left_button = None
        self.bin_right_button = None
        self.bin_both_button = None
        
        # State
        self.current_pair = (None, None)
        
        # Callbacks
        self.on_image_binned_callback = None
        self.on_both_binned_callback = None
        
        # Setup binning controller callbacks
        self.binning_controller.set_image_binned_callback(self._on_image_binned)
        self.binning_controller.set_both_binned_callback(self._on_both_binned)
    
    def create_bin_buttons(self, left_frame: tk.Frame, right_frame: tk.Frame, center_frame: tk.Frame = None) -> None:
        """
        Create binning buttons for the voting interface.
        
        Args:
            left_frame: Frame for left image (for bin left button)
            right_frame: Frame for right image (for bin right button)  
            center_frame: Optional center frame (for bin both button)
        """
        # Create bin left button
        self.bin_left_button = tk.Button(
            left_frame,
            text="🗑️ Bin Left Image",
            command=self._bin_left_image,
            state=tk.DISABLED,
            font=('Arial', 10, 'bold'),
            bg=Colors.BUTTON_DANGER,
            fg='white',
            relief=tk.FLAT,
            height=1
        )
        
        # Create bin right button
        self.bin_right_button = tk.Button(
            right_frame,
            text="🗑️ Bin Right Image", 
            command=self._bin_right_image,
            state=tk.DISABLED,
            font=('Arial', 10, 'bold'),
            bg=Colors.BUTTON_DANGER,
            fg='white',
            relief=tk.FLAT,
            height=1
        )
        
        # Position buttons in their respective frames
        # Assuming the frames have a grid layout with voting buttons at row 3
        self.bin_left_button.grid(row=4, column=0, sticky="ew", padx=10, pady=5)
        self.bin_right_button.grid(row=4, column=0, sticky="ew", padx=10, pady=5)
        
        # Create bin both button if center frame is provided
        if center_frame:
            self.bin_both_button = tk.Button(
                center_frame,
                text="🗑️🗑️ Bin Both",
                command=self._bin_both_images,
                state=tk.DISABLED,
                font=('Arial', 11, 'bold'),
                bg=Colors.BUTTON_DANGER,
                fg='white',
                relief=tk.FLAT,
                height=2,
                wraplength=100
            )
            
            # Position bin both button in center
            self.bin_both_button.pack(pady=10)
    
    def update_current_pair(self, left_image: str, right_image: str) -> None:
        """
        Update the current pair of images being displayed.
        
        Args:
            left_image: Filename of left image
            right_image: Filename of right image
        """
        self.current_pair = (left_image, right_image)
        
        # Enable buttons if we have a valid pair
        if left_image and right_image:
            self._enable_bin_buttons()
        else:
            self._disable_bin_buttons()
    
    def _enable_bin_buttons(self) -> None:
        """Enable all bin buttons."""
        if self.bin_left_button:
            self.bin_left_button.config(state=tk.NORMAL)
        if self.bin_right_button:
            self.bin_right_button.config(state=tk.NORMAL)
        if self.bin_both_button:
            self.bin_both_button.config(state=tk.NORMAL)
    
    def _disable_bin_buttons(self) -> None:
        """Disable all bin buttons."""
        if self.bin_left_button:
            self.bin_left_button.config(state=tk.DISABLED)
        if self.bin_right_button:
            self.bin_right_button.config(state=tk.DISABLED)
        if self.bin_both_button:
            self.bin_both_button.config(state=tk.DISABLED)
    
    def _bin_left_image(self) -> None:
        """Handle binning the left image."""
        if not self.current_pair[0]:
            return
        
        # Confirm the action
        if not self._confirm_bin_action(self.current_pair[0]):
            return
        
        # Disable buttons during processing
        self._disable_bin_buttons()
        
        # Bin the image
        success = self.binning_controller.bin_image(self.current_pair[0])
        
        if success:
            # Show success message
            self._show_bin_success_message(self.current_pair[0])
            
            # Trigger callback to get new pair
            if self.on_image_binned_callback:
                self.on_image_binned_callback('left', self.current_pair[0])
        else:
            # Re-enable buttons on failure
            self._enable_bin_buttons()
    
    def _bin_right_image(self) -> None:
        """Handle binning the right image."""
        if not self.current_pair[1]:
            return
        
        # Confirm the action
        if not self._confirm_bin_action(self.current_pair[1]):
            return
        
        # Disable buttons during processing
        self._disable_bin_buttons()
        
        # Bin the image
        success = self.binning_controller.bin_image(self.current_pair[1])
        
        if success:
            # Show success message
            self._show_bin_success_message(self.current_pair[1])
            
            # Trigger callback to get new pair
            if self.on_image_binned_callback:
                self.on_image_binned_callback('right', self.current_pair[1])
        else:
            # Re-enable buttons on failure
            self._enable_bin_buttons()
    
    def _bin_both_images(self) -> None:
        """Handle binning both images."""
        if not self.current_pair[0] or not self.current_pair[1]:
            return
        
        # Confirm the action
        if not self._confirm_bin_both_action(self.current_pair[0], self.current_pair[1]):
            return
        
        # Disable buttons during processing
        self._disable_bin_buttons()
        
        # Bin both images
        success1, success2 = self.binning_controller.bin_both_images(self.current_pair[0], self.current_pair[1])
        
        if success1 and success2:
            # Show success message
            self._show_bin_both_success_message(self.current_pair[0], self.current_pair[1])
            
            # Trigger callback to get new pair
            if self.on_both_binned_callback:
                self.on_both_binned_callback(self.current_pair[0], self.current_pair[1])
        else:
            # Re-enable buttons on failure (partial success is handled by binning controller)
            self._enable_bin_buttons()
    
    def _confirm_bin_action(self, image_name: str) -> bool:
        """
        Confirm binning action with user.
        
        Args:
            image_name: Name of image to bin
            
        Returns:
            True if user confirms, False otherwise
        """
        message = (f"Are you sure you want to bin this image?\n\n"
                  f"Image: {image_name}\n\n"
                  f"This will:\n"
                  f"• Move the image to the 'Bin' subfolder\n"
                  f"• Mark it as low-tier, high-confidence\n"
                  f"• Remove it from future voting\n"
                  f"• Preserve its statistics\n\n"
                  f"This action can be undone by manually moving the image back.")
        
        return messagebox.askyesno("Confirm Bin Image", message, icon='warning')
    
    def _confirm_bin_both_action(self, image1: str, image2: str) -> bool:
        """
        Confirm binning both images with user.
        
        Args:
            image1: Name of first image
            image2: Name of second image
            
        Returns:
            True if user confirms, False otherwise
        """
        message = (f"Are you sure you want to bin BOTH images?\n\n"
                  f"Images:\n• {image1}\n• {image2}\n\n"
                  f"This will:\n"
                  f"• Move both images to the 'Bin' subfolder\n"
                  f"• Mark them as low-tier, high-confidence\n"
                  f"• Remove them from future voting\n"
                  f"• Preserve their statistics\n\n"
                  f"This action can be undone by manually moving the images back.")
        
        return messagebox.askyesno("Confirm Bin Both Images", message, icon='warning')
    
    def _show_bin_success_message(self, image_name: str) -> None:
        """Show success message for binning a single image."""
        bin_path = self.binning_controller.get_bin_folder_path()
        messagebox.showinfo("Image Binned", 
                           f"Successfully binned: {image_name}\n\n"
                           f"Moved to: {bin_path}")
    
    def _show_bin_both_success_message(self, image1: str, image2: str) -> None:
        """Show success message for binning both images."""
        bin_path = self.binning_controller.get_bin_folder_path()
        messagebox.showinfo("Images Binned", 
                           f"Successfully binned both images:\n"
                           f"• {image1}\n"
                           f"• {image2}\n\n"
                           f"Moved to: {bin_path}")
    
    def _on_image_binned(self, image_name: str) -> None:
        """Handle callback when an image is binned."""
        print(f"Image binned via UI: {image_name}")
    
    def _on_both_binned(self, image1: str, image2: str) -> None:
        """Handle callback when both images are binned."""
        print(f"Both images binned via UI: {image1}, {image2}")
    
    def set_image_binned_callback(self, callback: Callable[[str, str], None]) -> None:
        """
        Set callback for when a single image is binned.
        
        Args:
            callback: Function to call with (side, image_name)
        """
        self.on_image_binned_callback = callback
    
    def set_both_binned_callback(self, callback: Callable[[str, str], None]) -> None:
        """
        Set callback for when both images are binned.
        
        Args:
            callback: Function to call with (image1, image2)
        """
        self.on_both_binned_callback = callback
    
    def setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts for binning."""
        # Bin left: Ctrl+1
        self.parent.bind('<Control-1>', lambda e: self._bin_left_image() if self.bin_left_button and self.bin_left_button['state'] == tk.NORMAL else None)
        
        # Bin right: Ctrl+2  
        self.parent.bind('<Control-2>', lambda e: self._bin_right_image() if self.bin_right_button and self.bin_right_button['state'] == tk.NORMAL else None)
        
        # Bin both: Ctrl+3
        self.parent.bind('<Control-3>', lambda e: self._bin_both_images() if self.bin_both_button and self.bin_both_button['state'] == tk.NORMAL else None)
        
        print("Binning keyboard shortcuts enabled: Ctrl+1 (bin left), Ctrl+2 (bin right), Ctrl+3 (bin both)")
    
    def get_bin_button_references(self) -> Tuple[Optional[tk.Button], Optional[tk.Button], Optional[tk.Button]]:
        """
        Get references to the bin buttons for external use.
        
        Returns:
            Tuple of (bin_left_button, bin_right_button, bin_both_button)
        """
        return self.bin_left_button, self.bin_right_button, self.bin_both_button
    
    def update_button_states(self, enable: bool) -> None:
        """
        Update the state of all bin buttons.
        
        Args:
            enable: True to enable buttons, False to disable
        """
        if enable:
            self._enable_bin_buttons()
        else:
            self._disable_bin_buttons()
    
    def cleanup(self) -> None:
        """Clean up resources."""
        # Clear callbacks
        self.on_image_binned_callback = None
        self.on_both_binned_callback = None
        
        # Clear references
        self.bin_left_button = None
        self.bin_right_button = None
        self.bin_both_button = None
        self.current_pair = (None, None)
