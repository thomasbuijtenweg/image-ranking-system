"""Folder manager for the Image Ranking System with binning support - FIXED."""

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
        
        # Reference to voting controller for initialization
        self.voting_controller = None
        
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
    
    def set_voting_controller_reference(self, voting_controller) -> None:
        """Set reference to voting controller for initialization."""
        self.voting_controller = voting_controller
        print(f"FolderManager: Voting controller reference set: {voting_controller is not None}")
    
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
        print(f"FolderManager: load_images called, folder: {self.data_manager.image_folder}")
        print(f"FolderManager: voting_controller is None: {self.voting_controller is None}")
        
        if not self.data_manager.image_folder:
            print("FolderManager: No image folder set")
            return
        
        start_time = time.time()
        images = self.image_processor.get_image_files(self.data_manager.image_folder, exclude_bin_folder=True)
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
        
        # FIXED: Initialize image binner for voting controller with better error handling
        if self.voting_controller is not None:
            try:
                print(f"FolderManager: Initializing image binner for folder: {self.data_manager.image_folder}")
                self.voting_controller.set_image_folder(self.data_manager.image_folder)
                print("FolderManager: Image binner initialized successfully")
            except Exception as e:
                print(f"FolderManager: Error initializing image binner: {e}")
                if self.status_bar:
                    self.status_bar.config(text=f"Warning: Image binner initialization failed: {e}")
        else:
            print("FolderManager: WARNING - Voting controller reference not set, cannot initialize image binner")
            if self.status_bar:
                self.status_bar.config(text="Warning: Voting controller not available - binning disabled")
        
        if self.status_bar:
            active_count = self.data_manager.get_active_image_count()
            binned_count = self.data_manager.get_binned_image_count()
            binner_status = "with binning" if self.voting_controller and hasattr(self.voting_controller, 'image_binner') and self.voting_controller.image_binner else "without binning"
            self.status_bar.config(
                text=f"Loaded {len(images)} images. Active: {active_count}, Binned: {binned_count}. Ready to vote {binner_status}! (↓ to bin loser)"
            )
        
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
            active_count = self.data_manager.get_active_image_count()
            binned_count = self.data_manager.get_binned_image_count()
            binner_status = "with binning" if self.voting_controller and hasattr(self.voting_controller, 'image_binner') and self.voting_controller.image_binner else "without binning"
            final_text = f"Metadata extraction complete for {total_processed} images. Active: {active_count}, Binned: {binned_count}. Ready to vote {binner_status}! (↓ to bin loser)"
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
        print(f"FolderManager: Loading from file: {filename}")
        success, error_msg = self.data_manager.load_from_file(filename)
        if success:
            print(f"FolderManager: Data loaded successfully, image_folder: {self.data_manager.image_folder}")
            
            # FIXED: Always reload images after loading save data to ensure proper initialization
            if self.data_manager.image_folder:
                print("FolderManager: Reloading images from saved folder")
                self.load_images()
            else:
                print("FolderManager: No image folder in save data")
            
            left_weights = self.data_manager.get_left_weights()
            right_weights = self.data_manager.get_right_weights()
            weights_message = ""
            if left_weights != right_weights:
                weights_message = "\n\nLoaded separate left and right selection weights."
            else:
                weights_message = "\n\nUsing same weights for both left and right selection."
            
            # Include binning information in success message
            active_count = self.data_manager.get_active_image_count()
            binned_count = self.data_manager.get_binned_image_count()
            binning_message = f"\n\nLoaded {active_count} active images and {binned_count} binned images."
            
            # FIXED: Add binner status to success message
            binner_status = "\n\nBinning: Available" if (self.voting_controller and 
                                                        hasattr(self.voting_controller, 'image_binner') and 
                                                        self.voting_controller.image_binner) else "\n\nBinning: Not available"
            
            messagebox.showinfo("Success", f"Data loaded from {filename}{weights_message}{binning_message}{binner_status}")
            return True
        else:
            print(f"FolderManager: Failed to load data: {error_msg}")
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
        
        images = self.image_processor.get_image_files(self.data_manager.image_folder, exclude_bin_folder=True)
        return len(images)
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self.metadata_processor.cancel_extraction()
        self.progress_tracker.close_progress_window()