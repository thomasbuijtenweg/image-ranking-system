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
from core.image_exporter import ImageExporter
from ui.components.export_preview_window import ExportPreviewWindow

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
                'purge_binned_votes': self.purge_binned_votes,
                'export_top_images': self.export_top_images,
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
    
    def purge_binned_votes(self) -> None:
        """Purge stale votes from all binned images in the currently loaded data."""
        try:
            if not self.data_manager.image_stats:
                messagebox.showinfo("No Data", "No data loaded. Please load a save file first.")
                return
            
            binned_count = self.data_manager.get_binned_image_count()
            if binned_count == 0:
                messagebox.showinfo("No Binned Images", "There are no binned images in the current data.")
                return
            
            # Confirm with user
            confirm = messagebox.askyesno(
                "Purge Binned Votes",
                f"This will remove all vote history involving {binned_count} binned image(s) "
                f"from the remaining active images, and recalculate their tiers.\n\n"
                f"This cannot be undone. Continue?"
            )
            
            if not confirm:
                return
            
            print(f"MainWindow: Starting vote purge for {binned_count} binned images...")
            result = self.data_manager.purge_all_binned_image_votes()
            
            # Update UI
            ui_refs = self.ui_builder.get_ui_references()
            active_count = self.data_manager.get_active_image_count()
            ui_refs['stats_label'].config(
                text=f"Votes: {self.data_manager.vote_count} | Active: {active_count} | Binned: {binned_count}"
            )
            
            if ui_refs.get('status_bar'):
                ui_refs['status_bar'].config(
                    text=f"Purge complete: {result['total_removed']} vote(s) removed from {result['total_affected']} image(s)"
                )
            
            if result['total_removed'] > 0:
                messagebox.showinfo(
                    "Purge Complete",
                    f"Purged votes from {result['binned_processed']} binned image(s):\n\n"
                    f"• {result['total_removed']} stale vote(s) removed\n"
                    f"• {result['total_affected']} active image(s) recalculated\n\n"
                    f"Save your progress to persist these changes."
                )
            else:
                messagebox.showinfo(
                    "Already Clean",
                    f"Checked {result['binned_processed']} binned image(s) — no stale votes found.\n\n"
                    f"All active images are already clean."
                )
            
            print(f"MainWindow: Vote purge completed: {result}")
            
        except Exception as e:
            print(f"MainWindow: Error purging binned votes: {e}")
            messagebox.showerror("Purge Error", f"Failed to purge binned votes:\n{str(e)}")
    
    def export_top_images(self) -> None:
        """Open the Export Preview window to review and export top-N images."""
        try:
            if not self.data_manager.image_stats:
                messagebox.showinfo("No Data", "No data loaded. Please load images first.")
                return

            active_count = self.data_manager.get_active_image_count()
            if active_count == 0:
                messagebox.showinfo("No Active Images", "There are no active images to export.")
                return

            if not self.data_manager.image_folder or \
                    not os.path.isdir(self.data_manager.image_folder):
                messagebox.showerror("No Folder",
                                     "Image folder is not set or does not exist.\n"
                                     "Load a folder first.")
                return

            # ── Step 1: ask for N ──────────────────────────────────────────
            dialog = tk.Toplevel(self.root)
            dialog.title("Export Top N Images")
            dialog.geometry("360x160")
            dialog.configure(bg=Colors.BG_PRIMARY)
            dialog.grab_set()
            dialog.resizable(False, False)

            tk.Label(dialog, text=f"Active images: {active_count}",
                     bg=Colors.BG_PRIMARY, fg=Colors.TEXT_SECONDARY).pack(pady=(16, 2))
            tk.Label(dialog, text="Number of top images to preview for export:",
                     bg=Colors.BG_PRIMARY, fg=Colors.TEXT_PRIMARY).pack(pady=(0, 6))

            n_var = tk.StringVar(value="50")
            entry = tk.Entry(dialog, textvariable=n_var, width=10,
                             bg=Colors.BG_TERTIARY, fg=Colors.TEXT_PRIMARY,
                             insertbackground=Colors.TEXT_PRIMARY, justify='center')
            entry.pack()
            entry.focus()

            n_holder = [None]

            def on_n_confirm():
                try:
                    n = int(n_var.get().strip())
                    if n <= 0:
                        raise ValueError
                    n_holder[0] = min(n, active_count)
                    dialog.destroy()
                except ValueError:
                    messagebox.showerror("Invalid Input",
                                         "Please enter a positive integer.",
                                         parent=dialog)

            def on_n_cancel():
                dialog.destroy()

            bf = tk.Frame(dialog, bg=Colors.BG_PRIMARY)
            bf.pack(pady=12)
            tk.Button(bf, text="Preview", command=on_n_confirm,
                      bg=Colors.BUTTON_SECONDARY, fg='white',
                      relief=tk.FLAT, width=10).pack(side=tk.LEFT, padx=6)
            tk.Button(bf, text="Cancel", command=on_n_cancel,
                      bg=Colors.BUTTON_NEUTRAL, fg='white',
                      relief=tk.FLAT, width=10).pack(side=tk.LEFT, padx=6)

            dialog.bind('<Return>', lambda e: on_n_confirm())
            dialog.bind('<Escape>', lambda e: on_n_cancel())
            self.root.wait_window(dialog)

            n = n_holder[0]
            if n is None:
                return  # user cancelled

            # ── Step 2: compute top-N candidates ──────────────────────────
            active = self.data_manager.get_active_images()
            sorted_active = sorted(
                active,
                key=lambda img: (
                    self.data_manager.image_stats[img].get('current_tier', 0),
                    self.data_manager.image_stats[img].get('wins', 0)
                ),
                reverse=True
            )
            candidates = sorted_active[:n]

            # Build (name, tier, votes, wins) tuples for the preview window
            image_list = []
            for img in candidates:
                s = self.data_manager.image_stats[img]
                image_list.append((
                    img,
                    s.get('current_tier', 0),
                    s.get('votes', 0),
                    s.get('wins', 0),
                ))

            # ── Step 3: open preview window; export runs in the callback ──
            def _do_export(selected_names: list):
                """Called by ExportPreviewWindow after the user clicks Export."""
                try:
                    export_folder = os.path.join(
                        self.data_manager.image_folder, 'Exports')
                    confirm = messagebox.askyesno(
                        "Confirm Export",
                        f"Export {len(selected_names)} image(s) to:\n"
                        f"{export_folder}\n\n"
                        f"• Their votes will be removed from remaining images\n"
                        f"• They will be fully removed from the ranking data\n\n"
                        f"This cannot be undone. Continue?"
                    )
                    if not confirm:
                        return

                    print(f"MainWindow: Exporting {len(selected_names)} selected images…")

                    exported = self.data_manager.export_specific_images(selected_names)
                    if not exported:
                        messagebox.showinfo("Nothing Exported", "No images were exported.")
                        return

                    exporter = ImageExporter(self.data_manager.image_folder)
                    moved_ok, move_errors = 0, []
                    for img_name in exported:
                        ok, err = exporter.move_image_to_exports(img_name)
                        if ok:
                            moved_ok += 1
                        else:
                            move_errors.append(f"{img_name}: {err}")

                    # Refresh UI
                    ui_refs = self.ui_builder.get_ui_references()
                    new_active = self.data_manager.get_active_image_count()
                    new_binned = self.data_manager.get_binned_image_count()
                    ui_refs['stats_label'].config(
                        text=f"Votes: {self.data_manager.vote_count} "
                             f"| Active: {new_active} | Binned: {new_binned}")
                    if ui_refs.get('status_bar'):
                        ui_refs['status_bar'].config(
                            text=f"Exported {moved_ok} image(s). "
                                 f"{new_active} active images remain.")

                    if self.voting_controller:
                        self.voting_controller.show_next_pair()

                    summary = (f"Exported {moved_ok} of {len(exported)} image(s) to:\n"
                               f"{exporter.export_folder}\n\n"
                               f"Active images remaining: {new_active}\n\n"
                               f"Save your progress to persist these changes.")
                    if move_errors:
                        summary += (f"\n\nFile move errors ({len(move_errors)}):\n"
                                    + "\n".join(move_errors[:5]))
                    messagebox.showinfo("Export Complete", summary)
                    print(f"MainWindow: Export complete — {moved_ok}/{len(exported)} files moved.")

                except Exception as e:
                    print(f"MainWindow: Error in export callback: {e}")
                    import traceback; traceback.print_exc()
                    messagebox.showerror("Export Error",
                                         f"Failed to export images:\n{str(e)}")

            ExportPreviewWindow(
                self.root,
                self.data_manager.image_folder,
                image_list,
                on_confirm=_do_export,
            )

        except Exception as e:
            print(f"MainWindow: Error opening export preview: {e}")
            import traceback; traceback.print_exc()
            messagebox.showerror("Export Error",
                                 f"Failed to open export preview:\n{str(e)}")

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
                    
                    # Load similarity cache if one exists for this folder
                    if self.data_manager.image_folder:
                        sm = self.data_manager.similarity_manager
                        sm.load_cache(self.data_manager.image_folder)
                    
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
                    
                    # Report similarity index status and auto-index if needed
                    sm = self.data_manager.similarity_manager
                    all_images = list(self.data_manager.image_stats.keys())
                    folder = self.data_manager.image_folder
                    ui_refs = self.ui_builder.get_ui_references()

                    if sm.is_ready and not getattr(sm, 'is_legacy', False):
                        missing = sm.count_missing(all_images)
                        if missing == 0:
                            sim_msg = (f"Similarity index loaded "
                                       f"({len(sm.filenames)} embeddings — all images covered).")
                            print(f"MainWindow: {sim_msg}")
                            if ui_refs.get('status_bar'):
                                ui_refs['status_bar'].config(text=sim_msg)
                        else:
                            sim_msg = (f"Similarity index loaded ({len(sm.filenames)} embeddings) — "
                                       f"{missing} new image(s) found, updating index in background…")
                            print(f"MainWindow: {sim_msg}")
                            if ui_refs.get('status_bar'):
                                ui_refs['status_bar'].config(text=sim_msg)
                            self._auto_update_similarity_index(folder, all_images)
                    elif sm.is_ready and getattr(sm, 'is_legacy', False):
                        sim_msg = (f"Legacy similarity index found ({len(sm.filenames)} visual-only embeddings) — "
                                   f"upgrading to full hybrid index in background…")
                        print(f"MainWindow: {sim_msg}")
                        if ui_refs.get('status_bar'):
                            ui_refs['status_bar'].config(text=sim_msg)
                        self._auto_build_similarity_index(folder, all_images)
                    else:
                        sim_msg = (f"No similarity index found — "
                                   f"building index for {len(all_images)} images in background…")
                        print(f"MainWindow: {sim_msg}")
                        if ui_refs.get('status_bar'):
                            ui_refs['status_bar'].config(text=sim_msg)
                        self._auto_build_similarity_index(folder, all_images)
                    
                    print(f"MainWindow: Data loaded successfully")
                else:
                    print(f"MainWindow: Failed to load data from {filename}: {error_msg}")
        except Exception as e:
            print(f"MainWindow: Error loading data: {e}")
            messagebox.showerror("Load Error", f"Failed to load data:\n{str(e)}")
    
    def _auto_build_similarity_index(self, folder: str, image_names: list) -> None:
        """Kick off a full similarity index build in the background (no UI prompts)."""
        sm = self.data_manager.similarity_manager
        ui_refs = self.ui_builder.get_ui_references()
        status_bar = ui_refs.get('status_bar')

        prompt_lookup = {
            name: (self.data_manager.image_stats.get(name, {}).get('prompt') or '')
            for name in image_names
        }

        def progress(current, total, name):
            if current % 25 == 0 or current == total:
                pct = int(current / max(total, 1) * 100)
                msg = (f"Building similarity index: {current}/{total} ({pct}%)…"
                       if name != "done" else "")
                print(f"[SimilarityManager] {msg}")
                if status_bar:
                    self.root.after(0, lambda m=msg: status_bar.config(text=m) if m else None)

        def completion(success, message):
            print(f"[SimilarityManager] Auto-build complete: {message}")
            if success:
                # Invalidate the CLIP filter index so it is rebuilt from the
                # freshly populated prompt_tags on next filter panel access.
                self.filter_manager.invalidate_clip_index()
            if status_bar:
                final = (f"✅ Similarity index built ({len(sm.filenames)} embeddings). "
                         f"Visual similarity pairing is now active."
                         if success else
                         f"⚠️ Similarity index build failed: {message}")
                self.root.after(0, lambda: status_bar.config(text=final))

        sm.build_index_async(folder, image_names, prompt_lookup, progress, completion)

    def _auto_update_similarity_index(self, folder: str, image_names: list) -> None:
        """Kick off an incremental index update in the background (no UI prompts)."""
        sm = self.data_manager.similarity_manager
        ui_refs = self.ui_builder.get_ui_references()
        status_bar = ui_refs.get('status_bar')

        prompt_lookup = {
            name: (self.data_manager.image_stats.get(name, {}).get('prompt') or '')
            for name in image_names
        }

        def progress(current, total, name):
            if current % 25 == 0 or current == total:
                pct = int(current / max(total, 1) * 100)
                msg = (f"Updating similarity index: {current}/{total} ({pct}%)…"
                       if name != "done" else "")
                print(f"[SimilarityManager] {msg}")
                if status_bar:
                    self.root.after(0, lambda m=msg: status_bar.config(text=m) if m else None)

        def completion(success, message):
            print(f"[SimilarityManager] Auto-update complete: {message}")
            if success:
                # Invalidate the CLIP filter index so new tags are picked up
                # on next filter panel access.
                self.filter_manager.invalidate_clip_index()
            if status_bar:
                final = (f"✅ Similarity index updated ({len(sm.filenames)} embeddings total). "
                         f"Visual similarity pairing is now active."
                         if success else
                         f"⚠️ Similarity index update failed: {message}")
                self.root.after(0, lambda: status_bar.config(text=final))

        sm.update_index_async(folder, image_names, prompt_lookup, progress, completion)

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