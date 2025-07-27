"""Main window for the Image Ranking System with binning support and improved error handling."""

import tkinter as tk
from tkinter import messagebox, filedialog
import sys
import os
import traceback

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
        
        # Initialize core components with error handling
        try:
            self.data_manager = DataManager()
            self.image_processor = ImageProcessor()
            self.ranking_algorithm = RankingAlgorithm(self.data_manager)
            self.prompt_analyzer = PromptAnalyzer(self.data_manager)
            print("Core components initialized successfully")
        except Exception as e:
            print(f"Error initializing core components: {e}")
            messagebox.showerror("Initialization Error", f"Failed to initialize core components:\n{str(e)}")
            sys.exit(1)
        
        # Initialize UI components with error handling
        try:
            self.ui_builder = UIBuilder(root)
            self.progress_tracker = ProgressTracker(root)
            self.metadata_processor = MetadataProcessor(self.data_manager, self.image_processor)
            self.folder_manager = FolderManager(
                self.data_manager, 
                self.image_processor, 
                self.metadata_processor, 
                self.progress_tracker
            )
            print("UI components initialized successfully")
        except Exception as e:
            print(f"Error initializing UI components: {e}")
            messagebox.showerror("UI Initialization Error", f"Failed to initialize UI components:\n{str(e)}")
            sys.exit(1)
        
        self.image_display = None
        self.voting_controller = None
        
        # Window references
        self.stats_window = None
        self.settings_window = None
        
        self._setup_application()
    
    def _setup_application(self) -> None:
        """Setup the complete application with comprehensive error handling."""
        try:
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
            
            # Set cross-references for binning functionality
            self.folder_manager.set_voting_controller_reference(self.voting_controller)
            
            self.folder_manager.set_ui_references(ui_refs['folder_label'], ui_refs['status_bar'])
            self.voting_controller.set_ui_references(ui_refs['status_bar'], ui_refs['stats_label'])
            
            self.folder_manager.set_load_complete_callback(self._on_images_loaded)
            self.voting_controller.set_vote_callback(self._on_vote_cast)
            
            self.voting_controller.setup_keyboard_shortcuts()
            self._setup_additional_shortcuts()
            
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            print("Application setup completed successfully")
            
        except Exception as e:
            error_msg = f"Critical error during application setup: {e}"
            print(error_msg)
            print(traceback.format_exc())
            messagebox.showerror("Setup Error", f"Failed to setup application:\n{str(e)}\n\nSee console for details.")
            sys.exit(1)
    
    def _setup_additional_shortcuts(self) -> None:
        """Setup additional keyboard shortcuts."""
        try:
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
            
            print("Keyboard shortcuts setup successfully")
        except Exception as e:
            print(f"Error setting up keyboard shortcuts: {e}")
            # Non-critical error, continue
    
    def _on_images_loaded(self, images: list) -> None:
        """Handle completion of image loading."""
        try:
            ui_refs = self.ui_builder.get_ui_references()
            active_count = self.data_manager.get_active_image_count()
            binned_count = self.data_manager.get_binned_image_count()
            ui_refs['stats_label'].config(
                text=f"Votes: {self.data_manager.vote_count} | Active: {active_count} | Binned: {binned_count}"
            )
            
            self.voting_controller.show_next_pair()
            
            print(f"Successfully loaded {len(images)} images (Active: {active_count}, Binned: {binned_count})")
        except Exception as e:
            print(f"Error handling image load completion: {e}")
            messagebox.showerror("Load Error", f"Error after loading images:\n{str(e)}")
    
    def _on_vote_cast(self, winner: str, loser: str) -> None:
        """Handle vote being cast."""
        try:
            # Refresh any open stats windows
            if self.stats_window and hasattr(self.stats_window, 'refresh_stats'):
                self.stats_window.refresh_stats()
        except Exception as e:
            print(f"Error handling vote cast: {e}")
            # Non-critical error, continue
    
    def save_data(self) -> None:
        """Save ranking data to file with error handling."""
        try:
            if not self.data_manager.image_stats:
                messagebox.showinfo("Info", "No data to save yet")
                return
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                if self.data_manager.save_to_file(filename):
                    active_count = self.data_manager.get_active_image_count()
                    binned_count = self.data_manager.get_binned_image_count()
                    messagebox.showinfo("Success", f"Data saved to {filename}\n\nSaved {active_count} active images and {binned_count} binned images.")
                else:
                    messagebox.showerror("Error", "Failed to save data")
        except Exception as e:
            print(f"Error saving data: {e}")
            messagebox.showerror("Save Error", f"Failed to save data:\n{str(e)}")
    
    def load_data(self) -> None:
        """Load ranking data from file with error handling."""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                self.image_display.clear_images()
                self.voting_controller.reset_voting_state()
                
                if self.folder_manager.load_from_file(filename):
                    ui_refs = self.ui_builder.get_ui_references()
                    active_count = self.data_manager.get_active_image_count()
                    binned_count = self.data_manager.get_binned_image_count()
                    ui_refs['stats_label'].config(
                        text=f"Votes: {self.data_manager.vote_count} | Active: {active_count} | Binned: {binned_count}"
                    )
        except Exception as e:
            print(f"Error loading data: {e}")
            messagebox.showerror("Load Error", f"Failed to load data:\n{str(e)}")
    
    def show_detailed_stats(self) -> None:
        """Show the detailed statistics window with error handling."""
        try:
            if not self.data_manager.image_stats:
                messagebox.showinfo("No Data", "No image data to display. Please load images first.")
                return
            
            if self.stats_window is None:
                print("Creating new stats window...")
                self.stats_window = StatsWindow(
                    self.root, 
                    self.data_manager, 
                    self.ranking_algorithm, 
                    self.prompt_analyzer
                )
                print("Stats window created successfully")
            else:
                print("Showing existing stats window...")
                self.stats_window.show()
        except Exception as e:
            error_msg = f"Error showing statistics window: {e}"
            print(error_msg)
            print(traceback.format_exc())
            messagebox.showerror("Statistics Error", f"Failed to show statistics window:\n{str(e)}\n\nSee console for details.")
            # Reset the stats window in case it's corrupted
            self.stats_window = None
    
    def show_prompt_analysis(self) -> None:
        """Show the prompt analysis functionality with error handling."""
        try:
            if not self.data_manager.image_stats:
                messagebox.showinfo("No Data", "No image data to display. Please load images first.")
                return
            
            prompt_count = sum(1 for stats in self.data_manager.image_stats.values() 
                              if stats.get('prompt'))
            
            if prompt_count == 0:
                messagebox.showinfo("No Prompts", "No AI generation prompts found in the images. "
                                  "Prompt analysis requires images with embedded prompt metadata.")
                return
            
            print(f"Found {prompt_count} images with prompts")
            
            if self.stats_window is None:
                print("Creating new stats window for prompt analysis...")
                self.stats_window = StatsWindow(
                    self.root, 
                    self.data_manager, 
                    self.ranking_algorithm, 
                    self.prompt_analyzer
                )
                print("Stats window created successfully")
            else:
                print("Showing existing stats window...")
                self.stats_window.show()
                
            # Focus on prompt analysis tab
            if hasattr(self.stats_window, 'focus_prompt_analysis_tab'):
                self.stats_window.focus_prompt_analysis_tab()
        except Exception as e:
            error_msg = f"Error showing prompt analysis: {e}"
            print(error_msg)
            print(traceback.format_exc())
            messagebox.showerror("Prompt Analysis Error", f"Failed to show prompt analysis:\n{str(e)}\n\nSee console for details.")
            # Reset the stats window in case it's corrupted
            self.stats_window = None
    
    def show_settings(self) -> None:
        """Show the settings window with error handling."""
        try:
            if self.settings_window is None:
                self.settings_window = SettingsWindow(self.root, self.data_manager)
            else:
                self.settings_window.show()
        except Exception as e:
            error_msg = f"Error showing settings window: {e}"
            print(error_msg)
            print(traceback.format_exc())
            messagebox.showerror("Settings Error", f"Failed to show settings window:\n{str(e)}\n\nSee console for details.")
            # Reset the settings window in case it's corrupted
            self.settings_window = None
    
    def on_closing(self) -> None:
        """Handle application closing with cleanup and error handling."""
        try:
            print("Cleaning up application...")
            
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
            
            print("Cleanup completed successfully")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
            # Continue with shutdown even if cleanup fails
        
        try:
            self.root.destroy()
        except Exception as e:
            print(f"Error destroying root window: {e}")
            # Force exit if normal destroy fails
            sys.exit(0)