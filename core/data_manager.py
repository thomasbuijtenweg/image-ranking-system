"""
Data management module for the Image Ranking System.

This module handles all data persistence operations including:
- Saving and loading ranking data to/from JSON files
- Managing image statistics and voting history
- Providing data validation and migration capabilities
- Delegating weight and preference management to WeightManager

Now includes performance optimizations and metadata caching.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from collections import defaultdict

from config import Defaults
from core.weight_manager import WeightManager


class DataManager:
    """
    Handles all data persistence operations for the ranking system.
    
    This class manages the structure and persistence of all ranking data,
    including image statistics, voting history, and delegates weight/preference
    management to a specialized WeightManager.
    """
    
    def __init__(self):
        """Initialize the data manager with default values."""
        self.weight_manager = WeightManager()
        self.reset_data()
    
    def reset_data(self):
        """Reset all data to initial state."""
        # Core application state
        self.image_folder = ""
        self.vote_count = 0
        self.image_stats = {}
        
        # Metadata cache to avoid re-extraction (performance optimization)
        self.metadata_cache = {}  # filename -> {prompt, display_metadata, last_modified}
        
        # Reset weight manager to defaults
        self.weight_manager.reset_to_defaults()
        
        # Cached data for performance
        self._last_calculated_rankings = None
        self._last_calculation_vote_count = -1
    
    # Weight management methods - delegate to WeightManager
    def get_left_weights(self) -> Dict[str, float]:
        """Get the weights used for left image selection."""
        return self.weight_manager.get_left_weights()
    
    def get_right_weights(self) -> Dict[str, float]:
        """Get the weights used for right image selection."""
        return self.weight_manager.get_right_weights()
    
    def set_left_weights(self, weights: Dict[str, float]) -> None:
        """Set the weights used for left image selection."""
        self.weight_manager.set_left_weights(weights)
    
    def set_right_weights(self, weights: Dict[str, float]) -> None:
        """Set the weights used for right image selection."""
        self.weight_manager.set_right_weights(weights)
    
    def get_legacy_weights(self) -> Dict[str, float]:
        """Get the legacy weights property (for backward compatibility)."""
        return self.weight_manager.get_legacy_weights()
    
    def set_legacy_weights(self, weights: Dict[str, float]) -> None:
        """Set the legacy weights property (for backward compatibility)."""
        self.weight_manager.set_legacy_weights(weights)
    
    def get_left_priority_preferences(self) -> Dict[str, bool]:
        """Get the priority preferences used for left image selection."""
        return self.weight_manager.get_left_priority_preferences()
    
    def get_right_priority_preferences(self) -> Dict[str, bool]:
        """Get the priority preferences used for right image selection."""
        return self.weight_manager.get_right_priority_preferences()
    
    def set_left_priority_preferences(self, preferences: Dict[str, bool]) -> None:
        """Set the priority preferences used for left image selection."""
        self.weight_manager.set_left_priority_preferences(preferences)
    
    def set_right_priority_preferences(self, preferences: Dict[str, bool]) -> None:
        """Set the priority preferences used for right image selection."""
        self.weight_manager.set_right_priority_preferences(preferences)
    
    @property
    def tier_distribution_std(self) -> float:
        """Get the tier distribution standard deviation."""
        return self.weight_manager.get_tier_distribution_std()
    
    @tier_distribution_std.setter
    def tier_distribution_std(self, value: float) -> None:
        """Set the tier distribution standard deviation."""
        self.weight_manager.set_tier_distribution_std(value)
    
    def initialize_image_stats(self, image_filename: str) -> None:
        """
        Initialize statistics for a new image.
        
        Args:
            image_filename: Name of the image file
        """
        if image_filename not in self.image_stats:
            self.image_stats[image_filename] = {
                'votes': 0,
                'wins': 0,
                'losses': 0,
                'current_tier': 0,
                'tier_history': [0],
                'last_voted': -1,
                'matchup_history': [],
                'prompt': None,
                'display_metadata': None
            }
        else:
            # Ensure existing stats have all required fields (for backward compatibility)
            required_fields = {
                'votes': 0,
                'wins': 0,
                'losses': 0,
                'current_tier': 0,
                'tier_history': [0],
                'last_voted': -1,
                'matchup_history': [],
                'prompt': None,
                'display_metadata': None
            }
            
            for field, default_value in required_fields.items():
                if field not in self.image_stats[image_filename]:
                    self.image_stats[image_filename][field] = default_value
        
        # Try to restore metadata from cache (performance optimization)
        self.restore_metadata_from_cache(image_filename)
    
    def restore_metadata_from_cache(self, image_filename: str) -> None:
        """
        Restore metadata from cache if available and still valid.
        
        Args:
            image_filename: Name of the image file
        """
        if image_filename not in self.metadata_cache:
            return
        
        cached_data = self.metadata_cache[image_filename]
        
        # Check if cached metadata is still valid by comparing file modification time
        try:
            if self.image_folder:
                img_path = os.path.join(self.image_folder, image_filename)
                if os.path.exists(img_path):
                    current_mtime = os.path.getmtime(img_path)
                    cached_mtime = cached_data.get('last_modified', 0)
                    
                    # If file hasn't been modified since cache, use cached data
                    if abs(current_mtime - cached_mtime) < 1.0:  # 1 second tolerance
                        stats = self.image_stats[image_filename]
                        stats['prompt'] = cached_data.get('prompt')
                        stats['display_metadata'] = cached_data.get('display_metadata')
                        return
        except (OSError, KeyError):
            pass
        
        # Cache is invalid, remove it
        del self.metadata_cache[image_filename]
    
    def record_vote(self, winner: str, loser: str) -> None:
        """
        Record a vote between two images.
        
        Args:
            winner: Filename of the winning image
            loser: Filename of the losing image
        """
        # Increment global vote count
        self.vote_count += 1
        
        # Update winner statistics
        winner_stats = self.image_stats[winner]
        winner_stats['votes'] += 1
        winner_stats['wins'] += 1
        winner_stats['current_tier'] += 1
        winner_stats['tier_history'].append(winner_stats['current_tier'])
        winner_stats['last_voted'] = self.vote_count
        winner_stats['matchup_history'].append((loser, True, self.vote_count))
        
        # Update loser statistics
        loser_stats = self.image_stats[loser]
        loser_stats['votes'] += 1
        loser_stats['losses'] += 1
        loser_stats['current_tier'] -= 1
        loser_stats['tier_history'].append(loser_stats['current_tier'])
        loser_stats['last_voted'] = self.vote_count
        loser_stats['matchup_history'].append((winner, False, self.vote_count))
        
        # Invalidate cached rankings
        self._last_calculated_rankings = None
    
    def get_image_stats(self, image_filename: str) -> Dict[str, Any]:
        """
        Get statistics for a specific image.
        
        Args:
            image_filename: Name of the image file
            
        Returns:
            Dictionary containing all statistics for the image
        """
        return self.image_stats.get(image_filename, {})
    
    def set_image_metadata(self, image_filename: str, prompt: Optional[str] = None, 
                          display_metadata: Optional[str] = None) -> None:
        """
        Set metadata for an image and update cache.
        
        Args:
            image_filename: Name of the image file
            prompt: AI generation prompt (if available)
            display_metadata: Formatted metadata for display
        """
        if image_filename in self.image_stats:
            if prompt is not None:
                self.image_stats[image_filename]['prompt'] = prompt
            if display_metadata is not None:
                self.image_stats[image_filename]['display_metadata'] = display_metadata
            
            # Update metadata cache for performance
            self.update_metadata_cache(image_filename, prompt, display_metadata)
    
    def update_metadata_cache(self, image_filename: str, prompt: Optional[str] = None, 
                             display_metadata: Optional[str] = None) -> None:
        """
        Update the metadata cache for an image.
        
        Args:
            image_filename: Name of the image file
            prompt: AI generation prompt (if available)
            display_metadata: Formatted metadata for display
        """
        try:
            if self.image_folder:
                img_path = os.path.join(self.image_folder, image_filename)
                if os.path.exists(img_path):
                    current_mtime = os.path.getmtime(img_path)
                    
                    # Initialize cache entry if it doesn't exist
                    if image_filename not in self.metadata_cache:
                        self.metadata_cache[image_filename] = {}
                    
                    cache_entry = self.metadata_cache[image_filename]
                    
                    # Update cache with new data
                    if prompt is not None:
                        cache_entry['prompt'] = prompt
                    if display_metadata is not None:
                        cache_entry['display_metadata'] = display_metadata
                    
                    cache_entry['last_modified'] = current_mtime
                    
        except OSError:
            # If we can't get file info, don't cache
            pass
    
    def get_tier_distribution(self) -> Dict[int, int]:
        """
        Get the distribution of images across tiers.
        
        Returns:
            Dictionary mapping tier numbers to image counts
        """
        tier_counts = defaultdict(int)
        for stats in self.image_stats.values():
            tier_counts[stats['current_tier']] += 1
        return dict(tier_counts)
    
    def get_overall_statistics(self) -> Dict[str, Any]:
        """
        Calculate overall statistics for the ranking system.
        
        Returns:
            Dictionary containing overall statistics
        """
        if not self.image_stats:
            return {
                'total_images': 0,
                'total_votes': 0,
                'avg_votes_per_image': 0,
                'tier_distribution': {}
            }
        
        total_images = len(self.image_stats)
        total_votes = self.vote_count
        avg_votes_per_image = sum(s['votes'] for s in self.image_stats.values()) / total_images
        
        return {
            'total_images': total_images,
            'total_votes': total_votes,
            'avg_votes_per_image': avg_votes_per_image,
            'tier_distribution': self.get_tier_distribution()
        }
    
    def get_metadata_cache_stats(self) -> Dict[str, int]:
        """
        Get statistics about the metadata cache.
        
        Returns:
            Dictionary with cache statistics
        """
        total_images = len(self.image_stats)
        cached_prompts = sum(1 for cache_data in self.metadata_cache.values() 
                            if cache_data.get('prompt') is not None)
        cached_metadata = sum(1 for cache_data in self.metadata_cache.values() 
                             if cache_data.get('display_metadata') is not None)
        
        return {
            'total_images': total_images,
            'cached_prompts': cached_prompts,
            'cached_metadata': cached_metadata,
            'cache_hit_rate_prompts': cached_prompts / max(total_images, 1),
            'cache_hit_rate_metadata': cached_metadata / max(total_images, 1)
        }
    
    def cleanup_stale_cache_entries(self) -> int:
        """
        Remove cache entries for images that no longer exist.
        
        Returns:
            Number of entries removed
        """
        if not self.image_folder:
            return 0
        
        removed_count = 0
        stale_entries = []
        
        for image_filename in self.metadata_cache:
            img_path = os.path.join(self.image_folder, image_filename)
            if not os.path.exists(img_path):
                stale_entries.append(image_filename)
        
        for entry in stale_entries:
            del self.metadata_cache[entry]
            removed_count += 1
        
        return removed_count
    
    def save_to_file(self, filename: str) -> bool:
        """
        Save all ranking data to a JSON file with metadata cache.
        
        Args:
            filename: Path to the output file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                'image_folder': self.image_folder,
                'vote_count': self.vote_count,
                'image_stats': self.image_stats,
                'metadata_cache': self.metadata_cache,  # Include metadata cache
                'timestamp': datetime.now().isoformat(),
                'version': '1.5'  # Updated version for metadata caching
            }
            
            # Add weight manager data
            data.update(self.weight_manager.export_to_data())
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    def load_from_file(self, filename: str) -> Tuple[bool, str]:
        """
        Load ranking data from a JSON file with metadata cache support.
        
        Args:
            filename: Path to the input file
            
        Returns:
            Tuple of (success_bool, error_message)
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate required fields
            required_fields = ['image_folder', 'vote_count', 'image_stats']
            for field in required_fields:
                if field not in data:
                    return False, f"Missing required field: {field}"
            
            # Load core data
            self.image_folder = data['image_folder']
            self.vote_count = data['vote_count']
            self.image_stats = data['image_stats']
            
            # Load metadata cache if available (performance optimization)
            if 'metadata_cache' in data:
                self.metadata_cache = data['metadata_cache']
                print(f"Loaded metadata cache for {len(self.metadata_cache)} images")
            else:
                self.metadata_cache = {}
            
            # Load weight manager data
            self.weight_manager.load_from_data(data)
            
            # Validate and fix any missing fields in image stats
            for image_filename in self.image_stats:
                self.initialize_image_stats(image_filename)
            
            # Invalidate cached rankings
            self._last_calculated_rankings = None
            
            return True, ""
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {e}"
        except Exception as e:
            return False, f"Error loading data: {e}"
    
    def validate_data_integrity(self) -> Tuple[bool, str]:
        """
        Validate the integrity of loaded data.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if vote count matches recorded votes
            total_recorded_votes = sum(stats['votes'] for stats in self.image_stats.values())
            if total_recorded_votes != self.vote_count * 2:  # Each vote affects 2 images
                return False, f"Vote count mismatch: {total_recorded_votes} vs {self.vote_count * 2}"
            
            # Check if wins + losses = total votes for each image
            for image_name, stats in self.image_stats.items():
                if stats['wins'] + stats['losses'] != stats['votes']:
                    return False, f"Win/loss mismatch for {image_name}"
            
            # Check if tier history is consistent
            for image_name, stats in self.image_stats.items():
                if len(stats['tier_history']) != stats['votes'] + 1:  # +1 for initial tier
                    return False, f"Tier history length mismatch for {image_name}"
            
            # Validate weight manager data
            if not self.weight_manager.validate_weights(self.weight_manager.get_left_weights()):
                return False, "Invalid left weights"
            if not self.weight_manager.validate_weights(self.weight_manager.get_right_weights()):
                return False, "Invalid right weights"
            if not self.weight_manager.validate_preferences(self.weight_manager.get_left_priority_preferences()):
                return False, "Invalid left priority preferences"
            if not self.weight_manager.validate_preferences(self.weight_manager.get_right_priority_preferences()):
                return False, "Invalid right priority preferences"
            
            return True, ""
            
        except Exception as e:
            return False, f"Data validation error: {e}"
    
    def export_rankings_csv(self, filename: str) -> bool:
        """
        Export current rankings to a CSV file.
        
        Args:
            filename: Path to the output CSV file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            import csv
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'Image', 'Current Tier', 'Total Votes', 'Wins', 'Losses', 
                    'Win Rate', 'Tier Stability', 'Last Voted', 'Prompt'
                ])
                
                # Sort by current tier (descending)
                sorted_images = sorted(
                    self.image_stats.items(),
                    key=lambda x: x[1]['current_tier'],
                    reverse=True
                )
                
                for image_name, stats in sorted_images:
                    win_rate = stats['wins'] / stats['votes'] if stats['votes'] > 0 else 0
                    
                    # Calculate tier stability (standard deviation)
                    tier_history = stats['tier_history']
                    if len(tier_history) > 1:
                        import statistics
                        tier_stability = statistics.stdev(tier_history)
                    else:
                        tier_stability = 0.0
                    
                    writer.writerow([
                        image_name,
                        stats['current_tier'],
                        stats['votes'],
                        stats['wins'],
                        stats['losses'],
                        f"{win_rate:.1%}",
                        f"{tier_stability:.2f}",
                        stats['last_voted'],
                        stats.get('prompt', '')[:100] if stats.get('prompt') else ''
                    ])
            
            return True
            
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            return False