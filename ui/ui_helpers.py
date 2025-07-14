"""
UI helper utilities for the Image Ranking System.

This module contains common UI creation patterns and utilities
used across multiple windows and components.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Tuple, Callable, Optional
from config import Colors  # Import from the centralized config


def create_button_row(parent: tk.Widget, buttons: List[Tuple[str, Callable, str]], 
                     side: str = tk.LEFT, padx: int = 5) -> tk.Frame:
    """
    Create a row of buttons with consistent styling.
    
    Args:
        parent: Parent widget
        buttons: List of (text, command, color) tuples
        side: Pack side for buttons
        padx: Padding between buttons
        
    Returns:
        Frame containing the buttons
    """
    button_frame = tk.Frame(parent, bg=Colors.BG_PRIMARY)
    
    for text, command, color in buttons:
        btn = tk.Button(button_frame, text=text, command=command, 
                       bg=color, fg='white', relief=tk.FLAT)
        btn.pack(side=side, padx=padx)
    
    return button_frame


def create_labeled_frame(parent: tk.Widget, title: str, bg_color: str = Colors.BG_SECONDARY) -> tk.LabelFrame:
    """
    Create a labeled frame with consistent styling.
    
    Args:
        parent: Parent widget
        title: Frame title
        bg_color: Background color
        
    Returns:
        Configured LabelFrame
    """
    frame = tk.LabelFrame(parent, text=title, padx=10, pady=5, 
                         fg=Colors.TEXT_PRIMARY, bg=bg_color,
                         relief=tk.RAISED, borderwidth=1)
    return frame


def create_info_label(parent: tk.Widget, text: str = "", font_size: int = 10, 
                     color: str = Colors.TEXT_PRIMARY) -> tk.Label:
    """
    Create an info label with consistent styling.
    
    Args:
        parent: Parent widget
        text: Label text
        font_size: Font size
        color: Text color
        
    Returns:
        Configured Label
    """
    return tk.Label(parent, text=text, font=('Arial', font_size), 
                   fg=color, bg=parent.cget('bg'), justify=tk.LEFT)


def create_scrollable_treeview(parent: tk.Widget, columns: List[str], 
                              height: int = 20) -> Tuple[ttk.Treeview, ttk.Scrollbar]:
    """
    Create a treeview with scrollbar using consistent styling.
    
    Args:
        parent: Parent widget
        columns: List of column names
        height: Treeview height
        
    Returns:
        Tuple of (treeview, scrollbar)
    """
    # Create treeview with scrollbar
    tree = ttk.Treeview(parent, columns=columns, show='tree headings', height=height)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    # Configure column headings
    for col in columns:
        tree.heading(col, text=col)
    
    return tree, scrollbar


def create_text_with_scrollbar(parent: tk.Widget, height: int = 4, 
                              bg_color: str = Colors.BG_TERTIARY) -> Tuple[tk.Text, ttk.Scrollbar]:
    """
    Create a text widget with scrollbar.
    
    Args:
        parent: Parent widget
        height: Text widget height
        bg_color: Background color
        
    Returns:
        Tuple of (text_widget, scrollbar)
    """
    text_widget = tk.Text(parent, height=height, wrap=tk.WORD, 
                         bg=bg_color, fg=Colors.TEXT_PRIMARY, 
                         font=('Arial', 10), relief=tk.FLAT, state=tk.DISABLED)
    
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=text_widget.yview)
    text_widget.configure(yscrollcommand=scrollbar.set)
    
    return text_widget, scrollbar


def setup_dark_theme_style() -> ttk.Style:
    """
    Set up ttk styles for dark mode.
    
    Returns:
        Configured Style object
    """
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
    
    return style


def bind_hover_events(widget: tk.Widget, on_enter: Callable, on_leave: Callable):
    """
    Bind hover events to a widget and all its children.
    
    Args:
        widget: Widget to bind events to
        on_enter: Function to call on mouse enter
        on_leave: Function to call on mouse leave
    """
    # Bind to the widget itself
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)
    
    # Also bind to all child widgets
    def bind_to_children(parent_widget):
        for child in parent_widget.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)
            bind_to_children(child)
    
    bind_to_children(widget)


def create_navigation_buttons(parent: tk.Widget, jump_to_top: Callable, 
                            jump_to_bottom: Callable, instruction_text: str = "") -> tk.Frame:
    """
    Create standard navigation buttons.
    
    Args:
        parent: Parent widget
        jump_to_top: Function to call for jump to top
        jump_to_bottom: Function to call for jump to bottom
        instruction_text: Optional instruction text to display
        
    Returns:
        Frame containing navigation elements
    """
    nav_frame = tk.Frame(parent, bg=Colors.BG_SECONDARY)
    
    tk.Button(nav_frame, text="Jump to Top", command=jump_to_top, 
             bg=Colors.BUTTON_BG, fg=Colors.TEXT_PRIMARY, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
    tk.Button(nav_frame, text="Jump to Bottom", command=jump_to_bottom, 
             bg=Colors.BUTTON_BG, fg=Colors.TEXT_PRIMARY, relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
    
    if instruction_text:
        tk.Label(nav_frame, text=instruction_text, 
                font=('Arial', 10, 'italic'), fg=Colors.TEXT_SECONDARY, 
                bg=Colors.BG_SECONDARY).pack(side=tk.RIGHT, padx=20)
    
    return nav_frame


def create_search_frame(parent: tk.Widget, search_var: tk.StringVar, 
                       search_command: Callable, label_text: str = "Search:") -> tk.Frame:
    """
    Create a search input frame.
    
    Args:
        parent: Parent widget
        search_var: StringVar for search input
        search_command: Function to call when searching
        label_text: Label text for search input
        
    Returns:
        Frame containing search elements
    """
    search_frame = tk.Frame(parent, bg=parent.cget('bg'))
    
    tk.Label(search_frame, text=label_text, font=('Arial', 10), 
            fg=Colors.TEXT_PRIMARY, bg=parent.cget('bg')).pack(side=tk.LEFT)
    
    search_entry = tk.Entry(search_frame, textvariable=search_var, width=15,
                           bg=Colors.BG_TERTIARY, fg=Colors.TEXT_PRIMARY)
    search_entry.pack(side=tk.LEFT, padx=(5, 5))
    search_entry.bind('<Return>', lambda e: search_command())
    
    tk.Button(search_frame, text="Search", command=search_command,
             bg=Colors.BUTTON_SECONDARY, fg='white', relief=tk.FLAT).pack(side=tk.LEFT)
    
    return search_frame