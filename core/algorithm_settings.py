"""Algorithm settings management for the Image Ranking System - tier bounds system removed."""

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
    DEFAULT_MAX_VOTES_MULTIPLIER = 1.5
    DEFAULT_MAX_VOTES_HARD_LIMIT_MULTIPLIER = 2.0
    DEFAULT_SIM_WEIGHT_VISUAL = 0.50
    DEFAULT_SIM_WEIGHT_TEXT   = 0.30
    DEFAULT_SIM_WEIGHT_TAGS   = 0.20
    DEFAULT_TARGET_COUNT          = 0      # 0 = cutline system disabled
    DEFAULT_CUTLINE_BUFFER_TIERS  = 2      # tiers either side of cutline = boundary zone
    DEFAULT_ZONE_BASE_VOTES       = 5      # min votes before any image can be confirmed
    DEFAULT_ZONE_VOTES_PER_TIER   = 0.5    # extra votes required per tier from cutline
    
    # Valid ranges for settings
    VALID_RANGES = {
        'tier_distribution_std': (0.5, 5.0),
        'confidence_vote_scale': (1.0, 100.0),
        'confidence_balance': (0.0, 1.0),
        'overflow_threshold': (0.5, 3.0),
        'min_overflow_images': (1, 20),
        'min_votes_for_stability': (1, 50),
        'max_votes_multiplier': (1.0, 5.0),
        'max_votes_hard_limit_multiplier': (1.5, 10.0),
        'sim_weight_visual': (0.0, 1.0),
        'sim_weight_text':   (0.0, 1.0),
        'sim_weight_tags':   (0.0, 1.0),
        'target_count':         (0, 100000),
        'cutline_buffer_tiers': (1, 10),
        'zone_base_votes':      (1, 50),
        'zone_votes_per_tier':  (0.0, 5.0),
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
        self.max_votes_multiplier = self.DEFAULT_MAX_VOTES_MULTIPLIER
        self.max_votes_hard_limit_multiplier = self.DEFAULT_MAX_VOTES_HARD_LIMIT_MULTIPLIER
        self.sim_weight_visual = self.DEFAULT_SIM_WEIGHT_VISUAL
        self.sim_weight_text   = self.DEFAULT_SIM_WEIGHT_TEXT
        self.sim_weight_tags   = self.DEFAULT_SIM_WEIGHT_TAGS
        self.target_count         = self.DEFAULT_TARGET_COUNT
        self.cutline_buffer_tiers = self.DEFAULT_CUTLINE_BUFFER_TIERS
        self.zone_base_votes      = self.DEFAULT_ZONE_BASE_VOTES
        self.zone_votes_per_tier  = self.DEFAULT_ZONE_VOTES_PER_TIER
    
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
        if setting_name in ['min_overflow_images', 'min_votes_for_stability',
                             'target_count', 'cutline_buffer_tiers', 'zone_base_votes']:
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
                'max_votes_multiplier': self.max_votes_multiplier,
                'max_votes_hard_limit_multiplier': self.max_votes_hard_limit_multiplier,
                'sim_weight_visual': self.sim_weight_visual,
                'sim_weight_text':   self.sim_weight_text,
                'sim_weight_tags':   self.sim_weight_tags,
                'target_count':         self.target_count,
                'cutline_buffer_tiers': self.cutline_buffer_tiers,
                'zone_base_votes':      self.zone_base_votes,
                'zone_votes_per_tier':  self.zone_votes_per_tier,
                'algorithm_version': '2.6'
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
            self.set_value('max_votes_multiplier',
                          settings.get('max_votes_multiplier', self.DEFAULT_MAX_VOTES_MULTIPLIER))
            self.set_value('max_votes_hard_limit_multiplier',
                          settings.get('max_votes_hard_limit_multiplier', self.DEFAULT_MAX_VOTES_HARD_LIMIT_MULTIPLIER))
            self.set_value('sim_weight_visual',
                          settings.get('sim_weight_visual', self.DEFAULT_SIM_WEIGHT_VISUAL))
            self.set_value('sim_weight_text',
                          settings.get('sim_weight_text', self.DEFAULT_SIM_WEIGHT_TEXT))
            self.set_value('sim_weight_tags',
                          settings.get('sim_weight_tags', self.DEFAULT_SIM_WEIGHT_TAGS))
            self.set_value('target_count',
                          settings.get('target_count', self.DEFAULT_TARGET_COUNT))
            self.set_value('cutline_buffer_tiers',
                          settings.get('cutline_buffer_tiers', self.DEFAULT_CUTLINE_BUFFER_TIERS))
            self.set_value('zone_base_votes',
                          settings.get('zone_base_votes', self.DEFAULT_ZONE_BASE_VOTES))
            self.set_value('zone_votes_per_tier',
                          settings.get('zone_votes_per_tier', self.DEFAULT_ZONE_VOTES_PER_TIER))
            
            print(f"Loaded algorithm settings v{settings.get('algorithm_version', '2.2')}")
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
            },
            'max_votes_multiplier': {
                'value': self.max_votes_multiplier,
                'default': self.DEFAULT_MAX_VOTES_MULTIPLIER,
                'range': self.VALID_RANGES['max_votes_multiplier'],
                'description': 'Images with votes > avg_votes * multiplier get deprioritised'
            },
            'max_votes_hard_limit_multiplier': {
                'value': self.max_votes_hard_limit_multiplier,
                'default': self.DEFAULT_MAX_VOTES_HARD_LIMIT_MULTIPLIER,
                'range': self.VALID_RANGES['max_votes_hard_limit_multiplier'],
                'description': 'Images with votes > avg_votes * this multiplier are excluded entirely from voting'
            },
            'sim_weight_visual': {
                'value': self.sim_weight_visual,
                'default': self.DEFAULT_SIM_WEIGHT_VISUAL,
                'range': self.VALID_RANGES['sim_weight_visual'],
                'description': 'Weight of CLIP visual similarity in hybrid score (should sum to 1 with text+tags)'
            },
            'sim_weight_text': {
                'value': self.sim_weight_text,
                'default': self.DEFAULT_SIM_WEIGHT_TEXT,
                'range': self.VALID_RANGES['sim_weight_text'],
                'description': 'Weight of CLIP prompt-text similarity in hybrid score'
            },
            'sim_weight_tags': {
                'value': self.sim_weight_tags,
                'default': self.DEFAULT_SIM_WEIGHT_TAGS,
                'range': self.VALID_RANGES['sim_weight_tags'],
                'description': 'Weight of structured tag overlap (artists/roles/styles) in hybrid score'
            },
            'target_count': {
                'value': self.target_count,
                'default': self.DEFAULT_TARGET_COUNT,
                'range': self.VALID_RANGES['target_count'],
                'description': 'Target number of images to keep. 0 = cutline system disabled'
            },
            'cutline_buffer_tiers': {
                'value': self.cutline_buffer_tiers,
                'default': self.DEFAULT_CUTLINE_BUFFER_TIERS,
                'range': self.VALID_RANGES['cutline_buffer_tiers'],
                'description': 'Tiers either side of cutline that form the boundary zone'
            },
            'zone_base_votes': {
                'value': self.zone_base_votes,
                'default': self.DEFAULT_ZONE_BASE_VOTES,
                'range': self.VALID_RANGES['zone_base_votes'],
                'description': 'Minimum votes required before any image can be confirmed in/out'
            },
            'zone_votes_per_tier': {
                'value': self.zone_votes_per_tier,
                'default': self.DEFAULT_ZONE_VOTES_PER_TIER,
                'range': self.VALID_RANGES['zone_votes_per_tier'],
                'description': 'Additional votes required per tier distance from cutline'
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
        new_settings.max_votes_multiplier = self.max_votes_multiplier
        new_settings.max_votes_hard_limit_multiplier = self.max_votes_hard_limit_multiplier
        new_settings.sim_weight_visual = self.sim_weight_visual
        new_settings.sim_weight_text   = self.sim_weight_text
        new_settings.sim_weight_tags   = self.sim_weight_tags
        new_settings.target_count         = self.target_count
        new_settings.cutline_buffer_tiers = self.cutline_buffer_tiers
        new_settings.zone_base_votes      = self.zone_base_votes
        new_settings.zone_votes_per_tier  = self.zone_votes_per_tier
        return new_settings
