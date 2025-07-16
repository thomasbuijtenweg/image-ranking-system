"""Weight management for the Image Ranking System."""

from typing import Dict
from config import Defaults


class WeightManager:
    """Manages algorithm weights and priority preferences."""
    
    def __init__(self):
        self.reset_to_defaults()
    
    def reset_to_defaults(self):
        """Reset all weights and preferences to default values."""
        self.left_weights = Defaults.LEFT_SELECTION_WEIGHTS.copy()
        self.right_weights = Defaults.RIGHT_SELECTION_WEIGHTS.copy()
        self.weights = Defaults.SELECTION_WEIGHTS.copy()
        self.left_priority_preferences = Defaults.LEFT_PRIORITY_PREFERENCES.copy()
        self.right_priority_preferences = Defaults.RIGHT_PRIORITY_PREFERENCES.copy()
        self.tier_distribution_std = 1.5
    
    def get_left_weights(self) -> Dict[str, float]:
        return self.left_weights.copy()
    
    def get_right_weights(self) -> Dict[str, float]:
        return self.right_weights.copy()
    
    def set_left_weights(self, weights: Dict[str, float]) -> None:
        if self.validate_weights(weights):
            self.left_weights = weights.copy()
            self.weights = weights.copy()
    
    def set_right_weights(self, weights: Dict[str, float]) -> None:
        if self.validate_weights(weights):
            self.right_weights = weights.copy()
    
    def get_legacy_weights(self) -> Dict[str, float]:
        return self.weights.copy()
    
    def set_legacy_weights(self, weights: Dict[str, float]) -> None:
        if self.validate_weights(weights):
            self.weights = weights.copy()
            self.left_weights = weights.copy()
            self.right_weights = weights.copy()
    
    def get_left_priority_preferences(self) -> Dict[str, bool]:
        return self.left_priority_preferences.copy()
    
    def get_right_priority_preferences(self) -> Dict[str, bool]:
        return self.right_priority_preferences.copy()
    
    def set_left_priority_preferences(self, preferences: Dict[str, bool]) -> None:
        if self.validate_preferences(preferences):
            self.left_priority_preferences = preferences.copy()
    
    def set_right_priority_preferences(self, preferences: Dict[str, bool]) -> None:
        if self.validate_preferences(preferences):
            self.right_priority_preferences = preferences.copy()
    
    def get_tier_distribution_std(self) -> float:
        return self.tier_distribution_std
    
    def set_tier_distribution_std(self, std_dev: float) -> None:
        if isinstance(std_dev, (int, float)) and std_dev > 0:
            self.tier_distribution_std = std_dev
    
    def validate_weights(self, weights: Dict[str, float]) -> bool:
        """Validate weight values."""
        if not isinstance(weights, dict):
            return False
        
        required_keys = ['recency', 'low_votes', 'instability', 'tier_size']
        for key in required_keys:
            if key not in weights:
                return False
            if not isinstance(weights[key], (int, float)) or weights[key] < 0:
                return False
        
        return True
    
    def validate_preferences(self, preferences: Dict[str, bool]) -> bool:
        """Validate priority preference values."""
        if not isinstance(preferences, dict):
            return False
        
        required_keys = ['prioritize_high_stability', 'prioritize_high_votes', 'prioritize_new_images']
        for key in required_keys:
            if key not in preferences:
                return False
            if not isinstance(preferences[key], bool):
                return False
        
        return True
    
    def load_from_data(self, data: Dict) -> None:
        """Load weights and preferences from saved data."""
        if 'left_weights' in data and 'right_weights' in data:
            if self.validate_weights(data['left_weights']):
                self.left_weights = data['left_weights']
            if self.validate_weights(data['right_weights']):
                self.right_weights = data['right_weights']
            if 'weights' in data and self.validate_weights(data['weights']):
                self.weights = data['weights']
            else:
                self.weights = self.left_weights.copy()
        elif 'weights' in data:
            if self.validate_weights(data['weights']):
                self.weights = data['weights']
                self.left_weights = data['weights'].copy()
                self.right_weights = data['weights'].copy()
        
        if 'left_priority_preferences' in data and 'right_priority_preferences' in data:
            left_prefs = data['left_priority_preferences'].copy()
            right_prefs = data['right_priority_preferences'].copy()
            
            if 'prioritize_new_images' not in left_prefs:
                left_prefs['prioritize_new_images'] = False
            if 'prioritize_new_images' not in right_prefs:
                right_prefs['prioritize_new_images'] = False
            
            if self.validate_preferences(left_prefs):
                self.left_priority_preferences = left_prefs
            if self.validate_preferences(right_prefs):
                self.right_priority_preferences = right_prefs
        
        if 'tier_distribution_std' in data:
            if isinstance(data['tier_distribution_std'], (int, float)) and data['tier_distribution_std'] > 0:
                self.tier_distribution_std = data['tier_distribution_std']
    
    def export_to_data(self) -> Dict:
        """Export weights and preferences to data dictionary for saving."""
        return {
            'left_weights': self.left_weights,
            'right_weights': self.right_weights,
            'weights': self.weights,
            'left_priority_preferences': self.left_priority_preferences,
            'right_priority_preferences': self.right_priority_preferences,
            'tier_distribution_std': self.tier_distribution_std
        }