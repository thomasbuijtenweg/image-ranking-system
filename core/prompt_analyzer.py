"""Prompt analysis for the Image Ranking System with binning support and word combination analysis."""

import re
import os
import statistics
from typing import Dict, List, Tuple, Any
from collections import defaultdict

from core.data_manager import DataManager


class PromptAnalyzer:
    """Analyzes prompt text to find correlations between words and image tiers, including word combinations."""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.rare_word_threshold = 3
    
    def extract_main_prompt(self, full_prompt: str) -> str:
        """Extract the main/positive prompt from the full prompt text."""
        if not full_prompt:
            return ""
        
        separators = [
            'negative prompt:',
            'negative:',
            'neg:',
            'steps:',
            'cfg scale:',
            'sampler:',
            'seed:',
            'model:',
            'clip skip:',
            'denoising strength:',
            'parameters:',
            '\nsteps:',
            '\ncfg',
            '\nsampler',
            '\nseed',
            '\nmodel'
        ]
        
        lower_prompt = full_prompt.lower()
        main_prompt = full_prompt
        
        earliest_pos = len(full_prompt)
        for separator in separators:
            pos = lower_prompt.find(separator)
            if pos != -1 and pos < earliest_pos:
                earliest_pos = pos
        
        if earliest_pos < len(full_prompt):
            main_prompt = full_prompt[:earliest_pos]
        
        return main_prompt.strip()
    
    def extract_words(self, prompt_text: str) -> List[str]:
        """Extract individual words from prompt text."""
        if not prompt_text:
            return []
        
        cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', ' ', prompt_text)
        words = cleaned_text.lower().split()
        words = [word for word in words if len(word) > 1]
        
        return words
    
    def analyze_word_performance(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze word performance with separate handling for active and binned images.
        
        Returns:
            Dictionary with enhanced word statistics including binning data
        """
        active_word_data = defaultdict(list)  # tier data for active images
        binned_word_data = defaultdict(int)   # frequency count for binned images
        
        for image_name, stats in self.data_manager.image_stats.items():
            prompt = stats.get('prompt')
            if not prompt:
                continue
            
            main_prompt = self.extract_main_prompt(prompt)
            words = self.extract_words(main_prompt)
            
            if self.data_manager.is_image_binned(image_name):
                # Binned images: just count word frequency
                for word in set(words):
                    binned_word_data[word] += 1
            else:
                # Active images: full tier analysis
                current_tier = stats.get('current_tier', 0)
                for word in set(words):
                    active_word_data[word].append(current_tier)
        
        # Also check binned images in the Bin folder for additional prompts
        # NOTE: This requires image_processor to be passed to PromptAnalyzer or accessed via data_manager
        # For now, this section is commented out. The binning analysis will still work for all images
        # that have been tracked in image_stats (which should be all images that were voted on)
        
        # if self.data_manager.image_folder and hasattr(self, 'image_processor'):
        #     binned_files = self.image_processor.get_binned_image_files(
        #         self.data_manager.image_folder)
        #     
        #     for binned_file in binned_files:
        #         if binned_file not in self.data_manager.image_stats:
        #             # This handles binned images that might not be in our stats
        #             try:
        #                 bin_folder = os.path.join(self.data_manager.image_folder, "Bin")
        #                 binned_path = os.path.join(bin_folder, binned_file)
        #                 prompt = self.image_processor.extract_prompt_from_image(binned_path)
        #                 
        #                 if prompt:
        #                     main_prompt = self.extract_main_prompt(prompt)
        #                     words = self.extract_words(main_prompt)
        #                     for word in set(words):
        #                         binned_word_data[word] += 1
        #             except Exception as e:
        #                 print(f"Error processing binned image {binned_file}: {e}")
        
        # Combine the analysis
        word_analysis = {}
        all_words = set(active_word_data.keys()) | set(binned_word_data.keys())
        
        for word in all_words:
            active_tiers = active_word_data.get(word, [])
            binned_count = binned_word_data.get(word, 0)
            
            # Calculate active image statistics
            active_frequency = len(active_tiers)
            average_tier = statistics.mean(active_tiers) if active_tiers else 0
            std_deviation = statistics.stdev(active_tiers) if len(active_tiers) > 1 else 0.0
            
            # Calculate binning statistics
            total_frequency = active_frequency + binned_count
            binning_rate = binned_count / total_frequency if total_frequency > 0 else 0
            
            # Calculate quality indicator
            quality_indicator = self._calculate_quality_indicator(active_tiers, binned_count)
            
            # Determine if word is rare (based on total frequency)
            is_rare = total_frequency < self.rare_word_threshold
            
            # Create tier distribution for active images only
            tier_distribution = defaultdict(int)
            for tier in active_tiers:
                tier_distribution[tier] += 1
            
            word_analysis[word] = {
                # Active image statistics (tier-based)
                'active_frequency': active_frequency,
                'active_tiers': active_tiers,
                'average_tier': average_tier,
                'std_deviation': std_deviation,
                'tier_distribution': dict(tier_distribution),
                
                # Binned image statistics
                'binned_frequency': binned_count,
                'binning_rate': binning_rate,
                
                # Combined statistics
                'total_frequency': total_frequency,
                'quality_indicator': quality_indicator,
                'is_rare': is_rare,
                
                # Legacy fields for backward compatibility
                'frequency': total_frequency,  # Keep for existing code
                'tiers': active_tiers  # Keep for existing code
            }
        
        return word_analysis
    
    def _calculate_quality_indicator(self, active_tiers: List[int], binned_count: int) -> float:
        """
        Calculate a quality score combining tier performance and binning rate.
        
        Args:
            active_tiers: List of tier values for active images
            binned_count: Number of binned images with this word
            
        Returns:
            Quality score where higher = better, negative = poor quality
        """
        total_images = len(active_tiers) + binned_count
        
        if total_images == 0:
            return 0.0
        
        if not active_tiers:
            # Only binned images - very poor quality
            return -2.0
        
        # Base score from active tier performance
        avg_tier = statistics.mean(active_tiers)
        
        # Penalty based on binning rate
        binning_rate = binned_count / total_images
        binning_penalty = binning_rate * 3.0  # Adjustable weight
        
        # Combined quality indicator
        return avg_tier - binning_penalty
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get enhanced summary including binning statistics."""
        word_analysis = self.analyze_word_performance()
        
        if not word_analysis:
            return {
                'total_words': 0,
                'total_active_images_with_prompts': 0,
                'total_binned_images_with_prompts': 0,
                'rare_words_count': 0,
                'avg_words_per_active_image': 0,
                'high_binning_rate_words': 0
            }
        
        active_images_with_prompts = len([
            img for img, stats in self.data_manager.image_stats.items()
            if stats.get('prompt') and not self.data_manager.is_image_binned(img)
        ])
        
        binned_images_with_prompts = len([
            img for img, stats in self.data_manager.image_stats.items()
            if stats.get('prompt') and self.data_manager.is_image_binned(img)
        ])
        
        rare_words = sum(1 for data in word_analysis.values() if data['is_rare'])
        
        high_binning_rate_words = sum(
            1 for data in word_analysis.values() 
            if data['binning_rate'] > 0.5  # More than 50% binned
        )
        
        total_active_word_instances = sum(
            data['active_frequency'] for data in word_analysis.values()
        )
        avg_words_per_active_image = (
            total_active_word_instances / active_images_with_prompts 
            if active_images_with_prompts > 0 else 0
        )
        
        return {
            'total_words': len(word_analysis),
            'total_active_images_with_prompts': active_images_with_prompts,
            'total_binned_images_with_prompts': binned_images_with_prompts,
            'rare_words_count': rare_words,
            'avg_words_per_active_image': avg_words_per_active_image,
            'high_binning_rate_words': high_binning_rate_words,
            # Legacy field for backward compatibility
            'total_images_with_prompts': active_images_with_prompts + binned_images_with_prompts
        }
    
    def get_worst_performing_words(self, min_frequency: int = 3, count: int = 20) -> List[Tuple[str, Dict[str, Any]]]:
        """Get words with the worst quality indicators (high binning rates, low tiers)."""
        word_analysis = self.analyze_word_performance()
        
        # Filter words with sufficient frequency and sort by quality indicator
        qualified_words = [
            (word, data) for word, data in word_analysis.items()
            if data['total_frequency'] >= min_frequency
        ]
        
        qualified_words.sort(key=lambda x: x[1]['quality_indicator'])
        
        return qualified_words[:count]
    
    def get_high_binning_rate_words(self, min_binning_rate: float = 0.3, count: int = 20) -> List[Tuple[str, Dict[str, Any]]]:
        """Get words with high binning rates."""
        word_analysis = self.analyze_word_performance()
        
        high_binning_words = [
            (word, data) for word, data in word_analysis.items()
            if data['binning_rate'] >= min_binning_rate and data['total_frequency'] >= 2
        ]
        
        high_binning_words.sort(key=lambda x: x[1]['binning_rate'], reverse=True)
        
        return high_binning_words[:count]
    
    def get_sorted_word_analysis(self, sort_by: str = 'average_tier', 
                                ascending: bool = False) -> List[Tuple[str, Dict[str, Any]]]:
        """Get word analysis results sorted by specified criteria."""
        word_analysis = self.analyze_word_performance()
        
        if sort_by in ['average_tier', 'frequency', 'std_deviation', 'quality_indicator', 'binning_rate']:
            sorted_words = sorted(
                word_analysis.items(),
                key=lambda x: x[1].get(sort_by, 0),
                reverse=not ascending
            )
        else:
            sorted_words = sorted(word_analysis.items())
        
        return sorted_words
    
    def search_words_by_pattern(self, pattern: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Search for words matching a pattern."""
        word_analysis = self.analyze_word_performance()
        pattern_lower = pattern.lower()
        
        matching_words = []
        for word, data in word_analysis.items():
            if pattern_lower in word:
                matching_words.append((word, data))
        
        # Sort by average tier (best first) for backward compatibility
        matching_words.sort(key=lambda x: x[1]['average_tier'], reverse=True)
        
        return matching_words
    
    def analyze_word_combinations(self, min_pair_frequency: int = 3) -> Dict[Tuple[str, str], Dict[str, Any]]:
        """
        Analyze word pair combinations for synergistic/antagonistic effects.
        
        Args:
            min_pair_frequency: Minimum number of occurrences for a pair to be analyzed
            
        Returns:
            Dictionary mapping word pairs to their analysis data
        """
        # Extract all word pairs from active images
        word_pairs = defaultdict(list)  # (word1, word2) -> [tier_values]
        individual_performance = self.analyze_word_performance()
        
        for image_name, stats in self.data_manager.image_stats.items():
            if self.data_manager.is_image_binned(image_name):
                continue
                
            prompt = stats.get('prompt')
            if not prompt:
                continue
                
            words = set(self.extract_words(self.extract_main_prompt(prompt)))  # Use set to avoid duplicate pairs
            current_tier = stats.get('current_tier', 0)
            
            # Generate all unique word pairs
            word_list = list(words)
            for i, word1 in enumerate(word_list):
                for word2 in word_list[i+1:]:  # Avoid duplicates and self-pairs
                    # Always store in alphabetical order for consistency
                    pair_key = tuple(sorted([word1, word2]))
                    word_pairs[pair_key].append(current_tier)
        
        # Calculate synergy/antagonism for each pair
        pair_analysis = {}
        
        for pair, tier_values in word_pairs.items():
            if len(tier_values) < min_pair_frequency:
                continue
                
            word1, word2 = pair
            
            # Get individual performances
            word1_perf = individual_performance.get(word1, {})
            word2_perf = individual_performance.get(word2, {})
            
            word1_avg = word1_perf.get('average_tier', 0)
            word2_avg = word2_perf.get('average_tier', 0)
            
            # Calculate expected performance (average of individual performances)
            expected_performance = (word1_avg + word2_avg) / 2
            
            # Calculate actual performance
            actual_performance = statistics.mean(tier_values)
            
            # Calculate synergy score
            synergy_score = actual_performance - expected_performance
            
            # Calculate statistical significance
            pair_std = statistics.stdev(tier_values) if len(tier_values) > 1 else 0.0
            
            pair_analysis[pair] = {
                'word1': word1,
                'word2': word2,
                'pair_frequency': len(tier_values),
                'actual_performance': actual_performance,
                'expected_performance': expected_performance,
                'synergy_score': synergy_score,
                'synergy_type': self._classify_synergy(synergy_score, len(tier_values)),
                'tier_values': tier_values,
                'std_deviation': pair_std,
                'confidence': self._calculate_pair_confidence(tier_values, synergy_score),
                'word1_individual_perf': word1_avg,
                'word2_individual_perf': word2_avg,
                'word1_frequency': word1_perf.get('active_frequency', 0),
                'word2_frequency': word2_perf.get('active_frequency', 0)
            }
        
        return pair_analysis
    
    def _classify_synergy(self, score: float, sample_size: int) -> str:
        """
        Classify synergy type based on score and sample size.
        
        Args:
            score: Synergy score (actual - expected performance)
            sample_size: Number of samples for this pair
            
        Returns:
            Classification string
        """
        # Adjust thresholds based on sample size (more conservative with fewer samples)
        base_threshold = 0.3
        size_factor = min(sample_size / 10.0, 1.0)  # Scale from 0.1 to 1.0
        threshold = base_threshold * (1.5 - size_factor)  # Higher threshold for small samples
        
        if score > threshold:
            return "Strong Synergy" if score > threshold * 2 else "Moderate Synergy"
        elif score < -threshold:
            return "Strong Antagonism" if score < -threshold * 2 else "Moderate Antagonism"
        else:
            return "Neutral"
    
    def _calculate_pair_confidence(self, tier_values: List[int], synergy_score: float) -> float:
        """
        Calculate confidence in the synergy measurement.
        
        Args:
            tier_values: List of tier values for this pair
            synergy_score: Calculated synergy score
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if len(tier_values) < 2:
            return 0.1
        
        # Sample size factor (more samples = higher confidence)
        sample_size_factor = min(len(tier_values) / 15.0, 1.0)
        
        # Consistency factor (lower std deviation = higher confidence)
        std_dev = statistics.stdev(tier_values)
        consistency_factor = 1.0 / (1.0 + std_dev)
        
        # Effect size factor (larger absolute synergy score = higher confidence)
        effect_size_factor = min(abs(synergy_score) / 2.0, 1.0)
        
        # Combined confidence
        confidence = (sample_size_factor + consistency_factor + effect_size_factor) / 3.0
        
        return min(confidence, 1.0)
    
    def get_combination_examples(self, word1: str, word2: str, max_examples: int = 5) -> List[str]:
        """
        Get example images that contain both words in the pair.
        
        Args:
            word1: First word in the pair
            word2: Second word in the pair
            max_examples: Maximum number of examples to return
            
        Returns:
            List of image filenames containing both words
        """
        examples = []
        word1_lower = word1.lower()
        word2_lower = word2.lower()
        
        for image_name, stats in self.data_manager.image_stats.items():
            if self.data_manager.is_image_binned(image_name):
                continue
                
            prompt = stats.get('prompt')
            if not prompt:
                continue
                
            try:
                main_prompt = self.extract_main_prompt(prompt)
                words = self.extract_words(main_prompt)
                
                if word1_lower in words and word2_lower in words:
                    examples.append(image_name)
                    if len(examples) >= max_examples:
                        break
            except Exception as e:
                print(f"Error processing prompt for {image_name} when finding combination examples: {e}")
                continue
        
        return examples
    
    def get_top_synergistic_pairs(self, min_frequency: int = 3, count: int = 10) -> List[Tuple[Tuple[str, str], Dict[str, Any]]]:
        """Get the top synergistic word pairs."""
        combinations = self.analyze_word_combinations(min_frequency)
        
        synergistic_pairs = [
            (pair, data) for pair, data in combinations.items()
            if data['synergy_score'] > 0
        ]
        
        synergistic_pairs.sort(key=lambda x: x[1]['synergy_score'], reverse=True)
        return synergistic_pairs[:count]
    
    def get_top_antagonistic_pairs(self, min_frequency: int = 3, count: int = 10) -> List[Tuple[Tuple[str, str], Dict[str, Any]]]:
        """Get the top antagonistic word pairs."""
        combinations = self.analyze_word_combinations(min_frequency)
        
        antagonistic_pairs = [
            (pair, data) for pair, data in combinations.items()
            if data['synergy_score'] < 0
        ]
        
        antagonistic_pairs.sort(key=lambda x: x[1]['synergy_score'])
        return antagonistic_pairs[:count]
    
    def get_combination_summary(self) -> Dict[str, Any]:
        """Get summary statistics for word combinations."""
        try:
            combinations = self.analyze_word_combinations()
            
            if not combinations:
                return {
                    'total_combinations': 0,
                    'synergistic_count': 0,
                    'antagonistic_count': 0,
                    'neutral_count': 0,
                    'avg_synergy_score': 0,
                    'strongest_synergy': None,
                    'strongest_antagonism': None
                }
            
            synergy_scores = [data['synergy_score'] for data in combinations.values()]
            synergistic = [p for p, d in combinations.items() if d['synergy_score'] > 0.1]
            antagonistic = [p for p, d in combinations.items() if d['synergy_score'] < -0.1]
            neutral = [p for p, d in combinations.items() if -0.1 <= d['synergy_score'] <= 0.1]
            
            # Find strongest effects
            strongest_synergy = max(combinations.items(), key=lambda x: x[1]['synergy_score'])
            strongest_antagonism = min(combinations.items(), key=lambda x: x[1]['synergy_score'])
            
            return {
                'total_combinations': len(combinations),
                'synergistic_count': len(synergistic),
                'antagonistic_count': len(antagonistic),
                'neutral_count': len(neutral),
                'avg_synergy_score': statistics.mean(synergy_scores),
                'strongest_synergy': strongest_synergy,
                'strongest_antagonism': strongest_antagonism
            }
            
        except Exception as e:
            print(f"Error getting combination summary: {e}")
            return {'error': str(e)}
