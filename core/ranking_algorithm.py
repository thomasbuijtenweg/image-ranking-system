"""Ranking algorithm for intelligent pair selection."""

import random
import statistics
import math
from typing import List, Tuple, Dict, Any, Optional, Set
from collections import defaultdict

from core.data_manager import DataManager


class RankingAlgorithm:
    """Implements intelligent pair selection for image ranking."""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self._cached_rankings = None
        self._last_calculation_vote_count = -1
    
    def select_next_pair(self, available_images: List[str], 
                        exclude_pair: Optional[Tuple[str, str]] = None) -> Tuple[Optional[str], Optional[str]]:
        """Select next pair using separate weights for left and right selection."""
        if len(available_images) < 2:
            return None, None
        
        exclude_set = set(exclude_pair) if exclude_pair else set()
        
        # All images are treated equally - no special handling for new images
        return self._select_tier_based_pair_with_weights(available_images, exclude_set)
    
    def _select_tier_based_pair_with_weights(self, available_images: List[str], 
                                           exclude_set: Set[str]) -> Tuple[Optional[str], Optional[str]]:
        """Select a pair using tier-based algorithm with separate left and right weights."""
        left_candidates = available_images[:]
        right_candidates = available_images[:]
        
        if len(left_candidates) == 0 or len(right_candidates) == 0:
            return None, None
        
        left_priorities = self._calculate_priority_scores(left_candidates, 'left')
        right_priorities = self._calculate_priority_scores(right_candidates, 'right')
        
        left_images_by_tier = defaultdict(list)
        right_images_by_tier = defaultdict(list)
        
        for img in left_candidates:
            if img in left_priorities:
                tier = self.data_manager.get_image_stats(img).get('current_tier', 0)
                left_images_by_tier[tier].append(img)
        
        for img in right_candidates:
            if img in right_priorities:
                tier = self.data_manager.get_image_stats(img).get('current_tier', 0)
                right_images_by_tier[tier].append(img)
        
        # Try same tier first (80% of the time)
        if random.random() < 0.8:
            pair = self._select_from_same_tier_with_weights(left_images_by_tier, right_images_by_tier, 
                                                           left_priorities, right_priorities, exclude_set)
            if pair[0] and pair[1]:
                return pair
        
        # Try adjacent tiers
        pair = self._select_from_adjacent_tiers_with_weights(left_images_by_tier, right_images_by_tier, 
                                                           left_priorities, right_priorities, exclude_set)
        if pair[0] and pair[1]:
            return pair
        
        # Fallback - pick highest priority from each weight set
        return self._select_highest_priorities_with_weights(left_priorities, right_priorities, exclude_set)
    
    def _select_from_same_tier_with_weights(self, left_images_by_tier: Dict[int, List[str]], 
                                          right_images_by_tier: Dict[int, List[str]],
                                          left_priorities: Dict[str, float], 
                                          right_priorities: Dict[str, float],
                                          exclude_set: Set[str]) -> Tuple[Optional[str], Optional[str]]:
        """Select images from the same tier using separate left/right weights."""
        common_tiers = set(left_images_by_tier.keys()) & set(right_images_by_tier.keys())
        
        if not common_tiers:
            return None, None
        
        sorted_tiers = sorted(common_tiers, key=lambda t: len(left_images_by_tier[t]) + len(right_images_by_tier[t]), reverse=True)
        
        for tier in sorted_tiers:
            left_tier_images = left_images_by_tier[tier]
            right_tier_images = right_images_by_tier[tier]
            
            if len(left_tier_images) >= 1 and len(right_tier_images) >= 1:
                left_sorted = sorted(left_tier_images, key=lambda x: left_priorities[x], reverse=True)
                right_sorted = sorted(right_tier_images, key=lambda x: right_priorities[x], reverse=True)
                
                for left_img in left_sorted[:3]:
                    for right_img in right_sorted[:3]:
                        if (left_img != right_img and 
                            not (exclude_set and {left_img, right_img} == exclude_set)):
                            return left_img, right_img
        
        return None, None
    
    def _select_from_adjacent_tiers_with_weights(self, left_images_by_tier: Dict[int, List[str]], 
                                               right_images_by_tier: Dict[int, List[str]],
                                               left_priorities: Dict[str, float], 
                                               right_priorities: Dict[str, float],
                                               exclude_set: Set[str]) -> Tuple[Optional[str], Optional[str]]:
        """Select images from adjacent tiers using separate left/right weights."""
        all_tiers = sorted(set(left_images_by_tier.keys()) | set(right_images_by_tier.keys()))
        
        for i in range(len(all_tiers) - 1):
            tier1, tier2 = all_tiers[i], all_tiers[i + 1]
            if abs(tier2 - tier1) <= 1:
                left_tier1 = left_images_by_tier.get(tier1, [])
                left_tier2 = left_images_by_tier.get(tier2, [])
                right_tier1 = right_images_by_tier.get(tier1, [])
                right_tier2 = right_images_by_tier.get(tier2, [])
                
                combinations = [
                    (left_tier1, right_tier2),
                    (left_tier2, right_tier1),
                    (left_tier1, right_tier1),
                    (left_tier2, right_tier2)
                ]
                
                for left_images, right_images in combinations:
                    if left_images and right_images:
                        left_img = max(left_images, key=lambda x: left_priorities.get(x, 0))
                        right_img = max(right_images, key=lambda x: right_priorities.get(x, 0))
                        
                        if (left_img != right_img and 
                            not (exclude_set and {left_img, right_img} == exclude_set)):
                            return left_img, right_img
        
        return None, None
    
    def _select_highest_priorities_with_weights(self, left_priorities: Dict[str, float], 
                                              right_priorities: Dict[str, float],
                                              exclude_set: Set[str]) -> Tuple[Optional[str], Optional[str]]:
        """Select highest priority images from each weight set."""
        if not left_priorities or not right_priorities:
            return None, None
        
        left_sorted = sorted(left_priorities.keys(), key=lambda x: left_priorities[x], reverse=True)
        right_sorted = sorted(right_priorities.keys(), key=lambda x: right_priorities[x], reverse=True)
        
        for left_img in left_sorted[:5]:
            for right_img in right_sorted[:5]:
                if (left_img != right_img and 
                    not (exclude_set and {left_img, right_img} == exclude_set)):
                    return left_img, right_img
        
        # Ultimate fallback
        all_images = list(set(left_priorities.keys()) | set(right_priorities.keys()))
        if len(all_images) >= 2:
            max_attempts = 10
            for _ in range(max_attempts):
                pair = random.sample(all_images, 2)
                if not (exclude_set and set(pair) == exclude_set):
                    return pair[0], pair[1]
        
        return None, None
    
    def _calculate_expected_tier_proportion(self, tier: int, total_images: int) -> float:
        """Calculate expected proportion of images in a tier based on normal distribution."""
        std_dev = self.data_manager.tier_distribution_std
        
        density = math.exp(-(tier ** 2) / (2 * std_dev ** 2))
        
        all_tiers = set()
        for stats in self.data_manager.image_stats.values():
            all_tiers.add(stats.get('current_tier', 0))
        
        total_density = sum(math.exp(-(t ** 2) / (2 * std_dev ** 2)) for t in all_tiers)
        
        return density / total_density if total_density > 0 else 0.0
    
    def _calculate_priority_scores(self, images: List[str], weight_set: str) -> Dict[str, float]:
        """Calculate priority scores for each image based on multiple factors."""
        if not images:
            return {}
        
        if weight_set == 'left':
            weights = self.data_manager.get_left_weights()
            preferences = self.data_manager.get_left_priority_preferences()
        elif weight_set == 'right':
            weights = self.data_manager.get_right_weights()
            preferences = self.data_manager.get_right_priority_preferences()
        else:
            raise ValueError(f"Invalid weight_set: {weight_set}. Must be 'left' or 'right'.")
        
        max_votes = max(self.data_manager.get_image_stats(img).get('votes', 0) for img in images)
        max_stability = max(self._calculate_tier_stability(img) for img in images)
        vote_count = self.data_manager.vote_count
        
        # Calculate tier sizes based on normal distribution
        tier_sizes = defaultdict(int)
        for img in images:
            tier = self.data_manager.get_image_stats(img).get('current_tier', 0)
            tier_sizes[tier] += 1
        
        total_images = len(images)
        
        tier_size_scores = {}
        for tier, actual_size in tier_sizes.items():
            expected_proportion = self._calculate_expected_tier_proportion(tier, total_images)
            expected_size = expected_proportion * total_images
            
            if expected_size > 0:
                overpopulation_ratio = actual_size / expected_size
                tier_size_scores[tier] = min(overpopulation_ratio, 3.0) / 3.0
            else:
                tier_size_scores[tier] = 0.0
        
        image_priorities = {}
        for img in images:
            stats = self.data_manager.get_image_stats(img)
            votes = stats.get('votes', 0)
            
            # Calculate component scores
            last_voted = stats.get('last_voted', -1)
            recency_score = ((vote_count - last_voted) / (vote_count + 1) 
                           if last_voted >= 0 else 1.0)
            
            if preferences.get('prioritize_high_votes', False):
                vote_score = votes / (max_votes + 1)
            else:
                vote_score = 1 - (votes / (max_votes + 1))
            
            stability = self._calculate_tier_stability(img)
            if preferences.get('prioritize_high_stability', False):
                stability_score = 1 - (stability / (max_stability + 0.1))
            else:
                stability_score = stability / (max_stability + 0.1)
            
            current_tier = stats.get('current_tier', 0)
            tier_size_score = tier_size_scores.get(current_tier, 0.0)
            
            priority = (weights['recency'] * recency_score + 
                       weights['low_votes'] * vote_score + 
                       weights['instability'] * stability_score +
                       weights['tier_size'] * tier_size_score)
            
            image_priorities[img] = priority
        
        return image_priorities
    
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
                          if stats.get('last_voted', -1) >= 0 else float('inf'))
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
                            key=lambda x: x[1]['recency'], reverse=True)
        }
        
        self._cached_rankings = rankings
        self._last_calculation_vote_count = current_vote_count
        
        return rankings
    
    def get_selection_explanation(self, image1: str, image2: str) -> str:
        """Generate explanation of why this pair was selected."""
        stats1 = self.data_manager.get_image_stats(image1)
        stats2 = self.data_manager.get_image_stats(image2)
        
        votes1 = stats1.get('votes', 0)
        votes2 = stats2.get('votes', 0)
        tier1 = stats1.get('current_tier', 0)
        tier2 = stats2.get('current_tier', 0)
        
        left_prefs = self.data_manager.get_left_priority_preferences()
        right_prefs = self.data_manager.get_right_priority_preferences()
        
        tier_diff = abs(tier1 - tier2)
        
        if tier_diff == 0:
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
            
            if tier_size > expected_size * 1.2:
                explanation += f" - Both from over-populated Tier {tier1} ({tier_size} images, expected ~{expected_size:.1f})"
            else:
                explanation += f" - Both from Tier {tier1} ({tier_size} images in tier)"
                
            return explanation
        else:
            return f"Left image selected from Tier {tier1} using left weights, right image selected from Tier {tier2} using right weights (tier difference: {tier_diff})"
      
    def invalidate_cache(self):
        """Invalidate the cached rankings to force recalculation."""
        self._cached_rankings = None
        self._last_calculation_vote_count = -1