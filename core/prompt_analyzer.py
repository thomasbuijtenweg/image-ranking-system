"""Prompt analysis for the Image Ranking System with binning support."""

import re
import os
import statistics
from typing import Dict, List, Tuple, Any
from collections import defaultdict

from core.data_manager import DataManager


class PromptAnalyzer:
    """Analyzes prompt text to find correlations between words and image tiers."""
    
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