"""
Folder manager for the Image Ranking System.

This module handles folder selection, image loading,
and coordination of the loading process.
"""

import os
import time
from tkinter import filedialog, messagebox


class FolderManager:
    """
    Handles folder selection and image loading operations.
    
    This class manages the process of selecting folders,
    scanning for images, and coordinating the loading process.
    """
    
    def __init__(self, data_manager, image_processor, metadata_processor, progress_tracker):
        """
        Initialize the folder manager.
        
        Args:
            data_manager: DataManager instance
            image_processor: ImageProcessor instance
            metadata_processor: MetadataProcessor instance
            progress_tracker: ProgressTracker instance
        """
        self.data_manager = data_manager
        self.image_processor = image_processor
        self.metadata_processor = metadata_processor
        self.progress_tracker = progress_tracker
        
        # UI references
        self.folder_label = None
        self.status_bar = None
        
        # Callbacks
        self.on_load_complete_callback = None
        self.on_progress_callback = None
        
        # Setup metadata processor callbacks
        self.metadata_processor.set_progress_callback(self._on_metadata_progress)
        self.metadata_processor.set_complete_callback(self._on_metadata_complete)
        
        # Setup progress tracker cancel callback
        self.progress_tracker.set_cancel_callback(self._on_cancel_loading)
    
    def set_ui_references(self, folder_label, status_bar) -> None:
        """
        Set references to UI elements.
        
        Args:
            folder_label: Label showing current folder
            status_bar: Status bar for messages
        """
        self.folder_label = folder_label
        self.status_bar = status_bar
    
    def set_load_complete_callback(self, callback) -> None:
        """
        Set callback for when loading is complete.
        
        Args:
            callback: Function to call when loading finishes
        """
        self.on_load_complete_callback = callback
    
    def set_progress_callback(self, callback) -> None:
        """
        Set callback for progress updates.
        
        Args:
            callback: Function to call with progress updates
        """
        self.on_progress_callback = callback
    
    def select_folder(self) -> bool:
        """
        Handle folder selection for image loading.
        
        Returns:
            True if folder was selected and loading started, False otherwise
        """
        folder = filedialog.askdirectory(title="Select folder containing images (includes subfolders)")
        if folder:
            self.data_manager.image_folder = folder
            self.load_images()
            return True
        return False
    
    def load_images(self) -> None:
        """Load images from the selected folder with optimized performance."""
        if not self.data_manager.image_folder:
            return
        
        # Quick file scan first (fast)
        start_time = time.time()
        images = self.image_processor.get_image_files(self.data_manager.image_folder)
        scan_time = time.time() - start_time
        
        if not images:
            messagebox.showerror("Error", "No images found in selected folder or its subfolders")
            return
        
        print(f"File scan completed in {scan_time:.2f}s for {len(images)} images")
        
        # Update folder label immediately
        folder_name = os.path.basename(self.data_manager.image_folder)
        if self.folder_label:
            self.folder_label.config(text=f"Folder: {folder_name} ({len(images)} images including subfolders)")
        
        # Show progress window for large collections
        if len(images) > 100:
            self.progress_tracker.show_progress_window("Loading Images", len(images))
        
        # Initialize basic stats for all images (fast - no metadata extraction)
        self._initialize_image_stats(images)
        
        # Close progress window
        self.progress_tracker.close_progress_window()
        
        # Start background metadata extraction
        self.metadata_processor.start_background_extraction(images)
        
        # Update status
        if self.status_bar:
            self.status_bar.config(text=f"Loaded {len(images)} images. Metadata extraction running in background. Ready to vote!")
        
        # Call completion callback
        if self.on_load_complete_callback:
            self.on_load_complete_callback(images)
    
    def _initialize_image_stats(self, images: list) -> None:
        """
        Initialize basic statistics for all images.
        
        Args:
            images: List of image filenames
        """
        processed_count = 0
        for img in images:
            self.data_manager.initialize_image_stats(img)
            processed_count += 1
            
            # Update progress for every 100 images or at the end
            if processed_count % 100 == 0 or processed_count == len(images):
                self.progress_tracker.update_progress(
                    processed_count, 
                    len(images), 
                    f"Initializing: {processed_count}/{len(images)}"
                )
                
                if self.on_progress_callback:
                    self.on_progress_callback(processed_count, len(images))
    
    def _on_metadata_progress(self, completed: int, total: int, message: str) -> None:
        """Handle metadata extraction progress updates."""
        if self.status_bar:
            self.status_bar.config(text=message)
        
        if self.on_progress_callback:
            self.on_progress_callback(completed, total)
    
    def _on_metadata_complete(self, total_processed: int) -> None:
        """Handle metadata extraction completion."""
        if self.status_bar:
            final_text = f"Metadata extraction complete for {total_processed} images. Ready to vote!"
            self.status_bar.config(text=final_text)
        
        print(f"Background metadata extraction completed for {total_processed} images")
    
    def _on_cancel_loading(self) -> None:
        """Handle loading cancellation."""
        # Cancel metadata extraction
        self.metadata_processor.cancel_extraction()
        
        # Update status
        if self.status_bar:
            self.status_bar.config(text="Loading cancelled")
        
        print("Image loading cancelled")
    
    def load_from_file(self, filename: str) -> bool:
        """
        Load ranking data from file and reload images.
        
        Args:
            filename: Path to the data file
            
        Returns:
            True if successful, False otherwise
        """
        success, error_msg = self.data_manager.load_from_file(filename)
        if success:
            # Reload images from folder
            if self.data_manager.image_folder:
                self.load_images()
            
            # Check if separate weights were loaded
            left_weights = self.data_manager.get_left_weights()
            right_weights = self.data_manager.get_right_weights()
            weights_message = ""
            if left_weights != right_weights:
                weights_message = "\n\nLoaded separate left and right selection weights."
            else:
                weights_message = "\n\nUsing same weights for both left and right selection."
            
            messagebox.showinfo("Success", f"Data loaded from {filename}{weights_message}")
            return True
        else:
            messagebox.showerror("Error", f"Could not load data: {error_msg}")
            return False
    
    def get_current_folder(self) -> str:
        """
        Get the currently selected folder.
        
        Returns:
            Current folder path
        """
        return self.data_manager.image_folder
    
    def is_folder_selected(self) -> bool:
        """
        Check if a folder is currently selected.
        
        Returns:
            True if folder is selected, False otherwise
        """
        return bool(self.data_manager.image_folder)
    
    def get_image_count(self) -> int:
        """
        Get the number of images in the current folder.
        
        Returns:
            Number of images
        """
        if not self.data_manager.image_folder:
            return 0
        
        images = self.image_processor.get_image_files(self.data_manager.image_folder)
        return len(images)
    
    def cleanup(self) -> None:
        """Clean up resources."""
        # Cancel any ongoing operations
        self.metadata_processor.cancel_extraction()
        self.progress_tracker.close_progress_window()
