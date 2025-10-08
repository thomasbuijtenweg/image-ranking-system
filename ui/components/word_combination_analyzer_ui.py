"""
Word combination analyzer UI component for the Image Ranking System.

This module handles the word combination analysis interface, including combination
analysis table, filtering functionality, and hover interactions.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Optional, Dict, Any, Tuple

from config import Colors


class WordCombinationAnalyzerUI:
    """
    Handles the word combination analysis user interface.
    
    This component manages the combination analysis tab with word pair statistics,
    synergy analysis, filtering functionality, and hover interactions.
    """
    
    def __init__(self, data_manager, prompt_analyzer):
        """
        Initialize the word combination analyzer UI.
        
        Args:
            data_manager: DataManager instance
            prompt_analyzer: PromptAnalyzer instance
        """
        self.data_manager = data_manager
        self.prompt_analyzer = prompt_analyzer
        
        # UI elements
        self.combination_tree = None
        self.filter_frame = None
        self.synergy_filter_var = None
        self.min_frequency_var = None
        self.content_frame = None
        
        # Sorting state
        self.sort_column = None
        self.sort_reverse = False
        
        # Callbacks
        self.hover_callback = None
        self.leave_callback = None
        self.export_callback = None
    
    def create_combination_analysis_tab(self, parent_frame):
        """
        Create the word combination analysis tab interface.
        
        Args:
            parent_frame: Parent frame to contain the tab content
            
        Returns:
            The created tab frame
        """
        # Create main content frame
        self.content_frame = tk.Frame(parent_frame, bg=Colors.BG_SECONDARY)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create header section
        self.create_header_section(self.content_frame)
        
        # Create filter controls
        self.create_filter_section(self.content_frame)
        
        # Create results table
        self.create_results_table(self.content_frame)
        
        # Initial population
        self.refresh_combination_analysis()
        
        return self.content_frame
    
    def create_header_section(self, parent):
        """Create header with explanation and summary."""
        header_frame = tk.Frame(parent, bg=Colors.BG_SECONDARY)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title
        title_label = tk.Label(header_frame, 
                              text="Word Combination Analysis", 
                              font=('Arial', 14, 'bold'), 
                              fg=Colors.TEXT_PRIMARY, 
                              bg=Colors.BG_SECONDARY)
        title_label.pack(anchor=tk.W)
        
        # Explanation
        explanation = ("Analyzes how word pairs perform compared to their individual performance. "
                      "Synergistic pairs perform better together than expected from individual words, "
                      "while antagonistic pairs perform worse than expected.")
        
        tk.Label(header_frame, text=explanation, font=('Arial', 10), 
                fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY, 
                wraplength=800, justify=tk.LEFT).pack(anchor=tk.W, pady=5)
        
        # Dynamic summary
        try:
            summary = self.prompt_analyzer.get_combination_summary()
            if 'error' not in summary:
                summary_text = (f"Found {summary['total_combinations']} word pairs | "
                               f"{summary['synergistic_count']} synergistic | "
                               f"{summary['antagonistic_count']} antagonistic | "
                               f"{summary['neutral_count']} neutral | "
                               f"Avg synergy: {summary['avg_synergy_score']:.3f}")
            else:
                summary_text = f"Error loading summary: {summary['error']}"
        except Exception as e:
            summary_text = f"Error generating summary: {str(e)}"
        
        summary_label = tk.Label(header_frame, text=summary_text, 
                                font=('Arial', 11, 'bold'), fg=Colors.TEXT_INFO, 
                                bg=Colors.BG_SECONDARY, justify=tk.LEFT)
        summary_label.pack(anchor=tk.W, pady=(5, 0))
    
    def create_filter_section(self, parent):
        """Create filtering controls."""
        self.filter_frame = tk.Frame(parent, bg=Colors.BG_SECONDARY, 
                                    relief=tk.RAISED, borderwidth=1)
        self.filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Filter controls in a horizontal layout
        controls_frame = tk.Frame(self.filter_frame, bg=Colors.BG_SECONDARY)
        controls_frame.pack(padx=10, pady=10)
        
        # Synergy type filter
        tk.Label(controls_frame, text="Show:", font=('Arial', 10, 'bold'), 
                fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(side=tk.LEFT)
        
        self.synergy_filter_var = tk.StringVar(value="All")
        synergy_options = ["All", "Strong Synergy", "Moderate Synergy", "Neutral", 
                          "Moderate Antagonism", "Strong Antagonism"]
        
        synergy_combo = ttk.Combobox(controls_frame, textvariable=self.synergy_filter_var, 
                                    values=synergy_options, state="readonly", width=18)
        synergy_combo.pack(side=tk.LEFT, padx=5)
        synergy_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_combination_analysis())
        
        # Minimum frequency filter
        tk.Label(controls_frame, text="Min Frequency:", font=('Arial', 10, 'bold'), 
                fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(side=tk.LEFT, padx=(20, 5))
        
        self.min_frequency_var = tk.IntVar(value=3)
        frequency_spinbox = tk.Spinbox(controls_frame, from_=2, to=20, 
                                      textvariable=self.min_frequency_var, 
                                      width=5, command=self.refresh_combination_analysis)
        frequency_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = tk.Frame(controls_frame, bg=Colors.BG_SECONDARY)
        button_frame.pack(side=tk.RIGHT, padx=10)
        
        tk.Button(button_frame, text="Refresh", command=self.refresh_combination_analysis,
                 bg=Colors.BUTTON_INFO, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        
        tk.Button(button_frame, text="Export Combinations", command=self.trigger_export,
                 bg=Colors.BUTTON_WARNING, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        
        # Instructions
        instruction_text = "Click headers to sort • Hover over rows to see example images • Colors: Green=Synergy, Red=Antagonism"
        tk.Label(controls_frame, text=instruction_text, font=('Arial', 9, 'italic'), 
                fg=Colors.TEXT_INFO, bg=Colors.BG_SECONDARY).pack(side=tk.LEFT, padx=(20, 0))
    
    def create_results_table(self, parent):
        """Create the results table with sortable columns."""
        table_frame = tk.Frame(parent, bg=Colors.BG_SECONDARY)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Column definitions
        columns = ('Word Pair', 'Freq', 'Actual', 'Expected', 'Synergy', 'Type', 'Confidence', 'Examples')
        
        self.combination_tree = ttk.Treeview(table_frame, columns=columns, 
                                           show='tree headings', height=20)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", 
                                command=self.combination_tree.yview)
        self.combination_tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure headers with sort functionality
        self.combination_tree.heading('#0', text='', anchor=tk.W)
        for col in columns:
            self.combination_tree.heading(col, text=col, anchor=tk.CENTER)
            self.combination_tree.heading(col, command=lambda c=col: self.sort_by_column(c))
        
        # Set column widths
        self.combination_tree.column('#0', width=0, stretch=False)
        self.combination_tree.column('Word Pair', width=180)
        self.combination_tree.column('Freq', width=50)
        self.combination_tree.column('Actual', width=70)
        self.combination_tree.column('Expected', width=70)
        self.combination_tree.column('Synergy', width=70)
        self.combination_tree.column('Type', width=120)
        self.combination_tree.column('Confidence', width=80)
        self.combination_tree.column('Examples', width=200)
        
        # Bind hover events
        self.combination_tree.bind('<Motion>', self.on_tree_hover)
        self.combination_tree.bind('<Leave>', self.on_tree_leave)
        
        # Pack elements
        self.combination_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def refresh_combination_analysis(self):
        """Refresh the combination analysis display."""
        if not self.combination_tree:
            return
        
        # Clear existing items
        for item in self.combination_tree.get_children():
            self.combination_tree.delete(item)
        
        try:
            # Get minimum frequency
            min_freq = self.min_frequency_var.get() if self.min_frequency_var else 3
            
            # Get combination analysis
            combination_data = self.prompt_analyzer.analyze_word_combinations(min_freq)
            
            if not combination_data:
                # No combination data available
                placeholder_item = self.combination_tree.insert('', tk.END, values=(
                    "No combination data available", "", "", "", "", "", "", 
                    "Increase image count or reduce minimum frequency"
                ))
                self.combination_tree.tag_configure('placeholder', foreground=Colors.TEXT_SECONDARY)
                self.combination_tree.item(placeholder_item, tags=('placeholder',))
                return
            
            # Apply synergy type filter
            synergy_filter = self.synergy_filter_var.get() if self.synergy_filter_var else "All"
            if synergy_filter != "All":
                combination_data = {
                    pair: data for pair, data in combination_data.items() 
                    if data['synergy_type'] == synergy_filter
                }
            
            # Sort by synergy score (strongest synergy first)
            sorted_combinations = sorted(
                combination_data.items(),
                key=lambda x: x[1]['synergy_score'],
                reverse=True
            )
            
            # Populate table
            for pair, data in sorted_combinations:
                try:
                    # Get example images
                    examples = self.prompt_analyzer.get_combination_examples(
                        data['word1'], data['word2'], max_examples=3)
                    example_text = ", ".join(examples[:2])
                    if len(examples) > 2:
                        example_text += f" (+{len(examples)-2} more)"
                    elif not examples:
                        example_text = "No examples found"
                    
                    # Color coding based on synergy type
                    effect_type = data['synergy_type']
                    if "Strong Synergy" in effect_type:
                        tag_color = "strong_synergy"
                    elif "Moderate Synergy" in effect_type:
                        tag_color = "moderate_synergy"
                    elif "Strong Antagonism" in effect_type:
                        tag_color = "strong_antagonism"
                    elif "Moderate Antagonism" in effect_type:
                        tag_color = "moderate_antagonism"
                    else:
                        tag_color = "neutral"
                    
                    # Create pair display string
                    pair_display = f"{data['word1']} + {data['word2']}"
                    
                    item = self.combination_tree.insert('', tk.END, values=(
                        pair_display,
                        data['pair_frequency'],
                        f"{data['actual_performance']:.2f}",
                        f"{data['expected_performance']:.2f}",
                        f"{data['synergy_score']:+.2f}",
                        effect_type,
                        f"{data['confidence']:.2f}",
                        example_text
                    ), tags=(str(pair), tag_color))
                    
                except Exception as e:
                    print(f"Error processing combination {pair}: {e}")
                    # Add error entry
                    self.combination_tree.insert('', tk.END, values=(
                        f"{pair[0]} + {pair[1]}", "Error", "Error", "Error", "Error", 
                        f"Error: {str(e)}", "Error", "Error processing"
                    ), tags=(str(pair), "error"))
            
            # Configure color tags
            self.combination_tree.tag_configure('strong_synergy', foreground='#00FF00')  # Bright green
            self.combination_tree.tag_configure('moderate_synergy', foreground=Colors.TEXT_SUCCESS)  # Regular green
            self.combination_tree.tag_configure('neutral', foreground=Colors.TEXT_PRIMARY)
            self.combination_tree.tag_configure('moderate_antagonism', foreground=Colors.TEXT_WARNING)  # Orange
            self.combination_tree.tag_configure('strong_antagonism', foreground=Colors.TEXT_ERROR)  # Red
            self.combination_tree.tag_configure('error', foreground=Colors.TEXT_ERROR)
            self.combination_tree.tag_configure('placeholder', foreground=Colors.TEXT_SECONDARY)
            
            print(f"Successfully populated combination analysis with {len(sorted_combinations)} pairs")
        
        except Exception as e:
            error_msg = f"Error refreshing combination analysis: {e}"
            print(error_msg)
            # Show error to user
            try:
                messagebox.showerror("Combination Analysis Error", 
                                   f"Failed to refresh combination analysis:\n{str(e)}")
            except:
                pass
            
            # Add error row to table
            try:
                self.combination_tree.insert('', tk.END, values=(
                    "CRITICAL ERROR", "Failed", "Failed", "Failed", "Failed", 
                    "Failed", "Failed", str(e)
                ))
            except:
                pass
    
    def sort_by_column(self, column):
        """
        Sort the combination table by the specified column.
        
        Args:
            column: Column name to sort by
        """
        if not self.combination_tree:
            return
        
        try:
            # Toggle sort direction if clicking the same column
            if self.sort_column == column:
                self.sort_reverse = not self.sort_reverse
            else:
                self.sort_column = column
                self.sort_reverse = False
            
            # Get all items with their values
            items = []
            for item in self.combination_tree.get_children():
                values = self.combination_tree.item(item, 'values')
                items.append((item, values))
            
            # Define sort key functions for each column
            def get_sort_key(item_data):
                values = item_data[1]  # Get the values tuple
                
                try:
                    if column == 'Word Pair':
                        return str(values[0]).lower()
                    elif column == 'Freq':
                        return int(values[1]) if str(values[1]).isdigit() else 0
                    elif column == 'Actual':
                        return float(values[2]) if str(values[2]).replace('.', '').replace('-', '').isdigit() else 0
                    elif column == 'Expected':
                        return float(values[3]) if str(values[3]).replace('.', '').replace('-', '').isdigit() else 0
                    elif column == 'Synergy':
                        return float(values[4]) if str(values[4]).replace('.', '').replace('-', '').replace('+', '').isdigit() else 0
                    elif column == 'Type':
                        # Sort by synergy strength: Strong Synergy > Moderate Synergy > Neutral > Moderate Antagonism > Strong Antagonism
                        type_order = {
                            'Strong Synergy': 5,
                            'Moderate Synergy': 4,
                            'Neutral': 3,
                            'Moderate Antagonism': 2,
                            'Strong Antagonism': 1
                        }
                        return type_order.get(str(values[5]), 0)
                    elif column == 'Confidence':
                        return float(values[6]) if str(values[6]).replace('.', '').isdigit() else 0
                    elif column == 'Examples':
                        return str(values[7]).lower()
                    else:
                        return str(values[0]).lower()  # Default to pair name
                except (ValueError, IndexError, AttributeError) as e:
                    print(f"Error sorting by {column}: {e}")
                    return str(values[0]).lower() if values else ""  # Fallback
            
            # Sort items
            items.sort(key=get_sort_key, reverse=self.sort_reverse)
            
            # Update the tree order
            for index, (item, values) in enumerate(items):
                self.combination_tree.move(item, '', index)
            
            # Update column header to show sort direction
            columns = ('Word Pair', 'Freq', 'Actual', 'Expected', 'Synergy', 'Type', 'Confidence', 'Examples')
            for col in columns:
                current_text = self.combination_tree.heading(col, 'text')
                # Remove existing direction indicators
                clean_text = current_text.replace(" ↑", "").replace(" ↓", "")
                
                if col == column:
                    direction = " ↓" if self.sort_reverse else " ↑"
                    self.combination_tree.heading(col, text=clean_text + direction)
                else:
                    self.combination_tree.heading(col, text=clean_text)
        
        except Exception as e:
            print(f"Error sorting combination analysis by {column}: {e}")
            messagebox.showerror("Sort Error", f"Failed to sort by {column}:\n{str(e)}")
    
    def on_tree_hover(self, event):
        """
        Handle mouse hover over combination tree items.
        
        Args:
            event: Tkinter event object
        """
        if not self.combination_tree:
            return
        
        try:
            item = self.combination_tree.identify_row(event.y)
            if item:
                # Get the word pair from the item's tags
                tags = self.combination_tree.item(item, 'tags')
                if tags and self.hover_callback and len(tags) > 0:
                    pair_str = tags[0]
                    
                    # Don't try to preview placeholder or error entries
                    if pair_str not in ["No combination data available", "CRITICAL ERROR"] and pair_str.strip():
                        try:
                            # Parse the pair string back to individual words
                            # Format is "('word1', 'word2')" from str(pair)
                            if pair_str.startswith("(") and pair_str.endswith(")"):
                                pair_content = pair_str[1:-1]  # Remove parentheses
                                words = [w.strip().strip("'\"") for w in pair_content.split(",")]
                                if len(words) == 2:
                                    word1, word2 = words[0], words[1]
                                    # Find an example image for this word pair
                                    examples = self.prompt_analyzer.get_combination_examples(word1, word2, max_examples=1)
                                    if examples:
                                        self.hover_callback(examples[0])
                        except Exception as e:
                            print(f"Error showing hover preview for combination '{pair_str}': {e}")
        except Exception as e:
            print(f"Error in combination tree hover: {e}")
    
    def on_tree_leave(self, event):
        """
        Handle mouse leaving the combination tree.
        
        Args:
            event: Tkinter event object
        """
        if self.leave_callback:
            try:
                self.leave_callback()
            except Exception as e:
                print(f"Error in combination tree leave: {e}")
    
    def trigger_export(self):
        """Trigger the export functionality."""
        if self.export_callback:
            try:
                self.export_callback()
            except Exception as e:
                print(f"Error in export: {e}")
                messagebox.showerror("Export Error", f"Failed to export combination analysis:\n{str(e)}")
        else:
            messagebox.showinfo("Export", "Export functionality not yet implemented for combinations.")
    
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
        Get summary of the current combination analysis.
        
        Returns:
            Dictionary with analysis summary
        """
        if not self.combination_tree:
            return {'total_combinations': 0, 'filter_info': {}}
        
        total_combinations = len(self.combination_tree.get_children())
        
        # Get filter information
        synergy_filter = self.synergy_filter_var.get() if self.synergy_filter_var else "All"
        min_frequency = self.min_frequency_var.get() if self.min_frequency_var else 3
        
        # Get current sort information
        sort_info = {
            'column': self.sort_column,
            'reverse': self.sort_reverse
        }
        
        # Get detailed statistics from prompt analyzer
        try:
            combination_summary = self.prompt_analyzer.get_combination_summary()
            return {
                'total_combinations_displayed': total_combinations,
                'filter_info': {
                    'synergy_filter': synergy_filter,
                    'min_frequency': min_frequency
                },
                'sort_info': sort_info,
                'detailed_stats': combination_summary
            }
        except Exception as e:
            print(f"Error getting combination analysis summary: {e}")
            return {
                'total_combinations_displayed': total_combinations,
                'filter_info': {
                    'synergy_filter': synergy_filter,
                    'min_frequency': min_frequency
                },
                'sort_info': sort_info,
                'detailed_stats': {'error': str(e)}
            }
    
    def clear_filters(self):
        """Clear all filters and refresh."""
        if self.synergy_filter_var:
            self.synergy_filter_var.set("All")
        if self.min_frequency_var:
            self.min_frequency_var.set(3)
        self.refresh_combination_analysis()
    
    def cleanup(self):
        """Clean up UI resources."""
        if self.combination_tree:
            # Clear all items
            try:
                for item in self.combination_tree.get_children():
                    self.combination_tree.delete(item)
            except:
                pass
            
            # Clear callbacks
            self.hover_callback = None
            self.leave_callback = None
            self.export_callback = None
        
        # Clear references
        self.combination_tree = None
        self.content_frame = None
