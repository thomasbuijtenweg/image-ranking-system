"""
Ranking algorithm module for the Image Ranking System.

This module implements the intelligent pair selection algorithm that determines
which images should be compared next. The algorithm considers multiple factors:
- Recency (how recently an image was voted on)
- Vote count (prioritizing images with fewer votes)
- Tier stability (prioritizing images with unstable positions)
- Tier size (prioritizing images in crowded tiers)

By centralizing this logic, we can easily experiment with different ranking
strategies and maintain the complex selection logic in one place.
"""

import random
import statistics
from typing import List, Tuple, Dict, Any, Optional, Set
from collections import defaultdict

from core.data_manager import DataManager


class RankingAlgorithm:
    """
    Implements the intelligent pair selection algorithm for image ranking.
    
    This class contains the core logic for determining which pairs of images
    should be compared next, based on multiple weighted factors that promote
    efficient and fair ranking convergence.
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
        Select the next pair of images to compare.
        
        This is the main entry point for pair selection. It implements a
        sophisticated algorithm that considers multiple factors to choose
        the most informative pair for comparison.
        
        Args:
            available_images: List of image filenames to choose from
            exclude_pair: Optional pair to exclude from selection
            
        Returns:
            Tuple of (image1, image2) or (None, None) if no pair can be selected
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
        
        # PRIORITY 2: Normal tier-based selection
        return self._select_tier_based_pair(voted_images, exclude_set)
    
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
    
    def _select_tier_based_pair(self, voted_images: List[str], 
                               exclude_set: Set[str]) -> Tuple[Optional[str], Optional[str]]:
        """
        Select a pair using tier-based algorithm with priority scores.
        
        Args:
            voted_images: List of images that have been voted on
            exclude_set: Set of image names to exclude from pairing
            
        Returns:
            Tuple of (image1, image2) or (None, None) if no pair available
        """
        if not voted_images:
            return None, None
        
        # Calculate priority scores for each image
        image_priorities = self._calculate_priority_scores(voted_images)
        
        # Group images by tier
        images_by_tier = defaultdict(list)
        for img in voted_images:
            if img in image_priorities:  # Only include images with priority scores
                tier = self.data_manager.get_image_stats(img).get('current_tier', 0)
                images_by_tier[tier].append(img)
        
        # Try to find pairs within the same tier (prioritize crowded tiers)
        sorted_tiers = sorted(images_by_tier.keys())
        tiers_by_size = sorted(sorted_tiers, key=lambda t: len(images_by_tier[t]), reverse=True)
        
        for tier in tiers_by_size:
            tier_images = images_by_tier[tier]
            if len(tier_images) >= 2:
                # Sort by priority within this tier
                tier_images_sorted = sorted(tier_images, 
                                          key=lambda x: image_priorities[x], reverse=True)
                
                # Check if the top two would recreate the excluded pair
                if exclude_set and {tier_images_sorted[0], tier_images_sorted[1]} == exclude_set:
                    # Try other combinations
                    for i in range(len(tier_images_sorted)):
                        for j in range(i + 1, len(tier_images_sorted)):
                            if {tier_images_sorted[i], tier_images_sorted[j]} != exclude_set:
                                return tier_images_sorted[i], tier_images_sorted[j]
                else:
                    # Use priority-based selection most of the time
                    if random.random() < 0.8:  # 80% chance for priority-based
                        return tier_images_sorted[0], tier_images_sorted[1]
                    else:  # 20% chance for random within tier
                        return random.sample(tier_images, 2)
        
        # If no tier has 2+ images, try adjacent tiers
        for i in range(len(sorted_tiers) - 1):
            tier1, tier2 = sorted_tiers[i], sorted_tiers[i + 1]
            if abs(tier2 - tier1) <= 1:  # Adjacent tiers
                images1 = images_by_tier[tier1]
                images2 = images_by_tier[tier2]
                
                if images1 and images2:
                    # Pick highest priority from each tier
                    img1 = max(images1, key=lambda x: image_priorities[x])
                    img2 = max(images2, key=lambda x: image_priorities[x])
                    
                    # Check if this would recreate the excluded pair
                    if not (exclude_set and {img1, img2} == exclude_set):
                        return img1, img2
        
        # Fallback: pick the two highest priority images regardless of tier
        if image_priorities:
            sorted_by_priority = sorted(image_priorities.keys(), 
                                      key=lambda x: image_priorities[x], reverse=True)
            if len(sorted_by_priority) >= 2:
                # Find the first valid pair that doesn't match the excluded pair
                for i in range(len(sorted_by_priority)):
                    for j in range(i + 1, len(sorted_by_priority)):
                        img1, img2 = sorted_by_priority[i], sorted_by_priority[j]
                        if not (exclude_set and {img1, img2} == exclude_set):
                            return img1, img2
        
        # Ultimate fallback: random selection
        if len(voted_images) >= 2:
            # Keep trying random pairs until we find one that doesn't match excluded
            max_attempts = 10
            for _ in range(max_attempts):
                pair = random.sample(voted_images, 2)
                if not (exclude_set and set(pair) == exclude_set):
                    return pair[0], pair[1]
        
        return None, None
    
    def _calculate_priority_scores(self, images: List[str]) -> Dict[str, float]:
        """
        Calculate priority scores for each image based on multiple factors.
        
        Args:
            images: List of image filenames to calculate scores for
            
        Returns:
            Dictionary mapping image names to priority scores
        """
        if not images:
            return {}
        
        # Get current weights from data manager
        weights = self.data_manager.weights
        
        # Calculate maximum values for normalization
        max_votes = max(self.data_manager.get_image_stats(img).get('votes', 0) for img in images)
        max_stability = max(self._calculate_tier_stability(img) for img in images)
        vote_count = self.data_manager.vote_count
        
        # Calculate tier sizes
        tier_sizes = defaultdict(int)
        for img in images:
            tier = self.data_manager.get_image_stats(img).get('current_tier', 0)
            tier_sizes[tier] += 1
        max_tier_size = max(tier_sizes.values()) if tier_sizes else 1
        
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
            
            # Low vote score: higher = needs voting more (has fewer total votes)
            votes = stats.get('votes', 0)
            low_vote_score = 1 - (votes / (max_votes + 1))
            
            # Stability score: higher = less stable (needs more data)
            stability = self._calculate_tier_stability(img)
            stability_score = stability / (max_stability + 0.1)
            
            # Tier size score: higher = tier has more images (needs more sorting)
            current_tier = stats.get('current_tier', 0)
            tier_size_score = tier_sizes.get(current_tier, 1) / max_tier_size
            
            # Combined priority score (weighted average)
            priority = (weights['recency'] * recency_score + 
                       weights['low_votes'] * low_vote_score + 
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
            image1: First image in the pair
            image2: Second image in the pair
            
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
        
        # Both images have been voted on
        tier_diff = abs(tier1 - tier2)
        
        if tier_diff == 0:
            # Same tier comparison
            tier_size = sum(1 for img in self.data_manager.image_stats.keys() 
                          if self.data_manager.get_image_stats(img).get('current_tier', 0) == tier1)
            return f"Comparing images within Tier {tier1} ({tier_size} images in tier)"
        else:
            # Different tier comparison
            return f"Comparing Tier {tier1} vs Tier {tier2} (difference: {tier_diff})"
    
    def invalidate_cache(self):
        """Invalidate the cached rankings to force recalculation."""
        self._cached_rankings = None
        self._last_calculation_vote_count = -1