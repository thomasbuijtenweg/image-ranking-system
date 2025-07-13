"""
Rankings window module for the Image Ranking System.

This module implements the rankings display window that shows images
ranked by various metrics like tier, win rate, and total votes.

By separating this window logic into its own module, we create a
clean separation of concerns and make the code more maintainable.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Tuple, Any

from config import Colors


class RankingsWindow:
    """
    Window for displaying image rankings across different metrics.
    
    This window provides tabbed views of rankings sorted by various
    criteria, giving users insight into how images are performing
    in the ranking system.
    """
    
    def __init__(self, parent: tk.Tk, data_manager, ranking_algorithm):
        """
        Initialize the rankings window.
        
        Args:
            parent: Parent window
            data_manager: DataManager instance
            ranking_algorithm: RankingAlgorithm instance
        """
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
        self.window = tk.Toplevel(self.parent)
        self.window.title("Image Rankings")
        self.window.geometry("1000x700")
        self.window.configure(bg=Colors.BG_PRIMARY)
        
        # Handle window closing
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # Create main frame
        main_frame = tk.Frame(self.window, bg=Colors.BG_PRIMARY)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create navigation frame
        nav_frame = tk.Frame(main_frame, bg=Colors.BG_PRIMARY)
        nav_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create notebook for different ranking tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
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
        tree.column('Image', width=120)
        tree.column('Value', width=80)
        tree.column('Votes', width=60)
        tree.column('Wins', width=50)
        tree.column('Losses', width=50)
        tree.column('Stability', width=70)
        tree.column('Prompt', width=300)
        
        # Add data to tree
        self.populate_ranking_tree(tree, ranking_key, ranking_data)
        
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
            
            # Get prompt if available
            prompt = stats.get('prompt', 'No prompt found')
            if prompt and len(prompt) > 60:
                prompt = prompt[:57] + "..."
            
            # Insert row into tree
            tree.insert('', tk.END, values=(
                rank, img, value_str, 
                stats.get('votes', 0), stats.get('wins', 0), stats.get('losses', 0), 
                f"{stability:.2f}", prompt
            ))
    
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
    
    def close_window(self):
        """Handle window closing."""
        if self.window:
            self.window.destroy()
            self.window = None