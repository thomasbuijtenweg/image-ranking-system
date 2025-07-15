"""
UI builder for the Image Ranking System.

This module handles the creation and layout of UI widgets
for the main window.
"""

import tkinter as tk
from tkinter import ttk

from config import Colors, Defaults


class UIBuilder:
    """
    Handles UI widget creation and layout for the main window.
    
    This class centralizes the UI construction logic to keep
    the main window focused on coordination.
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
        
        # Setup dark theme
        self._setup_dark_theme()
    
    def _setup_dark_theme(self) -> None:
        """Configure ttk styles for dark mode."""
        style = ttk.Style()
        
        try:
            style.theme_use('clam')  # clam theme works better for customization
        except:
            pass
        
        # Configure Treeview for dark mode
        style.configure("Treeview",
                       background=Colors.BG_SECONDARY,
                       foreground=Colors.TEXT_PRIMARY,
                       fieldbackground=Colors.BG_SECONDARY,
                       borderwidth=0,
                       selectbackground=Colors.BUTTON_HOVER,
                       selectforeground=Colors.TEXT_PRIMARY)
        
        style.configure("Treeview.Heading",
                       background=Colors.BUTTON_BG,
                       foreground=Colors.TEXT_PRIMARY,
                       borderwidth=1,
                       relief=tk.FLAT,
                       font=('Arial', 10, 'bold'))
        
        # Configure other ttk widgets
        style.configure("TNotebook", background=Colors.BG_PRIMARY, borderwidth=0)
        style.configure("TNotebook.Tab", 
                       background=Colors.BUTTON_BG,
                       foreground=Colors.TEXT_PRIMARY,
                       padding=[20, 10],
                       borderwidth=0,
                       focuscolor='none')
    
    def build_main_ui(self) -> dict:
        """
        Build the main UI layout.
        
        Returns:
            Dictionary containing references to important UI elements
        """
        # Configure main window
        self.parent.configure(bg=Colors.BG_PRIMARY)
        self.parent.minsize(800, 600)
        
        # Create main components
        top_frame = self._create_top_frame()
        main_frame = self._create_main_frame()
        self._create_status_bar()
        
        return {
            'top_frame': top_frame,
            'main_frame': main_frame,
            'folder_label': self.folder_label,
            'stats_label': self.stats_label,
            'status_bar': self.status_bar
        }
    
    def _create_top_frame(self) -> tk.Frame:
        """Create the top frame with buttons and status information."""
        top_frame = tk.Frame(self.parent, bg=Colors.BG_PRIMARY)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Folder and stats labels
        self.folder_label = tk.Label(top_frame, text="No folder selected", 
                                   fg=Colors.TEXT_SECONDARY, bg=Colors.BG_PRIMARY)
        self.folder_label.pack(side=tk.LEFT, padx=20)
        
        self.stats_label = tk.Label(top_frame, text="Total votes: 0", 
                                  font=('Arial', 10, 'bold'), 
                                  fg=Colors.TEXT_PRIMARY, bg=Colors.BG_PRIMARY)
        self.stats_label.pack(side=tk.RIGHT, padx=10)
        
        return top_frame
    
    def _create_main_frame(self) -> tk.Frame:
        """Create the main voting area with image display."""
        main_frame = tk.Frame(self.parent, bg=Colors.BG_PRIMARY)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        return main_frame
    
    def _create_status_bar(self) -> None:
        """Create the status bar at the bottom of the window."""
        self.status_bar = tk.Label(self.parent, text="Select a folder to begin", 
                                 relief=tk.SUNKEN, anchor=tk.W, 
                                 bg=Colors.BUTTON_BG, fg=Colors.TEXT_PRIMARY)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_control_buttons(self, parent: tk.Frame, callbacks: dict) -> None:
        """
        Create the control buttons in the specified parent frame.
        
        Args:
            parent: Parent frame for the buttons
            callbacks: Dictionary mapping button names to callback functions
        """
        button_configs = [
            ("Select Image Folder", "select_folder", Colors.BUTTON_SUCCESS),
            ("Save Progress", "save_data", Colors.BUTTON_INFO),
            ("Load Progress", "load_data", Colors.BUTTON_INFO),
            ("View Stats", "show_stats", Colors.BUTTON_WARNING),
            ("Prompt Analysis", "show_prompt_analysis", Colors.BUTTON_INFO),
            ("Settings", "show_settings", Colors.BUTTON_NEUTRAL)
        ]
        
        for text, callback_key, color in button_configs:
            if callback_key in callbacks:
                tk.Button(parent, text=text, command=callbacks[callback_key], 
                         bg=color, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
    
    def maximize_window(self) -> None:
        """Maximize the window in a platform-independent way."""
        try:
            self.parent.state('zoomed')  # Windows
        except tk.TclError:
            try:
                self.parent.attributes('-zoomed', True)  # Linux
            except tk.TclError:
                # macOS or other platforms - just make it large
                self.parent.geometry("1200x800")
    
    def setup_window_properties(self) -> None:
        """Setup basic window properties."""
        self.parent.title("Image Ranking System")
        self.parent.geometry(f"{Defaults.WINDOW_WIDTH}x{Defaults.WINDOW_HEIGHT}")
        self.maximize_window()
    
    def create_image_frame_containers(self, parent: tk.Frame) -> tuple:
        """
        Create containers for image frames that can be passed to other components.
        
        Args:
            parent: Parent frame
            
        Returns:
            Tuple of (left_container, right_container)
        """
        # Configure grid for equal distribution with minimum sizes
        parent.grid_columnconfigure(0, weight=1, uniform="equal", minsize=400)
        parent.grid_columnconfigure(1, weight=0, minsize=80)  # VS label column
        parent.grid_columnconfigure(2, weight=1, uniform="equal", minsize=400)
        parent.grid_rowconfigure(0, weight=1, minsize=500)
        
        # Create containers that other components can populate
        left_container = tk.Frame(parent, relief=tk.RAISED, borderwidth=2, bg=Colors.BG_SECONDARY)
        left_container.grid(row=0, column=0, sticky="nsew", padx=5)
        
        right_container = tk.Frame(parent, relief=tk.RAISED, borderwidth=2, bg=Colors.BG_SECONDARY)
        right_container.grid(row=0, column=2, sticky="nsew", padx=5)
        
        # Create VS label
        vs_label = tk.Label(parent, text="VS", font=('Arial', 24, 'bold'), 
                          fg=Colors.TEXT_PRIMARY, bg=Colors.BG_PRIMARY)
        vs_label.grid(row=0, column=1, padx=20)
        
        return left_container, right_container
    
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
