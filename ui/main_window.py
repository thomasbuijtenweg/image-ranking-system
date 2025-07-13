"""
Main window module for the Image Ranking System.

This module implements the primary user interface for image voting,
including the side-by-side image display, voting controls, and
integration with all the core system components.

By separating this UI logic from the core business logic, we make
the application more maintainable and easier to test.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Tuple
import os
import gc

from config import Colors, Defaults, KeyBindings
from core.data_manager import DataManager
from core.image_processor import ImageProcessor
from core.ranking_algorithm import RankingAlgorithm
from ui.rankings_window import RankingsWindow
from ui.stats_window import StatsWindow
from ui.settings_window import SettingsWindow


class MainWindow:
    """
    Main application window handling the voting interface.
    
    This class manages the primary user interface where users compare
    and vote on image pairs. It coordinates between the data manager,
    image processor, and ranking algorithm to provide a smooth voting experience.
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
        self.root.configure(bg=Colors.BG_PRIMARY)
        
        # Initialize core components
        self.data_manager = DataManager()
        self.image_processor = ImageProcessor()
        self.ranking_algorithm = RankingAlgorithm(self.data_manager)
        
        # UI state
        self.current_pair = (None, None)
        self.next_pair = (None, None)
        self.next_pair_images = {'left': None, 'right': None}
        self.previous_pair = (None, None)
        
        # Current displayed images (keep references to prevent garbage collection)
        self.current_images = {'left': None, 'right': None}
        
        # Window references to prevent multiple instances
        self.rankings_window = None
        self.stats_window = None
        self.settings_window = None
        
        # Timer references
        self.resize_timer = None
        self.preload_timer = None
        
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
            ("View Rankings", self.show_rankings, Colors.BUTTON_WARNING),
            ("View Stats", self.show_detailed_stats, Colors.BUTTON_SECONDARY),
            ("Settings", self.show_settings, Colors.BUTTON_NEUTRAL)
        ]
        
        for text, command, color in buttons:
            tk.Button(parent, text=text, command=command, 
                     bg=color, fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
    
    def create_main_frame(self):
        """Create the main voting area with image display."""
        main_frame = tk.Frame(self.root, bg=Colors.BG_PRIMARY)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure grid weights for equal distribution
        main_frame.grid_columnconfigure(0, weight=1, uniform="equal")
        main_frame.grid_columnconfigure(1, weight=0)  # VS label column
        main_frame.grid_columnconfigure(2, weight=1, uniform="equal")
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Create left and right image frames
        self.create_image_frame(main_frame, 'left', 0)
        self.create_vs_label(main_frame)
        self.create_image_frame(main_frame, 'right', 2)
    
    def create_image_frame(self, parent, side: str, column: int):
        """Create an image display frame for one side of the comparison."""
        frame = tk.Frame(parent, relief=tk.RAISED, borderwidth=2, bg=Colors.BG_SECONDARY)
        frame.grid(row=0, column=column, sticky="nsew", padx=5)
        
        # Image display label
        image_label = tk.Label(frame, text="No image", 
                              bg=Colors.BG_TERTIARY, fg=Colors.TEXT_PRIMARY, cursor="hand2")
        image_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        image_label.bind("<Button-1>", lambda e: self.vote(side))
        
        # Info label showing stats
        info_label = tk.Label(frame, text="", font=('Arial', 10), 
                             fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY)
        info_label.pack(pady=5)
        
        # Metadata label - larger font for better readability, with text wrapping
        metadata_label = tk.Label(frame, text="", font=('Arial', 10), 
                                 fg=Colors.TEXT_SECONDARY, bg=Colors.BG_SECONDARY, 
                                 justify=tk.LEFT)
        metadata_label.pack(pady=2, fill=tk.X, padx=10)
        
        # Vote button
        arrow = "←" if side == 'left' else "→"
        vote_button = tk.Button(frame, text=f"Vote for this image ({arrow})", 
                               command=lambda: self.vote(side), 
                               state=tk.DISABLED, font=('Arial', 12, 'bold'),
                               bg=Colors.BUTTON_SUCCESS, fg='white', height=2, relief=tk.FLAT)
        vote_button.pack(fill=tk.X, padx=10, pady=10)
        
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
        
        for key in KeyBindings.RANKINGS:
            self.root.bind(key, lambda e: self.show_rankings())
        
        for key in KeyBindings.STATS:
            self.root.bind(key, lambda e: self.show_detailed_stats())
        
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
        folder = filedialog.askdirectory(title="Select folder containing images")
        if folder:
            # Clear old images before loading new ones
            self.clear_old_images()
            
            self.data_manager.image_folder = folder
            self.load_images()
    
    def load_images(self):
        """Load images from the selected folder."""
        images = self.image_processor.get_image_files(self.data_manager.image_folder)
        
        if not images:
            messagebox.showerror("Error", "No images found in selected folder")
            return
        
        # Update folder label
        folder_name = os.path.basename(self.data_manager.image_folder)
        self.folder_label.config(text=f"Folder: {folder_name} ({len(images)} images)")
        
        # Initialize stats for all images
        for img in images:
            self.data_manager.initialize_image_stats(img)
            
            # Extract metadata if not already done
            stats = self.data_manager.get_image_stats(img)
            if stats.get('prompt') is None:
                img_path = os.path.join(self.data_manager.image_folder, img)
                try:
                    prompt = self.image_processor.extract_prompt_from_image(img_path)
                    metadata = self.image_processor.get_image_metadata(img_path)
                    self.data_manager.set_image_metadata(img, prompt, metadata)
                except Exception as e:
                    print(f"Error extracting metadata from {img}: {e}")
        
        # Update status and show first pair
        self.status_bar.config(text=f"Loaded {len(images)} images. Click images or use arrow keys (←/→) to vote.")
        self.show_next_pair()
    
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
        
        # Get next pair using ranking algorithm
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
            
            # Calculate display dimensions
            self.root.update_idletasks()
            window_width = self.root.winfo_width()
            window_height = self.root.winfo_height()
            max_image_width = max((window_width - 150) // 2, Defaults.MIN_IMAGE_WIDTH)
            max_image_height = max(window_height - 300, Defaults.MIN_IMAGE_HEIGHT)
            
            # Load and resize image
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
        """Update the info and metadata labels for an image."""
        stats = self.data_manager.get_image_stats(filename)
        
        # Calculate individual stability
        stability = self.ranking_algorithm._calculate_tier_stability(filename)
        
        # Create info text
        info_text = (f"Tier: {stats.get('current_tier', 0)} | "
                    f"Wins: {stats.get('wins', 0)} | "
                    f"Losses: {stats.get('losses', 0)} | "
                    f"Stability: {stability:.2f}")
        
        # Get prompt or metadata for display - show full prompt
        prompt = stats.get('prompt')
        metadata = stats.get('display_metadata')
        
        if prompt:
            # Show full prompt with better formatting
            metadata_text = f"Prompt: {prompt}"
        elif metadata:
            metadata_text = metadata
        else:
            metadata_text = "No prompt found"
        
        # Update labels with dynamic wraplength
        if side == 'left':
            self.left_info_label.config(text=info_text)
            # Update wraplength based on current frame width
            try:
                self.root.update_idletasks()
                frame_width = self.left_metadata_label.winfo_width()
                if frame_width > 100:  # Only update if frame has been rendered
                    self.left_metadata_label.config(text=metadata_text, wraplength=max(frame_width - 20, 300))
                else:
                    self.left_metadata_label.config(text=metadata_text, wraplength=400)
            except:
                self.left_metadata_label.config(text=metadata_text, wraplength=400)
        else:
            self.right_info_label.config(text=info_text)
            # Update wraplength based on current frame width
            try:
                self.root.update_idletasks()
                frame_width = self.right_metadata_label.winfo_width()
                if frame_width > 100:  # Only update if frame has been rendered
                    self.right_metadata_label.config(text=metadata_text, wraplength=max(frame_width - 20, 300))
                else:
                    self.right_metadata_label.config(text=metadata_text, wraplength=400)
            except:
                self.right_metadata_label.config(text=metadata_text, wraplength=400)
    
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
                messagebox.showinfo("Success", f"Data loaded from {filename}")
            else:
                messagebox.showerror("Error", f"Could not load data: {error_msg}")
    
    def show_rankings(self):
        """Show the rankings window."""
        if not self.data_manager.image_stats:
            messagebox.showinfo("No Data", "No ranking data to display. Please load images first.")
            return
        
        if self.rankings_window is None:
            self.rankings_window = RankingsWindow(self.root, self.data_manager, self.ranking_algorithm)
        else:
            self.rankings_window.show()
    
    def show_detailed_stats(self):
        """Show the detailed statistics window."""
        if not self.data_manager.image_stats:
            messagebox.showinfo("No Data", "No image data to display. Please load images first.")
            return
        
        if self.stats_window is None:
            self.stats_window = StatsWindow(self.root, self.data_manager, self.ranking_algorithm)
        else:
            self.stats_window.show()
    
    def show_settings(self):
        """Show the settings window."""
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self.root, self.data_manager)
        else:
            self.settings_window.show()
    
    def on_closing(self):
        """Handle application closing."""
        # Cancel any pending timers
        if self.resize_timer:
            self.root.after_cancel(self.resize_timer)
        if self.preload_timer:
            self.root.after_cancel(self.preload_timer)
        
        # Clear all image references
        self.clear_old_images()
        
        # Clean up image processor resources
        self.image_processor.cleanup_resources()
        
        # Destroy the window
        self.root.destroy()