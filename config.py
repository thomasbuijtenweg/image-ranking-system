"""Configuration constants for the Image Ranking System."""

class Colors:
    """Color constants for the dark theme interface."""
    
    BG_PRIMARY = '#1e1e1e'
    BG_SECONDARY = '#2d2d2d'
    BG_TERTIARY = '#3d3d3d'
    
    TEXT_PRIMARY = '#ffffff'
    TEXT_SECONDARY = '#999999'
    TEXT_SUCCESS = '#66ff66'
    TEXT_ERROR = '#ff6666'
    TEXT_INFO = '#6666ff'
    
    BUTTON_SUCCESS = '#4CAF50'
    BUTTON_INFO = '#2196F3'
    BUTTON_WARNING = '#FF9800'
    BUTTON_SECONDARY = '#9C27B0'
    BUTTON_NEUTRAL = '#607D8B'
    BUTTON_DANGER = '#FF5722'
    
    BUTTON_BG = '#333333'
    BUTTON_HOVER = '#4a4a4a'
    BUTTON_ACTIVE = '#555555'
    
    BORDER = '#333333'
    SEPARATOR = '#4a4a4a'


class Defaults:
    """Default configuration values for the application."""
    
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    
    MIN_IMAGE_WIDTH = 200
    MIN_IMAGE_HEIGHT = 200
    MAX_PROMPT_DISPLAY_LENGTH = 150
    
    BASE_SELECTION_WEIGHTS = {
        'recency': 0.25,
        'low_votes': 0.25,
        'instability': 0.25,
        'tier_size': 0.25
    }
    
    LEFT_SELECTION_WEIGHTS = BASE_SELECTION_WEIGHTS.copy()
    RIGHT_SELECTION_WEIGHTS = BASE_SELECTION_WEIGHTS.copy()
    SELECTION_WEIGHTS = BASE_SELECTION_WEIGHTS.copy()
    
    LEFT_PRIORITY_PREFERENCES = {
        'prioritize_high_stability': False,
        'prioritize_high_votes': False,
        'prioritize_new_images': False
    }
    
    RIGHT_PRIORITY_PREFERENCES = {
        'prioritize_high_stability': False,
        'prioritize_high_votes': False,
        'prioritize_new_images': False
    }
    
    VOTE_DELAY_MS = 500
    RESIZE_DEBOUNCE_MS = 300
    PRELOAD_DELAY_MS = 100
    
    SUPPORTED_IMAGE_EXTENSIONS = (
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'
    )
    
    PROMPT_KEYWORDS = [
        'parameters', 'prompt', 'description', 'comment', 
        'positive', 'negative', 'sd-metadata', 'dream',
        'generation_data', 'invokeai_metadata'
    ]
    
    AI_KEYWORDS = [
        'prompt', 'negative', 'steps', 'cfg', 'sampler', 
        'model', 'seed', 'denoising', 'clip skip'
    ]


class KeyBindings:
    """Keyboard shortcut definitions."""
    VOTE_LEFT = ['<Left>', '<a>']
    VOTE_RIGHT = ['<Right>', '<d>']
    SAVE = ['<Control-s>']
    LOAD = ['<Control-o>']
    STATS = ['<Control-t>']
    PROMPT_ANALYSIS = ['<Control-p>']
    SETTINGS = ['<Control-comma>']