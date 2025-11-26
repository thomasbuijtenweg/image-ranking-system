"""UI component for prompt-based filtering controls."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class FilterUI:
    """Manages the filter control interface."""
    
    def __init__(self, parent: tk.Widget, filter_manager, on_filter_change: Optional[Callable] = None):
        self.parent = parent
        self.filter_manager = filter_manager
        self.on_filter_change = on_filter_change
        
        self.filter_frame = None
        self.content_frame = None  # Collapsible content
        self.is_expanded = False  # Start collapsed
        self.toggle_button = None
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search_change)
        
        # UI elements
        self.search_listbox = None
        self.include_listbox = None
        self.exclude_listbox = None
        self.logic_var = tk.StringVar(value='AND')
        self.stats_label = None
        self.header_stats_label = None  # Stats visible when collapsed
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """Create the filter UI with collapsible content."""
        # Main filter frame
        self.filter_frame = tk.Frame(self.parent, bg='#2b2b2b')
        self.filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Header (always visible) with toggle button
        header_frame = tk.Frame(self.filter_frame, bg='#3a3a3a', relief=tk.RAISED, bd=1)
        header_frame.pack(fill=tk.X, padx=2, pady=2)
        
        # Toggle button
        self.toggle_button = tk.Button(
            header_frame, 
            text="▶ Prompt Filters",
            command=self._toggle_expand,
            bg='#3a3a3a',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief=tk.FLAT,
            anchor='w',
            padx=10,
            pady=5
        )
        self.toggle_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Header stats (visible when collapsed)
        self.header_stats_label = tk.Label(
            header_frame, 
            text="No filters active",
            bg='#3a3a3a',
            fg='#aaaaaa',
            font=('Arial', 9)
        )
        self.header_stats_label.pack(side=tk.RIGHT, padx=10)
        
        # Content frame (collapsible)
        self.content_frame = tk.Frame(self.filter_frame, bg='#2b2b2b')
        # Don't pack it yet - will be packed when expanded
        
        self._create_filter_content()
        
        # Initial state
        self._update_header_stats()
    
    def _create_filter_content(self) -> None:
        """Create the actual filter controls (inside content_frame)."""
        
        # Search section
        search_frame = ttk.Frame(self.content_frame)
        search_frame.pack(fill=tk.X, pady=(10, 10), padx=10)
        
        ttk.Label(search_frame, text="Search words:").pack(side=tk.LEFT, padx=(0, 5))
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Search results
        search_results_frame = ttk.LabelFrame(self.content_frame, text="Available Words (click to add)", padding=5)
        search_results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=10)
        
        # Scrollable listbox with word frequencies
        search_scroll = ttk.Scrollbar(search_results_frame, orient=tk.VERTICAL)
        self.search_listbox = tk.Listbox(
            search_results_frame,
            yscrollcommand=search_scroll.set,
            height=8,
            selectmode=tk.SINGLE
        )
        search_scroll.config(command=self.search_listbox.yview)
        search_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.search_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.search_listbox.bind('<Double-Button-1>', self._on_word_double_click)
        
        # Add buttons frame
        add_buttons_frame = ttk.Frame(self.content_frame)
        add_buttons_frame.pack(fill=tk.X, pady=(0, 10), padx=10)
        
        ttk.Button(add_buttons_frame, text="Add to Include", 
                  command=self._add_to_include).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(add_buttons_frame, text="Add to Exclude", 
                  command=self._add_to_exclude).pack(side=tk.LEFT)
        
        # Active filters section
        filters_container = ttk.Frame(self.content_frame)
        filters_container.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # Include filters
        include_frame = ttk.LabelFrame(filters_container, text="Include (must have)", padding=5)
        include_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        include_scroll = ttk.Scrollbar(include_frame, orient=tk.VERTICAL)
        self.include_listbox = tk.Listbox(
            include_frame,
            yscrollcommand=include_scroll.set,
            height=6,
            selectmode=tk.SINGLE
        )
        include_scroll.config(command=self.include_listbox.yview)
        include_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.include_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.include_listbox.bind('<Double-Button-1>', self._on_include_double_click)
        
        # Exclude filters
        exclude_frame = ttk.LabelFrame(filters_container, text="Exclude (must NOT have)", padding=5)
        exclude_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        exclude_scroll = ttk.Scrollbar(exclude_frame, orient=tk.VERTICAL)
        self.exclude_listbox = tk.Listbox(
            exclude_frame,
            yscrollcommand=exclude_scroll.set,
            height=6,
            selectmode=tk.SINGLE
        )
        exclude_scroll.config(command=self.exclude_listbox.yview)
        exclude_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.exclude_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.exclude_listbox.bind('<Double-Button-1>', self._on_exclude_double_click)
        
        # Control buttons
        control_frame = ttk.Frame(self.content_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0), padx=10)
        
        # Logic toggle
        logic_frame = ttk.Frame(control_frame)
        logic_frame.pack(side=tk.LEFT)
        
        ttk.Label(logic_frame, text="Include Logic:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Radiobutton(logic_frame, text="AND (all words)", 
                       variable=self.logic_var, value='AND',
                       command=self._on_logic_change).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Radiobutton(logic_frame, text="OR (any word)", 
                       variable=self.logic_var, value='OR',
                       command=self._on_logic_change).pack(side=tk.LEFT)
        
        # Clear and Apply buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side=tk.RIGHT)
        
        ttk.Button(button_frame, text="Clear All Filters", 
                  command=self._clear_filters).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Apply Filters", 
                  command=self._apply_filters).pack(side=tk.LEFT)
        
        # Stats display (inside expanded view)
        self.stats_label = ttk.Label(self.content_frame, text="", foreground="blue")
        self.stats_label.pack(pady=(10, 10), padx=10)
    
    def _toggle_expand(self) -> None:
        """Toggle the expanded/collapsed state of the filter panel."""
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            # Expand - show content
            self.toggle_button.config(text="▼ Prompt Filters")
            self.content_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0, 2))
            # Populate content when first expanded
            self._refresh_search_results()
            self._refresh_filter_lists()
            self._update_stats()
        else:
            # Collapse - hide content
            self.toggle_button.config(text="▶ Prompt Filters")
            self.content_frame.pack_forget()
        
        self._update_header_stats()
    
    def _update_header_stats(self) -> None:
        """Update the header stats label (visible when collapsed)."""
        stats = self.filter_manager.get_filter_stats()
        
        if stats['is_active']:
            filter_count = len(stats['include_words']) + len(stats['exclude_words'])
            self.header_stats_label.config(
                text=f"{filter_count} filter(s) active - {stats['filtered_image_count']}/{stats['total_active_images']} images ({stats['filtered_percentage']:.1f}%)",
                fg='#4CAF50'  # Green when active
            )
        else:
            self.header_stats_label.config(
                text="No filters active",
                fg='#aaaaaa'  # Gray when inactive
            )
    
    def _on_search_change(self, *args) -> None:
        """Handle search text change."""
        self._refresh_search_results()
    
    def _refresh_search_results(self) -> None:
        """Refresh the search results listbox."""
        pattern = self.search_var.get()
        results = self.filter_manager.search_words(pattern, limit=100)
        
        self.search_listbox.delete(0, tk.END)
        for word, frequency in results:
            self.search_listbox.insert(tk.END, f"{word} ({frequency})")
    
    def _refresh_filter_lists(self) -> None:
        """Refresh the include and exclude filter lists."""
        # Include list
        self.include_listbox.delete(0, tk.END)
        for word in sorted(self.filter_manager.include_words):
            freq = self.filter_manager.get_word_frequency(word)
            self.include_listbox.insert(tk.END, f"{word} ({freq})")
        
        # Exclude list
        self.exclude_listbox.delete(0, tk.END)
        for word in sorted(self.filter_manager.exclude_words):
            freq = self.filter_manager.get_word_frequency(word)
            self.exclude_listbox.insert(tk.END, f"{word} ({freq})")
    
    def _update_stats(self) -> None:
        """Update the filter statistics display."""
        stats = self.filter_manager.get_filter_stats()
        
        if stats['is_active']:
            self.stats_label.config(
                text=f"Filtering: {stats['filtered_image_count']} / {stats['total_active_images']} images "
                     f"({stats['filtered_percentage']:.1f}%)",
                foreground="blue"
            )
        else:
            self.stats_label.config(
                text=f"No filters active - {stats['total_active_images']} images available",
                foreground="gray"
            )
        
        # Also update header stats
        self._update_header_stats()
    
    def _get_selected_word_from_search(self) -> Optional[str]:
        """Get the selected word from search results."""
        selection = self.search_listbox.curselection()
        if not selection:
            return None
        
        text = self.search_listbox.get(selection[0])
        # Extract word from "word (frequency)" format
        word = text.split(' (')[0] if ' (' in text else text
        return word
    
    def _add_to_include(self) -> None:
        """Add selected word to include filters."""
        word = self._get_selected_word_from_search()
        if word:
            self.filter_manager.add_include_word(word)
            self._refresh_filter_lists()
            self._update_stats()
    
    def _add_to_exclude(self) -> None:
        """Add selected word to exclude filters."""
        word = self._get_selected_word_from_search()
        if word:
            self.filter_manager.add_exclude_word(word)
            self._refresh_filter_lists()
            self._update_stats()
    
    def _on_word_double_click(self, event) -> None:
        """Handle double-click on search result - add to include."""
        self._add_to_include()
    
    def _on_include_double_click(self, event) -> None:
        """Handle double-click on include filter - remove it."""
        selection = self.include_listbox.curselection()
        if not selection:
            return
        
        text = self.include_listbox.get(selection[0])
        word = text.split(' (')[0] if ' (' in text else text
        
        self.filter_manager.remove_include_word(word)
        self._refresh_filter_lists()
        self._update_stats()
    
    def _on_exclude_double_click(self, event) -> None:
        """Handle double-click on exclude filter - remove it."""
        selection = self.exclude_listbox.curselection()
        if not selection:
            return
        
        text = self.exclude_listbox.get(selection[0])
        word = text.split(' (')[0] if ' (' in text else text
        
        self.filter_manager.remove_exclude_word(word)
        self._refresh_filter_lists()
        self._update_stats()
    
    def _on_logic_change(self) -> None:
        """Handle filter logic change."""
        logic = self.logic_var.get()
        self.filter_manager.set_filter_logic(logic)
        self._update_stats()
    
    def _clear_filters(self) -> None:
        """Clear all filters."""
        self.filter_manager.clear_filters()
        self._refresh_filter_lists()
        self._update_stats()
        
        if self.on_filter_change:
            self.on_filter_change()
    
    def _apply_filters(self) -> None:
        """Apply the current filters."""
        if self.on_filter_change:
            self.on_filter_change()
        
        self._update_stats()
    
    def refresh(self) -> None:
        """Refresh all UI elements."""
        if self.is_expanded:
            self._refresh_search_results()
            self._refresh_filter_lists()
            self._update_stats()
        else:
            # Just update header when collapsed
            self._update_header_stats()
    
    def show(self) -> None:
        """Show the filter frame."""
        self.filter_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)
    
    def hide(self) -> None:
        """Hide the filter frame."""
        self.filter_frame.pack_forget()
