"""Statistics window for the Image Ranking System with word combination analysis."""

import tkinter as tk
from tkinter import ttk
import os

from config import Colors
from ui.mixins import ImagePreviewMixin
from ui.components.chart_generator import ChartGenerator
from ui.components.data_exporter import DataExporter
from ui.components.prompt_analyzer_ui import PromptAnalyzerUI
from ui.components.word_combination_analyzer_ui import WordCombinationAnalyzerUI
from ui.components.stats_table import StatsTable


class StatsWindow(ImagePreviewMixin):
    """Window for displaying detailed statistics about the ranking system with combination analysis."""
    
    def __init__(self, parent: tk.Tk, data_manager, ranking_algorithm, prompt_analyzer):
        ImagePreviewMixin.__init__(self)
        
        self.parent = parent
        self.data_manager = data_manager
        self.ranking_algorithm = ranking_algorithm
        self.prompt_analyzer = prompt_analyzer
        self.window = None
        self.notebook = None
        
        self.chart_generator = ChartGenerator(data_manager)
        self.data_exporter = DataExporter(data_manager, prompt_analyzer, ranking_algorithm)
        self.stats_table = StatsTable(data_manager, ranking_algorithm, prompt_analyzer)
        self.prompt_analyzer_ui = PromptAnalyzerUI(data_manager, prompt_analyzer)
        self.word_combination_ui = None  # Will be created if needed
    
    def show(self):
        """Show the statistics window."""
        if self.window is None or not self.window.winfo_exists():
            self.create_window()
        else:
            self.window.lift()
            self.window.focus_force()
    
    def focus_prompt_analysis_tab(self):
        """Focus on the prompt analysis tab."""
        if self.notebook:
            for i in range(self.notebook.index("end")):
                if "Prompt Analysis" in self.notebook.tab(i, "text"):
                    self.notebook.select(i)
                    break
    
    def create_window(self):
        """Create the statistics window."""
        try:
            from core.image_processor import ImageProcessor
            self.image_processor = ImageProcessor()
            
            self.window = tk.Toplevel(self.parent)
            self.window.title("Detailed Statistics & Analysis")
            self.window.geometry("1800x900")
            self.window.minsize(1200, 600)
            self.window.configure(bg=Colors.BG_PRIMARY)
            
            self.window.protocol("WM_DELETE_WINDOW", self.close_window)
            
            self.setup_preview_resize_handling()
            
            main_frame = tk.Frame(self.window, bg=Colors.BG_PRIMARY)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            main_frame.grid_columnconfigure(0, weight=1, minsize=700)
            main_frame.grid_columnconfigure(1, weight=1, minsize=700)
            main_frame.grid_rowconfigure(0, weight=1)
            
            self.notebook = ttk.Notebook(main_frame)
            self.notebook.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
            
            preview_frame = self.create_image_preview_area(main_frame, include_additional_stats=True)
            preview_frame.grid(row=0, column=1, sticky="nsew")
            
            self.create_main_stats_tab(self.notebook)
            
            prompt_count = sum(1 for stats in self.data_manager.image_stats.values() 
                              if stats.get('prompt'))
            if prompt_count > 0:
                self.create_prompt_analysis_tab(self.notebook)
            
            print("Stats window created and populated successfully with combination analysis")
            
        except Exception as e:
            print(f"Error creating stats window: {e}")
            import traceback
            print(traceback.format_exc())
            raise
    
    def create_main_stats_tab(self, notebook: ttk.Notebook):
        """Create the main statistics tab."""
        try:
            frame = tk.Frame(notebook, bg=Colors.BG_SECONDARY)
            notebook.add(frame, text="Image Statistics")
            
            header_frame = tk.Frame(frame, bg=Colors.BG_SECONDARY)
            header_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Get overall statistics with error handling
            try:
                overall_stats = self.data_manager.get_overall_statistics()
                print(f"Overall stats keys: {list(overall_stats.keys())}")  # Debug output
                
                # Calculate total images from active + binned
                total_active = overall_stats.get('total_active_images', 0)
                total_binned = overall_stats.get('total_binned_images', 0)
                total_images = total_active + total_binned
                
                overall_text = (f"Total Images: {total_images} (Active: {total_active}, Binned: {total_binned}) | "
                               f"Total Votes: {overall_stats.get('total_votes', 0)} | "
                               f"Avg Votes/Active Image: {overall_stats.get('avg_votes_per_active_image', 0):.1f}")
            except Exception as e:
                print(f"Error getting overall statistics: {e}")
                overall_text = f"Error loading statistics: {str(e)}"
            
            tk.Label(header_frame, text=overall_text, font=('Arial', 12, 'bold'), 
                    fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
            
            # Create chart with error handling
            try:
                chart_frame = tk.Frame(frame, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=1)
                chart_frame.pack(fill=tk.X, padx=10, pady=5)
                self.chart_generator.create_tier_distribution_chart(chart_frame)
            except Exception as e:
                print(f"Error creating chart: {e}")
                # Create a simple label instead of crashing
                error_frame = tk.Frame(frame, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=1)
                error_frame.pack(fill=tk.X, padx=10, pady=5)
                tk.Label(error_frame, text=f"Chart unavailable: {str(e)}", 
                        fg=Colors.TEXT_ERROR, bg=Colors.BG_SECONDARY).pack(pady=10)
            
            instruction_text = "Click column headers to sort • Hover over any row to see image preview"
            tk.Label(header_frame, text=instruction_text, font=('Arial', 10, 'italic'), 
                    fg=Colors.TEXT_INFO, bg=Colors.BG_SECONDARY).pack(anchor=tk.W, pady=(5, 0))
            
            # Create stats table with error handling
            try:
                self.stats_table.create_stats_table(frame)
                self.stats_table.set_hover_callback(self.display_preview_image)
                self.stats_table.set_leave_callback(lambda: None)
            except Exception as e:
                print(f"Error creating stats table: {e}")
                # Create error label instead of crashing
                error_label = tk.Label(frame, text=f"Table unavailable: {str(e)}", 
                                     fg=Colors.TEXT_ERROR, bg=Colors.BG_SECONDARY)
                error_label.pack(pady=20)
            
        except Exception as e:
            print(f"Error creating main stats tab: {e}")
            # Create a basic error tab
            error_frame = tk.Frame(notebook, bg=Colors.BG_SECONDARY)
            notebook.add(error_frame, text="Statistics (Error)")
            tk.Label(error_frame, text=f"Error creating statistics tab:\n{str(e)}", 
                    fg=Colors.TEXT_ERROR, bg=Colors.BG_SECONDARY, 
                    font=('Arial', 12), justify=tk.CENTER).pack(expand=True)
    
    def create_prompt_analysis_tab(self, notebook: ttk.Notebook):
        """Create the prompt analysis tab with sub-tabs for individual words and combinations."""
        try:
            # Main frame for the prompt analysis tab
            main_frame = tk.Frame(notebook, bg=Colors.BG_SECONDARY)
            notebook.add(main_frame, text="Prompt Analysis")
            
            # Create sub-notebook for different analysis types
            sub_notebook = ttk.Notebook(main_frame)
            sub_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Individual word analysis tab
            word_frame = tk.Frame(sub_notebook, bg=Colors.BG_SECONDARY)
            sub_notebook.add(word_frame, text="Individual Words")
            self.prompt_analyzer_ui.create_prompt_analysis_tab(word_frame)
            
            # Set up individual word analysis callbacks
            self.prompt_analyzer_ui.set_hover_callback(self.display_preview_image)
            self.prompt_analyzer_ui.set_leave_callback(lambda: None)
            self.prompt_analyzer_ui.set_export_callback(self.export_word_analysis)
            
            # Word combination analysis tab
            try:
                combination_frame = tk.Frame(sub_notebook, bg=Colors.BG_SECONDARY)
                sub_notebook.add(combination_frame, text="Word Combinations")
                
                # Create the combination analyzer UI
                self.word_combination_ui = WordCombinationAnalyzerUI(self.data_manager, self.prompt_analyzer)
                self.word_combination_ui.create_combination_analysis_tab(combination_frame)
                
                # Set up combination analysis callbacks
                self.word_combination_ui.set_hover_callback(self.display_preview_image)
                self.word_combination_ui.set_leave_callback(lambda: None)
                self.word_combination_ui.set_export_callback(self.export_combination_analysis)
                
                print("Word combination analysis tab created successfully")
                
            except Exception as e:
                print(f"Error creating word combination analysis tab: {e}")
                # Create error tab instead
                error_frame = tk.Frame(sub_notebook, bg=Colors.BG_SECONDARY)
                sub_notebook.add(error_frame, text="Word Combinations (Error)")
                tk.Label(error_frame, text=f"Error creating combination analysis:\n{str(e)}", 
                        fg=Colors.TEXT_ERROR, bg=Colors.BG_SECONDARY, 
                        font=('Arial', 12), justify=tk.CENTER).pack(expand=True, pady=50)
            
        except Exception as e:
            print(f"Error creating prompt analysis tab: {e}")
            # Create a basic error tab
            error_frame = tk.Frame(notebook, bg=Colors.BG_SECONDARY)
            notebook.add(error_frame, text="Prompt Analysis (Error)")
            tk.Label(error_frame, text=f"Error creating prompt analysis tab:\n{str(e)}", 
                    fg=Colors.TEXT_ERROR, bg=Colors.BG_SECONDARY, 
                    font=('Arial', 12), justify=tk.CENTER).pack(expand=True)
    
    def export_word_analysis(self):
        """Export individual word analysis."""
        try:
            self.data_exporter.export_word_analysis(self.window)
        except Exception as e:
            print(f"Error exporting word analysis: {e}")
            tk.messagebox.showerror("Export Error", f"Failed to export word analysis:\n{str(e)}")
    
    def export_combination_analysis(self):
        """Export word combination analysis."""
        try:
            # Use the enhanced data exporter with combination analysis support
            self.data_exporter.export_combination_analysis(self.window)
        except Exception as e:
            print(f"Error exporting combination analysis: {e}")
            tk.messagebox.showerror("Export Error", f"Failed to export combination analysis:\n{str(e)}")
    
    def refresh_stats(self):
        """Refresh all statistics displays including combination analysis."""
        try:
            if hasattr(self, 'stats_table') and self.stats_table:
                self.stats_table.refresh_table()
            
            if hasattr(self, 'chart_generator') and self.chart_generator:
                # Find and refresh charts
                if self.window and self.window.winfo_exists():
                    for widget in self.window.winfo_children():
                        if isinstance(widget, tk.Frame):
                            for child in widget.winfo_children():
                                if isinstance(child, ttk.Notebook):
                                    for tab_id in range(child.index("end")):
                                        try:
                                            tab_frame = child.nametowidget(child.tabs()[tab_id])
                                            for frame_child in tab_frame.winfo_children():
                                                if hasattr(frame_child, 'winfo_children'):
                                                    for chart_candidate in frame_child.winfo_children():
                                                        if isinstance(chart_candidate, tk.Frame):
                                                            try:
                                                                self.chart_generator.refresh_chart(chart_candidate)
                                                            except Exception as chart_error:
                                                                print(f"Error refreshing chart: {chart_error}")
                                        except Exception as tab_error:
                                            print(f"Error refreshing tab: {tab_error}")
            
            if hasattr(self, 'prompt_analyzer_ui') and self.prompt_analyzer_ui:
                self.prompt_analyzer_ui.refresh_analysis()
            
            if hasattr(self, 'word_combination_ui') and self.word_combination_ui:
                self.word_combination_ui.refresh_combination_analysis()
                
        except Exception as e:
            print(f"Error refreshing stats: {e}")
    
    def get_stats_summary(self):
        """Get a summary of the current statistics including combination analysis."""
        try:
            summary = {
                'overall_stats': self.data_manager.get_overall_statistics(),
                'chart_data': self.chart_generator.get_chart_data_summary() if hasattr(self, 'chart_generator') else {},
                'table_stats': self.stats_table.get_table_stats() if hasattr(self, 'stats_table') else {},
                'prompt_analysis': self.prompt_analyzer_ui.get_analysis_summary() if hasattr(self, 'prompt_analyzer_ui') else {},
                'combination_analysis': self.word_combination_ui.get_analysis_summary() if hasattr(self, 'word_combination_ui') and self.word_combination_ui else {}
            }
            return summary
        except Exception as e:
            print(f"Error getting stats summary: {e}")
            return {'error': str(e)}
    
    def export_all_data(self):
        """Export all available data including combination analysis."""
        try:
            if hasattr(self, 'data_exporter'):
                export_options = self.data_exporter.get_export_options()
                
                dialog = tk.Toplevel(self.window)
                dialog.title("Export Data")
                dialog.geometry("500x400")
                dialog.configure(bg=Colors.BG_PRIMARY)
                dialog.transient(self.window)
                dialog.grab_set()
                
                dialog.geometry("+%d+%d" % (
                    self.window.winfo_rootx() + 200,
                    self.window.winfo_rooty() + 200
                ))
                
                tk.Label(dialog, text="Select Export Type", 
                        font=('Arial', 14, 'bold'), fg=Colors.TEXT_PRIMARY, 
                        bg=Colors.BG_PRIMARY).pack(pady=10)
                
                # Create scrollable frame for export options
                canvas = tk.Canvas(dialog, bg=Colors.BG_PRIMARY, highlightthickness=0)
                scrollbar = tk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
                scrollable_frame = tk.Frame(canvas, bg=Colors.BG_PRIMARY)
                
                canvas.configure(yscrollcommand=scrollbar.set)
                canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                
                for export_type, description in export_options.items():
                    # All exports are now enabled
                    btn = tk.Button(scrollable_frame, text=description, 
                                  command=lambda t=export_type: self._export_and_close(t, dialog),
                                  bg=Colors.BUTTON_INFO, fg='white', relief=tk.FLAT, 
                                  wraplength=400, justify=tk.LEFT)
                    btn.pack(pady=5, padx=20, fill=tk.X)
                
                scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
                
                canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=(0, 50))
                scrollbar.pack(side="right", fill="y", pady=(0, 50))
                
                tk.Button(dialog, text="Cancel", command=dialog.destroy,
                         bg=Colors.BUTTON_NEUTRAL, fg='white', relief=tk.FLAT).pack(side=tk.BOTTOM, pady=10)
        except Exception as e:
            print(f"Error showing export dialog: {e}")
            tk.messagebox.showerror("Export Error", f"Failed to show export options:\n{str(e)}")
    
    def _export_and_close(self, export_type, dialog):
        """Helper method to export data and close dialog."""
        try:
            dialog.destroy()
            self.data_exporter.export_by_type(export_type, self.window)
        except Exception as e:
            print(f"Error exporting {export_type}: {e}")
            tk.messagebox.showerror("Export Error", f"Failed to export {export_type}:\n{str(e)}")
    
    def close_window(self):
        """Handle window closing with cleanup including combination analysis."""
        try:
            if hasattr(self, 'chart_generator'):
                self.chart_generator.cleanup_chart()
            
            if hasattr(self, 'stats_table'):
                self.stats_table.cleanup()
            
            if hasattr(self, 'prompt_analyzer_ui'):
                self.prompt_analyzer_ui.cleanup()
            
            if hasattr(self, 'word_combination_ui') and self.word_combination_ui:
                self.word_combination_ui.cleanup()
            
            self.cleanup_preview_resources()
            
        except Exception as e:
            print(f"Error during stats window cleanup: {e}")
        
        try:
            if self.window:
                self.window.destroy()
                self.window = None
        except Exception as e:
            print(f"Error destroying stats window: {e}")
