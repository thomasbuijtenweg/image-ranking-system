"""Prompt analysis for the Image Ranking System."""

import re
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
        """Analyze the performance of each word across all images."""
        word_data = defaultdict(list)
        
        for image_name, stats in self.data_manager.image_stats.items():
            prompt = stats.get('prompt')
            if not prompt:
                continue
            
            main_prompt = self.extract_main_prompt(prompt)
            words = self.extract_words(main_prompt)
            current_tier = stats.get('current_tier', 0)
            
            for word in set(words):
                word_data[word].append(current_tier)
        
        word_analysis = {}
        for word, tiers in word_data.items():
            frequency = len(tiers)
            average_tier = statistics.mean(tiers)
            
            if frequency > 1:
                std_deviation = statistics.stdev(tiers)
            else:
                std_deviation = 0.0
            
            is_rare = frequency < self.rare_word_threshold
            
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
        """Get word analysis results sorted by specified criteria."""
        word_analysis = self.analyze_word_performance()
        
        if sort_by in ['average_tier', 'frequency', 'std_deviation']:
            sorted_words = sorted(
                word_analysis.items(),
                key=lambda x: x[1][sort_by],
                reverse=not ascending
            )
        else:
            sorted_words = sorted(word_analysis.items())
        
        return sorted_words
        
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get a summary of the prompt analysis."""
        word_analysis = self.analyze_word_performance()
        
        if not word_analysis:
            return {
                'total_words': 0,
                'total_images_with_prompts': 0,
                'rare_words_count': 0,
                'avg_words_per_image': 0
            }
        
        images_with_prompts = sum(1 for stats in self.data_manager.image_stats.values() 
                                if stats.get('prompt'))
        
        rare_words = sum(1 for data in word_analysis.values() if data['is_rare'])
        
        total_word_instances = sum(data['frequency'] for data in word_analysis.values())
        avg_words_per_image = total_word_instances / images_with_prompts if images_with_prompts > 0 else 0
        
        return {
            'total_words': len(word_analysis),
            'total_images_with_prompts': images_with_prompts,
            'rare_words_count': rare_words,
            'avg_words_per_image': avg_words_per_image
        }
        
    def search_words_by_pattern(self, pattern: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Search for words matching a pattern."""
        word_analysis = self.analyze_word_performance()
        pattern_lower = pattern.lower()
        
        matching_words = []
        for word, data in word_analysis.items():
            if pattern_lower in word:
                matching_words.append((word, data))
        
        matching_words.sort(key=lambda x: x[1]['average_tier'], reverse=True)
        
        return matching_words