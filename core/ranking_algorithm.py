"""Ranking algorithm for intelligent pair selection with binning support."""

import random
import math
import statistics
from typing import List, Tuple, Dict, Any, Optional, Set
from collections import defaultdict

from core.data_manager import DataManager
from core.confidence_calculator import ConfidenceCalculator


class RankingAlgorithm:
    """Implements intelligent pair selection based on tier overflow and image confidence with binning support."""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.confidence_calculator = ConfidenceCalculator(data_manager)
        self._cached_rankings = None
        self._last_calculation_vote_count = -1
    
    def select_next_pair(self, available_images: List[str], 
                        exclude_pair: Optional[Tuple[str, str]] = None) -> Tuple[Optional[str], Optional[str]]:
        """Select next pair using tier overflow and confidence-based selection (excludes binned images)."""
        # Filter out binned images
        voteable_images = [img for img in available_images if not self.data_manager.is_image_binned(img)]
        
        if len(voteable_images) < 2:
            print(f"Not enough voteable images: {len(voteable_images)} available (excluding {len(self.data_manager.get_binned_images())} binned)")
            return None, None
        
        # Find overflowing tiers (excluding binned images)
        overflowing_tiers = self._find_overflowing_tiers(voteable_images)
        
        if not overflowing_tiers:
            # If no overflowing tiers, fall back to random selection
            return self._fallback_random_selection(voteable_images, exclude_pair)
        
        # Select the most overflowing tier
        selected_tier = self._select_most_overflowing_tier(overflowing_tiers, voteable_images)
        
        # Get images in selected tier (excluding binned)
        tier_images = [img for img in voteable_images 
                       if self.data_manager.get_image_stats(img).get('current_tier', 0) == selected_tier]
        
        if len(tier_images) < 2:
            return self._fallback_random_selection(voteable_images, exclude_pair)
        
        # Select left image (lowest confidence)
        left_image = self._select_lowest_confidence_image(selected_tier, tier_images)
        
        # Select right image (high confidence + low recency, excluding left)
        right_image = self._select_high_confidence_low_recency_image(
            selected_tier, tier_images, left_image, exclude_pair)
        
        if left_image and right_image and left_image != right_image:
            # Double-check that neither image is binned
            if not self.data_manager.is_image_binned(left_image) and not self.data_manager.is_image_binned(right_image):
                return left_image, right_image
        
        return self._fallback_random_selection(voteable_images, exclude_pair)
    
    def _find_overflowing_tiers(self, available_images: List[str]) -> List[int]:
        """Find tiers that have more images than expected based on normal distribution (excludes binned images)."""
        # Only consider non-binned images
        voteable_images = [img for img in available_images if not self.data_manager.is_image_binned(img)]
        
        tier_counts = defaultdict(int)
        for img in voteable_images:
            tier = self.data_manager.get_image_stats(img).get('current_tier', 0)
            tier_counts[tier] += 1
        
        total_images = len(voteable_images)
        overflowing_tiers = []
        
        # Get overflow settings
        overflow_threshold = getattr(self.data_manager, 'overflow_threshold', 1.0)
        min_overflow_images = getattr(self.data_manager, 'min_overflow_images', 2)
        
        for tier, actual_count in tier_counts.items():
            expected_proportion = self._calculate_expected_tier_proportion(tier, total_images)
            expected_count = expected_proportion * total_images
            
            # Consider a tier overflowing if it has more than the threshold percentage of expected count
            # and has at least the minimum number of images
            if (actual_count > expected_count * overflow_threshold and 
                actual_count >= min_overflow_images):
                overflowing_tiers.append(tier)
        
        return overflowing_tiers
    
    def _select_most_overflowing_tier(self, overflowing_tiers: List[int], available_images: List[str]) -> int:
        """Select the most overflowing tier from the list (excludes binned images)."""
        if not overflowing_tiers:
            return 0
        
        # Only consider non-binned images
        voteable_images = [img for img in available_images if not self.data_manager.is_image_binned(img)]
        
        # Calculate overflow amount for each tier
        tier_counts = defaultdict(int)
        for img in voteable_images:
            tier = self.data_manager.get_image_stats(img).get('current_tier', 0)
            tier_counts[tier] += 1
        
        total_images = len(voteable_images)
        max_overflow = 0
        most_overflowing_tier = overflowing_tiers[0]
        
        overflow_threshold = getattr(self.data_manager, 'overflow_threshold', 1.0)
        
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
        # Don't calculate confidence for binned images - they shouldn't be selected
        if self.data_manager.is_image_binned(image_name):
            return 1.0  # High confidence to avoid selection
        
        return self.confidence_calculator.calculate_image_confidence(image_name)
    
    def _calculate_stability_confidence(self, image_name: str) -> float:
        """Calculate stability confidence using simplified square root approach."""
        # Don't calculate for binned images
        if self.data_manager.is_image_binned(image_name):
            return 1.0
        
        stats = self.data_manager.get_image_stats(image_name)
        votes = stats.get('votes', 0)
        
        if votes == 0:
            return 0.0  # No confidence for untested images
        
        tier_stability = self._calculate_tier_stability(image_name)
        effective_stability = tier_stability / math.sqrt(votes)
        
        return 1.0 / (1.0 + effective_stability)
    
    def _select_lowest_confidence_image(self, tier: int, tier_images: List[str]) -> Optional[str]:
        """Select the image with lowest confidence from the given tier (excludes binned images)."""
        # Filter out binned images
        voteable_tier_images = [img for img in tier_images if not self.data_manager.is_image_binned(img)]
        
        if not voteable_tier_images:
            return None
        
        # Calculate confidence for each image
        confidence_scores = []
        for img in voteable_tier_images:
            confidence = self._calculate_image_confidence(img)
            confidence_scores.append((confidence, img))
        
        # Sort by confidence (lowest first)
        confidence_scores.sort(key=lambda x: x[0])
        
        # Return the lowest confidence image
        return confidence_scores[0][1]
    
    def _select_high_confidence_low_recency_image(self, tier: int, tier_images: List[str], 
                                                exclude_image: str, exclude_pair: Optional[Tuple[str, str]] = None) -> Optional[str]:
        """Select image with high confidence and low recency from the tier (excludes binned images)."""
        # Filter out binned images and excluded image
        available_images = [img for img in tier_images 
                           if (not self.data_manager.is_image_binned(img) and img != exclude_image)]
        
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
        """Fallback to random selection when tier-based selection fails (excludes binned images)."""
        # Filter out binned images
        voteable_images = [img for img in available_images if not self.data_manager.is_image_binned(img)]
        
        if len(voteable_images) < 2:
            return None, None
        
        # Try random selection with exclusion
        exclude_set = set(exclude_pair) if exclude_pair else set()
        
        max_attempts = 10
        for _ in range(max_attempts):
            pair = random.sample(voteable_images, 2)
            if not exclude_set or set(pair) != exclude_set:
                return pair[0], pair[1]
        
        # If we can't avoid exclude_pair, just return any pair
        pair = random.sample(voteable_images, 2)
        return pair[0], pair[1]
    
    def _calculate_expected_tier_proportion(self, tier: int, total_images: int) -> float:
        """Calculate expected proportion of images in a tier based on normal distribution."""
        std_dev = getattr(self.data_manager, 'tier_distribution_std', 1.5)
        
        density = math.exp(-(tier ** 2) / (2 * std_dev ** 2))
        
        # Only consider non-binned images for tier calculations
        available_images = self.data_manager.get_available_images()
        all_tiers = set()
        for img in available_images:
            stats = self.data_manager.get_image_stats(img)
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
        """Calculate rankings for all metrics (includes binned images but marks them)."""
        current_vote_count = self.data_manager.vote_count
        if (self._cached_rankings is not None and 
            self._last_calculation_vote_count == current_vote_count):
            return self._cached_rankings
        
        image_metrics = {}
        
        # Include all images (both available and binned) in rankings
        for img, stats in self.data_manager.image_stats.items():
            individual_stability = self._calculate_tier_stability(img)
            is_binned = self.data_manager.is_image_binned(img)
            
            metrics = {
                'filename': img,
                'total_votes': stats.get('votes', 0),
                'win_rate': (stats.get('wins', 0) / stats.get('votes', 1) 
                           if stats.get('votes', 0) > 0 else 0),
                'current_tier': stats.get('current_tier', 0),
                'tier_stability': individual_stability,
                'recency': (current_vote_count - stats.get('last_voted', -1) 
                          if stats.get('last_voted', -1) >= 0 else float('inf')),
                'confidence': self._calculate_image_confidence(img),
                'is_binned': is_binned,
                'binned_display': "🗑️ BINNED" if is_binned else ""
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
        # Check for binned images
        img1_binned = self.data_manager.is_image_binned(image1)
        img2_binned = self.data_manager.is_image_binned(image2)
        
        if img1_binned or img2_binned:
            return f"Warning: Selected pair contains binned image(s) - this shouldn't happen!"
        
        stats1 = self.data_manager.get_image_stats(image1)
        stats2 = self.data_manager.get_image_stats(image2)
        
        tier1 = stats1.get('current_tier', 0)
        tier2 = stats2.get('current_tier', 0)
        
        # Get algorithm settings for explanation
        overflow_threshold = getattr(self.data_manager, 'overflow_threshold', 1.0)
        
        if tier1 == tier2:
            # Get detailed confidence breakdown
            breakdown1 = self.confidence_calculator.get_confidence_breakdown(image1)
            breakdown2 = self.confidence_calculator.get_confidence_breakdown(image2)
            
            # Get tier size information (excluding binned images)
            available_images = self.data_manager.get_available_images()
            tier_size = sum(1 for img in available_images 
                          if self.data_manager.get_image_stats(img).get('current_tier', 0) == tier1)
            
            total_images = len(available_images)
            expected_proportion = self._calculate_expected_tier_proportion(tier1, total_images)
            expected_size = expected_proportion * total_images
            
            explanation = (f"Overflowing Tier {tier1} ({tier_size} images, expected ~{expected_size:.1f}, "
                          f"threshold {overflow_threshold:.1f}x): "
                          f"Left image ({breakdown1['votes']} votes, confidence: {breakdown1['confidence']:.3f}) vs "
                          f"Right image ({breakdown2['votes']} votes, confidence: {breakdown2['confidence']:.3f}, not recently voted)")
        else:
            explanation = f"Fallback selection: Left image from Tier {tier1}, Right image from Tier {tier2}"
        
        # Add binning status note
        binned_count = len(self.data_manager.get_binned_images())
        if binned_count > 0:
            explanation += f" | {binned_count} images binned"
        
        return explanation
      
    def invalidate_cache(self):
        """Invalidate the cached rankings to force recalculation."""
        self._cached_rankings = None
        self._last_calculation_vote_count = -1
    
    def get_algorithm_summary(self) -> Dict[str, Any]:
        """Get a summary of current algorithm settings."""
        available_images = self.data_manager.get_available_images()
        binned_images = self.data_manager.get_binned_images()
        
        return {
            'tier_distribution_std': getattr(self.data_manager, 'tier_distribution_std', 1.5),
            'overflow_threshold': getattr(self.data_manager, 'overflow_threshold', 1.0),
            'min_overflow_images': getattr(self.data_manager, 'min_overflow_images', 2),
            'algorithm_type': 'tier_overflow_confidence_sqrt_pure_with_binning',
            'version': '2.3',
            'available_images': len(available_images),
            'binned_images': len(binned_images),
            'total_images': len(available_images) + len(binned_images)
        }
    
    def get_available_image_count(self) -> int:
        """Get the number of images available for voting (excluding binned)."""
        return len(self.data_manager.get_available_images())
    
    def get_binned_image_count(self) -> int:
        """Get the number of binned images."""
        return len(self.data_manager.get_binned_images())
    
    def can_select_pairs(self) -> bool:
        """Check if there are enough available images to select pairs."""
        return self.get_available_image_count() >= 2
