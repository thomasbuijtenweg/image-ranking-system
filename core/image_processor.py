"""
Image processing module for the Image Ranking System.

This module handles core image operations including loading, resizing,
and file validation. Metadata extraction is handled by a separate module.
"""

import os
from typing import Optional, Tuple, List
from PIL import Image, ImageTk

from config import Defaults
from core.metadata_extractor import MetadataExtractor


class ImageProcessor:
    """
    Handles core image processing operations for the ranking system.
    
    This class manages image loading, resizing, and file validation,
    with metadata extraction delegated to a specialized module.
    """
    
    def __init__(self):
        """Initialize the image processor."""
        self.supported_extensions = Defaults.SUPPORTED_IMAGE_EXTENSIONS
        self.metadata_extractor = MetadataExtractor()
    
    def get_image_files(self, folder_path: str) -> List[str]:
        """
        Get all supported image files from a folder and its subfolders recursively.
        
        Args:
            folder_path: Path to the folder containing images
            
        Returns:
            List of image file paths relative to the base folder
        """
        if not os.path.exists(folder_path):
            return []
        
        image_files = []
        
        try:
            # Use os.walk with followlinks=False to avoid infinite loops from circular symlinks
            for root, dirs, files in os.walk(folder_path, followlinks=False):
                # Skip hidden directories (optional - you can remove this filter if needed)
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    # Skip hidden files (optional - you can remove this filter if needed)
                    if file.startswith('.'):
                        continue
                        
                    if file.lower().endswith(self.supported_extensions):
                        # Get relative path from the base folder
                        full_path = os.path.join(root, file)
                        relative_path = os.path.relpath(full_path, folder_path)
                        
                        # Normalize path separators to forward slashes for consistency
                        # This ensures consistent storage in JSON files across platforms
                        relative_path = relative_path.replace(os.sep, '/')
                        
                        image_files.append(relative_path)
            
            return sorted(image_files)  # Sort for consistent ordering
            
        except OSError as e:
            print(f"Error scanning directory {folder_path}: {e}")
            return []
    
    def load_and_resize_image(self, image_path: str, max_width: int, max_height: int) -> Optional[ImageTk.PhotoImage]:
        """
        Load an image and resize it to fit within the specified dimensions.
        
        This method maintains the aspect ratio of the image while ensuring
        it fits within the given bounds. Uses proper resource management
        to prevent memory leaks.
        
        Args:
            image_path: Path to the image file
            max_width: Maximum width for the resized image
            max_height: Maximum height for the resized image
            
        Returns:
            PhotoImage object ready for display, or None if loading fails
        """
        try:
            # Use context manager to ensure proper cleanup
            with Image.open(image_path) as img:
                # Calculate scaling factor to fit within bounds
                img_width, img_height = img.size
                width_ratio = max_width / img_width
                height_ratio = max_height / img_height
                scale_factor = min(width_ratio, height_ratio)
                
                # Calculate new dimensions
                new_width = int(img_width * scale_factor)
                new_height = int(img_height * scale_factor)
                
                # Resize image maintaining aspect ratio
                # Create a copy to avoid issues with the context manager
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage for tkinter
                # Note: We need to keep the resized image in memory for PhotoImage
                return ImageTk.PhotoImage(resized_img)
            
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None
    
    def extract_prompt_from_image(self, image_path: str) -> Optional[str]:
        """
        Extract AI generation prompt from image metadata.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted prompt string, or None if not found
        """
        return self.metadata_extractor.extract_prompt_from_image(image_path)
    
    def get_image_metadata(self, image_path: str) -> Optional[str]:
        """
        Extract and format image metadata for display.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Formatted metadata string, or None if extraction fails
        """
        return self.metadata_extractor.get_image_metadata(image_path)
    
    def validate_image_file(self, image_path: str) -> bool:
        """
        Validate that a file is a readable image.
        
        Uses proper resource management to prevent memory leaks.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            True if the file is a valid image, False otherwise
        """
        try:
            # Use context manager to ensure proper cleanup
            with Image.open(image_path) as img:
                # Verify the image can be processed
                img.verify()
            return True
        except Exception:
            return False
    
    def get_image_dimensions(self, image_path: str) -> Optional[Tuple[int, int]]:
        """
        Get the dimensions of an image without fully loading it.
        
        Uses proper resource management to prevent memory leaks.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (width, height) or None if unable to read
        """
        try:
            # Use context manager to ensure proper cleanup
            with Image.open(image_path) as img:
                return img.size
        except Exception:
            return None
    
    def cleanup_resources(self):
        """
        Clean up any resources held by the image processor.
        
        This method can be called when the image processor is no longer needed
        to ensure all resources are properly released.
        """
        # Currently no persistent resources to clean up, but this method
        # provides a hook for future resource management needs
        pass
