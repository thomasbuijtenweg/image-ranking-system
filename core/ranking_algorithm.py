"""
Ranking algorithm module for the Image Ranking System.

This module implements the intelligent pair selection algorithm that determines
which images should be compared next. The algorithm considers multiple factors:
- Recency (how recently an image was voted on)
- Vote count (prioritizing images with fewer or more votes based on preference)
- Tier stability (prioritizing images with unstable or stable positions based on preference)
- Tier size (prioritizing images in tiers that deviate from expected normal distribution)

The tier size calculation now considers that tiers should follow a normal distribution
centered at tier 0, with tier 0 being the largest and sizes decreasing as we move away.

Now supports separate weight sets and priority preferences for left and right image selection.
"""

import random
import statistics
import math
from typing import List, Tuple, Dict, Any, Optional, Set
from collections import defaultdict

from core.data_manager import DataManager


class RankingAlgorithm:
    """
    Implements the intelligent pair selection algorithm for image ranking.
    
    This class contains the core logic for determining which pairs of images
    should be compared next, based on multiple weighted factors that promote
    efficient and fair ranking convergence. Now supports separate weights
    and priority preferences for left and right image selection.
    """
    
    def __init__(self, data_manager: DataManager):
        """
        Initialize the ranking algorithm.
        
        Args:
            data_manager: DataManager instance containing all ranking data
        """
        self.data_manager = data_manager
        self._cached_rankings = None
        self._last_calculation_vote_count = -1
    
    def select_next_pair(self, available_images: List[str], 
                        exclude_pair: Optional[Tuple[str, str]] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Select the next pair of images to compare using separate weights for left and right selection.
        
        This is the main entry point for pair selection. It implements a
        sophisticated algorithm that considers multiple factors to choose
        the most informative pair for comparison, with separate priority
        calculations for left and right image selection.
        
        Args:
            available_images: List of image filenames to choose from
            exclude_pair: Optional pair to exclude from selection
            
        Returns:
            Tuple of (left_image, right_image) or (None, None) if no pair can be selected
        """
        if len(available_images) < 2:
            return None, None
        
        # Convert exclude_pair to set for easier comparison
        exclude_set = set(exclude_pair) if exclude_pair else set()
        
        # Group images by voting status
        never_voted_images = []
        voted_images = []
        
        for img in available_images:
            stats = self.data_manager.get_image_stats(img)
            if stats.get('votes', 0) == 0:
                never_voted_images.append(img)
            else:
                voted_images.append(img)
        
        # PRIORITY 1: Introduce never-voted images
        if never_voted_images:
            return self._select_introduction_pair(never_voted_images, voted_images, exclude_set)
        
        # PRIORITY 2: Normal tier-based selection with separate left/right weights
        return self._select_tier_based_pair_with_weights(voted_images, exclude_set)
    
    def _select_introduction_pair(self, never_voted_images: List[str], 
                                voted_images: List[str], exclude_set: Set[str]) -> Tuple[str, str]:
        """
        Select a pair to introduce a never-voted image.
        
        Args:
            never_voted_images: List of images that have never been voted on
            voted_images: List of images that have been voted on
            exclude_set: Set of image names to exclude from pairing
            
        Returns:
            Tuple of (new_image, comparison_image)
        """
        # Pick a random never-voted image
        new_image = random.choice(never_voted_images)
        
        if voted_images:
            # Try to find a good comparison image from voted images
            tier_0_images = [img for img in voted_images 
                           if self.data_manager.get_image_stats(img).get('current_tier', 0) == 0]
            
            if tier_0_images:
                # Filter out images that would recreate the excluded pair
                valid_images = [img for img in tier_0_images 
                              if not (exclude_set and {new_image, img} == exclude_set)]
                if valid_images:
                    return new_image, random.choice(valid_images)
                elif len(tier_0_images) > 1:
                    # If no valid images but multiple tier 0 images, just pick one
                    return new_image, random.choice(tier_0_images)
            
            # If no tier 0 images, find the closest tier to 0
            voted_by_tier = defaultdict(list)
            for img in voted_images:
                tier = self.data_manager.get_image_stats(img).get('current_tier', 0)
                voted_by_tier[tier].append(img)
            
            closest_tier = min(voted_by_tier.keys(), key=lambda x: abs(x))
            return new_image, random.choice(voted_by_tier[closest_tier])
        else:
            # All images are unvoted, just pick two randomly
            return random.sample(never_voted_images, 2)
    
    def _select_tier_based_pair_with_weights(self, voted_images: List[str], 
                                           exclude_set: Set[str]) -> Tuple[Optional[str], Optional[str]]:
        """
        Select a pair using tier-based algorithm with separate left and right priority scores.
        
        Args:
            voted_images: List of images that have been voted on
            exclude_set: Set of image names to exclude from pairing
            
        Returns:
            Tuple of (left_image, right_image) or (None, None) if no pair available
        """
        if not voted_images:
            return None, None
        
        # Calculate priority scores for each image using both weight sets
        left_priorities = self._calculate_priority_scores(voted_images, 'left')
        right_priorities = self._calculate_priority_scores(voted_images, 'right')
        
        # Group images by tier for better selection strategy
        images_by_tier = defaultdict(list)
        for img in voted_images:
            if img in left_priorities and img in right_priorities:  # Only include images with priority scores
                tier = self.data_manager.get_image_stats(img).get('current_tier', 0)
                images_by_tier[tier].append(img)
        
        # Strategy 1: Try to select from same tier using separate weights (80% of the time)
        if random.random() < 0.8:
            pair = self._select_from_same_tier_with_weights(images_by_tier, left_priorities, right_priorities, exclude_set)
            if pair[0] and pair[1]:
                return pair
        
        # Strategy 2: Try adjacent tiers using separate weights
        pair = self._select_from_adjacent_tiers_with_weights(images_by_tier, left_priorities, right_priorities, exclude_set)
        if pair[0] and pair[1]:
            return pair
        
        # Strategy 3: Fallback - pick highest priority from each weight set regardless of tier
        return self._select_highest_priorities_with_weights(left_priorities, right_priorities, exclude_set)
    
    def _select_from_same_tier_with_weights(self, images_by_tier: Dict[int, List[str]], 
                                          left_priorities: Dict[str, float], 
                                          right_priorities: Dict[str, float],
                                          exclude_set: Set[str]) -> Tuple[Optional[str], Optional[str]]:
        """Select images from the same tier using separate left/right weights."""
        # Sort tiers by size (prioritize crowded tiers)
        sorted_tiers = sorted(images_by_tier.keys())
        tiers_by_size = sorted(sorted_tiers, key=lambda t: len(images_by_tier[t]), reverse=True)
        
        for tier in tiers_by_size:
            tier_images = images_by_tier[tier]
            if len(tier_images) >= 2:
                # Sort by each weight set
                left_sorted = sorted(tier_images, key=lambda x: left_priorities[x], reverse=True)
                right_sorted = sorted(tier_images, key=lambda x: right_priorities[x], reverse=True)
                
                # Try combinations of top images from each sorted list
                for left_img in left_sorted[:3]:  # Try top 3 from left weights
                    for right_img in right_sorted[:3]:  # Try top 3 from right weights
                        if (left_img != right_img and 
                            not (exclude_set and {left_img, right_img} == exclude_set)):
                            return left_img, right_img
        
        return None, None
    
    def _select_from_adjacent_tiers_with_weights(self, images_by_tier: Dict[int, List[str]], 
                                               left_priorities: Dict[str, float], 
                                               right_priorities: Dict[str, float],
                                               exclude_set: Set[str]) -> Tuple[Optional[str], Optional[str]]:
        """Select images from adjacent tiers using separate left/right weights."""
        sorted_tiers = sorted(images_by_tier.keys())
        
        for i in range(len(sorted_tiers) - 1):
            tier1, tier2 = sorted_tiers[i], sorted_tiers[i + 1]
            if abs(tier2 - tier1) <= 1:  # Adjacent tiers
                images1 = images_by_tier[tier1]
                images2 = images_by_tier[tier2]
                
                if images1 and images2:
                    # Pick highest priority from each tier using appropriate weights
                    left_img = max(images1, key=lambda x: left_priorities[x])
                    right_img = max(images2, key=lambda x: right_priorities[x])
                    
                    # Check if this would recreate the excluded pair
                    if not (exclude_set and {left_img, right_img} == exclude_set):
                        return left_img, right_img
                    
                    # Try the reverse assignment
                    left_img = max(images2, key=lambda x: left_priorities[x])
                    right_img = max(images1, key=lambda x: right_priorities[x])
                    
                    if not (exclude_set and {left_img, right_img} == exclude_set):
                        return left_img, right_img
        
        return None, None
    
    def _select_highest_priorities_with_weights(self, left_priorities: Dict[str, float], 
                                              right_priorities: Dict[str, float],
                                              exclude_set: Set[str]) -> Tuple[Optional[str], Optional[str]]:
        """Select the highest priority images from each weight set regardless of tier."""
        if not left_priorities or not right_priorities:
            return None, None
        
        # Get top candidates from each weight set
        left_sorted = sorted(left_priorities.keys(), key=lambda x: left_priorities[x], reverse=True)
        right_sorted = sorted(right_priorities.keys(), key=lambda x: right_priorities[x], reverse=True)
        
        # Try combinations of top images
        for left_img in left_sorted[:5]:  # Try top 5 from left weights
            for right_img in right_sorted[:5]:  # Try top 5 from right weights
                if (left_img != right_img and 
                    not (exclude_set and {left_img, right_img} == exclude_set)):
                    return left_img, right_img
        
        # Ultimate fallback: random selection
        all_images = list(left_priorities.keys())
        if len(all_images) >= 2:
            max_attempts = 10
            for _ in range(max_attempts):
                pair = random.sample(all_images, 2)
                if not (exclude_set and set(pair) == exclude_set):
                    return pair[0], pair[1]
        
        return None, None
    
    def _calculate_expected_tier_proportion(self, tier: int, total_images: int) -> float:
        """
        Calculate the expected proportion of images that should be in a given tier
        based on a normal distribution centered at tier 0.
        
        Args:
            tier: The tier number (can be positive, negative, or zero)
            total_images: Total number of images in the system
            
        Returns:
            Expected proportion of images (0.0 to 1.0) that should be in this tier
        """
        # Use normal distribution probability density function
        # Higher density at tier 0, decreasing as we move away
        std_dev = self.data_manager.tier_distribution_std
        
        # Calculate the probability density for this tier
        # Using a simplified approach: e^(-(tier^2)/(2*std_dev^2))
        density = math.exp(-(tier ** 2) / (2 * std_dev ** 2))
        
        # We need to normalize this across all existing tiers
        # Get all existing tiers to calculate total density
        all_tiers = set()
        for stats in self.data_manager.image_stats.values():
            all_tiers.add(stats.get('current_tier', 0))
        
        # Calculate total density across all existing tiers
        total_density = sum(math.exp(-(t ** 2) / (2 * std_dev ** 2)) for t in all_tiers)
        
        # Return normalized proportion
        return density / total_density if total_density > 0 else 0.0
    
    def _calculate_priority_scores(self, images: List[str], weight_set: str = 'left') -> Dict[str, float]:
        """
        Calculate priority scores for each image based on multiple factors and preferences.
        
        Args:
            images: List of image filenames to calculate scores for
            weight_set: Which weight set to use ('left' or 'right')
            
        Returns:
            Dictionary mapping image names to priority scores
        """
        if not images:
            return {}
        
        # Get appropriate weights and preferences based on weight_set
        if weight_set == 'left':
            weights = self.data_manager.get_left_weights()
            preferences = self.data_manager.get_left_priority_preferences()
        elif weight_set == 'right':
            weights = self.data_manager.get_right_weights()
            preferences = self.data_manager.get_right_priority_preferences()
        else:
            # Fallback to legacy weights for backward compatibility
            weights = self.data_manager.get_legacy_weights()
            # Use default preferences if not available
            preferences = {'prioritize_high_stability': False, 'prioritize_high_votes': False}
        
        # Calculate maximum values for normalization
        max_votes = max(self.data_manager.get_image_stats(img).get('votes', 0) for img in images)
        max_stability = max(self._calculate_tier_stability(img) for img in images)
        vote_count = self.data_manager.vote_count
        
        # Calculate tier sizes and expected sizes based on normal distribution
        tier_sizes = defaultdict(int)
        for img in images:
            tier = self.data_manager.get_image_stats(img).get('current_tier', 0)
            tier_sizes[tier] += 1
        
        total_images = len(images)
        
        # Calculate tier size scores based on deviation from expected normal distribution
        tier_size_scores = {}
        for tier, actual_size in tier_sizes.items():
            expected_proportion = self._calculate_expected_tier_proportion(tier, total_images)
            expected_size = expected_proportion * total_images
            
            # Score is higher when tier is more over-populated than expected
            # This means tiers with more images than they should have get higher priority
            if expected_size > 0:
                overpopulation_ratio = actual_size / expected_size
                # Cap the ratio to prevent extreme scores
                tier_size_scores[tier] = min(overpopulation_ratio, 3.0) / 3.0
            else:
                tier_size_scores[tier] = 0.0
        
        # Calculate priority scores
        image_priorities = {}
        for img in images:
            stats = self.data_manager.get_image_stats(img)
            
            # Skip if never voted (handled separately)
            if stats.get('votes', 0) == 0:
                continue
            
            # Calculate individual component scores (normalized to 0-1 range)
            # Recency score: higher = needs voting more (hasn't been voted recently)
            last_voted = stats.get('last_voted', -1)
            recency_score = ((vote_count - last_voted) / (vote_count + 1) 
                           if last_voted >= 0 else 1.0)
            
            # Vote count score: depends on preference
            votes = stats.get('votes', 0)
            if preferences.get('prioritize_high_votes', False):
                # Higher score for more votes
                vote_score = votes / (max_votes + 1)
            else:
                # Higher score for fewer votes (default behavior)
                vote_score = 1 - (votes / (max_votes + 1))
            
            # Stability score: depends on preference
            stability = self._calculate_tier_stability(img)
            if preferences.get('prioritize_high_stability', False):
                # Higher score for more stable images (lower standard deviation)
                stability_score = 1 - (stability / (max_stability + 0.1))
            else:
                # Higher score for less stable images (higher standard deviation) - default behavior
                stability_score = stability / (max_stability + 0.1)
            
            # Tier size score: higher = tier is more over-populated than expected
            current_tier = stats.get('current_tier', 0)
            tier_size_score = tier_size_scores.get(current_tier, 0.0)
            
            # Combined priority score (weighted average)
            # Note: We use the legacy weight names for backward compatibility
            # 'low_votes' weight now applies to either low or high votes based on preference
            # 'instability' weight now applies to either instability or stability based on preference
            priority = (weights['recency'] * recency_score + 
                       weights['low_votes'] * vote_score + 
                       weights['instability'] * stability_score +
                       weights['tier_size'] * tier_size_score)
            
            image_priorities[img] = priority
        
        return image_priorities
    
    def _calculate_tier_stability(self, image_name: str) -> float:
        """
        Calculate the tier stability for a single image.
        
        Stability is measured as the standard deviation of the image's
        tier history. Lower values indicate more stable positioning.
        
        Args:
            image_name: Name of the image file
            
        Returns:
            Standard deviation of tier history, or 0.0 if insufficient data
        """
        stats = self.data_manager.get_image_stats(image_name)
        tier_history = stats.get('tier_history', [0])
        
        if len(tier_history) <= 1:
            return 0.0  # Can't calculate std dev with 1 or fewer data points
        
        return statistics.stdev(tier_history)
    
    def calculate_all_rankings(self) -> Dict[str, List[Tuple[str, Dict[str, Any]]]]:
        """
        Calculate rankings for all metrics.
        
        This method computes comprehensive rankings across different metrics
        and caches the results for performance.
        
        Returns:
            Dictionary containing ranked lists for each metric
        """
        # Check if we need to recalculate
        current_vote_count = self.data_manager.vote_count
        if (self._cached_rankings is not None and 
            self._last_calculation_vote_count == current_vote_count):
            return self._cached_rankings
        
        # Calculate metrics for each image
        image_metrics = {}
        for img, stats in self.data_manager.image_stats.items():
            individual_stability = self._calculate_tier_stability(img)
            
            metrics = {
                'filename': img,
                'total_votes': stats.get('votes', 0),
                'win_rate': (stats.get('wins', 0) / stats.get('votes', 1) 
                           if stats.get('votes', 0) > 0 else 0),
                'current_tier': stats.get('current_tier', 0),
                'tier_stability': individual_stability,
                'recency': (current_vote_count - stats.get('last_voted', -1) 
                          if stats.get('last_voted', -1) >= 0 else float('inf'))
            }
            image_metrics[img] = metrics
        
        # Create sorted rankings for each metric
        rankings = {
            'total_votes': sorted(image_metrics.items(), 
                                key=lambda x: x[1]['total_votes'], reverse=True),
            'win_rate': sorted(image_metrics.items(), 
                             key=lambda x: x[1]['win_rate'], reverse=True),
            'current_tier': sorted(image_metrics.items(), 
                                 key=lambda x: x[1]['current_tier'], reverse=True),
            'tier_stability': sorted(image_metrics.items(), 
                                   key=lambda x: x[1]['tier_stability']),  # Lower is more stable
            'recency': sorted(image_metrics.items(), 
                            key=lambda x: x[1]['recency'], reverse=True)  # Higher means less recent
        }
        
        # Cache the results
        self._cached_rankings = rankings
        self._last_calculation_vote_count = current_vote_count
        
        return rankings
    
    def get_selection_explanation(self, image1: str, image2: str) -> str:
        """
        Generate a human-readable explanation of why this pair was selected.
        
        Args:
            image1: First image in the pair (left side)
            image2: Second image in the pair (right side)
            
        Returns:
            Explanatory text about the pair selection
        """
        stats1 = self.data_manager.get_image_stats(image1)
        stats2 = self.data_manager.get_image_stats(image2)
        
        votes1 = stats1.get('votes', 0)
        votes2 = stats2.get('votes', 0)
        tier1 = stats1.get('current_tier', 0)
        tier2 = stats2.get('current_tier', 0)
        
        # Check if either image is new
        if votes1 == 0 or votes2 == 0:
            if votes1 == 0 and votes2 == 0:
                return "Both images are new - establishing initial rankings"
            elif votes1 == 0:
                return f"Introducing {image1} (new) against {image2} (Tier {tier2})"
            else:
                return f"Introducing {image2} (new) against {image1} (Tier {tier1})"
        
        # Both images have been voted on - explain selection with separate weights
        tier_diff = abs(tier1 - tier2)
        
        # Get priority preferences to explain selection behavior
        left_prefs = self.data_manager.get_left_priority_preferences()
        right_prefs = self.data_manager.get_right_priority_preferences()
        
        if tier_diff == 0:
            # Same tier comparison
            tier_size = sum(1 for img in self.data_manager.image_stats.keys() 
                          if self.data_manager.get_image_stats(img).get('current_tier', 0) == tier1)
            
            total_images = len(self.data_manager.image_stats)
            expected_proportion = self._calculate_expected_tier_proportion(tier1, total_images)
            expected_size = expected_proportion * total_images
            
            explanation = f"Left image (Tier {tier1}) selected using left weights"
            if left_prefs.get('prioritize_high_stability'):
                explanation += " (prioritizing stable images)"
            if left_prefs.get('prioritize_high_votes'):
                explanation += " (prioritizing high vote counts)"
            
            explanation += f", right image (Tier {tier2}) selected using right weights"
            if right_prefs.get('prioritize_high_stability'):
                explanation += " (prioritizing stable images)"
            if right_prefs.get('prioritize_high_votes'):
                explanation += " (prioritizing high vote counts)"
            
            if tier_size > expected_size * 1.2:  # 20% threshold for "over-populated"
                explanation += f" - Both from over-populated Tier {tier1} ({tier_size} images, expected ~{expected_size:.1f})"
            else:
                explanation += f" - Both from Tier {tier1} ({tier_size} images in tier)"
                
            return explanation
        else:
            # Different tier comparison
            return f"Left image selected from Tier {tier1} using left weights, right image selected from Tier {tier2} using right weights (tier difference: {tier_diff})"
    
    def get_tier_distribution_info(self) -> Dict[str, Any]:
        """
        Get information about current tier distribution vs expected distribution.
        
        Returns:
            Dictionary containing distribution analysis
        """
        if not self.data_manager.image_stats:
            return {}
        
        # Calculate actual tier distribution
        actual_distribution = defaultdict(int)
        for stats in self.data_manager.image_stats.values():
            tier = stats.get('current_tier', 0)
            actual_distribution[tier] += 1
        
        total_images = len(self.data_manager.image_stats)
        
        # Calculate expected distribution
        expected_distribution = {}
        distribution_analysis = {}
        
        for tier in actual_distribution.keys():
            expected_proportion = self._calculate_expected_tier_proportion(tier, total_images)
            expected_count = expected_proportion * total_images
            actual_count = actual_distribution[tier]
            
            expected_distribution[tier] = expected_count
            distribution_analysis[tier] = {
                'actual': actual_count,
                'expected': expected_count,
                'ratio': actual_count / expected_count if expected_count > 0 else 0,
                'deviation': actual_count - expected_count
            }
        
        return {
            'actual_distribution': dict(actual_distribution),
            'expected_distribution': expected_distribution,
            'analysis': distribution_analysis,
            'total_images': total_images
        }
    
    def invalidate_cache(self):
        """Invalidate the cached rankings to force recalculation."""
        self._cached_rankings = None
        self._last_calculation_vote_count = -1