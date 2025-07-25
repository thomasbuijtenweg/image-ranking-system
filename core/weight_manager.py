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
        self.left_priority_preferences = Defaults.LEFT_PRIORITY_PREFERENCES.copy()
        self.right_priority_preferences = Defaults.RIGHT_PRIORITY_PREFERENCES.copy()
    
    def get_left_weights(self) -> Dict[str, float]:
        return self.left_weights.copy()
    
    def get_right_weights(self) -> Dict[str, float]:
        return self.right_weights.copy()
    
    def set_left_weights(self, weights: Dict[str, float]) -> None:
        if self.validate_weights(weights):
            self.left_weights = weights.copy()
    
    def set_right_weights(self, weights: Dict[str, float]) -> None:
        if self.validate_weights(weights):
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
        
        required_keys = ['prioritize_high_stability', 'prioritize_high_votes']
        for key in required_keys:
            if key not in preferences:
                return False
            if not isinstance(preferences[key], bool):
                return False
        
        return True
    
    def load_from_data(self, data: Dict) -> None:
        """Load weights and preferences from saved data."""
        # Load left and right weights
        if 'left_weights' in data and self.validate_weights(data['left_weights']):
            self.left_weights = data['left_weights']
        
        if 'right_weights' in data and self.validate_weights(data['right_weights']):
            self.right_weights = data['right_weights']
        
        # Backwards compatibility: if only old 'weights' exists, use for both sides
        if 'weights' in data and not ('left_weights' in data and 'right_weights' in data):
            if self.validate_weights(data['weights']):
                self.left_weights = data['weights'].copy()
                self.right_weights = data['weights'].copy()
        
        # Load priority preferences
        if 'left_priority_preferences' in data and 'right_priority_preferences' in data:
            left_prefs = data['left_priority_preferences'].copy()
            right_prefs = data['right_priority_preferences'].copy()
            
            # Remove deprecated 'prioritize_new_images' preference if it exists
            if 'prioritize_new_images' in left_prefs:
                del left_prefs['prioritize_new_images']
            if 'prioritize_new_images' in right_prefs:
                del right_prefs['prioritize_new_images']
            
            if self.validate_preferences(left_prefs):
                self.left_priority_preferences = left_prefs
            if self.validate_preferences(right_prefs):
                self.right_priority_preferences = right_prefs
    
    def export_to_data(self) -> Dict:
        """Export weights and preferences to data dictionary for saving."""
        return {
            'left_weights': self.left_weights,
            'right_weights': self.right_weights,
            'left_priority_preferences': self.left_priority_preferences,
            'right_priority_preferences': self.right_priority_preferences
        }