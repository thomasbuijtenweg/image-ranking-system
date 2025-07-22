"""
Binning controller for the Image Ranking System.

This module handles the binning functionality where images can be moved
to a special "Bin" folder and marked as low-tier, high-confidence to
exclude them from future voting while preserving their statistics.
"""

import os
import shutil
import tkinter as tk
from tkinter import messagebox
from typing import Set, Optional, Tuple

from config import Colors


class BinningController:
    """
    Handles image binning functionality.
    
    Binning an image means:
    - Moving it to a "Bin" subfolder
    - Setting it to a very low tier (-999)
    - Setting it to high confidence (1.0) to prevent selection
    - Excluding it from future voting pairs
    - Preserving its statistics for historical purposes
    """
    
    def __init__(self, data_manager, image_processor):
        """
        Initialize the binning controller.
        
        Args:
            data_manager: DataManager instance
            image_processor: ImageProcessor instance
        """
        self.data_manager = data_manager
        self.image_processor = image_processor
        
        # Callbacks
        self.on_image_binned_callback = None
        self.on_both_binned_callback = None
        
        # Initialize binned images tracking in data manager
        if not hasattr(self.data_manager, 'binned_images'):
            self.data_manager.binned_images = set()
    
    def set_image_binned_callback(self, callback):
        """Set callback for when a single image is binned."""
        self.on_image_binned_callback = callback
    
    def set_both_binned_callback(self, callback):
        """Set callback for when both images are binned."""
        self.on_both_binned_callback = callback
    
    def bin_image(self, image_filename: str) -> bool:
        """
        Bin a single image.
        
        Args:
            image_filename: Name of the image file to bin (original filename, not Bin/ prefixed)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure we're working with the original filename (strip any Bin/ prefix)
            original_filename = image_filename
            if image_filename.startswith('Bin/'):
                original_filename = image_filename[4:]  # Remove 'Bin/' prefix
            
            # Check if image is already binned
            if self.is_image_binned(original_filename):
                print(f"Image {original_filename} is already binned")
                return True
            
            # Move the physical file
            if not self._move_image_to_bin(original_filename):
                return False
            
            # Update image statistics (use original filename as key)
            self._update_binned_image_stats(original_filename)
            
            # Add to binned set (store original filename, not Bin/ prefixed)
            self.data_manager.binned_images.add(original_filename)
            
            print(f"Successfully binned image: {original_filename}")
            
            # Trigger callback
            if self.on_image_binned_callback:
                self.on_image_binned_callback(original_filename)
            
            return True
            
        except Exception as e:
            print(f"Error binning image {image_filename}: {e}")
            messagebox.showerror("Binning Error", f"Failed to bin {image_filename}: {str(e)}")
            return False
    
    def bin_both_images(self, image1: str, image2: str) -> Tuple[bool, bool]:
        """
        Bin both images in a pair.
        
        Args:
            image1: First image filename (original, not Bin/ prefixed)
            image2: Second image filename (original, not Bin/ prefixed)
            
        Returns:
            Tuple of (success1, success2)
        """
        # Ensure we're working with original filenames
        original_image1 = image1[4:] if image1.startswith('Bin/') else image1
        original_image2 = image2[4:] if image2.startswith('Bin/') else image2
        
        success1 = self.bin_image(original_image1)
        success2 = self.bin_image(original_image2)
        
        if success1 and success2:
            print(f"Successfully binned both images: {original_image1}, {original_image2}")
            
            # Trigger both binned callback
            if self.on_both_binned_callback:
                self.on_both_binned_callback(original_image1, original_image2)
        elif success1 or success2:
            binned = original_image1 if success1 else original_image2
            failed = original_image2 if success1 else original_image1
            messagebox.showwarning("Partial Success", 
                                 f"Binned {binned} successfully, but failed to bin {failed}")
        else:
            messagebox.showerror("Binning Failed", 
                               f"Failed to bin both images: {original_image1}, {original_image2}")
        
        return success1, success2
    
    def is_image_binned(self, image_filename: str) -> bool:
        """
        Check if an image is binned.
        
        Args:
            image_filename: Name of the image file
            
        Returns:
            True if the image is binned, False otherwise
        """
        return image_filename in getattr(self.data_manager, 'binned_images', set())
    
    def get_binned_images(self) -> Set[str]:
        """
        Get the set of all binned images.
        
        Returns:
            Set of binned image filenames
        """
        return getattr(self.data_manager, 'binned_images', set()).copy()
    
    def unbin_image(self, image_filename: str) -> bool:
        """
        Unbin an image (move it back from the bin).
        
        Args:
            image_filename: Name of the image file to unbin
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.is_image_binned(image_filename):
                print(f"Image {image_filename} is not binned")
                return True
            
            # Move file back from bin
            if not self._move_image_from_bin(image_filename):
                return False
            
            # Remove from binned set
            self.data_manager.binned_images.discard(image_filename)
            
            # Reset image statistics to normal values
            self._reset_binned_image_stats(image_filename)
            
            print(f"Successfully unbinned image: {image_filename}")
            return True
            
        except Exception as e:
            print(f"Error unbinning image {image_filename}: {e}")
            messagebox.showerror("Unbinning Error", f"Failed to unbin {image_filename}: {str(e)}")
            return False
    
    def get_bin_folder_path(self) -> str:
        """
        Get the path to the bin folder.
        
        Returns:
            Path to the bin folder
        """
        if not self.data_manager.image_folder:
            return ""
        return os.path.join(self.data_manager.image_folder, "Bin")
    
    def create_bin_folder(self) -> bool:
        """
        Create the bin folder if it doesn't exist.
        
        Returns:
            True if folder exists or was created successfully
        """
        try:
            bin_path = self.get_bin_folder_path()
            if not bin_path:
                return False
            
            if not os.path.exists(bin_path):
                os.makedirs(bin_path)
                print(f"Created bin folder: {bin_path}")
            
            return True
            
        except Exception as e:
            print(f"Error creating bin folder: {e}")
            return False
    
    def _move_image_to_bin(self, image_filename: str) -> bool:
        """Move an image file to the bin folder."""
        try:
            if not self.data_manager.image_folder:
                raise ValueError("No image folder selected")
            
            # Ensure we're working with original filename (no Bin/ prefix)
            original_filename = image_filename[4:] if image_filename.startswith('Bin/') else image_filename
            
            # Create bin folder if needed
            if not self.create_bin_folder():
                raise RuntimeError("Failed to create bin folder")
            
            source_path = os.path.join(self.data_manager.image_folder, original_filename)
            bin_path = self.get_bin_folder_path()
            dest_path = os.path.join(bin_path, os.path.basename(original_filename))
            
            # Check if source exists
            if not os.path.exists(source_path):
                raise FileNotFoundError(f"Source image not found: {source_path}")
            
            # Handle filename conflicts
            if os.path.exists(dest_path):
                base, ext = os.path.splitext(os.path.basename(original_filename))
                counter = 1
                while os.path.exists(dest_path):
                    new_name = f"{base}_binned_{counter}{ext}"
                    dest_path = os.path.join(bin_path, new_name)
                    counter += 1
                
                print(f"Renamed to avoid conflict: {os.path.basename(dest_path)}")
            
            # Move the file
            shutil.move(source_path, dest_path)
            print(f"Moved {original_filename} to bin folder")
            return True
            
        except Exception as e:
            print(f"Error moving image to bin: {e}")
            return False
    
    def _move_image_from_bin(self, image_filename: str) -> bool:
        """Move an image file back from the bin folder."""
        try:
            if not self.data_manager.image_folder:
                raise ValueError("No image folder selected")
            
            bin_path = self.get_bin_folder_path()
            source_path = os.path.join(bin_path, os.path.basename(image_filename))
            dest_path = os.path.join(self.data_manager.image_folder, image_filename)
            
            # Check if source exists
            if not os.path.exists(source_path):
                raise FileNotFoundError(f"Binned image not found: {source_path}")
            
            # Handle filename conflicts
            if os.path.exists(dest_path):
                base, ext = os.path.splitext(image_filename)
                counter = 1
                while os.path.exists(dest_path):
                    new_name = f"{base}_unbinned_{counter}{ext}"
                    dest_path = os.path.join(self.data_manager.image_folder, new_name)
                    counter += 1
                
                print(f"Renamed to avoid conflict: {os.path.basename(dest_path)}")
            
            # Move the file back
            shutil.move(source_path, dest_path)
            print(f"Moved {image_filename} back from bin folder")
            return True
            
        except Exception as e:
            print(f"Error moving image from bin: {e}")
            return False
    
    def _update_binned_image_stats(self, image_filename: str):
        """Update statistics for a binned image."""
        if image_filename not in self.data_manager.image_stats:
            return
        
        stats = self.data_manager.image_stats[image_filename]
        
        # Set to very low tier to indicate it's binned
        stats['current_tier'] = -999
        stats['tier_history'].append(-999)
        
        # Mark as binned in the stats for easy identification
        stats['binned'] = True
        stats['binned_vote_count'] = self.data_manager.vote_count
        
        # Add a note about binning
        if 'notes' not in stats:
            stats['notes'] = []
        stats['notes'].append(f"Binned at vote {self.data_manager.vote_count}")
        
        print(f"Updated stats for binned image: {image_filename}")
    
    def _reset_binned_image_stats(self, image_filename: str):
        """Reset statistics for an unbinned image."""
        if image_filename not in self.data_manager.image_stats:
            return
        
        stats = self.data_manager.image_stats[image_filename]
        
        # Reset tier to 0 (could be made configurable)
        stats['current_tier'] = 0
        stats['tier_history'].append(0)
        
        # Remove binned flag
        stats.pop('binned', None)
        stats.pop('binned_vote_count', None)
        
        # Add unbinning note
        if 'notes' not in stats:
            stats['notes'] = []
        stats['notes'].append(f"Unbinned at vote {self.data_manager.vote_count}")
        
        print(f"Reset stats for unbinned image: {image_filename}")
    
    def get_bin_statistics(self) -> dict:
        """
        Get statistics about binned images.
        
        Returns:
            Dictionary with bin statistics
        """
        binned_images = self.get_binned_images()
        
        if not binned_images:
            return {
                'total_binned': 0,
                'bin_folder_exists': os.path.exists(self.get_bin_folder_path()),
                'bin_folder_path': self.get_bin_folder_path()
            }
        
        # Calculate statistics
        total_votes_before_binning = 0
        avg_tier_before_binning = 0
        binned_at_votes = []
        
        for img in binned_images:
            stats = self.data_manager.get_image_stats(img)
            total_votes_before_binning += stats.get('votes', 0)
            
            # Try to get the tier before binning (second to last in history)
            tier_history = stats.get('tier_history', [0])
            if len(tier_history) >= 2:
                avg_tier_before_binning += tier_history[-2]  # Last is -999, second to last is actual
            
            binned_vote_count = stats.get('binned_vote_count')
            if binned_vote_count:
                binned_at_votes.append(binned_vote_count)
        
        avg_votes_before_binning = total_votes_before_binning / len(binned_images) if binned_images else 0
        avg_tier_before_binning = avg_tier_before_binning / len(binned_images) if binned_images else 0
        
        return {
            'total_binned': len(binned_images),
            'bin_folder_exists': os.path.exists(self.get_bin_folder_path()),
            'bin_folder_path': self.get_bin_folder_path(),
            'avg_votes_before_binning': avg_votes_before_binning,
            'avg_tier_before_binning': avg_tier_before_binning,
            'binned_at_votes': binned_at_votes,
            'binned_images': list(binned_images)
        }
    
    def cleanup(self):
        """Clean up resources."""
        self.on_image_binned_callback = None
        self.on_both_binned_callback = None
