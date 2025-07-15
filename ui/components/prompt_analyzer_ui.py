"""
Prompt analyzer UI component for the Image Ranking System.

This module handles the prompt analysis interface, including word analysis
table, search functionality, and hover interactions.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, List

from config import Colors


class PromptAnalyzerUI:
    """
    Handles the prompt analysis user interface.
    
    This component manages the prompt analysis tab with word statistics,
    search functionality, and hover interactions.
    """
    
    def __init__(self, data_manager, prompt_analyzer):
        """
        Initialize the prompt analyzer UI.
        
        Args:
            data_manager: DataManager instance
            prompt_analyzer: PromptAnalyzer instance
        """
        self.data_manager = data_manager
        self.prompt_analyzer = prompt_analyzer
        
        # UI elements
        self.word_tree = None
        self.search_var = None
        self.search_entry = None
        
        # Sorting state
        self.word_sort_column = None
        self.word_sort_reverse = False
        
        # Callbacks
        self.hover_callback = None
        self.leave_callback = None
        self.export_callback = None
    
    def create_prompt_analysis_tab(self, parent_frame):
        """
        Create the prompt analysis tab interface.
        
        Args:
            parent_frame: Parent frame to contain the tab content
            
        Returns:
            The created tab frame
        """
        # Create main content frame
        content_frame = tk.Frame(parent_frame, bg=Colors.BG_SECONDARY)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create control frame
        control_frame = tk.Frame(content_frame, bg=Colors.BG_SECONDARY)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Analysis summary
        summary = self.prompt_analyzer.get_analysis_summary()
        summary_text = (f"Prompt Analysis Summary: {summary['total_words']} unique words | "
                       f"{summary['total_images_with_prompts']} images with prompts | "
                       f"{summary['rare_words_count']} rare words | "
                       f"{summary['avg_words_per_image']:.1f} avg words/image")
        
        summary_label = tk.Label(control_frame, text=summary_text, 
                                font=('Arial', 11, 'bold'), fg=Colors.TEXT_PRIMARY, 
                                bg=Colors.BG_SECONDARY, justify=tk.LEFT)
        summary_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Control buttons frame
        button_frame = tk.Frame(control_frame, bg=Colors.BG_SECONDARY)
        button_frame.pack(fill=tk.X)
        
        # Instructions
        instruction_text = "Click column headers to sort • Hover over any row to see example image"
        tk.Label(button_frame, text=instruction_text, font=('Arial', 10, 'italic'), 
                fg=Colors.TEXT_INFO, bg=Colors.BG_SECONDARY).pack(side=tk.LEFT)
        
        # Export button
        export_button = tk.Button(button_frame, text="Export Word Analysis", 
                                 command=self.trigger_export,
                                 bg=Colors.BUTTON_WARNING, fg='white', relief=tk.FLAT)
        export_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Search frame
        search_frame = tk.Frame(button_frame, bg=Colors.BG_SECONDARY)
        search_frame.pack(side=tk.RIGHT, padx=(20, 10))
        
        tk.Label(search_frame, text="Search words:", font=('Arial', 10), 
                fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=15,
                                    bg=Colors.BG_TERTIARY, fg=Colors.TEXT_PRIMARY)
        self.search_entry.pack(side=tk.LEFT, padx=(5, 5))
        self.search_entry.bind('<Return>', lambda e: self.refresh_analysis())
        
        search_button = tk.Button(search_frame, text="Search", command=self.refresh_analysis,
                                 bg=Colors.BUTTON_SECONDARY, fg='white', relief=tk.FLAT)
        search_button.pack(side=tk.LEFT)
        
        # Create word analysis table
        self.create_word_analysis_table(content_frame)
        
        # Initial population
        self.refresh_analysis()
        
        return content_frame
    
    def create_word_analysis_table(self, parent_frame):
        """
        Create the word analysis table.
        
        Args:
            parent_frame: Parent frame to contain the table
        """
        # Create treeview for word analysis
        tree_frame = tk.Frame(parent_frame, bg=Colors.BG_SECONDARY)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview with scrollbar
        columns = ('Word', 'Frequency', 'Avg Tier', 'Std Dev', 'Tier Range', 'Example Images')
        self.word_tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', height=20)
        
        word_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.word_tree.yview)
        self.word_tree.configure(yscrollcommand=word_scrollbar.set)
        
        # Configure column headings with click handlers
        self.word_tree.heading('#0', text='', anchor=tk.W)
        self.word_tree.heading('Word', text='Word', anchor=tk.W)
        self.word_tree.heading('Frequency', text='Frequency', anchor=tk.CENTER)
        self.word_tree.heading('Avg Tier', text='Avg Tier', anchor=tk.CENTER)
        self.word_tree.heading('Std Dev', text='Std Dev', anchor=tk.CENTER)
        self.word_tree.heading('Tier Range', text='Tier Range', anchor=tk.CENTER)
        self.word_tree.heading('Example Images', text='Example Images', anchor=tk.W)
        
        # Set column widths
        self.word_tree.column('#0', width=0, stretch=False)
        self.word_tree.column('Word', width=120)
        self.word_tree.column('Frequency', width=80)
        self.word_tree.column('Avg Tier', width=80)
        self.word_tree.column('Std Dev', width=80)
        self.word_tree.column('Tier Range', width=100)
        self.word_tree.column('Example Images', width=200)
        
        # Bind click events to column headers for sorting
        for col in columns:
            self.word_tree.heading(col, command=lambda c=col: self.sort_by_column(c))
        
        # Bind events for word analysis
        self.word_tree.bind('<Motion>', self.on_tree_hover)
        self.word_tree.bind('<Leave>', self.on_tree_leave)
        
        # Pack tree and scrollbar
        self.word_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        word_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def refresh_analysis(self):
        """Refresh the prompt analysis display."""
        if not self.word_tree:
            return
            
        # Clear existing items
        for item in self.word_tree.get_children():
            self.word_tree.delete(item)
        
        # Get search term
        search_term = self.search_var.get().strip().lower() if self.search_var else ""
        
        # Get word analysis
        if search_term:
            # Use search functionality
            word_data = self.prompt_analyzer.search_words_by_pattern(search_term)
        else:
            # Get all words sorted by average tier (descending) as default
            word_data = self.prompt_analyzer.get_sorted_word_analysis('average_tier', ascending=False)
        
        # Populate tree
        for word, data in word_data:
            tiers = data['tiers']
            tier_range = f"{min(tiers)} to {max(tiers)}" if tiers else "N/A"
            
            # Get example images for this word
            example_images = self.get_example_images_for_word(word)
            example_text = ", ".join(example_images[:3])
            if len(example_images) > 3:
                example_text += f" (+{len(example_images)-3} more)"
            
            # Insert item with word as tag for hover detection
            self.word_tree.insert('', tk.END, values=(
                word,
                data['frequency'],
                f"{data['average_tier']:.2f}",
                f"{data['std_deviation']:.2f}",
                tier_range,
                example_text
            ), tags=(word,))
    
    def sort_by_column(self, column):
        """
        Sort the word analysis table by the specified column.
        
        Args:
            column: Column name to sort by
        """
        if not self.word_tree:
            return
            
        # Toggle sort direction if clicking the same column
        if self.word_sort_column == column:
            self.word_sort_reverse = not self.word_sort_reverse
        else:
            self.word_sort_column = column
            self.word_sort_reverse = False
        
        # Get all items with their values
        items = []
        for item in self.word_tree.get_children():
            values = self.word_tree.item(item, 'values')
            items.append((item, values))
        
        # Define sort key functions for each column
        def get_sort_key(item_data):
            values = item_data[1]  # Get the values tuple
            
            if column == 'Word':
                return values[0].lower()  # Sort by word (case-insensitive)
            elif column == 'Frequency':
                return int(values[1])
            elif column == 'Avg Tier':
                return float(values[2])
            elif column == 'Std Dev':
                return float(values[3])
            elif column == 'Tier Range':
                # Sort by the first number in the range
                range_str = values[4]
                if range_str == "N/A":
                    return float('-inf')
                try:
                    return int(range_str.split()[0])
                except:
                    return 0
            elif column == 'Example Images':
                return values[5].lower()
            else:
                return values[0]  # Default to word
        
        # Sort items
        items.sort(key=get_sort_key, reverse=self.word_sort_reverse)
        
        # Update the tree order
        for index, (item, values) in enumerate(items):
            self.word_tree.move(item, '', index)
        
        # Update column header to show sort direction
        columns = ('Word', 'Frequency', 'Avg Tier', 'Std Dev', 'Tier Range', 'Example Images')
        for col in columns:
            if col == column:
                direction = " ↓" if self.word_sort_reverse else " ↑"
                current_text = self.word_tree.heading(col, 'text')
                # Remove existing direction indicators
                clean_text = current_text.replace(" ↑", "").replace(" ↓", "")
                self.word_tree.heading(col, text=clean_text + direction)
            else:
                # Remove direction indicators from other columns
                current_text = self.word_tree.heading(col, 'text')
                clean_text = current_text.replace(" ↑", "").replace(" ↓", "")
                self.word_tree.heading(col, text=clean_text)
    
    def get_example_images_for_word(self, word: str) -> List[str]:
        """
        Get example images that contain a specific word.
        
        Args:
            word: Word to search for
            
        Returns:
            List of image filenames containing the word
        """
        example_images = []
        word_lower = word.lower()
        
        for image_name, stats in self.data_manager.image_stats.items():
            prompt = stats.get('prompt', '')
            if prompt:
                main_prompt = self.prompt_analyzer.extract_main_prompt(prompt)
                words = self.prompt_analyzer.extract_words(main_prompt)
                if word_lower in words:
                    example_images.append(image_name)
                    if len(example_images) >= 5:  # Limit for performance
                        break
        
        return example_images
    
    def on_tree_hover(self, event):
        """
        Handle mouse hover over word tree items.
        
        Args:
            event: Tkinter event object
        """
        if not self.word_tree:
            return
            
        item = self.word_tree.identify_row(event.y)
        if item:
            # Get the word from the item's tags
            tags = self.word_tree.item(item, 'tags')
            if tags and self.hover_callback:
                word = tags[0]
                # Find an example image for this word and display it
                example_images = self.get_example_images_for_word(word)
                if example_images:
                    self.hover_callback(example_images[0])
    
    def on_tree_leave(self, event):
        """
        Handle mouse leaving the word tree.
        
        Args:
            event: Tkinter event object
        """
        if self.leave_callback:
            self.leave_callback()
    
    def trigger_export(self):
        """Trigger the export functionality."""
        if self.export_callback:
            self.export_callback()
    
    def set_hover_callback(self, callback: Callable[[str], None]):
        """
        Set callback function for hover events.
        
        Args:
            callback: Function to call when hovering over an item
        """
        self.hover_callback = callback
    
    def set_leave_callback(self, callback: Callable[[], None]):
        """
        Set callback function for leave events.
        
        Args:
            callback: Function to call when leaving the table
        """
        self.leave_callback = callback
    
    def set_export_callback(self, callback: Callable[[], None]):
        """
        Set callback function for export events.
        
        Args:
            callback: Function to call when export is requested
        """
        self.export_callback = callback
    
    def get_analysis_summary(self):
        """
        Get summary of the current analysis.
        
        Returns:
            Dictionary with analysis summary
        """
        if not self.word_tree:
            return {'total_words': 0}
        
        total_words = len(self.word_tree.get_children())
        
        # Get search term
        search_term = self.search_var.get().strip() if self.search_var else ""
        
        # Get current sort information
        sort_info = {
            'column': self.word_sort_column,
            'reverse': self.word_sort_reverse
        }
        
        return {
            'total_words': total_words,
            'search_term': search_term,
            'sort_info': sort_info
        }
    
    def cleanup(self):
        """Clean up UI resources."""
        if self.word_tree:
            # Clear all items
            for item in self.word_tree.get_children():
                self.word_tree.delete(item)
            
            # Clear callbacks
            self.hover_callback = None
            self.leave_callback = None
            self.export_callback = None
        
        # Clear search
        if self.search_var:
            self.search_var.set("")
