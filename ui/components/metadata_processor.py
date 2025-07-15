"""
Metadata processor for the Image Ranking System.

This module handles background metadata extraction and processing
for large image collections.
"""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Set
import os


class MetadataProcessor:
    """
    Handles background metadata extraction and processing.
    
    This processor manages the background extraction of metadata from images
    to improve performance with large collections.
    """
    
    def __init__(self, data_manager, image_processor):
        """
        Initialize the metadata processor.
        
        Args:
            data_manager: DataManager instance
            image_processor: ImageProcessor instance
        """
        self.data_manager = data_manager
        self.image_processor = image_processor
        
        # Background processing
        self.metadata_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="metadata")
        self.metadata_futures = {}  # Track background metadata extraction
        self.loading_cancelled = False
        
        # Callbacks
        self.on_progress_callback = None
        self.on_complete_callback = None
    
    def set_progress_callback(self, callback) -> None:
        """
        Set callback function for progress updates.
        
        Args:
            callback: Function to call with progress updates (completed, total, message)
        """
        self.on_progress_callback = callback
    
    def set_complete_callback(self, callback) -> None:
        """
        Set callback function for completion.
        
        Args:
            callback: Function to call when processing is complete
        """
        self.on_complete_callback = callback
    
    def start_background_extraction(self, images: list) -> None:
        """
        Start background metadata extraction for images without metadata.
        
        Args:
            images: List of image filenames to process
        """
        self.loading_cancelled = False
        
        # Find images that need metadata extraction
        images_needing_metadata = []
        for img in images:
            stats = self.data_manager.get_image_stats(img)
            if stats.get('prompt') is None and stats.get('display_metadata') is None:
                images_needing_metadata.append(img)
        
        if not images_needing_metadata:
            print("No images need metadata extraction")
            if self.on_complete_callback:
                self.on_complete_callback(0)
            return
        
        print(f"Starting background metadata extraction for {len(images_needing_metadata)} images")
        
        # Submit metadata extraction tasks
        for img in images_needing_metadata:
            if not self.loading_cancelled:
                future = self.metadata_executor.submit(self.extract_metadata_for_image, img)
                self.metadata_futures[future] = img
        
        # Start a thread to collect results
        threading.Thread(target=self.collect_metadata_results, daemon=True).start()
    
    def extract_metadata_for_image(self, img_filename: str) -> tuple:
        """
        Extract metadata for a single image (runs in background thread).
        
        Args:
            img_filename: Name of the image file
            
        Returns:
            Tuple of (img_filename, prompt, metadata)
        """
        try:
            img_path = os.path.join(self.data_manager.image_folder, img_filename)
            
            # Extract prompt and metadata
            prompt = self.image_processor.extract_prompt_from_image(img_path)
            metadata = self.image_processor.get_image_metadata(img_path)
            
            return img_filename, prompt, metadata
            
        except Exception as e:
            print(f"Error extracting metadata from {img_filename}: {e}")
            return img_filename, None, None
    
    def collect_metadata_results(self) -> None:
        """Collect metadata extraction results from background threads."""
        completed_count = 0
        total_count = len(self.metadata_futures)
        
        for future in as_completed(self.metadata_futures):
            if self.loading_cancelled:
                break
                
            try:
                img_filename, prompt, metadata = future.result()
                
                # Update data manager
                self.data_manager.set_image_metadata(img_filename, prompt, metadata)
                
                completed_count += 1
                
                # Update progress periodically
                if completed_count % 50 == 0 or completed_count == total_count:
                    if self.on_progress_callback:
                        progress_message = f"Background metadata extraction: {completed_count}/{total_count} completed"
                        self.on_progress_callback(completed_count, total_count, progress_message)
                    
            except Exception as e:
                print(f"Error collecting metadata result: {e}")
        
        # Clear futures dict
        self.metadata_futures.clear()
        
        if not self.loading_cancelled:
            if self.on_complete_callback:
                self.on_complete_callback(total_count)
    
    def get_image_metadata_lazy(self, img_filename: str) -> tuple:
        """
        Get metadata for an image, extracting it if not available.
        
        Args:
            img_filename: Name of the image file
            
        Returns:
            Tuple of (prompt, display_metadata)
        """
        stats = self.data_manager.get_image_stats(img_filename)
        
        # If we already have metadata, return it
        if stats.get('prompt') is not None or stats.get('display_metadata') is not None:
            return stats.get('prompt'), stats.get('display_metadata')
        
        # If metadata extraction is in progress, return None (will be updated later)
        for future in self.metadata_futures:
            if self.metadata_futures[future] == img_filename:
                return None, "Metadata loading..."
        
        # If no extraction in progress, extract synchronously for critical images
        try:
            img_path = os.path.join(self.data_manager.image_folder, img_filename)
            prompt = self.image_processor.extract_prompt_from_image(img_path)
            metadata = self.image_processor.get_image_metadata(img_path)
            
            # Update data manager
            self.data_manager.set_image_metadata(img_filename, prompt, metadata)
            
            return prompt, metadata
            
        except Exception as e:
            print(f"Error extracting metadata for {img_filename}: {e}")
            return None, f"Error: {str(e)}"
    
    def cancel_extraction(self) -> None:
        """Cancel the metadata extraction process."""
        self.loading_cancelled = True
        
        # Cancel all pending metadata futures
        for future in self.metadata_futures:
            future.cancel()
        self.metadata_futures.clear()
        
        print("Metadata extraction cancelled")
    
    def is_processing(self) -> bool:
        """
        Check if metadata processing is currently running.
        
        Returns:
            True if processing is active, False otherwise
        """
        return len(self.metadata_futures) > 0 and not self.loading_cancelled
    
    def get_processing_status(self) -> tuple:
        """
        Get current processing status.
        
        Returns:
            Tuple of (completed_count, total_count, is_active)
        """
        if not self.metadata_futures:
            return 0, 0, False
        
        # Count completed futures
        completed = sum(1 for future in self.metadata_futures if future.done())
        total = len(self.metadata_futures)
        
        return completed, total, not self.loading_cancelled
    
    def cleanup(self) -> None:
        """Clean up resources."""
        # Cancel any ongoing extraction
        self.cancel_extraction()
        
        # Shutdown the executor
        self.metadata_executor.shutdown(wait=False)
