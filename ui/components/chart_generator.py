"""Chart generator for the Image Ranking System."""

import math
import tkinter as tk
from typing import Dict, Any

try:
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available. Chart functionality will be limited.")

from config import Colors


class ChartGenerator:
    """Handles chart generation for the statistics window."""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.chart_figure = None
        self.chart_canvas = None
        self.chart_widget = None
    
    def create_tier_distribution_chart(self, parent_frame):
        """Create a bar chart showing tier distribution with normal distribution overlay."""
        if not MATPLOTLIB_AVAILABLE:
            placeholder_label = tk.Label(parent_frame, 
                                        text="Chart functionality requires matplotlib\nRun: pip install matplotlib", 
                                        font=('Arial', 10, 'italic'), 
                                        fg=Colors.TEXT_ERROR, bg=Colors.BG_SECONDARY)
            placeholder_label.pack(pady=10)
            return placeholder_label
        
        tier_distribution = self.data_manager.get_tier_distribution()
        total_images = len(self.data_manager.image_stats)
        
        if not tier_distribution or total_images == 0:
            placeholder_label = tk.Label(parent_frame, text="No tier distribution data available", 
                                       font=('Arial', 10, 'italic'), 
                                       fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY)
            placeholder_label.pack(pady=10)
            return placeholder_label
        
        self.cleanup_chart()
        
        try:
            self.chart_figure = Figure(figsize=(10, 4), dpi=100, facecolor='#2d2d2d')
            ax = self.chart_figure.add_subplot(111)
            ax.set_facecolor('#2d2d2d')
            
            min_tier = min(tier_distribution.keys())
            max_tier = max(tier_distribution.keys())
            
            tier_range = list(range(min_tier, max_tier + 1))
            actual_counts = [tier_distribution.get(tier, 0) for tier in tier_range]
            
            bars = ax.bar(tier_range, actual_counts, alpha=0.7, color='#4CAF50', 
                         edgecolor='#66ff66', linewidth=1, label='Actual Distribution')
            
            # Calculate normal distribution curve
            std_dev = getattr(self.data_manager, 'tier_distribution_std', 1.5)
            
            curve_x = np.linspace(min_tier - 1, max_tier + 1, 100)
            curve_y = []
            
            for x in curve_x:
                density = math.exp(-(x ** 2) / (2 * std_dev ** 2))
                curve_y.append(density)
            
            if curve_y:
                total_density = sum(math.exp(-(t ** 2) / (2 * std_dev ** 2)) for t in tier_range)
                if total_density > 0:
                    curve_y = [(y / max(curve_y)) * (total_images / len(tier_range)) * 2 for y in curve_y]
            
            ax.plot(curve_x, curve_y, color='#ff6666', linewidth=2, 
                   label=f'Expected Distribution (σ={std_dev:.1f})')
            
            ax.set_xlabel('Tier', color='#ffffff', fontsize=10)
            ax.set_ylabel('Number of Images', color='#ffffff', fontsize=10)
            ax.set_title('Tier Distribution vs Expected Normal Distribution', 
                        color='#ffffff', fontsize=12, fontweight='bold')
            
            ax.tick_params(colors='#ffffff', labelsize=9)
            
            ax.set_xticks(tier_range)
            ax.set_xticklabels([f'{t:+d}' if t != 0 else '0' for t in tier_range])
            
            ax.grid(True, alpha=0.3, color='#666666')
            
            legend = ax.legend(loc='upper right', fancybox=True, shadow=True)
            legend.get_frame().set_facecolor('#3d3d3d')
            for text in legend.get_texts():
                text.set_color('#ffffff')
            
            self.chart_figure.tight_layout()
            
            self.chart_canvas = FigureCanvasTkAgg(self.chart_figure, parent_frame)
            self.chart_canvas.draw()
            self.chart_widget = self.chart_canvas.get_tk_widget()
            self.chart_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            return self.chart_widget
            
        except Exception as e:
            print(f"Error creating chart: {e}")
            error_label = tk.Label(parent_frame, 
                                 text=f"Error creating chart: {str(e)}", 
                                 font=('Arial', 10, 'italic'), 
                                 fg=Colors.TEXT_ERROR, bg=Colors.BG_SECONDARY)
            error_label.pack(pady=10)
            return error_label
    
    def cleanup_chart(self):
        """Clean up chart resources."""
        if self.chart_figure and MATPLOTLIB_AVAILABLE:
            try:
                plt.close(self.chart_figure)
            except:
                pass
            self.chart_figure = None
        
        if self.chart_canvas:
            try:
                self.chart_canvas.get_tk_widget().destroy()
            except:
                pass
            self.chart_canvas = None
        
        if self.chart_widget:
            try:
                self.chart_widget.destroy()
            except:
                pass
            self.chart_widget = None
    
    def refresh_chart(self, parent_frame):
        """Refresh the chart with updated data."""
        for widget in parent_frame.winfo_children():
            try:
                widget.destroy()
            except:
                pass
        
        return self.create_tier_distribution_chart(parent_frame)
    
    def get_chart_data_summary(self):
        """Get a summary of the chart data."""
        tier_distribution = self.data_manager.get_tier_distribution()
        total_images = len(self.data_manager.image_stats)
        
        if not tier_distribution:
            return {
                'total_images': 0,
                'tier_count': 0,
                'min_tier': 0,
                'max_tier': 0,
                'most_populated_tier': 0,
                'most_populated_count': 0,
                'matplotlib_available': MATPLOTLIB_AVAILABLE
            }
        
        min_tier = min(tier_distribution.keys())
        max_tier = max(tier_distribution.keys())
        most_populated_tier = max(tier_distribution.keys(), key=tier_distribution.get)
        most_populated_count = tier_distribution[most_populated_tier]
        
        return {
            'total_images': total_images,
            'tier_count': len(tier_distribution),
            'min_tier': min_tier,
            'max_tier': max_tier,
            'most_populated_tier': most_populated_tier,
            'most_populated_count': most_populated_count,
            'matplotlib_available': MATPLOTLIB_AVAILABLE
        }
    
    def is_available(self):
        """Check if chart generation is available."""
        return MATPLOTLIB_AVAILABLE