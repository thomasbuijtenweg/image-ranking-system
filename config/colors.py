"""
Color constants for the Image Ranking System dark theme.

This module centralizes all color definitions used throughout the application,
making it easy to modify the color scheme or create alternative themes.
"""


class Colors:
    """Color constants for the dark theme interface."""
    
    # Primary background colors
    BG_PRIMARY = '#1e1e1e'      # Main window background
    BG_SECONDARY = '#2d2d2d'    # Frame backgrounds
    BG_TERTIARY = '#3d3d3d'     # Entry fields and image placeholders
    
    # Text colors
    TEXT_PRIMARY = '#ffffff'    # Main text
    TEXT_SECONDARY = '#999999'  # Secondary/metadata text
    TEXT_SUCCESS = '#66ff66'    # Success messages
    TEXT_ERROR = '#ff6666'      # Error messages
    TEXT_INFO = '#6666ff'       # Information text
    
    # Button colors
    BUTTON_SUCCESS = '#4CAF50'  # Save, Apply, Vote buttons
    BUTTON_INFO = '#2196F3'     # Load, View buttons
    BUTTON_WARNING = '#FF9800'  # Rankings button
    BUTTON_SECONDARY = '#9C27B0' # Stats button
    BUTTON_NEUTRAL = '#607D8B'  # Settings button
    BUTTON_DANGER = '#FF5722'   # Delete, Reset buttons
    
    # Interactive element colors
    BUTTON_BG = '#333333'       # Default button background
    BUTTON_HOVER = '#4a4a4a'    # Button hover state
    BUTTON_ACTIVE = '#555555'   # Button active state
    
    # Border and separator colors
    BORDER = '#333333'
    SEPARATOR = '#4a4a4a'


class LightColors:
    """Alternative light theme colors (for future use)."""
    
    # Primary background colors
    BG_PRIMARY = '#ffffff'
    BG_SECONDARY = '#f5f5f5'
    BG_TERTIARY = '#e0e0e0'
    
    # Text colors
    TEXT_PRIMARY = '#000000'
    TEXT_SECONDARY = '#666666'
    TEXT_SUCCESS = '#2e7d32'
    TEXT_ERROR = '#d32f2f'
    TEXT_INFO = '#1976d2'
    
    # Button colors
    BUTTON_SUCCESS = '#4CAF50'
    BUTTON_INFO = '#2196F3'
    BUTTON_WARNING = '#FF9800'
    BUTTON_SECONDARY = '#9C27B0'
    BUTTON_NEUTRAL = '#607D8B'
    BUTTON_DANGER = '#FF5722'
    
    # Interactive element colors
    BUTTON_BG = '#e0e0e0'
    BUTTON_HOVER = '#d0d0d0'
    BUTTON_ACTIVE = '#c0c0c0'
    
    # Border and separator colors
    BORDER = '#cccccc'
    SEPARATOR = '#bbbbbb'
