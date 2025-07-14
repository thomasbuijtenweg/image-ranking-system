"""
Statistics window module for the Image Ranking System.

This module implements the detailed statistics window that shows
comprehensive information about individual images and overall
system performance. Now includes image preview functionality on hover
and prompt analysis capabilities.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from collections import defaultdict
import os

from config import Colors


class StatsWindow:
    """
    Window for displaying detailed statistics about the ranking system.
    
    This window provides comprehensive statistics about individual images,
    overall system performance, priority calculations, and prompt analysis.
    Now includes image preview on hover.
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
        self.parent = parent
        self.data_manager = data_manager
        self.ranking_algorithm = ranking_algorithm
        self.prompt_analyzer = prompt_analyzer
        self.window = None
        self.notebook = None
        self.image_label = None  # For displaying preview images
        self.current_image = None  # Current displayed image reference
        self.image_processor = None  # Will be set when window is created
        self.resize_timer = None  # Timer for resize debouncing
        self.current_displayed_image = None  # Track current image for resize refresh
    
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
        self.window.geometry("1600x800")  # Even larger window for optimal preview experience
        self.window.minsize(1000, 500)  # Set minimum window size to prevent cramped layout
        self.window.configure(bg=Colors.BG_PRIMARY)
        
        # Handle window closing
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # Handle window resize events
        self.window.bind('<Configure>', self.on_window_resize)
        self.resize_timer = None
        self.current_displayed_image = None  # Track current image for resize refresh
        
        # Create main frame
        main_frame = tk.Frame(self.window, bg=Colors.BG_PRIMARY)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure main frame grid - Fixed ratio: 40% stats, 60% image preview
        main_frame.grid_columnconfigure(0, weight=2, minsize=500)  # Stats take 40% of width
        main_frame.grid_columnconfigure(1, weight=3, minsize=700)  # Image preview takes 60% of width
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Create notebook for different stats tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Create image preview area
        self.create_image_preview_area(main_frame)
        
        # Create overall statistics tab
        self.create_overall_stats_tab(self.notebook)
        
        # Create individual image details tab
        self.create_image_details_tab(self.notebook)
        
        # Create prompt analysis tab if there are prompts to analyze
        prompt_count = sum(1 for stats in self.data_manager.image_stats.values() 
                          if stats.get('prompt'))
        if prompt_count > 0:
            self.create_prompt_analysis_tab(self.notebook)
    
    def create_image_preview_area(self, parent):
        """Create the image preview area on the right side."""
        preview_frame = tk.Frame(parent, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=2)
        preview_frame.grid(row=0, column=1, sticky="nsew")
        
        # Configure preview frame grid - text areas have fixed minimum sizes
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(0, weight=0, minsize=50)   # Title - fixed
        preview_frame.grid_rowconfigure(1, weight=1, minsize=400) # Image - expandable with minimum
        preview_frame.grid_rowconfigure(2, weight=0, minsize=60)  # Info - fixed minimum
        preview_frame.grid_rowconfigure(3, weight=0, minsize=60)  # Additional stats - fixed minimum
        preview_frame.grid_rowconfigure(4, weight=0, minsize=120) # Prompt - fixed minimum
        
        # Title - fixed height
        title_label = tk.Label(preview_frame, text="Image Preview", 
                              font=('Arial', 14, 'bold'), 
                              fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY,
                              height=2)
        title_label.grid(row=0, column=0, sticky="ew", pady=5)
        
        # Image display area - expandable, takes remaining space
        self.image_label = tk.Label(preview_frame, text="Hover over an image\nstatistic to preview", 
                                   bg=Colors.BG_TERTIARY, fg=Colors.TEXT_SECONDARY,
                                   font=('Arial', 12), justify=tk.CENTER)
        self.image_label.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # Image info label - fixed minimum height
        self.image_info_label = tk.Label(preview_frame, text="", 
                                        font=('Arial', 11), 
                                        fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY,
                                        justify=tk.CENTER, height=2)
        self.image_info_label.grid(row=2, column=0, sticky="ew", pady=2)
        
        # Additional stats label - fixed minimum height
        self.additional_stats_label = tk.Label(preview_frame, text="", 
                                             font=('Arial', 10), 
                                             fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY,
                                             justify=tk.CENTER, height=2)
        self.additional_stats_label.grid(row=3, column=0, sticky="ew", pady=2)
        
        # Prompt display area - fixed minimum height
        prompt_frame = tk.Frame(preview_frame, bg=Colors.BG_SECONDARY)
        prompt_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=5)
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
    
    def create_overall_stats_tab(self, notebook: ttk.Notebook):
        """Create the overall statistics tab."""
        frame = tk.Frame(notebook, bg=Colors.BG_SECONDARY)
        notebook.add(frame, text="Overall Statistics")
        
        # Calculate overall statistics
        overall_stats = self.data_manager.get_overall_statistics()
        
        # Create statistics text
        stats_text = self.format_overall_stats(overall_stats)
        
        # Display statistics
        stats_label = tk.Label(frame, text=stats_text, font=('Courier', 12), justify=tk.LEFT, 
                              fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY)
        stats_label.pack(padx=20, pady=20)
        
        # Add instruction text
        instruction_text = "\nSwitch to other tabs and hover over any image frame to see a large preview."
        instruction_label = tk.Label(frame, text=instruction_text, font=('Arial', 10, 'italic'), 
                                   fg=Colors.TEXT_INFO, bg=Colors.BG_SECONDARY)
        instruction_label.pack(pady=10)
    
    def format_overall_stats(self, stats: dict) -> str:
        """Format overall statistics for display."""
        text = f"""
Total Images: {stats['total_images']}
Total Votes Cast: {stats['total_votes']}
Average Votes per Image: {stats['avg_votes_per_image']:.1f}

Tier Distribution:
"""
        
        tier_distribution = stats['tier_distribution']
        for tier in sorted(tier_distribution.keys(), reverse=True):
            text += f"  Tier {tier:+3d}: {tier_distribution[tier]} images\n"
        
        return text
    
    def create_image_details_tab(self, notebook: ttk.Notebook):
        """Create the individual image details tab."""
        frame = tk.Frame(notebook, bg=Colors.BG_SECONDARY)
        notebook.add(frame, text="Image Details")
        
        # Navigation buttons
        nav_frame = tk.Frame(frame, bg=Colors.BG_SECONDARY)
        nav_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create scrollable frame for image details
        canvas = tk.Canvas(frame, bg=Colors.BG_SECONDARY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=Colors.BG_SECONDARY)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Create navigation buttons
        self.create_detail_navigation_buttons(nav_frame, canvas)
        
        # Add image details
        self.populate_image_details(scrollable_frame)
        
        # Configure scrolling
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
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
        summary_text = (f"Prompt Analysis Summary:\n"
                       f"• Total unique words: {summary['total_words']}\n"
                       f"• Images with prompts: {summary['total_images_with_prompts']}\n"
                       f"• Rare words (< 3 appearances): {summary['rare_words_count']}\n"
                       f"• Average words per image: {summary['avg_words_per_image']:.1f}")
        
        summary_label = tk.Label(control_frame, text=summary_text, 
                                font=('Arial', 11), fg=Colors.TEXT_PRIMARY, 
                                bg=Colors.BG_SECONDARY, justify=tk.LEFT)
        summary_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Control buttons
        button_frame = tk.Frame(control_frame, bg=Colors.BG_SECONDARY)
        button_frame.pack(fill=tk.X)
        
        # Sort options
        tk.Label(button_frame, text="Sort by:", font=('Arial', 10, 'bold'), 
                fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(side=tk.LEFT, padx=(0, 5))
        
        self.sort_var = tk.StringVar(value="average_tier")
        sort_options = [
            ("Average Tier (High to Low)", "average_tier_desc"),
            ("Average Tier (Low to High)", "average_tier_asc"),
            ("Frequency (High to Low)", "frequency_desc"),
            ("Frequency (Low to High)", "frequency_asc"),
            ("Alphabetical", "alphabetical")
        ]
        
        for text, value in sort_options:
            tk.Radiobutton(button_frame, text=text, variable=self.sort_var, value=value,
                          fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY,
                          selectcolor=Colors.BG_TERTIARY).pack(side=tk.LEFT, padx=5)
        
        # Refresh and export buttons
        button_row2 = tk.Frame(control_frame, bg=Colors.BG_SECONDARY)
        button_row2.pack(fill=tk.X, pady=(5, 0))
        
        tk.Button(button_row2, text="Refresh Analysis", command=self.refresh_prompt_analysis,
                 bg=Colors.BUTTON_INFO, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(button_row2, text="Export Word Analysis", command=self.export_word_analysis,
                 bg=Colors.BUTTON_WARNING, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        # Search frame
        search_frame = tk.Frame(button_row2, bg=Colors.BG_SECONDARY)
        search_frame.pack(side=tk.LEFT, padx=(20, 0))
        
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
        
        # Configure columns
        self.word_tree.heading('Word', text='Word')
        self.word_tree.heading('Frequency', text='Frequency')
        self.word_tree.heading('Avg Tier', text='Avg Tier')
        self.word_tree.heading('Std Dev', text='Std Dev')
        self.word_tree.heading('Tier Range', text='Tier Range')
        self.word_tree.heading('Example Images', text='Example Images')
        
        # Set column widths
        self.word_tree.column('#0', width=0, stretch=False)
        self.word_tree.column('Word', width=120)
        self.word_tree.column('Frequency', width=80)
        self.word_tree.column('Avg Tier', width=80)
        self.word_tree.column('Std Dev', width=80)
        self.word_tree.column('Tier Range', width=100)
        self.word_tree.column('Example Images', width=200)
        
        # Bind events for word analysis
        self.word_tree.bind('<Motion>', self.on_word_tree_hover)
        self.word_tree.bind('<Leave>', self.on_word_tree_leave)
        
        # Pack tree and scrollbar
        self.word_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        word_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Initial population
        self.refresh_prompt_analysis()
    
    def refresh_prompt_analysis(self):
        """Refresh the prompt analysis display."""
        if not hasattr(self, 'word_tree'):
            return
        
        # Clear existing items
        for item in self.word_tree.get_children():
            self.word_tree.delete(item)
        
        # Get sort option
        sort_option = self.sort_var.get()
        
        # Get search term
        search_term = self.search_var.get().strip().lower()
        
        # Get word analysis
        if search_term:
            # Use search functionality
            word_data = self.prompt_analyzer.search_words_by_pattern(search_term)
        else:
            # Get all words with appropriate sorting
            if sort_option == "average_tier_desc":
                word_data = self.prompt_analyzer.get_sorted_word_analysis('average_tier', ascending=False)
            elif sort_option == "average_tier_asc":
                word_data = self.prompt_analyzer.get_sorted_word_analysis('average_tier', ascending=True)
            elif sort_option == "frequency_desc":
                word_data = self.prompt_analyzer.get_sorted_word_analysis('frequency', ascending=False)
            elif sort_option == "frequency_asc":
                word_data = self.prompt_analyzer.get_sorted_word_analysis('frequency', ascending=True)
            else:  # alphabetical
                word_data = sorted(self.prompt_analyzer.analyze_word_performance().items())
        
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
    
    def create_detail_navigation_buttons(self, nav_frame: tk.Frame, canvas: tk.Canvas):
        """Create navigation buttons for the image details tab."""
        def jump_to_top():
            canvas.yview_moveto(0)
        
        def jump_to_bottom():
            canvas.yview_moveto(1)
        
        tk.Button(nav_frame, text="Jump to Top", command=jump_to_top, 
                 bg=Colors.BUTTON_BG, fg=Colors.TEXT_PRIMARY, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        tk.Button(nav_frame, text="Jump to Bottom", command=jump_to_bottom, 
                 bg=Colors.BUTTON_BG, fg=Colors.TEXT_PRIMARY, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        # Add instruction label
        tk.Label(nav_frame, text="Hover over any image frame to see a large preview →", 
                font=('Arial', 10, 'italic'), fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY).pack(side=tk.RIGHT, padx=20)
    
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
    
    def populate_image_details(self, parent: tk.Frame):
        """Populate the image details section."""
        # Sort images by current tier (descending) for better organization
        sorted_images = sorted(self.data_manager.image_stats.keys(), 
                              key=lambda x: self.data_manager.get_image_stats(x).get('current_tier', 0), 
                              reverse=True)
        
        for img in sorted_images:
            stats = self.data_manager.get_image_stats(img)
            
            # Create frame for this image
            img_frame = tk.LabelFrame(parent, text=img, padx=10, pady=5, 
                                    fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY,
                                    highlightbackground=Colors.BUTTON_BG, 
                                    highlightcolor=Colors.BUTTON_HOVER,
                                    highlightthickness=1, relief=tk.RIDGE, bd=1)
            img_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Add hover functionality to the frame
            self.add_hover_to_frame(img_frame, img)
            
            # Add image statistics
            self.add_image_statistics(img_frame, img, stats)
    
    def add_hover_to_frame(self, frame: tk.Frame, image_filename: str):
        """Add hover functionality to a frame and all its children."""
        def on_enter(event):
            self.display_preview_image(image_filename)
            frame.configure(highlightbackground=Colors.BUTTON_HOVER)
        
        def on_leave(event):
            frame.configure(highlightbackground=Colors.BUTTON_BG)
        
        # Bind to the frame itself
        frame.bind("<Enter>", on_enter)
        frame.bind("<Leave>", on_leave)
        
        # Also bind to all child widgets
        def bind_to_children(widget):
            for child in widget.winfo_children():
                child.bind("<Enter>", on_enter)
                child.bind("<Leave>", on_leave)
                bind_to_children(child)
        
        bind_to_children(frame)
    
    def add_image_statistics(self, parent: tk.Frame, img: str, stats: dict):
        """Add statistics for a single image."""
        # Basic stats
        basic_text = (f"Current Tier: {stats.get('current_tier', 0)} | "
                     f"Votes: {stats.get('votes', 0)} | "
                     f"Wins: {stats.get('wins', 0)} | "
                     f"Losses: {stats.get('losses', 0)}")
        basic_label = tk.Label(parent, text=basic_text, fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY)
        basic_label.pack(anchor=tk.W)
        
        # Win rate
        votes = stats.get('votes', 0)
        wins = stats.get('wins', 0)
        win_rate = wins / votes if votes > 0 else 0
        win_rate_label = tk.Label(parent, text=f"Win Rate: {win_rate:.1%}", 
                                 fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY)
        win_rate_label.pack(anchor=tk.W)
        
        # Tier stability
        stability = self.ranking_algorithm._calculate_tier_stability(img)
        stability_label = tk.Label(parent, text=f"Tier Stability (std dev): {stability:.2f}", 
                                  fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY)
        stability_label.pack(anchor=tk.W)
        
        # Display prompt if available - show full prompt
        prompt = stats.get('prompt')
        if prompt:
            prompt_title = tk.Label(parent, text="Prompt:", font=('Arial', 9, 'bold'), 
                                   fg=Colors.TEXT_SUCCESS, bg=Colors.BG_SECONDARY)
            prompt_title.pack(anchor=tk.W)
            
            # Create a text widget for the full prompt
            prompt_text = tk.Text(parent, height=4, wrap=tk.WORD, 
                                bg=Colors.BG_TERTIARY, fg=Colors.TEXT_PRIMARY, 
                                font=('Arial', 9), relief=tk.FLAT)
            prompt_text.insert(1.0, prompt)
            prompt_text.config(state=tk.DISABLED)
            prompt_text.pack(fill=tk.X, padx=10, pady=2)
        
        # Recent matchups
        matchup_history = stats.get('matchup_history', [])
        if matchup_history:
            recent_text = "Recent matchups: "
            for opponent, won, _ in matchup_history[-5:]:
                result = "W" if won else "L"
                recent_text += f"{result} vs {opponent}, "
            recent_label = tk.Label(parent, text=recent_text[:-2], font=('Arial', 9), 
                                   fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY)
            recent_label.pack(anchor=tk.W)
    
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
                
                # Update info labels
                stats = self.data_manager.get_image_stats(filename)
                
                # Basic info
                info_text = (f"{filename}\n"
                            f"Tier: {stats.get('current_tier', 0)} | "
                            f"Votes: {stats.get('votes', 0)}")
                self.image_info_label.config(text=info_text)
                
                # Additional stats
                stability = self.ranking_algorithm._calculate_tier_stability(filename)
                votes = stats.get('votes', 0)
                wins = stats.get('wins', 0)
                win_rate = wins / votes if votes > 0 else 0
                
                additional_text = (f"Win Rate: {win_rate:.1%} ({wins}/{votes})\n"
                                 f"Stability: {stability:.2f} | "
                                 f"Last voted: {stats.get('last_voted', 'Never')}")
                self.additional_stats_label.config(text=additional_text)
                
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
                self.additional_stats_label.config(text="")
                self.prompt_text.config(state=tk.NORMAL)
                self.prompt_text.delete(1.0, tk.END)
                self.prompt_text.insert(1.0, "Error loading image")
                self.prompt_text.config(state=tk.DISABLED)
                self.current_image = None
                
        except Exception as e:
            print(f"Error displaying preview for {filename}: {e}")
            self.image_label.config(image="", text="Error loading image")
            self.image_info_label.config(text=f"Error: {filename}")
            self.additional_stats_label.config(text="")
            self.prompt_text.config(state=tk.NORMAL)
            self.prompt_text.delete(1.0, tk.END)
            self.prompt_text.insert(1.0, "Error loading image")
            self.prompt_text.config(state=tk.DISABLED)
            self.current_image = None
    
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