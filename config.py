"""
Configuration constants for the Image Ranking System.

This file centralizes all the theming, UI constants, and default settings
in one place. This makes it easy to modify the appearance or behavior
of the entire application without hunting through multiple files.
"""

# Dark theme color palette
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

# Application default settings
class Defaults:
    """Default configuration values for the application."""
    # Window dimensions
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    
    # Image display settings
    MIN_IMAGE_WIDTH = 200
    MIN_IMAGE_HEIGHT = 200
    MAX_PROMPT_DISPLAY_LENGTH = 150
    
    # Ranking algorithm weights (these sum to 1.0)
    SELECTION_WEIGHTS = {
        'recency': 0.25,        # How recently an image was voted on
        'low_votes': 0.25,      # Prioritize images with fewer votes
        'instability': 0.25,    # Prioritize images with unstable tier positions
        'tier_size': 0.25       # Prioritize images in crowded tiers
    }
    
    # UI behavior settings
    VOTE_DELAY_MS = 500         # Delay before showing next pair after vote
    RESIZE_DEBOUNCE_MS = 300    # Delay before redrawing images after resize
    PRELOAD_DELAY_MS = 100      # Delay before preloading next pair
    
    # File handling
    SUPPORTED_IMAGE_EXTENSIONS = (
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'
    )
    
    # Metadata extraction settings
    PROMPT_KEYWORDS = [
        'parameters', 'prompt', 'description', 'comment', 
        'positive', 'negative', 'sd-metadata', 'dream',
        'generation_data', 'invokeai_metadata'
    ]
    
    # AI generation detection keywords
    AI_KEYWORDS = [
        'prompt', 'negative', 'steps', 'cfg', 'sampler', 
        'model', 'seed', 'denoising', 'clip skip'
    ]

# TTK Style configuration for dark theme
class TTKStyles:
    """Configuration for ttk widget styling."""
    
    @staticmethod
    def get_treeview_config():
        """Returns configuration dict for Treeview styling."""
        return {
            "Treeview": {
                "background": Colors.BG_SECONDARY,
                "foreground": Colors.TEXT_PRIMARY,
                "fieldbackground": Colors.BG_SECONDARY,
                "borderwidth": 0,
                "selectbackground": Colors.BUTTON_HOVER,
                "selectforeground": Colors.TEXT_PRIMARY
            },
            "Treeview.Heading": {
                "background": Colors.BUTTON_BG,
                "foreground": Colors.TEXT_PRIMARY,
                "borderwidth": 1,
                "relief": "flat",
                "font": ('Arial', 10, 'bold')
            }
        }
    
    @staticmethod
    def get_notebook_config():
        """Returns configuration dict for Notebook styling."""
        return {
            "TNotebook": {
                "background": Colors.BG_PRIMARY,
                "borderwidth": 0
            },
            "TNotebook.Tab": {
                "background": Colors.BUTTON_BG,
                "foreground": Colors.TEXT_PRIMARY,
                "padding": [20, 10],
                "borderwidth": 0,
                "focuscolor": 'none'
            }
        }
    
    @staticmethod
    def get_scrollbar_config():
        """Returns configuration dict for Scrollbar styling."""
        return {
            "Vertical.TScrollbar": {
                "background": Colors.BUTTON_BG,
                "bordercolor": Colors.BUTTON_BG,
                "arrowcolor": Colors.TEXT_PRIMARY,
                "troughcolor": Colors.BG_SECONDARY,
                "darkcolor": Colors.BUTTON_BG,
                "lightcolor": Colors.BUTTON_BG,
                "gripcount": 0
            }
        }

# Keyboard shortcuts
class KeyBindings:
    """Keyboard shortcut definitions."""
    VOTE_LEFT = ['<Left>', '<a>']
    VOTE_RIGHT = ['<Right>', '<d>']
    SAVE = ['<Control-s>']
    LOAD = ['<Control-o>']
    RANKINGS = ['<Control-r>']
    STATS = ['<Control-t>']
    SETTINGS = ['<Control-comma>']