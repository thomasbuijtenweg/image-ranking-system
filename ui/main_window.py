"""Main window for the Image Ranking System with binning support and improved error handling - FIXED."""

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
from core.filter_manager import FilterManager

from ui.components.image_display import ImageDisplayController
from ui.components.voting_controller import VotingController
from ui.components.metadata_processor import MetadataProcessor
from ui.components.progress_tracker import ProgressTracker
from ui.components.folder_manager import FolderManager
from ui.components.ui_builder import UIBuilder
from ui.components.filter_ui import FilterUI

from ui.stats_window import StatsWindow
from ui.settings_window import SettingsWindow


class MainWindow:
    """Main application window coordinating all components."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        
        # Initialize core components with error handling
        try:
            print("MainWindow: Initializing core components...")
            self.data_manager = DataManager()
            self.image_processor = ImageProcessor()
            self.ranking_algorithm = RankingAlgorithm(self.data_manager)
            self.prompt_analyzer = PromptAnalyzer(self.data_manager)
            self.filter_manager = FilterManager(self.data_manager, self.prompt_analyzer)
            print("MainWindow: Core components initialized successfully")
        except Exception as e:
            print(f"MainWindow: Error initializing core components: {e}")
            messagebox.showerror("Initialization Error", f"Failed to initialize core components:\n{str(e)}")
            sys.exit(1)
        
        # Initialize UI components with error handling
        try:
            print("MainWindow: Initializing UI components...")
            self.ui_builder = UIBuilder(root)
            self.progress_tracker = ProgressTracker(root)
            self.metadata_processor = MetadataProcessor(self.data_manager, self.image_processor)
            self.folder_manager = FolderManager(
                self.data_manager, 
                self.image_processor, 
                self.metadata_processor, 
                self.progress_tracker
            )
            print("MainWindow: UI components initialized successfully")
        except Exception as e:
            print(f"MainWindow: Error initializing UI components: {e}")
            messagebox.showerror("UI Initialization Error", f"Failed to initialize UI components:\n{str(e)}")
            sys.exit(1)
        
        self.image_display = None
        self.voting_controller = None
        self.filter_ui = None
        
        # Window references
        self.stats_window = None
        self.settings_window = None
        
        self._setup_application()
    
    def _setup_application(self) -> None:
        """Setup the complete application with comprehensive error handling."""
        try:
            print("MainWindow: Starting application setup...")
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
            
            print("MainWindow: Creating image display controller...")
            self.image_display = ImageDisplayController(
                self.root, 
                self.data_manager, 
                self.image_processor, 
                self.prompt_analyzer
            )
            
            # Create a container frame for filters (uses pack)
            filter_container = tk.Frame(ui_refs['main_frame'], bg='#2b2b2b')
            filter_container.pack(fill=tk.X, padx=5, pady=5)
            
            # Create filter UI in its own container
            print("MainWindow: Creating filter UI...")
            self.filter_ui = FilterUI(
                filter_container,
                self.filter_manager,
                on_filter_change=self._on_filter_changed
            )
            print("MainWindow: Filter UI created successfully")
            
            # Create a separate container for image display (uses grid)
            image_container = tk.Frame(ui_refs['main_frame'], bg='#2b2b2b')
            image_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            self.image_display.create_image_frames(image_container)
            self.image_display.set_ranking_algorithm(self.ranking_algorithm)
            print("MainWindow: Image display controller created successfully")
            
            print("MainWindow: Creating voting controller...")
            self.voting_controller = VotingController(
                self.root,
                self.data_manager,
                self.ranking_algorithm,
                self.image_processor,
                self.image_display
            )
            
            left_frame, right_frame = self.image_display.get_frames()
            self.voting_controller.create_vote_buttons(left_frame, right_frame)
            print("MainWindow: Voting controller created successfully")
            
            # FIXED: Set cross-references for binning functionality BEFORE any other operations
            print("MainWindow: Setting up cross-references...")
            self.folder_manager.set_voting_controller_reference(self.voting_controller)
            
            # Set filter manager reference in voting controller
            self.voting_controller.set_filter_manager(self.filter_manager)
            
            self.folder_manager.set_ui_references(ui_refs['folder_label'], ui_refs['status_bar'])
            self.voting_controller.set_ui_references(ui_refs['status_bar'], ui_refs['stats_label'])
            
            self.folder_manager.set_load_complete_callback(self._on_images_loaded)
            self.voting_controller.set_vote_callback(self._on_vote_cast)
            print("MainWindow: Cross-references set successfully")
            
            print("MainWindow: Setting up keyboard shortcuts...")
            self.voting_controller.setup_keyboard_shortcuts()
            self._setup_additional_shortcuts()
            print("MainWindow: Keyboard shortcuts set up successfully")
            
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            print("MainWindow: Application setup completed successfully")
            
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
            
            print("MainWindow: Keyboard shortcuts setup successfully")
        except Exception as e:
            print(f"MainWindow: Error setting up keyboard shortcuts: {e}")
            # Non-critical error, continue
    
    def _on_images_loaded(self, images: list) -> None:
        """Handle completion of image loading."""
        try:
            print(f"MainWindow: Images loaded callback - {len(images)} images")
            ui_refs = self.ui_builder.get_ui_references()
            active_count = self.data_manager.get_active_image_count()
            binned_count = self.data_manager.get_binned_image_count()
            ui_refs['stats_label'].config(
                text=f"Votes: {self.data_manager.vote_count} | Active: {active_count} | Binned: {binned_count}"
            )
            
            # FIXED: Verify that image binner is properly initialized
            binner_status = ""
            if self.voting_controller and hasattr(self.voting_controller, 'image_binner'):
                if self.voting_controller.image_binner:
                    binner_status = " | Binning: Ready"
                else:
                    binner_status = " | Binning: Not initialized"
                    print("MainWindow: WARNING - Image binner not initialized after loading images")
            else:
                binner_status = " | Binning: Unavailable"
                print("MainWindow: WARNING - Voting controller or image binner attribute missing")
            
            if 'status_bar' in ui_refs and ui_refs['status_bar']:
                current_text = ui_refs['status_bar'].cget('text')
                ui_refs['status_bar'].config(text=current_text + binner_status)
            
            # Refresh filter UI after loading images
            if self.filter_ui:
                self.filter_ui.refresh()
                print("MainWindow: Filter UI refreshed after loading images")
            
            self.voting_controller.show_next_pair()
            
            print(f"MainWindow: Successfully loaded {len(images)} images (Active: {active_count}, Binned: {binned_count}){binner_status}")
        except Exception as e:
            print(f"MainWindow: Error handling image load completion: {e}")
            messagebox.showerror("Load Error", f"Error after loading images:\n{str(e)}")
    
    def _on_vote_cast(self, winner: str, loser: str) -> None:
        """Handle vote being cast."""
        try:
            # Refresh any open stats windows
            if self.stats_window and hasattr(self.stats_window, 'refresh_stats'):
                self.stats_window.refresh_stats()
        except Exception as e:
            print(f"MainWindow: Error handling vote cast: {e}")
            # Non-critical error, continue
    
    def _on_filter_changed(self) -> None:
        """Handle filter changes."""
        try:
            print("MainWindow: Filter changed, refreshing voting pair...")
            # Refresh the current image pair to respect new filters
            if self.voting_controller:
                self.voting_controller.show_next_pair()
            
            # Update filter UI
            if self.filter_ui:
                self.filter_ui.refresh()
            
            print("MainWindow: Filter change handled successfully")
        except Exception as e:
            print(f"MainWindow: Error handling filter change: {e}")
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
                # Prepare filter state for saving
                filter_state = None
                if self.filter_manager:
                    filter_state = self.filter_manager.export_state()
                
                # Get core data
                serializable_stats = {}
                for img_name, stats in self.data_manager.image_stats.items():
                    stats_copy = stats.copy()
                    if 'tested_against' in stats_copy:
                        stats_copy['tested_against'] = list(stats_copy['tested_against'])
                    serializable_stats[img_name] = stats_copy
                
                core_data = {
                    'image_folder': self.data_manager.image_folder,
                    'vote_count': self.data_manager.vote_count,
                    'image_stats': serializable_stats,
                    'metadata_cache': self.data_manager.metadata_cache,
                    'binned_images': list(self.data_manager.binned_images)
                }
                
                # Get other settings
                weight_data = self.data_manager.weight_manager.export_to_data()
                algorithm_settings = self.data_manager.algorithm_settings.export_settings()
                
                # Prepare complete save data with filter state
                save_data = self.data_manager.data_persistence.prepare_save_data(
                    core_data, weight_data, algorithm_settings, filter_state)
                
                # Save to file
                if self.data_manager.data_persistence.save_to_file(filename, save_data):
                    active_count = self.data_manager.get_active_image_count()
                    binned_count = self.data_manager.get_binned_image_count()
                    
                    # Get filter stats for save message
                    filter_info = ""
                    if self.filter_manager and self.filter_manager.is_active():
                        stats = self.filter_manager.get_filter_stats()
                        filter_info = f"\n\nActive filters saved: {len(stats['include_words'])} include, {len(stats['exclude_words'])} exclude words."
                    
                    # FIXED: Include binning status in save message
                    binner_status = ""
                    if self.voting_controller and hasattr(self.voting_controller, 'image_binner') and self.voting_controller.image_binner:
                        binner_status = "\n\nBinning functionality is active and will be restored when loading this save."
                    else:
                        binner_status = "\n\nNote: Binning functionality was not active when saving."
                    
                    messagebox.showinfo("Success", f"Data saved to {filename}\n\nSaved {active_count} active images and {binned_count} binned images.{filter_info}{binner_status}")
                else:
                    messagebox.showerror("Error", "Failed to save data")
        except Exception as e:
            print(f"MainWindow: Error saving data: {e}")
            messagebox.showerror("Save Error", f"Failed to save data:\n{str(e)}")
    
    def load_data(self) -> None:
        """Load ranking data from file with error handling."""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                print(f"MainWindow: Loading data from {filename}")
                self.image_display.clear_images()
                self.voting_controller.reset_voting_state()
                
                # FIXED: Clear any existing image binner before loading
                if self.voting_controller:
                    self.voting_controller.image_binner = None
                    self.voting_controller.image_folder_path = None
                    print("MainWindow: Cleared existing image binner before loading")
                
                # Load data from file
                success, data, error_msg = self.data_manager.data_persistence.load_from_file(filename)
                
                if success:
                    # Validate and fix data
                    data = self.data_manager.data_persistence.validate_and_fix_data(data)
                    
                    # Extract and load core data
                    core_data = self.data_manager.data_persistence.extract_core_data(data)
                    self.data_manager.image_folder = core_data['image_folder']
                    self.data_manager.vote_count = core_data['vote_count']
                    self.data_manager.image_stats = core_data['image_stats']
                    self.data_manager.metadata_cache = core_data['metadata_cache']
                    self.data_manager.binned_images = core_data['binned_images']
                    
                    # Convert tested_against lists back to sets
                    for img_name, stats in self.data_manager.image_stats.items():
                        if 'tested_against' in stats and isinstance(stats['tested_against'], list):
                            stats['tested_against'] = set(stats['tested_against'])
                        elif 'tested_against' not in stats:
                            stats['tested_against'] = set()
                    
                    # Load other settings
                    self.data_manager.weight_manager.load_from_data(data)
                    self.data_manager.algorithm_settings.load_settings(data)
                    
                    # Load filter state if present
                    if 'filter_state' in data and self.filter_manager:
                        print("MainWindow: Restoring filter state...")
                        self.filter_manager.import_state(data['filter_state'])
                        if self.filter_ui:
                            self.filter_ui.refresh()
                        print("MainWindow: Filter state restored")
                    
                    # Update existing images with strategic timing
                    self.data_manager._update_existing_images_with_strategic_timing()
                    
                    # Initialize all image stats
                    for image_filename in self.data_manager.image_stats:
                        self.data_manager.initialize_image_stats(image_filename)
                    
                    # Now reload images from folder
                    if self.data_manager.image_folder:
                        print(f"MainWindow: Reloading images from saved folder: {self.data_manager.image_folder}")
                        self.folder_manager.load_images()
                    
                    ui_refs = self.ui_builder.get_ui_references()
                    active_count = self.data_manager.get_active_image_count()
                    binned_count = self.data_manager.get_binned_image_count()
                    ui_refs['stats_label'].config(
                        text=f"Votes: {self.data_manager.vote_count} | Active: {active_count} | Binned: {binned_count}"
                    )
                    
                    # Show filter info if filters were restored
                    if 'filter_state' in data and self.filter_manager and self.filter_manager.is_active():
                        filter_stats = self.filter_manager.get_filter_stats()
                        print(f"MainWindow: Filters restored - {len(filter_stats['include_words'])} include, {len(filter_stats['exclude_words'])} exclude")
                    
                    print(f"MainWindow: Data loaded successfully")
                else:
                    print(f"MainWindow: Failed to load data from {filename}: {error_msg}")
        except Exception as e:
            print(f"MainWindow: Error loading data: {e}")
            messagebox.showerror("Load Error", f"Failed to load data:\n{str(e)}")
    
    def show_detailed_stats(self) -> None:
        """Show the detailed statistics window with error handling."""
        try:
            if not self.data_manager.image_stats:
                messagebox.showinfo("No Data", "No image data to display. Please load images first.")
                return
            
            if self.stats_window is None:
                print("MainWindow: Creating new stats window...")
                self.stats_window = StatsWindow(
                    self.root, 
                    self.data_manager, 
                    self.ranking_algorithm, 
                    self.prompt_analyzer
                )
                print("MainWindow: Stats window created successfully")
            else:
                print("MainWindow: Showing existing stats window...")
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
            
            print(f"MainWindow: Found {prompt_count} images with prompts")
            
            if self.stats_window is None:
                print("MainWindow: Creating new stats window for prompt analysis...")
                self.stats_window = StatsWindow(
                    self.root, 
                    self.data_manager, 
                    self.ranking_algorithm, 
                    self.prompt_analyzer
                )
                print("MainWindow: Stats window created successfully")
            else:
                print("MainWindow: Showing existing stats window...")
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
            print("MainWindow: Cleaning up application...")
            
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
            
            print("MainWindow: Cleanup completed successfully")
            
        except Exception as e:
            print(f"MainWindow: Error during cleanup: {e}")
            # Continue with shutdown even if cleanup fails
        
        try:
            self.root.destroy()
        except Exception as e:
            print(f"MainWindow: Error destroying root window: {e}")
            # Force exit if normal destroy fails
            sys.exit(0)