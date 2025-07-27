"""Enhanced Data Manager with intelligent tier bounds and image binning support."""

import os
from typing import Dict, Any, Optional, Tuple
from collections import defaultdict

from config import Defaults
from core.weight_manager import WeightManager
from core.tier_bounds_manager import TierBoundsManager
from core.data_persistence import DataPersistence
from core.algorithm_settings import AlgorithmSettings


class DataManager:
    """Handles data persistence and ranking statistics with intelligent tier bounds and binning."""
    
    def __init__(self):
        self.weight_manager = WeightManager()
        self.tier_bounds_manager = TierBoundsManager()
        self.data_persistence = DataPersistence()
        self.algorithm_settings = AlgorithmSettings()
        self.reset_data()
    
    def reset_data(self):
        """Reset all data to initial state."""
        self.image_folder = ""
        self.vote_count = 0
        self.image_stats = {}
        self.metadata_cache = {}
        self.binned_images = set()  # Track binned image filenames
        self.weight_manager.reset_to_defaults()
        self.tier_bounds_manager.reset_to_defaults()
        self.algorithm_settings.reset_to_defaults()
    
    def bin_image(self, image_name: str) -> bool:
        """
        Mark an image as binned and remove it from active ranking.
        
        Args:
            image_name: Name of the image to bin
            
        Returns:
            True if successfully binned, False if already binned
        """
        if image_name in self.binned_images:
            return False
        
        self.binned_images.add(image_name)
        print(f"Image '{image_name}' has been binned")
        return True
    
    def is_image_binned(self, image_name: str) -> bool:
        """Check if an image is binned."""
        return image_name in self.binned_images
    
    def get_active_images(self) -> list:
        """Get list of active (non-binned) image names."""
        return [img for img in self.image_stats.keys() if img not in self.binned_images]
    
    def get_binned_images(self) -> list:
        """Get list of binned image names."""
        return list(self.binned_images)
    
    def get_active_image_count(self) -> int:
        """Get count of active (non-binned) images."""
        return len(self.get_active_images())
    
    def get_binned_image_count(self) -> int:
        """Get count of binned images."""
        return len(self.binned_images)
    
    def record_vote(self, winner: str, loser: str) -> None:
        """Record a vote between two images with tier bounds checking."""
        self.vote_count += 1
        
        # Calculate target tiers
        winner_current_tier = self.image_stats[winner].get('current_tier', 0)
        loser_current_tier = self.image_stats[loser].get('current_tier', 0)
        
        winner_target_tier = winner_current_tier + 1
        loser_target_tier = loser_current_tier - 1
        
        # Check if moves are allowed
        winner_can_move, winner_reason = self.tier_bounds_manager.can_move_to_tier(
            winner, winner_target_tier, self.image_stats, self.algorithm_settings.tier_distribution_std)
        loser_can_move, loser_reason = self.tier_bounds_manager.can_move_to_tier(
            loser, loser_target_tier, self.image_stats, self.algorithm_settings.tier_distribution_std)
        
        # Update winner stats
        winner_stats = self.image_stats[winner]
        winner_stats['votes'] += 1
        winner_stats['wins'] += 1
        
        if winner_can_move:
            winner_stats['current_tier'] = winner_target_tier
        # If can't move, tier stays the same
        
        winner_stats['tier_history'].append(winner_stats['current_tier'])
        winner_stats['last_voted'] = self.vote_count
        winner_stats['matchup_history'].append((loser, True, self.vote_count))
        
        # Update loser stats
        loser_stats = self.image_stats[loser]
        loser_stats['votes'] += 1
        loser_stats['losses'] += 1
        
        if loser_can_move:
            loser_stats['current_tier'] = loser_target_tier
        # If can't move, tier stays the same
        
        loser_stats['tier_history'].append(loser_stats['current_tier'])
        loser_stats['last_voted'] = self.vote_count
        loser_stats['matchup_history'].append((winner, False, self.vote_count))
        
        # Log tier bound decisions if they affected the outcome
        if not winner_can_move:
            print(f"Winner {winner} hit tier bound: {winner_reason}")
        if not loser_can_move:
            print(f"Loser {loser} hit tier bound: {loser_reason}")
    
    def save_to_file(self, filename: str) -> bool:
        """Save all ranking data including binned images."""
        # Prepare core data
        core_data = {
            'image_folder': self.image_folder,
            'vote_count': self.vote_count,
            'image_stats': self.image_stats,
            'metadata_cache': self.metadata_cache,
            'binned_images': list(self.binned_images)  # Convert set to list for JSON
        }
        
        # Gather all settings
        weight_data = self.weight_manager.export_to_data()
        algorithm_settings = self.algorithm_settings.export_settings()
        tier_bounds_settings = self.tier_bounds_manager.export_settings()
        
        # Prepare complete save data
        save_data = self.data_persistence.prepare_save_data(
            core_data, weight_data, algorithm_settings, tier_bounds_settings)
        
        # Save to file
        return self.data_persistence.save_to_file(filename, save_data)
    
    def load_from_file(self, filename: str) -> Tuple[bool, str]:
        """Load ranking data including binned images."""
        # Load data from file
        success, data, error_msg = self.data_persistence.load_from_file(filename)
        if not success:
            return False, error_msg
        
        # Validate and fix data
        data = self.data_persistence.validate_and_fix_data(data)
        
        # Extract core data
        core_data = self.data_persistence.extract_core_data(data)
        self.image_folder = core_data['image_folder']
        self.vote_count = core_data['vote_count']
        self.image_stats = core_data['image_stats']
        self.metadata_cache = core_data['metadata_cache']
        self.binned_images = core_data['binned_images']  # This is already a set
        
        # Load other settings
        self.weight_manager.load_from_data(data)
        self.algorithm_settings.load_settings(data)
        self.tier_bounds_manager.load_settings(data)
        
        # Update existing images with strategic timing
        self._update_existing_images_with_strategic_timing()
        
        # Initialize all image stats
        for image_filename in self.image_stats:
            self.initialize_image_stats(image_filename)
        
        return True, ""
    
    def get_tier_distribution(self) -> Dict[int, int]:
        """Get the distribution of ACTIVE images across tiers."""
        tier_counts = defaultdict(int)
        for img_name, stats in self.image_stats.items():
            if img_name not in self.binned_images:  # Only active images
                tier_counts[stats['current_tier']] += 1
        return dict(tier_counts)
    
    def get_overall_statistics(self) -> Dict[str, Any]:
        """Calculate overall statistics with enhanced error handling and backward compatibility."""
        try:
            active_images = self.get_active_images()
            total_active_images = len(active_images)
            total_binned_images = len(self.binned_images)
            total_images = total_active_images + total_binned_images
            
            if not active_images:
                return {
                    'total_images': total_images,  # For backward compatibility
                    'total_active_images': 0,
                    'total_binned_images': total_binned_images,
                    'total_votes': self.vote_count,
                    'avg_votes_per_image': 0,  # For backward compatibility
                    'avg_votes_per_active_image': 0,
                    'tier_distribution': {},
                    'tier_bounds_info': self.get_tier_bounds_info()
                }
            
            total_votes = self.vote_count
            
            # Calculate average votes per active image
            try:
                total_active_votes = sum(
                    self.image_stats[img]['votes'] for img in active_images
                    if img in self.image_stats
                )
                avg_votes_per_active_image = total_active_votes / total_active_images
            except (KeyError, ZeroDivisionError, TypeError) as e:
                print(f"Error calculating average votes per active image: {e}")
                avg_votes_per_active_image = 0
            
            # Calculate average votes per total image (for backward compatibility)
            try:
                total_all_votes = sum(
                    self.image_stats[img]['votes'] for img in self.image_stats
                    if img in self.image_stats
                )
                avg_votes_per_image = total_all_votes / total_images if total_images > 0 else 0
            except (KeyError, ZeroDivisionError, TypeError) as e:
                print(f"Error calculating average votes per total image: {e}")
                avg_votes_per_image = 0
            
            return {
                'total_images': total_images,  # For backward compatibility
                'total_active_images': total_active_images,
                'total_binned_images': total_binned_images,
                'total_votes': total_votes,
                'avg_votes_per_image': avg_votes_per_image,  # For backward compatibility
                'avg_votes_per_active_image': avg_votes_per_active_image,
                'tier_distribution': self.get_tier_distribution(),
                'tier_bounds_info': self.get_tier_bounds_info()
            }
            
        except Exception as e:
            print(f"Error in get_overall_statistics: {e}")
            # Return safe defaults
            return {
                'total_images': len(self.image_stats),
                'total_active_images': 0,
                'total_binned_images': 0,
                'total_votes': self.vote_count,
                'avg_votes_per_image': 0,
                'avg_votes_per_active_image': 0,
                'tier_distribution': {},
                'tier_bounds_info': {}
            }
    
    def get_tier_bounds_info(self) -> Dict[str, Any]:
        """Get information about current tier bounds."""
        return self.tier_bounds_manager.get_bounds_info(self.algorithm_settings.tier_distribution_std, self.image_stats)
    
    # Weight manager delegations
    def get_left_weights(self) -> Dict[str, float]:
        return self.weight_manager.get_left_weights()
    
    def get_right_weights(self) -> Dict[str, float]:
        return self.weight_manager.get_right_weights()
    
    def set_left_weights(self, weights: Dict[str, float]) -> None:
        self.weight_manager.set_left_weights(weights)
    
    def set_right_weights(self, weights: Dict[str, float]) -> None:
        self.weight_manager.set_right_weights(weights)
    
    def get_left_priority_preferences(self) -> Dict[str, bool]:
        return self.weight_manager.get_left_priority_preferences()
    
    def get_right_priority_preferences(self) -> Dict[str, bool]:
        return self.weight_manager.get_right_priority_preferences()
    
    def set_left_priority_preferences(self, preferences: Dict[str, bool]) -> None:
        self.weight_manager.set_left_priority_preferences(preferences)
    
    def set_right_priority_preferences(self, preferences: Dict[str, bool]) -> None:
        self.weight_manager.set_right_priority_preferences(preferences)
    
    def initialize_image_stats(self, image_filename: str) -> None:
        """Initialize stats for a new image with strategic placement."""
        if image_filename not in self.image_stats:
            strategic_last_voted = self._calculate_strategic_last_voted(image_filename)
            
            self.image_stats[image_filename] = {
                'votes': 0,
                'wins': 0,
                'losses': 0,
                'current_tier': 0,
                'tier_history': [0],
                'last_voted': strategic_last_voted,
                'matchup_history': [],
                'prompt': None,
                'display_metadata': None
            }
        else:
            # Ensure required fields exist
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
        
        self.restore_metadata_from_cache(image_filename)
    
    def _calculate_strategic_last_voted(self, image_filename: str) -> int:
        """Calculate strategic last_voted value for a new image."""
        if not self.image_stats or image_filename in self.image_stats:
            return 0
        
        highest_last_voted = -1
        for stats in self.image_stats.values():
            last_voted = stats.get('last_voted', -1)
            if last_voted > highest_last_voted:
                highest_last_voted = last_voted
        
        if highest_last_voted == -1:
            return 0
        elif highest_last_voted == 0:
            return 0
        else:
            return 1 + (highest_last_voted // 2)
    
    def get_image_stats(self, image_filename: str) -> Dict[str, Any]:
        """Get statistics for a specific image."""
        return self.image_stats.get(image_filename, {})
    
    def _update_existing_images_with_strategic_timing(self) -> None:
        """Update existing images that have never been voted on to use strategic timing."""
        if not self.image_stats:
            return
        
        highest_last_voted = -1
        for stats in self.image_stats.values():
            last_voted = stats.get('last_voted', -1)
            if last_voted > highest_last_voted:
                highest_last_voted = last_voted
        
        if highest_last_voted == -1:
            return
        
        strategic_value = 0 if highest_last_voted == 0 else 1 + (highest_last_voted // 2)
        
        updated_count = 0
        for image_filename, stats in self.image_stats.items():
            if stats.get('last_voted', -1) == -1:
                stats['last_voted'] = strategic_value
                updated_count += 1
        
        if updated_count > 0:
            print(f"Updated {updated_count} never-voted images with strategic timing")
    
    def set_image_metadata(self, image_filename: str, prompt: Optional[str] = None, 
                          display_metadata: Optional[str] = None) -> None:
        """Set metadata for an image and update cache."""
        if image_filename in self.image_stats:
            if prompt is not None:
                self.image_stats[image_filename]['prompt'] = prompt
            if display_metadata is not None:
                self.image_stats[image_filename]['display_metadata'] = display_metadata
            
            self.update_metadata_cache(image_filename, prompt, display_metadata)
    
    def update_metadata_cache(self, image_filename: str, prompt: Optional[str] = None, 
                             display_metadata: Optional[str] = None) -> None:
        """Update the metadata cache for an image."""
        try:
            if self.image_folder:
                img_path = os.path.join(self.image_folder, image_filename)
                if os.path.exists(img_path):
                    current_mtime = os.path.getmtime(img_path)
                    
                    if image_filename not in self.metadata_cache:
                        self.metadata_cache[image_filename] = {}
                    
                    cache_entry = self.metadata_cache[image_filename]
                    
                    if prompt is not None:
                        cache_entry['prompt'] = prompt
                    if display_metadata is not None:
                        cache_entry['display_metadata'] = display_metadata
                    
                    cache_entry['last_modified'] = current_mtime
        except OSError:
            pass
    
    def restore_metadata_from_cache(self, image_filename: str) -> None:
        """Restore metadata from cache if available and valid."""
        if image_filename not in self.metadata_cache:
            return
        
        cached_data = self.metadata_cache[image_filename]
        
        try:
            if self.image_folder:
                img_path = os.path.join(self.image_folder, image_filename)
                if os.path.exists(img_path):
                    current_mtime = os.path.getmtime(img_path)
                    cached_mtime = cached_data.get('last_modified', 0)
                    
                    if abs(current_mtime - cached_mtime) < 1.0:
                        stats = self.image_stats[image_filename]
                        stats['prompt'] = cached_data.get('prompt')
                        stats['display_metadata'] = cached_data.get('display_metadata')
                        return
        except (OSError, KeyError):
            pass
        
        del self.metadata_cache[image_filename]
