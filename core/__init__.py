"""
Core package for the Image Ranking System.

This package contains the core business logic modules:
- data_manager: Handles data persistence and management
- image_processor: Handles image loading and resizing
- ranking_algorithm: Implements the intelligent pair selection algorithm
- prompt_analyzer: Analyzes prompt text to find correlations with image tiers
- metadata_extractor: Handles metadata and prompt extraction from images
- weight_manager: Manages algorithm weights and priority preferences

By organizing these modules in a package, we create a clean separation
between business logic and user interface components.
"""

from .data_manager import DataManager
from .image_processor import ImageProcessor
from .ranking_algorithm import RankingAlgorithm
from .prompt_analyzer import PromptAnalyzer
from .metadata_extractor import MetadataExtractor
from .weight_manager import WeightManager

__all__ = ['DataManager', 'ImageProcessor', 'RankingAlgorithm', 'PromptAnalyzer', 'MetadataExtractor', 'WeightManager']
__version__ = '1.0.0'