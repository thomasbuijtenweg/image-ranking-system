"""Ranking algorithm for intelligent pair selection based on tier overflow and confidence."""

import random
import math
import statistics
from typing import List, Tuple, Dict, Any, Optional, Set
from collections import defaultdict

from core.data_manager import DataManager
from core.confidence_calculator import ConfidenceCalculator


class RankingAlgorithm:
    """Implements intelligent pair selection based on tier overflow and image confidence."""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.confidence_calculator = ConfidenceCalculator(data_manager)
    
    def select_next_pair(self, available_images: List[str], 
                    exclude_pair: Optional[Tuple[str, str]] = None) -> Tuple[Optional[str], Optional[str]]:
        """Select next pair using tier overflow and confidence-based selection, avoiding tested pairs."""
    
        # Filter out binned images
        active_images = [img for img in available_images 
                        if not self.data_manager.is_image_binned(img)]
        
        if len(active_images) < 2:
            return None, None
        
        # Find overflowing tiers (using only active images)
        overflowing_tiers = self._find_overflowing_tiers(active_images)
        
        if not overflowing_tiers:
            # If no overflowing tiers, fall back to random selection
            return self._fallback_random_selection(active_images, exclude_pair)
        
        # Select the most overflowing tier
        selected_tier = self._select_most_overflowing_tier(overflowing_tiers, active_images)
        
        # Get images in selected tier
        tier_images = [img for img in active_images 
                    if self.data_manager.get_image_stats(img).get('current_tier', 0) == selected_tier]
        
        if len(tier_images) < 2:
            return self._fallback_random_selection(active_images, exclude_pair)
        
        # Try to find an untested pair from this tier
        max_attempts = min(50, len(tier_images) * (len(tier_images) - 1) // 2)
        
        for attempt in range(max_attempts):
            # Select left image (lowest confidence)
            left_image = self._select_lowest_confidence_image(selected_tier, tier_images)
            
            # Select right image (high confidence + low recency, excluding left)
            right_image = self._select_high_confidence_low_recency_image(
                selected_tier, tier_images, left_image, exclude_pair)
            
            if left_image and right_image and left_image != right_image:
                # NEW: Check if this pair has already been tested
                if not self.data_manager.has_pair_been_tested(left_image, right_image):
                    # Also check exclude_pair
                    if not exclude_pair or {left_image, right_image} != set(exclude_pair):
                        return left_image, right_image
                
                # If this pair was already tested, remove these images from consideration and try again
                if left_image in tier_images:
                    tier_images.remove(left_image)
                if right_image in tier_images:
                    tier_images.remove(right_image)
                
                if len(tier_images) < 2:
                    break
    
        # If we couldn't find an untested pair in overflow tier, try random
        return self._fallback_random_selection(active_images, exclude_pair)
    
    def _find_overflowing_tiers(self, active_images: List[str]) -> List[int]:
        """Find tiers that have more ACTIVE images than expected based on normal distribution."""
        tier_counts = defaultdict(int)
        for img in active_images:  # Only count active images
            tier = self.data_manager.get_image_stats(img).get('current_tier', 0)
            tier_counts[tier] += 1
        
        total_active_images = len(active_images)  # Use active image count
        overflowing_tiers = []
        
        # Get overflow settings from algorithm_settings
        overflow_threshold = self.data_manager.algorithm_settings.overflow_threshold
        min_overflow_images = self.data_manager.algorithm_settings.min_overflow_images
        
        for tier, actual_count in tier_counts.items():
            expected_proportion = self._calculate_expected_tier_proportion(tier, total_active_images)
            expected_count = expected_proportion * total_active_images
            
            # Consider a tier overflowing if it has more than the threshold percentage of expected count
            # and has at least the minimum number of images
            if (actual_count > expected_count * overflow_threshold and 
                actual_count >= min_overflow_images):
                overflowing_tiers.append(tier)
        
        return overflowing_tiers
    
    def _select_most_overflowing_tier(self, overflowing_tiers: List[int], active_images: List[str]) -> int:
        """Select the most overflowing tier from the list."""
        if not overflowing_tiers:
            return 0
        
        # Calculate overflow amount for each tier
        tier_counts = defaultdict(int)
        for img in active_images:  # Use active_images instead of available_images
            tier = self.data_manager.get_image_stats(img).get('current_tier', 0)
            tier_counts[tier] += 1
        
        total_images = len(active_images)
        max_overflow = 0
        most_overflowing_tier = overflowing_tiers[0]
        
        overflow_threshold = self.data_manager.algorithm_settings.overflow_threshold
        
        for tier in overflowing_tiers:
            actual_count = tier_counts[tier]
            expected_proportion = self._calculate_expected_tier_proportion(tier, total_images)
            expected_count = expected_proportion * total_images * overflow_threshold
            
            overflow_amount = actual_count - expected_count
            if overflow_amount > max_overflow:
                max_overflow = overflow_amount
                most_overflowing_tier = tier
        
        return most_overflowing_tier
    
    def _calculate_image_confidence(self, image_name: str) -> float:
        """Calculate confidence score for an image based on tier stability and vote count."""
        return self.confidence_calculator.calculate_image_confidence(image_name)
    
    def _calculate_stability_confidence(self, image_name: str) -> float:
        """Calculate stability confidence using simplified square root approach."""
        stats = self.data_manager.get_image_stats(image_name)
        votes = stats.get('votes', 0)
        
        if votes == 0:
            return 0.0  # No confidence for untested images
        
        tier_stability = self._calculate_tier_stability(image_name)
        effective_stability = tier_stability / math.sqrt(votes)
        
        return 1.0 / (1.0 + effective_stability)
    
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
    
    def _fallback_random_selection(self, active_images: List[str], 
                             exclude_pair: Optional[Tuple[str, str]] = None) -> Tuple[Optional[str], Optional[str]]:
        """Fallback to random selection when tier-based selection fails, avoiding tested pairs."""
        if len(active_images) < 2:
            return None, None
        
        exclude_set = set(exclude_pair) if exclude_pair else set()
        
        # Try to find an untested pair
        max_attempts = min(100, len(active_images) * (len(active_images) - 1) // 2)
        
        for _ in range(max_attempts):
            pair = random.sample(active_images, 2)
            img1, img2 = pair
            
            # Skip excluded pair
            if set(pair) == exclude_set:
                continue
            
            # NEW: Check if this pair has already been tested
            if not self.data_manager.has_pair_been_tested(img1, img2):
                return img1, img2
        
        # If we can't find any untested pairs, return any valid pair
        # This should be very rare - only happens when most pairs have been tested
        for _ in range(10):
            pair = random.sample(active_images, 2)
            if not exclude_set or set(pair) != exclude_set:
                print(f"Warning: All pairs may have been tested, returning tested pair: {pair[0]} vs {pair[1]}")
                return pair[0], pair[1]
        
        # Final fallback
        pair = random.sample(active_images, 2)
        print(f"Final fallback: {pair[0]} vs {pair[1]}")
        return pair[0], pair[1]
    
    def _calculate_expected_tier_proportion(self, tier: int, total_active_images: int) -> float:
        """Calculate expected proportion of images in a tier based on normal distribution."""
        std_dev = self.data_manager.algorithm_settings.tier_distribution_std
        
        density = math.exp(-(tier ** 2) / (2 * std_dev ** 2))
        
        # Only consider tiers that have active images
        all_tiers = set()
        for img_name, stats in self.data_manager.image_stats.items():
            if not self.data_manager.is_image_binned(img_name):  # Only active images
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
    
    def get_selection_explanation(self, image1: str, image2: str) -> str:
        """Generate explanation of why this pair was selected."""
        stats1 = self.data_manager.get_image_stats(image1)
        stats2 = self.data_manager.get_image_stats(image2)
        
        tier1 = stats1.get('current_tier', 0)
        tier2 = stats2.get('current_tier', 0)
        
        # Get algorithm settings for explanation
        overflow_threshold = self.data_manager.algorithm_settings.overflow_threshold
        
        # NEW: Check if this pair has been tested before
        has_been_tested = self.data_manager.has_pair_been_tested(image1, image2)
        pair_status = "⚠️ Previously tested" if has_been_tested else "✅ Fresh pair"
        
        # Get overall pair statistics
        pair_stats = self.data_manager.get_pair_stats()
        
        if tier1 == tier2:
            # Get detailed confidence breakdown
            breakdown1 = self.confidence_calculator.get_confidence_breakdown(image1)
            breakdown2 = self.confidence_calculator.get_confidence_breakdown(image2)
            
            # Get tier size information
            tier_size = sum(1 for img in self.data_manager.image_stats.keys() 
                        if self.data_manager.get_image_stats(img).get('current_tier', 0) == tier1
                        and not self.data_manager.is_image_binned(img))
            
            total_images = len(self.data_manager.get_active_images())
            expected_proportion = self._calculate_expected_tier_proportion(tier1, total_images)
            expected_size = expected_proportion * total_images
            
            explanation = (f"Overflowing Tier {tier1} ({tier_size} images, expected ~{expected_size:.1f}, "
                        f"threshold {overflow_threshold:.1f}x): "
                        f"Left image ({breakdown1['votes']} votes, confidence: {breakdown1['confidence']:.3f}) vs "
                        f"Right image ({breakdown2['votes']} votes, confidence: {breakdown2['confidence']:.3f}) | "
                        f"{pair_status} | Coverage: {pair_stats['coverage_percentage']:.1f}%")
        else:
            explanation = (f"Fallback selection: Left image from Tier {tier1}, Right image from Tier {tier2} | "
                        f"{pair_status} | Coverage: {pair_stats['coverage_percentage']:.1f}%")
        
        return explanation