"""Modern main window for the Image Ranking System."""

import tkinter as tk
from tkinter import messagebox, filedialog
import sys
import os

from config import Colors, Fonts, KeyBindings, Styling
from core.data_manager import DataManager
from core.image_processor import ImageProcessor
from core.ranking_algorithm import RankingAlgorithm
from core.prompt_analyzer import PromptAnalyzer

from ui.components.image_display import ImageDisplayController
from ui.components.voting_controller import VotingController
from ui.components.metadata_processor import MetadataProcessor
from ui.components.progress_tracker import ProgressTracker
from ui.components.folder_manager import FolderManager
from ui.components.ui_builder import UIBuilder, ModernButton, ModernFrame

from ui.stats_window import StatsWindow
from ui.settings_window import SettingsWindow


class ModernVoteButton(ModernButton):
    """Custom vote button with enhanced styling for voting interface."""
    
    def __init__(self, parent, side='left', **kwargs):
        # Choose style based on side
        if side == 'left':
            style = 'success'
            text = "← Vote Left"
        else:
            style = 'primary'
            text = "Vote Right →"
        
        super().__init__(parent, text=text, style=style, **kwargs)
        
        # Add special styling for vote buttons
        self.configure(font=Fonts.HEADING, pady=Styling.PADDING_LARGE)
        
        # Add glow effect when enabled
        self.bind('<Button-1>', self._on_vote_click)
    
    def _on_vote_click(self, event):
        """Handle vote button click with visual feedback."""
        # Temporary visual feedback
        original_bg = self.cget('bg')
        self.configure(bg=Colors.PURPLE_SECONDARY)
        self.after(100, lambda: self.configure(bg=original_bg))


class MainWindow:
    """Modern main application window with sleek design."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        
        # Initialize core components
        self.data_manager = DataManager()
        self.image_processor = ImageProcessor()
        self.ranking_algorithm = RankingAlgorithm(self.data_manager)
        self.prompt_analyzer = PromptAnalyzer(self.data_manager)
        
        # Initialize modern UI components
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
        
        # Modern vote buttons
        self.left_vote_button = None
        self.right_vote_button = None
        
        # Window references
        self.stats_window = None
        self.settings_window = None
        
        self._setup_modern_application()
    
    def _setup_modern_application(self) -> None:
        """Setup the complete modern application."""
        self.ui_builder.setup_window_properties()
        
        # Build main UI
        ui_refs = self.ui_builder.build_main_ui()
        
        # Create modern control buttons
        self._create_modern_controls(ui_refs['top_frame'])
        
        # Setup modern image display
        self.image_display = ImageDisplayController(
            self.root, 
            self.data_manager, 
            self.image_processor, 
            self.prompt_analyzer
        )
        
        # Create modern image frames
        self.image_display.create_image_frames(ui_refs['main_frame'])
        self.image_display.set_ranking_algorithm(self.ranking_algorithm)
        
        # Setup modern voting interface
        self._setup_modern_voting()
        
        # Setup folder manager
        self.folder_manager.set_ui_references(ui_refs['folder_label'], ui_refs['status_bar'])
        
        # Setup callbacks
        self.folder_manager.set_load_complete_callback(self._on_images_loaded)
        
        # Setup keyboard shortcuts
        self._setup_modern_shortcuts()
        
        # Setup window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _create_modern_controls(self, parent_frame: tk.Frame) -> None:
        """Create modern control buttons with enhanced styling."""
        # Button container
        button_container = ModernFrame(parent_frame)
        button_container.pack(fill=tk.X, pady=Styling.PADDING_LARGE)
        
        # Modern button configurations
        button_configs = [
            ("📁 Select Folder", self.folder_manager.select_folder, "success"),
            ("💾 Save Progress", self.save_data, "primary"),
            ("📂 Load Progress", self.load_data, "primary"),
            ("📊 Statistics", self.show_detailed_stats, "secondary"),
            ("🔍 Prompt Analysis", self.show_prompt_analysis, "secondary"),
            ("⚙️ Settings", self.show_settings, "ghost")
        ]
        
        for text, command, style in button_configs:
            btn = ModernButton(button_container, 
                             text=text,
                             command=command,
                             style=style,
                             font=Fonts.MEDIUM)
            btn.pack(side=tk.LEFT, padx=(0, Styling.PADDING_MEDIUM))
    
    def _setup_modern_voting(self) -> None:
        """Setup modern voting interface with enhanced buttons."""
        # Get frame references
        left_frame, right_frame = self.image_display.get_frames()
        
        # Create modern vote buttons
        self.left_vote_button = ModernVoteButton(
            left_frame,
            side='left',
            command=lambda: self.vote('left'),
            state=tk.DISABLED
        )
        
        self.right_vote_button = ModernVoteButton(
            right_frame,
            side='right',
            command=lambda: self.vote('right'),
            state=tk.DISABLED
        )
        
        # Position buttons in their frames
        self.left_vote_button.grid(row=3, column=0, sticky="ew", 
                                  padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        self.right_vote_button.grid(row=3, column=0, sticky="ew", 
                                   padx=Styling.PADDING_LARGE, pady=Styling.PADDING_LARGE)
        
        # Setup click handlers for images
        self.image_display.bind_click_handlers(
            lambda: self.vote('left'),
            lambda: self.vote('right')
        )
        
        # Initialize voting state
        self.current_pair = (None, None)
        self.previous_pair = (None, None)
    
    def _setup_modern_shortcuts(self) -> None:
        """Setup modern keyboard shortcuts."""
        # Voting shortcuts
        for key in KeyBindings.VOTE_LEFT:
            self.root.bind(key, lambda e: self.vote('left') if self._can_vote() else None)
        
        for key in KeyBindings.VOTE_RIGHT:
            self.root.bind(key, lambda e: self.vote('right') if self._can_vote() else None)
        
        # Other shortcuts
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
    
    def _can_vote(self) -> bool:
        """Check if voting is currently possible."""
        return (self.left_vote_button and 
                self.left_vote_button['state'] == tk.NORMAL and
                self.right_vote_button and 
                self.right_vote_button['state'] == tk.NORMAL)
    
    def show_next_pair(self) -> None:
        """Display the next pair of images for voting."""
        if self.data_manager.image_folder == "":
            return
        
        images = self.image_processor.get_image_files(self.data_manager.image_folder)
        if len(images) < 2:
            return
        
        # Clear previous images
        self.image_display.clear_images()
        
        # Store previous pair
        if self.current_pair[0] and self.current_pair[1]:
            self.previous_pair = self.current_pair
        
        # Get next pair
        img1, img2 = self.ranking_algorithm.select_next_pair(images, self.previous_pair)
        if not img1 or not img2:
            return
        
        self.current_pair = (img1, img2)
        
        # Display images
        self.image_display.display_image(img1, 'left')
        self.image_display.display_image(img2, 'right')
        
        # Enable voting buttons
        self.left_vote_button.config(state=tk.NORMAL)
        self.right_vote_button.config(state=tk.NORMAL)
        
        # Update status with modern styling
        explanation = self.ranking_algorithm.get_selection_explanation(img1, img2)
        ui_refs = self.ui_builder.get_ui_references()
        ui_refs['status_bar'].config(text=explanation, fg=Colors.TEXT_PRIMARY)
    
    def vote(self, side: str) -> None:
        """Process a vote with modern visual feedback."""
        if not self.current_pair[0] or not self.current_pair[1]:
            return
        
        winner = self.current_pair[0] if side == 'left' else self.current_pair[1]
        loser = self.current_pair[1] if side == 'left' else self.current_pair[0]
        
        # Record vote
        self.data_manager.record_vote(winner, loser)
        self.ranking_algorithm.invalidate_cache()
        
        # Update stats with modern styling
        ui_refs = self.ui_builder.get_ui_references()
        ui_refs['stats_label'].config(text=f"Total votes: {self.data_manager.vote_count}")
        
        # Update status with success color
        status_message = f"✅ {winner} wins over {loser}"
        ui_refs['status_bar'].config(text=status_message, fg=Colors.SUCCESS)
        
        # Disable voting buttons
        self.left_vote_button.config(state=tk.DISABLED)
        self.right_vote_button.config(state=tk.DISABLED)
        
        # Show next pair after delay
        self.root.after(500, self.show_next_pair)
    
    def _on_images_loaded(self, images: list) -> None:
        """Handle completion of image loading with modern feedback."""
        ui_refs = self.ui_builder.get_ui_references()
        ui_refs['stats_label'].config(text=f"Total votes: {self.data_manager.vote_count}")
        
        # Update status with success styling
        status_message = f"✅ Loaded {len(images)} images successfully"
        ui_refs['status_bar'].config(text=status_message, fg=Colors.SUCCESS)
        
        # Show first pair
        self.show_next_pair()
        
        print(f"Successfully loaded {len(images)} images with modern interface")
    
    def save_data(self) -> None:
        """Save ranking data with modern dialog."""
        if not self.data_manager.image_stats:
            self._show_modern_info("No Data", "No data to save yet")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Ranking Data"
        )
        
        if filename:
            if self.data_manager.save_to_file(filename):
                self._show_modern_success("Success", f"Data saved to {filename}")
            else:
                self._show_modern_error("Error", "Failed to save data")
    
    def load_data(self) -> None:
        """Load ranking data with modern dialog."""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Ranking Data"
        )
        
        if filename:
            self.image_display.clear_images()
            self.current_pair = (None, None)
            
            if self.folder_manager.load_from_file(filename):
                ui_refs = self.ui_builder.get_ui_references()
                ui_refs['stats_label'].config(text=f"Total votes: {self.data_manager.vote_count}")
    
    def show_detailed_stats(self) -> None:
        """Show modern statistics window."""
        if not self.data_manager.image_stats:
            self._show_modern_info("No Data", "No image data to display. Please load images first.")
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
        """Show modern prompt analysis."""
        if not self.data_manager.image_stats:
            self._show_modern_info("No Data", "No image data to display. Please load images first.")
            return
        
        prompt_count = sum(1 for stats in self.data_manager.image_stats.values() 
                          if stats.get('prompt'))
        
        if prompt_count == 0:
            self._show_modern_info("No Prompts", 
                                  "No AI generation prompts found in the images.\n"
                                  "Prompt analysis requires images with embedded metadata.")
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
        """Show modern settings window."""
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self.root, self.data_manager)
        else:
            self.settings_window.show()
    
    def _show_modern_info(self, title: str, message: str) -> None:
        """Show modern info dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.configure(bg=Colors.BG_PRIMARY)
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Content
        content_frame = ModernFrame(dialog, style='card')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Icon and title
        title_frame = ModernFrame(content_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        icon_label = tk.Label(title_frame, text="ℹ️", font=Fonts.DISPLAY, 
                             fg=Colors.INFO, bg=Colors.BG_CARD)
        icon_label.pack(side=tk.LEFT)
        
        title_label = tk.Label(title_frame, text=title, font=Fonts.HEADING,
                              fg=Colors.TEXT_PRIMARY, bg=Colors.BG_CARD)
        title_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Message
        msg_label = tk.Label(content_frame, text=message, font=Fonts.NORMAL,
                            fg=Colors.TEXT_SECONDARY, bg=Colors.BG_CARD,
                            wraplength=350, justify=tk.LEFT)
        msg_label.pack(pady=10)
        
        # OK button
        ok_button = ModernButton(content_frame, text="OK", command=dialog.destroy, style='primary')
        ok_button.pack(pady=10)
    
    def _show_modern_success(self, title: str, message: str) -> None:
        """Show modern success dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.configure(bg=Colors.BG_PRIMARY)
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Content
        content_frame = ModernFrame(dialog, style='card')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Icon and title
        title_frame = ModernFrame(content_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        icon_label = tk.Label(title_frame, text="✅", font=Fonts.DISPLAY, 
                             fg=Colors.SUCCESS, bg=Colors.BG_CARD)
        icon_label.pack(side=tk.LEFT)
        
        title_label = tk.Label(title_frame, text=title, font=Fonts.HEADING,
                              fg=Colors.TEXT_PRIMARY, bg=Colors.BG_CARD)
        title_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Message
        msg_label = tk.Label(content_frame, text=message, font=Fonts.NORMAL,
                            fg=Colors.TEXT_SECONDARY, bg=Colors.BG_CARD,
                            wraplength=350, justify=tk.LEFT)
        msg_label.pack(pady=10)
        
        # OK button
        ok_button = ModernButton(content_frame, text="OK", command=dialog.destroy, style='success')
        ok_button.pack(pady=10)
    
    def _show_modern_error(self, title: str, message: str) -> None:
        """Show modern error dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.configure(bg=Colors.BG_PRIMARY)
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Content
        content_frame = ModernFrame(dialog, style='card')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Icon and title
        title_frame = ModernFrame(content_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        icon_label = tk.Label(title_frame, text="❌", font=Fonts.DISPLAY, 
                             fg=Colors.ERROR, bg=Colors.BG_CARD)
        icon_label.pack(side=tk.LEFT)
        
        title_label = tk.Label(title_frame, text=title, font=Fonts.HEADING,
                              fg=Colors.TEXT_PRIMARY, bg=Colors.BG_CARD)
        title_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Message
        msg_label = tk.Label(content_frame, text=message, font=Fonts.NORMAL,
                            fg=Colors.TEXT_SECONDARY, bg=Colors.BG_CARD,
                            wraplength=350, justify=tk.LEFT)
        msg_label.pack(pady=10)
        
        # OK button
        ok_button = ModernButton(content_frame, text="OK", command=dialog.destroy, style='error')
        ok_button.pack(pady=10)
    
    def on_closing(self) -> None:
        """Handle application closing with modern cleanup."""
        # Show modern confirmation dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Confirm Exit")
        dialog.geometry("350x150")
        dialog.configure(bg=Colors.BG_PRIMARY)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Content
        content_frame = ModernFrame(dialog, style='card')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Message
        msg_label = tk.Label(content_frame, text="Are you sure you want to exit?",
                            font=Fonts.MEDIUM, fg=Colors.TEXT_PRIMARY, bg=Colors.BG_CARD)
        msg_label.pack(pady=10)
        
        # Button frame
        button_frame = ModernFrame(content_frame)
        button_frame.pack(pady=10)
        
        # Buttons
        def confirm_exit():
            dialog.destroy()
            self._cleanup_and_exit()
        
        def cancel_exit():
            dialog.destroy()
        
        cancel_btn = ModernButton(button_frame, text="Cancel", command=cancel_exit, style='secondary')
        cancel_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        exit_btn = ModernButton(button_frame, text="Exit", command=confirm_exit, style='error')
        exit_btn.pack(side=tk.LEFT)
    
    def _cleanup_and_exit(self) -> None:
        """Perform cleanup and exit."""
        # Cleanup components
        self.metadata_processor.cleanup()
        self.progress_tracker.cleanup()
        self.folder_manager.cleanup()
        
        if self.image_display:
            self.image_display.cleanup()
        
        # Close windows
        if self.stats_window:
            self.stats_window.close_window()
        if self.settings_window:
            self.settings_window.close_window()
        
        # Cleanup image processor
        self.image_processor.cleanup_resources()
        
        # Destroy main window
        self.root.destroy()
