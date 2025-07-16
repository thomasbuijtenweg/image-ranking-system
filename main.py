"""Main entry point for the Image Ranking System."""

import tkinter as tk
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow


def main():
    """Initialize and run the application."""
    root = tk.Tk()
    root.title("Image Ranking System")
    root.state('zoomed')
    
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)