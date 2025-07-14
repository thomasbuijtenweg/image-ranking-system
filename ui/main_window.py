"""
Main window module for the Image Ranking System.

This module implements the primary user interface for image voting,
including the side-by-side image display, voting controls, and
integration with all the core system components.

Now includes performance optimizations for large image collections:
- Lazy metadata extraction
- Background processing
- Progress feedback
- Memory management improvements
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Tuple
import os
import gc
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from config import Colors, Defaults, KeyBindings
from core.data_manager import DataManager
from core.image_processor import ImageProcessor
from core.ranking_algorithm import RankingAlgorithm
from core.prompt_analyzer import PromptAnalyzer
from ui.stats_window import StatsWindow
from ui.settings_window import SettingsWindow


class MainWindow:
    """
    Main application window handling the voting interface with performance optimizations.
    
    This class manages the primary user interface where users compare
    and vote on image pairs. It coordinates between the data manager,
    image processor, and ranking algorithm to provide a smooth voting experience.
    Now optimized for large collections (10,000+ images).
    """
    
    def __init__(self, root: tk.Tk):
        """
        Initialize the main window.
        
        Args:
            root: The root tkinter window
        """
        self.root = root
        self.root.title("Image Ranking System")
        self.root.geometry(f"{Defaults.WINDOW_WIDTH}x{Defaults.WINDOW_HEIGHT}")
        self.root.minsize(800, 600)  # Set minimum window size to prevent cramped layout
        self.root.configure(bg=Colors.BG_PRIMARY)
        
        # Initialize core components
        self.data_manager = DataManager()
        self.image_processor = ImageProcessor()
        self.ranking_algorithm = RankingAlgorithm(self.data_manager)
        self.prompt_analyzer = PromptAnalyzer(self.data_manager)
        
        # Performance optimization: Background processing
        self.metadata_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="metadata")
        self.metadata_futures = {}  # Track background metadata extraction
        self.loading_cancelled = False
        
        # UI state
        self.current_pair = (None, None)
        self.next_pair = (None, None)
        self.next_pair_images = {'left': None, 'right': None}
        self.previous_pair = (None, None)
        
        # Current displayed images (keep references to prevent garbage collection)
        self.current_images = {'left': None, 'right': None}
        
        # Window references to prevent multiple instances
        self.stats_window = None
        self.settings_window = None
        
        # Timer references
        self.resize_timer = None
        self.preload_timer = None
        
        # Progress tracking
        self.progress_window = None
        self.progress_var = None
        self.progress_label_var = None
        
        # Setup the user interface
        self.setup_dark_theme()
        self.create_widgets()
        self.setup_key_bindings()
        
        # Bind window events
        self.root.bind('<Configure>', self.on_window_resize)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Handle platform-specific window maximization
        self.maximize_window()
    
    def maximize_window(self):
        """Maximize the window in a platform-independent way."""
        try:
            self.root.state('zoomed')  # Windows
        except tk.TclError:
            try:
                self.root.attributes('-zoomed', True)  # Linux
            except tk.TclError:
                # macOS or other platforms - just make it large
                self.root.geometry("1200x800")
    
    def setup_dark_theme(self):
        """Configure ttk styles for dark mode."""
        style = ttk.Style()
        
        try:
            style.theme_use('clam')  # clam theme works better for customization
        except:
            pass
        
        # Configure Treeview for dark mode
        style.configure("Treeview",
                       background=Colors.BG_SECONDARY,
                       foreground=Colors.TEXT_PRIMARY,
                       fieldbackground=Colors.BG_SECONDARY,
                       borderwidth=0,
                       selectbackground=Colors.BUTTON_HOVER,
                       selectforeground=Colors.TEXT_PRIMARY)
        
        style.configure("Treeview.Heading",
                       background=Colors.BUTTON_BG,
                       foreground=Colors.TEXT_PRIMARY,
                       borderwidth=1,
                       relief=tk.FLAT,
                       font=('Arial', 10, 'bold'))
        
        # Configure other ttk widgets
        style.configure("TNotebook", background=Colors.BG_PRIMARY, borderwidth=0)
        style.configure("TNotebook.Tab", 
                       background=Colors.BUTTON_BG,
                       foreground=Colors.TEXT_PRIMARY,
                       padding=[20, 10],
                       borderwidth=0,
                       focuscolor='none')
    
    def create_widgets(self):
        """Create and arrange all UI widgets."""
        # Top frame for controls and stats
        self.create_top_frame()
        
        # Main voting area
        self.create_main_frame()
        
        # Bottom status bar
        self.create_status_bar()
    
    def create_top_frame(self):
        """Create the top frame with buttons and status information."""
        top_frame = tk.Frame(self.root, bg=Colors.BG_PRIMARY)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create control buttons
        self.create_control_buttons(top_frame)
        
        # Folder and stats labels
        self.folder_label = tk.Label(top_frame, text="No folder selected", 
                                   fg=Colors.TEXT_SECONDARY, bg=Colors.BG_PRIMARY)
        self.folder_label.pack(side=tk.LEFT, padx=20)
        
        self.stats_label = tk.Label(top_frame, text="Total votes: 0", 
                                  font=('Arial', 10, 'bold'), 
                                  fg=Colors.TEXT_PRIMARY, bg=Colors.BG_PRIMARY)
        self.stats_label.pack(side=tk.RIGHT, padx=10)
    
    def create_control_buttons(self, parent):
        """Create the control buttons in the top frame."""
        buttons = [
            ("Select Image Folder", self.select_folder, Colors.BUTTON_SUCCESS),
            ("Save Progress", self.save_data, Colors.BUTTON_INFO),
            ("Load Progress", self.load_data, Colors.BUTTON_INFO),
            ("View Stats", self.show_detailed_stats, Colors.BUTTON_WARNING),
            ("Prompt Analysis", self.show_prompt_analysis, Colors.BUTTON_INFO),
            ("Settings", self.show_settings, Colors.BUTTON_NEUTRAL)
        ]
        
        for text, command, color in buttons:
            tk.Button(parent, text=text, command=command, 
                     bg=color, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
    
    def create_main_frame(self):
        """Create the main voting area with image display."""
        main_frame = tk.Frame(self.root, bg=Colors.BG_PRIMARY)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure grid weights for equal distribution with minimum sizes
        main_frame.grid_columnconfigure(0, weight=1, uniform="equal", minsize=400)
        main_frame.grid_columnconfigure(1, weight=0, minsize=80)  # VS label column
        main_frame.grid_columnconfigure(2, weight=1, uniform="equal", minsize=400)
        main_frame.grid_rowconfigure(0, weight=1, minsize=500)
        
        # Create left and right image frames
        self.create_image_frame(main_frame, 'left', 0)
        self.create_vs_label(main_frame)
        self.create_image_frame(main_frame, 'right', 2)
    
    def create_image_frame(self, parent, side: str, column: int):
        """Create an image display frame for one side of the comparison."""
        frame = tk.Frame(parent, relief=tk.RAISED, borderwidth=2, bg=Colors.BG_SECONDARY)
        frame.grid(row=0, column=column, sticky="nsew", padx=5)
        
        # Configure frame grid - text areas have fixed minimum sizes
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1, minsize=400)     # Image - expandable with minimum
        frame.grid_rowconfigure(1, weight=0, minsize=30)     # Info - fixed minimum
        frame.grid_rowconfigure(2, weight=0, minsize=60)     # Metadata - fixed minimum
        frame.grid_rowconfigure(3, weight=0, minsize=60)     # Vote button - fixed minimum
        
        # Image display label - expandable, takes most space
        image_label = tk.Label(frame, text="No image", 
                              bg=Colors.BG_TERTIARY, fg=Colors.TEXT_PRIMARY, cursor="hand2")
        image_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        image_label.bind("<Button-1>", lambda e: self.vote(side))
        
        # Info label showing stats - fixed minimum height
        info_label = tk.Label(frame, text="", font=('Arial', 10), 
                             fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY, height=2)
        info_label.grid(row=1, column=0, sticky="ew", pady=2)
        
        # Metadata label - fixed minimum height with text wrapping
        metadata_label = tk.Label(frame, text="", font=('Arial', 10), 
                                 fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY, 
                                 justify=tk.LEFT, height=3)
        metadata_label.grid(row=2, column=0, sticky="ew", padx=10, pady=2)
        
        # Vote button - fixed height
        arrow = "←" if side == 'left' else "→"
        vote_button = tk.Button(frame, text=f"Vote for this image ({arrow})", 
                               command=lambda: self.vote(side), 
                               state=tk.DISABLED, font=('Arial', 12, 'bold'),
                               bg=Colors.BUTTON_SUCCESS, fg='white', height=2, relief=tk.FLAT)
        vote_button.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        
        # Store references
        if side == 'left':
            self.left_image_label = image_label
            self.left_info_label = info_label
            self.left_metadata_label = metadata_label
            self.left_vote_button = vote_button
        else:
            self.right_image_label = image_label
            self.right_info_label = info_label
            self.right_metadata_label = metadata_label
            self.right_vote_button = vote_button
    
    def create_vs_label(self, parent):
        """Create the VS label in the center of the main frame."""
        vs_label = tk.Label(parent, text="VS", font=('Arial', 24, 'bold'), 
                          fg=Colors.TEXT_PRIMARY, bg=Colors.BG_PRIMARY)
        vs_label.grid(row=0, column=1, padx=20)
    
    def create_status_bar(self):
        """Create the status bar at the bottom of the window."""
        self.status_bar = tk.Label(self.root, text="Select a folder to begin", 
                                 relief=tk.SUNKEN, anchor=tk.W, 
                                 bg=Colors.BUTTON_BG, fg=Colors.TEXT_PRIMARY)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_key_bindings(self):
        """Setup keyboard shortcuts."""
        # Voting shortcuts
        for key in KeyBindings.VOTE_LEFT:
            self.root.bind(key, lambda e: self.vote('left') if self.left_vote_button['state'] == tk.NORMAL else None)
        
        for key in KeyBindings.VOTE_RIGHT:
            self.root.bind(key, lambda e: self.vote('right') if self.right_vote_button['state'] == tk.NORMAL else None)
        
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
    
    def on_window_resize(self, event):
        """Handle window resize events with debouncing."""
        if event.widget == self.root:
            # Cancel previous timer if it exists
            if self.resize_timer:
                self.root.after_cancel(self.resize_timer)
            
            # Set a new timer to redraw images after resize stops
            self.resize_timer = self.root.after(Defaults.RESIZE_DEBOUNCE_MS, self.refresh_current_images)
    
    def refresh_current_images(self):
        """Refresh the currently displayed images with new size."""
        if self.current_pair[0] and self.current_pair[1]:
            self.display_image(self.current_pair[0], 'left')
            self.display_image(self.current_pair[1], 'right')
    
    def clear_old_images(self):
        """Clear old image references to help with garbage collection."""
        # Clear current displayed images
        self.current_images['left'] = None
        self.current_images['right'] = None
        
        # Clear preloaded images
        self.next_pair_images['left'] = None
        self.next_pair_images['right'] = None
        
        # Force garbage collection
        gc.collect()
    
    def select_folder(self):
        """Handle folder selection for image loading."""
        folder = filedialog.askdirectory(title="Select folder containing images (includes subfolders)")
        if folder:
            # Clear old images before loading new ones
            self.clear_old_images()
            
            self.data_manager.image_folder = folder
            self.load_images()
    
    def load_images(self):
        """Load images from the selected folder with optimized performance."""
        if not self.data_manager.image_folder:
            return
            
        # Quick file scan first (fast)
        start_time = time.time()
        images = self.image_processor.get_image_files(self.data_manager.image_folder)
        scan_time = time.time() - start_time
        
        if not images:
            messagebox.showerror("Error", "No images found in selected folder or its subfolders")
            return
        
        print(f"File scan completed in {scan_time:.2f}s for {len(images)} images")
        
        # Update folder label immediately
        folder_name = os.path.basename(self.data_manager.image_folder)
        self.folder_label.config(text=f"Folder: {folder_name} ({len(images)} images including subfolders)")
        
        # Show progress window for large collections
        if len(images) > 100:
            self.show_progress_window(len(images))
        
        # Initialize basic stats for all images (fast - no metadata extraction)
        processed_count = 0
        for img in images:
            self.data_manager.initialize_image_stats(img)
            processed_count += 1
            
            # Update progress for every 100 images or at the end
            if processed_count % 100 == 0 or processed_count == len(images):
                if self.progress_var:
                    self.progress_var.set(processed_count)
                    self.progress_label_var.set(f"Initializing: {processed_count}/{len(images)}")
                    self.root.update_idletasks()
        
        # Close progress window
        if self.progress_window:
            self.progress_window.destroy()
            self.progress_window = None
        
        # Start background metadata extraction for images that need it
        self.start_background_metadata_extraction(images)
        
        # Update status and show first pair immediately
        self.status_bar.config(text=f"Loaded {len(images)} images. Metadata extraction running in background. Ready to vote!")
        self.show_next_pair()
    
    def start_background_metadata_extraction(self, images):
        """Start background metadata extraction for images without metadata."""
        images_needing_metadata = []
        
        for img in images:
            stats = self.data_manager.get_image_stats(img)
            if stats.get('prompt') is None and stats.get('display_metadata') is None:
                images_needing_metadata.append(img)
        
        if not images_needing_metadata:
            print("No images need metadata extraction")
            return
        
        print(f"Starting background metadata extraction for {len(images_needing_metadata)} images")
        
        # Submit metadata extraction tasks
        for img in images_needing_metadata:
            if not self.loading_cancelled:
                future = self.metadata_executor.submit(self.extract_metadata_for_image, img)
                self.metadata_futures[future] = img
        
        # Start a thread to collect results
        threading.Thread(target=self.collect_metadata_results, daemon=True).start()
    
    def extract_metadata_for_image(self, img_filename):
        """Extract metadata for a single image (runs in background thread)."""
        try:
            img_path = os.path.join(self.data_manager.image_folder, img_filename)
            
            # Extract prompt and metadata
            prompt = self.image_processor.extract_prompt_from_image(img_path)
            metadata = self.image_processor.get_image_metadata(img_path)
            
            return img_filename, prompt, metadata
            
        except Exception as e:
            print(f"Error extracting metadata from {img_filename}: {e}")
            return img_filename, None, None
    
    def collect_metadata_results(self):
        """Collect metadata extraction results from background threads."""
        completed_count = 0
        total_count = len(self.metadata_futures)
        
        for future in as_completed(self.metadata_futures):
            if self.loading_cancelled:
                break
                
            try:
                img_filename, prompt, metadata = future.result()
                
                # Update data manager on main thread
                self.root.after(0, lambda f=img_filename, p=prompt, m=metadata: 
                               self.data_manager.set_image_metadata(f, p, m))
                
                completed_count += 1
                
                # Update status periodically
                if completed_count % 50 == 0 or completed_count == total_count:
                    progress_text = f"Background metadata extraction: {completed_count}/{total_count} completed"
                    self.root.after(0, lambda t=progress_text: self.status_bar.config(text=t))
                    
            except Exception as e:
                print(f"Error collecting metadata result: {e}")
        
        # Clear futures dict
        self.metadata_futures.clear()
        
        if not self.loading_cancelled:
            final_text = f"Metadata extraction complete for {total_count} images. Ready to vote!"
            self.root.after(0, lambda: self.status_bar.config(text=final_text))
    
    def show_progress_window(self, total_images):
        """Show a progress window for long operations."""
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("Loading Images...")
        self.progress_window.geometry("400x150")
        self.progress_window.configure(bg=Colors.BG_PRIMARY)
        self.progress_window.transient(self.root)
        self.progress_window.grab_set()
        
        # Center the window
        self.progress_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 200,
            self.root.winfo_rooty() + 200
        ))
        
        # Progress label
        self.progress_label_var = tk.StringVar(value="Scanning folder...")
        label = tk.Label(self.progress_window, textvariable=self.progress_label_var,
                        font=('Arial', 12), fg=Colors.TEXT_PRIMARY, bg=Colors.BG_PRIMARY)
        label.pack(pady=20)
        
        # Progress bar
        self.progress_var = tk.IntVar()
        progress_bar = ttk.Progressbar(self.progress_window, variable=self.progress_var,
                                     maximum=total_images, length=350)
        progress_bar.pack(pady=10)
        
        # Cancel button
        tk.Button(self.progress_window, text="Cancel", 
                 command=self.cancel_loading,
                 bg=Colors.BUTTON_DANGER, fg='white', relief=tk.FLAT).pack(pady=10)
    
    def cancel_loading(self):
        """Cancel the loading process."""
        self.loading_cancelled = True
        
        # Cancel all pending metadata futures
        for future in self.metadata_futures:
            future.cancel()
        self.metadata_futures.clear()
        
        if self.progress_window:
            self.progress_window.destroy()
            self.progress_window = None
        
        self.status_bar.config(text="Loading cancelled")
    
    def get_image_metadata_lazy(self, img_filename):
        """Get metadata for an image, extracting it if not available."""
        stats = self.data_manager.get_image_stats(img_filename)
        
        # If we already have metadata, return it
        if stats.get('prompt') is not None or stats.get('display_metadata') is not None:
            return stats.get('prompt'), stats.get('display_metadata')
        
        # If metadata extraction is in progress, return None (will be updated later)
        for future in self.metadata_futures:
            if self.metadata_futures[future] == img_filename:
                return None, "Metadata loading..."
        
        # If no extraction in progress, extract synchronously for critical images
        try:
            img_path = os.path.join(self.data_manager.image_folder, img_filename)
            prompt = self.image_processor.extract_prompt_from_image(img_path)
            metadata = self.image_processor.get_image_metadata(img_path)
            
            # Update data manager
            self.data_manager.set_image_metadata(img_filename, prompt, metadata)
            
            return prompt, metadata
            
        except Exception as e:
            print(f"Error extracting metadata for {img_filename}: {e}")
            return None, f"Error: {str(e)}"
    
    def show_next_pair(self):
        """Display the next pair of images for voting."""
        if self.data_manager.image_folder == "":
            return
        
        # Get available images
        images = self.image_processor.get_image_files(self.data_manager.image_folder)
        if len(images) < 2:
            return
        
        # Clear old images before loading new ones
        self.clear_old_images()
        
        # Store current pair as previous
        if self.current_pair[0] and self.current_pair[1]:
            self.previous_pair = self.current_pair
        
        # Get next pair using ranking algorithm with separate weights
        img1, img2 = self.ranking_algorithm.select_next_pair(images, self.previous_pair)
        if not img1 or not img2:
            return
        
        self.current_pair = (img1, img2)
        
        # Display images
        self.display_image(img1, 'left')
        self.display_image(img2, 'right')
        
        # Enable voting buttons
        self.left_vote_button.config(state=tk.NORMAL)
        self.right_vote_button.config(state=tk.NORMAL)
        
        # Update status with explanation
        explanation = self.ranking_algorithm.get_selection_explanation(img1, img2)
        self.status_bar.config(text=explanation)
        
        # Cancel any existing preload timer
        if self.preload_timer:
            self.root.after_cancel(self.preload_timer)
        
        # Preload next pair in background
        self.preload_timer = self.root.after(Defaults.PRELOAD_DELAY_MS, self.preload_next_pair)
    
    def preload_next_pair(self):
        """Preload the next pair of images in the background."""
        if self.data_manager.image_folder == "":
            return
        
        images = self.image_processor.get_image_files(self.data_manager.image_folder)
        if len(images) < 2:
            return
        
        # Get next pair (excluding current pair)
        self.next_pair = self.ranking_algorithm.select_next_pair(images, self.current_pair)
        
        if self.next_pair[0] and self.next_pair[1]:
            # Clear old preloaded images
            self.next_pair_images = {'left': None, 'right': None}
            
            try:
                # Calculate display dimensions
                self.root.update_idletasks()
                window_width = self.root.winfo_width()
                window_height = self.root.winfo_height()
                max_image_width = max((window_width - 150) // 2, Defaults.MIN_IMAGE_WIDTH)
                max_image_height = max(window_height - 300, Defaults.MIN_IMAGE_HEIGHT)
                
                # Preload images
                for idx, filename in enumerate(self.next_pair):
                    img_path = os.path.join(self.data_manager.image_folder, filename)
                    photo = self.image_processor.load_and_resize_image(
                        img_path, max_image_width, max_image_height)
                    
                    if photo:
                        side = 'left' if idx == 0 else 'right'
                        self.next_pair_images[side] = photo
                        
            except Exception as e:
                print(f"Error preloading images: {e}")
                # Clear partially loaded images to prevent memory issues
                self.next_pair_images = {'left': None, 'right': None}
    
    def display_image(self, filename: str, side: str):
        """Display an image on the specified side."""
        try:
            img_path = os.path.join(self.data_manager.image_folder, filename)
            
            # Force window to update and get actual dimensions
            self.root.update_idletasks()
            
            # Get the actual size of the image label area after layout
            if side == 'left':
                label_width = self.left_image_label.winfo_width()
                label_height = self.left_image_label.winfo_height()
            else:
                label_width = self.right_image_label.winfo_width()
                label_height = self.right_image_label.winfo_height()
            
            # Only proceed if we have valid dimensions (widget has been rendered)
            if label_width <= 1 or label_height <= 1:
                # Widget not yet rendered, try again after a short delay
                self.root.after(100, lambda: self.display_image(filename, side))
                return
            
            # Use almost all available space, leaving small margin, but with reasonable minimums
            max_image_width = max(label_width - 20, 300)
            max_image_height = max(label_height - 20, 300)
            
            # Load and resize image to fill the available space
            photo = self.image_processor.load_and_resize_image(
                img_path, max_image_width, max_image_height)
            
            if photo:
                # Update image display
                if side == 'left':
                    self.left_image_label.config(image=photo, text="")
                    self.current_images['left'] = photo  # Keep reference
                else:
                    self.right_image_label.config(image=photo, text="")
                    self.current_images['right'] = photo  # Keep reference
                
                # Update info and metadata
                self.update_image_info(filename, side)
            else:
                # Handle image loading failure
                if side == 'left':
                    self.left_image_label.config(image="", text="Failed to load image")
                    self.current_images['left'] = None
                else:
                    self.right_image_label.config(image="", text="Failed to load image")
                    self.current_images['right'] = None
            
        except Exception as e:
            error_msg = f"Could not load image {filename}: {str(e)}"
            print(error_msg)
            messagebox.showerror("Error", error_msg)
            
            # Clear the image display for this side
            if side == 'left':
                self.left_image_label.config(image="", text="Error loading image")
                self.current_images['left'] = None
            else:
                self.right_image_label.config(image="", text="Error loading image")
                self.current_images['right'] = None
    
    def update_image_info(self, filename: str, side: str):
        """Update the info and metadata labels for an image with lazy loading."""
        stats = self.data_manager.get_image_stats(filename)
        
        # Calculate individual stability
        stability = self.ranking_algorithm._calculate_tier_stability(filename)
        
        # Create info text with indication of selection weights used
        weight_indicator = "(Left weights)" if side == 'left' else "(Right weights)"
        info_text = (f"Tier: {stats.get('current_tier', 0)} | "
                    f"Wins: {stats.get('wins', 0)} | "
                    f"Losses: {stats.get('losses', 0)} | "
                    f"Stability: {stability:.2f} {weight_indicator}")
        
        # Get prompt with lazy loading - only extract when actually needed
        prompt = stats.get('prompt')
        if prompt is None:
            # Extract metadata on-demand for this specific image
            try:
                img_path = os.path.join(self.data_manager.image_folder, filename)
                prompt = self.image_processor.extract_prompt_from_image(img_path)
                # Also get display metadata while we're at it
                display_metadata = self.image_processor.get_image_metadata(img_path)
                self.data_manager.set_image_metadata(filename, prompt, display_metadata)
            except Exception as e:
                print(f"Error extracting metadata from {filename}: {e}")
                prompt = None
        
        # Format prompt text
        if prompt:
            # Extract only the main/positive prompt using the prompt analyzer
            main_prompt = self.prompt_analyzer.extract_main_prompt(prompt)
            if main_prompt:
                prompt_text = f"Prompt: {main_prompt}"
            else:
                prompt_text = "Prompt: (empty or unreadable)"
        else:
            prompt_text = "Prompt: No prompt found"
        
        # Update labels with dynamic wraplength
        if side == 'left':
            self.left_info_label.config(text=info_text)
            try:
                self.root.update_idletasks()
                frame_width = self.left_metadata_label.winfo_width()
                if frame_width > 100:  # Only update if frame has been rendered
                    self.left_metadata_label.config(text=prompt_text, wraplength=max(frame_width - 20, 300))
                else:
                    self.left_metadata_label.config(text=prompt_text, wraplength=400)
            except:
                self.left_metadata_label.config(text=prompt_text, wraplength=400)
        else:
            self.right_info_label.config(text=info_text)
            try:
                self.root.update_idletasks()
                frame_width = self.right_metadata_label.winfo_width()
                if frame_width > 100:  # Only update if frame has been rendered
                    self.right_metadata_label.config(text=prompt_text, wraplength=max(frame_width - 20, 300))
                else:
                    self.right_metadata_label.config(text=prompt_text, wraplength=400)
            except:
                self.right_metadata_label.config(text=prompt_text, wraplength=400)
    
    def vote(self, side: str):
        """Process a vote for the specified side."""
        if not self.current_pair[0] or not self.current_pair[1]:
            return
        
        winner = self.current_pair[0] if side == 'left' else self.current_pair[1]
        loser = self.current_pair[1] if side == 'left' else self.current_pair[0]
        
        # Record the vote
        self.data_manager.record_vote(winner, loser)
        
        # Invalidate cached rankings
        self.ranking_algorithm.invalidate_cache()
        
        # Update UI
        self.stats_label.config(text=f"Total votes: {self.data_manager.vote_count}")
        self.status_bar.config(text=f"Vote recorded: {winner} wins over {loser}")
        
        # Disable buttons temporarily
        self.left_vote_button.config(state=tk.DISABLED)
        self.right_vote_button.config(state=tk.DISABLED)
        
        # Show next pair after delay
        self.root.after(Defaults.VOTE_DELAY_MS, self.show_next_pair)
    
    def save_data(self):
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
    
    def load_data(self):
        """Load ranking data from file."""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            success, error_msg = self.data_manager.load_from_file(filename)
            if success:
                # Clear old images before loading new ones
                self.clear_old_images()
                
                # Reload images from folder
                self.load_images()
                
                # Update UI
                self.stats_label.config(text=f"Total votes: {self.data_manager.vote_count}")
                
                # Check if separate weights were loaded
                left_weights = self.data_manager.get_left_weights()
                right_weights = self.data_manager.get_right_weights()
                weights_message = ""
                if left_weights != right_weights:
                    weights_message = "\n\nLoaded separate left and right selection weights."
                else:
                    weights_message = "\n\nUsing same weights for both left and right selection."
                
                messagebox.showinfo("Success", f"Data loaded from {filename}{weights_message}")
            else:
                messagebox.showerror("Error", f"Could not load data: {error_msg}")
    
    def show_detailed_stats(self):
        """Show the detailed statistics window."""
        if not self.data_manager.image_stats:
            messagebox.showinfo("No Data", "No image data to display. Please load images first.")
            return
        
        if self.stats_window is None:
            self.stats_window = StatsWindow(self.root, self.data_manager, self.ranking_algorithm, self.prompt_analyzer)
        else:
            self.stats_window.show()
    
    def show_prompt_analysis(self):
        """Show the prompt analysis functionality in the stats window."""
        if not self.data_manager.image_stats:
            messagebox.showinfo("No Data", "No image data to display. Please load images first.")
            return
        
        # Check if there are any prompts to analyze
        prompt_count = sum(1 for stats in self.data_manager.image_stats.values() 
                          if stats.get('prompt'))
        
        if prompt_count == 0:
            messagebox.showinfo("No Prompts", "No AI generation prompts found in the images. "
                              "Prompt analysis requires images with embedded prompt metadata.")
            return
        
        # Show the stats window and focus on prompt analysis tab
        if self.stats_window is None:
            self.stats_window = StatsWindow(self.root, self.data_manager, self.ranking_algorithm, self.prompt_analyzer)
        else:
            self.stats_window.show()
            # Focus on prompt analysis tab if it exists
            self.stats_window.focus_prompt_analysis_tab()
    
    def show_settings(self):
        """Show the settings window."""
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self.root, self.data_manager)
        else:
            self.settings_window.show()
    
    def on_closing(self):
        """Handle application closing with cleanup."""
        # Cancel any ongoing metadata extraction
        self.loading_cancelled = True
        
        # Cancel all pending metadata futures
        for future in self.metadata_futures:
            future.cancel()
        self.metadata_futures.clear()
        
        # Shutdown the metadata executor
        self.metadata_executor.shutdown(wait=False)
        
        # Cancel any pending timers
        if self.resize_timer:
            self.root.after_cancel(self.resize_timer)
        if self.preload_timer:
            self.root.after_cancel(self.preload_timer)
        
        # Close progress window if open
        if self.progress_window:
            self.progress_window.destroy()
        
        # Clear all image references
        self.clear_old_images()
        
        # Clean up image processor resources
        self.image_processor.cleanup_resources()
        
        # Destroy the window
        self.root.destroy()
