"""Main window for the Image Ranking System."""

import tkinter as tk
from tkinter import messagebox, filedialog
import sys
import os

from config import Colors, Defaults, KeyBindings
from core.data_manager import DataManager
from core.image_processor import ImageProcessor
from core.ranking_algorithm import RankingAlgorithm
from core.prompt_analyzer import PromptAnalyzer

from ui.components.image_display import ImageDisplayController
from ui.components.voting_controller import VotingController
from ui.components.metadata_processor import MetadataProcessor
from ui.components.progress_tracker import ProgressTracker
from ui.components.folder_manager import FolderManager
from ui.components.ui_builder import UIBuilder

from ui.stats_window import StatsWindow
from ui.settings_window import SettingsWindow


class MainWindow:
    """Main application window coordinating all components."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        
        # Initialize core components
        self.data_manager = DataManager()
        self.image_processor = ImageProcessor()
        self.ranking_algorithm = RankingAlgorithm(self.data_manager)
        self.prompt_analyzer = PromptAnalyzer(self.data_manager)
        
        # Initialize UI components
        self.ui_builder = UIBuilder(root)
        self.progress_tracker = ProgressTracker(root)
        self.metadata_processor = MetadataProcessor(self.data_manager, self.image_processor)
        self.folder_manager = FolderManager(
            self.data_manager, 
            self.image_processor, 
            self.metadata_processor, 
            self.progress_tracker
        )
        
        self.image_display = None
        self.voting_controller = None
        
        # Window references
        self.stats_window = None
        self.settings_window = None
        
        self._setup_application()
    
    def _setup_application(self) -> None:
        """Setup the complete application."""
        self.ui_builder.setup_window_properties()
        
        ui_refs = self.ui_builder.build_main_ui()
        
        button_callbacks = {
            'select_folder': self.folder_manager.select_folder,
            'save_data': self.save_data,
            'load_data': self.load_data,
            'show_stats': self.show_detailed_stats,
            'show_prompt_analysis': self.show_prompt_analysis,
            'show_settings': self.show_settings
        }
        self.ui_builder.create_control_buttons(ui_refs['top_frame'], button_callbacks)
        
        self.image_display = ImageDisplayController(
            self.root, 
            self.data_manager, 
            self.image_processor, 
            self.prompt_analyzer
        )
        
        self.image_display.create_image_frames(ui_refs['main_frame'])
        self.image_display.set_ranking_algorithm(self.ranking_algorithm)
        
        self.voting_controller = VotingController(
            self.root,
            self.data_manager,
            self.ranking_algorithm,
            self.image_processor,
            self.image_display
        )
        
        left_frame, right_frame = self.image_display.get_frames()
        self.voting_controller.create_vote_buttons(left_frame, right_frame)
        
        self.folder_manager.set_ui_references(ui_refs['folder_label'], ui_refs['status_bar'])
        self.voting_controller.set_ui_references(ui_refs['status_bar'], ui_refs['stats_label'])
        
        self.folder_manager.set_load_complete_callback(self._on_images_loaded)
        self.voting_controller.set_vote_callback(self._on_vote_cast)
        
        self.voting_controller.setup_keyboard_shortcuts()
        self._setup_additional_shortcuts()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _setup_additional_shortcuts(self) -> None:
        """Setup additional keyboard shortcuts."""
        for key in KeyBindings.SAVE:
            self.root.bind(key, lambda e: self.save_data())
        
        for key in KeyBindings.LOAD:
            self.root.bind(key, lambda e: self.load_data())
        
        for key in KeyBindings.STATS:
            self.root.bind(key, lambda e: self.show_detailed_stats())
        
        for key in KeyBindings.PROMPT_ANALYSIS:
            self.root.bind(key, lambda e: self.show_prompt_analysis())
        
        for key in KeyBindings.SETTINGS:
            self.root.bind(key, lambda e: self.show_settings())
    
    def _on_images_loaded(self, images: list) -> None:
        """Handle completion of image loading."""
        ui_refs = self.ui_builder.get_ui_references()
        ui_refs['stats_label'].config(text=f"Total votes: {self.data_manager.vote_count}")
        
        self.voting_controller.show_next_pair()
        
        print(f"Successfully loaded {len(images)} images")
    
    def _on_vote_cast(self, winner: str, loser: str) -> None:
        """Handle vote being cast."""
        pass
    
    def save_data(self) -> None:
        """Save ranking data to file."""
        if not self.data_manager.image_stats:
            messagebox.showinfo("Info", "No data to save yet")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            if self.data_manager.save_to_file(filename):
                messagebox.showinfo("Success", f"Data saved to {filename}")
            else:
                messagebox.showerror("Error", "Failed to save data")
    
    def load_data(self) -> None:
        """Load ranking data from file."""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            self.image_display.clear_images()
            self.voting_controller.reset_voting_state()
            
            if self.folder_manager.load_from_file(filename):
                ui_refs = self.ui_builder.get_ui_references()
                ui_refs['stats_label'].config(text=f"Total votes: {self.data_manager.vote_count}")
    
    def show_detailed_stats(self) -> None:
        """Show the detailed statistics window."""
        if not self.data_manager.image_stats:
            messagebox.showinfo("No Data", "No image data to display. Please load images first.")
            return
        
        if self.stats_window is None:
            self.stats_window = StatsWindow(
                self.root, 
                self.data_manager, 
                self.ranking_algorithm, 
                self.prompt_analyzer
            )
        else:
            self.stats_window.show()
    
    def show_prompt_analysis(self) -> None:
        """Show the prompt analysis functionality."""
        if not self.data_manager.image_stats:
            messagebox.showinfo("No Data", "No image data to display. Please load images first.")
            return
        
        prompt_count = sum(1 for stats in self.data_manager.image_stats.values() 
                          if stats.get('prompt'))
        
        if prompt_count == 0:
            messagebox.showinfo("No Prompts", "No AI generation prompts found in the images. "
                              "Prompt analysis requires images with embedded prompt metadata.")
            return
        
        if self.stats_window is None:
            self.stats_window = StatsWindow(
                self.root, 
                self.data_manager, 
                self.ranking_algorithm, 
                self.prompt_analyzer
            )
        else:
            self.stats_window.show()
            self.stats_window.focus_prompt_analysis_tab()
    
    def show_settings(self) -> None:
        """Show the settings window."""
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self.root, self.data_manager)
        else:
            self.settings_window.show()
    
    def on_closing(self) -> None:
        """Handle application closing with cleanup."""
        self.metadata_processor.cleanup()
        self.progress_tracker.cleanup()
        self.folder_manager.cleanup()
        self.voting_controller.cleanup()
        self.image_display.cleanup()
        
        if self.stats_window:
            self.stats_window.close_window()
        if self.settings_window:
            self.settings_window.close_window()
        
        self.image_processor.cleanup_resources()
        
        self.root.destroy()