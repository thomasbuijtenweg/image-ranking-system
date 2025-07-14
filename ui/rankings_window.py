"""
Rankings window module for the Image Ranking System.

This module implements the rankings display window that shows images
ranked by various metrics like tier, win rate, and total votes.
Now includes image preview functionality on hover using the ImagePreviewMixin.

By separating this window logic into its own module, we create a
clean separation of concerns and make the code more maintainable.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Tuple, Any
import os

from config import Colors
from ui.mixins import ImagePreviewMixin


class RankingsWindow(ImagePreviewMixin):
    """
    Window for displaying image rankings across different metrics.
    
    This window provides tabbed views of rankings sorted by various
    criteria, giving users insight into how images are performing
    in the ranking system. Now includes image preview on hover using
    the ImagePreviewMixin.
    """
    
    def __init__(self, parent: tk.Tk, data_manager, ranking_algorithm):
        """
        Initialize the rankings window.
        
        Args:
            parent: Parent window
            data_manager: DataManager instance
            ranking_algorithm: RankingAlgorithm instance
        """
        # Initialize the mixin
        ImagePreviewMixin.__init__(self)
        
        self.parent = parent
        self.data_manager = data_manager
        self.ranking_algorithm = ranking_algorithm
        self.window = None
        self.trees = {}  # Store tree references for navigation
    
    def show(self):
        """Show the rankings window, creating it if necessary."""
        if self.window is None or not self.window.winfo_exists():
            self.create_window()
        else:
            self.window.lift()
            self.window.focus_force()
    
    def create_window(self):
        """Create the rankings window with all its components."""
        # Import here to avoid circular imports
        from core.image_processor import ImageProcessor
        self.image_processor = ImageProcessor()
        
        self.window = tk.Toplevel(self.parent)
        self.window.title("Image Rankings")
        self.window.geometry("1800x900")  # Even larger window for optimal preview experience
        self.window.minsize(1200, 600)  # Set minimum window size to prevent cramped layout
        self.window.configure(bg=Colors.BG_PRIMARY)
        
        # Handle window closing
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # Setup resize handling from mixin
        self.setup_preview_resize_handling()
        
        # Create main frame
        main_frame = tk.Frame(self.window, bg=Colors.BG_PRIMARY)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create navigation frame
        nav_frame = tk.Frame(main_frame, bg=Colors.BG_PRIMARY)
        nav_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create content frame (will contain notebook and image preview)
        content_frame = tk.Frame(main_frame, bg=Colors.BG_PRIMARY)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure content frame grid - Fixed ratio: 40% rankings, 60% image preview
        content_frame.grid_columnconfigure(0, weight=2, minsize=600)  # Rankings take 40% of width
        content_frame.grid_columnconfigure(1, weight=3, minsize=800)  # Image preview takes 60% of width
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Create notebook for different ranking tabs
        notebook = ttk.Notebook(content_frame)
        notebook.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Create image preview area using mixin
        preview_frame = self.create_image_preview_area(content_frame, include_additional_stats=False)
        preview_frame.grid(row=0, column=1, sticky="nsew")
        
        # Get current rankings
        rankings = self.ranking_algorithm.calculate_all_rankings()
        
        # Create tabs for each ranking type
        self.create_ranking_tabs(notebook, rankings)
        
        # Create navigation buttons
        self.create_navigation_buttons(nav_frame, notebook)
    
    def create_ranking_tabs(self, notebook: ttk.Notebook, rankings: Dict[str, List[Tuple[str, Dict[str, Any]]]]):
        """
        Create tabs for different ranking metrics.
        
        Args:
            notebook: The notebook widget to add tabs to
            rankings: Dictionary of ranking data from the algorithm
        """
        ranking_types = [
            ("Current Tier", 'current_tier', "Highest tier first"),
            ("Win Rate", 'win_rate', "Highest win percentage first"),
            ("Total Votes", 'total_votes', "Most voted images first"),
            ("Stability", 'tier_stability', "Most stable tier (lowest std dev) first"),
            ("Recently Voted", 'recency', "Least recently voted first")
        ]
        
        for tab_name, ranking_key, description in ranking_types:
            # Create frame for tab
            frame = tk.Frame(notebook, bg=Colors.BG_SECONDARY)
            notebook.add(frame, text=tab_name)
            
            # Add description
            tk.Label(frame, text=description, font=('Arial', 10, 'italic'), 
                    fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(pady=5)
            
            # Create the ranking tree
            tree = self.create_ranking_tree(frame, ranking_key, rankings[ranking_key])
            self.trees[tab_name] = tree
    
    def create_ranking_tree(self, parent: tk.Frame, ranking_key: str, 
                           ranking_data: List[Tuple[str, Dict[str, Any]]]) -> ttk.Treeview:
        """
        Create a treeview for displaying ranking data.
        
        Args:
            parent: Parent frame
            ranking_key: Key for the ranking metric
            ranking_data: List of (image_name, metrics) tuples
            
        Returns:
            The created treeview widget
        """
        # Create scrollable frame
        tree_frame = tk.Frame(parent, bg=Colors.BG_SECONDARY)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create treeview with scrollbar
        columns = ('Rank', 'Image', 'Value', 'Votes', 'Wins', 'Losses', 'Stability', 'Prompt')
        tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', height=20)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure columns
        tree.heading('Rank', text='Rank')
        tree.heading('Image', text='Image')
        tree.heading('Value', text=ranking_key.replace('_', ' ').title())
        tree.heading('Votes', text='Total Votes')
        tree.heading('Wins', text='Wins')
        tree.heading('Losses', text='Losses')
        tree.heading('Stability', text='Stability')
        tree.heading('Prompt', text='Prompt')
        
        # Set column widths
        tree.column('#0', width=0, stretch=False)
        tree.column('Rank', width=50)
        tree.column('Image', width=150)
        tree.column('Value', width=100)
        tree.column('Votes', width=80)
        tree.column('Wins', width=60)
        tree.column('Losses', width=60)
        tree.column('Stability', width=80)
        tree.column('Prompt', width=300)  # Wider for better prompt display
        
        # Add data to tree
        self.populate_ranking_tree(tree, ranking_key, ranking_data)
        
        # Bind hover events
        tree.bind('<Motion>', self.on_tree_hover)
        tree.bind('<Leave>', self.on_tree_leave)
        
        # Pack tree and scrollbar
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        return tree
    
    def populate_ranking_tree(self, tree: ttk.Treeview, ranking_key: str, 
                             ranking_data: List[Tuple[str, Dict[str, Any]]]):
        """
        Populate a treeview with ranking data.
        
        Args:
            tree: The treeview to populate
            ranking_key: Key for the ranking metric
            ranking_data: List of (image_name, metrics) tuples
        """
        for rank, (img, metrics) in enumerate(ranking_data, 1):
            stats = self.data_manager.get_image_stats(img)
            value = metrics[ranking_key]
            
            # Format value based on type
            if ranking_key == 'win_rate':
                value_str = f"{value:.1%}"
            elif ranking_key == 'tier_stability':
                value_str = f"{value:.2f}"
            elif ranking_key == 'recency':
                value_str = f"{int(value)} votes ago" if value != float('inf') else "Never"
            else:
                value_str = str(int(value))
            
            # Calculate individual stability
            stability = self.ranking_algorithm._calculate_tier_stability(img)
            
            # Get prompt if available - show more text
            prompt = stats.get('prompt', 'No prompt found')
            if prompt and len(prompt) > 80:  # Show more characters
                prompt = prompt[:77] + "..."
            
            # Insert row into tree with image filename as tag
            item = tree.insert('', tk.END, values=(
                rank, img, value_str, 
                stats.get('votes', 0), stats.get('wins', 0), stats.get('losses', 0), 
                f"{stability:.2f}", prompt
            ), tags=(img,))  # Use filename as tag for hover detection
    
    def on_tree_hover(self, event):
        """Handle mouse hover over tree items."""
        tree = event.widget
        item = tree.identify_row(event.y)
        
        if item:
            # Get the image filename from the item's tags
            tags = tree.item(item, 'tags')
            if tags:
                image_filename = tags[0]
                self.display_preview_image(image_filename)
    
    def on_tree_leave(self, event):
        """Handle mouse leaving the tree."""
        # You might want to clear the preview or keep it - keeping it for now
        pass
    
    def create_navigation_buttons(self, nav_frame: tk.Frame, notebook: ttk.Notebook):
        """
        Create navigation buttons for the rankings window.
        
        Args:
            nav_frame: Frame to contain navigation buttons
            notebook: Notebook widget for tab operations
        """
        def jump_to_top():
            current_tab = notebook.tab('current')['text']
            if current_tab in self.trees:
                tree = self.trees[current_tab]
                children = tree.get_children()
                if children:
                    tree.see(children[0])
                    tree.selection_set(children[0])
        
        def jump_to_bottom():
            current_tab = notebook.tab('current')['text']
            if current_tab in self.trees:
                tree = self.trees[current_tab]
                children = tree.get_children()
                if children:
                    tree.see(children[-1])
                    tree.selection_set(children[-1])
        
        tk.Button(nav_frame, text="Jump to Top", command=jump_to_top, 
                 bg=Colors.BUTTON_BG, fg=Colors.TEXT_PRIMARY, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        tk.Button(nav_frame, text="Jump to Bottom", command=jump_to_bottom, 
                 bg=Colors.BUTTON_BG, fg=Colors.TEXT_PRIMARY, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        # Add instruction label
        tk.Label(nav_frame, text="Hover over any image in the rankings to see a large preview →", 
                font=('Arial', 10, 'italic'), fg=Colors.TEXT_SECONDARY, bg=Colors.BG_PRIMARY).pack(side=tk.RIGHT, padx=20)
    
    def close_window(self):
        """Handle window closing."""
        # Clean up preview resources using mixin
        self.cleanup_preview_resources()
        
        if self.window:
            self.window.destroy()
            self.window = None