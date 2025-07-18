"""Confidence calculation for the Image Ranking System."""

import math
import statistics
from typing import Dict, Any

from core.data_manager import DataManager


class ConfidenceCalculator:
    """Handles confidence calculation for images based on voting history and tier stability."""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def calculate_image_confidence(self, image_name: str) -> float:
        """
        Calculate confidence score for an image based on tier stability and vote count.
        
        Uses the pure square root approach: confidence = 1 / (1 + tier_stability / sqrt(votes))
        Special case: 0 votes returns 0.0 confidence.
        
        Args:
            image_name: Name of the image to calculate confidence for
            
        Returns:
            Float between 0.0 and 1.0 representing confidence level
        """
        stats = self.data_manager.get_image_stats(image_name)
        votes = stats.get('votes', 0)
        
        if votes == 0:
            return 0.0  # No confidence for untested images
        
        tier_stability = self.calculate_tier_stability(image_name)
        effective_stability = tier_stability / math.sqrt(votes)
        
        return 1.0 / (1.0 + effective_stability)
    
    def calculate_tier_stability(self, image_name: str) -> float:
        """
        Calculate the tier stability (standard deviation) for a single image.
        
        Args:
            image_name: Name of the image to calculate stability for
            
        Returns:
            Standard deviation of the image's tier history
        """
        stats = self.data_manager.get_image_stats(image_name)
        tier_history = stats.get('tier_history', [0])
        
        if len(tier_history) <= 1:
            return 0.0
        
        return statistics.stdev(tier_history)
    
    def get_confidence_breakdown(self, image_name: str) -> Dict[str, Any]:
        """
        Get detailed breakdown of confidence calculation for debugging/analysis.
        
        Args:
            image_name: Name of the image to analyze
            
        Returns:
            Dictionary with confidence calculation details
        """
        stats = self.data_manager.get_image_stats(image_name)
        votes = stats.get('votes', 0)
        
        if votes == 0:
            return {
                'confidence': 0.0,
                'votes': 0,
                'tier_stability': 0.0,
                'effective_stability': 0.0,
                'tier_history': stats.get('tier_history', [0]),
                'calculation': 'Special case: 0 votes = 0.0 confidence'
            }
        
        tier_stability = self.calculate_tier_stability(image_name)
        effective_stability = tier_stability / math.sqrt(votes)
        confidence = 1.0 / (1.0 + effective_stability)
        
        return {
            'confidence': confidence,
            'votes': votes,
            'tier_stability': tier_stability,
            'effective_stability': effective_stability,
            'tier_history': stats.get('tier_history', [0]),
            'calculation': f'1 / (1 + {tier_stability:.3f} / sqrt({votes})) = {confidence:.3f}'
        }
    
    def compare_confidence(self, image1: str, image2: str) -> Dict[str, Any]:
        """
        Compare confidence between two images with detailed breakdown.
        
        Args:
            image1: First image name
            image2: Second image name
            
        Returns:
            Dictionary with comparison details
        """
        breakdown1 = self.get_confidence_breakdown(image1)
        breakdown2 = self.get_confidence_breakdown(image2)
        
        return {
            'image1': {
                'name': image1,
                'confidence': breakdown1['confidence'],
                'votes': breakdown1['votes'],
                'tier_stability': breakdown1['tier_stability'],
                'calculation': breakdown1['calculation']
            },
            'image2': {
                'name': image2,
                'confidence': breakdown2['confidence'],
                'votes': breakdown2['votes'],
                'tier_stability': breakdown2['tier_stability'],
                'calculation': breakdown2['calculation']
            },
            'winner': image1 if breakdown1['confidence'] < breakdown2['confidence'] else image2,
            'confidence_difference': abs(breakdown1['confidence'] - breakdown2['confidence'])
        }
    
    def get_lowest_confidence_images(self, image_list: list, count: int = 5) -> list:
        """
        Get the lowest confidence images from a list.
        
        Args:
            image_list: List of image names to evaluate
            count: Number of lowest confidence images to return
            
        Returns:
            List of tuples (image_name, confidence_score) sorted by confidence (lowest first)
        """
        confidence_scores = []
        
        for image_name in image_list:
            confidence = self.calculate_image_confidence(image_name)
            confidence_scores.append((image_name, confidence))
        
        confidence_scores.sort(key=lambda x: x[1])  # Sort by confidence (lowest first)
        
        return confidence_scores[:count]
    
    def get_highest_confidence_images(self, image_list: list, count: int = 5) -> list:
        """
        Get the highest confidence images from a list.
        
        Args:
            image_list: List of image names to evaluate
            count: Number of highest confidence images to return
            
        Returns:
            List of tuples (image_name, confidence_score) sorted by confidence (highest first)
        """
        confidence_scores = []
        
        for image_name in image_list:
            confidence = self.calculate_image_confidence(image_name)
            confidence_scores.append((image_name, confidence))
        
        confidence_scores.sort(key=lambda x: x[1], reverse=True)  # Sort by confidence (highest first)
        
        return confidence_scores[:count]
    
    def get_confidence_statistics(self, image_list: list) -> Dict[str, float]:
        """
        Get confidence statistics for a list of images.
        
        Args:
            image_list: List of image names to analyze
            
        Returns:
            Dictionary with confidence statistics
        """
        if not image_list:
            return {
                'count': 0,
                'average': 0.0,
                'minimum': 0.0,
                'maximum': 0.0,
                'std_deviation': 0.0
            }
        
        confidences = [self.calculate_image_confidence(img) for img in image_list]
        
        return {
            'count': len(confidences),
            'average': statistics.mean(confidences),
            'minimum': min(confidences),
            'maximum': max(confidences),
            'std_deviation': statistics.stdev(confidences) if len(confidences) > 1 else 0.0
        }