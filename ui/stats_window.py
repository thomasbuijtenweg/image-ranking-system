"""
Statistics window module for the Image Ranking System.

This module implements the detailed statistics window that shows
comprehensive information about individual images and overall
system performance.
"""

import tkinter as tk
from tkinter import ttk
from collections import defaultdict

from config import Colors


class StatsWindow:
    """
    Window for displaying detailed statistics about the ranking system.
    
    This window provides comprehensive statistics about individual images,
    overall system performance, and priority calculations.
    """
    
    def __init__(self, parent: tk.Tk, data_manager, ranking_algorithm):
        """
        Initialize the statistics window.
        
        Args:
            parent: Parent window
            data_manager: DataManager instance
            ranking_algorithm: RankingAlgorithm instance
        """
        self.parent = parent
        self.data_manager = data_manager
        self.ranking_algorithm = ranking_algorithm
        self.window = None
    
    def show(self):
        """Show the statistics window, creating it if necessary."""
        if self.window is None or not self.window.winfo_exists():
            self.create_window()
        else:
            self.window.lift()
            self.window.focus_force()
    
    def create_window(self):
        """Create the statistics window with all its components."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Detailed Statistics")
        self.window.geometry("900x600")
        self.window.configure(bg=Colors.BG_PRIMARY)
        
        # Handle window closing
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
        # Create notebook for different stats tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create overall statistics tab
        self.create_overall_stats_tab(notebook)
        
        # Create individual image details tab
        self.create_image_details_tab(notebook)
    
    def create_overall_stats_tab(self, notebook: ttk.Notebook):
        """Create the overall statistics tab."""
        frame = tk.Frame(notebook, bg=Colors.BG_SECONDARY)
        notebook.add(frame, text="Overall Statistics")
        
        # Calculate overall statistics
        overall_stats = self.data_manager.get_overall_statistics()
        
        # Create statistics text
        stats_text = self.format_overall_stats(overall_stats)
        
        # Display statistics
        tk.Label(frame, text=stats_text, font=('Courier', 12), justify=tk.LEFT, 
                fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(padx=20, pady=20)
    
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
    
    def populate_image_details(self, parent: tk.Frame):
        """Populate the image details section."""
        for img in sorted(self.data_manager.image_stats.keys()):
            stats = self.data_manager.get_image_stats(img)
            
            # Create frame for this image
            img_frame = tk.LabelFrame(parent, text=img, padx=10, pady=5, 
                                    fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY,
                                    highlightbackground=Colors.BUTTON_BG, 
                                    highlightcolor=Colors.BUTTON_HOVER,
                                    highlightthickness=1, relief=tk.RIDGE, bd=1)
            img_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Add image statistics
            self.add_image_statistics(img_frame, img, stats)
    
    def add_image_statistics(self, parent: tk.Frame, img: str, stats: dict):
        """Add statistics for a single image."""
        # Basic stats
        basic_text = (f"Current Tier: {stats.get('current_tier', 0)} | "
                     f"Votes: {stats.get('votes', 0)} | "
                     f"Wins: {stats.get('wins', 0)} | "
                     f"Losses: {stats.get('losses', 0)}")
        tk.Label(parent, text=basic_text, fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        # Win rate
        votes = stats.get('votes', 0)
        wins = stats.get('wins', 0)
        win_rate = wins / votes if votes > 0 else 0
        tk.Label(parent, text=f"Win Rate: {win_rate:.1%}", 
                fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        # Tier stability
        stability = self.ranking_algorithm._calculate_tier_stability(img)
        tk.Label(parent, text=f"Tier Stability (std dev): {stability:.2f}", 
                fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        # Display prompt if available
        prompt = stats.get('prompt')
        if prompt:
            tk.Label(parent, text="Prompt:", font=('Arial', 9, 'bold'), 
                    fg=Colors.TEXT_SUCCESS, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
            
            # Create a text widget for the prompt
            prompt_text = tk.Text(parent, height=3, wrap=tk.WORD, 
                                bg=Colors.BG_TERTIARY, fg=Colors.TEXT_PRIMARY, 
                                font=('Arial', 8), relief=tk.FLAT)
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
            tk.Label(parent, text=recent_text[:-2], font=('Arial', 9), 
                    fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
    
    def close_window(self):
        """Handle window closing."""
        if self.window:
            self.window.destroy()
            self.window = None