"""Main window for the Image Ranking System with binning support."""

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

# Import binning components
from ui.components.binning_controller import BinningController
from ui.components.binning_ui_controller import BinningUIController

from ui.stats_window import StatsWindow
from ui.settings_window import SettingsWindow


class MainWindow:
    """Main application window coordinating all components including binning functionality."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        
        # Initialize core components
        self.data_manager = DataManager()
        self.image_processor = ImageProcessor()
        self.ranking_algorithm = RankingAlgorithm(self.data_manager)
        self.prompt_analyzer = PromptAnalyzer(self.data_manager)
        
        # Initialize binning components
        self.binning_controller = BinningController(self.data_manager, self.image_processor)
        
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
        self.binning_ui_controller = None
        
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
            'show_settings': self.show_settings,
            'show_bin_management': self.show_bin_management  # New button for bin management
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
        
        # Initialize binning UI controller BEFORE voting controller
        self.binning_ui_controller = BinningUIController(
            self.root,
            self.binning_controller,
            None  # Will be set after voting controller is created
        )
        
        self.voting_controller = VotingController(
            self.root,
            self.data_manager,
            self.ranking_algorithm,
            self.image_processor,
            self.image_display,
            self.binning_ui_controller
        )
        
        # Link binning UI controller to voting controller
        self.binning_ui_controller.voting_controller = self.voting_controller
        
        left_frame, right_frame = self.image_display.get_frames()
        self.voting_controller.create_vote_buttons(left_frame, right_frame)
        
        self.folder_manager.set_ui_references(ui_refs['folder_label'], ui_refs['status_bar'])
        self.voting_controller.set_ui_references(ui_refs['status_bar'], ui_refs['stats_label'])
        
        self.folder_manager.set_load_complete_callback(self._on_images_loaded)
        self.voting_controller.set_vote_callback(self._on_vote_cast)
        
        self.voting_controller.setup_keyboard_shortcuts()
        self._setup_additional_shortcuts()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Display initial binning info
        self._update_stats_with_binning_info()
    
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
        
        # New shortcut for bin management
        self.root.bind('<Control-b>', lambda e: self.show_bin_management())
        
        print("Keyboard shortcuts enabled including Ctrl+B for bin management")
    
    def _on_images_loaded(self, images: list) -> None:
        """Handle completion of image loading."""
        ui_refs = self.ui_builder.get_ui_references()
        self._update_stats_label(ui_refs['stats_label'])
        
        self.voting_controller.show_next_pair()
        
        # Check if any images were previously binned
        binned_count = len(self.data_manager.get_binned_images())
        available_count = len(self.data_manager.get_available_images())
        
        print(f"Successfully loaded {len(images)} images ({available_count} available, {binned_count} binned)")
        
        if binned_count > 0:
            bin_path = self.binning_controller.get_bin_folder_path()
            print(f"Found {binned_count} previously binned images in: {bin_path}")
    
    def _on_vote_cast(self, winner: str, loser: str) -> None:
        """Handle vote being cast."""
        # Update stats display with binning info
        ui_refs = self.ui_builder.get_ui_references()
        self._update_stats_label(ui_refs['stats_label'])
    
    def _update_stats_label(self, stats_label: tk.Label) -> None:
        """Update the stats label with binning information."""
        available_count = len(self.data_manager.get_available_images())
        binned_count = len(self.data_manager.get_binned_images())
        total_votes = self.data_manager.vote_count
        
        stats_text = f"Votes: {total_votes} | Available: {available_count}"
        if binned_count > 0:
            stats_text += f" | Binned: {binned_count}"
        
        stats_label.config(text=stats_text)
    
    def _update_stats_with_binning_info(self) -> None:
        """Update stats display with binning information."""
        ui_refs = self.ui_builder.get_ui_references()
        self._update_stats_label(ui_refs['stats_label'])
    
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
                binned_count = len(self.data_manager.get_binned_images())
                message = f"Data saved to {filename}"
                if binned_count > 0:
                    message += f"\n\nIncluded {binned_count} binned images in save file."
                    message += "\nBinned images remain in the Bin folder."
                
                messagebox.showinfo("Success", message)
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
                self._update_stats_label(ui_refs['stats_label'])
                
                # Check for binned images after loading
                binned_count = len(self.data_manager.get_binned_images())
                if binned_count > 0:
                    bin_path = self.binning_controller.get_bin_folder_path()
                    messagebox.showinfo("Binning Info", 
                                      f"Loaded data includes {binned_count} binned images.\n\n"
                                      f"These images should be in the Bin folder:\n{bin_path}\n\n"
                                      f"If the Bin folder is missing, binned images may not display correctly.")
    
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
    
    def show_bin_management(self) -> None:
        """Show bin management dialog."""
        if not self.data_manager.image_stats:
            messagebox.showinfo("No Data", "No image data to display. Please load images first.")
            return
        
        self._create_bin_management_dialog()
    
    def _create_bin_management_dialog(self) -> None:
        """Create and show the bin management dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Bin Management")
        dialog.geometry("600x500")
        dialog.configure(bg=Colors.BG_PRIMARY)
        dialog.transient(self.root)
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 200,
            self.root.winfo_rooty() + 100
        ))
        
        # Header
        header_frame = tk.Frame(dialog, bg=Colors.BG_PRIMARY)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(header_frame, text="🗑️ Bin Management", 
                font=('Arial', 16, 'bold'), fg=Colors.TEXT_PRIMARY, 
                bg=Colors.BG_PRIMARY).pack()
        
        # Statistics
        stats = self.binning_controller.get_bin_statistics()
        stats_frame = tk.Frame(dialog, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=1)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(stats_frame, text="Statistics", 
                font=('Arial', 14, 'bold'), fg=Colors.TEXT_SUCCESS, 
                bg=Colors.BG_SECONDARY).pack(pady=5)
        
        stats_text = f"""Total Binned Images: {stats['total_binned']}
Bin Folder Exists: {'✓' if stats['bin_folder_exists'] else '✗'}
Bin Folder Path: {stats['bin_folder_path']}

Available Images: {len(self.data_manager.get_available_images())}
Total Images: {len(self.data_manager.image_stats)}"""
        
        if stats['total_binned'] > 0:
            stats_text += f"""

Average Votes Before Binning: {stats['avg_votes_before_binning']:.1f}
Average Tier Before Binning: {stats['avg_tier_before_binning']:.1f}"""
        
        tk.Label(stats_frame, text=stats_text, 
                font=('Arial', 10), fg=Colors.TEXT_PRIMARY, 
                bg=Colors.BG_SECONDARY, justify=tk.LEFT).pack(pady=10)
        
        # Binned images list
        if stats['total_binned'] > 0:
            list_frame = tk.Frame(dialog, bg=Colors.BG_SECONDARY, relief=tk.RAISED, borderwidth=1)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            tk.Label(list_frame, text="Binned Images", 
                    font=('Arial', 14, 'bold'), fg=Colors.TEXT_SUCCESS, 
                    bg=Colors.BG_SECONDARY).pack(pady=5)
            
            # Create scrollable list
            from tkinter import ttk
            listbox_frame = tk.Frame(list_frame, bg=Colors.BG_SECONDARY)
            listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            listbox = tk.Listbox(listbox_frame, bg=Colors.BG_TERTIARY, fg=Colors.TEXT_PRIMARY, 
                               selectbackground=Colors.BUTTON_HOVER, height=8)
            scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=listbox.yview)
            listbox.configure(yscrollcommand=scrollbar.set)
            
            for img in stats['binned_images']:
                listbox.insert(tk.END, img)
            
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        button_frame = tk.Frame(dialog, bg=Colors.BG_PRIMARY)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Button(button_frame, text="Open Bin Folder", 
                 command=lambda: self._open_bin_folder(),
                 bg=Colors.BUTTON_INFO, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Refresh Stats", 
                 command=lambda: self._refresh_bin_dialog(dialog),
                 bg=Colors.BUTTON_SECONDARY, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Close", 
                 command=dialog.destroy,
                 bg=Colors.BUTTON_NEUTRAL, fg='white', relief=tk.FLAT).pack(side=tk.RIGHT, padx=5)
        
        # Instructions
        instruction_text = ("Instructions:\n"
                           "• Binned images are moved to the 'Bin' subfolder\n"
                           "• To unbin: manually move images back to main folder\n"
                           "• Binned images keep their statistics\n"
                           "• Use keyboard shortcuts: Ctrl+1 (bin left), Ctrl+2 (bin right), Ctrl+3 (bin both)")
        
        tk.Label(dialog, text=instruction_text, 
                font=('Arial', 9, 'italic'), fg=Colors.TEXT_SECONDARY, 
                bg=Colors.BG_PRIMARY, justify=tk.LEFT, wraplength=550).pack(pady=10)
    
    def _open_bin_folder(self) -> None:
        """Open the bin folder in the file manager."""
        bin_path = self.binning_controller.get_bin_folder_path()
        
        if not bin_path:
            messagebox.showwarning("No Folder", "No image folder selected yet.")
            return
        
        if not os.path.exists(bin_path):
            create = messagebox.askyesno("Create Bin Folder", 
                                       f"Bin folder doesn't exist:\n{bin_path}\n\n"
                                       "Would you like to create it?")
            if create:
                self.binning_controller.create_bin_folder()
            else:
                return
        
        # Try to open the folder with the default file manager
        try:
            import subprocess
            import platform
            
            if platform.system() == "Windows":
                subprocess.run(['explorer', bin_path])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(['open', bin_path])
            else:  # Linux
                subprocess.run(['xdg-open', bin_path])
        except Exception as e:
            messagebox.showinfo("Bin Folder Location", 
                              f"Could not open folder automatically.\n\n"
                              f"Bin folder location:\n{bin_path}")
    
    def _refresh_bin_dialog(self, dialog: tk.Toplevel) -> None:
        """Refresh the bin management dialog."""
        dialog.destroy()
        self._create_bin_management_dialog()
    
    def on_closing(self) -> None:
        """Handle application closing with cleanup."""
        self.metadata_processor.cleanup()
        self.progress_tracker.cleanup()
        self.folder_manager.cleanup()
        self.voting_controller.cleanup()
        self.image_display.cleanup()
        self.binning_controller.cleanup()
        
        if self.stats_window:
            self.stats_window.close_window()
        if self.settings_window:
            self.settings_window.close_window()
        
        self.image_processor.cleanup_resources()
        
        # Show final binning statistics
        binned_count = len(self.data_manager.get_binned_images())
        if binned_count > 0:
            bin_path = self.binning_controller.get_bin_folder_path()
            print(f"Application closing with {binned_count} binned images in: {bin_path}")
        
        self.root.destroy()
