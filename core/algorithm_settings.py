"""Algorithm settings management for the Image Ranking System."""

from typing import Dict, Any


class AlgorithmSettings:
    """Manages algorithm configuration and parameters."""
    
    # Default values
    DEFAULT_TIER_DISTRIBUTION_STD = 1.5
    DEFAULT_CONFIDENCE_VOTE_SCALE = 20.0
    DEFAULT_CONFIDENCE_BALANCE = 0.5
    DEFAULT_OVERFLOW_THRESHOLD = 1.0
    DEFAULT_MIN_OVERFLOW_IMAGES = 2
    DEFAULT_MIN_VOTES_FOR_STABILITY = 6
    
    # Valid ranges for settings
    VALID_RANGES = {
        'tier_distribution_std': (0.5, 5.0),
        'confidence_vote_scale': (1.0, 100.0),
        'confidence_balance': (0.0, 1.0),
        'overflow_threshold': (0.5, 3.0),
        'min_overflow_images': (1, 20),
        'min_votes_for_stability': (1, 50)
    }
    
    def __init__(self):
        self.reset_to_defaults()
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        self.tier_distribution_std = self.DEFAULT_TIER_DISTRIBUTION_STD
        self.confidence_vote_scale = self.DEFAULT_CONFIDENCE_VOTE_SCALE
        self.confidence_balance = self.DEFAULT_CONFIDENCE_BALANCE
        self.overflow_threshold = self.DEFAULT_OVERFLOW_THRESHOLD
        self.min_overflow_images = self.DEFAULT_MIN_OVERFLOW_IMAGES
        self.min_votes_for_stability = self.DEFAULT_MIN_VOTES_FOR_STABILITY
    
    def validate_setting(self, setting_name: str, value: Any) -> bool:
        """
        Validate a setting value.
        
        Args:
            setting_name: Name of the setting
            value: Value to validate
            
        Returns:
            True if valid, False otherwise
        """
        if setting_name not in self.VALID_RANGES:
            return False
        
        min_val, max_val = self.VALID_RANGES[setting_name]
        
        # Check type
        if setting_name in ['min_overflow_images', 'min_votes_for_stability']:
            if not isinstance(value, int):
                return False
        else:
            if not isinstance(value, (int, float)):
                return False
        
        # Check range
        return min_val <= value <= max_val
    
    def set_value(self, setting_name: str, value: Any) -> bool:
        """
        Set a setting value with validation.
        
        Args:
            setting_name: Name of the setting
            value: Value to set
            
        Returns:
            True if set successfully, False if invalid
        """
        if not self.validate_setting(setting_name, value):
            print(f"Invalid value for {setting_name}: {value}")
            return False
        
        setattr(self, setting_name, value)
        return True
    
    def get_value(self, setting_name: str) -> Any:
        """
        Get a setting value.
        
        Args:
            setting_name: Name of the setting
            
        Returns:
            Setting value or None if not found
        """
        return getattr(self, setting_name, None)
    
    def export_settings(self) -> Dict[str, Any]:
        """Export settings to a dictionary."""
        return {
            'algorithm_settings': {
                'tier_distribution_std': self.tier_distribution_std,
                'confidence_vote_scale': self.confidence_vote_scale,
                'confidence_balance': self.confidence_balance,
                'overflow_threshold': self.overflow_threshold,
                'min_overflow_images': self.min_overflow_images,
                'min_votes_for_stability': self.min_votes_for_stability,
                'algorithm_version': '2.1'
            }
        }
    
    def load_settings(self, data: Dict[str, Any]) -> None:
        """Load settings from saved data."""
        if 'algorithm_settings' in data:
            settings = data['algorithm_settings']
            
            # Load each setting with validation
            self.set_value('tier_distribution_std', 
                          settings.get('tier_distribution_std', self.DEFAULT_TIER_DISTRIBUTION_STD))
            self.set_value('confidence_vote_scale', 
                          settings.get('confidence_vote_scale', self.DEFAULT_CONFIDENCE_VOTE_SCALE))
            self.set_value('confidence_balance', 
                          settings.get('confidence_balance', self.DEFAULT_CONFIDENCE_BALANCE))
            self.set_value('overflow_threshold', 
                          settings.get('overflow_threshold', self.DEFAULT_OVERFLOW_THRESHOLD))
            self.set_value('min_overflow_images', 
                          settings.get('min_overflow_images', self.DEFAULT_MIN_OVERFLOW_IMAGES))
            self.set_value('min_votes_for_stability', 
                          settings.get('min_votes_for_stability', self.DEFAULT_MIN_VOTES_FOR_STABILITY))
            
            print(f"Loaded algorithm settings v{settings.get('algorithm_version', '2.1')}")
        else:
            # Set defaults if no settings found
            self.reset_to_defaults()
    
    def get_settings_info(self) -> Dict[str, Any]:
        """Get information about current settings."""
        return {
            'tier_distribution_std': {
                'value': self.tier_distribution_std,
                'default': self.DEFAULT_TIER_DISTRIBUTION_STD,
                'range': self.VALID_RANGES['tier_distribution_std'],
                'description': 'Standard deviation for tier distribution'
            },
            'confidence_vote_scale': {
                'value': self.confidence_vote_scale,
                'default': self.DEFAULT_CONFIDENCE_VOTE_SCALE,
                'range': self.VALID_RANGES['confidence_vote_scale'],
                'description': 'Scale factor for confidence calculation'
            },
            'confidence_balance': {
                'value': self.confidence_balance,
                'default': self.DEFAULT_CONFIDENCE_BALANCE,
                'range': self.VALID_RANGES['confidence_balance'],
                'description': 'Balance between stability and vote count'
            },
            'overflow_threshold': {
                'value': self.overflow_threshold,
                'default': self.DEFAULT_OVERFLOW_THRESHOLD,
                'range': self.VALID_RANGES['overflow_threshold'],
                'description': 'Multiplier for tier overflow detection'
            },
            'min_overflow_images': {
                'value': self.min_overflow_images,
                'default': self.DEFAULT_MIN_OVERFLOW_IMAGES,
                'range': self.VALID_RANGES['min_overflow_images'],
                'description': 'Minimum images needed for overflow'
            },
            'min_votes_for_stability': {
                'value': self.min_votes_for_stability,
                'default': self.DEFAULT_MIN_VOTES_FOR_STABILITY,
                'range': self.VALID_RANGES['min_votes_for_stability'],
                'description': 'Minimum votes for stability calculation'
            }
        }
    
    def clone(self) -> 'AlgorithmSettings':
        """Create a copy of the current settings."""
        new_settings = AlgorithmSettings()
        new_settings.tier_distribution_std = self.tier_distribution_std
        new_settings.confidence_vote_scale = self.confidence_vote_scale
        new_settings.confidence_balance = self.confidence_balance
        new_settings.overflow_threshold = self.overflow_threshold
        new_settings.min_overflow_images = self.min_overflow_images
        new_settings.min_votes_for_stability = self.min_votes_for_stability
        return new_settings