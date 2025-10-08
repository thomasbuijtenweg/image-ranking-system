"""Data exporter for the Image Ranking System with word combination analysis support."""

import csv
import os
from tkinter import filedialog, messagebox
from typing import Dict, List, Any, Optional


class DataExporter:
    """Handles data export functionality for the statistics system including word combinations."""
    
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
                    'Word', 'Active Frequency', 'Binned Frequency', 'Total Frequency',
                    'Average Tier', 'Std Deviation', 'Binning Rate', 'Quality Indicator',
                    'Min Tier', 'Max Tier', 'Is Rare', 'Example Images'
                ])
                
                sorted_words = sorted(word_analysis.items(), 
                                    key=lambda x: x[1]['average_tier'], reverse=True)
                
                for word, data in sorted_words:
                    active_tiers = data.get('active_tiers', [])
                    min_tier = min(active_tiers) if active_tiers else 0
                    max_tier = max(active_tiers) if active_tiers else 0
                    example_images = self._get_example_images_for_word(word)
                    
                    writer.writerow([
                        word,
                        data.get('active_frequency', 0),
                        data.get('binned_frequency', 0),
                        data.get('total_frequency', 0),
                        f"{data.get('average_tier', 0):.3f}",
                        f"{data.get('std_deviation', 0):.3f}",
                        f"{data.get('binning_rate', 0):.3f}",
                        f"{data.get('quality_indicator', 0):.3f}",
                        min_tier,
                        max_tier,
                        data.get('is_rare', False),
                        "; ".join(example_images[:5])
                    ])
            
            messagebox.showinfo("Export Complete", f"Word analysis exported to {filename}")
            return True
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export word analysis: {e}")
            return False
    
    def export_combination_analysis(self, parent_window=None, min_frequency: int = 3) -> bool:
        """Export word combination analysis data to CSV file."""
        if not self._has_prompt_data():
            messagebox.showinfo("No Data", "No prompt data available for combination analysis.")
            return False
        
        filename = filedialog.asksaveasfilename(
            parent=parent_window,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Word Combination Analysis"
        )
        
        if not filename:
            return False
        
        try:
            combination_analysis = self.prompt_analyzer.analyze_word_combinations(min_frequency)
            
            if not combination_analysis:
                messagebox.showinfo("No Data", f"No word combination data available with minimum frequency of {min_frequency}.")
                return False
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'Word 1', 'Word 2', 'Pair Frequency', 'Actual Performance', 'Expected Performance',
                    'Synergy Score', 'Synergy Type', 'Confidence', 'Std Deviation',
                    'Word 1 Individual Perf', 'Word 2 Individual Perf',
                    'Word 1 Frequency', 'Word 2 Frequency', 'Example Images'
                ])
                
                # Sort by synergy score (strongest synergy first)
                sorted_combinations = sorted(combination_analysis.items(), 
                                           key=lambda x: x[1]['synergy_score'], reverse=True)
                
                for pair, data in sorted_combinations:
                    # Get example images for this pair
                    example_images = self.prompt_analyzer.get_combination_examples(
                        data['word1'], data['word2'], max_examples=3)
                    example_text = "; ".join(example_images) if example_images else "No examples found"
                    
                    writer.writerow([
                        data['word1'],
                        data['word2'],
                        data['pair_frequency'],
                        f"{data['actual_performance']:.3f}",
                        f"{data['expected_performance']:.3f}",
                        f"{data['synergy_score']:+.3f}",
                        data['synergy_type'],
                        f"{data['confidence']:.3f}",
                        f"{data['std_deviation']:.3f}",
                        f"{data['word1_individual_perf']:.3f}",
                        f"{data['word2_individual_perf']:.3f}",
                        data['word1_frequency'],
                        data['word2_frequency'],
                        example_text
                    ])
            
            messagebox.showinfo("Export Complete", 
                              f"Word combination analysis exported to {filename}\n\n"
                              f"Exported {len(sorted_combinations)} word pairs with minimum frequency {min_frequency}")
            return True
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export combination analysis: {e}")
            return False
    
    def export_top_synergies_and_antagonisms(self, parent_window=None) -> bool:
        """Export a focused report on the top synergistic and antagonistic word pairs."""
        if not self._has_prompt_data():
            messagebox.showinfo("No Data", "No prompt data available for combination analysis.")
            return False
        
        filename = filedialog.asksaveasfilename(
            parent=parent_window,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Top Synergies & Antagonisms"
        )
        
        if not filename:
            return False
        
        try:
            # Get top synergistic and antagonistic pairs
            top_synergistic = self.prompt_analyzer.get_top_synergistic_pairs(count=15)
            top_antagonistic = self.prompt_analyzer.get_top_antagonistic_pairs(count=15)
            
            if not top_synergistic and not top_antagonistic:
                messagebox.showinfo("No Data", "No significant word pair effects found.")
                return False
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Summary header
                writer.writerow(['Word Combination Effects Summary'])
                writer.writerow(['Generated by Image Ranking System'])
                writer.writerow([])
                
                # Top synergistic pairs
                if top_synergistic:
                    writer.writerow(['=== TOP SYNERGISTIC PAIRS ==='])
                    writer.writerow(['Word 1', 'Word 2', 'Synergy Score', 'Frequency', 'Confidence', 'Example Images'])
                    
                    for pair, data in top_synergistic:
                        examples = self.prompt_analyzer.get_combination_examples(
                            data['word1'], data['word2'], max_examples=2)
                        example_text = ", ".join(examples) if examples else "No examples"
                        
                        writer.writerow([
                            data['word1'],
                            data['word2'],
                            f"{data['synergy_score']:+.3f}",
                            data['pair_frequency'],
                            f"{data['confidence']:.3f}",
                            example_text
                        ])
                    
                    writer.writerow([])
                
                # Top antagonistic pairs
                if top_antagonistic:
                    writer.writerow(['=== TOP ANTAGONISTIC PAIRS ==='])
                    writer.writerow(['Word 1', 'Word 2', 'Antagonism Score', 'Frequency', 'Confidence', 'Example Images'])
                    
                    for pair, data in top_antagonistic:
                        examples = self.prompt_analyzer.get_combination_examples(
                            data['word1'], data['word2'], max_examples=2)
                        example_text = ", ".join(examples) if examples else "No examples"
                        
                        writer.writerow([
                            data['word1'],
                            data['word2'],
                            f"{data['synergy_score']:+.3f}",
                            data['pair_frequency'],
                            f"{data['confidence']:.3f}",
                            example_text
                        ])
                
                # Summary statistics
                writer.writerow([])
                writer.writerow(['=== SUMMARY STATISTICS ==='])
                summary = self.prompt_analyzer.get_combination_summary()
                
                if 'error' not in summary:
                    writer.writerow(['Total Combinations Analyzed', summary['total_combinations']])
                    writer.writerow(['Synergistic Pairs', summary['synergistic_count']])
                    writer.writerow(['Antagonistic Pairs', summary['antagonistic_count']])
                    writer.writerow(['Neutral Pairs', summary['neutral_count']])
                    writer.writerow(['Average Synergy Score', f"{summary['avg_synergy_score']:.3f}"])
                    
                    if summary.get('strongest_synergy'):
                        strongest_pair, strongest_data = summary['strongest_synergy']
                        writer.writerow(['Strongest Synergy', 
                                       f"{strongest_data['word1']} + {strongest_data['word2']} ({strongest_data['synergy_score']:+.3f})"])
                    
                    if summary.get('strongest_antagonism'):
                        strongest_pair, strongest_data = summary['strongest_antagonism']
                        writer.writerow(['Strongest Antagonism', 
                                       f"{strongest_data['word1']} + {strongest_data['word2']} ({strongest_data['synergy_score']:+.3f})"])
            
            messagebox.showinfo("Export Complete", 
                              f"Top synergies and antagonisms exported to {filename}\n\n"
                              f"Included {len(top_synergistic)} synergistic and {len(top_antagonistic)} antagonistic pairs")
            return True
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export synergies and antagonisms: {e}")
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
                    'Image Name', 'Status', 'Current Tier', 'Total Votes', 'Wins', 'Losses', 
                    'Win Rate', 'Stability', 'Last Voted', 'Has Prompt', 'Prompt Preview'
                ])
                
                all_images = []
                for img_name, stats in self.data_manager.image_stats.items():
                    votes = stats.get('votes', 0)
                    wins = stats.get('wins', 0)
                    losses = stats.get('losses', 0)
                    win_rate = (wins / votes) if votes > 0 else 0
                    
                    # Determine status
                    status = "BINNED" if self.data_manager.is_image_binned(img_name) else "ACTIVE"
                    
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
                        status,
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
                
                all_images.sort(key=lambda x: x[2], reverse=True)
                
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
                writer.writerow(['Total Active Images', overall_stats.get('total_active_images', 0)])
                writer.writerow(['Total Binned Images', overall_stats.get('total_binned_images', 0)])
                writer.writerow(['Total Votes', overall_stats['total_votes']])
                writer.writerow(['Average Votes per Active Image', f"{overall_stats.get('avg_votes_per_active_image', 0):.1f}"])
                writer.writerow([])
                
                writer.writerow(['=== TIER DISTRIBUTION ==='])
                writer.writerow(['Tier', 'Image Count'])
                tier_distribution = overall_stats['tier_distribution']
                for tier in sorted(tier_distribution.keys()):
                    count = tier_distribution[tier]
                    writer.writerow([f"{tier:+d}" if tier != 0 else "0", count])
                writer.writerow([])
                
                writer.writerow(['=== TOP IMAGES BY TIER ==='])
                writer.writerow(['Rank', 'Image Name', 'Status', 'Tier', 'Votes', 'Win Rate', 'Stability'])
                
                tier_ranking = rankings['current_tier']
                for rank, (img_name, metrics) in enumerate(tier_ranking[:50], 1):
                    status = "BINNED" if self.data_manager.is_image_binned(img_name) else "ACTIVE"
                    writer.writerow([
                        rank,
                        img_name,
                        status,
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
        """Get available export options including combination analysis."""
        options = {
            'image_statistics': 'Export individual image statistics',
            'tier_distribution': 'Export tier distribution summary',
            'ranking_summary': 'Export comprehensive ranking summary'
        }
        
        if self._has_prompt_data():
            options['word_analysis'] = 'Export individual word analysis data'
            options['combination_analysis'] = 'Export word combination analysis (synergies & antagonisms)'
            options['top_effects'] = 'Export top synergistic and antagonistic pairs (focused report)'
        
        return options
    
    def export_by_type(self, export_type: str, parent_window=None) -> bool:
        """Export data by type including combination analysis."""
        try:
            if export_type == 'word_analysis':
                return self.export_word_analysis(parent_window)
            elif export_type == 'combination_analysis':
                return self.export_combination_analysis(parent_window)
            elif export_type == 'top_effects':
                return self.export_top_synergies_and_antagonisms(parent_window)
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
        """Get list of available export types including combination analysis."""
        return list(self.get_export_options().keys())
    
    def validate_export_data(self, export_type: str) -> bool:
        """Validate that data exists for the specified export type."""
        if export_type in ['word_analysis', 'combination_analysis', 'top_effects']:
            return self._has_prompt_data()
        elif export_type in ['image_statistics', 'tier_distribution', 'ranking_summary']:
            return bool(self.data_manager.image_stats)
        else:
            return False
