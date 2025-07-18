"""
Modern UI builder for the Image Ranking System.

This module handles the creation and layout of modern, sleek UI widgets
for the main window with improved visual design.
"""

import tkinter as tk
from tkinter import ttk

from config import Colors, Fonts, ButtonStyles, UIComponents, Styling


class ModernButton(tk.Button):
    """Custom button class with modern styling and hover effects."""
    
    def __init__(self, parent, style='primary', **kwargs):
        """Initialize modern button with style."""
        # Get the style configuration
        if style == 'primary':
            style_config = ButtonStyles.PRIMARY
        elif style == 'secondary':
            style_config = ButtonStyles.SECONDARY
        elif style == 'success':
            style_config = ButtonStyles.SUCCESS
        elif style == 'warning':
            style_config = ButtonStyles.WARNING
        elif style == 'error':
            style_config = ButtonStyles.ERROR
        elif style == 'ghost':
            style_config = ButtonStyles.GHOST
        else:
            style_config = ButtonStyles.PRIMARY
        
        # Merge style config with kwargs
        final_config = {**style_config, **kwargs}
        
        super().__init__(parent, **final_config)
        
        # Store original colors for hover effects
        self.original_bg = final_config['bg']
        self.active_bg = final_config['activebackground']
        
        # Bind hover events
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        
        # Add padding
        self.configure(padx=Styling.PADDING_LARGE, pady=Styling.PADDING_MEDIUM)
    
    def _on_enter(self, event):
        """Handle mouse enter - hover effect."""
        self.configure(bg=self.active_bg)
    
    def _on_leave(self, event):
        """Handle mouse leave - restore original color."""
        self.configure(bg=self.original_bg)


class ModernFrame(tk.Frame):
    """Custom frame class with modern styling."""
    
    def __init__(self, parent, style='default', **kwargs):
        """Initialize modern frame with style."""
        if style == 'card':
            style_config = UIComponents.FRAME_CARD_STYLE
        else:
            style_config = UIComponents.FRAME_STYLE
        
        final_config = {**style_config, **kwargs}
        super().__init__(parent, **final_config)


class ModernLabel(tk.Label):
    """Custom label class with modern styling."""
    
    def __init__(self, parent, style='primary', **kwargs):
        """Initialize modern label with style."""
        if style == 'secondary':
            style_config = UIComponents.LABEL_SECONDARY_STYLE
        else:
            style_config = UIComponents.LABEL_STYLE
        
        final_config = {**style_config, **kwargs}
        super().__init__(parent, **final_config)


class ModernEntry(tk.Entry):
    """Custom entry class with modern styling."""
    
    def __init__(self, parent, **kwargs):
        """Initialize modern entry with style."""
        style_config = UIComponents.INPUT_STYLE
        final_config = {**style_config, **kwargs}
        super().__init__(parent, **final_config)
        
        # Add padding
        self.configure(
            bd=0,
            highlightthickness=2,
            relief='flat'
        )


class UIBuilder:
    """
    Handles modern UI widget creation and layout for the main window.
    
    This class centralizes the UI construction logic with modern design principles.
    """
    
    def __init__(self, parent: tk.Tk):
        """
        Initialize the UI builder.
        
        Args:
            parent: Parent tkinter window
        """
        self.parent = parent
        
        # UI references to return
        self.folder_label = None
        self.stats_label = None
        self.status_bar = None
        
        # Setup modern theme
        self._setup_modern_theme()
    
    def _setup_modern_theme(self) -> None:
        """Configure ttk styles for modern dark theme."""
        style = ttk.Style()
        
        try:
            style.theme_use('clam')
        except:
            pass
        
        # Configure Treeview for modern dark theme
        style.configure("Treeview",
                       background=Colors.BG_CARD,
                       foreground=Colors.TEXT_PRIMARY,
                       fieldbackground=Colors.BG_CARD,
                       borderwidth=0,
                       selectbackground=Colors.PURPLE_PRIMARY,
                       selectforeground=Colors.TEXT_PRIMARY,
                       font=Fonts.NORMAL,
                       rowheight=28)
        
        style.configure("Treeview.Heading",
                       background=Colors.BG_TERTIARY,
                       foreground=Colors.TEXT_PRIMARY,
                       borderwidth=0,
                       relief='flat',
                       font=Fonts.HEADING)
        
        style.map("Treeview.Heading",
                 background=[('active', Colors.PURPLE_PRIMARY)])
        
        # Configure Notebook for modern theme
        style.configure("TNotebook", 
                       background=Colors.BG_PRIMARY, 
                       borderwidth=0,
                       tabposition='n')
        
        style.configure("TNotebook.Tab",
                       background=Colors.BG_TERTIARY,
                       foreground=Colors.TEXT_SECONDARY,
                       padding=[20, 12],
                       borderwidth=0,
                       focuscolor='none',
                       font=Fonts.MEDIUM)
        
        style.map("TNotebook.Tab",
                 background=[('selected', Colors.PURPLE_PRIMARY),
                           ('active', Colors.PURPLE_SECONDARY)],
                 foreground=[('selected', Colors.TEXT_PRIMARY),
                           ('active', Colors.TEXT_PRIMARY)])
        
        # Configure Progressbar
        style.configure("TProgressbar",
                       background=Colors.PURPLE_PRIMARY,
                       troughcolor=Colors.BG_TERTIARY,
                       borderwidth=0,
                       lightcolor=Colors.PURPLE_PRIMARY,
                       darkcolor=Colors.PURPLE_PRIMARY)
        
        # Configure Scrollbar
        style.configure("Vertical.TScrollbar",
                       background=Colors.BG_TERTIARY,
                       troughcolor=Colors.BG_SECONDARY,
                       borderwidth=0,
                       arrowcolor=Colors.TEXT_SECONDARY,
                       darkcolor=Colors.BG_TERTIARY,
                       lightcolor=Colors.BG_TERTIARY)
        
        style.map("Vertical.TScrollbar",
                 background=[('active', Colors.PURPLE_PRIMARY)])
    
    def build_main_ui(self) -> dict:
        """
        Build the main UI layout with modern styling.
        
        Returns:
            Dictionary containing references to important UI elements
        """
        # Configure main window
        self.parent.configure(bg=Colors.BG_PRIMARY)
        self.parent.minsize(1000, 700)
        
        # Create main components
        top_frame = self._create_modern_top_frame()
        main_frame = self._create_modern_main_frame()
        self._create_modern_status_bar()
        
        return {
            'top_frame': top_frame,
            'main_frame': main_frame,
            'folder_label': self.folder_label,
            'stats_label': self.stats_label,
            'status_bar': self.status_bar
        }
    
    def _create_modern_top_frame(self) -> tk.Frame:
        """Create the modern top frame with sleek header styling."""
        # Main header container
        header_container = ModernFrame(self.parent, style='card')
        header_container.pack(fill=tk.X, padx=Styling.PADDING_LARGE, pady=(Styling.PADDING_LARGE, 0))
        
        # Inner frame for content
        top_frame = ModernFrame(header_container)
        top_frame.pack(fill=tk.X, padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        # Left side - folder info
        left_frame = ModernFrame(top_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # App title
        title_label = ModernLabel(left_frame, 
                                 text="Image Ranking System",
                                 font=Fonts.TITLE,
                                 fg=Colors.TEXT_PRIMARY)
        title_label.pack(anchor=tk.W)
        
        # Folder label with modern styling
        self.folder_label = ModernLabel(left_frame,
                                       text="No folder selected",
                                       style='secondary',
                                       font=Fonts.MEDIUM)
        self.folder_label.pack(anchor=tk.W, pady=(4, 0))
        
        # Right side - stats with accent color
        right_frame = ModernFrame(top_frame)
        right_frame.pack(side=tk.RIGHT)
        
        self.stats_label = ModernLabel(right_frame,
                                      text="Total votes: 0",
                                      font=Fonts.HEADING,
                                      fg=Colors.PURPLE_PRIMARY)
        self.stats_label.pack(anchor=tk.E)
        
        return top_frame
    
    def _create_modern_main_frame(self) -> tk.Frame:
        """Create the modern main frame with card-like styling."""
        # Container for the main content
        main_container = ModernFrame(self.parent)
        main_container.pack(fill=tk.BOTH, expand=True, padx=Styling.PADDING_LARGE, pady=Styling.PADDING_MEDIUM)
        
        # Main content area with card styling
        main_frame = ModernFrame(main_container, style='card')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        return main_frame
    
    def _create_modern_status_bar(self) -> None:
        """Create the modern status bar with sleek styling."""
        # Status bar container
        status_container = ModernFrame(self.parent, style='card')
        status_container.pack(side=tk.BOTTOM, fill=tk.X, padx=Styling.PADDING_LARGE, pady=(0, Styling.PADDING_LARGE))
        
        self.status_bar = ModernLabel(status_container,
                                     text="Select a folder to begin",
                                     font=Fonts.MEDIUM,
                                     fg=Colors.TEXT_SECONDARY)
        self.status_bar.pack(side=tk.LEFT, padx=Styling.PADDING_LARGE, pady=Styling.PADDING_MEDIUM)
        
        # Add status indicator dot
        status_dot = ModernLabel(status_container,
                                text="●",
                                font=Fonts.MEDIUM,
                                fg=Colors.PURPLE_PRIMARY)
        status_dot.pack(side=tk.LEFT, padx=(0, Styling.PADDING_MEDIUM), pady=Styling.PADDING_MEDIUM)
    
    def create_control_buttons(self, parent: tk.Frame, callbacks: dict) -> None:
        """
        Create modern control buttons with improved styling.
        
        Args:
            parent: Parent frame for the buttons
            callbacks: Dictionary mapping button names to callback functions
        """
        # Button container with modern spacing
        button_container = ModernFrame(parent)
        button_container.pack(fill=tk.X, padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        # Button configurations with modern styling
        button_configs = [
            ("📁 Select Folder", "select_folder", "success"),
            ("💾 Save Progress", "save_data", "primary"),
            ("📂 Load Progress", "load_data", "primary"),
            ("📊 View Stats", "show_stats", "secondary"),
            ("🔍 Prompt Analysis", "show_prompt_analysis", "secondary"),
            ("⚙️ Settings", "show_settings", "ghost")
        ]
        
        for text, callback_key, style in button_configs:
            if callback_key in callbacks:
                btn = ModernButton(button_container, 
                                 text=text,
                                 command=callbacks[callback_key],
                                 style=style,
                                 font=Fonts.MEDIUM)
                btn.pack(side=tk.LEFT, padx=(0, Styling.PADDING_MEDIUM))
    
    def maximize_window(self) -> None:
        """Maximize the window in a platform-independent way."""
        try:
            self.parent.state('zoomed')  # Windows
        except tk.TclError:
            try:
                self.parent.attributes('-zoomed', True)  # Linux
            except tk.TclError:
                # macOS or other platforms - just make it large
                self.parent.geometry("1400x900")
    
    def setup_window_properties(self) -> None:
        """Setup modern window properties."""
        self.parent.title("Image Ranking System")
        self.parent.geometry("1400x900")
        
        # Set window icon background
        self.parent.configure(bg=Colors.BG_PRIMARY)
        
        # Try to set window attributes for better appearance
        try:
            self.parent.attributes('-alpha', 0.98)  # Subtle transparency
        except:
            pass
        
        self.maximize_window()
    
    def create_modern_image_containers(self, parent: tk.Frame) -> tuple:
        """
        Create modern image containers with sleek card-like appearance.
        
        Args:
            parent: Parent frame
            
        Returns:
            Tuple of (left_container, right_container, vs_frame)
        """
        # Configure grid for modern layout
        parent.grid_columnconfigure(0, weight=1, uniform="equal", minsize=450)
        parent.grid_columnconfigure(1, weight=0, minsize=100)  # VS section
        parent.grid_columnconfigure(2, weight=1, uniform="equal", minsize=450)
        parent.grid_rowconfigure(0, weight=1, minsize=600)
        
        # Left image container - modern card style
        left_container = ModernFrame(parent, style='card')
        left_container.grid(row=0, column=0, sticky="nsew", padx=(Styling.PADDING_LARGE, Styling.PADDING_MEDIUM))
        
        # VS section with modern styling
        vs_frame = ModernFrame(parent)
        vs_frame.grid(row=0, column=1, sticky="nsew", padx=Styling.PADDING_SMALL)
        
        # Create VS label with modern design
        vs_container = ModernFrame(vs_frame, style='card')
        vs_container.pack(fill=tk.BOTH, expand=True, pady=Styling.PADDING_LARGE)
        
        vs_label = ModernLabel(vs_container,
                              text="VS",
                              font=Fonts.DISPLAY,
                              fg=Colors.PURPLE_PRIMARY)
        vs_label.pack(expand=True)
        
        # Right image container - modern card style
        right_container = ModernFrame(parent, style='card')
        right_container.grid(row=0, column=2, sticky="nsew", padx=(Styling.PADDING_MEDIUM, Styling.PADDING_LARGE))
        
        return left_container, right_container, vs_frame
    
    def create_modern_image_frame(self, parent: tk.Frame, side: str) -> dict:
        """
        Create a modern image display frame with sleek styling.
        
        Args:
            parent: Parent frame
            side: 'left' or 'right'
            
        Returns:
            Dictionary with frame components
        """
        # Configure frame grid
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1, minsize=450)     # Image area
        parent.grid_rowconfigure(1, weight=0, minsize=80)     # Info area
        parent.grid_rowconfigure(2, weight=0, minsize=100)    # Metadata area
        parent.grid_rowconfigure(3, weight=0, minsize=60)     # Button area
        
        # Image display area with modern styling
        image_frame = ModernFrame(parent)
        image_frame.grid(row=0, column=0, sticky="nsew", padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        image_label = ModernLabel(image_frame,
                                 text="No image",
                                 bg=Colors.BG_TERTIARY,
                                 fg=Colors.TEXT_SECONDARY,
                                 font=Fonts.MEDIUM,
                                 cursor="hand2")
        image_label.pack(fill=tk.BOTH, expand=True)
        
        # Info area with modern card styling
        info_frame = ModernFrame(parent, style='card')
        info_frame.grid(row=1, column=0, sticky="ew", padx=Styling.PADDING_LARGE, pady=(0, Styling.PADDING_SMALL))
        
        info_label = ModernLabel(info_frame,
                                text="",
                                font=Fonts.MEDIUM,
                                fg=Colors.TEXT_PRIMARY)
        info_label.pack(padx=Styling.PADDING_MEDIUM, pady=Styling.PADDING_MEDIUM)
        
        # Metadata area with modern styling
        metadata_frame = ModernFrame(parent, style='card')
        metadata_frame.grid(row=2, column=0, sticky="ew", padx=Styling.PADDING_LARGE, pady=(0, Styling.PADDING_SMALL))
        
        metadata_label = ModernLabel(metadata_frame,
                                    text="",
                                    font=Fonts.SMALL,
                                    fg=Colors.TEXT_SECONDARY,
                                    justify=tk.LEFT,
                                    wraplength=400)
        metadata_label.pack(padx=Styling.PADDING_MEDIUM, pady=Styling.PADDING_MEDIUM, fill=tk.X)
        
        # Button area
        button_frame = ModernFrame(parent)
        button_frame.grid(row=3, column=0, sticky="ew", padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        return {
            'image_label': image_label,
            'info_label': info_label,
            'metadata_label': metadata_label,
            'button_frame': button_frame
        }
    
    def create_vote_button(self, parent: tk.Frame, text: str, command, side: str) -> ModernButton:
        """
        Create a modern vote button with dynamic styling.
        
        Args:
            parent: Parent frame
            text: Button text
            command: Button command
            side: 'left' or 'right'
            
        Returns:
            ModernButton instance
        """
        # Use different accent for left vs right
        style = 'success' if side == 'left' else 'primary'
        
        button = ModernButton(parent,
                             text=text,
                             command=command,
                             style=style,
                             font=Fonts.HEADING,
                             state=tk.DISABLED)
        
        button.pack(fill=tk.X, padx=Styling.PADDING_MEDIUM, pady=Styling.PADDING_MEDIUM)
        
        return button
    
    def get_ui_references(self) -> dict:
        """
        Get references to important UI elements.
        
        Returns:
            Dictionary containing UI element references
        """
        return {
            'folder_label': self.folder_label,
            'stats_label': self.stats_label,
            'status_bar': self.status_bar
        }
    
    def update_status_with_animation(self, message: str, color: str = None) -> None:
        """
        Update status bar with subtle animation effect.
        
        Args:
            message: Status message
            color: Optional color override
        """
        if self.status_bar:
            # Set color based on message type if not specified
            if color is None:
                if "error" in message.lower() or "failed" in message.lower():
                    color = Colors.ERROR
                elif "success" in message.lower() or "complete" in message.lower():
                    color = Colors.SUCCESS
                elif "loading" in message.lower() or "processing" in message.lower():
                    color = Colors.PURPLE_PRIMARY
                else:
                    color = Colors.TEXT_SECONDARY
            
            self.status_bar.config(text=message, fg=color)
