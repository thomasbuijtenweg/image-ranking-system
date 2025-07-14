"""
Rankings window module for the Image Ranking System.

This module implements the rankings display window that shows images
in a single sortable table instead of multiple redundant tabs.
Now includes image preview functionality on hover using the ImagePreviewMixin.

By using a single sortable table, we create a more efficient and
user-friendly interface that eliminates redundant information display.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Tuple, Any
import os

from config import Colors
from ui.mixins import ImagePreviewMixin


class RankingsWindow(ImagePreviewMixin):
    """
    Window for displaying image rankings in a single sortable table.
    
    This window provides a comprehensive view of all ranking metrics
    in one sortable table, giving users efficient access to ranking
    information with image preview on hover using the ImagePreviewMixin.
    """
    
    def __init__(self, parent: tk.Tk, data_manager, ranking_algorithm, prompt_analyzer):
        """
        Initialize the rankings window.
        
        Args:
            parent: Parent window
            data_manager: DataManager instance
            ranking_algorithm: RankingAlgorithm instance
            prompt_analyzer: PromptAnalyzer instance
        """
        # Initialize the mixin
        ImagePreviewMixin.__init__(self)
        
        self.parent = parent
        self.data_manager = data_manager
        self.ranking_algorithm = ranking_algorithm
        self.prompt_analyzer = prompt_analyzer
        self.window = None
        self.rankings_tree = None
        self.current_sort_column = None
        self.current_sort_reverse = False
    
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
        self.window.geometry("1800x900")  # Large window for optimal table and preview experience
        self.window.minsize(1200, 600)  # Set minimum window size to prevent cramped layout
        self.window.configure(bg=Colors.BG_PRIMARY)
        
        # Handle window closing
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # Setup resize handling from mixin
        self.setup_preview_resize_handling()
        
        # Create main frame
        main_frame = tk.Frame(self.window, bg=Colors.BG_PRIMARY)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure main frame grid - 50% rankings table, 50% image preview
        main_frame.grid_columnconfigure(0, weight=1, minsize=700)  # Rankings table
        main_frame.grid_columnconfigure(1, weight=1, minsize=700)  # Image preview
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Create rankings table frame
        rankings_frame = tk.Frame(main_frame, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=2)
        rankings_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Create image preview area using mixin
        preview_frame = self.create_image_preview_area(main_frame, include_additional_stats=False)
        preview_frame.grid(row=0, column=1, sticky="nsew")
        
        # Create the rankings table
        self.create_rankings_table(rankings_frame)
    
    def create_rankings_table(self, parent: tk.Frame):
        """Create the main rankings table with sortable columns."""
        # Create header with title and instructions
        header_frame = tk.Frame(parent, bg=Colors.BG_SECONDARY)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Title
        tk.Label(header_frame, text="Image Rankings", font=('Arial', 16, 'bold'), 
                fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        # Calculate basic statistics
        total_images = len(self.data_manager.image_stats)
        total_votes = self.data_manager.vote_count
        
        # Instructions
        instruction_text = f"Total Images: {total_images} | Total Votes: {total_votes} | Click column headers to sort • Hover over any row to see image preview"
        tk.Label(header_frame, text=instruction_text, font=('Arial', 10, 'italic'), 
                fg=Colors.TEXT_INFO, bg=Colors.BG_SECONDARY).pack(anchor=tk.W, pady=(5, 0))
        
        # Create frame for the table
        table_frame = tk.Frame(parent, bg=Colors.BG_SECONDARY)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Define columns
        columns = ('Rank', 'Image', 'Tier', 'Votes', 'Wins', 'Losses', 'Win Rate', 'Stability', 'Recency', 'Prompt Preview')
        
        # Create treeview with scrollbar
        self.rankings_tree = ttk.Treeview(table_frame, columns=columns, show='tree headings', height=25)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.rankings_tree.yview)
        self.rankings_tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure column headings with click handlers
        self.rankings_tree.heading('#0', text='', anchor=tk.W)
        self.rankings_tree.heading('Rank', text='Rank', anchor=tk.CENTER)
        self.rankings_tree.heading('Image', text='Image Name', anchor=tk.W)
        self.rankings_tree.heading('Tier', text='Current Tier', anchor=tk.CENTER)
        self.rankings_tree.heading('Votes', text='Total Votes', anchor=tk.CENTER)
        self.rankings_tree.heading('Wins', text='Wins', anchor=tk.CENTER)
        self.rankings_tree.heading('Losses', text='Losses', anchor=tk.CENTER)
        self.rankings_tree.heading('Win Rate', text='Win Rate %', anchor=tk.CENTER)
        self.rankings_tree.heading('Stability', text='Stability', anchor=tk.CENTER)
        self.rankings_tree.heading('Recency', text='Recency', anchor=tk.CENTER)
        self.rankings_tree.heading('Prompt Preview', text='Prompt Preview', anchor=tk.W)
        
        # Set column widths
        self.rankings_tree.column('#0', width=0, stretch=False)
        self.rankings_tree.column('Rank', width=60)
        self.rankings_tree.column('Image', width=180)
        self.rankings_tree.column('Tier', width=80)
        self.rankings_tree.column('Votes', width=80)
        self.rankings_tree.column('Wins', width=60)
        self.rankings_tree.column('Losses', width=60)
        self.rankings_tree.column('Win Rate', width=80)
        self.rankings_tree.column('Stability', width=80)
        self.rankings_tree.column('Recency', width=90)
        self.rankings_tree.column('Prompt Preview', width=300)
        
        # Bind click events to column headers for sorting
        for col in columns:
            self.rankings_tree.heading(col, command=lambda c=col: self.sort_by_column(c))
        
        # Bind hover events
        self.rankings_tree.bind('<Motion>', self.on_rankings_tree_hover)
        self.rankings_tree.bind('<Leave>', self.on_rankings_tree_leave)
        
        # Pack tree and scrollbar
        self.rankings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create navigation buttons
        self.create_navigation_buttons(parent)
        
        # Populate the table
        self.populate_rankings_table()
    
    def populate_rankings_table(self):
        """Populate the rankings table with data."""
        # Clear existing items
        for item in self.rankings_tree.get_children():
            self.rankings_tree.delete(item)
        
        # Get all rankings data
        rankings_data = self.ranking_algorithm.calculate_all_rankings()
        
        # Get all images and their comprehensive stats
        all_images = []
        for img_name, stats in self.data_manager.image_stats.items():
            # Calculate derived statistics
            votes = stats.get('votes', 0)
            wins = stats.get('wins', 0)
            losses = stats.get('losses', 0)
            win_rate = (wins / votes * 100) if votes > 0 else 0
            stability = self.ranking_algorithm._calculate_tier_stability(img_name)
            last_voted = stats.get('last_voted', -1)
            
            # Calculate recency
            if last_voted == -1:
                recency = float('inf')
                recency_str = "Never"
            else:
                recency = self.data_manager.vote_count - last_voted
                recency_str = f"{recency} ago" if recency > 0 else "Current"
            
            # Get prompt preview
            prompt = stats.get('prompt', '')
            if prompt:
                # Use the prompt analyzer to extract main prompt
                main_prompt = self.prompt_analyzer.extract_main_prompt(prompt)
                prompt_preview = main_prompt[:100] + "..." if len(main_prompt) > 100 else main_prompt
            else:
                prompt_preview = "No prompt found"
            
            all_images.append({
                'name': img_name,
                'tier': stats.get('current_tier', 0),
                'votes': votes,
                'wins': wins,
                'losses': losses,
                'win_rate': win_rate,
                'stability': stability,
                'recency': recency,
                'recency_str': recency_str,
                'prompt_preview': prompt_preview
            })
        
        # Sort by current tier (descending) by default
        all_images.sort(key=lambda x: x['tier'], reverse=True)
        
        # Insert data into tree with rank numbers
        for rank, img_data in enumerate(all_images, 1):
            self.rankings_tree.insert('', tk.END, values=(
                rank,
                img_data['name'],
                f"{img_data['tier']:+d}",
                img_data['votes'],
                img_data['wins'],
                img_data['losses'],
                f"{img_data['win_rate']:.1f}%",
                f"{img_data['stability']:.2f}",
                img_data['recency_str'],
                img_data['prompt_preview']
            ), tags=(img_data['name'],))  # Use filename as tag for hover detection
    
    def sort_by_column(self, column):
        """Sort the table by the specified column."""
        # Toggle sort direction if clicking the same column
        if self.current_sort_column == column:
            self.current_sort_reverse = not self.current_sort_reverse
        else:
            self.current_sort_column = column
            self.current_sort_reverse = False
        
        # Get all items with their values
        items = []
        for item in self.rankings_tree.get_children():
            values = self.rankings_tree.item(item, 'values')
            items.append((item, values))
        
        # Define sort key functions for each column
        def get_sort_key(item_data):
            values = item_data[1]  # Get the values tuple
            
            if column == 'Rank':
                return int(values[0])
            elif column == 'Image':
                return values[1].lower()  # Sort by name (case-insensitive)
            elif column == 'Tier':
                return int(values[2])  # Remove the + sign and convert to int
            elif column == 'Votes':
                return int(values[3])
            elif column == 'Wins':
                return int(values[4])
            elif column == 'Losses':
                return int(values[5])
            elif column == 'Win Rate':
                return float(values[6].rstrip('%'))  # Remove % and convert to float
            elif column == 'Stability':
                return float(values[7])
            elif column == 'Recency':
                # Special handling for "Never" and "Current"
                if values[8] == "Never":
                    return float('inf')
                elif values[8] == "Current":
                    return 0
                else:
                    return int(values[8].split()[0])  # Extract number from "X ago"
            elif column == 'Prompt Preview':
                return values[9].lower()
            else:
                return values[1]  # Default to name
        
        # Sort items
        items.sort(key=get_sort_key, reverse=self.current_sort_reverse)
        
        # Update the tree order and recalculate ranks
        for index, (item, values) in enumerate(items):
            self.rankings_tree.move(item, '', index)
            # Update rank column to reflect new order
            new_values = list(values)
            new_values[0] = index + 1
            self.rankings_tree.item(item, values=new_values)
        
        # Update column header to show sort direction
        for col in ('Rank', 'Image', 'Tier', 'Votes', 'Wins', 'Losses', 'Win Rate', 'Stability', 'Recency', 'Prompt Preview'):
            if col == column:
                direction = " ↓" if self.current_sort_reverse else " ↑"
                current_text = self.rankings_tree.heading(col, 'text')
                # Remove existing direction indicators
                clean_text = current_text.replace(" ↑", "").replace(" ↓", "")
                self.rankings_tree.heading(col, text=clean_text + direction)
            else:
                # Remove direction indicators from other columns
                current_text = self.rankings_tree.heading(col, 'text')
                clean_text = current_text.replace(" ↑", "").replace(" ↓", "")
                self.rankings_tree.heading(col, text=clean_text)
    
    def on_rankings_tree_hover(self, event):
        """Handle mouse hover over rankings tree items."""
        item = self.rankings_tree.identify_row(event.y)
        
        if item:
            # Get the image filename from the item's tags
            tags = self.rankings_tree.item(item, 'tags')
            if tags:
                image_filename = tags[0]
                self.display_preview_image(image_filename)
    
    def on_rankings_tree_leave(self, event):
        """Handle mouse leaving the rankings tree."""
        # Keep the current image displayed for better UX
        pass
    
    def create_navigation_buttons(self, parent: tk.Frame):
        """Create navigation buttons for the rankings window."""
        nav_frame = tk.Frame(parent, bg=Colors.BG_SECONDARY)
        nav_frame.pack(fill=tk.X, padx=10, pady=5)
        
        def jump_to_top():
            children = self.rankings_tree.get_children()
            if children:
                self.rankings_tree.see(children[0])
                self.rankings_tree.selection_set(children[0])
        
        def jump_to_bottom():
            children = self.rankings_tree.get_children()
            if children:
                self.rankings_tree.see(children[-1])
                self.rankings_tree.selection_set(children[-1])
        
        def jump_to_tier_zero():
            """Jump to the first tier 0 image."""
            for item in self.rankings_tree.get_children():
                values = self.rankings_tree.item(item, 'values')
                if values[2] == "+0":  # Tier column shows "+0"
                    self.rankings_tree.see(item)
                    self.rankings_tree.selection_set(item)
                    break
        
        tk.Button(nav_frame, text="Jump to Top", command=jump_to_top, 
                 bg=Colors.BUTTON_BG, fg=Colors.TEXT_PRIMARY, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(nav_frame, text="Jump to Tier 0", command=jump_to_tier_zero, 
                 bg=Colors.BUTTON_INFO, fg=Colors.TEXT_PRIMARY, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(nav_frame, text="Jump to Bottom", command=jump_to_bottom, 
                 bg=Colors.BUTTON_BG, fg=Colors.TEXT_PRIMARY, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
    
    def close_window(self):
        """Handle window closing."""
        # Clean up preview resources using mixin
        self.cleanup_preview_resources()
        
        if self.window:
            self.window.destroy()
            self.window = None