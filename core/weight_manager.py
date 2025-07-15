"""
Weight management module for the Image Ranking System.

This module handles all weight-related operations including validation,
storage, and management of separate left/right selection weights and
priority preferences.
"""

from typing import Dict
from config import Defaults


class WeightManager:
    """
    Manages algorithm weights and priority preferences.
    
    This class handles the storage and validation of selection weights
    and priority preferences for both left and right image selection.
    """
    
    def __init__(self):
        """Initialize the weight manager with default values."""
        self.reset_to_defaults()
    
    def reset_to_defaults(self):
        """Reset all weights and preferences to default values."""
        # Separate weights for left and right image selection
        self.left_weights = Defaults.LEFT_SELECTION_WEIGHTS.copy()
        self.right_weights = Defaults.RIGHT_SELECTION_WEIGHTS.copy()
        
        # Legacy weights property for backward compatibility
        self.weights = Defaults.SELECTION_WEIGHTS.copy()
        
        # Priority preferences for left and right image selection
        self.left_priority_preferences = Defaults.LEFT_PRIORITY_PREFERENCES.copy()
        self.right_priority_preferences = Defaults.RIGHT_PRIORITY_PREFERENCES.copy()
        
        # Tier distribution parameter for normal distribution calculation
        self.tier_distribution_std = 1.5  # Default standard deviation
    
    def get_left_weights(self) -> Dict[str, float]:
        """Get the weights used for left image selection."""
        return self.left_weights.copy()
    
    def get_right_weights(self) -> Dict[str, float]:
        """Get the weights used for right image selection."""
        return self.right_weights.copy()
    
    def set_left_weights(self, weights: Dict[str, float]) -> None:
        """Set the weights used for left image selection."""
        if self.validate_weights(weights):
            self.left_weights = weights.copy()
            # Also update legacy weights property for backward compatibility
            self.weights = weights.copy()
    
    def set_right_weights(self, weights: Dict[str, float]) -> None:
        """Set the weights used for right image selection."""
        if self.validate_weights(weights):
            self.right_weights = weights.copy()
    
    def get_legacy_weights(self) -> Dict[str, float]:
        """Get the legacy weights property (for backward compatibility)."""
        return self.weights.copy()
    
    def set_legacy_weights(self, weights: Dict[str, float]) -> None:
        """Set the legacy weights property (for backward compatibility)."""
        if self.validate_weights(weights):
            self.weights = weights.copy()
            # When legacy weights are set, apply to both left and right
            self.left_weights = weights.copy()
            self.right_weights = weights.copy()
    
    def get_left_priority_preferences(self) -> Dict[str, bool]:
        """Get the priority preferences used for left image selection."""
        return self.left_priority_preferences.copy()
    
    def get_right_priority_preferences(self) -> Dict[str, bool]:
        """Get the priority preferences used for right image selection."""
        return self.right_priority_preferences.copy()
    
    def set_left_priority_preferences(self, preferences: Dict[str, bool]) -> None:
        """Set the priority preferences used for left image selection."""
        if self.validate_preferences(preferences):
            self.left_priority_preferences = preferences.copy()
    
    def set_right_priority_preferences(self, preferences: Dict[str, bool]) -> None:
        """Set the priority preferences used for right image selection."""
        if self.validate_preferences(preferences):
            self.right_priority_preferences = preferences.copy()
    
    def get_tier_distribution_std(self) -> float:
        """Get the tier distribution standard deviation."""
        return self.tier_distribution_std
    
    def set_tier_distribution_std(self, std_dev: float) -> None:
        """Set the tier distribution standard deviation."""
        if isinstance(std_dev, (int, float)) and std_dev > 0:
            self.tier_distribution_std = std_dev
    
    def validate_weights(self, weights: Dict[str, float]) -> bool:
        """
        Validate weight values.
        
        Args:
            weights: Dictionary of weight values to validate
            
        Returns:
            True if weights are valid, False otherwise
        """
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
        """
        Validate priority preference values.
        
        Args:
            preferences: Dictionary of preference values to validate
            
        Returns:
            True if preferences are valid, False otherwise
        """
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
        """
        Load weights and preferences from saved data.
        
        Args:
            data: Dictionary containing saved weight/preference data
        """
        # Load weights with backward compatibility
        if 'left_weights' in data and 'right_weights' in data:
            # New format with separate left/right weights
            if self.validate_weights(data['left_weights']):
                self.left_weights = data['left_weights']
            if self.validate_weights(data['right_weights']):
                self.right_weights = data['right_weights']
            # Also load legacy weights if present
            if 'weights' in data and self.validate_weights(data['weights']):
                self.weights = data['weights']
            else:
                # Use left weights as legacy weights
                self.weights = self.left_weights.copy()
        elif 'weights' in data:
            # Old format - use the same weights for both left and right
            if self.validate_weights(data['weights']):
                self.weights = data['weights']
                self.left_weights = data['weights'].copy()
                self.right_weights = data['weights'].copy()
        
        # Load priority preferences with backward compatibility
        if 'left_priority_preferences' in data and 'right_priority_preferences' in data:
            # Handle the case where old data doesn't have the new 'prioritize_new_images' field
            left_prefs = data['left_priority_preferences'].copy()
            right_prefs = data['right_priority_preferences'].copy()
            
            # Add missing 'prioritize_new_images' field if not present (backward compatibility)
            if 'prioritize_new_images' not in left_prefs:
                left_prefs['prioritize_new_images'] = False
            if 'prioritize_new_images' not in right_prefs:
                right_prefs['prioritize_new_images'] = False
            
            if self.validate_preferences(left_prefs):
                self.left_priority_preferences = left_prefs
            if self.validate_preferences(right_prefs):
                self.right_priority_preferences = right_prefs
        
        # Load tier distribution parameter
        if 'tier_distribution_std' in data:
            if isinstance(data['tier_distribution_std'], (int, float)) and data['tier_distribution_std'] > 0:
                self.tier_distribution_std = data['tier_distribution_std']
    
    def export_to_data(self) -> Dict:
        """
        Export weights and preferences to data dictionary for saving.
        
        Returns:
            Dictionary containing all weight and preference data
        """
        return {
            'left_weights': self.left_weights,
            'right_weights': self.right_weights,
            'weights': self.weights,  # Keep for backward compatibility
            'left_priority_preferences': self.left_priority_preferences,
            'right_priority_preferences': self.right_priority_preferences,
            'tier_distribution_std': self.tier_distribution_std
        }