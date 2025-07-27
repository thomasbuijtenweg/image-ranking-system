"""Image binning functionality for the Image Ranking System."""

import os
import shutil
from typing import Tuple, Optional


class ImageBinner:
    """Handles physical file operations for binning images."""
    
    def __init__(self, base_folder: str):
        self.base_folder = base_folder
        self.bin_folder = os.path.join(base_folder, "Bin")
    
    def ensure_bin_folder_exists(self) -> bool:
        """
        Create the Bin folder if it doesn't exist.
        
        Returns:
            True if folder exists or was created successfully
        """
        try:
            if not os.path.exists(self.bin_folder):
                os.makedirs(self.bin_folder)
                print(f"Created Bin folder: {self.bin_folder}")
            return True
        except Exception as e:
            print(f"Error creating Bin folder: {e}")
            return False
    
    def move_image_to_bin(self, image_name: str) -> Tuple[bool, str]:
        """
        Move an image file to the Bin folder.
        
        Args:
            image_name: Relative path/name of the image to move
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Ensure bin folder exists
            if not self.ensure_bin_folder_exists():
                return False, "Could not create Bin folder"
            
            # Get source and destination paths
            source_path = os.path.join(self.base_folder, image_name)
            
            # Handle subdirectories: flatten the path for bin folder
            filename_only = os.path.basename(image_name)
            dest_path = os.path.join(self.bin_folder, filename_only)
            
            # Check if source exists
            if not os.path.exists(source_path):
                return False, f"Source file not found: {source_path}"
            
            # Move the file
            shutil.move(source_path, dest_path)
            print(f"Moved {source_path} -> {dest_path}")
            
            return True, ""
            
        except Exception as e:
            error_msg = f"Error moving image to bin: {e}"
            print(error_msg)
            return False, error_msg
    
    def get_binned_image_path(self, image_name: str) -> str:
        """Get the full path to a binned image."""
        filename_only = os.path.basename(image_name)
        return os.path.join(self.bin_folder, filename_only)
    
    def is_image_in_bin(self, image_name: str) -> bool:
        """Check if an image file exists in the bin folder."""
        binned_path = self.get_binned_image_path(image_name)
        return os.path.exists(binned_path)