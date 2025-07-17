"""Ranking algorithm for intelligent pair selection based on tier overflow and confidence."""

import random
import statistics
import math
from typing import List, Tuple, Dict, Any, Optional, Set
from collections import defaultdict

from core.data_manager import DataManager


class RankingAlgorithm:
    """Implements intelligent pair selection based on tier overflow and image confidence."""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self._cached_rankings = None
        self._last_calculation_vote_count = -1
    
    def select_next_pair(self, available_images: List[str], 
                        exclude_pair: Optional[Tuple[str, str]] = None) -> Tuple[Optional[str], Optional[str]]:
        """Select next pair using tier overflow and confidence-based selection."""
        if len(available_images) < 2:
            return None, None
        
        # Find overflowing tiers
        overflowing_tiers = self._find_overflowing_tiers(available_images)
        
        if not overflowing_tiers:
            # If no overflowing tiers, fall back to random selection
            return self._fallback_random_selection(available_images, exclude_pair)
        
        # Select the most overflowing tier
        selected_tier = self._select_most_overflowing_tier(overflowing_tiers, available_images)
        
        # Get images in selected tier
        tier_images = [img for img in available_images 
                       if self.data_manager.get_image_stats(img).get('current_tier', 0) == selected_tier]
        
        if len(tier_images) < 2:
            return self._fallback_random_selection(available_images, exclude_pair)
        
        # Select left image (lowest confidence)
        left_image = self._select_lowest_confidence_image(selected_tier, tier_images)
        
        # Select right image (high confidence + low recency, excluding left)
        right_image = self._select_high_confidence_low_recency_image(
            selected_tier, tier_images, left_image, exclude_pair)
        
        if left_image and right_image and left_image != right_image:
            return left_image, right_image
        
        return self._fallback_random_selection(available_images, exclude_pair)
    
    def _find_overflowing_tiers(self, available_images: List[str]) -> List[int]:
        """Find tiers that have more images than expected based on normal distribution."""
        tier_counts = defaultdict(int)
        for img in available_images:
            tier = self.data_manager.get_image_stats(img).get('current_tier', 0)
            tier_counts[tier] += 1
        
        total_images = len(available_images)
        overflowing_tiers = []
        
        for tier, actual_count in tier_counts.items():
            expected_proportion = self._calculate_expected_tier_proportion(tier, total_images)
            expected_count = expected_proportion * total_images
            
            # Consider a tier overflowing if it has more than 120% of expected count
            if actual_count > expected_count * 1.2 and actual_count > 2:  # Need at least 2 images
                overflowing_tiers.append(tier)
        
        return overflowing_tiers
    
    def _select_most_overflowing_tier(self, overflowing_tiers: List[int], available_images: List[str]) -> int:
        """Select the most overflowing tier from the list."""
        if not overflowing_tiers:
            return 0
        
        # Calculate overflow amount for each tier
        tier_counts = defaultdict(int)
        for img in available_images:
            tier = self.data_manager.get_image_stats(img).get('current_tier', 0)
            tier_counts[tier] += 1
        
        total_images = len(available_images)
        max_overflow = 0
        most_overflowing_tier = overflowing_tiers[0]
        
        for tier in overflowing_tiers:
            actual_count = tier_counts[tier]
            expected_proportion = self._calculate_expected_tier_proportion(tier, total_images)
            expected_count = expected_proportion * total_images
            
            overflow_amount = actual_count - expected_count
            if overflow_amount > max_overflow:
                max_overflow = overflow_amount
                most_overflowing_tier = tier
        
        return most_overflowing_tier
    
    def _calculate_image_confidence(self, image_name: str) -> float:
        """Calculate confidence score for an image based on tier stability and vote count."""
        stats = self.data_manager.get_image_stats(image_name)
        
        # Get tier stability (standard deviation of tier history)
        tier_stability = self._calculate_tier_stability(image_name)
        
        # Get vote count
        votes = stats.get('votes', 0)
        
        # Calculate confidence components
        # Stability component: lower std dev = higher confidence
        # Invert and normalize stability (higher stability = lower confidence)
        stability_confidence = 1.0 / (1.0 + tier_stability)
        
        # Vote component: more votes = higher confidence
        # Normalize vote count with reasonable scaling
        vote_confidence = min(1.0, votes / 20.0)  # 20 votes = full confidence
        
        # Combine both components (equal weight)
        confidence = (stability_confidence + vote_confidence) / 2.0
        
        return confidence
    
    def _select_lowest_confidence_image(self, tier: int, tier_images: List[str]) -> Optional[str]:
        """Select the image with lowest confidence from the given tier."""
        if not tier_images:
            return None
        
        # Calculate confidence for each image
        confidence_scores = []
        for img in tier_images:
            confidence = self._calculate_image_confidence(img)
            confidence_scores.append((confidence, img))
        
        # Sort by confidence (lowest first)
        confidence_scores.sort(key=lambda x: x[0])
        
        # Return the lowest confidence image
        return confidence_scores[0][1]
    
    def _select_high_confidence_low_recency_image(self, tier: int, tier_images: List[str], 
                                                exclude_image: str, exclude_pair: Optional[Tuple[str, str]] = None) -> Optional[str]:
        """Select image with high confidence and low recency (not checked recently) from the tier."""
        if not tier_images:
            return None
        
        # Filter out excluded images
        available_images = [img for img in tier_images if img != exclude_image]
        
        if exclude_pair:
            exclude_set = set(exclude_pair)
            available_images = [img for img in available_images if img not in exclude_set]
        
        if not available_images:
            return None
        
        # Calculate combined score for each image
        scored_images = []
        current_vote_count = self.data_manager.vote_count
        
        for img in available_images:
            confidence = self._calculate_image_confidence(img)
            
            # Calculate time since last voted (higher = less recent = better)
            stats = self.data_manager.get_image_stats(img)
            last_voted = stats.get('last_voted', -1)
            
            if last_voted == -1:
                time_since_voted = current_vote_count + 1  # Never voted = maximum
            else:
                time_since_voted = current_vote_count - last_voted
            
            # Normalize time_since_voted to 0-1 range
            max_time = current_vote_count + 1
            time_factor = time_since_voted / max_time if max_time > 0 else 0
            
            # Combine confidence and time factor (equal weight)
            combined_score = (confidence + time_factor) / 2.0
            
            scored_images.append((combined_score, img))
        
        # Sort by combined score (highest first)
        scored_images.sort(key=lambda x: x[0], reverse=True)
        
        # Return the best scoring image
        return scored_images[0][1]
    
    def _fallback_random_selection(self, available_images: List[str], exclude_pair: Optional[Tuple[str, str]] = None) -> Tuple[Optional[str], Optional[str]]:
        """Fallback to random selection when tier-based selection fails."""
        if len(available_images) < 2:
            return None, None
        
        # Try random selection with exclusion
        exclude_set = set(exclude_pair) if exclude_pair else set()
        
        max_attempts = 10
        for _ in range(max_attempts):
            pair = random.sample(available_images, 2)
            if not exclude_set or set(pair) != exclude_set:
                return pair[0], pair[1]
        
        # If we can't avoid exclude_pair, just return any pair
        pair = random.sample(available_images, 2)
        return pair[0], pair[1]
    
    def _calculate_expected_tier_proportion(self, tier: int, total_images: int) -> float:
        """Calculate expected proportion of images in a tier based on normal distribution."""
        std_dev = self.data_manager.tier_distribution_std
        
        density = math.exp(-(tier ** 2) / (2 * std_dev ** 2))
        
        all_tiers = set()
        for stats in self.data_manager.image_stats.values():
            all_tiers.add(stats.get('current_tier', 0))
        
        total_density = sum(math.exp(-(t ** 2) / (2 * std_dev ** 2)) for t in all_tiers)
        
        return density / total_density if total_density > 0 else 0.0
    
    def _calculate_tier_stability(self, image_name: str) -> float:
        """Calculate the tier stability for a single image."""
        stats = self.data_manager.get_image_stats(image_name)
        tier_history = stats.get('tier_history', [0])
        
        if len(tier_history) <= 1:
            return 0.0
        
        return statistics.stdev(tier_history)
    
    def calculate_all_rankings(self) -> Dict[str, List[Tuple[str, Dict[str, Any]]]]:
        """Calculate rankings for all metrics."""
        current_vote_count = self.data_manager.vote_count
        if (self._cached_rankings is not None and 
            self._last_calculation_vote_count == current_vote_count):
            return self._cached_rankings
        
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
                          if stats.get('last_voted', -1) >= 0 else float('inf')),
                'confidence': self._calculate_image_confidence(img)
            }
            image_metrics[img] = metrics
        
        rankings = {
            'total_votes': sorted(image_metrics.items(), 
                                key=lambda x: x[1]['total_votes'], reverse=True),
            'win_rate': sorted(image_metrics.items(), 
                             key=lambda x: x[1]['win_rate'], reverse=True),
            'current_tier': sorted(image_metrics.items(), 
                                 key=lambda x: x[1]['current_tier'], reverse=True),
            'tier_stability': sorted(image_metrics.items(), 
                                   key=lambda x: x[1]['tier_stability']),
            'recency': sorted(image_metrics.items(), 
                            key=lambda x: x[1]['recency'], reverse=True),
            'confidence': sorted(image_metrics.items(), 
                               key=lambda x: x[1]['confidence'], reverse=True)
        }
        
        self._cached_rankings = rankings
        self._last_calculation_vote_count = current_vote_count
        
        return rankings
    
    def get_selection_explanation(self, image1: str, image2: str) -> str:
        """Generate explanation of why this pair was selected."""
        stats1 = self.data_manager.get_image_stats(image1)
        stats2 = self.data_manager.get_image_stats(image2)
        
        tier1 = stats1.get('current_tier', 0)
        tier2 = stats2.get('current_tier', 0)
        
        if tier1 == tier2:
            # Calculate confidence for both images
            confidence1 = self._calculate_image_confidence(image1)
            confidence2 = self._calculate_image_confidence(image2)
            
            # Get tier size information
            tier_size = sum(1 for img in self.data_manager.image_stats.keys() 
                          if self.data_manager.get_image_stats(img).get('current_tier', 0) == tier1)
            
            total_images = len(self.data_manager.image_stats)
            expected_proportion = self._calculate_expected_tier_proportion(tier1, total_images)
            expected_size = expected_proportion * total_images
            
            explanation = (f"Overflowing Tier {tier1} ({tier_size} images, expected ~{expected_size:.1f}): "
                          f"Left image (low confidence: {confidence1:.2f}) vs "
                          f"Right image (high confidence: {confidence2:.2f}, not recently voted)")
        else:
            explanation = f"Fallback selection: Left image from Tier {tier1}, Right image from Tier {tier2}"
        
        return explanation
      
    def invalidate_cache(self):
        """Invalidate the cached rankings to force recalculation."""
        self._cached_rankings = None
        self._last_calculation_vote_count = -1
