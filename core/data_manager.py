"""Enhanced Data Manager with intelligent tier bounds."""

import json
import os
import math
import statistics
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from collections import defaultdict

from config import Defaults
from core.weight_manager import WeightManager


class DataManager:
    """Handles data persistence and ranking statistics with intelligent tier bounds."""
    
    def __init__(self):
        self.weight_manager = WeightManager()
        self.reset_data()
    
    def reset_data(self):
        """Reset all data to initial state."""
        self.image_folder = ""
        self.vote_count = 0
        self.image_stats = {}
        self.metadata_cache = {}
        self.weight_manager.reset_to_defaults()
        self._last_calculated_rankings = None
        self._last_calculation_vote_count = -1
        
        # Initialize algorithm settings
        self.tier_distribution_std = 1.5
        self.confidence_vote_scale = 20.0
        self.confidence_balance = 0.5
        self.overflow_threshold = 1.0
        self.min_overflow_images = 2
        self.min_votes_for_stability = 6
        
        # New tier bounds settings
        self.tier_bounds_enabled = True
        self.tier_bounds_std_multiplier = 3.0  # 3 standard deviations = 99.7% of images
        self.tier_bounds_min_confidence = 0.8  # Minimum confidence to exceed bounds
        self.tier_bounds_min_votes = 10  # Minimum votes to exceed bounds
        self.tier_bounds_adaptive = True  # Allow bounds to grow with collection
    
    def calculate_tier_bounds(self) -> Tuple[int, int]:
        """
        Calculate the current tier bounds based on standard deviation and collection size.
        
        Returns:
            Tuple of (min_tier, max_tier)
        """
        if not self.tier_bounds_enabled:
            return float('-inf'), float('inf')
        
        # Base bounds on standard deviation
        base_bound = int(self.tier_distribution_std * self.tier_bounds_std_multiplier)
        
        if self.tier_bounds_adaptive:
            # Adaptive bounds grow with collection size
            total_images = len(self.image_stats)
            
            # Allow more tiers for larger collections
            # log scaling: 100 images = +0 tiers, 1000 images = +1 tier, 10000 images = +2 tiers
            adaptive_bonus = int(math.log10(max(total_images, 10)) - 2) if total_images > 100 else 0
            
            # Also consider current tier distribution
            if self.image_stats:
                current_tiers = [stats.get('current_tier', 0) for stats in self.image_stats.values()]
                current_min = min(current_tiers)
                current_max = max(current_tiers)
                
                # Allow expansion by 1 tier beyond current bounds
                expansion_min = min(current_min - 1, -base_bound - adaptive_bonus)
                expansion_max = max(current_max + 1, base_bound + adaptive_bonus)
                
                return expansion_min, expansion_max
            else:
                return -base_bound - adaptive_bonus, base_bound + adaptive_bonus
        else:
            # Fixed bounds
            return -base_bound, base_bound
    
    def can_move_to_tier(self, image_name: str, target_tier: int) -> Tuple[bool, str]:
        """
        Check if an image can move to the target tier.
        
        Args:
            image_name: Name of the image
            target_tier: Tier the image wants to move to
            
        Returns:
            Tuple of (can_move, reason)
        """
        if not self.tier_bounds_enabled:
            return True, "Tier bounds disabled"
        
        min_tier, max_tier = self.calculate_tier_bounds()
        
        # Check if target tier is within bounds
        if min_tier <= target_tier <= max_tier:
            return True, "Within bounds"
        
        # If outside bounds, check if image qualifies to exceed bounds
        stats = self.image_stats.get(image_name, {})
        votes = stats.get('votes', 0)
        
        # Calculate confidence (simplified version of the confidence calculator)
        if votes == 0:
            confidence = 0.0
        else:
            tier_history = stats.get('tier_history', [0])
            if len(tier_history) <= 1:
                stability = 0.0
            else:
                stability = statistics.stdev(tier_history)
            
            effective_stability = stability / math.sqrt(votes)
            confidence = 1.0 / (1.0 + effective_stability)
        
        # Check qualification criteria
        if (confidence >= self.tier_bounds_min_confidence and 
            votes >= self.tier_bounds_min_votes):
            return True, f"High confidence ({confidence:.3f}) and sufficient votes ({votes})"
        
        # Not qualified to exceed bounds
        reason = f"Insufficient qualification: confidence={confidence:.3f} (need {self.tier_bounds_min_confidence}), votes={votes} (need {self.tier_bounds_min_votes})"
        return False, reason
    
    def record_vote(self, winner: str, loser: str) -> None:
        """Record a vote between two images with tier bounds checking."""
        self.vote_count += 1
        
        # Calculate target tiers
        winner_current_tier = self.image_stats[winner].get('current_tier', 0)
        loser_current_tier = self.image_stats[loser].get('current_tier', 0)
        
        winner_target_tier = winner_current_tier + 1
        loser_target_tier = loser_current_tier - 1
        
        # Check if moves are allowed
        winner_can_move, winner_reason = self.can_move_to_tier(winner, winner_target_tier)
        loser_can_move, loser_reason = self.can_move_to_tier(loser, loser_target_tier)
        
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
    
    def get_tier_bounds_info(self) -> Dict[str, Any]:
        """Get information about current tier bounds."""
        if not self.tier_bounds_enabled:
            return {'enabled': False}
        
        min_tier, max_tier = self.calculate_tier_bounds()
        
        # Count images at bounds
        at_min_bound = sum(1 for stats in self.image_stats.values() 
                          if stats.get('current_tier', 0) <= min_tier)
        at_max_bound = sum(1 for stats in self.image_stats.values() 
                          if stats.get('current_tier', 0) >= max_tier)
        
        # Count qualified images that could exceed bounds
        qualified_for_bounds = 0
        for image_name, stats in self.image_stats.items():
            votes = stats.get('votes', 0)
            if votes >= self.tier_bounds_min_votes:
                # Quick confidence check
                tier_history = stats.get('tier_history', [0])
                if len(tier_history) > 1:
                    stability = statistics.stdev(tier_history)
                    confidence = 1.0 / (1.0 + stability / math.sqrt(votes))
                    if confidence >= self.tier_bounds_min_confidence:
                        qualified_for_bounds += 1
        
        return {
            'enabled': True,
            'min_tier': min_tier,
            'max_tier': max_tier,
            'std_multiplier': self.tier_bounds_std_multiplier,
            'min_confidence': self.tier_bounds_min_confidence,
            'min_votes': self.tier_bounds_min_votes,
            'adaptive': self.tier_bounds_adaptive,
            'images_at_min_bound': at_min_bound,
            'images_at_max_bound': at_max_bound,
            'qualified_for_bounds': qualified_for_bounds,
            'total_images': len(self.image_stats)
        }
    
    def export_tier_bounds_settings(self) -> Dict[str, Any]:
        """Export tier bounds settings."""
        return {
            'tier_bounds_settings': {
                'enabled': self.tier_bounds_enabled,
                'std_multiplier': self.tier_bounds_std_multiplier,
                'min_confidence': self.tier_bounds_min_confidence,
                'min_votes': self.tier_bounds_min_votes,
                'adaptive': self.tier_bounds_adaptive
            }
        }
    
    def load_tier_bounds_settings(self, data: Dict[str, Any]) -> None:
        """Load tier bounds settings from saved data."""
        if 'tier_bounds_settings' in data:
            settings = data['tier_bounds_settings']
            self.tier_bounds_enabled = settings.get('enabled', True)
            self.tier_bounds_std_multiplier = settings.get('std_multiplier', 3.0)
            self.tier_bounds_min_confidence = settings.get('min_confidence', 0.8)
            self.tier_bounds_min_votes = settings.get('min_votes', 10)
            self.tier_bounds_adaptive = settings.get('adaptive', True)
        else:
            # Set defaults if no settings found
            self.tier_bounds_enabled = True
            self.tier_bounds_std_multiplier = 3.0
            self.tier_bounds_min_confidence = 0.8
            self.tier_bounds_min_votes = 10
            self.tier_bounds_adaptive = True
    
    def save_to_file(self, filename: str) -> bool:
        """Save all ranking data to a JSON file."""
        try:
            data = {
                'image_folder': self.image_folder,
                'vote_count': self.vote_count,
                'image_stats': self.image_stats,
                'metadata_cache': self.metadata_cache,
                'timestamp': datetime.now().isoformat(),
                'version': '2.1'  # Updated version for tier bounds
            }
            
            # Export weight manager data (for backward compatibility)
            data.update(self.weight_manager.export_to_data())
            
            # Export algorithm settings
            data.update(self.export_algorithm_settings())
            
            # Export tier bounds settings
            data.update(self.export_tier_bounds_settings())
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    def load_from_file(self, filename: str) -> Tuple[bool, str]:
        """Load ranking data from a JSON file."""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            required_fields = ['image_folder', 'vote_count', 'image_stats']
            for field in required_fields:
                if field not in data:
                    return False, f"Missing required field: {field}"
            
            self.image_folder = data['image_folder']
            self.vote_count = data['vote_count']
            self.image_stats = data['image_stats']
            
            if 'metadata_cache' in data:
                self.metadata_cache = data['metadata_cache']
            else:
                self.metadata_cache = {}
            
            # Load weight manager data (for backward compatibility)
            self.weight_manager.load_from_data(data)
            
            # Load algorithm settings
            self.load_algorithm_settings(data)
            
            # Load tier bounds settings
            self.load_tier_bounds_settings(data)
            
            # Validate and fix vote count inconsistencies
            self._validate_and_fix_vote_counts()
            
            # Update existing images with strategic timing
            self._update_existing_images_with_strategic_timing()
            
            for image_filename in self.image_stats:
                self.initialize_image_stats(image_filename)
            
            self._last_calculated_rankings = None
            
            return True, ""
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {e}"
        except Exception as e:
            return False, f"Error loading data: {e}"
    
    # ... (rest of the existing methods remain the same)
    
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
    
    @property
    def tier_distribution_std(self) -> float:
        return getattr(self, '_tier_distribution_std', 1.5)
    
    @tier_distribution_std.setter
    def tier_distribution_std(self, value: float) -> None:
        self._tier_distribution_std = value
    
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
    
    def export_algorithm_settings(self) -> Dict[str, Any]:
        """Export current algorithm settings to a dictionary."""
        return {
            'algorithm_settings': {
                'tier_distribution_std': getattr(self, '_tier_distribution_std', 1.5),
                'confidence_vote_scale': getattr(self, 'confidence_vote_scale', 20.0),
                'confidence_balance': getattr(self, 'confidence_balance', 0.5),
                'overflow_threshold': getattr(self, 'overflow_threshold', 1.0),
                'min_overflow_images': getattr(self, 'min_overflow_images', 2),
                'min_votes_for_stability': getattr(self, 'min_votes_for_stability', 6),
                'algorithm_version': '2.1'
            }
        }
    
    def load_algorithm_settings(self, data: Dict[str, Any]) -> None:
        """Load algorithm settings from loaded data."""
        if 'algorithm_settings' in data:
            settings = data['algorithm_settings']
            self.tier_distribution_std = settings.get('tier_distribution_std', 1.5)
            self.confidence_vote_scale = settings.get('confidence_vote_scale', 20.0)
            self.confidence_balance = settings.get('confidence_balance', 0.5)
            self.overflow_threshold = settings.get('overflow_threshold', 1.0)
            self.min_overflow_images = settings.get('min_overflow_images', 2)
            self.min_votes_for_stability = settings.get('min_votes_for_stability', 6)
            
            print(f"Loaded algorithm settings v{settings.get('algorithm_version', '2.1')}")
        else:
            # Set defaults
            self.tier_distribution_std = 1.5
            self.confidence_vote_scale = 20.0
            self.confidence_balance = 0.5
            self.overflow_threshold = 1.0
            self.min_overflow_images = 2
            self.min_votes_for_stability = 6
    
    def _validate_and_fix_vote_counts(self) -> None:
        """Validate and fix vote count inconsistencies from legacy data."""
        if not self.image_stats:
            return
        
        fixed_count = 0
        for image_filename, stats in self.image_stats.items():
            wins = stats.get('wins', 0)
            losses = stats.get('losses', 0)
            votes = stats.get('votes', 0)
            expected_votes = wins + losses
            
            if votes != expected_votes:
                stats['votes'] = expected_votes
                fixed_count += 1
        
        if fixed_count > 0:
            print(f"Corrected vote count inconsistencies for {fixed_count} images")
    
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
