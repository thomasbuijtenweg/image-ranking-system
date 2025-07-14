"""
Optimized image processor with improved file scanning and metadata extraction.
"""

import os
import fnmatch
from typing import Optional, Tuple, List, Set
from PIL import Image, ImageTk
import concurrent.futures
import threading

from config import Defaults
from core.metadata_extractor import MetadataExtractor


class ImageProcessor:
    """
    Optimized image processor with improved performance for large collections.
    """
    
    def __init__(self):
        """Initialize the image processor."""
        self.supported_extensions = Defaults.SUPPORTED_IMAGE_EXTENSIONS
        self.metadata_extractor = MetadataExtractor()
        
        # Cache for file lists to avoid repeated scanning
        self._file_cache = {}
        self._cache_lock = threading.Lock()
    
    def get_image_files(self, folder_path: str, use_cache: bool = True) -> List[str]:
        """
        Get all supported image files from a folder with optimized scanning.
        
        Args:
            folder_path: Path to the folder containing images
            use_cache: Whether to use cached results if available
            
        Returns:
            List of image file paths relative to the base folder
        """
        if not os.path.exists(folder_path):
            return []
        
        # Check cache first
        if use_cache:
            with self._cache_lock:
                cache_key = os.path.abspath(folder_path)
                if cache_key in self._file_cache:
                    cached_data = self._file_cache[cache_key]
                    # Check if cache is still valid (folder not modified)
                    try:
                        current_mtime = os.path.getmtime(folder_path)
                        if abs(current_mtime - cached_data['mtime']) < 1.0:
                            return cached_data['files']
                    except OSError:
                        pass
        
        # Scan folder with optimizations
        image_files = self._scan_folder_optimized(folder_path)
        
        # Update cache
        if use_cache:
            with self._cache_lock:
                try:
                    cache_key = os.path.abspath(folder_path)
                    self._file_cache[cache_key] = {
                        'files': image_files,
                        'mtime': os.path.getmtime(folder_path)
                    }
                except OSError:
                    pass
        
        return image_files
    
    def _scan_folder_optimized(self, folder_path: str) -> List[str]:
        """
        Optimized folder scanning with better performance.
        
        Args:
            folder_path: Path to scan
            
        Returns:
            List of relative image file paths
        """
        image_files = []
        
        # Create a set of lowercase extensions for faster lookup
        extensions_lower = set(ext.lower() for ext in self.supported_extensions)
        
        try:
            # Use os.walk with optimizations
            for root, dirs, files in os.walk(folder_path, followlinks=False):
                # Skip hidden directories early
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                # Process files in batches for better performance
                batch_size = 1000
                for i in range(0, len(files), batch_size):
                    file_batch = files[i:i + batch_size]
                    
                    for file in file_batch:
                        # Skip hidden files
                        if file.startswith('.'):
                            continue
                        
                        # Quick extension check without multiple string operations
                        file_lower = file.lower()
                        if any(file_lower.endswith(ext) for ext in extensions_lower):
                            # Get relative path from the base folder
                            full_path = os.path.join(root, file)
                            relative_path = os.path.relpath(full_path, folder_path)
                            
                            # Normalize path separators for consistency
                            relative_path = relative_path.replace(os.sep, '/')
                            
                            image_files.append(relative_path)
            
            return sorted(image_files)  # Sort for consistent ordering
            
        except OSError as e:
            print(f"Error scanning directory {folder_path}: {e}")
            return []
    
        
    def load_and_resize_image(self, image_path: str, max_width: int, max_height: int) -> Optional[ImageTk.PhotoImage]:
        """
        Load an image and resize it with optimizations for better performance.
        """
        try:
            # Use context manager to ensure proper cleanup
            with Image.open(image_path) as img:
                # Quick size check to avoid unnecessary processing
                img_width, img_height = img.size
                
                # If image is already smaller than target, don't resize
                if img_width <= max_width and img_height <= max_height:
                    # Create a copy for PhotoImage (context manager will close original)
                    img_copy = img.copy()
                    return ImageTk.PhotoImage(img_copy)
                
                # Calculate scaling factor to fit within bounds
                width_ratio = max_width / img_width
                height_ratio = max_height / img_height
                scale_factor = min(width_ratio, height_ratio)
                
                # Calculate new dimensions
                new_width = int(img_width * scale_factor)
                new_height = int(img_height * scale_factor)
                
                # Use optimized resampling for better performance vs quality balance
                # LANCZOS is high quality but slow, BILINEAR is faster
                resample_method = Image.Resampling.BILINEAR if (new_width * new_height) > 500000 else Image.Resampling.LANCZOS
                
                # Resize image maintaining aspect ratio
                resized_img = img.resize((new_width, new_height), resample_method)
                
                # Convert to PhotoImage for tkinter
                return ImageTk.PhotoImage(resized_img)
            
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None
    
    def extract_prompt_from_image(self, image_path: str) -> Optional[str]:
        """
        Extract AI generation prompt from image metadata with caching.
        """
        return self.metadata_extractor.extract_prompt_from_image(image_path)
    
    def get_image_metadata(self, image_path: str) -> Optional[str]:
        """
        Extract and format image metadata for display with optimizations.
        """
        return self.metadata_extractor.get_image_metadata(image_path)
    
        
      
    def clear_file_cache(self):
        """Clear the file cache to free memory."""
        with self._cache_lock:
            self._file_cache.clear()
    
        
    def cleanup_resources(self):
        """
        Clean up resources and caches.
        """
        self.clear_file_cache()
        if hasattr(self.metadata_extractor, 'cleanup_resources'):
            self.metadata_extractor.cleanup_resources()
