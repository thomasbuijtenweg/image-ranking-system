"""Configuration constants for the Image Ranking System - Modern UI Design."""

class Colors:
    """Modern color palette with black, white, grey, and purple accents."""
    
    # Primary backgrounds - Deep blacks and greys
    BG_PRIMARY = '#0a0a0a'      # Deep black
    BG_SECONDARY = '#1a1a1a'    # Dark grey
    BG_TERTIARY = '#2a2a2a'     # Medium grey
    BG_CARD = '#1e1e1e'         # Card background
    BG_HOVER = '#333333'        # Hover state
    
    # Text colors
    TEXT_PRIMARY = '#ffffff'     # Pure white
    TEXT_SECONDARY = '#b3b3b3'   # Light grey
    TEXT_TERTIARY = '#808080'    # Medium grey
    TEXT_MUTED = '#666666'       # Dark grey
    TEXT_INFO = '#8b5cf6'        # Add this line - Purple for info text
    
    # Purple accent colors
    PURPLE_PRIMARY = '#8b5cf6'   # Main purple
    PURPLE_SECONDARY = '#a78bfa' # Light purple
    PURPLE_TERTIARY = '#7c3aed'  # Dark purple
    PURPLE_MUTED = '#6d28d9'     # Deep purple
    
    # Status colors with purple tint
    SUCCESS = '#10b981'          # Green
    WARNING = '#f59e0b'          # Orange
    ERROR = '#ef4444'            # Red
    INFO = PURPLE_PRIMARY        # Purple for info
    
    # Button colors
    BUTTON_PRIMARY = PURPLE_PRIMARY
    BUTTON_SECONDARY = '#4a5568'
    BUTTON_SUCCESS = SUCCESS
    BUTTON_WARNING = WARNING
    BUTTON_ERROR = ERROR
    BUTTON_GHOST = BG_SECONDARY  # Use background color instead of transparent
    
    # Border and separator colors
    BORDER_PRIMARY = '#404040'
    BORDER_SECONDARY = '#2d2d2d'
    BORDER_ACCENT = PURPLE_PRIMARY
    SEPARATOR = '#303030'
    
    # Gradient colors for modern effects
    GRADIENT_START = BG_SECONDARY
    GRADIENT_END = BG_TERTIARY


class Fonts:
    """Modern font configuration."""
    
    # Font families - prioritize modern, clean fonts
    FAMILY_PRIMARY = ('Segoe UI', 'Arial', 'sans-serif')
    FAMILY_SECONDARY = ('Consolas', 'Monaco', 'monospace')
    FAMILY_HEADING = ('Segoe UI', 'Arial', 'sans-serif')
    
    # Font sizes
    SIZE_SMALL = 9
    SIZE_NORMAL = 10
    SIZE_MEDIUM = 11
    SIZE_LARGE = 12
    SIZE_HEADING = 14
    SIZE_TITLE = 16
    SIZE_DISPLAY = 20
    
    # Font weights
    WEIGHT_NORMAL = 'normal'
    WEIGHT_BOLD = 'bold'
    
    # Pre-configured font tuples
    SMALL = (FAMILY_PRIMARY, SIZE_SMALL, WEIGHT_NORMAL)
    NORMAL = (FAMILY_PRIMARY, SIZE_NORMAL, WEIGHT_NORMAL)
    MEDIUM = (FAMILY_PRIMARY, SIZE_MEDIUM, WEIGHT_NORMAL)
    LARGE = (FAMILY_PRIMARY, SIZE_LARGE, WEIGHT_NORMAL)
    HEADING = (FAMILY_HEADING, SIZE_HEADING, WEIGHT_BOLD)
    TITLE = (FAMILY_HEADING, SIZE_TITLE, WEIGHT_BOLD)
    DISPLAY = (FAMILY_HEADING, SIZE_DISPLAY, WEIGHT_BOLD)
    
    # Special purpose fonts
    MONO = (FAMILY_SECONDARY, SIZE_NORMAL, WEIGHT_NORMAL)
    MONO_SMALL = (FAMILY_SECONDARY, SIZE_SMALL, WEIGHT_NORMAL)


class Styling:
    """Modern styling constants."""
    
    # Border radius for rounded corners
    RADIUS_SMALL = 4
    RADIUS_MEDIUM = 8
    RADIUS_LARGE = 12
    RADIUS_BUTTON = 6
    
    # Padding and margins
    PADDING_SMALL = 4
    PADDING_MEDIUM = 8
    PADDING_LARGE = 12
    PADDING_EXTRA_LARGE = 16
    
    MARGIN_SMALL = 4
    MARGIN_MEDIUM = 8
    MARGIN_LARGE = 12
    MARGIN_EXTRA_LARGE = 16
    
    # Shadows (for supported widgets)
    SHADOW_LIGHT = '#00000020'
    SHADOW_MEDIUM = '#00000040'
    SHADOW_HEAVY = '#00000060'
    
    # Animation timing
    ANIMATION_FAST = 150
    ANIMATION_NORMAL = 250
    ANIMATION_SLOW = 350


class ButtonStyles:
    """Pre-configured button styles for consistency."""
    
    PRIMARY = {
        'bg': Colors.BUTTON_PRIMARY,
        'fg': Colors.TEXT_PRIMARY,
        'relief': 'flat',
        'borderwidth': 0,
        'font': Fonts.MEDIUM,
        'cursor': 'hand2',
        'activebackground': Colors.PURPLE_SECONDARY,
        'activeforeground': Colors.TEXT_PRIMARY
    }
    
    SECONDARY = {
        'bg': Colors.BUTTON_SECONDARY,
        'fg': Colors.TEXT_PRIMARY,
        'relief': 'flat',
        'borderwidth': 0,
        'font': Fonts.MEDIUM,
        'cursor': 'hand2',
        'activebackground': Colors.BG_HOVER,
        'activeforeground': Colors.TEXT_PRIMARY
    }
    
    SUCCESS = {
        'bg': Colors.BUTTON_SUCCESS,
        'fg': Colors.TEXT_PRIMARY,
        'relief': 'flat',
        'borderwidth': 0,
        'font': Fonts.MEDIUM,
        'cursor': 'hand2',
        'activebackground': '#059669',
        'activeforeground': Colors.TEXT_PRIMARY
    }
    
    WARNING = {
        'bg': Colors.BUTTON_WARNING,
        'fg': Colors.TEXT_PRIMARY,
        'relief': 'flat',
        'borderwidth': 0,
        'font': Fonts.MEDIUM,
        'cursor': 'hand2',
        'activebackground': '#d97706',
        'activeforeground': Colors.TEXT_PRIMARY
    }
    
    ERROR = {
        'bg': Colors.BUTTON_ERROR,
        'fg': Colors.TEXT_PRIMARY,
        'relief': 'flat',
        'borderwidth': 0,
        'font': Fonts.MEDIUM,
        'cursor': 'hand2',
        'activebackground': '#dc2626',
        'activeforeground': Colors.TEXT_PRIMARY
    }
    
    GHOST = {
        'bg': Colors.BUTTON_GHOST,
        'fg': Colors.TEXT_SECONDARY,
        'relief': 'flat',
        'borderwidth': 1,
        'font': Fonts.MEDIUM,
        'cursor': 'hand2',
        'activebackground': Colors.BG_HOVER,
        'activeforeground': Colors.TEXT_PRIMARY,
        'highlightbackground': Colors.BORDER_PRIMARY,
        'highlightcolor': Colors.BORDER_ACCENT
    }


class Defaults:
    """Default configuration values for the application."""
    
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 900
    
    MIN_IMAGE_WIDTH = 250
    MIN_IMAGE_HEIGHT = 250
    MAX_PROMPT_DISPLAY_LENGTH = 150
    
    # Algorithm weights remain the same
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
        'prioritize_high_votes': False
    }
    
    RIGHT_PRIORITY_PREFERENCES = {
        'prioritize_high_stability': False,
        'prioritize_high_votes': False
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


class UIComponents:
    """Modern UI component configurations."""
    
    # Card-like containers
    CARD_STYLE = {
        'bg': Colors.BG_CARD,
        'relief': 'flat',
        'borderwidth': 1,
        'highlightbackground': Colors.BORDER_PRIMARY,
        'highlightthickness': 1
    }
    
    # Input fields
    INPUT_STYLE = {
        'bg': Colors.BG_TERTIARY,
        'fg': Colors.TEXT_PRIMARY,
        'relief': 'flat',
        'borderwidth': 1,
        'highlightbackground': Colors.BORDER_PRIMARY,
        'highlightcolor': Colors.BORDER_ACCENT,
        'highlightthickness': 1,
        'font': Fonts.NORMAL,
        'insertbackground': Colors.TEXT_PRIMARY
    }
    
    # Labels
    LABEL_STYLE = {
        'bg': Colors.BG_SECONDARY,
        'fg': Colors.TEXT_PRIMARY,
        'font': Fonts.NORMAL
    }
    
    LABEL_SECONDARY_STYLE = {
        'bg': Colors.BG_SECONDARY,
        'fg': Colors.TEXT_SECONDARY,
        'font': Fonts.NORMAL
    }
    
    # Frames
    FRAME_STYLE = {
        'bg': Colors.BG_SECONDARY,
        'relief': 'flat',
        'borderwidth': 0
    }
    
    FRAME_CARD_STYLE = {
        'bg': Colors.BG_CARD,
        'relief': 'flat',
        'borderwidth': 1,
        'highlightbackground': Colors.BORDER_PRIMARY,
        'highlightthickness': 1
    }
