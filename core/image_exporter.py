"""Image export functionality for the Image Ranking System.

Mirrors ImageBinner but targets an 'Exports' folder instead of 'Bin'.
Used to move the top-N ranked images out of the active sorting pool.
"""

import os
import shutil
from typing import Tuple


class ImageExporter:
    """Handles physical file operations for exporting top-ranked images."""
    
    def __init__(self, base_folder: str):
        self.base_folder = base_folder
        self.export_folder = os.path.join(base_folder, "Exports")
    
    def ensure_export_folder_exists(self) -> bool:
        """Create the Exports folder if it doesn't exist."""
        try:
            if not os.path.exists(self.export_folder):
                os.makedirs(self.export_folder)
                print(f"Created Exports folder: {self.export_folder}")
            return True
        except Exception as e:
            print(f"Error creating Exports folder: {e}")
            return False
    
    def move_image_to_exports(self, image_name: str) -> Tuple[bool, str]:
        """
        Move an image file to the Exports folder.

        Args:
            image_name: Relative path/name of the image to move

        Returns:
            Tuple of (success, error_message)
        """
        try:
            if not self.ensure_export_folder_exists():
                return False, "Could not create Exports folder"
            
            source_path = os.path.join(self.base_folder, image_name)
            filename_only = os.path.basename(image_name)
            dest_path = os.path.join(self.export_folder, filename_only)
            
            if not os.path.exists(source_path):
                return False, f"Source file not found: {source_path}"
            
            shutil.move(source_path, dest_path)
            print(f"Exported {source_path} -> {dest_path}")
            return True, ""
            
        except Exception as e:
            error_msg = f"Error moving image to Exports: {e}"
            print(error_msg)
            return False, error_msg
    
    def get_exported_image_path(self, image_name: str) -> str:
        """Get the full path to an exported image."""
        filename_only = os.path.basename(image_name)
        return os.path.join(self.export_folder, filename_only)
    
    def is_image_exported(self, image_name: str) -> bool:
        """Check if an image file exists in the Exports folder."""
        return os.path.exists(self.get_exported_image_path(image_name))
