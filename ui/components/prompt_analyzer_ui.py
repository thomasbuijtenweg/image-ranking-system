"""
Prompt analyzer UI component for the Image Ranking System with binning support.

This module handles the prompt analysis interface, including word analysis
table, search functionality, and hover interactions with enhanced binning statistics.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Optional

from config import Colors


class PromptAnalyzerUI:
    """
    Handles the prompt analysis user interface with binning support.
    
    This component manages the prompt analysis tab with word statistics,
    search functionality, hover interactions, and enhanced binning analytics.
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
        self.content_frame = None
        
        # Sorting state
        self.word_sort_column = None
        self.word_sort_reverse = False
        
        # Callbacks
        self.hover_callback = None
        self.leave_callback = None
        self.export_callback = None
    
    def create_prompt_analysis_tab(self, parent_frame):
        """
        Create the prompt analysis tab interface with enhanced binning statistics.
        
        Args:
            parent_frame: Parent frame to contain the tab content
            
        Returns:
            The created tab frame
        """
        # Create main content frame
        self.content_frame = tk.Frame(parent_frame, bg=Colors.BG_SECONDARY)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create control frame
        control_frame = tk.Frame(self.content_frame, bg=Colors.BG_SECONDARY)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Enhanced analysis summary with binning statistics
        try:
            summary = self.prompt_analyzer.get_analysis_summary()
            summary_text = (f"Enhanced Prompt Analysis: {summary['total_words']} unique words | "
                           f"{summary['total_active_images_with_prompts']} active images with prompts | "
                           f"{summary['total_binned_images_with_prompts']} binned images with prompts | "
                           f"{summary['rare_words_count']} rare words | "
                           f"{summary['high_binning_rate_words']} high-binning words | "
                           f"{summary['avg_words_per_active_image']:.1f} avg words/active image")
        except Exception as e:
            print(f"Error getting analysis summary: {e}")
            summary_text = f"Error loading enhanced analysis summary: {str(e)}"
        
        summary_label = tk.Label(control_frame, text=summary_text, 
                                font=('Arial', 11, 'bold'), fg=Colors.TEXT_PRIMARY, 
                                bg=Colors.BG_SECONDARY, justify=tk.LEFT)
        summary_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Control buttons frame
        button_frame = tk.Frame(control_frame, bg=Colors.BG_SECONDARY)
        button_frame.pack(fill=tk.X)
        
        # Instructions
        instruction_text = "Click column headers to sort • Hover over any row to see example image • Red text = high binning rate"
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
        
        # Create word analysis table with enhanced columns
        self.create_word_analysis_table(self.content_frame)
        
        # Initial population
        self.refresh_analysis()
        
        return self.content_frame
    
    def create_word_analysis_table(self, parent_frame):
        """
        Create the enhanced word analysis table with binning statistics.
        
        Args:
            parent_frame: Parent frame to contain the table
        """
        # Create treeview for word analysis
        tree_frame = tk.Frame(parent_frame, bg=Colors.BG_SECONDARY)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview with scrollbar - enhanced columns for binning data
        columns = ('Word', 'Active Freq', 'Avg Tier', 'Binned Freq', 'Binning Rate', 'Quality Score', 'Example Images')
        self.word_tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', height=20)
        
        word_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.word_tree.yview)
        self.word_tree.configure(yscrollcommand=word_scrollbar.set)
        
        # Configure column headings with click handlers
        self.word_tree.heading('#0', text='', anchor=tk.W)
        self.word_tree.heading('Word', text='Word', anchor=tk.W)
        self.word_tree.heading('Active Freq', text='Active Freq', anchor=tk.CENTER)
        self.word_tree.heading('Avg Tier', text='Avg Tier', anchor=tk.CENTER)
        self.word_tree.heading('Binned Freq', text='Binned Freq', anchor=tk.CENTER)
        self.word_tree.heading('Binning Rate', text='Binning Rate', anchor=tk.CENTER)
        self.word_tree.heading('Quality Score', text='Quality Score', anchor=tk.CENTER)
        self.word_tree.heading('Example Images', text='Example Images', anchor=tk.W)
        
        # Set column widths
        self.word_tree.column('#0', width=0, stretch=False)
        self.word_tree.column('Word', width=120)
        self.word_tree.column('Active Freq', width=80)
        self.word_tree.column('Avg Tier', width=80)
        self.word_tree.column('Binned Freq', width=80)
        self.word_tree.column('Binning Rate', width=90)
        self.word_tree.column('Quality Score', width=90)
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
        """Refresh the enhanced prompt analysis display with binning data."""
        if not self.word_tree:
            return
        
        # Clear existing items
        for item in self.word_tree.get_children():
            self.word_tree.delete(item)
        
        # Check if we have any prompt data
        prompt_count = sum(1 for stats in self.data_manager.image_stats.values() 
                          if stats.get('prompt'))
        
        if prompt_count == 0:
            # Show message if no prompt data
            placeholder_item = self.word_tree.insert('', tk.END, values=(
                "No prompt data available", "", "", "", "", "", "Load images with AI generation prompts to analyze"
            ))
            self.word_tree.tag_configure('placeholder', foreground=Colors.TEXT_SECONDARY)
            self.word_tree.item(placeholder_item, tags=('placeholder',))
            return
        
        try:
            # Get search term
            search_term = self.search_var.get().strip().lower() if self.search_var else ""
            
            # Get word analysis
            if search_term:
                try:
                    word_data = self.prompt_analyzer.search_words_by_pattern(search_term)
                except Exception as e:
                    print(f"Error searching words: {e}")
                    error_item = self.word_tree.insert('', tk.END, values=(
                        f"Search error: {str(e)}", "", "", "", "", "", ""
                    ))
                    self.word_tree.tag_configure('error', foreground=Colors.TEXT_ERROR)
                    self.word_tree.item(error_item, tags=('error',))
                    return
            else:
                try:
                    # Sort by quality indicator by default (best words first)
                    word_analysis = self.prompt_analyzer.analyze_word_performance()
                    if not word_analysis:
                        # No word data available
                        placeholder_item = self.word_tree.insert('', tk.END, values=(
                            "No word analysis data", "", "", "", "", "", "Check if images have prompt metadata"
                        ))
                        self.word_tree.tag_configure('placeholder', foreground=Colors.TEXT_SECONDARY)
                        self.word_tree.item(placeholder_item, tags=('placeholder',))
                        return
                    
                    word_data = sorted(word_analysis.items(), 
                                     key=lambda x: x[1].get('quality_indicator', 0), reverse=True)
                except Exception as e:
                    print(f"Error analyzing word performance: {e}")
                    error_item = self.word_tree.insert('', tk.END, values=(
                        f"Analysis error: {str(e)}", "", "", "", "", "", ""
                    ))
                    self.word_tree.tag_configure('error', foreground=Colors.TEXT_ERROR)
                    self.word_tree.item(error_item, tags=('error',))
                    return
            
            # Populate tree with enhanced data
            for word, data in word_data:
                try:
                    active_tiers = data.get('active_tiers', [])
                    
                    # Get example images for this word
                    try:
                        example_images = self.get_example_images_for_word(word)
                        example_text = ", ".join(example_images[:3])
                        if len(example_images) > 3:
                            example_text += f" (+{len(example_images)-3} more)"
                    except Exception as e:
                        print(f"Error getting examples for word '{word}': {e}")
                        example_text = "Error getting examples"
                    
                    # Color coding based on quality and binning rate
                    quality_score = data.get('quality_indicator', 0)
                    binning_rate = data.get('binning_rate', 0)
                    
                    if binning_rate > 0.7:  # Very high binning rate
                        tag_color = "terrible"
                    elif binning_rate > 0.5:  # High binning rate
                        tag_color = "poor"
                    elif quality_score > 1.0:
                        tag_color = "excellent"
                    elif quality_score > 0.0:
                        tag_color = "good"
                    else:
                        tag_color = "poor"
                    
                    # Insert item with enhanced data
                    self.word_tree.insert('', tk.END, values=(
                        word,
                        data.get('active_frequency', 0),
                        f"{data.get('average_tier', 0):.2f}",
                        data.get('binned_frequency', 0),
                        f"{data.get('binning_rate', 0):.1%}",
                        f"{data.get('quality_indicator', 0):.2f}",
                        example_text
                    ), tags=(word, tag_color))
                
                except Exception as e:
                    print(f"Error processing word '{word}': {e}")
                    # Add error entry for this word
                    self.word_tree.insert('', tk.END, values=(
                        word, "Error", "Error", "Error", "Error", "Error", f"Error: {str(e)}"
                    ), tags=(word, "error"))
            
            # Configure color tags with enhanced color coding
            self.word_tree.tag_configure('excellent', foreground=Colors.TEXT_SUCCESS)
            self.word_tree.tag_configure('good', foreground=Colors.TEXT_PRIMARY)
            self.word_tree.tag_configure('poor', foreground=Colors.TEXT_WARNING)
            self.word_tree.tag_configure('terrible', foreground=Colors.TEXT_ERROR)
            self.word_tree.tag_configure('error', foreground=Colors.TEXT_ERROR)
            self.word_tree.tag_configure('placeholder', foreground=Colors.TEXT_SECONDARY)
            
            print(f"Successfully populated prompt analysis with {len(word_data) if word_data else 0} words")
        
        except Exception as e:
            error_msg = f"Critical error refreshing enhanced prompt analysis: {e}"
            print(error_msg)
            # Show error to user
            try:
                messagebox.showerror("Prompt Analysis Error", f"Failed to refresh prompt analysis:\n{str(e)}")
            except:
                pass
            
            # Add error row to table
            try:
                self.word_tree.insert('', tk.END, values=(
                    "CRITICAL ERROR", "Failed", "Failed", "Failed", "Failed", "Failed", str(e)
                ))
            except:
                pass
    
    def sort_by_column(self, column):
        """
        Sort the word analysis table by the specified column.
        
        Args:
            column: Column name to sort by
        """
        if not self.word_tree:
            return
        
        try:
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
                
                try:
                    if column == 'Word':
                        return str(values[0]).lower()  # Sort by word (case-insensitive)
                    elif column == 'Active Freq':
                        return int(values[1]) if str(values[1]).isdigit() else 0
                    elif column == 'Avg Tier':
                        return float(values[2]) if str(values[2]).replace('.', '').replace('-', '').isdigit() else 0
                    elif column == 'Binned Freq':
                        return int(values[3]) if str(values[3]).isdigit() else 0
                    elif column == 'Binning Rate':
                        rate_str = str(values[4]).rstrip('%')
                        return float(rate_str) if rate_str.replace('.', '').isdigit() else 0
                    elif column == 'Quality Score':
                        return float(values[5]) if str(values[5]).replace('.', '').replace('-', '').isdigit() else 0
                    elif column == 'Example Images':
                        return str(values[6]).lower()
                    else:
                        return str(values[0]).lower()  # Default to word
                except (ValueError, IndexError, AttributeError) as e:
                    print(f"Error sorting by {column}, using fallback: {e}")
                    return str(values[0]).lower() if values else ""  # Fallback to word
            
            # Sort items
            items.sort(key=get_sort_key, reverse=self.word_sort_reverse)
            
            # Update the tree order
            for index, (item, values) in enumerate(items):
                self.word_tree.move(item, '', index)
            
            # Update column header to show sort direction
            columns = ('Word', 'Active Freq', 'Avg Tier', 'Binned Freq', 'Binning Rate', 'Quality Score', 'Example Images')
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
        
        except Exception as e:
            print(f"Error sorting word analysis by {column}: {e}")
            messagebox.showerror("Sort Error", f"Failed to sort by {column}:\n{str(e)}")
    
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
        
        try:
            for image_name, stats in self.data_manager.image_stats.items():
                prompt = stats.get('prompt', '')
                if prompt:
                    try:
                        main_prompt = self.prompt_analyzer.extract_main_prompt(prompt)
                        words = self.prompt_analyzer.extract_words(main_prompt)
                        if word_lower in words:
                            example_images.append(image_name)
                            if len(example_images) >= 5:  # Limit for performance
                                break
                    except Exception as e:
                        print(f"Error processing prompt for {image_name} when finding examples for '{word}': {e}")
                        continue
        except Exception as e:
            print(f"Error getting example images for word '{word}': {e}")
        
        return example_images
    
    def on_tree_hover(self, event):
        """
        Handle mouse hover over word tree items.
        
        Args:
            event: Tkinter event object
        """
        if not self.word_tree:
            return
        
        try:
            item = self.word_tree.identify_row(event.y)
            if item:
                # Get the word from the item's tags
                tags = self.word_tree.item(item, 'tags')
                if tags and self.hover_callback and len(tags) > 0:
                    word = tags[0]
                    # Don't try to preview placeholder, error, or empty entries
                    if word not in ["No prompt data available", "No word analysis data", "CRITICAL ERROR"] and word.strip():
                        # Find an example image for this word and display it
                        try:
                            example_images = self.get_example_images_for_word(word)
                            if example_images:
                                self.hover_callback(example_images[0])
                        except Exception as e:
                            print(f"Error showing hover preview for word '{word}': {e}")
        except Exception as e:
            print(f"Error in tree hover: {e}")
    
    def on_tree_leave(self, event):
        """
        Handle mouse leaving the word tree.
        
        Args:
            event: Tkinter event object
        """
        if self.leave_callback:
            try:
                self.leave_callback()
            except Exception as e:
                print(f"Error in tree leave: {e}")
    
    def trigger_export(self):
        """Trigger the export functionality."""
        if self.export_callback:
            try:
                self.export_callback()
            except Exception as e:
                print(f"Error in export: {e}")
                messagebox.showerror("Export Error", f"Failed to export word analysis:\n{str(e)}")
    
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
        Get summary of the current analysis with enhanced binning statistics.
        
        Returns:
            Dictionary with analysis summary
        """
        if not self.word_tree:
            return {'total_words': 0, 'search_term': '', 'sort_info': {}}
        
        total_words = len(self.word_tree.get_children())
        
        # Get search term
        search_term = self.search_var.get().strip() if self.search_var else ""
        
        # Get current sort information
        sort_info = {
            'column': self.word_sort_column,
            'reverse': self.word_sort_reverse
        }
        
        # Get enhanced statistics from prompt analyzer
        try:
            prompt_summary = self.prompt_analyzer.get_analysis_summary()
            return {
                'total_words': total_words,
                'search_term': search_term,
                'sort_info': sort_info,
                'enhanced_stats': prompt_summary
            }
        except Exception as e:
            print(f"Error getting enhanced analysis summary: {e}")
            return {
                'total_words': total_words,
                'search_term': search_term,
                'sort_info': sort_info,
                'enhanced_stats': {'error': str(e)}
            }
    
    def clear_search(self):
        """Clear the search field and refresh."""
        if self.search_var:
            self.search_var.set("")
            self.refresh_analysis()
    
    def cleanup(self):
        """Clean up UI resources."""
        if self.word_tree:
            # Clear all items
            try:
                for item in self.word_tree.get_children():
                    self.word_tree.delete(item)
            except:
                pass
            
            # Clear callbacks
            self.hover_callback = None
            self.leave_callback = None
            self.export_callback = None
        
        # Clear search
        if self.search_var:
            self.search_var.set("")
        
        # Clear references
        self.word_tree = None
        self.search_entry = None
        self.content_frame = None