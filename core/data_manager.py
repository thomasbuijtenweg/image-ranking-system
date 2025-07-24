"""Enhanced Data Manager with intelligent tier bounds."""

import os
from typing import Dict, Any, Optional, Tuple
from collections import defaultdict

from config import Defaults
from core.weight_manager import WeightManager
from core.tier_bounds_manager import TierBoundsManager
from core.data_persistence import DataPersistence
from core.algorithm_settings import AlgorithmSettings


class DataManager:
    """Handles data persistence and ranking statistics with intelligent tier bounds."""
    
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
        self.weight_manager.reset_to_defaults()
        self.tier_bounds_manager.reset_to_defaults()
        self.algorithm_settings.reset_to_defaults()
        self._last_calculated_rankings = None
        self._last_calculation_vote_count = -1
    
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
            winner, winner_target_tier, self.image_stats, self.tier_distribution_std)
        loser_can_move, loser_reason = self.tier_bounds_manager.can_move_to_tier(
            loser, loser_target_tier, self.image_stats, self.tier_distribution_std)
        
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
        
        self._last_calculated_rankings = None
    
    def save_to_file(self, filename: str) -> bool:
        """Save all ranking data to a JSON file."""
        # Prepare core data
        core_data = {
            'image_folder': self.image_folder,
            'vote_count': self.vote_count,
            'image_stats': self.image_stats,
            'metadata_cache': self.metadata_cache
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
        """Load ranking data from a JSON file."""
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
        
        # Load other settings
        self.weight_manager.load_from_data(data)
        self.algorithm_settings.load_settings(data)
        self.tier_bounds_manager.load_settings(data)
        
        # Update existing images with strategic timing
        self._update_existing_images_with_strategic_timing()
        
        # Initialize all image stats
        for image_filename in self.image_stats:
            self.initialize_image_stats(image_filename)
        
        self._last_calculated_rankings = None
        
        return True, ""
    
    # Algorithm settings property accessors for backward compatibility
    @property
    def tier_distribution_std(self):
        return self.algorithm_settings.tier_distribution_std
    
    @tier_distribution_std.setter
    def tier_distribution_std(self, value):
        self.algorithm_settings.set_value('tier_distribution_std', value)
    
    @property
    def confidence_vote_scale(self):
        return self.algorithm_settings.confidence_vote_scale
    
    @confidence_vote_scale.setter
    def confidence_vote_scale(self, value):
        self.algorithm_settings.set_value('confidence_vote_scale', value)
    
    @property
    def confidence_balance(self):
        return self.algorithm_settings.confidence_balance
    
    @confidence_balance.setter
    def confidence_balance(self, value):
        self.algorithm_settings.set_value('confidence_balance', value)
    
    @property
    def overflow_threshold(self):
        return self.algorithm_settings.overflow_threshold
    
    @overflow_threshold.setter
    def overflow_threshold(self, value):
        self.algorithm_settings.set_value('overflow_threshold', value)
    
    @property
    def min_overflow_images(self):
        return self.algorithm_settings.min_overflow_images
    
    @min_overflow_images.setter
    def min_overflow_images(self, value):
        self.algorithm_settings.set_value('min_overflow_images', value)
    
    @property
    def min_votes_for_stability(self):
        return self.algorithm_settings.min_votes_for_stability
    
    @min_votes_for_stability.setter
    def min_votes_for_stability(self, value):
        self.algorithm_settings.set_value('min_votes_for_stability', value)
    
    # Tier bounds property accessors
    @property
    def tier_bounds_enabled(self):
        return self.tier_bounds_manager.enabled
    
    @tier_bounds_enabled.setter
    def tier_bounds_enabled(self, value):
        self.tier_bounds_manager.enabled = value
    
    @property
    def tier_bounds_std_multiplier(self):
        return self.tier_bounds_manager.std_multiplier
    
    @tier_bounds_std_multiplier.setter
    def tier_bounds_std_multiplier(self, value):
        self.tier_bounds_manager.std_multiplier = value
    
    @property
    def tier_bounds_min_confidence(self):
        return self.tier_bounds_manager.min_confidence
    
    @tier_bounds_min_confidence.setter
    def tier_bounds_min_confidence(self, value):
        self.tier_bounds_manager.min_confidence = value
    
    @property
    def tier_bounds_min_votes(self):
        return self.tier_bounds_manager.min_votes
    
    @tier_bounds_min_votes.setter
    def tier_bounds_min_votes(self, value):
        self.tier_bounds_manager.min_votes = value
    
    @property
    def tier_bounds_adaptive(self):
        return self.tier_bounds_manager.adaptive
    
    @tier_bounds_adaptive.setter
    def tier_bounds_adaptive(self, value):
        self.tier_bounds_manager.adaptive = value
    
    def get_tier_bounds_info(self) -> Dict[str, Any]:
        """Get information about current tier bounds."""
        return self.tier_bounds_manager.get_bounds_info(self.tier_distribution_std, self.image_stats)
    
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
    
    def get_tier_distribution(self) -> Dict[int, int]:
        """Get the distribution of images across tiers."""
        tier_counts = defaultdict(int)
        for stats in self.image_stats.values():
            tier_counts[stats['current_tier']] += 1
        return dict(tier_counts)
    
    def get_overall_statistics(self) -> Dict[str, Any]:
        """Calculate overall statistics for the ranking system."""
        if not self.image_stats:
            return {
                'total_images': 0,
                'total_votes': 0,
                'avg_votes_per_image': 0,
                'tier_distribution': {},
                'tier_bounds_info': self.get_tier_bounds_info()
            }
        
        total_images = len(self.image_stats)
        total_votes = self.vote_count
        avg_votes_per_image = sum(s['votes'] for s in self.image_stats.values()) / total_images
        
        return {
            'total_images': total_images,
            'total_votes': total_votes,
            'avg_votes_per_image': avg_votes_per_image,
            'tier_distribution': self.get_tier_distribution(),
            'tier_bounds_info': self.get_tier_bounds_info()
        }
    
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