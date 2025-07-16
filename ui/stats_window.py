"""Statistics window for the Image Ranking System."""

import tkinter as tk
from tkinter import ttk
import os

from config import Colors
from ui.mixins import ImagePreviewMixin
from ui.components.chart_generator import ChartGenerator
from ui.components.data_exporter import DataExporter
from ui.components.prompt_analyzer_ui import PromptAnalyzerUI
from ui.components.stats_table import StatsTable


class StatsWindow(ImagePreviewMixin):
    """Window for displaying detailed statistics about the ranking system."""
    
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
        from core.image_processor import ImageProcessor
        self.image_processor = ImageProcessor()
        
        self.window = tk.Toplevel(self.parent)
        self.window.title("Detailed Statistics")
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
    
    def create_main_stats_tab(self, notebook: ttk.Notebook):
        """Create the main statistics tab."""
        frame = tk.Frame(notebook, bg=Colors.BG_SECONDARY)
        notebook.add(frame, text="Image Statistics")
        
        header_frame = tk.Frame(frame, bg=Colors.BG_SECONDARY)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        overall_stats = self.data_manager.get_overall_statistics()
        overall_text = (f"Total Images: {overall_stats['total_images']} | "
                       f"Total Votes: {overall_stats['total_votes']} | "
                       f"Avg Votes/Image: {overall_stats['avg_votes_per_image']:.1f}")
        
        tk.Label(header_frame, text=overall_text, font=('Arial', 12, 'bold'), 
                fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY).pack(anchor=tk.W)
        
        chart_frame = tk.Frame(frame, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=1)
        chart_frame.pack(fill=tk.X, padx=10, pady=5)
        self.chart_generator.create_tier_distribution_chart(chart_frame)
        
        instruction_text = "Click column headers to sort • Hover over any row to see image preview"
        tk.Label(header_frame, text=instruction_text, font=('Arial', 10, 'italic'), 
                fg=Colors.TEXT_INFO, bg=Colors.BG_SECONDARY).pack(anchor=tk.W, pady=(5, 0))
        
        self.stats_table.create_stats_table(frame)
        
        self.stats_table.set_hover_callback(self.display_preview_image)
        self.stats_table.set_leave_callback(lambda: None)
    
    def create_prompt_analysis_tab(self, notebook: ttk.Notebook):
        """Create the prompt analysis tab."""
        frame = tk.Frame(notebook, bg=Colors.BG_SECONDARY)
        notebook.add(frame, text="Prompt Analysis")
        
        self.prompt_analyzer_ui.create_prompt_analysis_tab(frame)
        
        self.prompt_analyzer_ui.set_hover_callback(self.display_preview_image)
        self.prompt_analyzer_ui.set_leave_callback(lambda: None)
        self.prompt_analyzer_ui.set_export_callback(self.export_word_analysis)
    
    def export_word_analysis(self):
        """Export word analysis."""
        self.data_exporter.export_word_analysis(self.window)
    
    def refresh_stats(self):
        """Refresh all statistics displays."""
        if hasattr(self, 'stats_table'):
            self.stats_table.refresh_table()
        
        if hasattr(self, 'chart_generator'):
            for widget in self.window.winfo_children():
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Notebook):
                            for tab_id in range(child.index("end")):
                                tab_frame = child.nametowidget(child.tabs()[tab_id])
                                for frame_child in tab_frame.winfo_children():
                                    if hasattr(frame_child, 'winfo_children'):
                                        for chart_candidate in frame_child.winfo_children():
                                            if isinstance(chart_candidate, tk.Frame):
                                                try:
                                                    self.chart_generator.refresh_chart(chart_candidate)
                                                except:
                                                    pass
        
        if hasattr(self, 'prompt_analyzer_ui'):
            self.prompt_analyzer_ui.refresh_analysis()
    
    def get_stats_summary(self):
        """Get a summary of the current statistics."""
        summary = {
            'overall_stats': self.data_manager.get_overall_statistics(),
            'chart_data': self.chart_generator.get_chart_data_summary() if hasattr(self, 'chart_generator') else {},
            'table_stats': self.stats_table.get_table_stats() if hasattr(self, 'stats_table') else {},
            'prompt_analysis': self.prompt_analyzer_ui.get_analysis_summary() if hasattr(self, 'prompt_analyzer_ui') else {}
        }
        return summary
    
    def export_all_data(self):
        """Export all available data."""
        if hasattr(self, 'data_exporter'):
            export_options = self.data_exporter.get_export_options()
            
            dialog = tk.Toplevel(self.window)
            dialog.title("Export Data")
            dialog.geometry("400x300")
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
            
            for export_type, description in export_options.items():
                btn = tk.Button(dialog, text=description, 
                              command=lambda t=export_type: self._export_and_close(t, dialog),
                              bg=Colors.BUTTON_INFO, fg='white', relief=tk.FLAT, 
                              wraplength=300, justify=tk.LEFT)
                btn.pack(pady=5, padx=20, fill=tk.X)
            
            tk.Button(dialog, text="Cancel", command=dialog.destroy,
                     bg=Colors.BUTTON_NEUTRAL, fg='white', relief=tk.FLAT).pack(pady=10)
    
    def _export_and_close(self, export_type, dialog):
        """Helper method to export data and close dialog."""
        dialog.destroy()
        self.data_exporter.export_by_type(export_type, self.window)
    
    def close_window(self):
        """Handle window closing with cleanup."""
        if hasattr(self, 'chart_generator'):
            self.chart_generator.cleanup_chart()
        
        if hasattr(self, 'stats_table'):
            self.stats_table.cleanup()
        
        if hasattr(self, 'prompt_analyzer_ui'):
            self.prompt_analyzer_ui.cleanup()
        
        self.cleanup_preview_resources()
        
        if self.window:
            self.window.destroy()
            self.window = None