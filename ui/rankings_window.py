"""
Rankings window module for the Image Ranking System.

This module implements the rankings display window that shows images
ranked by various metrics like tier, win rate, and total votes.
Now includes image preview functionality on hover.

By separating this window logic into its own module, we create a
clean separation of concerns and make the code more maintainable.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Tuple, Any
import os

from config import Colors


class RankingsWindow:
    """
    Window for displaying image rankings across different metrics.
    
    This window provides tabbed views of rankings sorted by various
    criteria, giving users insight into how images are performing
    in the ranking system. Now includes image preview on hover.
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
        self.image_label = None  # For displaying preview images
        self.current_image = None  # Current displayed image reference
        self.image_processor = None  # Will be set when window is created
        self.resize_timer = None  # Timer for resize debouncing
        self.current_displayed_image = None  # Track current image for resize refresh
    
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
        
        # Handle window resize events
        self.window.bind('<Configure>', self.on_window_resize)
        self.resize_timer = None
        self.current_displayed_image = None  # Track current image for resize refresh
        
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
        
        # Create image preview area
        self.create_image_preview_area(content_frame)
        
        # Get current rankings
        rankings = self.ranking_algorithm.calculate_all_rankings()
        
        # Create tabs for each ranking type
        self.create_ranking_tabs(notebook, rankings)
        
        # Create navigation buttons
        self.create_navigation_buttons(nav_frame, notebook)
    
    def create_image_preview_area(self, parent):
        """Create the image preview area on the right side."""
        preview_frame = tk.Frame(parent, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=2)
        preview_frame.grid(row=0, column=1, sticky="nsew")
        
        # Configure preview frame grid - text areas have fixed minimum sizes
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=0, minsize=50)   # Title - fixed
        preview_frame.grid_rowconfigure(1, weight=1, minsize=400) # Image - expandable with minimum
        preview_frame.grid_rowconfigure(2, weight=0, minsize=60)  # Info - fixed minimum
        preview_frame.grid_rowconfigure(3, weight=0, minsize=120) # Prompt - fixed minimum
        
        # Title - fixed height
        title_label = tk.Label(preview_frame, text="Image Preview", 
                              font=('Arial', 14, 'bold'), 
                              fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY,
                              height=2)
        title_label.grid(row=0, column=0, sticky="ew", pady=5)
        
        # Image display area - expandable, takes remaining space
        self.image_label = tk.Label(preview_frame, text="Hover over an image\nin the rankings to preview", 
                                   bg=Colors.BG_TERTIARY, fg=Colors.TEXT_SECONDARY,
                                   font=('Arial', 12), justify=tk.CENTER)
        self.image_label.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # Image info label - fixed minimum height
        self.image_info_label = tk.Label(preview_frame, text="", 
                                        font=('Arial', 11), 
                                        fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY,
                                        justify=tk.CENTER, height=3)
        self.image_info_label.grid(row=2, column=0, sticky="ew", pady=2)
        
        # Prompt display area - fixed minimum height
        prompt_frame = tk.Frame(preview_frame, bg=Colors.BG_SECONDARY)
        prompt_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        prompt_frame.grid_columnconfigure(0, weight=1)
        prompt_frame.grid_rowconfigure(0, weight=0)
        prompt_frame.grid_rowconfigure(1, weight=1)
        
        # Prompt label
        tk.Label(prompt_frame, text="Prompt:", font=('Arial', 10, 'bold'), 
                fg=Colors.TEXT_SUCCESS, bg=Colors.BG_SECONDARY).grid(row=0, column=0, sticky="w")
        
        # Scrollable text widget for full prompt - fixed height
        self.prompt_text = tk.Text(prompt_frame, height=4, wrap=tk.WORD, 
                                  bg=Colors.BG_TERTIARY, fg=Colors.TEXT_PRIMARY, 
                                  font=('Arial', 10), relief=tk.FLAT, state=tk.DISABLED)
        prompt_scrollbar = ttk.Scrollbar(prompt_frame, orient="vertical", command=self.prompt_text.yview)
        self.prompt_text.configure(yscrollcommand=prompt_scrollbar.set)
        
        self.prompt_text.grid(row=1, column=0, sticky="ew", pady=2)
        prompt_scrollbar.grid(row=1, column=1, sticky="ns")
    
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
    
    def display_preview_image(self, filename: str):
        """Display a preview image in the preview area."""
        if not filename or not self.data_manager.image_folder:
            return
        
        try:
            img_path = os.path.join(self.data_manager.image_folder, filename)
            if not os.path.exists(img_path):
                return
            
            # Force window to update and get actual dimensions
            self.window.update_idletasks()
            
            # Get the actual size of the image label area after layout
            label_width = self.image_label.winfo_width()
            label_height = self.image_label.winfo_height()
            
            # Only proceed if we have valid dimensions (widget has been rendered)
            if label_width <= 1 or label_height <= 1:
                # Widget not yet rendered, try again after a short delay
                self.window.after(100, lambda: self.display_preview_image(filename))
                return
            
            # Use almost all available space, leaving small margin, but with reasonable minimums
            preview_width = max(label_width - 10, 300)
            preview_height = max(label_height - 10, 300)
            
            # Load and resize image to fill the available space
            photo = self.image_processor.load_and_resize_image(
                img_path, preview_width, preview_height)
            
            if photo:
                # Clear old image reference
                self.current_image = None
                
                # Update image display
                self.image_label.config(image=photo, text="")
                self.current_image = photo  # Keep reference to prevent garbage collection
                
                # Store the current image filename for resize refreshing
                self.current_displayed_image = filename
                
                # Update info label
                stats = self.data_manager.get_image_stats(filename)
                votes = stats.get('votes', 0)
                wins = stats.get('wins', 0)
                win_rate = wins / max(votes, 1) if votes > 0 else 0
                
                info_text = (f"{filename}\n"
                            f"Tier: {stats.get('current_tier', 0)} | "
                            f"Votes: {votes} | "
                            f"Win Rate: {win_rate:.1%}")
                self.image_info_label.config(text=info_text)
                
                # Update prompt display with full text
                prompt = stats.get('prompt', '')
                self.prompt_text.config(state=tk.NORMAL)
                self.prompt_text.delete(1.0, tk.END)
                if prompt:
                    self.prompt_text.insert(1.0, prompt)
                else:
                    self.prompt_text.insert(1.0, "No prompt information available")
                self.prompt_text.config(state=tk.DISABLED)
                
            else:
                # Handle image loading failure
                self.image_label.config(image="", text="Failed to load image")
                self.image_info_label.config(text=f"Error loading: {filename}")
                self.prompt_text.config(state=tk.NORMAL)
                self.prompt_text.delete(1.0, tk.END)
                self.prompt_text.insert(1.0, "Error loading image")
                self.prompt_text.config(state=tk.DISABLED)
                self.current_image = None
                
        except Exception as e:
            print(f"Error displaying preview for {filename}: {e}")
            self.image_label.config(image="", text="Error loading image")
            self.image_info_label.config(text=f"Error: {filename}")
            self.prompt_text.config(state=tk.NORMAL)
            self.prompt_text.delete(1.0, tk.END)
            self.prompt_text.insert(1.0, "Error loading image")
            self.prompt_text.config(state=tk.DISABLED)
            self.current_image = None
    
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
    
    def on_window_resize(self, event):
        """Handle window resize events with debouncing."""
        if event.widget == self.window:
            # Cancel previous timer if it exists
            if self.resize_timer:
                self.window.after_cancel(self.resize_timer)
            
            # Set a new timer to refresh image after resize stops
            self.resize_timer = self.window.after(300, self.refresh_current_image)
    
    def refresh_current_image(self):
        """Refresh the currently displayed image with new size."""
        if self.current_displayed_image:
            self.display_preview_image(self.current_displayed_image)
    
    def close_window(self):
        """Handle window closing."""
        # Cancel any pending resize timer
        if self.resize_timer:
            self.window.after_cancel(self.resize_timer)
        
        # Clear image references
        self.current_image = None
        self.current_displayed_image = None
        if self.image_label:
            self.image_label.config(image="")
        if hasattr(self, 'prompt_text') and self.prompt_text:
            self.prompt_text.config(state=tk.NORMAL)
            self.prompt_text.delete(1.0, tk.END)
        
        # Clean up image processor
        if self.image_processor:
            self.image_processor.cleanup_resources()
        
        if self.window:
            self.window.destroy()
            self.window = None