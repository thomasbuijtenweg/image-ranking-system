"""Optimized image processor with file scanning and metadata extraction."""

import os
import fnmatch
from typing import Optional, Tuple, List, Set
from PIL import Image, ImageTk
import concurrent.futures
import threading

from config import Defaults
from core.metadata_extractor import MetadataExtractor
from core.image_binner import ImageBinner


class ImageProcessor:
    """Optimized image processor for large collections."""
    
    def __init__(self):
        self.supported_extensions = Defaults.SUPPORTED_IMAGE_EXTENSIONS
        self.metadata_extractor = MetadataExtractor()
        self._file_cache = {}
        self._cache_lock = threading.Lock()
    
    def get_image_files(self, folder_path: str, exclude_bin_folder: bool = True, use_cache: bool = True) -> List[str]:
        """Get all supported image files from a folder, optionally excluding Bin folder."""
        if not os.path.exists(folder_path):
            return []
        
        if use_cache:
            with self._cache_lock:
                cache_key = os.path.abspath(folder_path)
                if cache_key in self._file_cache:
                    cached_data = self._file_cache[cache_key]
                    try:
                        current_mtime = os.path.getmtime(folder_path)
                        if abs(current_mtime - cached_data['mtime']) < 1.0:
                            return cached_data['files']
                    except OSError:
                        pass
        
        image_files = self._scan_folder_optimized(folder_path, exclude_bin_folder)
        
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
    
    def _scan_folder_optimized(self, folder_path: str, exclude_bin_folder: bool = True) -> List[str]:
        """Optimized folder scanning with optional Bin folder exclusion."""
        image_files = []
        extensions_lower = set(ext.lower() for ext in self.supported_extensions)
        
        try:
            for root, dirs, files in os.walk(folder_path, followlinks=False):
                # Skip hidden directories and optionally the Bin folder
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                if exclude_bin_folder:
                    dirs[:] = [d for d in dirs if d.lower() != 'bin']
                
                batch_size = 1000
                for i in range(0, len(files), batch_size):
                    file_batch = files[i:i + batch_size]
                    
                    for file in file_batch:
                        if file.startswith('.'):
                            continue
                        
                        file_lower = file.lower()
                        if any(file_lower.endswith(ext) for ext in extensions_lower):
                            full_path = os.path.join(root, file)
                            relative_path = os.path.relpath(full_path, folder_path)
                            relative_path = relative_path.replace(os.sep, '/')
                            image_files.append(relative_path)
            
            return sorted(image_files)
            
        except OSError as e:
            print(f"Error scanning directory {folder_path}: {e}")
            return []
        
    def load_and_resize_image(self, image_path: str, max_width: int, max_height: int) -> Optional[ImageTk.PhotoImage]:
        """Load an image and resize it with optimizations."""
        try:
            with Image.open(image_path) as img:
                img_width, img_height = img.size
                
                if img_width <= max_width and img_height <= max_height:
                    img_copy = img.copy()
                    return ImageTk.PhotoImage(img_copy)
                
                width_ratio = max_width / img_width
                height_ratio = max_height / img_height
                scale_factor = min(width_ratio, height_ratio)
                
                new_width = int(img_width * scale_factor)
                new_height = int(img_height * scale_factor)
                
                resample_method = Image.Resampling.BILINEAR if (new_width * new_height) > 500000 else Image.Resampling.LANCZOS
                
                resized_img = img.resize((new_width, new_height), resample_method)
                return ImageTk.PhotoImage(resized_img)
            
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            return None
    
    def get_binned_image_files(self, folder_path: str) -> List[str]:
        """Get image files from the Bin folder for word analysis."""
        bin_folder = os.path.join(folder_path, "Bin")
        if not os.path.exists(bin_folder):
            return []
        
        return self._scan_single_folder(bin_folder)
    
    def _scan_single_folder(self, folder_path: str) -> List[str]:
        """Scan a single folder for image files."""
        image_files = []
        extensions_lower = set(ext.lower() for ext in self.supported_extensions)
        
        try:
            for file in os.listdir(folder_path):
                if file.startswith('.'):
                    continue
                
                file_lower = file.lower()
                if any(file_lower.endswith(ext) for ext in extensions_lower):
                    image_files.append(file)
            
            return sorted(image_files)
            
        except OSError as e:
            print(f"Error scanning folder {folder_path}: {e}")
            return []
    
    def extract_prompt_from_image(self, image_path: str) -> Optional[str]:
        """Extract AI generation prompt from image metadata."""
        return self.metadata_extractor.extract_prompt_from_image(image_path)
    
    def get_image_metadata(self, image_path: str) -> Optional[str]:
        """Extract and format image metadata for display."""
        return self.metadata_extractor.get_image_metadata(image_path)
        
    def clear_file_cache(self):
        """Clear the file cache to free memory."""
        with self._cache_lock:
            self._file_cache.clear()
        
    def cleanup_resources(self):
        """Clean up resources and caches."""
        self.clear_file_cache()
        if hasattr(self.metadata_extractor, 'cleanup_resources'):
            self.metadata_extractor.cleanup_resources()