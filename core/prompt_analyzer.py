"""
Prompt analysis module for the Image Ranking System.

This module analyzes prompt text to determine correlations between
specific words and image tier rankings. It helps identify which
prompt words tend to produce higher quality images.
"""

import re
import statistics
from typing import Dict, List, Tuple, Any
from collections import defaultdict

from core.data_manager import DataManager


class PromptAnalyzer:
    """
    Analyzes prompt text to find correlations between words and image tiers.
    
    This class processes all image prompts to extract individual words,
    calculates statistics for each word's performance across tiers,
    and identifies which words correlate with higher quality images.
    """
    
    def __init__(self, data_manager: DataManager):
        """
        Initialize the prompt analyzer.
        
        Args:
            data_manager: DataManager instance containing image data
        """
        self.data_manager = data_manager
        self.rare_word_threshold = 3  # Words appearing in fewer images are considered rare
    
    def extract_main_prompt(self, full_prompt: str) -> str:
        """
        Extract the main/positive prompt from the full prompt text.
        
        This method separates the positive prompt from negative prompts
        and other metadata that might be included in the prompt text.
        
        Args:
            full_prompt: The complete prompt text
            
        Returns:
            Just the main/positive prompt portion
        """
        if not full_prompt:
            return ""
        
        # Common separators for negative prompts and other metadata
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
        
        # Convert to lowercase for case-insensitive matching
        lower_prompt = full_prompt.lower()
        main_prompt = full_prompt  # Start with full prompt
        
        # Find the earliest separator and cut there
        earliest_pos = len(full_prompt)
        for separator in separators:
            pos = lower_prompt.find(separator)
            if pos != -1 and pos < earliest_pos:
                earliest_pos = pos
        
        if earliest_pos < len(full_prompt):
            main_prompt = full_prompt[:earliest_pos]
        
        return main_prompt.strip()
    
    def extract_words(self, prompt_text: str) -> List[str]:
        """
        Extract individual words from prompt text.
        
        This method cleans the text by removing punctuation and special
        characters, converts to lowercase, and splits into individual words.
        
        Args:
            prompt_text: The prompt text to process
            
        Returns:
            List of cleaned, lowercase words
        """
        if not prompt_text:
            return []
        
        # Remove punctuation and special characters, keep only letters, numbers, and spaces
        # This regex keeps alphanumeric characters and spaces, removes everything else
        cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', ' ', prompt_text)
        
        # Convert to lowercase and split into words
        words = cleaned_text.lower().split()
        
        # Filter out empty strings and very short words that are likely noise
        words = [word for word in words if len(word) > 1]
        
        return words
    
    def analyze_word_performance(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze the performance of each word across all images.
        
        This method processes all image prompts to calculate statistics
        for each unique word, including frequency, tier distribution,
        average tier, and standard deviation.
        
        Returns:
            Dictionary mapping words to their performance statistics
        """
        word_data = defaultdict(list)  # word -> list of tiers where it appears
        
        # Process all images with prompts
        for image_name, stats in self.data_manager.image_stats.items():
            prompt = stats.get('prompt')
            if not prompt:
                continue
            
            # Extract main prompt and words
            main_prompt = self.extract_main_prompt(prompt)
            words = self.extract_words(main_prompt)
            current_tier = stats.get('current_tier', 0)
            
            # Record this tier for each word in the prompt
            for word in set(words):  # Use set to avoid counting same word multiple times per image
                word_data[word].append(current_tier)
        
        # Calculate statistics for each word
        word_analysis = {}
        for word, tiers in word_data.items():
            frequency = len(tiers)
            average_tier = statistics.mean(tiers)
            
            # Calculate standard deviation (handle case of single data point)
            if frequency > 1:
                std_deviation = statistics.stdev(tiers)
            else:
                std_deviation = 0.0
            
            # Determine if word is rare (appears in few images)
            is_rare = frequency < self.rare_word_threshold
            
            # Calculate tier distribution for detailed analysis
            tier_distribution = defaultdict(int)
            for tier in tiers:
                tier_distribution[tier] += 1
            
            word_analysis[word] = {
                'frequency': frequency,
                'tiers': tiers,
                'average_tier': average_tier,
                'std_deviation': std_deviation,
                'is_rare': is_rare,
                'tier_distribution': dict(tier_distribution)
            }
        
        return word_analysis
    
    def get_sorted_word_analysis(self, sort_by: str = 'average_tier', 
                                ascending: bool = False) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Get word analysis results sorted by specified criteria.
        
        Args:
            sort_by: Field to sort by ('average_tier', 'frequency', 'std_deviation')
            ascending: Whether to sort in ascending order
            
        Returns:
            List of (word, analysis_data) tuples sorted by the specified criteria
        """
        word_analysis = self.analyze_word_performance()
        
        # Sort by the specified field
        if sort_by in ['average_tier', 'frequency', 'std_deviation']:
            sorted_words = sorted(
                word_analysis.items(),
                key=lambda x: x[1][sort_by],
                reverse=not ascending
            )
        else:
            # Default to alphabetical if invalid sort field
            sorted_words = sorted(word_analysis.items())
        
        return sorted_words
    
        
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the prompt analysis.
        
        Returns:
            Dictionary containing overall analysis statistics
        """
        word_analysis = self.analyze_word_performance()
        
        if not word_analysis:
            return {
                'total_words': 0,
                'total_images_with_prompts': 0,
                'rare_words_count': 0,
                'avg_words_per_image': 0
            }
        
        # Count images with prompts
        images_with_prompts = sum(1 for stats in self.data_manager.image_stats.values() 
                                if stats.get('prompt'))
        
        # Count rare words
        rare_words = sum(1 for data in word_analysis.values() if data['is_rare'])
        
        # Calculate average words per image (approximate)
        total_word_instances = sum(data['frequency'] for data in word_analysis.values())
        avg_words_per_image = total_word_instances / images_with_prompts if images_with_prompts > 0 else 0
        
        return {
            'total_words': len(word_analysis),
            'total_images_with_prompts': images_with_prompts,
            'rare_words_count': rare_words,
            'avg_words_per_image': avg_words_per_image
        }
    
        
    def search_words_by_pattern(self, pattern: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Search for words matching a pattern.
        
        Args:
            pattern: Pattern to search for (supports simple wildcard matching)
            
        Returns:
            List of matching words with their analysis data
        """
        word_analysis = self.analyze_word_performance()
        pattern_lower = pattern.lower()
        
        matching_words = []
        for word, data in word_analysis.items():
            if pattern_lower in word:  # Simple substring matching
                matching_words.append((word, data))
        
        # Sort by average tier (descending)
        matching_words.sort(key=lambda x: x[1]['average_tier'], reverse=True)
        
        return matching_words