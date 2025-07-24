"""Tier bounds management for the Image Ranking System."""

import math
import statistics
from typing import Tuple, Dict, Any


class TierBoundsManager:
    """Manages intelligent tier bounds to prevent runaway tier inflation."""
    
    def __init__(self):
        self.reset_to_defaults()
    
    def reset_to_defaults(self):
        """Reset tier bounds settings to default values."""
        self.enabled = True
        self.std_multiplier = 3.0  # 3 standard deviations = 99.7% of images
        self.min_confidence = 0.8  # Minimum confidence to exceed bounds
        self.min_votes = 10  # Minimum votes to exceed bounds
        self.adaptive = True  # Allow bounds to grow with collection
    
    def calculate_bounds(self, tier_distribution_std: float, image_stats: Dict[str, Any]) -> Tuple[int, int]:
        """
        Calculate the current tier bounds based on standard deviation and collection size.
        
        Args:
            tier_distribution_std: Standard deviation for tier distribution
            image_stats: Dictionary of image statistics
            
        Returns:
            Tuple of (min_tier, max_tier)
        """
        if not self.enabled:
            return float('-inf'), float('inf')
        
        # Base bounds on standard deviation
        base_bound = int(tier_distribution_std * self.std_multiplier)
        
        if self.adaptive:
            # Adaptive bounds grow with collection size
            total_images = len(image_stats)
            
            # Allow more tiers for larger collections
            # log scaling: 100 images = +0 tiers, 1000 images = +1 tier, 10000 images = +2 tiers
            adaptive_bonus = int(math.log10(max(total_images, 10)) - 2) if total_images > 100 else 0
            
            # Also consider current tier distribution
            if image_stats:
                current_tiers = [stats.get('current_tier', 0) for stats in image_stats.values()]
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
    
    def can_move_to_tier(self, image_name: str, target_tier: int, 
                        image_stats: Dict[str, Any], tier_distribution_std: float) -> Tuple[bool, str]:
        """
        Check if an image can move to the target tier.
        
        Args:
            image_name: Name of the image
            target_tier: Tier the image wants to move to
            image_stats: Dictionary of all image statistics
            tier_distribution_std: Standard deviation for tier distribution
            
        Returns:
            Tuple of (can_move, reason)
        """
        if not self.enabled:
            return True, "Tier bounds disabled"
        
        min_tier, max_tier = self.calculate_bounds(tier_distribution_std, image_stats)
        
        # Check if target tier is within bounds
        if min_tier <= target_tier <= max_tier:
            return True, "Within bounds"
        
        # If outside bounds, check if image qualifies to exceed bounds
        stats = image_stats.get(image_name, {})
        votes = stats.get('votes', 0)
        
        # Calculate confidence (simplified version)
        confidence = self._calculate_confidence(stats)
        
        # Check qualification criteria
        if (confidence >= self.min_confidence and 
            votes >= self.min_votes):
            return True, f"High confidence ({confidence:.3f}) and sufficient votes ({votes})"
        
        # Not qualified to exceed bounds
        reason = f"Insufficient qualification: confidence={confidence:.3f} (need {self.min_confidence}), votes={votes} (need {self.min_votes})"
        return False, reason
    
    def _calculate_confidence(self, stats: Dict[str, Any]) -> float:
        """Calculate confidence for an image based on its statistics."""
        votes = stats.get('votes', 0)
        
        if votes == 0:
            return 0.0
        
        tier_history = stats.get('tier_history', [0])
        if len(tier_history) <= 1:
            stability = 0.0
        else:
            stability = statistics.stdev(tier_history)
        
        effective_stability = stability / math.sqrt(votes)
        confidence = 1.0 / (1.0 + effective_stability)
        
        return confidence
    
    def get_bounds_info(self, tier_distribution_std: float, image_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about current tier bounds."""
        if not self.enabled:
            return {'enabled': False}
        
        min_tier, max_tier = self.calculate_bounds(tier_distribution_std, image_stats)
        
        # Count images at bounds
        at_min_bound = sum(1 for stats in image_stats.values() 
                          if stats.get('current_tier', 0) <= min_tier)
        at_max_bound = sum(1 for stats in image_stats.values() 
                          if stats.get('current_tier', 0) >= max_tier)
        
        # Count qualified images that could exceed bounds
        qualified_for_bounds = 0
        for image_name, stats in image_stats.items():
            votes = stats.get('votes', 0)
            if votes >= self.min_votes:
                confidence = self._calculate_confidence(stats)
                if confidence >= self.min_confidence:
                    qualified_for_bounds += 1
        
        return {
            'enabled': True,
            'min_tier': min_tier,
            'max_tier': max_tier,
            'std_multiplier': self.std_multiplier,
            'min_confidence': self.min_confidence,
            'min_votes': self.min_votes,
            'adaptive': self.adaptive,
            'images_at_min_bound': at_min_bound,
            'images_at_max_bound': at_max_bound,
            'qualified_for_bounds': qualified_for_bounds,
            'total_images': len(image_stats)
        }
    
    def export_settings(self) -> Dict[str, Any]:
        """Export tier bounds settings."""
        return {
            'tier_bounds_settings': {
                'enabled': self.enabled,
                'std_multiplier': self.std_multiplier,
                'min_confidence': self.min_confidence,
                'min_votes': self.min_votes,
                'adaptive': self.adaptive
            }
        }
    
    def load_settings(self, data: Dict[str, Any]) -> None:
        """Load tier bounds settings from saved data."""
        if 'tier_bounds_settings' in data:
            settings = data['tier_bounds_settings']
            self.enabled = settings.get('enabled', True)
            self.std_multiplier = settings.get('std_multiplier', 3.0)
            self.min_confidence = settings.get('min_confidence', 0.8)
            self.min_votes = settings.get('min_votes', 10)
            self.adaptive = settings.get('adaptive', True)
        else:
            # Set defaults if no settings found
            self.reset_to_defaults()