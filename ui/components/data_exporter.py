"""
Data exporter component for the Image Ranking System.

This module handles exporting various types of data from the system,
including word analysis, image statistics, and rankings.
"""

import csv
from tkinter import filedialog, messagebox
from typing import Dict, List, Any, Optional


class DataExporter:
    """
    Handles data export functionality for the statistics system.
    
    This component provides various export options for different
    types of data from the ranking system.
    """
    
    def __init__(self, data_manager, prompt_analyzer, ranking_algorithm):
        """
        Initialize the data exporter.
        
        Args:
            data_manager: DataManager instance
            prompt_analyzer: PromptAnalyzer instance
            ranking_algorithm: RankingAlgorithm instance
        """
        self.data_manager = data_manager
        self.prompt_analyzer = prompt_analyzer
        self.ranking_algorithm = ranking_algorithm
    
    def export_word_analysis(self, parent_window=None) -> bool:
        """
        Export word analysis data to CSV file.
        
        Args:
            parent_window: Parent window for dialog
            
        Returns:
            True if export successful, False otherwise
        """
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
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'Word', 'Frequency', 'Average Tier', 'Std Deviation', 
                    'Min Tier', 'Max Tier', 'Is Rare', 'Example Images'
                ])
                
                # Sort by average tier (descending)
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
                        "; ".join(example_images[:5])  # Include up to 5 examples
                    ])
            
            messagebox.showinfo("Export Complete", f"Word analysis exported to {filename}")
            return True
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export word analysis: {e}")
            return False
    
    def export_image_statistics(self, parent_window=None) -> bool:
        """
        Export image statistics to CSV file.
        
        Args:
            parent_window: Parent window for dialog
            
        Returns:
            True if export successful, False otherwise
        """
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
                
                # Write header
                writer.writerow([
                    'Image Name', 'Current Tier', 'Total Votes', 'Wins', 'Losses', 
                    'Win Rate', 'Stability', 'Last Voted', 'Has Prompt', 'Prompt Preview'
                ])
                
                # Get all images and their stats
                all_images = []
                for img_name, stats in self.data_manager.image_stats.items():
                    votes = stats.get('votes', 0)
                    wins = stats.get('wins', 0)
                    losses = stats.get('losses', 0)
                    win_rate = (wins / votes) if votes > 0 else 0
                    stability = self.ranking_algorithm._calculate_tier_stability(img_name)
                    last_voted = stats.get('last_voted', -1)
                    
                    # Format last voted
                    if last_voted == -1:
                        last_voted_str = "Never"
                    else:
                        votes_ago = self.data_manager.vote_count - last_voted
                        last_voted_str = f"{votes_ago} votes ago" if votes_ago > 0 else "Current"
                    
                    # Get prompt info
                    prompt = stats.get('prompt', '')
                    has_prompt = bool(prompt)
                    prompt_preview = ""
                    
                    if prompt:
                        main_prompt = self.prompt_analyzer.extract_main_prompt(prompt)
                        prompt_preview = main_prompt[:200] + "..." if len(main_prompt) > 200 else main_prompt
                    
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
                
                # Sort by current tier (descending)
                all_images.sort(key=lambda x: x[1], reverse=True)
                
                # Write data
                for img_data in all_images:
                    writer.writerow(img_data)
            
            messagebox.showinfo("Export Complete", f"Image statistics exported to {filename}")
            return True
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export image statistics: {e}")
            return False
    
    def export_tier_distribution(self, parent_window=None) -> bool:
        """
        Export tier distribution data to CSV file.
        
        Args:
            parent_window: Parent window for dialog
            
        Returns:
            True if export successful, False otherwise
        """
        filename = filedialog.asksaveasfilename(
            parent=parent_window,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Tier Distribution"
        )
        
        if not filename:
            return False
        
        try:
            tier_distribution = self.data_manager.get_tier_distribution()
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(['Tier', 'Image Count', 'Percentage'])
                
                # Calculate total for percentages
                total_images = sum(tier_distribution.values())
                
                # Sort by tier
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
        """
        Export a comprehensive ranking summary to CSV file.
        
        Args:
            parent_window: Parent window for dialog
            
        Returns:
            True if export successful, False otherwise
        """
        filename = filedialog.asksaveasfilename(
            parent=parent_window,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Ranking Summary"
        )
        
        if not filename:
            return False
        
        try:
            # Get comprehensive rankings
            rankings = self.ranking_algorithm.calculate_all_rankings()
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write overall statistics header
                overall_stats = self.data_manager.get_overall_statistics()
                writer.writerow(['=== OVERALL STATISTICS ==='])
                writer.writerow(['Total Images', overall_stats['total_images']])
                writer.writerow(['Total Votes', overall_stats['total_votes']])
                writer.writerow(['Average Votes per Image', f"{overall_stats['avg_votes_per_image']:.1f}"])
                writer.writerow([])  # Empty row
                
                # Write tier distribution
                writer.writerow(['=== TIER DISTRIBUTION ==='])
                writer.writerow(['Tier', 'Image Count'])
                tier_distribution = overall_stats['tier_distribution']
                for tier in sorted(tier_distribution.keys()):
                    count = tier_distribution[tier]
                    writer.writerow([f"{tier:+d}" if tier != 0 else "0", count])
                writer.writerow([])  # Empty row
                
                # Write top images by tier
                writer.writerow(['=== TOP IMAGES BY TIER ==='])
                writer.writerow(['Rank', 'Image Name', 'Tier', 'Votes', 'Win Rate', 'Stability'])
                
                tier_ranking = rankings['current_tier']
                for rank, (img_name, metrics) in enumerate(tier_ranking[:50], 1):  # Top 50
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
        """
        Get example images that contain a specific word.
        
        Args:
            word: Word to search for
            
        Returns:
            List of image filenames containing the word
        """
        example_images = []
        word_lower = word.lower()
        
        for image_name, stats in self.data_manager.image_stats.items():
            prompt = stats.get('prompt', '')
            if prompt:
                main_prompt = self.prompt_analyzer.extract_main_prompt(prompt)
                words = self.prompt_analyzer.extract_words(main_prompt)
                if word_lower in words:
                    example_images.append(image_name)
                    if len(example_images) >= 10:  # Limit for performance
                        break
        
        return example_images
    
    def get_export_options(self) -> Dict[str, str]:
        """
        Get available export options.
        
        Returns:
            Dictionary mapping export type to description
        """
        return {
            'word_analysis': 'Export word analysis data (words, frequencies, tiers)',
            'image_statistics': 'Export individual image statistics',
            'tier_distribution': 'Export tier distribution summary',
            'ranking_summary': 'Export comprehensive ranking summary'
        }
    
    def export_by_type(self, export_type: str, parent_window=None) -> bool:
        """
        Export data by type.
        
        Args:
            export_type: Type of export ('word_analysis', 'image_statistics', etc.)
            parent_window: Parent window for dialog
            
        Returns:
            True if export successful, False otherwise
        """
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
