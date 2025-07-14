"""
Metadata extraction module for the Image Ranking System.

This module handles extraction of metadata and AI generation prompts
from various image formats and metadata sources.
"""

import os
from typing import Optional, List
from PIL import Image
from PIL.ExifTags import TAGS

from config import Defaults


class MetadataExtractor:
    """
    Handles extraction of metadata and prompts from images.
    
    This class specializes in extracting AI generation prompts and
    general metadata from various image sources and formats.
    """
    
    def __init__(self):
        """Initialize the metadata extractor."""
        self.prompt_keywords = Defaults.PROMPT_KEYWORDS
        self.ai_keywords = Defaults.AI_KEYWORDS
    
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
            with Image.open(image_path) as img:
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
                try:
                    exifdata = img.getexif()
                    if exifdata:
                        prompt = self._extract_from_exif(exifdata)
                        if prompt:
                            return prompt
                except Exception as exif_error:
                    print(f"Error reading EXIF data from {image_path}: {exif_error}")
                
                return None
            
        except Exception as e:
            print(f"Error extracting prompt from {image_path}: {e}")
            return None
    
    def get_image_metadata(self, image_path: str) -> Optional[str]:
        """
        Extract and format image metadata for display.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Formatted metadata string, or None if extraction fails
        """
        metadata_lines = []
        
        try:
            with Image.open(image_path) as img:
                # Basic image information
                metadata_lines.append(f"Size: {img.width} × {img.height}")
                metadata_lines.append(f"Format: {img.format}")
                metadata_lines.append(f"Mode: {img.mode}")
                
                # File size
                file_size = os.path.getsize(image_path)
                size_str = self._format_file_size(file_size)
                metadata_lines.append(f"File size: {size_str}")
                
                # Extract EXIF data for camera information
                try:
                    exifdata = img.getexif()
                    if exifdata:
                        self._add_exif_metadata(exifdata, metadata_lines)
                except Exception as exif_error:
                    print(f"Error reading EXIF data from {image_path}: {exif_error}")
                    metadata_lines.append("EXIF data unavailable")
                
                # Limit number of lines displayed
                if len(metadata_lines) > 10:
                    metadata_lines = metadata_lines[:10]
                    metadata_lines.append("...")
                
                return '\n'.join(metadata_lines)
            
        except Exception as e:
            return f"Error reading metadata: {str(e)}"
    
    def _extract_from_png_text(self, png_text: dict) -> Optional[str]:
        """Extract prompt from PNG text chunks."""
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
        """Extract prompt from PIL info dictionary."""
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
        """Extract prompt from EXIF data."""
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
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Convert bytes to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def _add_exif_metadata(self, exifdata: dict, metadata_lines: List[str]) -> None:
        """Add relevant EXIF metadata to the display lines."""
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
        """Format EXIF values for display."""
        try:
            if tag == 'ExposureTime':
                if isinstance(value, tuple) and len(value) == 2:
                    return f"{value[0]}/{value[1]}s"
                else:
                    return f"{value}s"
            elif tag == 'FNumber':
                if isinstance(value, tuple) and len(value) == 2:
                    return f"f/{float(value[0])/float(value[1]):.1f}"
                else:
                    return f"f/{value}"
            elif tag == 'FocalLength':
                if isinstance(value, tuple) and len(value) == 2:
                    return f"{float(value[0])/float(value[1]):.1f}mm"
                else:
                    return f"{value}mm"
            else:
                return str(value)
        except (ValueError, ZeroDivisionError, TypeError):
            return str(value)
