"""
Utility functions for the Image Ranking System.

This module contains helper functions that are used across multiple
parts of the application. By centralizing these utilities, we avoid
code duplication and make the codebase more maintainable.
"""

import os
import json
from typing import Optional, Dict, Any
from datetime import datetime


def validate_image_folder(folder_path: str) -> bool:
    """
    Validate that a folder exists and is readable.
    
    Args:
        folder_path: Path to the folder to validate
        
    Returns:
        True if the folder is valid, False otherwise
    """
    if not folder_path:
        return False
    
    try:
        return os.path.exists(folder_path) and os.path.isdir(folder_path)
    except (OSError, TypeError):
        return False


def safe_json_load(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Safely load JSON data from a file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON data or None if loading fails
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError, TypeError):
        return None


def safe_json_save(data: Dict[str, Any], file_path: str) -> bool:
    """
    Safely save data to a JSON file.
    
    Args:
        data: Data to save
        file_path: Path to the output file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except (OSError, TypeError):
        return False


def format_timestamp(timestamp: Optional[str] = None) -> str:
    """
    Format a timestamp for display.
    
    Args:
        timestamp: ISO format timestamp string, or None for current time
        
    Returns:
        Formatted timestamp string
    """
    if timestamp is None:
        dt = datetime.now()
    else:
        try:
            dt = datetime.fromisoformat(timestamp)
        except ValueError:
            dt = datetime.now()
    
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length with optional suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add if text is truncated
        
    Returns:
        Truncated text with suffix if needed
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def ensure_directory_exists(dir_path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        dir_path: Path to the directory
        
    Returns:
        True if directory exists or was created successfully
    """
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True
    except OSError:
        return False


def get_file_size_string(file_path: str) -> str:
    """
    Get a human-readable file size string.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Human-readable size string
    """
    try:
        size = os.path.getsize(file_path)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    except OSError:
        return "Unknown size"


def validate_weights(weights: Dict[str, float], expected_sum: float = 1.0, tolerance: float = 0.01) -> bool:
    """
    Validate that weight values are reasonable.
    
    Args:
        weights: Dictionary of weight values
        expected_sum: Expected sum of all weights
        tolerance: Tolerance for sum validation
        
    Returns:
        True if weights are valid, False otherwise
    """
    if not weights:
        return False
    
    # Check that all weights are non-negative
    if any(w < 0 for w in weights.values()):
        return False
    
    # Check that sum is close to expected value
    total = sum(weights.values())
    return abs(total - expected_sum) <= tolerance


def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    Clamp a value between minimum and maximum bounds.
    
    Args:
        value: Value to clamp
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Returns:
        Clamped value
    """
    return max(min_value, min(value, max_value))


def calculate_percentage(numerator: int, denominator: int) -> float:
    """
    Safely calculate a percentage.
    
    Args:
        numerator: Numerator value
        denominator: Denominator value
        
    Returns:
        Percentage as a float (0.0 to 1.0)
    """
    if denominator == 0:
        return 0.0
    
    return numerator / denominator