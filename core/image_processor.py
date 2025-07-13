"""
Image processing module for the Image Ranking System.

This module handles all image-related operations including:
- Loading and resizing images for display
- Extracting metadata and AI generation prompts
- Formatting metadata for display
- Managing image file validation

By centralizing image operations here, we can easily modify how images
are processed without affecting the rest of the application.
"""

import os
from typing import Optional, Tuple, List
from PIL import Image, ImageTk
from PIL.ExifTags import TAGS

from config import Defaults


class ImageProcessor:
    """
    Handles all image processing operations for the ranking system.
    
    This class manages image loading, resizing, and metadata extraction,
    providing a clean interface for the rest of the application.
    """
    
    def __init__(self):
        """Initialize the image processor."""
        self.supported_extensions = Defaults.SUPPORTED_IMAGE_EXTENSIONS
        self.prompt_keywords = Defaults.PROMPT_KEYWORDS
        self.ai_keywords = Defaults.AI_KEYWORDS
    
    def get_image_files(self, folder_path: str) -> List[str]:
        """
        Get all supported image files from a folder.
        
        Args:
            folder_path: Path to the folder containing images
            
        Returns:
            List of image filenames
        """
        if not os.path.exists(folder_path):
            return []
        
        try:
            files = os.listdir(folder_path)
            return [f for f in files if f.lower().endswith(self.supported_extensions)]
        except OSError:
            return []
    
    def load_and_resize_image(self, image_path: str, max_width: int, max_height: int) -> Optional[ImageTk.PhotoImage]:
        """
        Load an image and resize it to fit within the specified dimensions.
        
        This method maintains the aspect ratio of the image while ensuring
        it fits within the given bounds.
        
        Args:
            image_path: Path to the image file
            max_width: Maximum width for the resized image
            max_height: Maximum height for the resized image
            
        Returns:
            PhotoImage object ready for display, or None if loading fails
        """
        try:
            # Load the image
            img = Image.open(image_path)
            
            # Calculate scaling factor to fit within bounds
            img_width, img_height = img.size
            width_ratio = max_width / img_width
            height_ratio = max_height / img_height
            scale_factor = min(width_ratio, height_ratio)
            
            # Calculate new dimensions
            new_width = int(img_width * scale_factor)
            new_height = int(img_height * scale_factor)
            
            # Resize image maintaining aspect ratio
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage for tkinter
            return ImageTk.PhotoImage(img)
            
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None
    
    def extract_prompt_from_image(self, image_path: str) -> Optional[str]:
        """
        Extract AI generation prompt from image metadata.
        
        This method checks multiple metadata sources commonly used by
        AI image generation tools to store prompt information.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted prompt string, or None if not found
        """
        try:
            img = Image.open(image_path)
            
            # Method 1: PNG text chunks (most common for AI-generated images)
            if img.format == 'PNG' and hasattr(img, 'text'):
                prompt = self._extract_from_png_text(img.text)
                if prompt:
                    return prompt
            
            # Method 2: PIL info dictionary
            if hasattr(img, 'info'):
                prompt = self._extract_from_pil_info(img.info)
                if prompt:
                    return prompt
            
            # Method 3: EXIF data
            exifdata = img.getexif()
            if exifdata:
                prompt = self._extract_from_exif(exifdata)
                if prompt:
                    return prompt
            
            return None
            
        except Exception as e:
            print(f"Error extracting prompt from {image_path}: {e}")
            return None
    
    def _extract_from_png_text(self, png_text: dict) -> Optional[str]:
        """
        Extract prompt from PNG text chunks.
        
        Args:
            png_text: Dictionary of PNG text chunks
            
        Returns:
            Extracted prompt or None
        """
        # Try common prompt fields first
        for field in self.prompt_keywords:
            if field in png_text:
                return png_text[field]
        
        # Try any field with prompt-like keywords
        for key, value in png_text.items():
            if any(keyword in key.lower() for keyword in ['prompt', 'parameter', 'generation']):
                return value
        
        return None
    
    def _extract_from_pil_info(self, info_dict: dict) -> Optional[str]:
        """
        Extract prompt from PIL info dictionary.
        
        Args:
            info_dict: PIL image info dictionary
            
        Returns:
            Extracted prompt or None
        """
        # Try common prompt fields first
        for field in self.prompt_keywords:
            if field in info_dict:
                return info_dict[field]
        
        # Search for prompt-like content
        for key, value in info_dict.items():
            if isinstance(value, str) and any(keyword in str(key).lower() for keyword in ['prompt', 'parameter']):
                return value
        
        return None
    
    def _extract_from_exif(self, exifdata: dict) -> Optional[str]:
        """
        Extract prompt from EXIF data.
        
        Args:
            exifdata: EXIF data dictionary
            
        Returns:
            Extracted prompt or None
        """
        for tag_id in exifdata:
            tag = TAGS.get(tag_id, tag_id)
            value = exifdata.get(tag_id)
            
            if isinstance(value, str) and len(value) > 20:
                # Check if this looks like a prompt
                if any(keyword in value.lower() for keyword in self.ai_keywords):
                    return value
            
            # Check specific EXIF fields
            if tag in ['ImageDescription', 'UserComment', 'Software'] and isinstance(value, str):
                if len(value) > 10:
                    return value
        
        return None
    
    def get_image_metadata(self, image_path: str) -> Optional[str]:
        """
        Extract and format image metadata for display.
        
        This method extracts various metadata fields and formats them
        into a readable string for display in the user interface.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Formatted metadata string, or None if extraction fails
        """
        metadata_lines = []
        
        try:
            img = Image.open(image_path)
            
            # Basic image information
            metadata_lines.append(f"Size: {img.width} × {img.height}")
            metadata_lines.append(f"Format: {img.format}")
            metadata_lines.append(f"Mode: {img.mode}")
            
            # File size
            file_size = os.path.getsize(image_path)
            size_str = self._format_file_size(file_size)
            metadata_lines.append(f"File size: {size_str}")
            
            # Extract EXIF data for camera information
            exifdata = img.getexif()
            if exifdata:
                self._add_exif_metadata(exifdata, metadata_lines)
            
            # Limit number of lines displayed
            if len(metadata_lines) > 10:
                metadata_lines = metadata_lines[:10]
                metadata_lines.append("...")
            
            return '\n'.join(metadata_lines)
            
        except Exception as e:
            return f"Error reading metadata: {str(e)}"
    
    def _format_file_size(self, size_bytes: int) -> str:
        """
        Convert bytes to human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Human-readable size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def _add_exif_metadata(self, exifdata: dict, metadata_lines: List[str]) -> None:
        """
        Add relevant EXIF metadata to the display lines.
        
        Args:
            exifdata: EXIF data dictionary
            metadata_lines: List to append metadata lines to
        """
        # Priority EXIF tags for display
        priority_tags = {
            'DateTime': 'Date taken',
            'DateTimeOriginal': 'Original date',
            'Make': 'Camera make',
            'Model': 'Camera model',
            'ExposureTime': 'Exposure',
            'FNumber': 'F-stop',
            'ISO': 'ISO',
            'FocalLength': 'Focal length',
            'LensModel': 'Lens',
            'Software': 'Software',
            'Artist': 'Artist',
            'Copyright': 'Copyright',
            'ImageDescription': 'Description',
            'UserComment': 'User Comment'
        }
        
        for tag_id in exifdata:
            tag = TAGS.get(tag_id, tag_id)
            if tag in priority_tags:
                value = exifdata.get(tag_id)
                if value:
                    formatted_value = self._format_exif_value(tag, value)
                    if formatted_value:
                        # Truncate long values
                        if len(formatted_value) > 30:
                            formatted_value = formatted_value[:27] + "..."
                        
                        metadata_lines.append(f"{priority_tags[tag]}: {formatted_value}")
    
    def _format_exif_value(self, tag: str, value) -> Optional[str]:
        """
        Format EXIF values for display.
        
        Args:
            tag: EXIF tag name
            value: Raw EXIF value
            
        Returns:
            Formatted value string or None
        """
        try:
            if tag == 'ExposureTime':
                if isinstance(value, tuple):
                    return f"{value[0]}/{value[1]}s"
                else:
                    return f"{value}s"
            elif tag == 'FNumber':
                if isinstance(value, tuple):
                    return f"f/{float(value[0])/float(value[1]):.1f}"
                else:
                    return f"f/{value}"
            elif tag == 'FocalLength':
                if isinstance(value, tuple):
                    return f"{float(value[0])/float(value[1]):.1f}mm"
                else:
                    return f"{value}mm"
            else:
                return str(value)
        except:
            return str(value)
    
    def validate_image_file(self, image_path: str) -> bool:
        """
        Validate that a file is a readable image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            True if the file is a valid image, False otherwise
        """
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True
        except Exception:
            return False
    
    def get_image_dimensions(self, image_path: str) -> Optional[Tuple[int, int]]:
        """
        Get the dimensions of an image without fully loading it.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (width, height) or None if unable to read
        """
        try:
            with Image.open(image_path) as img:
                return img.size
        except Exception:
            return None