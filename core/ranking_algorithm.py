"""Ranking algorithm for intelligent pair selection based on tier overflow and confidence - tier bounds system removed."""

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
        
        # Sort overflowing tiers by priority (lowest first)
        sorted_overflowing_tiers = sorted(overflowing_tiers)
        
        # Try each overflowing tier in order (lowest first)
        for selected_tier in sorted_overflowing_tiers:
            # Get images in selected tier
            tier_images = [img for img in active_images 
                        if self.data_manager.get_image_stats(img).get('current_tier', 0) == selected_tier]
            
            if len(tier_images) < 2:
                # Not enough images in this tier, try next tier
                continue
            
            # Check if this tier has any untested pairs available
            if not self._has_untested_pairs(tier_images, exclude_pair):
                # All pairs in this tier have been tested, skip to next tier
                continue
            
            # Try to find an untested pair from this tier
            max_attempts = min(50, len(tier_images) * (len(tier_images) - 1) // 2)
            
            for attempt in range(max_attempts):
                # Select left image (lowest confidence)
                left_image = self._select_lowest_confidence_image(selected_tier, tier_images)
                
                # Select right image (high confidence + low recency, excluding left)
                right_image = self._select_high_confidence_low_recency_image(
                    selected_tier, tier_images, left_image, exclude_pair)
                
                if left_image and right_image and left_image != right_image:
                    # Check if this pair has already been tested
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
                        # Not enough images left in this tier, move to next tier
                        break
            
            # If we found a valid pair in this tier, we would have returned already
            # Otherwise, continue to next tier
        
        # If we couldn't find an untested pair in any overflow tier, fall back to random
        return self._fallback_random_selection(active_images, exclude_pair)
    
    def _find_overflowing_tiers(self, active_images: List[str]) -> List[int]:
        """Find tiers that have more ACTIVE images than expected based on normal distribution.
        Uses dynamic mean centering for more adaptive tier management."""
        tier_counts = defaultdict(int)
        tier_list = []  # Keep track of all tiers for mean calculation
        
        for img in active_images:  # Only count active images
            tier = self.data_manager.get_image_stats(img).get('current_tier', 0)
            tier_counts[tier] += 1
            tier_list.append(tier)
        
        total_active_images = len(active_images)  # Use active image count
        overflowing_tiers = []
        
        # Calculate and display the current mean tier (for debugging/monitoring)
        if tier_list:
            mean_tier = sum(tier_list) / len(tier_list)
            # Optional: Log the dynamic mean for transparency
            if hasattr(self, '_last_logged_mean') and abs(self._last_logged_mean - mean_tier) > 0.5:
                print(f"Distribution center shifted to tier {mean_tier:.2f} (was {self._last_logged_mean:.2f})")
                self._last_logged_mean = mean_tier
            elif not hasattr(self, '_last_logged_mean'):
                print(f"Distribution centered at tier {mean_tier:.2f}")
                self._last_logged_mean = mean_tier
        
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
        """Select the most overflowing tier from the list - NOW PRIORITIZES LOWEST TIERS."""
        if not overflowing_tiers:
            return 0
        
        # CHANGED: Always select the LOWEST tier when multiple are overflowing
        # This ensures we focus on cleaning up low-tier images first for faster dataset reduction
        lowest_tier = min(overflowing_tiers)
        
        # Optional: Log which tier was selected for transparency
        if len(overflowing_tiers) > 1:
            print(f"Multiple tiers overflowing {overflowing_tiers}, selecting lowest: {lowest_tier} for low-tier focus")
        
        return lowest_tier
        
        # NOTE: Original logic below is kept commented for reference/easy rollback
        # The original logic selected the tier with the highest overflow amount
        # # Calculate overflow amount for each tier
        # tier_counts = defaultdict(int)
        # for img in active_images:  # Use active_images instead of available_images
        #     tier = self.data_manager.get_image_stats(img).get('current_tier', 0)
        #     tier_counts[tier] += 1
        # 
        # total_images = len(active_images)
        # max_overflow = 0
        # most_overflowing_tier = overflowing_tiers[0]
        # 
        # overflow_threshold = self.data_manager.algorithm_settings.overflow_threshold
        # 
        # for tier in overflowing_tiers:
        #     actual_count = tier_counts[tier]
        #     expected_proportion = self._calculate_expected_tier_proportion(tier, total_images)
        #     expected_count = expected_proportion * total_images * overflow_threshold
        #     
        #     overflow_amount = actual_count - expected_count
        #     if overflow_amount > max_overflow:
        #         max_overflow = overflow_amount
        #         most_overflowing_tier = tier
        # 
        # return most_overflowing_tier
    
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
        """Select image with low confidence, prioritizing under-tested images."""
        if not tier_images:
            return None
        
        current_vote_count = self.data_manager.vote_count
        min_votes_threshold = self.data_manager.algorithm_settings.min_votes_for_stability
        
        # Calculate combined score for each image
        combined_scores = []
        for img in tier_images:
            confidence = self._calculate_image_confidence(img)
            stats = self.data_manager.get_image_stats(img)
            votes = stats.get('votes', 0)
            tier_history = stats.get('tier_history', [0])
            
            # Calculate time since last voted (higher = less recent = better)
            last_voted = stats.get('last_voted', -1)
            
            if last_voted == -1:
                time_since_voted = current_vote_count + 1  # Never voted = maximum
            else:
                time_since_voted = current_vote_count - last_voted
            
            # Normalize time_since_voted to 0-1 range
            max_time = current_vote_count + 1
            time_factor = time_since_voted / max_time if max_time > 0 else 0
            
            # Calculate vote deficiency factor (prioritize under-tested images)
            # If votes < min_votes_threshold, boost priority
            if votes < min_votes_threshold:
                # Scale from 1.0 (0 votes) to 0.0 (min_votes_threshold)
                vote_deficiency = 1.0 - (votes / min_votes_threshold)
            else:
                # No boost for well-tested images
                vote_deficiency = 0.0
            
            # Calculate tier stability for detailed logging
            tier_stability = self._calculate_tier_stability(img)
            
            # Combine with weighted factors:
            # 50% inverted confidence (lower confidence = higher priority)
            # 20% recency (older = higher priority)  
            # 30% vote deficiency (fewer votes = higher priority)
            inverted_confidence = 1.0 - confidence
            
            combined_score = (inverted_confidence * 0.5) + (time_factor * 0.2) + (vote_deficiency * 0.3)
            
            combined_scores.append((combined_score, confidence, time_since_voted, votes, vote_deficiency, tier_stability, tier_history, img))
        
        # Sort by combined score (highest first = lowest confidence + least recent + fewest votes)
        combined_scores.sort(key=lambda x: x[0], reverse=True)
        
        # Log selection reasoning
        print("\n=== LEFT Image Selection (Low Confidence + Under-tested Priority) ===")
        print(f"Tier {tier} has {len(combined_scores)} candidates")
        print(f"Weight: 50% Confidence (inverted) + 20% Recency + 30% Vote Deficiency")
        print(f"Min votes threshold: {min_votes_threshold}\n")
        
        # Show top 3 candidates (selected + 2 runner-ups)
        top_candidates = combined_scores[:min(3, len(combined_scores))]
        for i, (score, conf, recency, votes, vote_def, tier_stab, tier_hist, img) in enumerate(top_candidates):
            status = "✓ SELECTED" if i == 0 else "  Runner-up"
            conf_contribution = (1.0 - conf) * 0.5
            recency_normalized = recency / max(1, current_vote_count + 1)
            recency_contribution = recency_normalized * 0.2
            vote_contribution = vote_def * 0.3
            
            under_tested_marker = " [UNDER-TESTED]" if votes < min_votes_threshold else ""
            
            print(f"{status} #{i+1}: {img}{under_tested_marker}")
            print(f"    Combined Score: {score:.4f}")
            
            # Detailed confidence calculation breakdown
            if votes > 0:
                effective_stability = tier_stab / math.sqrt(votes) if votes > 0 else 0
                print(f"    - Confidence: {conf:.4f}")
                print(f"        • Tier History: {tier_hist}")
                print(f"        • Tier Stability (stdev): {tier_stab:.4f}")
                print(f"        • Vote Count: {votes} → sqrt({votes}) = {math.sqrt(votes):.4f}")
                print(f"        • Effective Stability: {tier_stab:.4f} / {math.sqrt(votes):.4f} = {effective_stability:.4f}")
                print(f"        • Confidence Formula: 1 / (1 + {effective_stability:.4f}) = {conf:.4f}")
            else:
                print(f"    - Confidence: {conf:.4f} (0 votes = 0 confidence)")
            
            print(f"        → Inverted: {1.0-conf:.4f} → Contribution: {conf_contribution:.4f} (50%)")
            
            print(f"    - Recency: {recency} votes ago → Normalized: {recency_normalized:.4f} → Contribution: {recency_contribution:.4f} (20%)")
            print(f"    - Vote Count: {votes} votes → Deficiency: {vote_def:.4f} → Contribution: {vote_contribution:.4f} (30%)")
            
            if i == 0 and len(combined_scores) > 1:
                second_score = combined_scores[1][0]
                margin = score - second_score
                print(f"    ▶ Won by margin: {margin:.4f}")
            elif i > 0:
                winner_score = combined_scores[0][0]
                deficit = winner_score - score
                print(f"    ▶ Lost by margin: {deficit:.4f}")
            print()
        
        # Return the image with highest combined score
        return combined_scores[0][7]
    
    def _select_high_confidence_low_recency_image(self, tier: int, tier_images: List[str], 
                                                exclude_image: str, exclude_pair: Optional[Tuple[str, str]] = None) -> Optional[str]:
        """Select image with high confidence and low recency, prioritizing recency over confidence."""
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
            stats = self.data_manager.get_image_stats(img)
            votes = stats.get('votes', 0)
            tier_history = stats.get('tier_history', [0])
            
            # Calculate time since last voted (higher = less recent = better)
            last_voted = stats.get('last_voted', -1)
            
            if last_voted == -1:
                time_since_voted = current_vote_count + 1  # Never voted = maximum
            else:
                time_since_voted = current_vote_count - last_voted
            
            # Normalize time_since_voted to 0-1 range
            max_time = current_vote_count + 1
            time_factor = time_since_voted / max_time if max_time > 0 else 0
            
            # Calculate tier stability for detailed logging
            tier_stability = self._calculate_tier_stability(img)
            
            # Combine with 40% confidence and 60% recency (recency prioritized)
            combined_score = (confidence * 0.4) + (time_factor * 0.6)
            
            scored_images.append((combined_score, confidence, time_since_voted, votes, tier_stability, tier_history, img))
        
        # Sort by combined score (highest first)
        scored_images.sort(key=lambda x: x[0], reverse=True)
        
        # Log selection reasoning
        print("\n=== RIGHT Image Selection (Recency Priority + High Confidence) ===")
        print(f"Tier {tier} has {len(scored_images)} candidates (excluding LEFT image)")
        print(f"Weight: 40% Confidence + 60% Recency\n")
        
        # Show top 3 candidates (selected + 2 runner-ups)
        top_candidates = scored_images[:min(3, len(scored_images))]
        for i, (score, conf, recency, votes, tier_stab, tier_hist, img) in enumerate(top_candidates):
            status = "✓ SELECTED" if i == 0 else "  Runner-up"
            conf_contribution = conf * 0.4
            recency_normalized = recency / max(1, current_vote_count + 1)
            recency_contribution = recency_normalized * 0.6
            
            print(f"{status} #{i+1}: {img}")
            print(f"    Combined Score: {score:.4f}")
            
            # Detailed confidence calculation breakdown
            if votes > 0:
                effective_stability = tier_stab / math.sqrt(votes) if votes > 0 else 0
                print(f"    - Confidence: {conf:.4f}")
                print(f"        • Tier History: {tier_hist}")
                print(f"        • Tier Stability (stdev): {tier_stab:.4f}")
                print(f"        • Vote Count: {votes} → sqrt({votes}) = {math.sqrt(votes):.4f}")
                print(f"        • Effective Stability: {tier_stab:.4f} / {math.sqrt(votes):.4f} = {effective_stability:.4f}")
                print(f"        • Confidence Formula: 1 / (1 + {effective_stability:.4f}) = {conf:.4f}")
            else:
                print(f"    - Confidence: {conf:.4f} (0 votes = 0 confidence)")
            
            print(f"        → Contribution: {conf_contribution:.4f} (40%)")
            
            print(f"    - Recency: {recency} votes ago → Normalized: {recency_normalized:.4f} → Contribution: {recency_contribution:.4f} (60%)")
            
            if i == 0 and len(scored_images) > 1:
                second_score = scored_images[1][0]
                margin = score - second_score
                print(f"    ▶ Won by margin: {margin:.4f}")
            elif i > 0:
                winner_score = scored_images[0][0]
                deficit = winner_score - score
                print(f"    ▶ Lost by margin: {deficit:.4f}")
            print()
        
        print("=" * 60)
        
        # Return the best scoring image
        return scored_images[0][6]
    
    def _has_untested_pairs(self, tier_images: List[str], 
                           exclude_pair: Optional[Tuple[str, str]] = None) -> bool:
        """Check if a tier has any untested pairs available."""
        if len(tier_images) < 2:
            return False
        
        exclude_set = set(exclude_pair) if exclude_pair else set()
        
        # Check all possible pairs in this tier
        for i, img1 in enumerate(tier_images):
            for img2 in tier_images[i+1:]:
                # Skip the exclude_pair
                if exclude_set and {img1, img2} == exclude_set:
                    continue
                
                # If we find any untested pair, return True
                if not self.data_manager.has_pair_been_tested(img1, img2):
                    return True
        
        # No untested pairs found in this tier
        return False
    
    def _fallback_random_selection(self, active_images: List[str], 
                             exclude_pair: Optional[Tuple[str, str]] = None) -> Tuple[Optional[str], Optional[str]]:
        """Fallback to selecting least recently tested images when tier-based selection fails."""
        if len(active_images) < 2:
            return None, None
        
        exclude_set = set(exclude_pair) if exclude_pair else set()
        current_vote_count = self.data_manager.vote_count
        
        # Score all images by how long since they were last tested
        # Higher score = tested longer ago = higher priority
        image_recency_scores = []
        for img in active_images:
            stats = self.data_manager.get_image_stats(img)
            last_voted = stats.get('last_voted', -1)
            
            if last_voted == -1:
                # Never voted = maximum priority
                time_since_voted = current_vote_count + 1
            else:
                time_since_voted = current_vote_count - last_voted
            
            image_recency_scores.append((time_since_voted, img))
        
        # Sort by recency score (highest first = least recently tested)
        image_recency_scores.sort(key=lambda x: x[0], reverse=True)
        
        # Try to find an untested pair starting with least recently tested images
        for i, (score1, img1) in enumerate(image_recency_scores):
            for score2, img2 in image_recency_scores[i+1:]:
                # Skip excluded pair
                if exclude_set and {img1, img2} == exclude_set:
                    continue
                
                # Check if this pair has already been tested
                if not self.data_manager.has_pair_been_tested(img1, img2):
                    return img1, img2
        
        # If we can't find any untested pairs, select the least recently tested pair
        # This is very rare - only happens when most/all pairs have been tested
        print(f"Warning: All untested pairs exhausted, selecting least recently tested pair")
        
        # Get the two least recently tested images that aren't the exclude_pair
        for i, (score1, img1) in enumerate(image_recency_scores):
            for score2, img2 in image_recency_scores[i+1:]:
                if not exclude_set or {img1, img2} != exclude_set:
                    return img1, img2
        
        # Final fallback (should be extremely rare)
        if len(active_images) >= 2:
            pair = [image_recency_scores[0][1], image_recency_scores[1][1]]
            print(f"Final fallback: {pair[0]} vs {pair[1]}")
            return pair[0], pair[1]
        
        return None, None
    
    def _calculate_expected_tier_proportion(self, tier: int, total_active_images: int) -> float:
        """Calculate expected proportion of images in a tier based on normal distribution.
        Now dynamically centers the distribution on the actual mean tier of active images."""
        std_dev = self.data_manager.algorithm_settings.tier_distribution_std
        
        # Calculate the actual mean tier of active images
        active_tiers = []
        for img_name, stats in self.data_manager.image_stats.items():
            if not self.data_manager.is_image_binned(img_name):  # Only active images
                active_tiers.append(stats.get('current_tier', 0))
        
        if not active_tiers:
            return 0.0
        
        # Calculate mean tier (this is where the normal distribution should be centered)
        mean_tier = sum(active_tiers) / len(active_tiers)
        
        # Use dynamic mean for normal distribution calculation
        density = math.exp(-((tier - mean_tier) ** 2) / (2 * std_dev ** 2))
        
        # Only consider tiers that have active images
        all_tiers = set(active_tiers)
        
        # Calculate total density with dynamic mean
        total_density = sum(math.exp(-((t - mean_tier) ** 2) / (2 * std_dev ** 2)) for t in all_tiers)
        
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
        
        # Calculate current mean tier for display
        active_tiers = []
        for img_name, stats in self.data_manager.image_stats.items():
            if not self.data_manager.is_image_binned(img_name):
                active_tiers.append(stats.get('current_tier', 0))
        mean_tier = sum(active_tiers) / len(active_tiers) if active_tiers else 0
        
        # Get algorithm settings for explanation
        overflow_threshold = self.data_manager.algorithm_settings.overflow_threshold
        
        # Check if this pair has been tested before
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
                        f"threshold {overflow_threshold:.1f}x, center={mean_tier:.1f}): "
                        f"Left image ({breakdown1['votes']} votes, confidence: {breakdown1['confidence']:.3f}) vs "
                        f"Right image ({breakdown2['votes']} votes, confidence: {breakdown2['confidence']:.3f}) | "
                        f"{pair_status} | Coverage: {pair_stats['coverage_percentage']:.1f}%")
        else:
            explanation = (f"Fallback selection: Left image from Tier {tier1}, Right image from Tier {tier2} | "
                        f"{pair_status} | Coverage: {pair_stats['coverage_percentage']:.1f}%")
        
        return explanation
    
    def calculate_all_rankings(self) -> Dict[str, List[Tuple[str, Dict[str, Any]]]]:
        """
        Calculate comprehensive rankings for all images.
        
        Returns:
            Dictionary with different ranking types
        """
        try:
            active_images = self.data_manager.get_active_images()
            
            if not active_images:
                return {
                    'current_tier': [],
                    'win_rate': [],
                    'confidence': [],
                    'stability': []
                }
            
            # Prepare image metrics
            image_metrics = []
            
            for img_name in active_images:
                stats = self.data_manager.get_image_stats(img_name)
                
                # Basic stats
                votes = stats.get('votes', 0)
                wins = stats.get('wins', 0)
                current_tier = stats.get('current_tier', 0)
                
                # Calculated metrics
                win_rate = wins / votes if votes > 0 else 0
                confidence = self._calculate_image_confidence(img_name)
                stability = self._calculate_tier_stability(img_name)
                
                image_metrics.append({
                    'name': img_name,
                    'current_tier': current_tier,
                    'total_votes': votes,
                    'wins': wins,
                    'win_rate': win_rate,
                    'confidence': confidence,
                    'tier_stability': stability
                })
            
            # Create different rankings
            rankings = {}
            
            # By current tier (highest first)
            rankings['current_tier'] = sorted(
                [(img['name'], img) for img in image_metrics],
                key=lambda x: x[1]['current_tier'],
                reverse=True
            )
            
            # By win rate (highest first)
            rankings['win_rate'] = sorted(
                [(img['name'], img) for img in image_metrics],
                key=lambda x: x[1]['win_rate'],
                reverse=True
            )
            
            # By confidence (highest first)
            rankings['confidence'] = sorted(
                [(img['name'], img) for img in image_metrics],
                key=lambda x: x[1]['confidence'],
                reverse=True
            )
            
            # By stability (lowest first - most stable)
            rankings['stability'] = sorted(
                [(img['name'], img) for img in image_metrics],
                key=lambda x: x[1]['tier_stability']
            )
            
            return rankings
            
        except Exception as e:
            print(f"Error calculating rankings: {e}")
            return {
                'current_tier': [],
                'win_rate': [],
                'confidence': [],
                'stability': []
            }
    
    def get_distribution_stats(self) -> Dict[str, Any]:
        """Get statistics about the current tier distribution."""
        active_tiers = []
        tier_counts = defaultdict(int)
        
        for img_name, stats in self.data_manager.image_stats.items():
            if not self.data_manager.is_image_binned(img_name):
                tier = stats.get('current_tier', 0)
                active_tiers.append(tier)
                tier_counts[tier] += 1
        
        if not active_tiers:
            return {
                'mean_tier': 0,
                'median_tier': 0,
                'std_dev': 0,
                'min_tier': 0,
                'max_tier': 0,
                'total_active': 0,
                'tier_distribution': {}
            }
        
        # Calculate statistics
        mean_tier = sum(active_tiers) / len(active_tiers)
        median_tier = statistics.median(active_tiers)
        std_dev = statistics.stdev(active_tiers) if len(active_tiers) > 1 else 0
        
        # Find overflowing tiers
        overflowing = self._find_overflowing_tiers([img for img in self.data_manager.image_stats.keys()
                                                     if not self.data_manager.is_image_binned(img)])
        
        return {
            'mean_tier': round(mean_tier, 2),
            'median_tier': median_tier,
            'std_dev': round(std_dev, 2),
            'min_tier': min(active_tiers),
            'max_tier': max(active_tiers),
            'total_active': len(active_tiers),
            'tier_distribution': dict(tier_counts),
            'overflowing_tiers': overflowing,
            'distribution_center': round(mean_tier, 2)  # Explicitly show where normal distribution is centered
        }
