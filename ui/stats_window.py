"""Modern statistics window for the Image Ranking System."""

import tkinter as tk
from tkinter import ttk
import os

from config import Colors, Fonts, Styling
from ui.mixins import ImagePreviewMixin
from ui.components.chart_generator import ChartGenerator
from ui.components.data_exporter import DataExporter
from ui.components.prompt_analyzer_ui import PromptAnalyzerUI
from ui.components.stats_table import StatsTable
from ui.components.ui_builder import ModernFrame, ModernButton, ModernLabel


class ModernStatsWindow(ImagePreviewMixin):
    """Modern statistics window with sleek design and enhanced functionality."""
    
    def __init__(self, parent: tk.Tk, data_manager, ranking_algorithm, prompt_analyzer):
        ImagePreviewMixin.__init__(self)
        
        self.parent = parent
        self.data_manager = data_manager
        self.ranking_algorithm = ranking_algorithm
        self.prompt_analyzer = prompt_analyzer
        self.window = None
        self.notebook = None
        
        # Initialize components
        self.chart_generator = ChartGenerator(data_manager)
        self.data_exporter = DataExporter(data_manager, prompt_analyzer, ranking_algorithm)
        self.stats_table = StatsTable(data_manager, ranking_algorithm, prompt_analyzer)
        self.prompt_analyzer_ui = PromptAnalyzerUI(data_manager, prompt_analyzer)
    
    def show(self):
        """Show the modern statistics window."""
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
        """Create the modern statistics window."""
        from core.image_processor import ImageProcessor
        self.image_processor = ImageProcessor()
        
        # Create modern window
        self.window = tk.Toplevel(self.parent)
        self.window.title("📊 Statistics & Analytics")
        self.window.geometry("1600x1000")
        self.window.minsize(1200, 700)
        self.window.configure(bg=Colors.BG_PRIMARY)
        
        # Window icon and properties
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        self.setup_preview_resize_handling()
        
        # Main container
        main_container = ModernFrame(self.window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        # Header
        self._create_modern_header(main_container)
        
        # Content layout
        content_frame = ModernFrame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(Styling.PADDING_LARGE, 0))
        
        content_frame.grid_columnconfigure(0, weight=2, minsize=800)
        content_frame.grid_columnconfigure(1, weight=1, minsize=500)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Left side - tabbed interface
        self._create_tabbed_interface(content_frame)
        
        # Right side - image preview
        self._create_modern_preview(content_frame)
    
    def _create_modern_header(self, parent):
        """Create modern header with statistics summary."""
        header_frame = ModernFrame(parent, style='card')
        header_frame.pack(fill=tk.X, pady=(0, Styling.PADDING_LARGE))
        
        # Header content
        header_content = ModernFrame(header_frame)
        header_content.pack(fill=tk.X, padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        # Title and icon
        title_frame = ModernFrame(header_content)
        title_frame.pack(fill=tk.X, pady=(0, Styling.PADDING_MEDIUM))
        
        icon_label = ModernLabel(title_frame, 
                                text="📊", 
                                font=Fonts.DISPLAY,
                                fg=Colors.PURPLE_PRIMARY)
        icon_label.pack(side=tk.LEFT)
        
        title_label = ModernLabel(title_frame,
                                 text="Statistics & Analytics",
                                 font=Fonts.TITLE,
                                 fg=Colors.TEXT_PRIMARY)
        title_label.pack(side=tk.LEFT, padx=(Styling.PADDING_MEDIUM, 0))
        
        # Statistics summary
        stats_frame = ModernFrame(header_content)
        stats_frame.pack(fill=tk.X)
        
        overall_stats = self.data_manager.get_overall_statistics()
        
        # Create stat cards
        stat_configs = [
            ("Total Images", str(overall_stats['total_images']), "📸"),
            ("Total Votes", str(overall_stats['total_votes']), "🗳️"),
            ("Avg Votes/Image", f"{overall_stats['avg_votes_per_image']:.1f}", "📊"),
            ("Unique Tiers", str(len(overall_stats['tier_distribution'])), "🎯")
        ]
        
        for i, (label, value, icon) in enumerate(stat_configs):
            self._create_stat_card(stats_frame, label, value, icon, i)
        
        # Export button
        export_btn = ModernButton(header_content,
                                 text="📤 Export Data",
                                 command=self.export_all_data,
                                 style='secondary')
        export_btn.pack(side=tk.RIGHT, padx=(Styling.PADDING_MEDIUM, 0))
    
    def _create_stat_card(self, parent, label, value, icon, index):
        """Create a modern stat card."""
        card = ModernFrame(parent, style='card')
        card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0 if index == 0 else Styling.PADDING_SMALL, 0))
        
        card_content = ModernFrame(card)
        card_content.pack(padx=Styling.PADDING_MEDIUM, pady=Styling.PADDING_MEDIUM)
        
        # Icon and value
        icon_label = ModernLabel(card_content, text=icon, font=Fonts.LARGE)
        icon_label.pack()
        
        value_label = ModernLabel(card_content,
                                 text=value,
                                 font=Fonts.HEADING,
                                 fg=Colors.PURPLE_PRIMARY)
        value_label.pack()
        
        label_label = ModernLabel(card_content,
                                 text=label,
                                 font=Fonts.SMALL,
                                 style='secondary')
        label_label.pack()
    
    def _create_tabbed_interface(self, parent):
        """Create modern tabbed interface for statistics."""
        tab_frame = ModernFrame(parent)
        tab_frame.grid(row=0, column=0, sticky="nsew", padx=(0, Styling.PADDING_MEDIUM))
        
        # Create notebook
        self.notebook = ttk.Notebook(tab_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_main_stats_tab(self.notebook)
        
        # Add prompt analysis tab if data exists
        prompt_count = sum(1 for stats in self.data_manager.image_stats.values() 
                          if stats.get('prompt'))
        if prompt_count > 0:
            self.create_prompt_analysis_tab(self.notebook)
    
    def _create_modern_preview(self, parent):
        """Create modern image preview area."""
        preview_container = ModernFrame(parent, style='card')
        preview_container.grid(row=0, column=1, sticky="nsew")
        
        # Preview header
        preview_header = ModernFrame(preview_container)
        preview_header.pack(fill=tk.X, padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        header_icon = ModernLabel(preview_header,
                                 text="🖼️",
                                 font=Fonts.LARGE,
                                 fg=Colors.PURPLE_PRIMARY)
        header_icon.pack(side=tk.LEFT)
        
        header_title = ModernLabel(preview_header,
                                  text="Image Preview",
                                  font=Fonts.HEADING,
                                  fg=Colors.TEXT_PRIMARY)
        header_title.pack(side=tk.LEFT, padx=(Styling.PADDING_MEDIUM, 0))
        
        # Preview content
        preview_content = ModernFrame(preview_container)
        preview_content.pack(fill=tk.BOTH, expand=True, padx=Styling.PADDING_LARGE, pady=(0, Styling.PADDING_LARGE))
        
        # Create preview area
        self.create_image_preview_area(preview_content, include_additional_stats=True)
    
    def create_main_stats_tab(self, notebook: ttk.Notebook):
        """Create the main statistics tab with modern styling."""
        frame = ModernFrame(notebook)
        notebook.add(frame, text="📊 Image Statistics")
        
        # Content container
        content_frame = ModernFrame(frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        # Chart section
        chart_section = ModernFrame(content_frame, style='card')
        chart_section.pack(fill=tk.X, pady=(0, Styling.PADDING_LARGE))
        
        # Chart header
        chart_header = ModernFrame(chart_section)
        chart_header.pack(fill=tk.X, padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        chart_title = ModernLabel(chart_header,
                                 text="📈 Tier Distribution",
                                 font=Fonts.HEADING,
                                 fg=Colors.PURPLE_PRIMARY)
        chart_title.pack(side=tk.LEFT)
        
        # Chart content
        chart_content = ModernFrame(chart_section)
        chart_content.pack(fill=tk.X, padx=Styling.PADDING_LARGE, pady=(0, Styling.PADDING_LARGE))
        
        self.chart_generator.create_tier_distribution_chart(chart_content)
        
        # Table section
        table_section = ModernFrame(content_frame, style='card')
        table_section.pack(fill=tk.BOTH, expand=True)
        
        # Table header
        table_header = ModernFrame(table_section)
        table_header.pack(fill=tk.X, padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        table_title = ModernLabel(table_header,
                                 text="📋 Individual Statistics",
                                 font=Fonts.HEADING,
                                 fg=Colors.PURPLE_PRIMARY)
        table_title.pack(side=tk.LEFT)
        
        # Instructions
        instructions = ModernLabel(table_header,
                                  text="💡 Click columns to sort • Hover rows for preview",
                                  font=Fonts.SMALL,
                                  style='secondary')
        instructions.pack(side=tk.RIGHT)
        
        # Table content
        table_content = ModernFrame(table_section)
        table_content.pack(fill=tk.BOTH, expand=True, padx=Styling.PADDING_LARGE, pady=(0, Styling.PADDING_LARGE))
        
        self.stats_table.create_stats_table(table_content)
        
        # Set up hover callbacks
        self.stats_table.set_hover_callback(self.display_preview_image)
        self.stats_table.set_leave_callback(lambda: None)
    
    def create_prompt_analysis_tab(self, notebook: ttk.Notebook):
        """Create the prompt analysis tab with modern styling."""
        frame = ModernFrame(notebook)
        notebook.add(frame, text="🔍 Prompt Analysis")
        
        # Content container
        content_frame = ModernFrame(frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        # Analysis section
        analysis_section = ModernFrame(content_frame, style='card')
        analysis_section.pack(fill=tk.BOTH, expand=True)
        
        # Analysis header
        analysis_header = ModernFrame(analysis_section)
        analysis_header.pack(fill=tk.X, padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        analysis_title = ModernLabel(analysis_header,
                                    text="🧠 Word Performance Analysis",
                                    font=Fonts.HEADING,
                                    fg=Colors.PURPLE_PRIMARY)
        analysis_title.pack(side=tk.LEFT)
        
        # Export button for word analysis
        export_btn = ModernButton(analysis_header,
                                 text="📤 Export Words",
                                 command=self.export_word_analysis,
                                 style='secondary')
        export_btn.pack(side=tk.RIGHT)
        
        # Analysis content
        analysis_content = ModernFrame(analysis_section)
        analysis_content.pack(fill=tk.BOTH, expand=True, padx=Styling.PADDING_LARGE, pady=(0, Styling.PADDING_LARGE))
        
        self.prompt_analyzer_ui.create_prompt_analysis_tab(analysis_content)
        
        # Set up hover callbacks
        self.prompt_analyzer_ui.set_hover_callback(self.display_preview_image)
        self.prompt_analyzer_ui.set_leave_callback(lambda: None)
        self.prompt_analyzer_ui.set_export_callback(self.export_word_analysis)
    
    def export_word_analysis(self):
        """Export word analysis with modern dialog."""
        self.data_exporter.export_word_analysis(self.window)
    
    def export_all_data(self):
        """Export all available data with modern interface."""
        if hasattr(self, 'data_exporter'):
            export_options = self.data_exporter.get_export_options()
            
            # Create modern export dialog
            dialog = tk.Toplevel(self.window)
            dialog.title("📤 Export Data")
            dialog.geometry("500x400")
            dialog.configure(bg=Colors.BG_PRIMARY)
            dialog.resizable(False, False)
            dialog.transient(self.window)
            dialog.grab_set()
            
            # Center dialog
            dialog.geometry("+%d+%d" % (
                self.window.winfo_rootx() + 200,
                self.window.winfo_rooty() + 200
            ))
            
            # Dialog content
            content = ModernFrame(dialog, style='card')
            content.pack(fill=tk.BOTH, expand=True, padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
            
            # Header
            header = ModernFrame(content)
            header.pack(fill=tk.X, pady=(0, Styling.PADDING_LARGE))
            
            icon = ModernLabel(header, text="📤", font=Fonts.DISPLAY, fg=Colors.PURPLE_PRIMARY)
            icon.pack(side=tk.LEFT)
            
            title = ModernLabel(header, text="Export Data", font=Fonts.TITLE, fg=Colors.TEXT_PRIMARY)
            title.pack(side=tk.LEFT, padx=(Styling.PADDING_MEDIUM, 0))
            
            # Export options
            options_frame = ModernFrame(content)
            options_frame.pack(fill=tk.BOTH, expand=True, pady=(0, Styling.PADDING_LARGE))
            
            for export_type, description in export_options.items():
                option_frame = ModernFrame(options_frame, style='card')
                option_frame.pack(fill=tk.X, pady=(0, Styling.PADDING_SMALL))
                
                btn = ModernButton(option_frame,
                                  text=description,
                                  command=lambda t=export_type: self._export_and_close(t, dialog),
                                  style='secondary')
                btn.pack(fill=tk.X, padx=Styling.PADDING_MEDIUM, pady=Styling.PADDING_MEDIUM)
            
            # Cancel button
            cancel_btn = ModernButton(content,
                                     text="Cancel",
                                     command=dialog.destroy,
                                     style='ghost')
            cancel_btn.pack(pady=(Styling.PADDING_MEDIUM, 0))
    
    def _export_and_close(self, export_type, dialog):
        """Helper method to export data and close dialog."""
        dialog.destroy()
        self.data_exporter.export_by_type(export_type, self.window)
    
    def refresh_stats(self):
        """Refresh all statistics displays."""
        if hasattr(self, 'stats_table'):
            self.stats_table.refresh_table()
        
        if hasattr(self, 'chart_generator'):
            # Find and refresh charts
            for widget in self.window.winfo_children():
                self._refresh_charts_recursive(widget)
        
        if hasattr(self, 'prompt_analyzer_ui'):
            self.prompt_analyzer_ui.refresh_analysis()
    
    def _refresh_charts_recursive(self, widget):
        """Recursively find and refresh charts."""
        try:
            if hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Frame):
                        try:
                            self.chart_generator.refresh_chart(child)
                        except:
                            pass
                    self._refresh_charts_recursive(child)
        except:
            pass
    
    def get_stats_summary(self):
        """Get a comprehensive summary of current statistics."""
        summary = {
            'overall_stats': self.data_manager.get_overall_statistics(),
            'chart_data': self.chart_generator.get_chart_data_summary() if hasattr(self, 'chart_generator') else {},
            'table_stats': self.stats_table.get_table_stats() if hasattr(self, 'stats_table') else {},
            'prompt_analysis': self.prompt_analyzer_ui.get_analysis_summary() if hasattr(self, 'prompt_analyzer_ui') else {}
        }
        return summary
    
    def close_window(self):
        """Handle window closing with modern cleanup."""
        # Cleanup chart resources
        if hasattr(self, 'chart_generator'):
            self.chart_generator.cleanup_chart()
        
        # Cleanup table resources
        if hasattr(self, 'stats_table'):
            self.stats_table.cleanup()
        
        # Cleanup prompt analysis resources
        if hasattr(self, 'prompt_analyzer_ui'):
            self.prompt_analyzer_ui.cleanup()
        
        # Cleanup preview resources
        self.cleanup_preview_resources()
        
        # Close window
        if self.window:
            self.window.destroy()
            self.window = None


# For backward compatibility
class StatsWindow(ModernStatsWindow):
    """Backward compatibility alias for the modern stats window."""
    pass
