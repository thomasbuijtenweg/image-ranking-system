"""Data exporter for the Image Ranking System."""

import csv
import os
from tkinter import filedialog, messagebox
from typing import Dict, List, Any, Optional


class DataExporter:
    """Handles data export functionality for the statistics system."""
    
    def __init__(self, data_manager, prompt_analyzer, ranking_algorithm):
        self.data_manager = data_manager
        self.prompt_analyzer = prompt_analyzer
        self.ranking_algorithm = ranking_algorithm
    
    def export_word_analysis(self, parent_window=None) -> bool:
        """Export word analysis data to CSV file."""
        if not self._has_prompt_data():
            messagebox.showinfo("No Data", "No prompt data available for analysis.")
            return False
        
        filename = filedialog.asksaveasfilename(
            parent=parent_window,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Word Analysis"
        )
        
        if not filename:
            return False
        
        try:
            word_analysis = self.prompt_analyzer.analyze_word_performance()
            
            if not word_analysis:
                messagebox.showinfo("No Data", "No word analysis data available.")
                return False
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                writer.writerow([
                    'Word', 'Frequency', 'Average Tier', 'Std Deviation', 
                    'Min Tier', 'Max Tier', 'Is Rare', 'Example Images'
                ])
                
                sorted_words = sorted(word_analysis.items(), 
                                    key=lambda x: x[1]['average_tier'], reverse=True)
                
                for word, data in sorted_words:
                    tiers = data['tiers']
                    min_tier = min(tiers) if tiers else 0
                    max_tier = max(tiers) if tiers else 0
                    example_images = self._get_example_images_for_word(word)
                    
                    writer.writerow([
                        word,
                        data['frequency'],
                        f"{data['average_tier']:.3f}",
                        f"{data['std_deviation']:.3f}",
                        min_tier,
                        max_tier,
                        data['is_rare'],
                        "; ".join(example_images[:5])
                    ])
            
            messagebox.showinfo("Export Complete", f"Word analysis exported to {filename}")
            return True
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export word analysis: {e}")
            return False
    
    def export_image_statistics(self, parent_window=None) -> bool:
        """Export image statistics to CSV file."""
        if not self.data_manager.image_stats:
            messagebox.showinfo("No Data", "No image statistics available to export.")
            return False
        
        filename = filedialog.asksaveasfilename(
            parent=parent_window,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Image Statistics"
        )
        
        if not filename:
            return False
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                writer.writerow([
                    'Image Name', 'Current Tier', 'Total Votes', 'Wins', 'Losses', 
                    'Win Rate', 'Stability', 'Last Voted', 'Has Prompt', 'Prompt Preview'
                ])
                
                all_images = []
                for img_name, stats in self.data_manager.image_stats.items():
                    votes = stats.get('votes', 0)
                    wins = stats.get('wins', 0)
                    losses = stats.get('losses', 0)
                    win_rate = (wins / votes) if votes > 0 else 0
                    
                    try:
                        stability = self.ranking_algorithm._calculate_tier_stability(img_name)
                    except:
                        stability = 0.0
                    
                    last_voted = stats.get('last_voted', -1)
                    
                    if last_voted == -1:
                        last_voted_str = "Never"
                    else:
                        votes_ago = self.data_manager.vote_count - last_voted
                        last_voted_str = f"{votes_ago} votes ago" if votes_ago > 0 else "Current"
                    
                    prompt = stats.get('prompt', '')
                    has_prompt = bool(prompt)
                    prompt_preview = ""
                    
                    if prompt:
                        try:
                            main_prompt = self.prompt_analyzer.extract_main_prompt(prompt)
                            prompt_preview = main_prompt[:200] + "..." if len(main_prompt) > 200 else main_prompt
                        except:
                            prompt_preview = "Error extracting prompt"
                    
                    all_images.append([
                        img_name,
                        stats.get('current_tier', 0),
                        votes,
                        wins,
                        losses,
                        f"{win_rate:.3f}",
                        f"{stability:.3f}",
                        last_voted_str,
                        has_prompt,
                        prompt_preview
                    ])
                
                all_images.sort(key=lambda x: x[1], reverse=True)
                
                for img_data in all_images:
                    writer.writerow(img_data)
            
            messagebox.showinfo("Export Complete", f"Image statistics exported to {filename}")
            return True
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export image statistics: {e}")
            return False
    
    def export_tier_distribution(self, parent_window=None) -> bool:
        """Export tier distribution data to CSV file."""
        tier_distribution = self.data_manager.get_tier_distribution()
        
        if not tier_distribution:
            messagebox.showinfo("No Data", "No tier distribution data available to export.")
            return False
        
        filename = filedialog.asksaveasfilename(
            parent=parent_window,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Tier Distribution"
        )
        
        if not filename:
            return False
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                writer.writerow(['Tier', 'Image Count', 'Percentage'])
                
                total_images = sum(tier_distribution.values())
                
                sorted_tiers = sorted(tier_distribution.items())
                
                for tier, count in sorted_tiers:
                    percentage = (count / total_images * 100) if total_images > 0 else 0
                    writer.writerow([
                        f"{tier:+d}" if tier != 0 else "0",
                        count,
                        f"{percentage:.1f}%"
                    ])
            
            messagebox.showinfo("Export Complete", f"Tier distribution exported to {filename}")
            return True
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export tier distribution: {e}")
            return False
    
    def export_ranking_summary(self, parent_window=None) -> bool:
        """Export a comprehensive ranking summary to CSV file."""
        if not self.data_manager.image_stats:
            messagebox.showinfo("No Data", "No ranking data available to export.")
            return False
        
        filename = filedialog.asksaveasfilename(
            parent=parent_window,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Ranking Summary"
        )
        
        if not filename:
            return False
        
        try:
            rankings = self.ranking_algorithm.calculate_all_rankings()
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                overall_stats = self.data_manager.get_overall_statistics()
                writer.writerow(['=== OVERALL STATISTICS ==='])
                writer.writerow(['Total Images', overall_stats['total_images']])
                writer.writerow(['Total Votes', overall_stats['total_votes']])
                writer.writerow(['Average Votes per Image', f"{overall_stats['avg_votes_per_image']:.1f}"])
                writer.writerow([])
                
                writer.writerow(['=== TIER DISTRIBUTION ==='])
                writer.writerow(['Tier', 'Image Count'])
                tier_distribution = overall_stats['tier_distribution']
                for tier in sorted(tier_distribution.keys()):
                    count = tier_distribution[tier]
                    writer.writerow([f"{tier:+d}" if tier != 0 else "0", count])
                writer.writerow([])
                
                writer.writerow(['=== TOP IMAGES BY TIER ==='])
                writer.writerow(['Rank', 'Image Name', 'Tier', 'Votes', 'Win Rate', 'Stability'])
                
                tier_ranking = rankings['current_tier']
                for rank, (img_name, metrics) in enumerate(tier_ranking[:50], 1):
                    writer.writerow([
                        rank,
                        img_name,
                        f"{metrics['current_tier']:+d}" if metrics['current_tier'] != 0 else "0",
                        metrics['total_votes'],
                        f"{metrics['win_rate']:.1%}",
                        f"{metrics['tier_stability']:.2f}"
                    ])
            
            messagebox.showinfo("Export Complete", f"Ranking summary exported to {filename}")
            return True
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export ranking summary: {e}")
            return False
    
    def _get_example_images_for_word(self, word: str) -> List[str]:
        """Get example images that contain a specific word."""
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
                            if len(example_images) >= 10:
                                break
                    except:
                        continue
        except Exception as e:
            print(f"Error getting example images for word '{word}': {e}")
        
        return example_images
    
    def _has_prompt_data(self) -> bool:
        """Check if there is any prompt data available."""
        for stats in self.data_manager.image_stats.values():
            if stats.get('prompt'):
                return True
        return False
    
    def get_export_options(self) -> Dict[str, str]:
        """Get available export options."""
        options = {
            'image_statistics': 'Export individual image statistics',
            'tier_distribution': 'Export tier distribution summary',
            'ranking_summary': 'Export comprehensive ranking summary'
        }
        
        if self._has_prompt_data():
            options['word_analysis'] = 'Export word analysis data (words, frequencies, tiers)'
        
        return options
    
    def export_by_type(self, export_type: str, parent_window=None) -> bool:
        """Export data by type."""
        try:
            if export_type == 'word_analysis':
                return self.export_word_analysis(parent_window)
            elif export_type == 'image_statistics':
                return self.export_image_statistics(parent_window)
            elif export_type == 'tier_distribution':
                return self.export_tier_distribution(parent_window)
            elif export_type == 'ranking_summary':
                return self.export_ranking_summary(parent_window)
            else:
                messagebox.showerror("Export Error", f"Unknown export type: {export_type}")
                return False
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export {export_type}: {e}")
            return False
    
    def get_available_exports(self) -> List[str]:
        """Get list of available export types."""
        return list(self.get_export_options().keys())
    
    def validate_export_data(self, export_type: str) -> bool:
        """Validate that data exists for the specified export type."""
        if export_type == 'word_analysis':
            return self._has_prompt_data()
        elif export_type in ['image_statistics', 'tier_distribution', 'ranking_summary']:
            return bool(self.data_manager.image_stats)
        else:
            return False