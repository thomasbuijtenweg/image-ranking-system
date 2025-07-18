"""Folder manager for the Image Ranking System."""

import os
import time
from tkinter import filedialog, messagebox


class FolderManager:
    """Handles folder selection and image loading operations."""
    
    def __init__(self, data_manager, image_processor, metadata_processor, progress_tracker):
        self.data_manager = data_manager
        self.image_processor = image_processor
        self.metadata_processor = metadata_processor
        self.progress_tracker = progress_tracker
        
        self.folder_label = None
        self.status_bar = None
        
        self.on_load_complete_callback = None
        self.on_progress_callback = None
        
        self.metadata_processor.set_progress_callback(self._on_metadata_progress)
        self.metadata_processor.set_complete_callback(self._on_metadata_complete)
        
        self.progress_tracker.set_cancel_callback(self._on_cancel_loading)
    
    def set_ui_references(self, folder_label, status_bar) -> None:
        """Set references to UI elements."""
        self.folder_label = folder_label
        self.status_bar = status_bar
    
    def set_load_complete_callback(self, callback) -> None:
        """Set callback for when loading is complete."""
        self.on_load_complete_callback = callback
    
    def set_progress_callback(self, callback) -> None:
        """Set callback for progress updates."""
        self.on_progress_callback = callback
    
    def select_folder(self) -> bool:
        """Handle folder selection for image loading."""
        folder = filedialog.askdirectory(title="Select folder containing images (includes subfolders)")
        if folder:
            self.data_manager.image_folder = folder
            self.load_images()
            return True
        return False
    
    def load_images(self) -> None:
        """Load images from the selected folder."""
        if not self.data_manager.image_folder:
            return
        
        start_time = time.time()
        images = self.image_processor.get_image_files(self.data_manager.image_folder)
        scan_time = time.time() - start_time
        
        if not images:
            messagebox.showerror("Error", "No images found in selected folder or its subfolders")
            return
        
        print(f"File scan completed in {scan_time:.2f}s for {len(images)} images")
        
        folder_name = os.path.basename(self.data_manager.image_folder)
        if self.folder_label:
            self.folder_label.config(text=f"Folder: {folder_name} ({len(images)} images including subfolders)")
        
        if len(images) > 100:
            self.progress_tracker.show_progress_window("Loading Images", len(images))
        
        self._initialize_image_stats(images)
        
        self.progress_tracker.close_progress_window()
        
        self.metadata_processor.start_background_extraction(images)
        
        if self.status_bar:
            self.status_bar.config(text=f"Loaded {len(images)} images. All images initialized at tier 0 with strategic vote timing. Metadata extraction running in background. Ready to vote!")
        
        if self.on_load_complete_callback:
            self.on_load_complete_callback(images)
    
    def _initialize_image_stats(self, images: list) -> None:
        """Initialize statistics for all images with strategic placement."""
        processed_count = 0
        for img in images:
            # All images are initialized at tier 0 with 0 votes and strategic last_voted timing
            self.data_manager.initialize_image_stats(img)
            processed_count += 1
            
            if processed_count % 100 == 0 or processed_count == len(images):
                self.progress_tracker.update_progress(
                    processed_count, 
                    len(images), 
                    f"Initializing: {processed_count}/{len(images)} (tier 0, strategic vote timing)"
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
        self.metadata_processor.cancel_extraction()
        
        if self.status_bar:
            self.status_bar.config(text="Loading cancelled")
        
        print("Image loading cancelled")
    
    def load_from_file(self, filename: str) -> bool:
        """Load ranking data from file and reload images."""
        success, error_msg = self.data_manager.load_from_file(filename)
        if success:
            if self.data_manager.image_folder:
                self.load_images()
            
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
        """Get the currently selected folder."""
        return self.data_manager.image_folder
    
    def is_folder_selected(self) -> bool:
        """Check if a folder is currently selected."""
        return bool(self.data_manager.image_folder)
    
    def get_image_count(self) -> int:
        """Get the number of images in the current folder."""
        if not self.data_manager.image_folder:
            return 0
        
        images = self.image_processor.get_image_files(self.data_manager.image_folder)
        return len(images)
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self.metadata_processor.cancel_extraction()
        self.progress_tracker.close_progress_window()
