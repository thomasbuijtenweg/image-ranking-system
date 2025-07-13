"""
Main entry point for the Image Ranking System.

This file serves as the application's starting point, initializing
the main window and starting the tkinter event loop.

By keeping this file simple and focused, we create a clean separation
between application startup and the main application logic.
"""

import tkinter as tk
import sys
import os

# Add the project root to the Python path to enable imports
# This allows us to import from our organized module structure
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow


def main():
    """
    Main function that initializes and runs the application.
    
    This function creates the root tkinter window and passes it to
    the MainWindow class, which handles all the application logic.
    """
    # Create the root tkinter window
    root = tk.Tk()
    
    # Set some basic window properties
    root.title("Image Ranking System")
    root.state('zoomed')  # Start maximized on Windows
    
    # Create the main application window
    # The MainWindow class handles all the complex UI logic
    app = MainWindow(root)
    
    # Start the tkinter event loop
    # This keeps the application running and responsive to user input
    root.mainloop()


if __name__ == "__main__":
    """
    This block ensures that main() only runs when this file is executed directly,
    not when it's imported as a module from another file.
    
    This is a Python best practice that makes your code more modular and testable.
    """
    try:
        main()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        # Handle unexpected errors gracefully
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)