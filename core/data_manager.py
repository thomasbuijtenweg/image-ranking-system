"""Data management for the Image Ranking System."""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from collections import defaultdict

from config import Defaults
from core.weight_manager import WeightManager


class DataManager:
    """Handles data persistence and ranking statistics."""
    
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
        return self.weight_manager.get_tier_distribution_std()
    
    @tier_distribution_std.setter
    def tier_distribution_std(self, value: float) -> None:
        self.weight_manager.set_tier_distribution_std(value)
    
    def initialize_image_stats(self, image_filename: str) -> None:
        """Initialize stats for a new image with automatic tier 0 assignment."""
        if image_filename not in self.image_stats:
            # New images get 1 vote and are automatically placed at tier 0
            # The single vote represents automatic placement rather than an actual comparison
            self.image_stats[image_filename] = {
                'votes': 1,
                'wins': 1,
                'losses': 0,
                'current_tier': 0,
                'tier_history': [0],
                'last_voted': -1,
                'matchup_history': [],
                'prompt': None,
                'display_metadata': None
            }
        else:
            # For existing images, ensure required fields exist
            # But don't override existing values unless the field is missing
            required_fields = {
                'votes': 1,
                'wins': 1,
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
    
    def record_vote(self, winner: str, loser: str) -> None:
        """Record a vote between two images."""
        self.vote_count += 1
        
        winner_stats = self.image_stats[winner]
        winner_stats['votes'] += 1
        winner_stats['wins'] += 1
        winner_stats['current_tier'] += 1
        winner_stats['tier_history'].append(winner_stats['current_tier'])
        winner_stats['last_voted'] = self.vote_count
        winner_stats['matchup_history'].append((loser, True, self.vote_count))
        
        loser_stats = self.image_stats[loser]
        loser_stats['votes'] += 1
        loser_stats['losses'] += 1
        loser_stats['current_tier'] -= 1
        loser_stats['tier_history'].append(loser_stats['current_tier'])
        loser_stats['last_voted'] = self.vote_count
        loser_stats['matchup_history'].append((winner, False, self.vote_count))
        
        self._last_calculated_rankings = None
    
    def get_image_stats(self, image_filename: str) -> Dict[str, Any]:
        """Get statistics for a specific image."""
        return self.image_stats.get(image_filename, {})
    
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
        """Save all ranking data to a JSON file."""
        try:
            data = {
                'image_folder': self.image_folder,
                'vote_count': self.vote_count,
                'image_stats': self.image_stats,
                'metadata_cache': self.metadata_cache,
                'timestamp': datetime.now().isoformat(),
                'version': '1.6'
            }
            
            data.update(self.weight_manager.export_to_data())
            
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
                print(f"Loaded metadata cache for {len(self.metadata_cache)} images")
            else:
                self.metadata_cache = {}
            
            self.weight_manager.load_from_data(data)
            
            for image_filename in self.image_stats:
                self.initialize_image_stats(image_filename)
            
            self._last_calculated_rankings = None
            
            return True, ""
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {e}"
        except Exception as e:
            return False, f"Error loading data: {e}"