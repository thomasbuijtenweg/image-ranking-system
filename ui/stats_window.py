"""
Statistics window module for the Image Ranking System.

This module implements the detailed statistics window that shows
comprehensive information about individual images and overall
system performance. Now features a single sortable table instead
of multiple redundant tabs, with image preview functionality on hover
using the ImagePreviewMixin and prompt analysis capabilities.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from collections import defaultdict
import os

from config import Colors
from ui.mixins import ImagePreviewMixin


class StatsWindow(ImagePreviewMixin):
    """
    Window for displaying detailed statistics about the ranking system.
    
    This window provides comprehensive statistics in a single sortable table
    with image preview on hover and prompt analysis capabilities.
    """
    
    def __init__(self, parent: tk.Tk, data_manager, ranking_algorithm, prompt_analyzer):
        """
        Initialize the statistics window.
        
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
        self.notebook = None
        self.stats_tree = None
        self.current_sort_column = None
        self.current_sort_reverse = False
        self.word_sort_column = None
        self.word_sort_reverse = False
    
    def show(self):
        """Show the statistics window, creating it if necessary."""
        if self.window is None or not self.window.winfo_exists():
            self.create_window()
        else:
            self.window.lift()
            self.window.focus_force()
    
    def focus_prompt_analysis_tab(self):
        """Focus on the prompt analysis tab if it exists."""
        if self.notebook:
            # Find the prompt analysis tab and select it
            for i in range(self.notebook.index("end")):
                if "Prompt Analysis" in self.notebook.tab(i, "text"):
                    self.notebook.select(i)
                    break
    
    def create_window(self):
        """Create the statistics window with all its components."""
        # Import here to avoid circular imports
        from core.image_processor import ImageProcessor
        self.image_processor = ImageProcessor()
        
        self.window = tk.Toplevel(self.parent)
        self.window.title("Detailed Statistics")
        self.window.geometry("1800x900")  # Even larger window for optimal table and preview experience
        self.window.minsize(1200, 600)  # Set minimum window size to prevent cramped layout
        self.window.configure(bg=Colors.BG_PRIMARY)
        
        # Handle window closing
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # Setup resize handling from mixin
        self.setup_preview_resize_handling()
        
        # Create main frame
        main_frame = tk.Frame(self.window, bg=Colors.BG_PRIMARY)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure main frame grid - 50% stats table, 50% image preview
        main_frame.grid_columnconfigure(0, weight=1, minsize=700)  # Stats table
        main_frame.grid_columnconfigure(1, weight=1, minsize=700)  # Image preview
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Create notebook for different tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Create image preview area using mixin
        preview_frame = self.create_image_preview_area(main_frame, include_additional_stats=True)
        preview_frame.grid(row=0, column=1, sticky="nsew")
        
        # Create the main statistics table tab
        self.create_main_stats_tab(self.notebook)
        
        # Create prompt analysis tab if there are prompts to analyze
        prompt_count = sum(1 for stats in self.data_manager.image_stats.values() 
                          if stats.get('prompt'))
        if prompt_count > 0:
            self.create_prompt_analysis_tab(self.notebook)
    
    def create_main_stats_tab(self, notebook: ttk.Notebook):
        """Create the main statistics tab with sortable table."""
        frame = tk.Frame(notebook, bg=Colors.BG_SECONDARY)
        notebook.add(frame, text="Image Statistics")
        
        # Create header with overall statistics
        header_frame = tk.Frame(frame, bg=Colors.BG_SECONDARY)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Calculate and display overall statistics
        overall_stats = self.data_manager.get_overall_statistics()
        overall_text = (f"Total Images: {overall_stats['total_images']} | "
                       f"Total Votes: {overall_stats['total_votes']} | "
                       f"Avg Votes/Image: {overall_stats['avg_votes_per_image']:.1f}")
        
        tk.Label(header_frame, text=overall_text, font=('Arial', 12, 'bold'), 
                fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        # Add tier distribution summary
        tier_dist = overall_stats['tier_distribution']
        tier_text = "Tier Distribution: "
        for tier in sorted(tier_dist.keys(), reverse=True):
            if tier_dist[tier] > 0:
                tier_text += f"T{tier:+d}:{tier_dist[tier]} "
        
        tk.Label(header_frame, text=tier_text, font=('Arial', 10), 
                fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        # Instructions
        instruction_text = "Click column headers to sort • Hover over any row to see image preview"
        tk.Label(header_frame, text=instruction_text, font=('Arial', 10, 'italic'), 
                fg=Colors.TEXT_INFO, bg=Colors.BG_SECONDARY).pack(anchor=tk.W, pady=(5, 0))
        
        # Create the statistics table
        self.create_stats_table(frame)
    
    def create_stats_table(self, parent: tk.Frame):
        """Create the main statistics table with sortable columns."""
        # Create frame for the table
        table_frame = tk.Frame(parent, bg=Colors.BG_SECONDARY)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Define columns
        columns = ('Image', 'Tier', 'Votes', 'Wins', 'Losses', 'Win Rate', 'Stability', 'Last Voted', 'Prompt Preview')
        
        # Create treeview with scrollbar
        self.stats_tree = ttk.Treeview(table_frame, columns=columns, show='tree headings', height=25)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.stats_tree.yview)
        self.stats_tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure column headings with click handlers
        self.stats_tree.heading('#0', text='', anchor=tk.W)
        self.stats_tree.heading('Image', text='Image Name', anchor=tk.W)
        self.stats_tree.heading('Tier', text='Current Tier', anchor=tk.CENTER)
        self.stats_tree.heading('Votes', text='Total Votes', anchor=tk.CENTER)
        self.stats_tree.heading('Wins', text='Wins', anchor=tk.CENTER)
        self.stats_tree.heading('Losses', text='Losses', anchor=tk.CENTER)
        self.stats_tree.heading('Win Rate', text='Win Rate %', anchor=tk.CENTER)
        self.stats_tree.heading('Stability', text='Stability', anchor=tk.CENTER)
        self.stats_tree.heading('Last Voted', text='Last Voted', anchor=tk.CENTER)
        self.stats_tree.heading('Prompt Preview', text='Prompt Preview', anchor=tk.W)
        
        # Set column widths
        self.stats_tree.column('#0', width=0, stretch=False)
        self.stats_tree.column('Image', width=180)
        self.stats_tree.column('Tier', width=80)
        self.stats_tree.column('Votes', width=80)
        self.stats_tree.column('Wins', width=60)
        self.stats_tree.column('Losses', width=60)
        self.stats_tree.column('Win Rate', width=80)
        self.stats_tree.column('Stability', width=80)
        self.stats_tree.column('Last Voted', width=90)
        self.stats_tree.column('Prompt Preview', width=300)
        
        # Bind click events to column headers for sorting
        for col in columns:
            self.stats_tree.heading(col, command=lambda c=col: self.sort_by_column(c))
        
        # Bind hover events
        self.stats_tree.bind('<Motion>', self.on_stats_tree_hover)
        self.stats_tree.bind('<Leave>', self.on_stats_tree_leave)
        
        # Pack tree and scrollbar
        self.stats_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate the table
        self.populate_stats_table()
    
    def populate_stats_table(self):
        """Populate the statistics table with data."""
        # Clear existing items
        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)
        
        # Get all images and their stats
        all_images = []
        for img_name, stats in self.data_manager.image_stats.items():
            # Calculate derived statistics
            votes = stats.get('votes', 0)
            wins = stats.get('wins', 0)
            losses = stats.get('losses', 0)
            win_rate = (wins / votes * 100) if votes > 0 else 0
            stability = self.ranking_algorithm._calculate_tier_stability(img_name)
            last_voted = stats.get('last_voted', -1)
            
            # Format last voted
            if last_voted == -1:
                last_voted_str = "Never"
            else:
                votes_ago = self.data_manager.vote_count - last_voted
                last_voted_str = f"{votes_ago} ago" if votes_ago > 0 else "Current"
            
            # Get prompt preview
            prompt = stats.get('prompt', '')
            if prompt:
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
                'last_voted': last_voted,
                'last_voted_str': last_voted_str,
                'prompt_preview': prompt_preview
            })
        
        # Sort by current tier (descending) by default
        all_images.sort(key=lambda x: x['tier'], reverse=True)
        
        # Insert data into tree
        for img_data in all_images:
            self.stats_tree.insert('', tk.END, values=(
                img_data['name'],
                f"{img_data['tier']:+d}",
                img_data['votes'],
                img_data['wins'],
                img_data['losses'],
                f"{img_data['win_rate']:.1f}%",
                f"{img_data['stability']:.2f}",
                img_data['last_voted_str'],
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
        for item in self.stats_tree.get_children():
            values = self.stats_tree.item(item, 'values')
            items.append((item, values))
        
        # Define sort key functions for each column
        def get_sort_key(item_data):
            values = item_data[1]  # Get the values tuple
            
            if column == 'Image':
                return values[0].lower()  # Sort by name (case-insensitive)
            elif column == 'Tier':
                return int(values[1])  # Remove the + sign and convert to int
            elif column == 'Votes':
                return int(values[2])
            elif column == 'Wins':
                return int(values[3])
            elif column == 'Losses':
                return int(values[4])
            elif column == 'Win Rate':
                return float(values[5].rstrip('%'))  # Remove % and convert to float
            elif column == 'Stability':
                return float(values[6])
            elif column == 'Last Voted':
                # Special handling for "Never" and "Current"
                if values[7] == "Never":
                    return float('inf')
                elif values[7] == "Current":
                    return 0
                else:
                    return int(values[7].split()[0])  # Extract number from "X ago"
            elif column == 'Prompt Preview':
                return values[8].lower()
            else:
                return values[0]  # Default to name
        
        # Sort items
        items.sort(key=get_sort_key, reverse=self.current_sort_reverse)
        
        # Update the tree order
        for index, (item, values) in enumerate(items):
            self.stats_tree.move(item, '', index)
        
        # Update column header to show sort direction
        for col in ('Image', 'Tier', 'Votes', 'Wins', 'Losses', 'Win Rate', 'Stability', 'Last Voted', 'Prompt Preview'):
            if col == column:
                direction = " ↓" if self.current_sort_reverse else " ↑"
                current_text = self.stats_tree.heading(col, 'text')
                # Remove existing direction indicators
                clean_text = current_text.replace(" ↑", "").replace(" ↓", "")
                self.stats_tree.heading(col, text=clean_text + direction)
            else:
                # Remove direction indicators from other columns
                current_text = self.stats_tree.heading(col, 'text')
                clean_text = current_text.replace(" ↑", "").replace(" ↓", "")
                self.stats_tree.heading(col, text=clean_text)
    
    def on_stats_tree_hover(self, event):
        """Handle mouse hover over stats tree items."""
        item = self.stats_tree.identify_row(event.y)
        
        if item:
            # Get the image filename from the item's tags
            tags = self.stats_tree.item(item, 'tags')
            if tags:
                image_filename = tags[0]
                self.display_preview_image(image_filename)
    
    def on_stats_tree_leave(self, event):
        """Handle mouse leaving the stats tree."""
        # Keep the current image displayed for better UX
        pass
    
    def create_prompt_analysis_tab(self, notebook: ttk.Notebook):
        """Create the prompt analysis tab."""
        frame = tk.Frame(notebook, bg=Colors.BG_SECONDARY)
        notebook.add(frame, text="Prompt Analysis")
        
        # Create main content frame
        content_frame = tk.Frame(frame, bg=Colors.BG_SECONDARY)
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
        tk.Button(button_frame, text="Export Word Analysis", command=self.export_word_analysis,
                 bg=Colors.BUTTON_WARNING, fg='white', relief=tk.FLAT).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Search frame
        search_frame = tk.Frame(button_frame, bg=Colors.BG_SECONDARY)
        search_frame.pack(side=tk.RIGHT, padx=(20, 10))
        
        tk.Label(search_frame, text="Search words:", font=('Arial', 10), 
                fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=15,
                                    bg=Colors.BG_TERTIARY, fg=Colors.TEXT_PRIMARY)
        self.search_entry.pack(side=tk.LEFT, padx=(5, 5))
        self.search_entry.bind('<Return>', lambda e: self.refresh_prompt_analysis())
        
        tk.Button(search_frame, text="Search", command=self.refresh_prompt_analysis,
                 bg=Colors.BUTTON_SECONDARY, fg='white', relief=tk.FLAT).pack(side=tk.LEFT)
        
        # Create treeview for word analysis
        tree_frame = tk.Frame(content_frame, bg=Colors.BG_SECONDARY)
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
            self.word_tree.heading(col, command=lambda c=col: self.sort_word_analysis_by_column(c))
        
        # Bind events for word analysis
        self.word_tree.bind('<Motion>', self.on_word_tree_hover)
        self.word_tree.bind('<Leave>', self.on_word_tree_leave)
        
        # Pack tree and scrollbar
        self.word_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        word_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Track sorting state for word analysis
        self.word_sort_column = None
        self.word_sort_reverse = False
        
        # Initial population
        self.refresh_prompt_analysis()
    
    def refresh_prompt_analysis(self):
        """Refresh the prompt analysis display."""
        if not hasattr(self, 'word_tree'):
            return
        
        # Clear existing items
        for item in self.word_tree.get_children():
            self.word_tree.delete(item)
        
        # Get search term
        search_term = self.search_var.get().strip().lower()
        
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
    
    def sort_word_analysis_by_column(self, column):
        """Sort the word analysis table by the specified column."""
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
        for col in ('Word', 'Frequency', 'Avg Tier', 'Std Dev', 'Tier Range', 'Example Images'):
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
    
    def get_example_images_for_word(self, word: str) -> list:
        """Get example images that contain a specific word."""
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
    
    def on_word_tree_hover(self, event):
        """Handle mouse hover over word tree items."""
        item = self.word_tree.identify_row(event.y)
        if item:
            # Get the word from the item's tags
            tags = self.word_tree.item(item, 'tags')
            if tags:
                word = tags[0]
                # Find an example image for this word and display it
                example_images = self.get_example_images_for_word(word)
                if example_images:
                    self.display_preview_image(example_images[0])
    
    def on_word_tree_leave(self, event):
        """Handle mouse leaving the word tree."""
        pass  # Keep the current image displayed
    
    def export_word_analysis(self):
        """Export word analysis to CSV."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Word Analysis"
        )
        
        if filename:
            try:
                import csv
                word_analysis = self.prompt_analyzer.analyze_word_performance()
                
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write header
                    writer.writerow([
                        'Word', 'Frequency', 'Average Tier', 'Std Deviation', 
                        'Min Tier', 'Max Tier', 'Is Rare', 'Example Images'
                    ])
                    
                    # Sort by average tier (descending)
                    sorted_words = sorted(word_analysis.items(), 
                                        key=lambda x: x[1]['average_tier'], reverse=True)
                    
                    for word, data in sorted_words:
                        tiers = data['tiers']
                        min_tier = min(tiers) if tiers else 0
                        max_tier = max(tiers) if tiers else 0
                        example_images = self.get_example_images_for_word(word)
                        
                        writer.writerow([
                            word,
                            data['frequency'],
                            f"{data['average_tier']:.3f}",
                            f"{data['std_deviation']:.3f}",
                            min_tier,
                            max_tier,
                            data['is_rare'],
                            "; ".join(example_images[:5])  # Include up to 5 examples
                        ])
                
                messagebox.showinfo("Export Complete", f"Word analysis exported to {filename}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export word analysis: {e}")
    
    def close_window(self):
        """Handle window closing."""
        # Clean up preview resources using mixin
        self.cleanup_preview_resources()
        
        if self.window:
            self.window.destroy()
            self.window = None