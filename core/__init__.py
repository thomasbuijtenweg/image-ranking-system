"""
Core package for the Image Ranking System.

This package contains the core business logic modules:
- data_manager: Handles data persistence and management
- image_processor: Handles image loading and metadata extraction
- ranking_algorithm: Implements the intelligent pair selection algorithm

By organizing these modules in a package, we create a clean separation
between business logic and user interface components.
"""

from .data_manager import DataManager
from .image_processor import ImageProcessor
from .ranking_algorithm import RankingAlgorithm

__all__ = ['DataManager', 'ImageProcessor', 'RankingAlgorithm']
__version__ = '1.0.0'