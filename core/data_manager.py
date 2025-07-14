"""
Data management module for the Image Ranking System.

This module handles all data persistence operations including:
- Saving and loading ranking data to/from JSON files
- Managing image statistics and voting history
- Providing data validation and migration capabilities
- Managing separate weights for left and right image selection

By centralizing data operations here, we can easily modify how data
is stored (JSON, database, etc.) without changing the rest of the application.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from collections import defaultdict

from config import Defaults


class DataManager:
    """
    Handles all data persistence operations for the ranking system.
    
    This class manages the structure and persistence of all ranking data,
    including image statistics, voting history, user preferences, and
    separate selection weights for left and right images.
    """
    
    def __init__(self):
        """Initialize the data manager with default values."""
        self.reset_data()
    
    def reset_data(self):
        """Reset all data to initial state."""
        # Core application state
        self.image_folder = ""
        self.vote_count = 0
        self.image_stats = {}
        
        # Separate weights for left and right image selection
        self.left_weights = Defaults.LEFT_SELECTION_WEIGHTS.copy()
        self.right_weights = Defaults.RIGHT_SELECTION_WEIGHTS.copy()
        
        # Legacy weights property for backward compatibility
        self.weights = Defaults.SELECTION_WEIGHTS.copy()
        
        # Tier distribution parameter for normal distribution calculation
        self.tier_distribution_std = 1.5  # Default standard deviation
        
        # Cached data for performance
        self._last_calculated_rankings = None
        self._last_calculation_vote_count = -1
    
    def get_left_weights(self) -> Dict[str, float]:
        """Get the weights used for left image selection."""
        return self.left_weights.copy()
    
    def get_right_weights(self) -> Dict[str, float]:
        """Get the weights used for right image selection."""
        return self.right_weights.copy()
    
    def set_left_weights(self, weights: Dict[str, float]) -> None:
        """Set the weights used for left image selection."""
        self.left_weights = weights.copy()
        # Also update legacy weights property for backward compatibility
        self.weights = weights.copy()
    
    def set_right_weights(self, weights: Dict[str, float]) -> None:
        """Set the weights used for right image selection."""
        self.right_weights = weights.copy()
    
    def get_legacy_weights(self) -> Dict[str, float]:
        """Get the legacy weights property (for backward compatibility)."""
        return self.weights.copy()
    
    def set_legacy_weights(self, weights: Dict[str, float]) -> None:
        """Set the legacy weights property (for backward compatibility)."""
        self.weights = weights.copy()
        # When legacy weights are set, apply to both left and right
        self.left_weights = weights.copy()
        self.right_weights = weights.copy()
    
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
        Set metadata for an image.
        
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
    
    def save_to_file(self, filename: str) -> bool:
        """
        Save all ranking data to a JSON file.
        
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
                'left_weights': self.left_weights,
                'right_weights': self.right_weights,
                'weights': self.weights,  # Keep for backward compatibility
                'tier_distribution_std': self.tier_distribution_std,
                'timestamp': datetime.now().isoformat(),
                'version': '1.2'  # Updated version for separate left/right weights
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    def load_from_file(self, filename: str) -> Tuple[bool, str]:
        """
        Load ranking data from a JSON file.
        
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
            
            # Load weights with backward compatibility
            if 'left_weights' in data and 'right_weights' in data:
                # New format with separate left/right weights
                self.left_weights = data['left_weights']
                self.right_weights = data['right_weights']
                # Also load legacy weights if present
                if 'weights' in data:
                    self.weights = data['weights']
                else:
                    # Use left weights as legacy weights
                    self.weights = self.left_weights.copy()
            elif 'weights' in data:
                # Old format - use the same weights for both left and right
                self.weights = data['weights']
                self.left_weights = data['weights'].copy()
                self.right_weights = data['weights'].copy()
            else:
                # No weights found - use defaults
                self.weights = Defaults.SELECTION_WEIGHTS.copy()
                self.left_weights = Defaults.LEFT_SELECTION_WEIGHTS.copy()
                self.right_weights = Defaults.RIGHT_SELECTION_WEIGHTS.copy()
            
            # Load tier distribution parameter (with backward compatibility)
            if 'tier_distribution_std' in data:
                self.tier_distribution_std = data['tier_distribution_std']
            else:
                self.tier_distribution_std = 1.5  # Default value for older files
            
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
            
            # Validate tier distribution parameter
            if not isinstance(self.tier_distribution_std, (int, float)) or self.tier_distribution_std <= 0:
                return False, "Invalid tier distribution standard deviation"
            
            # Validate weight sets
            for weight_name, weights in [('left_weights', self.left_weights), 
                                       ('right_weights', self.right_weights),
                                       ('legacy_weights', self.weights)]:
                if not isinstance(weights, dict):
                    return False, f"Invalid {weight_name} format"
                
                required_weight_keys = ['recency', 'low_votes', 'instability', 'tier_size']
                for key in required_weight_keys:
                    if key not in weights:
                        return False, f"Missing weight key '{key}' in {weight_name}"
                    if not isinstance(weights[key], (int, float)) or weights[key] < 0:
                        return False, f"Invalid weight value for '{key}' in {weight_name}"
            
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