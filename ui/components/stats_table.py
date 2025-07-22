"""
Statistics table component with binning support for the Image Ranking System.

This module handles the creation and management of the main statistics table,
including sorting, population, hover events, and binning status display.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Dict, Any, List

from config import Colors


class StatsTable:
    """
    Handles the main statistics table display and interaction with binning support.
    
    This component manages the sortable table showing individual image
    statistics with hover functionality for image preview and binning status.
    """
    
    def __init__(self, data_manager, ranking_algorithm, prompt_analyzer):
        """
        Initialize the statistics table.
        
        Args:
            data_manager: DataManager instance
            ranking_algorithm: RankingAlgorithm instance
            prompt_analyzer: PromptAnalyzer instance
        """
        self.data_manager = data_manager
        self.ranking_algorithm = ranking_algorithm
        self.prompt_analyzer = prompt_analyzer
        
        # Table widget
        self.stats_tree = None
        self.table_frame = None
        
        # Sorting state
        self.current_sort_column = None
        self.current_sort_reverse = False
        
        # Callbacks
        self.hover_callback = None
        self.leave_callback = None
        
        # Display options
        self.show_binned_images = True
    
    def create_stats_table(self, parent_frame):
        """
        Create the main statistics table with sortable columns including binning status.
        
        Args:
            parent_frame: Parent frame to contain the table
            
        Returns:
            The created table frame
        """
        # Create frame for the table
        self.table_frame = tk.Frame(parent_frame, bg=Colors.BG_SECONDARY)
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control frame for options
        control_frame = tk.Frame(self.table_frame, bg=Colors.BG_SECONDARY)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Overall stats with binning info
        overall_stats = self.data_manager.get_overall_statistics()
        overall_text = (f"Available Images: {overall_stats['total_images']} | "
                       f"Total Votes: {overall_stats['total_votes']} | "
                       f"Avg Votes/Image: {overall_stats['avg_votes_per_image']:.1f}")
        
        if overall_stats.get('binned_images', 0) > 0:
            overall_text += f" | Binned: {overall_stats['binned_images']}"
        
        tk.Label(control_frame, text=overall_text, font=('Arial', 12, 'bold'), 
                fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        # Toggle for showing binned images
        toggle_frame = tk.Frame(control_frame, bg=Colors.BG_SECONDARY)
        toggle_frame.pack(anchor=tk.W, pady=5)
        
        self.show_binned_var = tk.BooleanVar(value=self.show_binned_images)
        tk.Checkbutton(toggle_frame, text="Show binned images", 
                      variable=self.show_binned_var, 
                      command=self.toggle_binned_display,
                      bg=Colors.BG_SECONDARY, fg=Colors.TEXT_PRIMARY,
                      selectcolor=Colors.BG_TERTIARY,
                      activebackground=Colors.BG_SECONDARY,
                      activeforeground=Colors.TEXT_PRIMARY).pack(side=tk.LEFT)
        
        # Define columns - added Status column for binning
        columns = ('Status', 'Image', 'Tier', 'Votes', 'Wins', 'Losses', 'Win Rate', 'Stability', 'Confidence', 'Last Voted', 'Prompt Preview')
        
        # Create treeview with scrollbar
        tree_frame = tk.Frame(self.table_frame, bg=Colors.BG_SECONDARY)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.stats_tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', height=20)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.stats_tree.yview)
        self.stats_tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure column headings with click handlers
        self.stats_tree.heading('#0', text='', anchor=tk.W)
        self.stats_tree.heading('Status', text='Status', anchor=tk.CENTER)
        self.stats_tree.heading('Image', text='Image Name', anchor=tk.W)
        self.stats_tree.heading('Tier', text='Current Tier', anchor=tk.CENTER)
        self.stats_tree.heading('Votes', text='Total Votes', anchor=tk.CENTER)
        self.stats_tree.heading('Wins', text='Wins', anchor=tk.CENTER)
        self.stats_tree.heading('Losses', text='Losses', anchor=tk.CENTER)
        self.stats_tree.heading('Win Rate', text='Win Rate %', anchor=tk.CENTER)
        self.stats_tree.heading('Stability', text='Stability', anchor=tk.CENTER)
        self.stats_tree.heading('Confidence', text='Confidence', anchor=tk.CENTER)
        self.stats_tree.heading('Last Voted', text='Last Voted', anchor=tk.CENTER)
        self.stats_tree.heading('Prompt Preview', text='Prompt Preview', anchor=tk.W)
        
        # Set column widths
        self.stats_tree.column('#0', width=0, stretch=False)
        self.stats_tree.column('Status', width=80)
        self.stats_tree.column('Image', width=150)
        self.stats_tree.column('Tier', width=70)
        self.stats_tree.column('Votes', width=60)
        self.stats_tree.column('Wins', width=50)
        self.stats_tree.column('Losses', width=50)
        self.stats_tree.column('Win Rate', width=70)
        self.stats_tree.column('Stability', width=70)
        self.stats_tree.column('Confidence', width=80)
        self.stats_tree.column('Last Voted', width=80)
        self.stats_tree.column('Prompt Preview', width=250)
        
        # Bind click events to column headers for sorting
        for col in columns:
            self.stats_tree.heading(col, command=lambda c=col: self.sort_by_column(c))
        
        # Bind hover events
        self.stats_tree.bind('<Motion>', self.on_tree_hover)
        self.stats_tree.bind('<Leave>', self.on_tree_leave)
        
        # Pack tree and scrollbar
        self.stats_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Instructions
        instruction_text = "Click column headers to sort • Hover over any row to see image preview • 🗑️ = Binned images"
        tk.Label(control_frame, text=instruction_text, font=('Arial', 10, 'italic'), 
                fg=Colors.TEXT_INFO, bg=Colors.BG_SECONDARY).pack(anchor=tk.W, pady=(5, 0))
        
        # Populate the table
        self.populate_stats_table()
        
        return self.table_frame
    
    def toggle_binned_display(self):
        """Toggle display of binned images."""
        self.show_binned_images = self.show_binned_var.get()
        self.populate_stats_table()
    
    def populate_stats_table(self):
        """Populate the statistics table with data including binning status."""
        if not self.stats_tree:
            return
        
        try:
            # Clear existing items
            for item in self.stats_tree.get_children():
                self.stats_tree.delete(item)
            
            # Get all images and their stats
            all_images = []
            for img_name, stats in self.data_manager.image_stats.items():
                is_binned = self.data_manager.is_image_binned(img_name)
                
                # Skip binned images if not showing them
                if is_binned and not self.show_binned_images:
                    continue
                
                # Calculate derived statistics
                votes = stats.get('votes', 0)
                wins = stats.get('wins', 0)
                losses = stats.get('losses', 0)
                win_rate = (wins / votes * 100) if votes > 0 else 0
                stability = self.ranking_algorithm._calculate_tier_stability(img_name)
                confidence = self.ranking_algorithm._calculate_image_confidence(img_name)
                last_voted = stats.get('last_voted', -1)
                current_tier = stats.get('current_tier', 0)
                
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
                
                # Status indicator
                if is_binned:
                    status = "🗑️ BIN"
                    status_sort_key = 1000  # Sort binned items at bottom by default
                else:
                    status = "📁 OK"
                    status_sort_key = 0
                
                all_images.append({
                    'name': img_name,
                    'status': status,
                    'status_sort_key': status_sort_key,
                    'tier': current_tier,
                    'votes': votes,
                    'wins': wins,
                    'losses': losses,
                    'win_rate': win_rate,
                    'stability': stability,
                    'confidence': confidence,
                    'last_voted': last_voted,
                    'last_voted_str': last_voted_str,
                    'prompt_preview': prompt_preview,
                    'is_binned': is_binned
                })
            
            # Sort by current tier (descending) by default, with binned items at bottom
            all_images.sort(key=lambda x: (x['status_sort_key'], -x['tier']), reverse=False)
            
            # Insert data into tree
            for img_data in all_images:
                # Color binned items differently
                tags = [img_data['name']]
                if img_data['is_binned']:
                    tags.append('binned')
                
                self.stats_tree.insert('', tk.END, values=(
                    img_data['status'],
                    img_data['name'],
                    f"{img_data['tier']:+d}" if img_data['tier'] != 0 else "0",
                    img_data['votes'],
                    img_data['wins'],
                    img_data['losses'],
                    f"{img_data['win_rate']:.1f}%",
                    f"{img_data['stability']:.2f}",
                    f"{img_data['confidence']:.2f}",
                    img_data['last_voted_str'],
                    img_data['prompt_preview']
                ), tags=tags)
            
            # Configure tag styles
            self.stats_tree.tag_configure('binned', background='#4a2c2c', foreground='#ff9999')
        
        except Exception as e:
            print(f"Error populating stats table: {e}")
    
    def sort_by_column(self, column):
        """
        Sort the table by the specified column.
        
        Args:
            column: Column name to sort by
        """
        if not self.stats_tree:
            return
        
        try:
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
                tags = self.stats_tree.item(item, 'tags')
                items.append((item, values, tags))
            
            # Define sort key functions for each column
            def get_sort_key(item_data):
                values = item_data[1]  # Get the values tuple
                tags = item_data[2]   # Get the tags
                
                # For status column, use special sorting to keep binned items grouped
                if column == 'Status':
                    return 0 if values[0] == "📁 OK" else 1
                elif column == 'Image':
                    return values[1].lower()  # Sort by name (case-insensitive)
                elif column == 'Tier':
                    return int(values[2]) if values[2] != "0" else 0  # Handle +/- signs
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
                elif column == 'Confidence':
                    return float(values[8])
                elif column == 'Last Voted':
                    # Special handling for "Never" and "Current"
                    if values[9] == "Never":
                        return float('inf')
                    elif values[9] == "Current":
                        return 0
                    else:
                        return int(values[9].split()[0])  # Extract number from "X ago"
                elif column == 'Prompt Preview':
                    return values[10].lower()
                else:
                    return values[1]  # Default to name
            
            # Sort items
            items.sort(key=get_sort_key, reverse=self.current_sort_reverse)
            
            # Update the tree order
            for index, (item, values, tags) in enumerate(items):
                self.stats_tree.move(item, '', index)
            
            # Update column header to show sort direction
            columns = ('Status', 'Image', 'Tier', 'Votes', 'Wins', 'Losses', 'Win Rate', 'Stability', 'Confidence', 'Last Voted', 'Prompt Preview')
            for col in columns:
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
        
        except Exception as e:
            print(f"Error sorting stats table: {e}")
    
    def on_tree_hover(self, event):
        """
        Handle mouse hover over table items.
        
        Args:
            event: Tkinter event object
        """
        if not self.stats_tree:
            return
        
        try:
            item = self.stats_tree.identify_row(event.y)
            
            if item:
                # Get the image filename from the item's tags
                tags = self.stats_tree.item(item, 'tags')
                if tags and self.hover_callback:
                    # Find the image filename tag (not 'binned')
                    image_filename = None
                    for tag in tags:
                        if tag != 'binned':
                            image_filename = tag
                            break
                    
                    if image_filename:
                        self.hover_callback(image_filename)
        except Exception as e:
            print(f"Error in table hover: {e}")
    
    def on_tree_leave(self, event):
        """
        Handle mouse leaving the table.
        
        Args:
            event: Tkinter event object
        """
        if self.leave_callback:
            try:
                self.leave_callback()
            except Exception as e:
                print(f"Error in table leave: {e}")
    
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
    
    def refresh_table(self):
        """Refresh the table with updated data."""
        self.populate_stats_table()
    
    def get_table_stats(self):
        """
        Get summary statistics about the table data.
        
        Returns:
            Dictionary with table statistics
        """
        if not self.stats_tree:
            return {'total_rows': 0, 'sort_info': {}, 'binned_visible': False}
        
        total_rows = len(self.stats_tree.get_children())
        binned_count = len(self.data_manager.get_binned_images())
        
        # Get current sort information
        sort_info = {
            'column': self.current_sort_column,
            'reverse': self.current_sort_reverse
        }
        
        return {
            'total_rows': total_rows,
            'sort_info': sort_info,
            'binned_visible': self.show_binned_images,
            'binned_count': binned_count
        }
    
    def get_selected_images(self) -> List[str]:
        """
        Get currently selected image names.
        
        Returns:
            List of selected image filenames
        """
        if not self.stats_tree:
            return []
        
        selected_items = self.stats_tree.selection()
        selected_images = []
        
        for item in selected_items:
            tags = self.stats_tree.item(item, 'tags')
            # Find the image filename tag (not 'binned')
            for tag in tags:
                if tag != 'binned':
                    selected_images.append(tag)
                    break
        
        return selected_images
    
    def select_image(self, image_name: str):
        """
        Select an image in the table.
        
        Args:
            image_name: Name of the image to select
        """
        if not self.stats_tree:
            return
        
        # Find the item with the matching tag
        for item in self.stats_tree.get_children():
            tags = self.stats_tree.item(item, 'tags')
            if image_name in tags:
                self.stats_tree.selection_set(item)
                self.stats_tree.focus(item)
                self.stats_tree.see(item)
                break
    
    def clear_selection(self):
        """Clear the table selection."""
        if self.stats_tree:
            self.stats_tree.selection_remove(self.stats_tree.selection())
    
    def filter_by_tier(self, tier: int):
        """
        Filter the table to show only images in a specific tier.
        
        Args:
            tier: Tier number to filter by
        """
        # This would require a more complex implementation with filtering
        # For now, we'll just refresh and let the user sort by tier
        self.refresh_table()
    
    def reset_filter(self):
        """Reset any filters and show all images."""
        self.populate_stats_table()
    
    def get_binning_summary(self) -> Dict[str, Any]:
        """Get summary of binning status."""
        binned_images = self.data_manager.get_binned_images()
        available_images = self.data_manager.get_available_images()
        
        return {
            'total_binned': len(binned_images),
            'total_available': len(available_images),
            'total_all': len(self.data_manager.image_stats),
            'showing_binned': self.show_binned_images,
            'binned_list': list(binned_images)
        }
    
    def cleanup(self):
        """Clean up table resources."""
        if self.stats_tree:
            try:
                # Clear all items
                for item in self.stats_tree.get_children():
                    self.stats_tree.delete(item)
            except:
                pass
            
            # Clear callbacks
            self.hover_callback = None
            self.leave_callback = None
        
        # Clear references
        self.stats_tree = None
        self.table_frame = None
