"""
Modern statistics table component for the Image Ranking System.

This module handles the creation and management of the main statistics table
with modern styling, enhanced sorting, and hover effects.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Dict, Any, List

from config import Colors, Fonts, Styling
from ui.components.ui_builder import ModernFrame, ModernLabel, ModernButton


class ModernTreeview(ttk.Treeview):
    """Custom treeview with modern styling and enhanced functionality."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Configure modern styling
        self.configure(
            style="Modern.Treeview",
            selectmode='extended'
        )
        
        # Bind events for modern interactions
        self.bind('<Button-1>', self._on_click)
        self.bind('<Motion>', self._on_motion)
        self.bind('<Leave>', self._on_leave)
        
        # Track hover state
        self.hover_item = None
        self.last_hover_item = None
    
    def _on_click(self, event):
        """Handle click events with modern feedback."""
        item = self.identify_row(event.y)
        if item:
            # Visual feedback for click
            self.selection_set(item)
            self.focus(item)
    
    def _on_motion(self, event):
        """Handle mouse motion for hover effects."""
        item = self.identify_row(event.y)
        
        if item != self.hover_item:
            # Clear previous hover
            if self.hover_item:
                self.set(self.hover_item, '#hover', '')
            
            # Set new hover
            self.hover_item = item
            if item:
                self.set(item, '#hover', 'hover')
    
    def _on_leave(self, event):
        """Handle mouse leave."""
        if self.hover_item:
            self.set(self.hover_item, '#hover', '')
            self.hover_item = None


class ModernStatsTable:
    """
    Modern statistics table with enhanced styling and functionality.
    
    This component manages the sortable table showing individual image
    statistics with modern design and smooth interactions.
    """
    
    def __init__(self, data_manager, ranking_algorithm, prompt_analyzer):
        """
        Initialize the modern statistics table.
        
        Args:
            data_manager: DataManager instance
            ranking_algorithm: RankingAlgorithm instance
            prompt_analyzer: PromptAnalyzer instance
        """
        self.data_manager = data_manager
        self.ranking_algorithm = ranking_algorithm
        self.prompt_analyzer = prompt_analyzer
        
        # UI components
        self.table_frame = None
        self.stats_tree = None
        self.header_frame = None
        self.filter_frame = None
        
        # Sorting state
        self.current_sort_column = None
        self.current_sort_reverse = False
        
        # Filtering state
        self.filter_tier = None
        self.filter_text = ""
        
        # Callbacks
        self.hover_callback = None
        self.leave_callback = None
        self.selection_callback = None
        
        # Modern styling
        self._setup_modern_styles()
    
    def _setup_modern_styles(self):
        """Setup modern styles for the treeview."""
        style = ttk.Style()
        
        # Configure modern treeview style
        style.configure("Modern.Treeview",
                       background=Colors.BG_CARD,
                       foreground=Colors.TEXT_PRIMARY,
                       fieldbackground=Colors.BG_CARD,
                       borderwidth=0,
                       relief='flat',
                       selectbackground=Colors.PURPLE_PRIMARY,
                       selectforeground=Colors.TEXT_PRIMARY,
                       font=Fonts.NORMAL,
                       rowheight=32)
        
        # Configure modern treeview headings
        style.configure("Modern.Treeview.Heading",
                       background=Colors.BG_TERTIARY,
                       foreground=Colors.TEXT_PRIMARY,
                       borderwidth=0,
                       relief='flat',
                       font=Fonts.HEADING)
        
        # Configure hover effects
        style.map("Modern.Treeview",
                 background=[('selected', Colors.PURPLE_PRIMARY),
                           ('hover', Colors.BG_HOVER)])
        
        style.map("Modern.Treeview.Heading",
                 background=[('active', Colors.PURPLE_SECONDARY),
                           ('pressed', Colors.PURPLE_PRIMARY)])
    
    def create_stats_table(self, parent_frame):
        """
        Create the modern statistics table with enhanced styling.
        
        Args:
            parent_frame: Parent frame to contain the table
            
        Returns:
            The created table frame
        """
        # Main table container
        self.table_frame = ModernFrame(parent_frame, style='card')
        self.table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header with controls
        self._create_table_header()
        
        # Filter controls
        self._create_filter_controls()
        
        # Table content
        self._create_table_content()
        
        # Populate with data
        self.populate_stats_table()
        
        return self.table_frame
    
    def _create_table_header(self):
        """Create modern table header with title and controls."""
        self.header_frame = ModernFrame(self.table_frame)
        self.header_frame.pack(fill=tk.X, padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        # Title section
        title_frame = ModernFrame(self.header_frame)
        title_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Icon and title
        icon_label = ModernLabel(title_frame, text="📊", font=Fonts.LARGE, fg=Colors.PURPLE_PRIMARY)
        icon_label.pack(side=tk.LEFT)
        
        title_label = ModernLabel(title_frame, text="Image Statistics", font=Fonts.HEADING, fg=Colors.TEXT_PRIMARY)
        title_label.pack(side=tk.LEFT, padx=(Styling.PADDING_MEDIUM, 0))
        
        # Info badge
        total_images = len(self.data_manager.image_stats)
        info_badge = ModernLabel(title_frame, 
                               text=f"{total_images} images",
                               font=Fonts.SMALL,
                               fg=Colors.TEXT_SECONDARY)
        info_badge.pack(side=tk.LEFT, padx=(Styling.PADDING_MEDIUM, 0))
        
        # Controls section
        controls_frame = ModernFrame(self.header_frame)
        controls_frame.pack(side=tk.RIGHT)
        
        # Refresh button
        refresh_btn = ModernButton(controls_frame, 
                                  text="🔄 Refresh",
                                  command=self.refresh_table,
                                  style='secondary')
        refresh_btn.pack(side=tk.LEFT, padx=(0, Styling.PADDING_SMALL))
        
        # Clear selection button
        clear_btn = ModernButton(controls_frame,
                                text="✖️ Clear Selection",
                                command=self.clear_selection,
                                style='ghost')
        clear_btn.pack(side=tk.LEFT)
    
    def _create_filter_controls(self):
        """Create modern filter controls."""
        self.filter_frame = ModernFrame(self.table_frame, style='card')
        self.filter_frame.pack(fill=tk.X, padx=Styling.PADDING_LARGE, pady=(0, Styling.PADDING_MEDIUM))
        
        # Filter content
        filter_content = ModernFrame(self.filter_frame)
        filter_content.pack(fill=tk.X, padx=Styling.PADDING_MEDIUM, pady=Styling.PADDING_MEDIUM)
        
        # Filter label
        filter_label = ModernLabel(filter_content, text="🔍 Filters:", font=Fonts.MEDIUM, fg=Colors.TEXT_PRIMARY)
        filter_label.pack(side=tk.LEFT)
        
        # Tier filter
        tier_frame = ModernFrame(filter_content)
        tier_frame.pack(side=tk.LEFT, padx=(Styling.PADDING_LARGE, 0))
        
        tier_label = ModernLabel(tier_frame, text="Tier:", font=Fonts.SMALL, fg=Colors.TEXT_SECONDARY)
        tier_label.pack(side=tk.LEFT)
        
        self.tier_var = tk.StringVar(value="All")
        tier_combo = ttk.Combobox(tier_frame, 
                                 textvariable=self.tier_var,
                                 values=self._get_tier_options(),
                                 state='readonly',
                                 width=10)
        tier_combo.pack(side=tk.LEFT, padx=(Styling.PADDING_SMALL, 0))
        tier_combo.bind('<<ComboboxSelected>>', self._on_tier_filter_change)
        
        # Text filter
        text_frame = ModernFrame(filter_content)
        text_frame.pack(side=tk.LEFT, padx=(Styling.PADDING_LARGE, 0))
        
        text_label = ModernLabel(text_frame, text="Name:", font=Fonts.SMALL, fg=Colors.TEXT_SECONDARY)
        text_label.pack(side=tk.LEFT)
        
        self.text_var = tk.StringVar()
        text_entry = tk.Entry(text_frame,
                             textvariable=self.text_var,
                             width=20,
                             bg=Colors.BG_TERTIARY,
                             fg=Colors.TEXT_PRIMARY,
                             font=Fonts.SMALL,
                             relief='flat',
                             borderwidth=0,
                             highlightthickness=1,
                             highlightbackground=Colors.BORDER_PRIMARY,
                             highlightcolor=Colors.BORDER_ACCENT)
        text_entry.pack(side=tk.LEFT, padx=(Styling.PADDING_SMALL, 0))
        text_entry.bind('<KeyRelease>', self._on_text_filter_change)
        
        # Clear filters button
        clear_filters_btn = ModernButton(filter_content,
                                        text="❌ Clear Filters",
                                        command=self._clear_filters,
                                        style='ghost')
        clear_filters_btn.pack(side=tk.RIGHT)
    
    def _create_table_content(self):
        """Create the main table content area."""
        # Content frame
        content_frame = ModernFrame(self.table_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=Styling.PADDING_LARGE, pady=(0, Styling.PADDING_LARGE))
        
        # Define columns
        columns = ('Image', 'Tier', 'Votes', 'Wins', 'Losses', 'Win Rate', 'Stability', 'Confidence', 'Last Voted', 'Prompt Preview')
        
        # Create modern treeview
        self.stats_tree = ModernTreeview(content_frame, columns=columns, show='tree headings', height=20)
        
        # Create scrollbar
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.stats_tree.yview)
        self.stats_tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure column headings
        self.stats_tree.heading('#0', text='', anchor=tk.W)
        self.stats_tree.heading('Image', text='📁 Image Name', anchor=tk.W)
        self.stats_tree.heading('Tier', text='🎯 Tier', anchor=tk.CENTER)
        self.stats_tree.heading('Votes', text='🗳️ Votes', anchor=tk.CENTER)
        self.stats_tree.heading('Wins', text='🏆 Wins', anchor=tk.CENTER)
        self.stats_tree.heading('Losses', text='💔 Losses', anchor=tk.CENTER)
        self.stats_tree.heading('Win Rate', text='📊 Win Rate', anchor=tk.CENTER)
        self.stats_tree.heading('Stability', text='📈 Stability', anchor=tk.CENTER)
        self.stats_tree.heading('Confidence', text='🎯 Confidence', anchor=tk.CENTER)
        self.stats_tree.heading('Last Voted', text='🕐 Last Voted', anchor=tk.CENTER)
        self.stats_tree.heading('Prompt Preview', text='💬 Prompt Preview', anchor=tk.W)
        
        # Configure column widths
        self.stats_tree.column('#0', width=0, stretch=False)
        self.stats_tree.column('Image', width=180)
        self.stats_tree.column('Tier', width=80)
        self.stats_tree.column('Votes', width=70)
        self.stats_tree.column('Wins', width=60)
        self.stats_tree.column('Losses', width=60)
        self.stats_tree.column('Win Rate', width=90)
        self.stats_tree.column('Stability', width=80)
        self.stats_tree.column('Confidence', width=90)
        self.stats_tree.column('Last Voted', width=100)
        self.stats_tree.column('Prompt Preview', width=300)
        
        # Bind events
        for col in columns:
            self.stats_tree.heading(col, command=lambda c=col: self.sort_by_column(c))
        
        # Bind hover events
        self.stats_tree.bind('<Motion>', self._on_tree_hover)
        self.stats_tree.bind('<Leave>', self._on_tree_leave)
        self.stats_tree.bind('<<TreeviewSelect>>', self._on_selection_change)
        
        # Pack elements
        self.stats_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _get_tier_options(self):
        """Get available tier options for filtering."""
        tiers = set()
        for stats in self.data_manager.image_stats.values():
            tiers.add(stats.get('current_tier', 0))
        
        sorted_tiers = sorted(tiers)
        tier_options = ['All'] + [f"Tier {t:+d}" if t != 0 else "Tier 0" for t in sorted_tiers]
        
        return tier_options
    
    def _on_tier_filter_change(self, event):
        """Handle tier filter change."""
        selection = self.tier_var.get()
        if selection == 'All':
            self.filter_tier = None
        else:
            # Parse tier number from selection
            if selection == 'Tier 0':
                self.filter_tier = 0
            else:
                tier_str = selection.replace('Tier ', '').replace('+', '')
                self.filter_tier = int(tier_str)
        
        self.apply_filters()
    
    def _on_text_filter_change(self, event):
        """Handle text filter change."""
        self.filter_text = self.text_var.get().lower()
        self.apply_filters()
    
    def _clear_filters(self):
        """Clear all filters."""
        self.tier_var.set('All')
        self.text_var.set('')
        self.filter_tier = None
        self.filter_text = ""
        self.apply_filters()
    
    def apply_filters(self):
        """Apply current filters to the table."""
        # Clear existing items
        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)
        
        # Filter and populate
        filtered_data = []
        
        for img_name, stats in self.data_manager.image_stats.items():
            # Apply tier filter
            if self.filter_tier is not None:
                if stats.get('current_tier', 0) != self.filter_tier:
                    continue
            
            # Apply text filter
            if self.filter_text:
                if self.filter_text not in img_name.lower():
                    continue
            
            # Add to filtered data
            filtered_data.append((img_name, stats))
        
        # Populate table with filtered data
        self._populate_with_data(filtered_data)
    
    def populate_stats_table(self):
        """Populate the statistics table with all data."""
        if not self.stats_tree:
            return
        
        try:
            # Clear existing items
            for item in self.stats_tree.get_children():
                self.stats_tree.delete(item)
            
            # Get all data
            all_data = list(self.data_manager.image_stats.items())
            
            # Populate table
            self._populate_with_data(all_data)
            
        except Exception as e:
            print(f"Error populating stats table: {e}")
    
    def _populate_with_data(self, data_items):
        """Populate table with given data items."""
        processed_data = []
        
        for img_name, stats in data_items:
            # Calculate derived statistics
            votes = stats.get('votes', 0)
            wins = stats.get('wins', 0)
            losses = stats.get('losses', 0)
            win_rate = (wins / votes * 100) if votes > 0 else 0
            stability = self.ranking_algorithm._calculate_tier_stability(img_name)
            confidence = self.ranking_algorithm._calculate_image_confidence(img_name)
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
            
            processed_data.append({
                'name': img_name,
                'tier': stats.get('current_tier', 0),
                'votes': votes,
                'wins': wins,
                'losses': losses,
                'win_rate': win_rate,
                'stability': stability,
                'confidence': confidence,
                'last_voted': last_voted,
                'last_voted_str': last_voted_str,
                'prompt_preview': prompt_preview
            })
        
        # Sort by current tier (descending) by default
        processed_data.sort(key=lambda x: x['tier'], reverse=True)
        
        # Insert data into tree
        for img_data in processed_data:
            # Color-code tier
            tier_text = f"{img_data['tier']:+d}" if img_data['tier'] != 0 else "0"
            
            # Insert row
            item = self.stats_tree.insert('', tk.END, values=(
                img_data['name'],
                tier_text,
                img_data['votes'],
                img_data['wins'],
                img_data['losses'],
                f"{img_data['win_rate']:.1f}%",
                f"{img_data['stability']:.2f}",
                f"{img_data['confidence']:.2f}",
                img_data['last_voted_str'],
                img_data['prompt_preview']
            ), tags=(img_data['name'],))
            
            # Apply tier-based styling
            if img_data['tier'] > 0:
                self.stats_tree.set(item, 'Tier', f"🟢 {tier_text}")
            elif img_data['tier'] < 0:
                self.stats_tree.set(item, 'Tier', f"🔴 {tier_text}")
            else:
                self.stats_tree.set(item, 'Tier', f"⚪ {tier_text}")
    
    def sort_by_column(self, column):
        """Sort the table by the specified column with modern visual feedback."""
        if not self.stats_tree:
            return
        
        try:
            # Toggle sort direction
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
            
            # Sort items based on column
            items.sort(key=lambda x: self._get_sort_key(x[1], column), reverse=self.current_sort_reverse)
            
            # Update tree order
            for index, (item, values) in enumerate(items):
                self.stats_tree.move(item, '', index)
            
            # Update column headers with sort indicators
            self._update_sort_headers(column)
            
        except Exception as e:
            print(f"Error sorting stats table: {e}")
    
    def _get_sort_key(self, values, column):
        """Get sort key for a column."""
        if column == 'Image':
            return values[0].lower()
        elif column == 'Tier':
            tier_str = values[1].replace('🟢 ', '').replace('🔴 ', '').replace('⚪ ', '')
            return int(tier_str)
        elif column == 'Votes':
            return int(values[2])
        elif column == 'Wins':
            return int(values[3])
        elif column == 'Losses':
            return int(values[4])
        elif column == 'Win Rate':
            return float(values[5].rstrip('%'))
        elif column == 'Stability':
            return float(values[6])
        elif column == 'Confidence':
            return float(values[7])
        elif column == 'Last Voted':
            if values[8] == "Never":
                return float('inf')
            elif values[8] == "Current":
                return 0
            else:
                return int(values[8].split()[0])
        elif column == 'Prompt Preview':
            return values[9].lower()
        else:
            return values[0]
    
    def _update_sort_headers(self, sorted_column):
        """Update column headers with sort indicators."""
        columns = ('Image', 'Tier', 'Votes', 'Wins', 'Losses', 'Win Rate', 'Stability', 'Confidence', 'Last Voted', 'Prompt Preview')
        
        # Header text mapping
        header_text = {
            'Image': '📁 Image Name',
            'Tier': '🎯 Tier',
            'Votes': '🗳️ Votes',
            'Wins': '🏆 Wins',
            'Losses': '💔 Losses',
            'Win Rate': '📊 Win Rate',
            'Stability': '📈 Stability',
            'Confidence': '🎯 Confidence',
            'Last Voted': '🕐 Last Voted',
            'Prompt Preview': '💬 Prompt Preview'
        }
        
        for col in columns:
            if col == sorted_column:
                direction = " ▼" if self.current_sort_reverse else " ▲"
                self.stats_tree.heading(col, text=header_text[col] + direction)
            else:
                self.stats_tree.heading(col, text=header_text[col])
    
    def _on_tree_hover(self, event):
        """Handle tree hover events."""
        if not self.stats_tree:
            return
        
        try:
            item = self.stats_tree.identify_row(event.y)
            if item:
                tags = self.stats_tree.item(item, 'tags')
                if tags and self.hover_callback:
                    image_filename = tags[0]
                    self.hover_callback(image_filename)
        except Exception as e:
            print(f"Error in table hover: {e}")
    
    def _on_tree_leave(self, event):
        """Handle tree leave events."""
        if self.leave_callback:
            try:
                self.leave_callback()
            except Exception as e:
                print(f"Error in table leave: {e}")
    
    def _on_selection_change(self, event):
        """Handle selection change events."""
        if self.selection_callback:
            selected_images = self.get_selected_images()
            self.selection_callback(selected_images)
    
    def set_hover_callback(self, callback: Callable[[str], None]):
        """Set callback for hover events."""
        self.hover_callback = callback
    
    def set_leave_callback(self, callback: Callable[[], None]):
        """Set callback for leave events."""
        self.leave_callback = callback
    
    def set_selection_callback(self, callback: Callable[[List[str]], None]):
        """Set callback for selection change events."""
        self.selection_callback = callback
    
    def refresh_table(self):
        """Refresh the table with updated data."""
        # Update tier filter options
        if hasattr(self, 'tier_var'):
            tier_combo = None
            for widget in self.filter_frame.winfo_children():
                for subwidget in widget.winfo_children():
                    if isinstance(subwidget, ttk.Combobox):
                        tier_combo = subwidget
                        break
            
            if tier_combo:
                tier_combo.configure(values=self._get_tier_options())
        
        # Refresh data
        if self.filter_tier is not None or self.filter_text:
            self.apply_filters()
        else:
            self.populate_stats_table()
    
    def get_selected_images(self) -> List[str]:
        """Get currently selected image names."""
        if not self.stats_tree:
            return []
        
        selected_items = self.stats_tree.selection()
        selected_images = []
        
        for item in selected_items:
            tags = self.stats_tree.item(item, 'tags')
            if tags:
                selected_images.append(tags[0])
        
        return selected_images
    
    def select_image(self, image_name: str):
        """Select an image in the table."""
        if not self.stats_tree:
            return
        
        for item in self.stats_tree.get_children():
            tags = self.stats_tree.item(item, 'tags')
            if tags and tags[0] == image_name:
                self.stats_tree.selection_set(item)
                self.stats_tree.focus(item)
                self.stats_tree.see(item)
                break
    
    def clear_selection(self):
        """Clear the table selection."""
        if self.stats_tree:
            self.stats_tree.selection_remove(self.stats_tree.selection())
    
    def get_table_stats(self):
        """Get summary statistics about the table."""
        if not self.stats_tree:
            return {'total_rows': 0, 'filtered_rows': 0, 'sort_info': {}}
        
        total_rows = len(self.data_manager.image_stats)
        filtered_rows = len(self.stats_tree.get_children())
        
        return {
            'total_rows': total_rows,
            'filtered_rows': filtered_rows,
            'sort_info': {
                'column': self.current_sort_column,
                'reverse': self.current_sort_reverse
            },
            'filter_info': {
                'tier': self.filter_tier,
                'text': self.filter_text
            }
        }
    
    def cleanup(self):
        """Clean up table resources."""
        if self.stats_tree:
            try:
                for item in self.stats_tree.get_children():
                    self.stats_tree.delete(item)
            except:
                pass
            
            # Clear callbacks
            self.hover_callback = None
            self.leave_callback = None
            self.selection_callback = None
        
        # Clear references
        self.stats_tree = None
        self.table_frame = None


# Backward compatibility
class StatsTable(ModernStatsTable):
    """Backward compatibility alias."""
    pass
